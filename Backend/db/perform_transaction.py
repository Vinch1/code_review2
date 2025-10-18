import os, sys
pwdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(pwdir, ".."))

from typing import Dict, Any
from utils.log import logger
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from db.notification_outbox_repo import NotificationOutboxRepo
from db.code_review_store import CodeReviewStore
from . import make_mysql_url



DATABASE_URL = make_mysql_url()
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def perform_code_review_and_outbox(code_review_dict: Dict[str, Any]):
    with SessionLocal() as session:
        try:
        
            store = CodeReviewStore(session)
            record_id = store.insert_result(code_review_dict)

            outbox = NotificationOutboxRepo(session)
            outbox.insert(
                aggregate_type="code_review_result",
                aggregate_id=record_id
            )
            session.commit()
            logger.info(f"Transaction completed")
        except Exception as e:
            session.rollback()  # 回滚事务
            logger.error(f"Transaction failed, rolledback error: {e}")
            raise