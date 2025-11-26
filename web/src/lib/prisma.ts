import { PrismaClient,Prisma } from '@prisma/client';



const globalForPrisma = global as unknown as { prisma?: PrismaClient };

export const prisma =
  globalForPrisma.prisma ||
  new PrismaClient({
    log: ["error", "warn"],
  });

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;

// const serialzeExtensions = Prisma.defineExtension({
//   result: {
//     serialize: (result: any) => {
//       return JSON.parse(JSON.stringify(result, (_, v) => typeof v === "bigint" ? v.toString() : v));
//     }
//   }
// });
// prisma.$extends(serialzeExtensions);
export default prisma;