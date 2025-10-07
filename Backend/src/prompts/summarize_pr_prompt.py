"""Prompt builder for pull request summarization in Chinese."""
from typing import Dict, Any, Tuple


def build_summarize_pr_prompt(
    pr_data: Dict[str, Any],
    include_diff: bool = False,
    max_files_for_diff: int = 20,
    language: str = 'zh'
) -> Tuple[str, str]:
    """Return (system_prompt, user_prompt) for LLM PR summarization.

    pr_data expects keys: number, title, body, user, files [ { filename, status, additions, deletions, patch? } ]
    """
    sys_prompt = (
        "你是一位严谨的资深研发负责人。请用简体中文，"
        "对本次 Pull Request 的改动进行客观、可验证的总结。"
        "避免空洞表述，尽量引用具体文件或变更作为证据。"
        "输出必须为 JSON，且严格遵循用户要求的结构。"
    )

    files = pr_data.get('files') or []
    lines = []
    for idx, f in enumerate(files):
        filename = f.get('filename', '')
        status = f.get('status', '')
        add = int(f.get('additions', 0))
        dele = int(f.get('deletions', 0))
        lines.append(f"- {filename} | {status} | +{add} -{dele}")
        if include_diff and idx < max_files_for_diff:
            patch = f.get('patch')
            if patch:
                snippet = '\n'.join((patch or '').splitlines()[:120])
                lines.append("  ```diff\n" + snippet + "\n  ```")

    files_block = "\n".join(lines)

    title = pr_data.get('title') or ''
    body = pr_data.get('body') or ''
    number = pr_data.get('number')
    author = pr_data.get('user') or ''
    repo_full_name = (pr_data.get('head') or {}).get('repo', {}).get('full_name') or 'unknown'

    user_prompt = f"""
我需要你对 GitHub PR 的改动进行总结，并用简体中文输出 JSON。

仓库：{repo_full_name}
PR 编号：#{number}
标题：{title}
作者：{author}
说明（节选）：{body[:500]}

文件改动：
{files_block}

请输出 JSON（仅 JSON，不要多余文本/注释/Markdown），建议结构如下：
{{
  "overview": "一句话总结该 PR 的核心改动",
  "sections": [
    {{
      "type": "feature|optimization|bugfix|refactor|docs|test|chore|other",
      "bullets": ["简明要点1", "简明要点2"],
      "evidence": [
        {{"files": ["受影响文件1", "受影响文件2"], "reason": "为何归类/影响点"}}
      ]
    }}
  ]
}}

务必：
1) 用中文；2) 结论可验证；3) 仅输出合法 JSON；4) 不要包含 Markdown 代码块标记。
"""

    return sys_prompt, user_prompt

