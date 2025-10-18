import os, sys
from typing import Any, Dict, List
from flask import Blueprint, request, jsonify

pwdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(pwdir, ".."))

from utils.log import logger
from db.code_review_store import CodeReviewStore, CodeReviewResult

commit_records = Blueprint("commit_records", __name__)

def _to_dict(row: CodeReviewResult) -> Dict[str, Any]:
    # created_at 转成 ISO 字符串
    created = None
    if hasattr(row, "created_at") and row.created_at:
        try:
            created = row.created_at.isoformat()
        except Exception:
            created = str(row.created_at)

    return {
        "pr_number": row.pr_number,
        "repo": row.repo,
        "branch": row.branch,
        "author": row.author,
        "security_result": row.security_result,
        "summary_result": row.summary_result,
        "created_at": created
    }

@commit_records.route("/get_commit_records", methods=["POST"])
def get_commit_records():
    """
    入参（全部可选，作为过滤条件）：
    {
      "pr_number": int,
      "repo": "str",
      "branch": "str",
      "author": "str",
      "limit": 50,        # 可选，默认50
      "offset": 0         # 可选，默认0
    }

    返回：[
      {
        "pr_number": int,
        "repo": "str",
        "branch": "str",
        "author": "str",
        "security_result": {... 或 [...]},
        "summary_result": {...},
        "created_at": "2025-10-18T13:05:50"
      },
      ...
    ]
    """
    body = request.get_json(silent=True) or {}
    logger.info(f"[get_commit_records] body={body}")

    # 允许的过滤字段
    filters: Dict[str, Any] = {}
    for k in ("pr_number", "repo", "branch", "author"):
        v = body.get(k, None)
        if v not in (None, ""):
            filters[k] = v

    # 简单分页
    try:
        limit = int(body.get("limit", 50))
    except Exception:
        limit = 50
    try:
        offset = int(body.get("offset", 0))
    except Exception:
        offset = 0

    try:
        store = CodeReviewStore()
        rows: List[CodeReviewResult] = store.query_records(filters, limit=limit, offset=offset)
        data = [_to_dict(r) for r in rows]
        return jsonify(data), 200
    except Exception as e:
        logger.exception(f"[get_commit_records] failed: {e}")
        return jsonify({"message": f"get_commit_records failed: {e}"}), 500
