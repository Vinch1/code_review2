import os
import sys
pwdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(pwdir, ".."))
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.init_github_client import GitHubActionClient
from src.prompts.summarize_commits_prompt import build_summarize_commits_prompt
from utils.log import logger
from utils.json_parser import parse_json_with_fallbacks


github_client = GitHubActionClient()


def _compact_commit_record(detail: Dict[str, Any]) -> Dict[str, Any]:
    sha = detail.get('sha')
    commit = detail.get('commit') or {}
    message = commit.get('message') or ''
    title = message.splitlines()[0] if message else ''
    files = detail.get('files') or []
    return {
        'sha': sha,
        'title': title,
        'message': message,
        'files': [
            {
                'filename': f.get('filename', ''),
                'status': f.get('status', ''),
                'additions': f.get('additions', 0),
                'deletions': f.get('deletions', 0),
                # keep patch for possible diff inclusion
                'patch': f.get('patch')
            }
            for f in files
        ]
    }


def summarize_commits(
    llm_client,
    repo: str,
    since_iso: str,
    until_iso: str,
    include_diff: bool = False,
    max_commits_for_diff: int = 20,
    language: str = 'zh',
    author: Optional[str] = None
) -> Dict[str, Any]:
    """Summarize commits in a time window using LLM.

    Returns structured JSON when possible; otherwise returns raw text as fallback.
    """
    # List commits (by time window)
    commits = github_client.list_commits(repo, since_iso, until_iso, author=author)

    # Fetch details, order by size desc (add+del)
    details: List[Dict[str, Any]] = []
    for c in commits:
        sha = c.get('sha')
        try:
            det = github_client.get_commit_detail(repo, sha)
            details.append(det)
        except Exception as e:
            logger.warning(f"Failed to fetch commit detail for {sha}: {e}")

    def size_key(d):
        files = d.get('files') or []
        add = sum(int(f.get('additions', 0)) for f in files)
        dele = sum(int(f.get('deletions', 0)) for f in files)
        return add + dele

    details.sort(key=size_key, reverse=True)

    compact = [_compact_commit_record(d) for d in details]

    # Build prompt
    sys_prompt, user_prompt = build_summarize_commits_prompt(
        repo, since_iso, until_iso, compact, include_diff=include_diff, max_commits_for_diff=max_commits_for_diff, language=language
    )

    # Call LLM
    ok, text, err = llm_client.call_with_retry(user_prompt, system_prompt=sys_prompt)
    if not ok:
        return {
            'repo': repo,
            'since': since_iso,
            'until': until_iso,
            'error': err,
            'summary_text': ''
        }

    # Try to parse structured JSON
    success, parsed = parse_json_with_fallbacks(text, "LLM summarize commits")
    print(f"Summarize commits parse success={success}, parsed={parsed}")
    if success:
        return {
            'repo': repo,
            'since': since_iso,
            'until': until_iso,
            'summary': parsed
        }
    else:
        return {
            'repo': repo,
            'since': since_iso,
            'until': until_iso,
            'summary_text': text
        }


def _author_identity_from_commit(commit_obj: Dict[str, Any]) -> str:
    author = commit_obj.get('author') or {}
    login = author.get('login')
    if login:
        return login
    ca = (commit_obj.get('commit') or {}).get('author') or {}
    return ca.get('email') or ca.get('name') or 'unknown'


def _commit_day_label(commit_obj: Dict[str, Any]) -> str:
    ca = (commit_obj.get('commit') or {}).get('author') or {}
    date_str = ca.get('date') or ''
    # Normalize to ISO then to YYYY-MM-DD
    try:
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + "+00:00"
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(date_str).astimezone(timezone.utc)
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return 'unknown-date'


def summarize_commits_grouped_by_author_day(
    llm_client,
    repo: str,
    since_iso: str,
    until_iso: str,
    include_diff: bool = False,
    max_commits_for_diff: int = 10,
    language: str = 'zh',
    max_groups: int = 50,
    author: Optional[str] = None
) -> Dict[str, Any]:
    """Summarize commits grouped by (author, day).

    Returns a dict with groups list; each group contains author, date and summary.
    """
    commits = github_client.list_commits(repo, since_iso, until_iso, author=author)

    # Build map from SHA to original commit object (for author/date)
    sha_to_commit: Dict[str, Dict[str, Any]] = {}
    for c in commits:
        sha = c.get('sha')
        if sha:
            sha_to_commit[sha] = c

    # Fetch details
    details: Dict[str, Dict[str, Any]] = {}
    for c in commits:
        sha = c.get('sha')
        if not sha:
            continue
        try:
            det = github_client.get_commit_detail(repo, sha)
            details[sha] = det
        except Exception as e:
            logger.warning(f"Failed to fetch commit detail for {sha}: {e}")

    # Group by (author, day)
    from collections import defaultdict
    grouped: Dict[tuple, list] = defaultdict(list)
    for sha, det in details.items():
        c = sha_to_commit.get(sha) or {}
        author_id = _author_identity_from_commit(c)
        day_label = _commit_day_label(c)
        grouped[(author_id, day_label)].append(det)

    # Build results per group (limit groups to avoid explosion)
    groups_out: list = []
    for idx, ((author_id, day_label), dets) in enumerate(grouped.items()):
        if idx >= max_groups:
            logger.warning(f"Group limit reached: {max_groups}")
            break

        # Order commits by size desc similar to ungrouped
        def size_key(d):
            files = d.get('files') or []
            add = sum(int(f.get('additions', 0)) for f in files)
            dele = sum(int(f.get('deletions', 0)) for f in files)
            return add + dele
        dets.sort(key=size_key, reverse=True)

        compact = [_compact_commit_record(d) for d in dets]

        context_note = f"作者：{author_id}\n日期：{day_label}"
        sys_prompt, user_prompt = build_summarize_commits_prompt(
            repo,
            since_iso,
            until_iso,
            compact,
            include_diff=include_diff,
            max_commits_for_diff=max_commits_for_diff,
            language=language,
            context_note=context_note,
        )

        ok, text, err = llm_client.call_with_retry(user_prompt, system_prompt=sys_prompt)
        if not ok:
            groups_out.append({
                'author': author_id,
                'date': day_label,
                'commits': [c.get('sha') for c in dets if c.get('sha')],
                'error': err,
                'summary_text': ''
            })
            continue

        success, parsed = parse_json_with_fallbacks(text, "LLM summarize commits (grouped)")
        if success:
            groups_out.append({
                'author': author_id,
                'date': day_label,
                'commits': [c.get('sha') for c in dets if c.get('sha')],
                'summary': parsed
            })
        else:
            groups_out.append({
                'author': author_id,
                'date': day_label,
                'commits': [c.get('sha') for c in dets if c.get('sha')],
                'summary_text': text
            })

    return {
        'repo': repo,
        'since': since_iso,
        'until': until_iso,
        'group_by': 'author_day',
        'groups': groups_out
    }
