import { getServerSession } from "next-auth";
import { defaultAuthOptions } from "@/auth";

async function getAccessTokenFromSession(): Promise<string | undefined> {
  const session = await getServerSession(defaultAuthOptions);
  if (!session) return undefined;

  let token: string | undefined = session.accessToken as string | undefined;
  if (token) return token;

  const maybeAccounts = (session.user as unknown as { accounts?: Array<{ provider: string; access_token?: string }> })?.accounts;
  if (Array.isArray(maybeAccounts)) {
    const githubAccount = maybeAccounts.find((acc) => acc.provider === "github" && acc.access_token);
    if (githubAccount?.access_token) {
      token = githubAccount.access_token;
    }
  }
  return token;
}

/**
 * Resolve a GitHub access token from the current session or fallback env vars.
 * Throws if no suitable token is available.
 */
export async function requireGithubAccessToken(): Promise<string> {
  const tokenFromSession = await getAccessTokenFromSession();
  const fallbackTokens = [
    tokenFromSession,
    process.env.GITHUB_PERSONAL_TOKEN,
    process.env.GITHUB_TOKEN,
  ].filter((v): v is string => Boolean(v && v.length > 0));

  const token = fallbackTokens[0];
  if (!token) {
    throw new Error("无法获取 GitHub Access Token，请重新登录或配置 GITHUB_TOKEN");
  }
  return token;
}



