from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / "settings" / ".env")

import os
import json
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, JSON, TIMESTAMP, text
from sqlalchemy.orm import declarative_base, sessionmaker

# 连接 MySQL
def make_mysql_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    user = os.getenv("MYSQL_USER", "root")
    pwd  = os.getenv("MYSQL_PASSWORD", "")
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    db   = os.getenv("MYSQL_DB", "code_review2")
    params = os.getenv("MYSQL_PARAMS", "charset=utf8mb4")
    return f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}?{params}"

DATABASE_URL = make_mysql_url()
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


# ORM 模型（映射到表结构）
class CodeReviewResult(Base):
    __tablename__ = "code_review_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pr_number = Column(Integer)
    repo = Column(String(255))
    branch = Column(String(255))
    author = Column(String(255))
    security_result = Column(JSON)
    summary_result = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


# 数据访问类
class CodeReviewStore:
    """用于写入 / 查询 code_review_results 表"""

    def __init__(self):
        # 表如果不存在则创建
        Base.metadata.create_all(engine)
        self.db = SessionLocal()

    def insert_result(self, data: Dict[str, Any]) -> int:
        """
        data 示例:
        {
          "pr_number": "19",
          "repo": "Vinch1/CityUSEGroup2",
          "branch": "Vinch1-patch-15",
          "author": "Vinch1",
          "security_result": [...],
          "summary_result": {...}
        }
        """
        obj = CodeReviewResult(
            pr_number=int(data.get("pr_number")),
            repo=data.get("repo"),
            branch=data.get("branch"),
            author=data.get("author"),
            security_result=data.get("security_result"),
            summary_result=data.get("summary_result"),
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj.id

    def get_result(self, pr_number: str) -> Optional[CodeReviewResult]:
        return self.db.query(CodeReviewResult).filter_by(pr_number=str(pr_number)).first()


if __name__ == "__main__":
    # 测试示例
    store = CodeReviewStore()

    sample = {
        "pr_number": "19",
        "repo": "Vinch1/CityUSEGroup2",
        "branch": "Vinch1-patch-15",
        "author": "Vinch1",
        "security_result": [
            {"file": "database.py", "line": 12, "severity": "HIGH"}
        ],
        "summary_result": {
            "overview": "更新 database.py 文件，优化连接逻辑"
        }
    }

    pk = store.insert_result(sample)
    print(f"已写入数据库，id={pk}")

    row = store.get_result("19")
    print("读取结果：", row.repo if row else "未找到")
