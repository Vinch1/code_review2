import os
import sys
pwdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(pwdir, ".."))
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.init_github_client import GitHubActionClient
from src.prompts.summarize_commits_prompt import build_summarize_commits_prompt
from src.prompts.summarize_pr_prompt import build_summarize_pr_prompt
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


def summarize_pull_request(
    llm_client,
    repo: str,
    pr_number: int,
    include_diff: bool = False,
    max_files_for_diff: int = 20,
    language: str = 'zh'
) -> Dict[str, Any]:
    """Summarize a single pull request using LLM.

    Returns structured JSON when possible; otherwise returns raw text as fallback.
    Also returns pr file-level changes for downstream usage.
    """
    try:
        pr_data = github_client.get_pr_data(repo, pr_number)
    except Exception as e:
        logger.exception(f"Failed to fetch PR data for {repo}#{pr_number}: {e}")
        return {
            'repo': repo,
            'pr_number': pr_number,
            'error': str(e),
            'summary_text': '',
            'files': []
        }

    sys_prompt, user_prompt = build_summarize_pr_prompt(
        pr_data,
        include_diff=include_diff,
        max_files_for_diff=max_files_for_diff,
        language=language
    )

    ok, text, err = llm_client.call_with_retry(user_prompt, system_prompt=sys_prompt)
    if not ok:
        return {
            'repo': repo,
            'pr_number': pr_number,
            'error': err,
            'summary_text': '',
            'files': [
                {
                    'filename': f.get('filename', ''),
                    'status': f.get('status', ''),
                    'additions': f.get('additions', 0),
                    'deletions': f.get('deletions', 0),
                }
                for f in (pr_data.get('files') or [])
            ]
        }

    success, parsed = parse_json_with_fallbacks(text, "LLM summarize PR")
    if success:
        return {
            'repo': repo,
            'pr_number': pr_number,
            'summary': parsed,
            'title': pr_data.get('title'),
            'author': pr_data.get('user'),
            'created_at': pr_data.get('created_at'),
            'files': [
                {
                    'filename': f.get('filename', ''),
                    'status': f.get('status', ''),
                    'additions': f.get('additions', 0),
                    'deletions': f.get('deletions', 0),
                }
                for f in (pr_data.get('files') or [])
            ]
        }
    else:
        return {
            'repo': repo,
            'pr_number': pr_number,
            'summary_text': text,
            'title': pr_data.get('title'),
            'author': pr_data.get('user'),
            'created_at': pr_data.get('created_at'),
            'files': [
                {
                    'filename': f.get('filename', ''),
                    'status': f.get('status', ''),
                    'additions': f.get('additions', 0),
                    'deletions': f.get('deletions', 0),
                }
                for f in (pr_data.get('files') or [])
            ]
        }


def summarize_pull_requests_batch(
    llm_client,
    repo: str,
    pr_numbers: List[int],
    include_diff: bool = False,
    max_files_for_diff: int = 20,
    language: str = 'zh',
    max_workers: int = 4
) -> Dict[str, Any]:
    """Summarize multiple PRs concurrently using LLM.

    Returns a dict with an ordered list of results aligned to the input pr_numbers.
    Each item mirrors summarize_pull_request output.
    """
    # Local import fallback in case server hot-reload missed top-level import
    try:
        ThreadPoolExecutor  # type: ignore[name-defined]
    except NameError:
        from concurrent.futures import ThreadPoolExecutor  # noqa: F401

    results: List[Dict[str, Any]] = [None] * len(pr_numbers)

    def _run_one(idx: int, pr: int) -> None:
        try:
            res = summarize_pull_request(
                llm_client,
                repo,
                int(pr),
                include_diff=include_diff,
                max_files_for_diff=max_files_for_diff,
                language=language,
            )
            results[idx] = res
        except Exception as e:
            logger.exception(f"Batch summarize failed for PR #{pr}: {e}")
            results[idx] = {
                'repo': repo,
                'pr_number': pr,
                'error': str(e),
            }

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(_run_one, i, pr) for i, pr in enumerate(pr_numbers)]
        for f in futs:
            try:
                f.result()
            except Exception:
                # Individual errors are already captured per task
                pass

    return {
        'repo': repo,
        'count': len(pr_numbers),
        'results': results
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
