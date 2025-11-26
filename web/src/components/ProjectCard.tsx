"use client";

import React from "react";
import { Card, Flex, Tooltip, Typography, Tag, App, Space } from "antd";
import type { Project } from "@/types/project";
import dayjs from "dayjs";
import { useRouter } from "next/navigation";
import { CopyOutlined, GithubOutlined, InfoCircleOutlined, PlusCircleOutlined } from "@ant-design/icons";
import useProjectCardStyles from "./ProjectCard.styles";
import { WEBHOOK_URL } from "./config";

type ProjectCardProps = {
  project: Project;
};


export default function ProjectCard({ project }: ProjectCardProps) {
  const router = useRouter();
  const { styles } = useProjectCardStyles({ hasConfiged: project.hasConfiged ?? false });


  const { modal, message } = App.useApp();
  const handleCardClick = () => {
    if (project.hasConfiged) {
      router.push(`/projects/${project.owner}/${project.id}`);
      return;
    }
    modal.info({
      title: "添加项目",
      content: (() => {
        return (
          <Space direction="vertical">
            <Typography.Text type="secondary">
              请先配置 Webhook
            </Typography.Text>
            <Space>
              <Typography.Text type="secondary">
                {`api url: ${WEBHOOK_URL}`}
              </Typography.Text>
              <CopyOutlined onClick={() => {
                navigator.clipboard.writeText(WEBHOOK_URL);
                message.success(`copied`);
              }} />
            </Space>
          </Space>
        )
      })(),
      okText: "去配置 Webhook",
      cancelText: "取消",
      icon: <InfoCircleOutlined className={styles.icon} />,
      onOk: () => {
        window.open(project.webhookSettingsUrl || "", "_blank");
      },
      onCancel: () => {
        return false;
      }
    })

  };
  return (
    <Card
      hoverable
      onClick={handleCardClick}
      className={styles.card}
      title={
        <Flex align="center" justify="space-between">
          <Flex align="center" gap={8} className={styles.headerLeft}>
            <Tag className={styles.tag} >
              {project.hasConfiged ? "已配置" : "未配置"}
            </Tag>
            <Typography.Text strong className={styles.ellipsis}>
              <Tooltip title={project.name}>
                {project.name}
              </Tooltip>
            </Typography.Text>
          </Flex>
          <Flex align="center" gap={12} onClick={(e) => e.stopPropagation()}>
            {/** GitHub repo link icon */}
            <a
              href={project.repoUrl || (project.owner && project.repo ? `https://github.com/${project.owner}/${project.repo}` : "#")}
              target="_blank"
              rel="noreferrer"
              aria-label="Open GitHub repository"
              onClick={(e) => {
                if (!project.repoUrl && !(project.owner && project.repo)) e.preventDefault();
              }}
            >
              <Tooltip title="GitHub">
                <GithubOutlined className={styles.icon} />
              </Tooltip>
            </a>

            {!project.hasConfiged && (
              <a
                href={project.webhookSettingsUrl ? `${project.webhookSettingsUrl}/new` : (project.owner && project.repo ? `https://github.com/${project.owner}/${project.repo}/settings/hooks/new` : "#")}
                target="_blank"
                rel="noreferrer"
                aria-label="Configure webhook"
                onClick={(e) => {
                  if (!project.webhookSettingsUrl && !(project.owner && project.repo)) e.preventDefault();
                }}
              >
                <Tooltip title="配置 Webhook">
                  <PlusCircleOutlined className={styles.icon} />
                </Tooltip>
              </a>
            )}
          </Flex>
        </Flex>
      }
    >
      <Flex vertical gap={8} justify='space-between' className={styles.content}>
        <Typography.Paragraph className={styles.description}>
          {project.description || "暂无描述"}
        </Typography.Paragraph>
        <Typography.Text type="secondary">
          最近更新：{dayjs(project.updatedAt).format("YYYY-MM-DD HH:mm")}
        </Typography.Text>
      </Flex>
    </Card>
  );
}


