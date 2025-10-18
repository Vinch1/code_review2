import os, sys
pwdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(pwdir, ".."))

from utils.log import logger
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, text
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Optional
from db.code_review_store import make_mysql_url  # 复用原有连接逻辑

DATABASE_URL = make_mysql_url()
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


# ORM 模型：notification_outbox
class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"

    id = Column(Integer, primary_key=True, autoincrement=True)
    aggregate_type = Column(String(64), nullable=False)        # e.g. "code_review_result"
    aggregate_id = Column(Integer, nullable=False)             # 对应 code_review_results.id
    status = Column(String(16), nullable=False, server_default=text("'READY'"))
    retry_count = Column(Integer, nullable=False, server_default=text("0"))
    last_error = Column(Text)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP,
                        server_default=text("CURRENT_TIMESTAMP"),
                        server_onupdate=text("CURRENT_TIMESTAMP"))


# 数据访问类
class NotificationOutboxRepo:
    """用于插入、更新、删除 notification_outbox 表"""

    def __init__(self):
        Base.metadata.create_all(engine)
        self.db = SessionLocal()

    def insert(self, aggregate_type: str, aggregate_id: int):
        """
        新增一条 outbox 记录（同步插入）
        """
        obj = NotificationOutbox(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        logger.info(f"[Outbox] insert success id={obj.id}")
        return obj.id

    def update(self, id: int, status: Optional[str] = None,
               retry_count: Optional[int] = None,
               last_error: Optional[str] = None):
        """
        更新状态。只更新传入的字段。
        """
        obj = self.db.query(NotificationOutbox).filter_by(id=id).first()
        if not obj:
            logger.warning(f"[Outbox] update failed, id={id} not found")
            return False

        if status is not None:
            obj.status = status
        if retry_count is not None:
            obj.retry_count = retry_count
        if last_error is not None:
            obj.last_error = last_error

        self.db.commit()
        logger.info(f"[Outbox] update success id={id}")
        return True

    def delete(self, id: int):
        """
        删除指定 id 的 outbox 记录。
        """
        obj = self.db.query(NotificationOutbox).filter_by(id=id).first()
        if not obj:
            logger.warning(f"[Outbox] delete failed, id={id} not found")
            return False

        self.db.delete(obj)
        self.db.commit()
        logger.info(f"[Outbox] delete success id={id}")
        return True


# 手动测试
if __name__ == "__main__":
    repo = NotificationOutboxRepo()

    # 插入测试
    pk = repo.insert("code_review_result", 1)
    print(f"插入成功 id={pk}")

    # 更新测试
    repo.update(pk, status="FAILED", retry_count=2, last_error="Timeout")

    # 删除测试
    repo.delete(pk)
