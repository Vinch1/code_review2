import { NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { getCodeReviewResultsByRepo, getCodeReviewResultsByRepoGroupedByDay } from "@/lib/db";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const repo = searchParams.get("repo");
    const groupBy = searchParams.get("groupBy");

    if (repo && groupBy === "day") {
      const grouped = await getCodeReviewResultsByRepoGroupedByDay(repo);
      return NextResponse.json(JSON.parse(JSON.stringify(grouped, (_, v) => typeof v === "bigint" ? v.toString() : v)));
    }

    if (repo) {
      const results = await getCodeReviewResultsByRepo(repo);
      return NextResponse.json(results);
    }

    const results = await prisma.codeReviewResult.findMany({
      orderBy: { created_at: "desc" },
      take: 100,
    });
    return NextResponse.json(results);
  } catch (error) {
    console.error("Failed to fetch results", error);
    return NextResponse.json({ error: "Failed to fetch results" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const created = await prisma.codeReviewResult.create({
      data: {
        pr_number: body.pr_number ?? null,
        repo: body.repo ?? null,
        branch: body.branch ?? null,
        author: body.author ?? null,
        security_result: body.security_result ?? null,
        summary_result: body.summary_result ?? null,
      },
    });
    return NextResponse.json(created, { status: 201 });
  } catch (error) {
    console.error("Failed to create result", error);
    return NextResponse.json({ error: "Failed to create result" }, { status: 500 });
  }
}
