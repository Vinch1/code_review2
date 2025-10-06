import os
from flask import Flask, request, jsonify
from datetime import datetime, timezone
from repo import TaskRepo

app = Flask(__name__)

def ok(data=None, message="ok"):
    return jsonify({"resp_code": 200, "message": message, "data": data or {}})

def err(code, etype, message, hint=None):
    return jsonify({"resp_code": code, "error": {"type": etype, "message": message, "hint": hint}}), code

@app.get("/healthz")
def healthz():
    return ok({"db_mode": "MYSQL", "time": datetime.now(timezone.utc).isoformat()})

@app.post("/api/tasks/register")
def register_task():
    body = request.get_json(force=True, silent=False)
    pr_info_id = body.get("pr_info_id")
    receiver   = body.get("receiver")
    send_time  = body.get("send_time")  # ISO8601，可不传
    idem_key   = body.get("idempotency_key")

    if not pr_info_id or not receiver:
        return err(400, "InvalidParam", "pr_info_id and receiver are required")

    if not send_time:
        send_time = datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

    # MySQL DATETIME(6) 用天真时间（无时区）
    send_dt = datetime.fromisoformat(send_time.replace("Z","+00:00")).replace(tzinfo=None)

    res = TaskRepo.create_task(
        pr_info_id=pr_info_id,
        receiver=receiver,
        send_dt=send_dt,
        template_id="AI审查通知",
        idem_key=idem_key or f"{pr_info_id}-{send_time[:19]}"
    )
    return ok({"task_id": res["id"], "status": res["status"], "created": res["created"]})

# —— 若 Bot 不想直连 DB，可用这两条内部接口（否则可以不启用）
@app.post("/internal/tasks/claim")
def internal_claim():
    body = request.get_json(force=True, silent=False)
    bot_id = body.get("bot_id")
    limit  = int(body.get("limit", 10))
    if not bot_id:
        return err(400, "InvalidParam", "bot_id required")
    tasks = TaskRepo.claim_pending(claimer=bot_id, limit=limit, allow_retry_lt=5)
    return ok({"tasks": tasks})

@app.post("/internal/tasks/complete")
def internal_complete():
    body = request.get_json(force=True, silent=False)
    task_id = body.get("id")
    status  = body.get("status")  # sent | failed
    error   = body.get("error_msg")
    if not task_id or status not in ("sent", "failed"):
        return err(400, "InvalidParam", "id & status=sent|failed required")
    if status == "sent":
        TaskRepo.mark_sent(task_id)
    else:
        TaskRepo.mark_failed(task_id, error_msg=error)
    return ok({"id": task_id, "status": status})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
