import os
import sys
pwdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(pwdir, ".."))
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone

from src.init_github_client import GitHubActionClient
from utils.log import logger


# Initialize shared clients (reuse existing initialization pattern)
github_client = GitHubActionClient()


def _parse_iso8601(dt_str: str) -> datetime:
    """Parse ISO8601 string to aware datetime (UTC if 'Z')."""
    if not dt_str:
        raise ValueError("datetime string is required")
    # Support Z suffix
    if dt_str.endswith('Z'):
        dt_str = dt_str[:-1] + "+00:00"
    return datetime.fromisoformat(dt_str)


def _format_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def _bucket_floor(dt: datetime, bucket: str) -> datetime:
    dt = dt.astimezone(timezone.utc)
    if bucket == 'day':
        return datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)
    if bucket == 'week':
        # ISO week starts Monday
        start = dt - timedelta(days=(dt.weekday()))
        return datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    if bucket == 'month':
        return datetime(dt.year, dt.month, 1, tzinfo=timezone.utc)
    raise ValueError("bucket must be one of: day, week, month")


def _bucket_end(start: datetime, bucket: str) -> datetime:
    if bucket == 'day':
        return start + timedelta(days=1)
    if bucket == 'week':
        return start + timedelta(days=7)
    if bucket == 'month':
        # naive month increment
        year, month = start.year, start.month
        if month == 12:
            return datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        return datetime(year, month + 1, 1, tzinfo=timezone.utc)
    raise ValueError("bucket must be one of: day, week, month")


def _is_merge_commit(commit_obj: Dict[str, Any]) -> bool:
    parents = commit_obj.get('parents') or []
    return len(parents) > 1


def _is_bot_commit(commit_obj: Dict[str, Any]) -> bool:
    author = commit_obj.get('author') or {}
    login = (author.get('login') or '').lower()
    user_type = (author.get('type') or '').lower()
    name = ((commit_obj.get('commit') or {}).get('author') or {}).get('name', '')
    return (
        user_type == 'bot' or
        'bot' in login or
        'bot' in (name or '').lower()
    )


def _author_identity(commit_obj: Dict[str, Any]) -> str:
    author = commit_obj.get('author') or {}
    login = author.get('login')
    if login:
        return login
    # fallback to email or name
    ca = (commit_obj.get('commit') or {}).get('author') or {}
    return ca.get('email') or ca.get('name') or 'unknown'


def _commit_datetime(commit_obj: Dict[str, Any]) -> datetime:
    ca = (commit_obj.get('commit') or {}).get('author') or {}
    dt = _parse_iso8601(ca.get('date'))
    return dt.astimezone(timezone.utc)


def _path_excluded(filepath: str, extra_excluded: Optional[List[str]]) -> bool:
    # Use client's excluded dirs first
    if github_client._is_excluded(filepath):  # type: ignore
        return True
    if extra_excluded:
        for d in extra_excluded:
            if not d:
                continue
            nd = d[2:] if d.startswith('./') else d
            if filepath.startswith(d + '/') or filepath.startswith(nd + '/') or (f'/{nd}/' in filepath):
                return True
    return False


def get_commit_stats(
    repo: str,
    since: str,
    until: str,
    bucket: str = 'day',
    branch: Optional[str] = None,
    author: Optional[str] = None,
    exclude_dirs: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Aggregate commit stats per author and time bucket.

    Returns a dict with buckets, per-author series, and totals.
    """
    try:
        since_dt = _parse_iso8601(since)
        until_dt = _parse_iso8601(until)
    except Exception as e:
        raise ValueError(f"Invalid since/until format: {e}")

    # Fetch commits list (paginated)
    commits = github_client.list_commits(repo, since_dt.isoformat(), until_dt.isoformat(), branch=branch, author=author)

    # Pre-build buckets timeline
    timeline: List[Tuple[datetime, datetime]] = []
    cur = _bucket_floor(since_dt, bucket)
    end_limit = until_dt.astimezone(timezone.utc)
    while cur < end_limit:
        e = _bucket_end(cur, bucket)
        timeline.append((cur, e))
        cur = e

    # Index map for quick bucket lookup
    def bucket_index(dt: datetime) -> int:
        for i, (s, e) in enumerate(timeline):
            if s <= dt < e:
                return i
        return -1

    authors: Dict[str, Dict[str, Any]] = {}
    totals = {
        'additions': 0,
        'deletions': 0,
        'net': 0,
        'commits_count': 0,
        'files_changed': 0,
    }

    for c in commits:
        if _is_merge_commit(c) or _is_bot_commit(c):
            continue
        cdt = _commit_datetime(c)
        idx = bucket_index(cdt)
        if idx == -1:
            continue
        sha = c.get('sha')
        try:
            detail = github_client.get_commit_detail(repo, sha)
        except Exception as e:
            logger.warning(f"Failed to fetch commit detail for {sha}: {e}")
            continue

        add, dele, files_changed = 0, 0, 0
        for f in detail.get('files', []) or []:
            path = f.get('filename', '')
            if _path_excluded(path, exclude_dirs):
                continue
            add += int(f.get('additions', 0))
            dele += int(f.get('deletions', 0))
            files_changed += 1

        if add == 0 and dele == 0:
            continue

        author_id = _author_identity(c)
        if author_id not in authors:
            # Initialize series per timeline
            authors[author_id] = {
                'author': author_id,
                'series': [
                    {'additions': 0, 'deletions': 0, 'net': 0, 'commits_count': 0, 'files_changed': 0}
                    for _ in timeline
                ],
                'totals': {'additions': 0, 'deletions': 0, 'net': 0, 'commits_count': 0, 'files_changed': 0}
            }

        cell = authors[author_id]['series'][idx]
        cell['additions'] += add
        cell['deletions'] += dele
        cell['net'] += (add - dele)
        cell['commits_count'] += 1
        cell['files_changed'] += files_changed

        t = authors[author_id]['totals']
        t['additions'] += add
        t['deletions'] += dele
        t['net'] += (add - dele)
        t['commits_count'] += 1
        t['files_changed'] += files_changed

        totals['additions'] += add
        totals['deletions'] += dele
        totals['net'] += (add - dele)
        totals['commits_count'] += 1
        totals['files_changed'] += files_changed

    bucket_meta = [
        {
            'bucket_start': _format_iso(s),
            'bucket_end': _format_iso(e),
            'label': (
                s.strftime('%Y-%m-%d') if bucket == 'day' else
                (f"{s.strftime('%Y')}-W{int(s.strftime('%V')):02d}" if bucket == 'week' else s.strftime('%Y-%m'))
            )
        }
        for (s, e) in timeline
    ]

    # Build top contributors by net
    top_contributors = sorted(
        (
            {
                'author': a,
                **data['totals'],
            }
            for a, data in authors.items()
        ),
        key=lambda x: x['net'],
        reverse=True
    )

    return {
        'repo': repo,
        'bucket': bucket,
        'buckets': bucket_meta,
        'authors': [
            {'author': a, 'series': data['series'], 'totals': data['totals']} for a, data in authors.items()
        ],
        'totals': totals,
        'top_contributors': top_contributors[:10]
    }
