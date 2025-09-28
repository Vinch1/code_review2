"""Prompt builder for commit summarization in Chinese."""
from typing import List, Dict, Any, Tuple, Optional


def build_summarize_commits_prompt(
    repo: str,
    since_iso: str,
    until_iso: str,
    commits: List[Dict[str, Any]],
    include_diff: bool = False,
    max_commits_for_diff: int = 20,
    max_files_per_commit: int = 5,
    language: str = 'zh',
    context_note: Optional[str] = None
) -> Tuple[str, str]:
    """Return (system_prompt, user_prompt) for LLM summarization.

    commits item shape expects keys: sha, title, message, files [{filename, additions, deletions, patch?}]
    """
    sys_prompt = (
        "你是一位高级研发负责人。请用简体中文，给出高置信度、可验证的变更总结。"
        "避免空洞表述，尽量引用具体文件或提交信息作为证据。"
        "输出必须为 JSON，且严格遵循用户要求的结构。"
    )

    # Prepare compact commit list
    lines: List[str] = []
    num = 0
    for c in commits:
        sha = c.get('sha')
        title = c.get('title') or ''
        message = c.get('message') or ''
        files = c.get('files') or []
        add = sum(int(f.get('additions', 0)) for f in files)
        dele = sum(int(f.get('deletions', 0)) for f in files)
        lines.append(f"- {sha[:7]} | +{add} -{dele} | {title}")
        if include_diff and num < max_commits_for_diff:
            for f in files[:max_files_per_commit]:
                fn = f.get('filename', '')
                fadd = f.get('additions', 0)
                fdel = f.get('deletions', 0)
                lines.append(f"  * {fn} (+{fadd}/-{fdel})")
                patch = f.get('patch')
                if patch:
                    # Keep patch short; rely on model capability without flooding tokens
                    snippet = '\n'.join(patch.splitlines()[:80])
                    lines.append("  ```diff\n" + snippet + "\n  ```")
        num += 1

    commits_block = '\n'.join(lines)

    context_block = f"\n{context_note}\n" if context_note else "\n"

    user_prompt = f"""
我需要你对 GitHub 仓库的提交进行分类与总结，并用简体中文输出 JSON 结果。

仓库：{repo}
时间范围：{since_iso} ~ {until_iso}
{context_block}

提交概览（部分字段）：
{commits_block}

请将改动归类为以下类型：
- feature（新增功能）
- optimization（性能/可维护性优化）
- bugfix（缺陷修复）
- other（无法归类的杂项）

输出要求（必须是合法 JSON，且仅输出 JSON，不要多余文本/注释/Markdown）：
{{
  "sections": [
    {{
      "type": "feature|optimization|bugfix|other",
      "bullets": ["一句话要点1", "一句话要点2"],
      "evidence": [
        {{"sha": "提交短 SHA", "files": ["受影响文件1", "受影响文件2"]}}
      ]
    }}
  ],
  "classified_commits": [
    {{"sha": "短 SHA", "category": "feature|optimization|bugfix|other", "rationale": "分类理由（一句话）"}}
  ]
}}

务必确保：
1) 用中文描述；2) 结论有据可查；3) 输出严格是 JSON；4) 不要包含 Markdown 代码块标记。
"""

    return sys_prompt, user_prompt
