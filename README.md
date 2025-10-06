# Task Service 模块说明

本模块用于从 GitHub 仓库自动获取 Pull Request（PR）信息，  
并登记到 MySQL 数据库中的 `tasks` 表。  
它是整个 **Code Review 自动化系统** 的子服务之一，  
负责创建任务记录，供后续的 Security Audit / Bot 模块使用。

---

## 功能概述

- 定时轮询 GitHub 仓库的 Pull Requests  
- 自动登记新的 PR 任务到数据库  
- 任务数据格式统一（含 `pr_info_id`, `receiver`, `status`, `send_time` 等字段）  
- 保证幂等：同一个 PR 不会重复登记  
- 支持本地调试与未来服务器部署两种模式  

---

## 项目结构
```
tasks_service/
├─ app.py # Flask 服务入口，提供 API 和健康检查
├─ repo.py # TaskRepo：负责数据库的增删查改
├─ db.py # 数据库连接与初始化
├─ github_poll.py # 自动从 GitHub 拉取 PR 并创建任务
├─ requirements.txt # Python 依赖
├─ .env.example # 环境变量模板
└─ README.md # 模块说明文档（当前文件）
```

---

## 环境配置

### 1️ MySQL 数据库
建表语句（简化版）：
```sql
CREATE DATABASE IF NOT EXISTS metrics DEFAULT CHARACTER SET utf8mb4;
USE metrics;

CREATE TABLE IF NOT EXISTS tasks (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pr_info_id   VARCHAR(64)  NOT NULL,
  template_id  VARCHAR(32)  NOT NULL DEFAULT 'AI审查通知',
  receiver     VARCHAR(128) NOT NULL,
  send_time    DATETIME(6)  NOT NULL,
  status       ENUM('pending','in_progress','sent','failed') NOT NULL DEFAULT 'pending',
  retry_count  INT UNSIGNED NOT NULL DEFAULT 0,
  idem_key     VARCHAR(128) NULL UNIQUE,
  claimer      VARCHAR(64)  NULL,
  error_msg    VARCHAR(512) NULL,
  created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 2 环境变量 .env
```
# MySQL 连接字符串
MYSQL_URL=mysql+pymysql://root:123456@localhost:3306/metrics

# GitHub Access Token（需有 repo 权限）
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 仓库信息（当前监听测试仓库）
GITHUB_OWNER=Vinch1
GITHUB_REPO=CityUSEGroup2
```

