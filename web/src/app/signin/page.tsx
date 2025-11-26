"use client";

import dynamic from "next/dynamic";
const Authorization = dynamic(() => import("./components/Authorization"), { ssr: false });
export default function SignInPage() {
  return <Authorization />;
}


