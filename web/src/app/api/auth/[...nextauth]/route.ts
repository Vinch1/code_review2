import NextAuth from "next-auth";
import { defaultAuthOptions } from "@/auth";

const handler = NextAuth(defaultAuthOptions);

export { handler as GET, handler as POST } ;


