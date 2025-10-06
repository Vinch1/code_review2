from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from db import engine

class TaskRepo:
    @staticmethod
    def create_task(pr_info_id:str, receiver:str, send_dt:datetime,
                    template_id:str="AI审查通知", idem_key:str|None=None):
        """
        登记任务。传 idem_key 时保证幂等（已存在则返回旧记录）。
        """
        with engine.begin() as conn:
            if idem_key:
                row = conn.execute(
                    text("SELECT id, status FROM tasks WHERE idem_key=:k"),
                    {"k": idem_key}
                ).fetchone()
                if row:
                    return {"id": row.id, "status": row.status, "created": False}

            try:
                res = conn.execute(text("""
                    INSERT INTO tasks (pr_info_id, template_id, receiver, send_time, status, retry_count, idem_key)
                    VALUES (:p, :t, :r, :s, 'pending', 0, :k)
                """), {"p": pr_info_id, "t": template_id, "r": receiver, "s": send_dt, "k": idem_key})
                task_id = res.lastrowid
                return {"id": task_id, "status": "pending", "created": True}
            except IntegrityError:
                row = conn.execute(
                    text("SELECT id, status FROM tasks WHERE idem_key=:k"),
                    {"k": idem_key}
                ).fetchone()
                return {"id": row.id, "status": row.status, "created": False}

    @staticmethod
    def claim_pending(claimer:str, limit:int=10, allow_retry_lt:int|None=5):
        """
        抢占 pending 的任务（MySQL 行锁版）：
        - FOR UPDATE SKIP LOCKED 防止多 worker 重复拿
        """
        with engine.begin() as conn:
            cond_retry = "AND retry_count < :r" if allow_retry_lt is not None else ""
            params = {"limit": limit}
            if allow_retry_lt is not None:
                params["r"] = allow_retry_lt

            rows = conn.execute(text(f"""
                SELECT id
                  FROM tasks
                 WHERE status='pending' AND send_time <= NOW(6) {cond_retry}
                 ORDER BY send_time ASC
                 LIMIT :limit
                 FOR UPDATE SKIP LOCKED
            """), params).fetchall()

            if not rows:
                return []

            ids = tuple(r.id for r in rows)

            conn.execute(text("""
                UPDATE tasks SET status='in_progress', claimer=:c
                 WHERE id IN :ids
            """), {"c": claimer, "ids": ids})

            tasks = conn.execute(text("""
                SELECT id, pr_info_id, template_id, receiver, send_time, status, retry_count
                  FROM tasks WHERE id IN :ids
            """), {"ids": ids}).mappings().all()

            return tasks

    @staticmethod
    def mark_sent(task_id:int):
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE tasks SET status='sent', updated_at=NOW() WHERE id=:id
            """), {"id": task_id})

    @staticmethod
    def mark_failed(task_id:int, error_msg:str|None=None, inc_retry:bool=True):
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE tasks
                   SET status='failed',
                       retry_count = retry_count + :inc,
                       error_msg   = :err,
                       updated_at  = NOW()
                 WHERE id=:id
            """), {"id": task_id, "err": error_msg, "inc": 1 if inc_retry else 0})

# TODO: 后期补回 Outbox 模块（异步消息队列）