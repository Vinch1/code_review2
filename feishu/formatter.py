# feishu_demo/formatter.py
from typing import Dict

def build_summary_card(summary_text: str, meta: Dict) -> Dict:
    """
    卡片1：概要/变更总览（适合发在前面）
    meta 期望键：repo, branch, author, pr_number(可选), report_url(可选)
    """
    title = f"[CodeReview] {meta.get('repo','-')}@{meta.get('branch','-')}"
    if meta.get("pr_number"):
        title += f"  #PR-{meta['pr_number']}"
    title += f"  by {meta.get('author','-')}"

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "blue",
            "title": {"tag": "plain_text", "content": title[:150]}
        },
        "elements": [
            {"tag": "markdown", "content": summary_text[:4000]},
        ]
    }
    if meta.get("report_url"):
        card["elements"].append({
            "tag": "action",
            "actions": [{
                "tag": "button",
                "text": {"tag": "plain_text", "content": "查看完整报告"},
                "type": "primary",
                "url": meta["report_url"]
            }]
        })
    return card

def build_security_card(security_text: str, meta: Dict) -> Dict:
    """
    卡片2：安全发现汇总（重点问题/建议）
    """
    title = "Security Findings · 重点风险与建议"
    subtitle = f"{meta.get('repo','-')}@{meta.get('branch','-')}"
    if meta.get("pr_number"):
        subtitle += f"  #PR-{meta['pr_number']}"

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "red",
            "title": {"tag": "plain_text", "content": title}
        },
        "elements": [
            {"tag": "markdown", "content": f"*{subtitle}*\n\n{security_text[:3800]}"},
        ]
    }
    if meta.get("report_url"):
        card["elements"].append({
            "tag": "action",
            "actions": [{
                "tag": "button",
                "text": {"tag": "plain_text", "content": "在系统中查看详情"},
                "type": "default",
                "url": meta["report_url"]
            }]
        })
    return card
