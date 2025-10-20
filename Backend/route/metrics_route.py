import os, sys
pwdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(pwdir, ".."))
from flask import Blueprint, request
from utils.common import get_response
from utils.log import logger
from src.metrics.commit_stats_service import get_commit_stats
from src.metrics.pr_stats_service import get_pr_stats
from src.metrics.summarize_service import summarize_commits, summarize_pull_requests_batch
from src.init_llm_client import LLMClient


metrics = Blueprint('metrics', __name__)


@metrics.route('/commit_stats', methods=['GET'])
def get_commit_stats_api():
    repo = request.args.get('repo')
    since = request.args.get('since')
    until = request.args.get('until')
    bucket = request.args.get('bucket', 'day')
    branch = request.args.get('branch')
    author = request.args.get('author')
    exclude = request.args.get('exclude', '')
    exclude_dirs = [d.strip() for d in exclude.split(',') if d.strip()] if exclude else None

    if not repo or not since or not until:
        return get_response(400, '', 'params repo/since/until are required')
    try:
        data = get_commit_stats(repo, since, until, bucket=bucket, branch=branch, author=author, exclude_dirs=exclude_dirs)
        return get_response(200, data, 'success')
    except Exception as e:
        logger.exception(f"commit_stats failed: {e}")
        return get_response(500, '', f'commit_stats error: {str(e)}')


@metrics.route('/summarize_commits', methods=['POST'])
def summarize_commits_api():
    body = request.get_json(silent=True) or {}
    repo = body.get('repo')
    since = body.get('since')
    until = body.get('until')
    include_diff = bool(body.get('include_diff', False))
    max_commits_for_diff = int(body.get('max_commits_for_diff', 20))
    author = body.get('author')

    if not repo or not since or not until:
        return get_response(400, '', 'params repo/since/until are required')
    try:
        llm_client = LLMClient()
        data = summarize_commits(
            llm_client,
            repo,
            since,
            until,
            include_diff=include_diff,
            max_commits_for_diff=max_commits_for_diff,
            language='zh',
            author=author
        )
        return get_response(200, data, 'success')
    except Exception as e:
        logger.exception(f"summarize_commits failed: {e}")
        return get_response(500, '', f'summarize_commits error: {str(e)}')


@metrics.route('/summarize_prs_batch', methods=['POST'])
def summarize_prs_batch_api():
    body = request.get_json(silent=True) or {}
    repo = body.get('repo')
    pr_numbers = body.get('pr_numbers') or []
    include_diff = bool(body.get('include_diff', False))
    max_files_for_diff = int(body.get('max_files_for_diff', 20))
    max_workers = int(body.get('max_workers', 4))

    if not repo or not isinstance(pr_numbers, list) or not pr_numbers:
        return get_response(400, '', 'params repo (str) and pr_numbers (list) are required')
    try:
        llm_client = LLMClient()
        data = summarize_pull_requests_batch(
            llm_client,
            repo,
            [int(p) for p in pr_numbers],
            include_diff=include_diff,
            max_files_for_diff=max_files_for_diff,
            language='zh',
            max_workers=max_workers
        )
        return get_response(200, data, 'success')
    except Exception as e:
        logger.exception(f"summarize_prs_batch failed: {e}")
        return get_response(500, '', f'summarize_prs_batch error: {str(e)}')
@metrics.route('/pr_stats', methods=['GET'])
def get_pr_stats_api():
    repo = request.args.get('repo')
    since = request.args.get('since')
    until = request.args.get('until')
    bucket = request.args.get('bucket', 'day')
    author = request.args.get('author')

    if not repo or not since or not until:
        return get_response(400, '', 'params repo/since/until are required')
    try:
        data = get_pr_stats(repo, since, until, bucket=bucket, author=author)
        return get_response(200, data, 'success')
    except Exception as e:
        logger.exception(f"pr_stats failed: {e}")
        return get_response(500, '', f'pr_stats error: {str(e)}')
