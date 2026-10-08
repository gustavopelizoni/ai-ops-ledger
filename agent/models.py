from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class RepositoryTarget:
    owner: str
    name: str
    url: str
    selection_mode: str
    github_id: int | None = None
    default_branch: str | None = None
    commit_sha: str | None = None

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"full_name": self.full_name}


@dataclass
class RepositoryFile:
    path: str
    content: str
    size: int


@dataclass
class CollectedRepository:
    target: RepositoryTarget
    files: list[RepositoryFile]
    metadata: dict[str, Any]


@dataclass
class SelectedFile:
    path: str
    content: str
    line_count: int
    score: int


@dataclass
class SelectedContext:
    files: list[SelectedFile]
    dependencies: list[str] = field(default_factory=list)

    def text(self) -> str:
        return "\n\n".join(f"[FILE: {item.path}]\n{item.content}" for item in self.files)

    def line_counts(self) -> dict[str, int]:
        return {item.path: item.line_count for item in self.files}
