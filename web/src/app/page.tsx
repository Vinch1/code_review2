import { Project } from "@/types/project";
import ProjectCardList from "./components/ProjectCardList";
import ProjectCardListLoading from "./components/ProjectCardListLoading";
import Title from "antd/es/typography/Title";
import { Result } from "antd";
import { fetchProjectsWithConfigStatus } from "@/lib/github";

export default async function Home() {
  try {
    const projects: Project[] = await fetchProjectsWithConfigStatus();
    return (
      <div className="font-sans flex justify-center min-h-screen">
        <div className="flex flex-col gap-8 row-start-2 items-center sm:items-start w-full max-w-6xl mt-16">
          <Title level={2} style={{ margin: 0 }}>
            所有项目
          </Title>
          <ProjectCardList projects={projects} fallback={<ProjectCardListLoading />} />
        </div>
      </div>
    );
  } catch (error) {
    console.error("Error fetching GitHub projects:", error);
    return (
      <Result
        status="error"
        title="加载项目失败"
        subTitle="无法获取 GitHub 项目列表，请稍后重试。"
      />
    );
  }

}
