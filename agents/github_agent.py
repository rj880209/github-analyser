"""
GitHubAnalyserAgent — orchestrates Groq LLM calls to produce a structured repo report.
"""
from __future__ import annotations

import json
from typing import Optional
from groq import Groq


SYSTEM_PROMPT = """You are an expert software engineer and code reviewer with deep knowledge of
software architecture, security, and best practices. You analyse GitHub repositories and provide
structured, actionable insights.

Always respond ONLY with valid JSON — no markdown fences, no preamble, no explanation outside the JSON.

Your JSON must match this schema exactly:
{
  "summary": "2-3 sentence executive summary of the repo",
  "purpose": "What this project does and who it's for",
  "tech_stack": ["list", "of", "technologies"],
  "architecture": {
    "pattern": "e.g. MVC, microservices, monolith, serverless",
    "description": "How the codebase is structured",
    "strengths": ["strength 1", "strength 2"],
    "concerns": ["concern 1", "concern 2"]
  },
  "code_quality": {
    "score": 7,
    "rating": "Good",
    "observations": ["observation 1", "observation 2", "observation 3"]
  },
  "security": {
    "risk_level": "Low | Medium | High | Critical",
    "findings": [
      {"severity": "High", "issue": "...", "location": "...", "recommendation": "..."}
    ]
  },
  "dependencies": {
    "total_count": 12,
    "notable": ["dep 1", "dep 2"],
    "outdated_or_risky": ["risk 1"],
    "notes": "Overall dependency health"
  },
  "documentation": {
    "score": 6,
    "has_readme": true,
    "has_contributing": false,
    "has_changelog": false,
    "suggestions": ["suggestion 1"]
  },
  "bugs_and_issues": [
    {"severity": "Medium", "description": "...", "location": "...", "fix": "..."}
  ],
  "improvements": [
    {"priority": "High", "title": "...", "description": "...", "effort": "Low | Medium | High"}
  ],
  "overall_score": 7,
  "verdict": "One punchy sentence verdict on the repo"
}
"""


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


def _trim_file_contents(file_contents: dict[str, str], token_budget: int) -> dict[str, str]:
    """
    Trim file contents to fit within a token budget.
    Keeps all files but truncates the largest ones first.
    """
    # High-value files get more space
    PRIORITY_NAMES = {
        "requirements.txt", "pyproject.toml", "package.json",
        "Dockerfile", "docker-compose.yml", "README.md",
        "setup.py", "go.mod", "Cargo.toml",
    }

    def priority(path: str) -> int:
        name = path.split("/")[-1]
        return 0 if name in PRIORITY_NAMES else 1

    sorted_files = sorted(file_contents.items(), key=lambda x: priority(x[0]))

    trimmed: dict[str, str] = {}
    used_tokens = 0

    for path, content in sorted_files:
        if used_tokens >= token_budget:
            break
        content_tokens = _estimate_tokens(content)
        remaining = token_budget - used_tokens
        if content_tokens > remaining:
            # Truncate to fit
            max_chars = remaining * 4
            content = content[:max_chars] + "\n... [truncated to fit token limit]"
        trimmed[path] = content
        used_tokens += _estimate_tokens(content)

    return trimmed


def _build_user_prompt(
    repo_meta: dict,
    file_tree: list[dict],
    file_contents: dict[str, str],
    lang_stats: dict[str, int],
    analysis_options: list[str],
    max_prompt_tokens: int = 7000,
) -> str:
    """Construct the context block sent to the LLM, respecting a token budget."""

    # Repo facts
    total_bytes = sum(lang_stats.values()) or 1
    lang_breakdown = ", ".join(
        f"{lang} ({round(b/total_bytes*100)}%)"
        for lang, b in sorted(lang_stats.items(), key=lambda x: -x[1])
    )

    tree_paths = [e["path"] for e in file_tree if e.get("type") == "blob"]
    tree_sample = "\n".join(tree_paths[:80])  # reduced from 120

    options_text = ", ".join(o.split(" ", 1)[-1] for o in analysis_options)

    # Build the static header first to see how many tokens it uses
    header = f"""## Repository: {repo_meta.get('full_name', 'Unknown')}

**Description**: {repo_meta.get('description') or 'Not provided'}
**Stars**: {repo_meta.get('stargazers_count', 0):,}   **Forks**: {repo_meta.get('forks_count', 0):,}
**Open issues**: {repo_meta.get('open_issues_count', 0)}   **Watchers**: {repo_meta.get('watchers_count', 0):,}
**Default branch**: {repo_meta.get('default_branch', 'main')}
**Created**: {repo_meta.get('created_at', '')[:10]}   **Last push**: {repo_meta.get('pushed_at', '')[:10]}
**License**: {(repo_meta.get('license') or {}).get('name', 'None')}
**Topics**: {', '.join(repo_meta.get('topics', [])) or 'None'}
**Language stats**: {lang_breakdown}
**Total files indexed**: {len(tree_paths)}

## File tree (sample)
```
{tree_sample}
```

Please analyse the repository focusing on: **{options_text}**.
Provide a thorough, expert analysis in the specified JSON format.
Be specific — cite actual file names and code patterns you observe.
"""

    header_tokens = _estimate_tokens(header)
    # Reserve tokens for system prompt (~800) + response (~1500) + header + buffer
    files_budget = max_prompt_tokens - header_tokens - 800 - 1500 - 200

    trimmed_contents = _trim_file_contents(file_contents, max(files_budget, 1000))

    files_block = ""
    for path, content in trimmed_contents.items():
        files_block += f"\n\n### {path}\n```\n{content}\n```"

    return header.replace(
        "Please analyse the repository focusing on:",
        f"\n## Key file contents{files_block}\n\n---\n\nPlease analyse the repository focusing on:"
    ).strip()


# Groq on-demand TPM limits per model (conservative, leaving room for response)
MODEL_PROMPT_TOKEN_LIMITS = {
    "llama-3.3-70b-versatile": 7000,
    "llama-3.1-8b-instant":    14000,
    "mixtral-8x7b-32768":      28000,
}
DEFAULT_PROMPT_LIMIT = 7000


class GitHubAnalyserAgent:
    def __init__(
        self,
        groq_api_key: str,
        model: str,
        github_client,
        max_files: int = 20,
    ):
        self.client = Groq(api_key=groq_api_key)
        self.model = model
        self.github_client = github_client
        self.max_files = max_files
        self.prompt_token_limit = MODEL_PROMPT_TOKEN_LIMITS.get(model, DEFAULT_PROMPT_LIMIT)

    def _call_groq(self, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
        )
        return response.choices[0].message.content.strip()

    def analyse(
        self,
        repo_meta: dict,
        file_tree: list[dict],
        file_contents: dict[str, str],
        lang_stats: dict[str, int],
        analysis_options: list[str],
    ) -> dict:
        """Run the full analysis and return a parsed report dict."""

        # Try with full budget; fall back to 50% then 30% if still too large
        for budget_fraction in [1.0, 0.5, 0.3]:
            budget = int(self.prompt_token_limit * budget_fraction)
            user_prompt = _build_user_prompt(
                repo_meta, file_tree, file_contents, lang_stats,
                analysis_options, max_prompt_tokens=budget,
            )
            estimated = _estimate_tokens(user_prompt) + _estimate_tokens(SYSTEM_PROMPT)
            if estimated <= self.prompt_token_limit:
                break
        else:
            # Last resort: strip file contents entirely
            user_prompt = _build_user_prompt(
                repo_meta, file_tree, {}, lang_stats,
                analysis_options, max_prompt_tokens=3000,
            )

        try:
            raw = self._call_groq(user_prompt)
        except Exception as e:
            err = str(e)
            if "413" in err or "rate_limit" in err or "too large" in err.lower():
                # Hard retry: drop all file contents
                user_prompt = _build_user_prompt(
                    repo_meta, file_tree, {}, lang_stats,
                    analysis_options, max_prompt_tokens=3000,
                )
                raw = self._call_groq(user_prompt)
            else:
                raise

        # Strip accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("`").strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw_response": raw, "parse_error": True}
