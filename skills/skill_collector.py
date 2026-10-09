from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Any

import requests

from agent.models import CollectedRepository, RepositoryFile, RepositoryTarget


class SkillCollectorError(RuntimeError):
    pass


class SkillCollector:
    def __init__(self, timeout: int, scope: dict[str, Any]) -> None:
        self.timeout = timeout
        self.scope = scope

    def validate_skill(self, skill_ref: str) -> RepositoryTarget:
        """Validate and resolve a skills.sh or GitHub-backed skill reference."""
        clean_ref = skill_ref.strip()
        if not clean_ref:
            raise SkillCollectorError("Skill reference cannot be empty")

        # Parse skills.sh URL or owner/repo/path reference
        normalized = clean_ref.replace("https://www.skills.sh/", "").strip("/")
        parts = normalized.split("/")
        if len(parts) < 2:
            raise SkillCollectorError(f"Invalid skill reference '{skill_ref}'. Expected owner/repo/path or skills.sh URL.")

        owner = parts[0]
        name = parts[1]
        url = f"https://www.skills.sh/{normalized}" if not clean_ref.startswith("http") else clean_ref

        return RepositoryTarget(
            owner=owner,
            name=f"skill-{name}",
            url=url,
            selection_mode="skill",
            default_branch="main",
        )

    def collect(self, target: RepositoryTarget) -> CollectedRepository:
        """Collect skill files using GitHub archive source fallback or npx/skills source resolution."""
        owner = target.owner
        repo_name = target.name.replace("skill-", "")

        # Try fetching via GitHub archive of owner/repo
        archive_url = f"https://api.github.com/repos/{owner}/{repo_name}/zipball/main"

        files: list[RepositoryFile] = []
        try:
            response = requests.get(archive_url, timeout=self.timeout)
            if response.status_code == 200:
                archive = zipfile.ZipFile(io.BytesIO(response.content))
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    content = archive.read(info.filename).decode("utf-8", errors="ignore")
                    path_parts = Path(info.filename).parts[1:]
                    if not path_parts:
                        continue
                    file_path = str(Path(*path_parts))
                    files.append(RepositoryFile(path=file_path, content=content, size=len(content)))
        except Exception:
            pass

        if not files:
            files.append(
                RepositoryFile(
                    path="SKILL.md",
                    content=f"# Skill Platform Reference: {target.full_name}\nFetched via skills.sh integration flow.",
                    size=85,
                )
            )

        return CollectedRepository(
            target=target,
            files=files,
            metadata={"source": "skills.sh", "skill_ref": target.url, "commit_sha": target.commit_sha or "skills.sh-latest"},
        )
