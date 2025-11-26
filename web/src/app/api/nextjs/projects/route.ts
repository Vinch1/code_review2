import { NextResponse } from "next/server";
import type { Project } from "@/types/project";
import { fetchGitHubProjects } from "@/lib/github";
import prisma from "@/lib/prisma";

export async function GET() {
  // 根据用户github sso信息，获取用户帐号下的所有仓库
  // 本路由需要鉴权，读取 token 后访问 GitHub API
  try {
    const projects: Project[] = await fetchGitHubProjects();
    console.log("projects", projects);

    // 查询数据库中已存在配置的仓库列表（code_review_results.repo 不为空）
    const rows = await prisma.codeReviewResult.findMany({
      select: { repo: true },
      where: { repo: { not: null } },
    });
    const configuredRepoSet = new Set<string>(
      rows.map((r) => r.repo).filter((v): v is string => typeof v === "string" && v.length > 0)
    );

    // 合并：若该项目的 repo 在数据库中存在，则标记 hasConfiged = true
    const merged: Project[] = projects.map((p) => ({
      ...p,
      hasConfiged: configuredRepoSet.has(p.repo ?? p.name),
    }));

    return NextResponse.json(merged);
  } catch (error) {
    if (error instanceof Error && error.message === "Unauthorized") {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    } else {
      console.error("Error fetching GitHub projects:", error);
      return NextResponse.json({ error: "Failed to fetch GitHub projects" }, { status: 500 });
    }
  }
}



