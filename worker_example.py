import time
from repo import TaskRepo

BOT_ID = "bot-1"

def run():
    while True:
        tasks = TaskRepo.claim_pending(claimer=BOT_ID, limit=10, allow_retry_lt=5)
        if not tasks:
            time.sleep(3); continue

        for t in tasks:
            try:
                # 简化版：直接发送并把任务标记为 sent（无 outbox）
                # 1) 根据 t["pr_info_id"] 拉取审查详情
                # 2) 渲染模板并发飞书/企微
                TaskRepo.mark_sent(t["id"])
            except Exception as e:
                TaskRepo.mark_failed(t["id"], error_msg=str(e))

if __name__ == "__main__":
    run()
