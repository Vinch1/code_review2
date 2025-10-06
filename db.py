import os
from dotenv import load_dotenv
load_dotenv()

from urllib.parse import quote_plus
from sqlalchemy import create_engine

def make_engine():
    user = os.getenv("DB_USER", "root")
    pwd  = quote_plus(os.getenv("DB_PASSWORD", ""))
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    db   = os.getenv("DB_NAME", "metrics")
    url = f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}?charset=utf8mb4"
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)

engine = make_engine()
