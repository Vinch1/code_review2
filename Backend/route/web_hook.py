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

    # check if the pull request is related to security
    related_json = is_security_related(repo_name, pr_number)
    # if not success:
    #     logger.error(f"failed to check if pr{pr_number} is related to security")
    #     return get_response(500, "", "is_security_related failed")

    if related_json['is_security']:
        logger.info(f"pr{pr_number} is related to security because {related_json['reason']}")
        # call the security audit svr
        request_body = {
            "filter_instruction": "",
            "scan_instruction": "",
            "repo_name": repo_name,
            "pr_number": pr_number
        }
        logger.info(f"request body: {request_body}")
        resp = post_to_security_audit_srv(data=request_body)
        findings = resp['data']['security_audit_res']['findings']
        for finding in findings:
            text_to_db += finding['category'] + ": " + finding['description'] + "\n" + finding['recommendation'] + "\n"
        logger.info(f"extract svr response: {text_to_db}")
    else:
        logger.info(f"pr{pr_number} is not related to security because {related_json['reason']}")

    return get_response(200, params_dict, 'success')