"use client";

import React from "react";
import { Divider, Flex, Space, Tabs, Timeline, Typography, theme } from "antd";
import type { PrStatsResponse } from "@/lib/pr-stats";
import CodeReviewResultList from "./components/CodeReviewResultList/codeReviewResultList";
import PrStatsDashboard from "./components/PrStatsDashboard/prStatsDashboard";
import { useProjectDetailStyles } from "./style";
import { CodeReviewResult } from "@prisma/client";
type TimelineGroup = {
  day: string;
  records: CodeReviewResult[];
};

type ProjectDetailClientProps = {
  owner: string;
  projectId: string;
  groups: TimelineGroup[];
  initialStats: PrStatsResponse | null;
  defaultSince: string;
  defaultUntil: string;
  defaultBucket: "day" | "week" | "month";
};

export default function ProjectDetailClient({
  owner,
  projectId,
  groups,
  initialStats,
  defaultSince,
  defaultUntil,
  defaultBucket,
}: ProjectDetailClientProps) {
  const { styles } = useProjectDetailStyles();
  const {
    token: { colorIcon },
  } = theme.useToken();

  const timelineContent = (
    <>
      {!groups || groups.length === 0 ? (
        <Typography.Text type="secondary">暂无提交</Typography.Text>
      ) : (
        <Timeline
          items={groups.map((g) => ({
            color: colorIcon,
            children: (
              <Space direction="vertical" className="w-full">
                <Typography.Text type="secondary">{`Commits on ${g.day}`}</Typography.Text>
                <CodeReviewResultList data={g.records} />
              </Space>
            ),
          }))}
        />
      )}
    </>
  );

  return (
    <div className="font-sans flex justify-center min-h-screen w-full">
      <div className="w-full max-w-7xl mt-16 flex flex-col gap-8">
        <Flex vertical gap={12} className="mb-6">
          <Typography.Title level={3} style={{ margin: 0 }}>
            Code Review Results
          </Typography.Title>
        </Flex>
        <Divider className={styles.divider} />
        <Tabs
          defaultActiveKey="timeline"
          items={[
            {
              key: "timeline",
              label: "评审记录",
              children: timelineContent,
            },
            {
              key: "stats",
              label: "统计图表",
              children: (
                <PrStatsDashboard
                  owner={owner}
                  project={projectId}
                  initialData={initialStats}
                  initialBucket={defaultBucket}
                  initialSince={defaultSince}
                  initialUntil={defaultUntil}
                />
              ),
            },
          ]}
        />
      </div>
    </div>
  );
}


