# Backend Metrics & Summaries API

This backend provides commit statistics and LLM‑based commit summaries for GitHub repositories.

## Prerequisites

- Python 3.10+
- Install deps: `pip install -r Backend/requirements.txt`
- Configure `Backend/settings/.env`:
  - `GITHUB_TOKEN` – GitHub token with `repo` read access
  - `API_KEY` – Tongyi (DashScope compatible) API key
  - `BASE_URL` – e.g. `https://dashscope.aliyuncs.com/compatible-mode/v1`
  - `DEFAULT_TONGYI_MODEL` – e.g. `qwen-plus-latest`
- Start server: `python Backend/server.py`
  - Served at `http://<FLASK_HOST>:<FLASK_PORT>` (defaults in `.env`).

Note: JSON responses are UTF‑8 and will show Chinese directly (no `\uXXXX`).

## Endpoints

### 1) Commit Stats (by author × time bucket)

- Method: `GET`
- Path: `/api/metrics/commit_stats`
- Query params:
  - `repo` (required) – `owner/repo`
  - `since` (required) – ISO8601, e.g. `2025-09-01T00:00:00Z`
  - `until` (required) – ISO8601
  - `bucket` – `day|week|month` (default `day`)
  - `branch` – optional branch SHA/ref
  - `author` – optional GitHub login/email to filter commits
  - `exclude` – comma‑separated dirs to exclude (in addition to `EXCLUDE_DIRECTORIES` env)

Example:

```bash
curl -s "http://localhost:8080/api/metrics/commit_stats?repo=owner/repo&since=2025-09-01T00:00:00Z&until=2025-09-28T00:00:00Z&bucket=day&author=login" | jq
```

Response highlights:

```json
{
  "resp_code": 200,
  "data": {
    "repo": "owner/repo",
    "bucket": "day",
    "buckets": [{"label": "2025-09-01", "bucket_start": "...", "bucket_end": "..."}],
    "authors": [
      {
        "author": "login",
        "series": [ {"additions": 10, "deletions": 2, "net": 8, "commits_count": 1, "files_changed": 3}, ... ],
        "totals": {"additions": 100, "deletions": 20, "net": 80, "commits_count": 12, "files_changed": 25}
      }
    ],
    "totals": {"additions": 200, "deletions": 50, "net": 150, "commits_count": 20, "files_changed": 40},
    "top_contributors": [ ... ]
  }
}
```

### 2) PR Stats (by author × time bucket)

- Method: `GET`
- Path: `/api/metrics/pr_stats`
- Query params:
  - `repo` (required)
  - `since` (required)
  - `until` (required)
  - `bucket` – `day|week|month` (default `day`)
  - `author` – optional GitHub login to filter PRs

Example:

```bash
curl -s "http://localhost:8080/api/metrics/pr_stats?repo=owner/repo&since=2025-09-01T00:00:00Z&until=2025-09-28T00:00:00Z&bucket=day&author=login" | jq
```

Response highlights:

```json
{
  "repo": "owner/repo",
  "bucket": "day",
  "buckets": [{"label": "2025-09-01", "bucket_start": "...", "bucket_end": "..."}],
  "authors": [
    {
      "author": "login",
      "series": [ {"created": 1, "merged": 0, "closed": 1}, ... ],
      "totals": {"created": 5, "merged": 3, "closed": 4}
    }
  ],
  "totals": {"created": 8, "merged": 5, "closed": 7}
}
```

Notes:
- Time window filtering is based on PR `created_at` for inclusion; `merged`/`closed` are counted if their timestamps fall in the same window.

### 3) LLM Summaries (whole window)

- Method: `POST`
- Path: `/api/metrics/summarize_commits`
- Body (JSON):

```json
{
  "repo": "owner/repo",
  "since": "2025-09-01T00:00:00Z",
  "until": "2025-09-28T00:00:00Z",
  "include_diff": true,
  "max_commits_for_diff": 20,
  "author": "login-or-email (optional)"
}
```

Example:

```bash
curl -s -X POST http://localhost:8080/api/metrics/summarize_commits \
  -H "Content-Type: application/json" \
  -d '{
    "repo":"owner/repo",
    "since":"2025-09-01T00:00:00Z",
    "until":"2025-09-28T00:00:00Z",
    "include_diff":true,
    "max_commits_for_diff":20,
    "author":"login"
  }' | jq '.data.summary'
```

Response (successfully parsed JSON):

```json
{
  "sections": [
    {"type": "feature|optimization|bugfix|other", "bullets": ["..."], "evidence": [{"sha":"...","files":["..."]}]}
  ],
  "classified_commits": [
    {"sha": "abcdef1", "category": "feature", "rationale": "..."}
  ]
}
```

If the model returns non‑JSON, you will get `summary_text` instead.

### 4) LLM Summaries Grouped by Author × Day

- Method: `POST`
- Path: `/api/metrics/summarize_commits_grouped`
- Body (JSON): same as above with additional control fields:
  - `max_groups` – limit number of `author×day` groups summarized (default 50)
  - `author` – optional author filter at source (only that author’s commits)

Example:

```bash
curl -s -X POST http://localhost:8080/api/metrics/summarize_commits_grouped \
  -H "Content-Type: application/json" \
  -d '{
    "repo":"owner/repo",
    "since":"2025-09-01T00:00:00Z",
    "until":"2025-09-28T00:00:00Z",
    "author":"login",
    "include_diff":true,
    "max_commits_for_diff":10,
    "max_groups":50
  }' | jq '.data.groups'
```

Response shape:

```json
{
  "group_by": "author_day",
  "groups": [
    {
      "author": "login",
      "date": "2025-09-12",
      "commits": ["abcdef1", "abcdef2"],
      "summary": { "sections": [...], "classified_commits": [...] }
    }
  ]
}
```

## Notes & Limits

- Grouped summaries call the LLM once per group; use `max_groups` to bound cost.
- `include_diff` attaches short diff snippets for context (limited by `max_commits_for_diff`).
- Author filter passes through to GitHub API; for unlinked commits, email may work better than login.
- UTF‑8 responses: clients like `jq` will display Chinese directly.
