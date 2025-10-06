# Task Service

从 GitHub 仓库自动获取 Pull Request (PR)，并登记到 MySQL 数据库的任务表。  
用于 Code Review 自动化系统。

---

## 运行方式

### 1️ 环境配置（`.env`）
```
MYSQL_URL=mysql+pymysql://root:123456@localhost:3306/metrics
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxx
GITHUB_OWNER=Vinch1
GITHUB_REPO=CityUSEGroup2
```

### 2️ 启动步骤
```
# 启动 Flask 服务（端口 8080）
python app.py

# 启动轮询任务（自动拉取 PR）
python github_poll.py
```

---

## 验证
终端输出：
```
✅ 登记任务 PR #17
✅ 登记任务 PR #16
```

数据库中：
```sql
SELECT id, pr_info_id, status FROM tasks;
```

---

## TODO
- [ ] 加 Outbox 机制
- [ ] 改为 .env 动态配置仓库名
- [ ] 与 Bot 模块联动
