"""
GitHub API client — handles all REST calls to api.github.com.
"""
from __future__ import annotations

import base64
import re
from typing import Optional
import requests

# Files we always try to read (high-signal for analysis)
PRIORITY_FILES = [
    "README.md", "README.rst", "README.txt",
    "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg",
    "package.json", "package-lock.json", "yarn.lock",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".github/workflows",
    "Makefile", ".env.example",
    "CONTRIBUTING.md", "CHANGELOG.md", "LICENSE",
]

SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".bin", ".exe", ".dll", ".so",
    ".pdf", ".lock",
}

SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java",
    ".cpp", ".c", ".h", ".cs", ".rb", ".php", ".swift", ".kt",
    ".scala", ".r", ".jl", ".lua", ".sh", ".bash", ".zsh",
    ".yaml", ".yml", ".toml", ".json", ".xml", ".html", ".css",
    ".md", ".rst", ".txt",
}


class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    # ── internal ──────────────────────────────────────────────────────────
    def _get(self, path: str, **kwargs) -> dict | list:
        url = f"{self.BASE}/{path.lstrip('/')}"
        r = self.session.get(url, timeout=15, **kwargs)
        if r.status_code == 403:
            raise RuntimeError("GitHub rate limit exceeded or access denied. Add a token for higher limits.")
        if r.status_code == 404:
            raise RuntimeError(f"Repository not found or private: {url}")
        r.raise_for_status()
        return r.json()

    # ── public methods ────────────────────────────────────────────────────
    def get_repo_metadata(self, owner: str, repo: str) -> dict:
        """Full repo object from GET /repos/{owner}/{repo}."""
        return self._get(f"repos/{owner}/{repo}")

    def get_languages(self, owner: str, repo: str) -> dict[str, int]:
        """Language bytes breakdown."""
        return self._get(f"repos/{owner}/{repo}/languages")

    def get_file_tree(self, owner: str, repo: str, branch: str = "") -> list[dict]:
        """Flat list of all blob/tree entries via git tree API (recursive)."""
        if not branch:
            meta = self.get_repo_metadata(owner, repo)
            branch = meta.get("default_branch", "main")
        data = self._get(f"repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
        return data.get("tree", [])

    def get_file_content(self, owner: str, repo: str, path: str) -> str:
        """Decode a single file's base64 content. Returns empty string on error."""
        try:
            data = self._get(f"repos/{owner}/{repo}/contents/{path}")
            if isinstance(data, list):   # directory
                return ""
            encoded = data.get("content", "")
            return base64.b64decode(encoded).decode("utf-8", errors="replace")
        except Exception:
            return ""

    def get_key_files(
        self, owner: str, repo: str, tree: list[dict], max_files: int = 20
    ) -> dict[str, str]:
        """
        Return {path: content} for the most analytically valuable files.
        Priority: known config/docs first, then source files by path depth.
        """
        blobs = [e["path"] for e in tree if e.get("type") == "blob"]

        # Exact priority matches — fixed: use precise matching to avoid
        # false positives e.g. "Makefile" wrongly matching "Makefile.win"
        selected: list[str] = []
        for pf in PRIORITY_FILES:
            matches = [
                b for b in blobs
                if b == pf                   # exact root-level match
                or b.endswith("/" + pf)      # file nested in a subdirectory
            ]
            selected.extend(m for m in matches if m not in selected)

        # Fill remaining slots with source files (shortest paths first)
        source_files = sorted(
            [
                b for b in blobs
                if b not in selected
                and any(b.endswith(ext) for ext in SOURCE_EXTENSIONS)
                and not any(b.endswith(ext) for ext in SKIP_EXTENSIONS)
                and "node_modules" not in b
                and ".git" not in b
                and "dist/" not in b
                and "build/" not in b
            ],
            key=lambda p: (p.count("/"), len(p)),
        )
        selected.extend(f for f in source_files if f not in selected)
        selected = selected[:max_files]

        contents: dict[str, str] = {}
        for path in selected:
            text = self.get_file_content(owner, repo, path)
            if text.strip():
                # Truncate very large files to keep context manageable
                contents[path] = text[:3000] + ("\n... [truncated]" if len(text) > 3000 else "")
        return contents
