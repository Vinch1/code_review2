"use client";

import React from "react";
import { Row, Col, Empty } from "antd";
import ProjectCard from "@/components/ProjectCard";
import type { Project } from "@/types/project";

type ProjectCardListProps = {
  projects: Project[];
  fallback?: React.ReactNode;
};

// 每列最多三个，最少两个
export default function ProjectCardList({ projects }: ProjectCardListProps) {
  return (
    <div className="w-full">
      {projects.length === 0 ? (
        <Empty description="暂无项目" className="mt-6" />
      ) : (
        <Row
          gutter={[16, 16]}
          className="w-full mt-6"
          style={{ alignSelf: "stretch" }}
          justify="start"
        >
          {projects.map((p) => (
            <Col
              key={p.id}
              xs={12}   // 2 列
              sm={12}   // 2 列
              md={8}    // 3 列
              lg={8}    // 3 列
              xl={8}    // 3 列
              xxl={8}   // 3 列
            >
              <ProjectCard project={p} />
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
}
