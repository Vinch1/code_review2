# feishu_demo/map_review.py
from typing import Dict, Any, List
import textwrap
import json

SEV_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
SEV_NORM = {s: s for s in SEV_ORDER}
SEV_NORM.update({"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW"})

def _norm_sev(s: str) -> str:
    return SEV_NORM.get((s or "").upper(), "LOW")

def build_security_text(security_result: List[Dict[str, Any]], max_items: int = 6) -> str:
    """
    输入：security_result 为 list[dict]（你给的示例结构）
    输出：Markdown 文本，适合放入飞书卡片的 markdown 元素
    """
    if isinstance(security_result, (str, bytes)):
        security_result = json.loads(security_result)  # 兼容传字符串

    items = []
    for f in security_result or []:
        items.append({
            "file": f.get("file", "-"),
            "line": f.get("line", 0),
            "category": f.get("category", "-"),
            "severity": _norm_sev(f.get("severity")),
            "confidence": f.get("confidence"),
            "description": f.get("description", ""),
            "recommendation": f.get("recommendation", ""),
            "exploit_scenario": f.get("exploit_scenario", ""),
        })

    # 严重级优先，其次按文件/行号
    items.sort(key=lambda x: (SEV_ORDER.index(x["severity"]) if x["severity"] in SEV_ORDER else 99,
                              x["file"], x["line"]))

    lines = []
    if not items:
        return "暂无安全问题。"

    lines.append("**安全问题汇总（按严重级排序）**")
    for i, it in enumerate(items[:max_items], 1):
        head = f"{i}. **[{it['severity'].title()}] {it['category']}**  `({it['file']}:{it['line']})`"
        desc = textwrap.shorten(it["description"], width=300, placeholder="…") if it["description"] else ""
        rec  = textwrap.shorten(it["recommendation"], width=300, placeholder="…") if it["recommendation"] else ""
        lines.append(head)
        if desc:
            lines.append(f"   - 描述：{desc}")
        if rec:
            lines.append(f"   - 建议：{rec}")
        if it.get("exploit_scenario"):
            ex = textwrap.shorten(it["exploit_scenario"], width=260, placeholder="…")
            lines.append(f"   - 可能利用：{ex}")

    remain = max(0, len(items) - max_items)
    if remain:
        lines.append(f"\n> 还有 {remain} 条问题未展开，请在报告页查看。")

    return "\n".join(lines)

def build_summary_text(summary_resule: Dict[str, Any]) -> str:
    """
    输入：summary_resule（注意你当前字段名就是 resule）
    输出：Markdown 文本（概要/变更说明）
    结构严格按你给的示例：repo、files、title、author、summary.overview、summary.sections[*]
    """
    if isinstance(summary_resule, (str, bytes)):
        summary_resule = json.loads(summary_resule)

    repo = summary_resule.get("repo", "-")
    title = summary_resule.get("title", "")
    author = summary_resule.get("author", "-")
    pr_number = summary_resule.get("pr_number")

    lines = []
    header = f"**{title}**  \nRepo: `{repo}`"
    if pr_number is not None:
        header += f"   PR: **#{pr_number}**"
    header += f"   Author: **{author}**"
    lines.append(header)

    # 文件改动
    files = summary_resule.get("files", [])
    if files:
        lines.append("\n**改动文件**")
        for f in files:
            fn = f.get("filename", "-")
            st = f.get("status", "-")
            add = f.get("additions", 0)
            dele = f.get("deletions", 0)
            lines.append(f"- `{fn}`  ({st})  +{add} / -{dele}")

    # 概览
    overview = (summary_resule.get("summary", {}) or {}).get("overview")
    if overview:
        lines.append(f"\n**概览**\n> {overview}")

    # sections
    sections = (summary_resule.get("summary", {}) or {}).get("sections", [])
    for sec in sections or []:
        sec_type = sec.get("type", "section")
        lines.append(f"\n**{sec_type.title()}**")
        # bullets
        for b in sec.get("bullets", []) or []:
            lines.append(f"- {b}")
        # evidence
        evs = sec.get("evidence", []) or []
        for ev in evs:
            fs = ", ".join(ev.get("files", []) or [])
            rs = ev.get("reason", "")
            if fs or rs:
                lines.append(f"  - 证据：`{fs}` — {rs}")

    return "\n".join(lines)
