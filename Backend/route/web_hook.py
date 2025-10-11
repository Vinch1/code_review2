import os, sys
pwdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(pwdir, ".."))
import time
from flask import Blueprint, request
from src.core.security_audit_core import is_security_related
from utils.api_protocol import *
from utils.common import get_response
from utils.log import logger
from utils.api_post import post_to_security_audit_srv
from src.init_llm_client import LLMClient
from src.metrics.summarize_service import summarize_pull_request

github_hook = Blueprint('github_hook', __name__)

@github_hook.route('/github_hook', methods=['POST'])
def svr_github_hook():
    params_dict = request.get_json()
    logger.info(f"github_hook received params: {params_dict}")
    if params_dict is None or params_dict == '':
        return get_response(400, '', 'params are None')

    pull_request = params_dict.get('pull_request')
    url = pull_request.get('url', '')
    if not url:
        logger.error(f"no url in params_dict")
        return get_response(400, "", "no url in params_dict")
    repo_name = url.split('/')[-4] + "/" + url.split('/')[-3]
    pr_number = url.split('/')[-1]
    action_time = pull_request.get("created_at", "")
    author = url.split('/')[-4]
    branch = pull_request.get("head", {}).get("ref", "")

    request_body = {
        "filter_instruction": "",
        "scan_instruction": "",
        "repo_name": repo_name,
        "pr_number": pr_number
    }
    logger.info(f"request body: {request_body}")
    #NOTE security audit step: get security_result
    resp = post_to_security_audit_srv(data=request_body)
    security_result = resp['data']['security_audit_res']['findings']
    

    #NOTE summary step: get summary_result
    try:
        llm_client = LLMClient()
        summary_result = summarize_pull_request(
            llm_client,
            repo_name,
            int(pr_number),
            include_diff=False,  # 先关闭diff以节省token，如需可切换为True
            max_files_for_diff=20,
            language='zh'
        )
    except Exception as e:
        logger.exception(f"summarize_pull_request failed: {e}")
        summary_result = {
            'repo': repo_name,
            'pr_number': pr_number,
            'error': str(e),
        }

    # 返回审计与概要信息（后续可替换为入库逻辑）
    resp_data = {
        'repo_name': repo_name,
        'pr_number': pr_number,
        'action_time': action_time,
        'author': author,
        'branch': branch,
        'security_result': security_result,
        'summary_result': summary_result,  # 包含 files: [{filename,status,additions,deletions}]
    }
    """
    from db.code_review_store import CodeReviewStore

    try:
        store = CodeReviewStore()
        store.insert_result({
            "pr_number": pr_number,
            "repo": repo_name,
            "branch": branch,
            "author": author,
            "security_result": security_result,
            "summary_result": summary_result
        })
        logger.info(f"DB write success for PR #{pr_number}")
    except Exception as e:
        logger.error(f"DB write failed: {e}")
    """
    return get_response(200, resp_data, 'success')
