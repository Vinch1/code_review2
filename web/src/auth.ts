import { NextAuthOptions } from "next-auth";
import GitHub from "next-auth/providers/github";
export const defaultAuthOptions: NextAuthOptions = {
  providers: [
    GitHub({
      clientId: process.env.GITHUB_ID as string,
      clientSecret: process.env.GITHUB_SECRET as string,
      httpOptions:{
        timeout:parseInt(process?.env?.GITHUB_CALLBACK_TIMEOUT || '') as number ?? 10000
      }
    }),
    
  ],
  
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token
      }
      return token
    },

    // 将 access_token 暴露到 session
    async session({ session, token }) {
      session.accessToken = token.accessToken as string
      return session
    },
    async redirect({ url, baseUrl }) {
      // 优先跳转 callbackUrl（安全处理）
      if (url.startsWith("/")) return `${baseUrl}${url}`
      if (url.startsWith(baseUrl)) return url
      return baseUrl
    },
  },
  pages: {
    signIn: "/signin",
  },


};


