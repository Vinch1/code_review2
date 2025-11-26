"use server";

import { requireGithubAccessToken } from "@/lib/github-auth";
import { getPrStatsFromGitHub, PrStatsResponse } from "@/lib/pr-stats";

export type FetchPrStatsInput = {
  owner: string;
  project: string;
  since: string;
  until: string;
  bucket?: "day" | "week" | "month";
  author?: string | null;
};

export async function fetchPrStatsAction(input: FetchPrStatsInput): Promise<PrStatsResponse> {
  const token = await requireGithubAccessToken();
  return getPrStatsFromGitHub({
    owner: input.owner,
    project: input.project,
    repo: `${input.owner}/${input.project}`,
    since: input.since,
    until: input.until,
    bucket: input.bucket,
    author: input.author,
    token,
  });
}



