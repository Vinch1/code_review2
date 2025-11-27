# -*- coding: utf-8 -*-
"""
外盒轮询线程
- 提供单一接口 start_outbox_poller(interval_sec=15-轮询间隔秒, batch_size=10)
- 主进程只需在启动处调用一次，无需其它改动
"""
import logging, threading, time
from datetime import datetime, timedelta
from typing import List, Optional
from Backend.db.code_review_store import CodeReviewResult, SessionLocal as ReviewSession
from Backend.db.notification_outbox_repo import (
    NotificationOutbox, SessionLocal as OutboxSession, NotificationOutboxRepo
)

from .sender import default_sender
from .formatter import build_summary_card, build_security_card
from .map_review import build_summary_text, build_security_text

logger = logging.getLogger("feishu.outbox")

# ===================== 内部工具 =====================

def _compose_report_url(repo: Optional[str], pr_number: Optional[int]) -> Optional[str]:
    """优先拼 GitHub PR 链接；无效则返回 None"""
    if repo and pr_number and "/" in str(repo):
        return f"https://github.com/{repo}/pull/{pr_number}"
    return None


def _fetch_ready_tasks(limit: int) -> List[NotificationOutbox]:
    """
    拉取一批 READY 任务（按 created_at 升序）。
    如需多实例防重，请改为 with_for_update(skip_locked=True) 或增加 CLAIMED。
    """
    db = OutboxSession()
    try:
        q = db.query(NotificationOutbox)\
              .filter(NotificationOutbox.status == "READY")\
              .order_by(NotificationOutbox.created_at.asc())\
              .limit(limit)
        return q.all()
    finally:
        db.close()


def _fetch_failed_tasks(limit: int) -> List[NotificationOutbox]:
    """拉取一批 FAILED 任务重试"""
    db = OutboxSession()
    try:
        q = db.query(NotificationOutbox)\
              .filter(NotificationOutbox.status == "FAILED")\
              .order_by(NotificationOutbox.updated_at.asc())\
              .limit(limit)
        return q.all()
    finally:
        db.close()


def _load_review_row(review_id: int) -> Optional[CodeReviewResult]:
    """按 id 回查报告库记录"""
    db = ReviewSession()
    try:
        return db.query(CodeReviewResult).filter(CodeReviewResult.id == int(review_id)).first()
    finally:
        db.close()


def _mark_sent(outbox_id: int):
    repo = NotificationOutboxRepo()
    repo.update(outbox_id, status="SENT")   # 会触发 updated_at 刷新  :contentReference[oaicite:2]{index=2}


def _mark_failed(outbox_id: int, cur_retry: int, err: str):
    repo = NotificationOutboxRepo()
    # 截断错误字符串，避免过长
    err = (err or "")[:1000]
    repo.update(outbox_id, status="FAILED", retry_count=cur_retry + 1, last_error=err)  # :contentReference[oaicite:3]{index=3}


def _gc_sent_older_than(hours: int = 1, batch: int = 200):
    """
    清理 SENT 且 updated_at 超过 hours 小时的任务，避免外盒无限增长
    """
    db = OutboxSession()
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        q = db.query(NotificationOutbox)\
              .filter(NotificationOutbox.status == "SENT")\
              .filter(NotificationOutbox.updated_at < cutoff)\
              .order_by(NotificationOutbox.updated_at.asc())\
              .limit(batch)
        to_del = q.all()
        if not to_del:
            return 0
        repo = NotificationOutboxRepo(db)
        cnt = 0
        for t in to_del:
            if repo.delete(t.id):
                cnt += 1
        return cnt
    finally:
        db.close()


def _send_two_cards_for_review(review: CodeReviewResult):
    """
    将一条审查记录转换为两张卡片并依次发送
    """
    # 组文本
    summary_text = build_summary_text(review.summary_result)
    security_text = build_security_text(review.security_result)

    # 组 meta
    repo = review.repo
    pr_number = review.pr_number
    meta = {
        "repo": repo,
        "branch": review.branch or "main",
        "author": review.author or "-",
        "pr_number": pr_number,
        "report_url": _compose_report_url(repo, pr_number),
    }

    # 发卡片
    sender = default_sender()
    sender.send_card(build_summary_card(summary_text, meta))
    sender.send_card(build_security_card(security_text, meta))


# ===================== 对外：轮询器 =====================

def _poll_once(batch_size: int = 10):
    """
    单次轮询：
    - 处理 READY
    - 处理 FAILED（再试一次）
    - 清理历史 SENT>1h
    """
    ready = _fetch_ready_tasks(batch_size)
    failed = _fetch_failed_tasks(batch_size)

    def _process(task: NotificationOutbox):
        review_id = task.aggregate_id
        try:
            row = _load_review_row(review_id)
            if not row:
                raise RuntimeError(f"review not found: id={review_id}")

            _send_two_cards_for_review(row)
            _mark_sent(task.id)
            logger.info(f"[Outbox] SENT id={task.id} review_id={review_id}")
        except Exception as e:
            _mark_failed(task.id, task.retry_count or 0, str(e))
            logger.warning(f"[Outbox] FAILED id={task.id} review_id={review_id} err={e}")

    # 先 READY 再 FAILED
    for t in ready:
        _process(t)
    for t in failed:
        _process(t)

    # 清理历史
    removed = _gc_sent_older_than(hours=1, batch=200)
    if removed:
        logger.info(f"[Outbox] GC removed {removed} SENT tasks older than 1h")


def start_outbox_poller(interval_sec: int = 15, batch_size: int = 10):
    """
    对外唯一接口：启动外盒轮询线程（daemon）。
    用法（主进程入口）：
        from feishu_demo.outbox_poller import start_outbox_poller
        stop = start_outbox_poller(interval_sec=15, batch_size=10)
    """
    stop_event = threading.Event()

    def _loop():
        logger.info(f"[Outbox] poller started: interval={interval_sec}s, batch={batch_size}")
        while not stop_event.is_set():
            try:
                _poll_once(batch_size=batch_size)
            except Exception as e:
                logger.exception(f"[Outbox] poller iteration crashed: {e}")
            # 等待 interval 或被 stop
            stop_event.wait(interval_sec)
        logger.info("[Outbox] poller stopped")

    th = threading.Thread(target=_loop, name="OutboxPoller", daemon=True)
    th.start()

    def _stop():
        stop_event.set()

    return _stop
