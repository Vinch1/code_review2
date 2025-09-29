# api_app/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
from uuid import uuid4
import time

app = FastAPI(title="PR Security Audit API (Mock)", version="0.1.0")

# 允许前端跨域（开发期方便联调；上线可以改成白名单）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReviewRequest(BaseModel):
    repo_url: HttpUrl
    branch: Optional[str] = "main"
    pr_number: Optional[int] = None

# 超简单的“任务存储”（内存字典，重启会清空；Demo 足够用）
TASKS: Dict[str, Dict[str, Any]] = {}

def _mock_audit(task_id: str, req: ReviewRequest):
    """模拟长任务：等两秒，然后返回一份固定的审计结果"""
    TASKS[task_id]["status"] = "running"
    time.sleep(2)

    result = {
        "pr_number": req.pr_number,
        "repo": str(req.repo_url),
        "analysis_summary": {
            "files_reviewed": 12,
            "high_severity": 1,
            "medium_severity": 2,
            "low_severity": 1,
            "review_completed": True
        },
        "findings": [
            {"file": "app.py",            "line": 42, "issue": "SQL injection risk in string-formatted query", "severity": "HIGH"},
            {"file": "utils/auth.py",     "line": 88, "issue": "Hardcoded secret key",                         "severity": "MEDIUM"},
            {"file": "handlers/upload.py","line": 31, "issue": "Missing content-type validation",              "severity": "MEDIUM"},
            {"file": "config.py",         "line": 5,  "issue": "Debug mode enabled",                           "severity": "LOW"}
        ],
        "filtering_summary": {
            "total_original_findings": 6,
            "excluded_findings": 2,
            "kept_findings": 4,
            "filter_analysis": {"directory_excluded_count": 0},
            "excluded_findings_details": [
                {"file": "generated/client.py", "issue": "Auto-generated file", "severity": "INFO"}
            ]
        }
    }

    TASKS[task_id]["status"] = "completed"
    TASKS[task_id]["result"] = result

@app.get("/health")
def health():
    return {"ok": True, "version": "0.1.0"}

@app.post("/review")
def create_review(req: ReviewRequest, bg: BackgroundTasks):
    """提交审计任务：立即返回 task_id，后台跑（这里用 mock 两秒完成）"""
    task_id = uuid4().hex
    TASKS[task_id] = {"status": "pending", "input": req.dict()}
    bg.add_task(_mock_audit, task_id, req)
    return {"task_id": task_id, "status": "pending"}

@app.get("/review/{task_id}")
def get_review(task_id: str):
    """查询任务状态/结果"""
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(404, "task_id not found")
    return task
