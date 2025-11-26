import { NextRequest, NextResponse } from "next/server";
import { requireGithubAccessToken } from "@/lib/github-auth";
import { getPrStatsFromGitHub } from "@/lib/pr-stats";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const repo = searchParams.get("repo");
  const since = searchParams.get("since");
  const until = searchParams.get("until");
  const bucket = (searchParams.get("bucket") ?? "day") as "day" | "week" | "month";
  const author = searchParams.get("author");

  if (!repo || !since || !until) {
    return NextResponse.json(
      { error: "参数缺失：repo、since、until 为必填项" },
      { status: 400 },
    );
  }

  const [owner, project] = repo.split("/");
  if (!owner || !project) {
    return NextResponse.json(
      { error: "repo 参数格式应为 owner/name" },
      { status: 400 },
    );
  }

  try {
    const token = await requireGithubAccessToken();
    const data = await getPrStatsFromGitHub({
      owner,
      project,
      repo,
      since,
      until,
      bucket,
      author,
      token,
    });
    return NextResponse.json(data);
  } catch (error) {
    console.error("[pr-stats] error", error);
    const message = error instanceof Error ? error.message : "PR 统计数据获取失败";
    return NextResponse.json(
      { error: message },
      { status: 500 },
    );
  }
}


