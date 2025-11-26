import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import weekOfYear from "dayjs/plugin/weekOfYear";

dayjs.extend(utc);
dayjs.extend(weekOfYear);

type BucketOption = "day" | "week" | "month";

type GitHubUser = {
  login?: string | null;
};

type GitHubPullRequest = {
  id: number;
  number: number;
  created_at: string;
  closed_at: string | null;
  merged_at: string | null;
  user: GitHubUser | null;
};

export type PrStatsMetric = {
  created: number;
  merged: number;
  closed: number;
};

export type PrStatsBucket = {
  bucket_start: string;
  bucket_end: string;
  label: string;
};

export type PrStatsAuthor = {
  author: string;
  series: PrStatsMetric[];
  totals: PrStatsMetric;
};

export type PrStatsResponse = {
  repo: string;
  bucket: BucketOption;
  buckets: PrStatsBucket[];
  authors: PrStatsAuthor[];
  totals: PrStatsMetric;
};

type FetchPrsOptions = {
  owner: string;
  repo: string;
  since: Date;
  until: Date;
  token: string;
  author?: string | null;
};

const GITHUB_API = "https://api.github.com";
const PER_PAGE = 100;
const MAX_PAGES = 50; // Safety limit (5,000 PRs)

async function fetchPullRequestsFromGitHub({
  owner,
  repo,
  since,
  until,
  token,
  author,
}: FetchPrsOptions): Promise<GitHubPullRequest[]> {
  const results: GitHubPullRequest[] = [];
  let page = 1;
  const sinceTs = since.getTime();
  const untilTs = until.getTime();

  while (page <= MAX_PAGES) {
    const url = new URL(`${GITHUB_API}/repos/${owner}/${repo}/pulls`);
    url.searchParams.set("state", "all");
    url.searchParams.set("per_page", PER_PAGE.toString());
    url.searchParams.set("page", page.toString());
    url.searchParams.set("sort", "created");
    url.searchParams.set("direction", "desc");

    const res = await fetch(url.toString(), {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
      },
      cache: "no-store",
    });

    if (res.status === 403) {
      const reset = res.headers.get("x-ratelimit-reset");
      throw new Error(
        `GitHub API 速率受限，请稍后重试${reset ? ` (reset at ${reset})` : ""}`,
      );
    }

    if (!res.ok) {
      const message = await res.text();
      throw new Error(`GitHub PR 列表获取失败: ${res.status} ${message}`);
    }

    const data: unknown = await res.json();
    if (!Array.isArray(data) || data.length === 0) {
      break;
    }

    let reachedOlderThanSince = false;

    for (const item of data) {
      if (!item || typeof item !== "object") continue;
      const pr = item as GitHubPullRequest;
      if (!pr.created_at) continue;
      const createdTs = new Date(pr.created_at).getTime();

      if (createdTs < sinceTs) {
        reachedOlderThanSince = true;
        break;
      }
      if (createdTs > untilTs) {
        // Skip PRs newer than until (because we sorted desc).
        continue;
      }
      if (author && pr.user?.login && pr.user.login.toLowerCase() !== author.toLowerCase()) {
        continue;
      }
      results.push(pr);
    }

    if (reachedOlderThanSince || data.length < PER_PAGE) {
      break;
    }
    page += 1;
  }

  return results;
}

function startOfWeekUTC(date: Date): Date {
  const day = date.getUTCDay(); // 0 (Sun) ... 6 (Sat)
  const diff = (day + 6) % 7; // Make Monday=0
  const result = new Date(Date.UTC(
    date.getUTCFullYear(),
    date.getUTCMonth(),
    date.getUTCDate(),
  ));
  result.setUTCDate(result.getUTCDate() - diff);
  return result;
}

function addBucket(start: Date, bucket: BucketOption): Date {
  switch (bucket) {
    case "day":
      return new Date(start.getTime() + 24 * 60 * 60 * 1000);
    case "week":
      return new Date(start.getTime() + 7 * 24 * 60 * 60 * 1000);
    case "month":
    default: {
      const year = start.getUTCFullYear();
      const month = start.getUTCMonth();
      return new Date(Date.UTC(year, month + 1, 1));
    }
  }
}

function bucketFloor(date: Date, bucket: BucketOption): Date {
  switch (bucket) {
    case "day":
      return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
    case "week":
      return startOfWeekUTC(date);
    case "month":
    default:
      return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1));
  }
}

function bucketLabel(start: Date, bucket: BucketOption): string {
  if (bucket === "day") {
    return dayjs(start).utc().format("YYYY-MM-DD");
  }
  if (bucket === "week") {
    const weekNumber = parseInt(dayjs(start).utc().format("WW"), 10);
    return `${start.getUTCFullYear()}-W${weekNumber.toString().padStart(2, "0")}`;
  }
  return dayjs(start).utc().format("YYYY-MM");
}

function buildTimeline(since: Date, until: Date, bucket: BucketOption): Array<{ start: Date; end: Date; label: string }> {
  const timeline: Array<{ start: Date; end: Date; label: string }> = [];
  let current = bucketFloor(since, bucket);
  const limit = until;
  while (current < limit) {
    const end = addBucket(current, bucket);
    timeline.push({
      start: current,
      end,
      label: bucketLabel(current, bucket),
    });
    current = end;
  }
  return timeline;
}

function findBucketIndex(date: Date, timeline: Array<{ start: Date; end: Date }>): number {
  const ts = date.getTime();
  for (let i = 0; i < timeline.length; i += 1) {
    const { start, end } = timeline[i];
    if (ts >= start.getTime() && ts < end.getTime()) {
      return i;
    }
  }
  return -1;
}

function createEmptyMetric(): PrStatsMetric {
  return { created: 0, merged: 0, closed: 0 };
}

function computeStats(
  prs: GitHubPullRequest[],
  timeline: Array<{ start: Date; end: Date; label: string }>,
  bucket: BucketOption,
  repo: string,
): PrStatsResponse {
  const buckets: PrStatsBucket[] = timeline.map(({ start, end, label }) => ({
    bucket_start: start.toISOString(),
    bucket_end: end.toISOString(),
    label,
  }));

  const totals: PrStatsMetric = { created: 0, merged: 0, closed: 0 };
  const authorsMap = new Map<string, { series: PrStatsMetric[]; totals: PrStatsMetric }>();

  for (const pr of prs) {
    const author = (pr.user?.login ?? "unknown").trim() || "unknown";
    const createdAt = new Date(pr.created_at);
    const createdBucketIdx = findBucketIndex(createdAt, timeline);
    if (createdBucketIdx === -1) continue;

    if (!authorsMap.has(author)) {
      authorsMap.set(author, {
        series: timeline.map(() => createEmptyMetric()),
        totals: createEmptyMetric(),
      });
    }
    const authorData = authorsMap.get(author)!;

    authorData.series[createdBucketIdx].created += 1;
    authorData.totals.created += 1;
    totals.created += 1;

    if (pr.merged_at) {
      const mergedIdx = findBucketIndex(new Date(pr.merged_at), timeline);
      if (mergedIdx !== -1) {
        authorData.series[mergedIdx].merged += 1;
        authorData.totals.merged += 1;
        totals.merged += 1;
      }
    }
    if (pr.closed_at) {
      const closedIdx = findBucketIndex(new Date(pr.closed_at), timeline);
      if (closedIdx !== -1) {
        authorData.series[closedIdx].closed += 1;
        authorData.totals.closed += 1;
        totals.closed += 1;
      }
    }
  }

  const authors: PrStatsAuthor[] = Array.from(authorsMap.entries())
    .map(([author, data]) => ({
      author,
      series: data.series,
      totals: data.totals,
    }))
    .sort((a, b) => {
      if (b.totals.merged !== a.totals.merged) {
        return b.totals.merged - a.totals.merged;
      }
      return b.totals.created - a.totals.created;
    });

  return {
    repo,
    bucket,
    buckets,
    authors,
    totals,
  };
}

export type PrStatsParams = {
  owner: string;
  project: string;
  repo: string;
  since: string;
  until: string;
  bucket?: BucketOption;
  author?: string | null;
  token: string;
};

export async function getPrStatsFromGitHub({
  owner,
  project,
  repo,
  since,
  until,
  bucket = "day",
  author,
  token,
}: PrStatsParams): Promise<PrStatsResponse> {
  if (!since || !until) {
    throw new Error("since 与 until 参数必填");
  }

  const sinceDate = new Date(since);
  const untilDate = new Date(until);
  if (Number.isNaN(sinceDate.getTime()) || Number.isNaN(untilDate.getTime())) {
    throw new Error("since 或 until 参数格式不合法");
  }
  if (sinceDate >= untilDate) {
    throw new Error("since 需早于 until");
  }

  const timeline = buildTimeline(sinceDate, untilDate, bucket);
  if (timeline.length === 0) {
    return {
      repo,
      bucket,
      buckets: [],
      authors: [],
      totals: { created: 0, merged: 0, closed: 0 },
    };
  }

  const prs = await fetchPullRequestsFromGitHub({
    owner,
    repo: project,
    since: sinceDate,
    until: untilDate,
    token,
    author,
  });

  return computeStats(prs, timeline, bucket, repo);
}


