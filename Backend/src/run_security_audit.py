import os, sys, json
pwdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(pwdir, ".."))
from typing import Dict, Any
from src.init_github_client import initialize_clients
from src.init_findings_filter import initialize_findings_filter
from utils.api_protocol import *
from utils.log import logger
from src.prompts.security_audit_prompt import get_security_audit_prompt
from src.core.security_audit_core import apply_findings_filter
github_client, claude_runner = initialize_clients()

def audit_analysis(item_data) -> Dict[str, Any]:
    items = AuditReq(**item_data)
    custom_filtering_instructions = items.filter_instruction
    try:
        findings_filter = initialize_findings_filter(custom_filtering_instructions)
        logger.info("findings_filter init success")
    except Exception as e:
        logger.error(json.dumps({'error': str(e)}))

    custom_scan_instructions = items.scan_instruction
    repo_name, pr_number = items.repo_name, items.pr_number
    try:
        pr_diff = github_client.get_pr_diff(repo_name, pr_number)
        pr_data = github_client.get_pr_data(repo_name, pr_number)
        # logger.info(f"pr_data: {pr_data}")
        if pr_diff and pr_data:
            logger.info("get pr successs")
    except Exception as e:
        logger.error(json.dumps({'error': f'Failed to fetch PR data: {str(e)}'}))

    prompt = get_security_audit_prompt(pr_data, pr_diff, custom_scan_instructions=custom_scan_instructions)
    success, error_msg, results = claude_runner.run_security_audit(prompt)
    logger.info(f"success?: {success}, error_msg: {error_msg}")
    logger.info(f"results from run_security_audit: {results}")

    if not success and error_msg == "PROMPT_TOO_LONG":
        logger.error(f"[Info] Prompt too long, retrying without diff. Original prompt length: {len(prompt)} characters", file=sys.stderr)
        prompt_without_diff = get_security_audit_prompt(pr_data, pr_diff, include_diff=False, custom_scan_instructions=custom_scan_instructions)
        logger.error(f"[Info] New prompt length: {len(prompt_without_diff)} characters", file=sys.stderr)
        success, error_msg, results = claude_runner.run_security_audit(prompt_without_diff)
    if not success:
        logger.error(json.dumps({'error': f'Security audit failed: {error_msg}'}))

    # Filter findings to reduce false positives
    original_findings = results.get('findings', [])
    logger.info(f"Original findings: {original_findings}")
    # Prepare PR context for better filtering
    pr_context = {
        'repo_name': repo_name,
        'pr_number': pr_number,
        'title': pr_data.get('title', ''),
        'description': pr_data.get('body', '')
    }
    # Apply findings filter (including final directory exclusion)
    kept_findings, excluded_findings, analysis_summary = apply_findings_filter(
        findings_filter, original_findings, pr_context, github_client
    )

    output = {
            'pr_number': pr_number,
            'repo': repo_name,
            'findings': kept_findings,
            'analysis_summary': results.get('analysis_summary', {}),
            'filtering_summary': {
                'total_original_findings': len(original_findings),
                'excluded_findings': len(excluded_findings),
                'kept_findings': len(kept_findings),
                'filter_analysis': analysis_summary,
                'excluded_findings_details': excluded_findings  # Include full details of what was filtered
            }
        }
    response = AuditResp(
        pr_number=output['pr_number'],
        repo=output['repo'],
        findings=output['findings'],
        analysis_summary=output['analysis_summary'],
        filtering_summary=output['filtering_summary']
    )
    res_data = response.model_dump(exclude_unset=True)
    return res_data