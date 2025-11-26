import { withAuth } from "next-auth/middleware"
import { NextResponse } from "next/server"

export default withAuth(  
  async function middleware(req) {
  // 获取用户 token
  const token = req.nextauth.token
  if (!token) {
    const signInUrl = new URL("/signin", req.url)
    // 带上当前访问路径作为 callbackUrl
    signInUrl.searchParams.set("callbackUrl", req.nextUrl.pathname)
    return NextResponse.redirect(signInUrl)
  }

  // 已登录则继续
  return NextResponse.next()
},
{
    
    callbacks: {
      authorized: ({ token }) => !!token, // 有 token 才允许访问
    },
    pages: {
      signIn: "/signin", // 未登录跳转

    },
  })


export const config = {
  matcher: [
    "/projects/:path*",
    "/api/projects/:path*",
    "/",
  ],
};

