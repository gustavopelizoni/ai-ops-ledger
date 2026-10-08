from __future__ import annotations

import io
import re
import stat
import zipfile
from pathlib import PurePosixPath
from typing import Any, Iterable
from urllib.parse import urlparse

import requests

from agent.models import CollectedRepository, RepositoryFile, RepositoryTarget


class GitHubError(RuntimeError):
    pass


REPOSITORY_PATTERN = re.compile(r"^(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))/(?P<name>[A-Za-z0-9_.-]{1,100})$")
ALLOWED_ARCHIVE_HOSTS = {"api.github.com", "codeload.github.com"}


def parse_repository(value: str) -> tuple[str, str]:
    match = REPOSITORY_PATTERN.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Invalid repository '{value}'. Expected owner/repository.")
    return match.group("owner"), match.group("name")


def read_repository_list(path: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    with open(path, encoding="utf-8") as source:
        for number, raw in enumerate(source, start=1):
            value = raw.strip()
            if not value or value.startswith("#"):
                continue
            try:
                owner, name = parse_repository(value)
            except ValueError as error:
                raise ValueError(f"{path}:{number}: {error}") from error
            canonical = f"{owner}/{name}".lower()
            if canonical not in seen:
                seen.add(canonical)
                values.append(f"{owner}/{name}")
    if not values:
        raise ValueError(f"{path} does not contain any repositories")
    return values


class GitHubCollector:
    def __init__(self, token: str | None, timeout: int, scope: dict[str, Any]) -> None:
        self.timeout, self.scope = timeout, scope
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "hermes-agentic-auditor"})
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        except requests.RequestException as error:
            raise GitHubError(f"GitHub request failed: {error}") from error
        if response.status_code == 404:
            raise GitHubError("Repository was not found or is not publicly accessible")
        if response.status_code in {403, 429}:
            raise GitHubError("GitHub API rate limit or access restriction encountered")
        try:
            response.raise_for_status()
        except requests.RequestException as error:
            raise GitHubError(f"GitHub API returned {response.status_code}") from error
        return response

    @staticmethod
    def _target(data: dict[str, Any], mode: str) -> RepositoryTarget:
        if data.get("private"):
            raise GitHubError("Private repositories are out of scope for this MVP")
        full_name = data.get("full_name", "")
        try:
            owner, name = parse_repository(full_name)
        except ValueError as error:
            raise GitHubError("GitHub returned an invalid repository identity") from error
        return RepositoryTarget(
            owner=owner,
            name=name,
            url=data["html_url"],
            selection_mode=mode,
            github_id=data.get("id"),
            default_branch=data.get("default_branch"),
        )

    def validate(self, repository: str, mode: str = "explicit") -> RepositoryTarget:
        owner, name = parse_repository(repository)
        data = self._request("GET", f"https://api.github.com/repos/{owner}/{name}").json()
        return self._target(data, mode)

    def validate_all(self, repositories: Iterable[str]) -> list[RepositoryTarget]:
        """Validate all targets before any archive collection starts."""
        return [self.validate(repository, "explicit") for repository in repositories]

    def search(self, query: str, limit: int, sort: str = "stars") -> list[RepositoryTarget]:
        if not query.strip():
            raise ValueError("--search cannot be empty")
        if not 1 <= limit <= 100:
            raise ValueError("--limit must be between 1 and 100")
        params = {"q": query, "per_page": limit, "sort": sort, "order": "desc"}
        data = self._request("GET", "https://api.github.com/search/repositories", params=params).json()
        return [self._target(item, "discovery") for item in data.get("items", [])[:limit] if not item.get("private")]

    def pin(self, target: RepositoryTarget) -> RepositoryTarget:
        data = self._request("GET", f"https://api.github.com/repos/{target.full_name}/commits/{target.default_branch}").json()
        sha = data.get("sha")
        if not isinstance(sha, str) or not sha:
            raise GitHubError(f"Could not resolve a commit SHA for {target.full_name}")
        return RepositoryTarget(**({**target.__dict__, "commit_sha": sha}))

    def collect(self, target: RepositoryTarget) -> CollectedRepository:
        pinned = target if target.commit_sha else self.pin(target)
        response = self._request("GET", f"https://api.github.com/repos/{pinned.full_name}/zipball/{pinned.commit_sha}", stream=True)
        host = urlparse(response.url).hostname
        if host not in ALLOWED_ARCHIVE_HOSTS:
            raise GitHubError("Archive redirect target is not an approved GitHub host")
        max_bytes = int(self.scope["limits"]["max_repository_size_mb"]) * 1024 * 1024
        payload = io.BytesIO()
        total = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            total += len(chunk)
            if total > max_bytes:
                raise GitHubError("Archive exceeds configured compressed size limit")
            payload.write(chunk)
        files = self._safe_files(payload.getvalue())
        return CollectedRepository(target=pinned, files=files, metadata={"archive_bytes": total, "commit_sha": pinned.commit_sha})

    def _safe_files(self, payload: bytes) -> list[RepositoryFile]:
        limits = self.scope["limits"]
        ignored = set(self.scope["ignored_directories"])
        extensions = set(self.scope["allowed_extensions"])
        try:
            archive = zipfile.ZipFile(io.BytesIO(payload))
        except zipfile.BadZipFile as error:
            raise GitHubError("GitHub archive is not a valid zip file") from error
        infos = archive.infolist()
        if len(infos) > int(limits["max_archive_members"]):
            raise GitHubError("Archive has too many members")
        uncompressed = sum(info.file_size for info in infos)
        if uncompressed > int(limits["max_repository_size_mb"]) * 1024 * 1024:
            raise GitHubError("Archive exceeds configured uncompressed size limit")
        if uncompressed and uncompressed / max(len(payload), 1) > int(limits["max_compression_ratio"]):
            raise GitHubError("Archive compression ratio exceeds configured limit")
        result: list[RepositoryFile] = []
        per_file = int(limits["max_file_size_kb"]) * 1024
        for info in infos:
            path = PurePosixPath(info.filename)
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise GitHubError("Unsafe archive path")
            if stat.S_ISLNK(info.external_attr >> 16):
                raise GitHubError("Symlinks are not permitted in repository archives")
            relative = PurePosixPath(*path.parts[1:])  # GitHub zipball has one root directory.
            if not relative.parts or any(part in ignored for part in relative.parts):
                continue
            if relative.suffix.lower() not in extensions or info.file_size > per_file or info.is_dir():
                continue
            raw = archive.read(info)
            try:
                content = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            result.append(RepositoryFile(path=relative.as_posix(), content=content, size=info.file_size))
        return result
