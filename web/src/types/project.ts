
import { CodeReviewResult } from "@prisma/client";
export type Project = {
  id: string;
  name: string;
  description: string;
  updatedAt: string; // ISO string
  status?: "success" | "warning" | "error" | "processing" | "default" | "archived" | "paused" | "active";
  hasConfiged?: boolean; // whether configured as ai-coding project
  owner?: string; // GitHub owner
  repo?: string; // GitHub repo name
  repoUrl?: string; // GitHub repository URL
  webhookSettingsUrl?: string; // GitHub webhook settings URL
};


export type GitHubRepo = {
  name: string;
  full_name: string;
  description: string | null;
  archived: boolean;
  private: boolean;
  updated_at: string;
  link: string;
};





export type SecurityFinding = {
  file: string;
  line: number;
  category: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number;
  description: string;
  recommendation: string;
  exploit_scenario?: string;
  _filter_metadata?: {
    justification: string;
    confidence_score: number;
  };
};
