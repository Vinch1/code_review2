import prisma from "@/lib/prisma";
import type { CodeReviewResult } from "@prisma/client";
import dayjs from "dayjs";
import utc from 'dayjs/plugin/utc'
dayjs.extend(utc)
export type CodeReviewResultsGroupByDay = {
  day: string; // YYYY-MM-DD
  records: CodeReviewResult[];
};

export async function getCodeReviewResultsByRepo(repo: string): Promise<CodeReviewResult[]> {
  if (!repo) return [];
  return prisma.codeReviewResult.findMany({
    where: { repo },
    orderBy: { created_at: "desc" },
  });
}

export async function getCodeReviewResultsByRepoGroupedByDay(repo: string): Promise<CodeReviewResultsGroupByDay[]> {
  const rows = await getCodeReviewResultsByRepo(repo);
  const map = new Map<string, CodeReviewResult[]>();
  for (const row of rows) {
    const key = row.created_at ? dayjs(row.created_at).utc().format("YYYY-MM-DD") : "unknown";
    const list = map.get(key) || [];
    list.push(row);
    map.set(key, list);
  }
  return Array.from(map.entries())
    .sort((a, b) => (a[0] < b[0] ? 1 : -1))
    .map(([day, records]) => ({ day, records }));
}


