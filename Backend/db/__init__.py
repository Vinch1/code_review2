import os

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