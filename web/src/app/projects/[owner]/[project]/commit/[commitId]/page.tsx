import { getServerSession } from "next-auth";
import { defaultAuthOptions } from "@/auth";
import prisma from "@/lib/prisma";
import { fetchGithubFileContent } from "@/lib/github";
import { createHighlighter } from "shiki";
import { SecurityFinding } from "@/types/project";
import { Card, Space } from "antd";
import Title from "antd/es/typography/Title";
import CodeBlockWithPopover from "@/app/projects/[owner]/[project]/commit/[commitId]/components/CodeBlock";
import './shiki.css'

let _highlighter: Awaited<ReturnType<typeof createHighlighter>> | null = null;

async function getHighlighterInstance() {
    if (!_highlighter) {
        _highlighter = await createHighlighter({
            langs: ["typescript", "javascript", "tsx", "jsx", "python", "java", "go"],
            themes: ["github-light"],
        });
    }
    return _highlighter;
}

export default async function SecurityPage({ params }: {
    params: Promise<{ commitId: string; owner: string; project: string }>;
}) {
    const { commitId } = await params;
    const session = await getServerSession(defaultAuthOptions);
    const accessToken = session?.accessToken;
    const codeReviewResult = await prisma.codeReviewResult.findUnique({
        where: { id: BigInt(commitId) },
    });

    if (!codeReviewResult) return <div>Code review result not found</div>;
    const { branch, repo, security_result } = codeReviewResult;
    if (!branch || !repo || !accessToken) return <div>Invalid commit</div>;

    const parsedSecurityResult = JSON.parse(JSON.stringify(security_result)) as SecurityFinding[];
    const highlighter = await getHighlighterInstance();

    const fileHtmlList = await Promise.all(
        parsedSecurityResult.map(async (securityResult) => {
            const content = await fetchGithubFileContent({
                repo,
                branch,
                path: securityResult.file,
                token: accessToken!,
            });

            const lang = securityResult.file.split(".").pop() || "plaintext";

            const html = highlighter.codeToHtml(content, {
                lang,
                theme: "github-light",
                transformers: [
                    {
                        line(node, line) {
                            if (securityResult.line === line) {
                                this.addClassToHast(node, "code-unsafe");
                                node.properties["data-info"] = JSON.stringify({
                                    severity: securityResult.severity,
                                    description: securityResult.description,
                                    recommendation: securityResult.recommendation,
                                });
                            }
                        },
                    },
                ],
            });

            return { file: securityResult.file, html };
        })
    );

    return (
        <div>
            <Space style={{ padding: "10px", marginBottom: "1em" }}>
                <Title level={5} style={{ margin: 0 }}>
                    {`${parsedSecurityResult.length} issue${parsedSecurityResult.length < 2 ? "" : "s"} found`}
                </Title>
            </Space>

            {fileHtmlList.length === 0 ? (
                <div>没有检测到安全问题文件</div>
            ) : (
                fileHtmlList.map(({ file, html }) => (
                    <Card
                        key={file}
                        title={<code style={{ fontSize: 14, fontWeight: 400 }}>{file}</code>}
                        style={{ marginBottom: 16 }}
                    >
                        <CodeBlockWithPopover html={html} />
                    </Card>
                ))
            )}
        </div>
    );
}
