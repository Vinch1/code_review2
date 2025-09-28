import os
import sys
pwdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(pwdir, ".."))
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone

from src.init_github_client import GitHubActionClient


github_client = GitHubActionClient()


def _parse_iso8601(dt_str: str) -> datetime:
    if not dt_str:
        raise ValueError("datetime string is required")
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
        year, month = start.year, start.month
        if month == 12:
            return datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        return datetime(year, month + 1, 1, tzinfo=timezone.utc)
    raise ValueError("bucket must be one of: day, week, month")


def _bucket_index(dt: datetime, timeline: List[Tuple[datetime, datetime]]) -> int:
    for i, (s, e) in enumerate(timeline):
        if s <= dt < e:
            return i
    return -1


def _parse_github_dt(dt_str: str) -> datetime:
    # GitHub returns like 2025-09-12T10:20:30Z
    if not dt_str:
        raise ValueError("GitHub datetime missing")
    if dt_str.endswith('Z'):
        dt_str = dt_str[:-1] + "+00:00"
    return datetime.fromisoformat(dt_str).astimezone(timezone.utc)


def get_pr_stats(
    repo: str,
    since: str,
    until: str,
    bucket: str = 'day',
    author: Optional[str] = None,
) -> Dict[str, Any]:
    """Aggregate PR stats per author and time bucket.

    Metrics: created_count, merged_count, closed_count per bucket and per author.
    """
    since_dt = _parse_iso8601(since)
    until_dt = _parse_iso8601(until)

    # Fetch PRs (client filters by created_at within window)
    prs = github_client.list_pull_requests(repo, state='all', author=author, since_iso=since_dt.isoformat(), until_iso=until_dt.isoformat())

    # Build timeline buckets
    timeline: List[Tuple[datetime, datetime]] = []
    cur = _bucket_floor(since_dt, bucket)
    end_limit = until_dt.astimezone(timezone.utc)
    while cur < end_limit:
        e = _bucket_end(cur, bucket)
        timeline.append((cur, e))
        cur = e

    # Initialize output structures
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

    totals = {
        'created': 0,
        'merged': 0,
        'closed': 0,
    }

    authors: Dict[str, Dict[str, Any]] = {}

    def _author_login(pr: Dict[str, Any]) -> str:
        user = pr.get('user') or {}
        return user.get('login') or 'unknown'

    # Series cell template per bucket
    def _empty_cell():
        return {'created': 0, 'merged': 0, 'closed': 0}

    # Populate stats
    for pr in prs:
        try:
            created_dt = _parse_github_dt(pr.get('created_at'))
        except Exception:
            continue
        created_idx = _bucket_index(created_dt, timeline)
        if created_idx == -1:
            continue

        login = _author_login(pr)
        if login not in authors:
            authors[login] = {
                'author': login,
                'series': [_empty_cell() for _ in timeline],
                'totals': {'created': 0, 'merged': 0, 'closed': 0},
            }

        # Created
        authors[login]['series'][created_idx]['created'] += 1
        authors[login]['totals']['created'] += 1
        totals['created'] += 1

        # Merged (if present and within window)
        merged_at = pr.get('merged_at')
        if merged_at:
            try:
                mdt = _parse_github_dt(merged_at)
                midx = _bucket_index(mdt, timeline)
                if midx != -1:
                    authors[login]['series'][midx]['merged'] += 1
                    authors[login]['totals']['merged'] += 1
                    totals['merged'] += 1
            except Exception:
                pass

        # Closed (if present and within window)
        closed_at = pr.get('closed_at')
        if closed_at:
            try:
                cdt = _parse_github_dt(closed_at)
                cidx = _bucket_index(cdt, timeline)
                if cidx != -1:
                    authors[login]['series'][cidx]['closed'] += 1
                    authors[login]['totals']['closed'] += 1
                    totals['closed'] += 1
            except Exception:
                pass

    # Order authors by merged desc, then created
    ordered_authors = sorted(
        (
            {'author': a, 'series': data['series'], 'totals': data['totals']}
            for a, data in authors.items()
        ),
        key=lambda x: (x['totals']['merged'], x['totals']['created']),
        reverse=True
    )

    return {
        'repo': repo,
        'bucket': bucket,
        'buckets': bucket_meta,
        'authors': ordered_authors,
        'totals': totals,
    }

