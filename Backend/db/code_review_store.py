import os, sys
pwdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(pwdir, ".."))
from utils.log import logger
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, JSON, TIMESTAMP, text,  desc
from sqlalchemy.orm import declarative_base, sessionmaker
from . import make_mysql_url


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

    def __init__(self, session=None):
        self.db = session if session else SessionLocal()
        Base.metadata.create_all(engine)
        # self.db = SessionLocal()

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
        self.db.flush()
        # self.db.commit()
        # self.db.refresh(obj)
        logger.info(f"[review] waiting to commit: {obj.id}")
        return obj.id

    def get_result(self, pr_number: str) -> Optional[CodeReviewResult]:
        return self.db.query(CodeReviewResult).filter_by(pr_number=str(pr_number)).first()

    def query_records(self, filters: Dict[str, Any], limit: int = 50, offset: int = 0):
        """
        根据可选条件查询记录，按 created_at DESC 排序，支持分页
        filters 支持的 key: pr_number, repo, branch, author
        """
        q = self.db.query(CodeReviewResult)

        if "pr_number" in filters:
            # 模型里 pr_number 是 Integer，这里确保转 int
            try:
                q = q.filter(CodeReviewResult.pr_number == int(filters["pr_number"]))
            except Exception:
                q = q.filter(CodeReviewResult.pr_number == filters["pr_number"])

        if "repo" in filters:
            q = q.filter(CodeReviewResult.repo == str(filters["repo"]))
        if "branch" in filters:
            q = q.filter(CodeReviewResult.branch == str(filters["branch"]))
        if "author" in filters:
            q = q.filter(CodeReviewResult.author == str(filters["author"]))

        q = q.order_by(desc(CodeReviewResult.created_at))

        if offset:
            q = q.offset(int(offset))
        if limit:
            q = q.limit(int(limit))

        return q.all()



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
