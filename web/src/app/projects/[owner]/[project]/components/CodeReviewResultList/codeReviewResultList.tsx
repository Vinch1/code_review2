"use client";

import React, { useEffect, useState } from "react";
import { Avatar, Flex, List, Space, Typography, Button } from "antd";
import dayjs from "dayjs";
import type { CodeReviewResult } from "@prisma/client";
import { fetchGithubAvatarByToken } from "@/lib/github";
import { useSession } from "next-auth/react";
import useCodeReviewResultListStyles from "./style";
import { SecurityFinding } from "@/types/project";
import Link from "next/link";

type CodeReviewResultTableProps = {
  data: CodeReviewResult[];
  loading?: boolean;
};


export default function CodeReviewResultList({ data, loading }: CodeReviewResultTableProps) {
  const session = useSession();
  const accessToken = session.data?.accessToken;
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);

  useEffect(() => {
    fetchGithubAvatarByToken(accessToken as string).then((avatarUrl) => {
      setAvatarUrl(avatarUrl);
    });
  }, [accessToken]);

  const {
    styles: {
      avatar,
      listItemContent,
      listItem,
      listItemFlex,
      buttonDanger,
      buttonSafe
    }
  } = useCodeReviewResultListStyles();


  const renderListItemContent = (item: CodeReviewResult) => {

    const parsedSummaryResult = JSON.parse(JSON.stringify(item.summary_result));
    const parsedSecurityResult = JSON.parse(JSON.stringify(item.security_result)) as SecurityFinding[];

    const handleRiskyClick = (event: React.MouseEvent<HTMLElement>, securityResult: SecurityFinding[]) => {
      window.history.pushState({
        security_contents: securityResult
      }, '', `/projects/${item.repo}/commit/${item.id}`);
      window.location.reload();
    }

    return (
      <List.Item
        className={listItem}
      >
        <Flex className={listItemFlex}>
          <Space direction="vertical" className={listItemContent} >
            <Typography.Text strong>{parsedSummaryResult?.summary?.overview}</Typography.Text>
            <Space direction="horizontal" >
              <Avatar src={avatarUrl} className={avatar} />
              <Typography.Text type="secondary">{`authored By: ${item.author} at ${dayjs(item.created_at).format('YYYY-MM-DD HH:mm:ss')}`}</Typography.Text>
              {item.branch && (
                <Typography.Text type="secondary">
                  <Link
                    href={`https://github.com/${item.repo}/tree/${item.branch}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {`on branch: ${item.branch}`}
                  </Link>
                </Typography.Text>
              )}
            </Space>
          </Space>
          {parsedSecurityResult.length > 0 ? <Button type="link" danger className={buttonDanger} onClick={(evt) => handleRiskyClick(evt, parsedSecurityResult)}>risky</Button> : <Button type="link" className={buttonSafe}>safe</Button>}
        </Flex>
      </List.Item>
    );
  };
  return (

    <List<CodeReviewResult>
      dataSource={data}
      loading={loading}
      rowKey={(item) => item.id.toString()}
      itemLayout="horizontal"
      bordered
      renderItem={
        renderListItemContent
      }
    />
  );
}