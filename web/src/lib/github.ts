import { defaultAuthOptions } from "@/auth";
import type { GitHubRepo, Project } from "@/types/project";
import { getServerSession } from "next-auth";
import prisma from "@/lib/prisma";

const GITHUB_API_URL = "https://api.github.com";

async function fetchUserRepos(token: string): Promise<GitHubRepo[]> {
  const res = await fetch(`${GITHUB_API_URL}/user/repos?per_page=100`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
    },
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to fetch GitHub repos");
  return res.json();
}
export async function getGithubLoginFromToken(token?: string) {
  const getAccessTokenFromSession = async () => {
    const session = await getServerSession(defaultAuthOptions);
    // next-auth的github provider下，session?.accessToken 一般可用
    // 但如无accessToken，可适配session?.token?.access_token等结构
    let token = session?.accessToken
    if (!token && session?.user && Array.isArray(session.user.accounts)) {
      // union多provider时，尝试取github的
      const gh = session.user.accounts.find((a: { provider: string; access_token: string; }) => a.provider === "github");
      if (gh?.access_token) token = gh.access_token;
    }
    return token;
  };
  if (!token) {
    token = await getAccessTokenFromSession();
  }
  if (!token) throw new Error("Unauthorized");
  const res = await fetch(`${GITHUB_API_URL}/user`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json"
    },
  });
  if (!res.ok) throw new Error("Failed to fetch GitHub user");
  const user = await res.json();
  return user?.login as string | null;
}
export async function fetchGitHubProjects(): Promise<Project[]> {
  const getAccessTokenFromSession = async () => {
    const session = await getServerSession(defaultAuthOptions);
    // next-auth的github provider下，session?.accessToken 一般可用
    // 但如无accessToken，可适配session?.token?.access_token等结构
    let token = session?.accessToken
    if (!token && session?.user && Array.isArray(session.user.accounts)) {
      // union多provider时，尝试取github的
      const gh = session.user.accounts.find((a: { provider: string; access_token: string; }) => a.provider === "github");
      if (gh?.access_token) token = gh.access_token;
    }
    return token;
  };

  const token = await getAccessTokenFromSession();

  if (!token) throw new Error("Unauthorized");
  const ghRepos = await fetchUserRepos(token);
  const owner = await getGithubLoginFromToken();
  return (Array.isArray(ghRepos) ? ghRepos : []).map((r: GitHubRepo) => {
    const repoUrl = r.link || (owner ? `https://github.com/${owner}/${r.name}` : undefined);
    const webhookSettingsUrl = owner ? `https://github.com/${owner}/${r.name}/settings/hooks` : undefined;
    return {
      id: r.name,
      name: r.name,
      description: r.description || "暂无项目描述",
      updatedAt: r.updated_at,
      status: r.archived ? "archived" : r.private ? "paused" : "active",
      owner: owner ?? undefined,
      repo: r.name,
      repoUrl,
      webhookSettingsUrl,
      hasConfiged: false,
    } as Project;
  });
}


export async function fetchProjectsWithConfigStatus(): Promise<Project[]> {
  const projects = await fetchGitHubProjects();
  const rows = await prisma.codeReviewResult.findMany({
    select: { repo: true },
    where: { repo: { not: null } },
  });
  const configuredRepoSet = new Set<string>(
    rows.map((r) => r.repo?.split('/').pop()).filter((v): v is string => typeof v === "string" && v.length > 0)
  );
  // 先合并 hasConfiged 字段，再排序（已配置的在前）
  const res = projects
    .map((p) => ({
      ...p,
      hasConfiged: configuredRepoSet.has(p.repo ?? ""),
    }))
    .sort((a, b) => Number(b.hasConfiged) - Number(a.hasConfiged));
  return res;
}

/**
 * 通过 GitHub access token 获取用户头像 URL
 * @param {string} token - GitHub access token
 * @returns {Promise<string>} 头像图片 URL
 */
export async function fetchGithubAvatarByToken(token: string): Promise<string> {
  const res = await fetch("https://api.github.com/user", {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json"
    }
  });
  if (!res.ok) throw new Error("Failed to fetch GitHub user info");
  const data = await res.json();
  if (typeof data.avatar_url === "string") {
    return data.avatar_url;
  }
  throw new Error("GitHub account has no avatar");
}
/**
 * 获取某项目的所有 branch
 * @param {string} owner - 仓库拥有者
 * @param {string} repo - 仓库名
 * @param {string} token - 用户 GitHub access token
 * @returns {Promise<string[]>} 分支名数组
 */
export async function fetchGithubBranches(owner: string, repo: string, token: string): Promise<string[]> {
  const branches: string[] = [];
  let page = 1;
  const perPage = 100;
  while (true) {
    const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/branches?per_page=${perPage}&page=${page}`, {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
      },
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch branches: ${res.statusText}`);
    }
    const data = await res.json();
    if (!Array.isArray(data)) break;
    branches.push(...data.map((b) => b.name));
    if (data.length < perPage) break;
    page++;
  }
  return branches;
}
/**
 * 获取某个仓库某个分支下的指定文件内容
 * @param {string} owner - 仓库拥有者
 * @param {string} repo - 仓库名
 * @param {string} branch - 分支名
 * @param {string} path - 文件路径(相对仓库根目录)
 * @param {string} token - 用户 GitHub access token
 * @returns {Promise<string>} 文件内容（以 string 返回，原始内容为 base64 需解码）
 */
export async function fetchGithubFileContent({
  repo,
  branch,
  path,
  token
}: {
  repo: string;
  branch: string;
  path: string;
  token: string;
}): Promise<string> {
  const url = `https://api.github.com/repos/${repo}/contents/${path}?ref=${branch}`;
  console.log(url);
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github.v3.raw"
    }
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch file: ${res.status} ${res.statusText}`);
  }
  // Github API 会根据Accept返回不同类型:
  // 如果Accept: v3.raw，则为原始内容，否则为json对象（含content/base64）
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    // 走 fallback，防止内容特别大时API自动切回application/json
    const data = await res.json();
    if (data && typeof data.content === "string" && data.encoding === "base64") {
      return Buffer.from(data.content, "base64").toString("utf-8");
    }
    throw new Error("Unexpected response structure when fetching file");
  } else {
    // content-type为text/plain、text/*或octet-stream，直接返回
    return res.text();
  }
}
