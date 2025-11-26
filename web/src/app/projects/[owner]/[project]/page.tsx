import dayjs from "dayjs";
import ProjectDetailClient from "./page.client";
import { getCodeReviewResultsByRepoGroupedByDay } from "@/lib/db";
import { requireGithubAccessToken } from "@/lib/github-auth";
import { getPrStatsFromGitHub, type PrStatsResponse } from "@/lib/pr-stats";
import { CodeReviewResult } from "@prisma/client";
type PageProps = {
  params: {
    owner: string;
    project: string;
  };
};

const DEFAULT_BUCKET = "day" as const;

export default async function ProjectDetailPage({ params }: PageProps) {
  const owner = params.owner;
  const projectId = params.project;
  const repoFullName = `${owner}/${projectId}`;

  const groupsRaw = await getCodeReviewResultsByRepoGroupedByDay(repoFullName);
  const groups = JSON.parse(
    JSON.stringify(groupsRaw, (_, value) => (typeof value === "bigint" ? value.toString() : value)),
  ) as Array<{ day: string; records: CodeReviewResult[] }>;

  const defaultSince = dayjs().subtract(29, "day").startOf("day").toISOString();
  const defaultUntil = dayjs().endOf("day").toISOString();

  let initialStats: PrStatsResponse | null = null;
  try {
    const token = await requireGithubAccessToken();
    initialStats = await getPrStatsFromGitHub({
      owner,
      project: projectId,
      repo: repoFullName,
      since: defaultSince,
      until: defaultUntil,
      bucket: DEFAULT_BUCKET,
      token,
    });
  } catch (error) {
    console.error("[ProjectDetailPage] 初始 PR 统计获取失败", error);
  }

  return (
    <ProjectDetailClient
      owner={owner}
      projectId={projectId}
      groups={groups}
      initialStats={initialStats}
      defaultSince={defaultSince}
      defaultUntil={defaultUntil}
      defaultBucket={DEFAULT_BUCKET}
    />
  );
}

