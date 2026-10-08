from __future__ import annotations

import os
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    root: Path
    ollama_host: str
    model: str
    github_token: str | None
    max_llm_retries: int
    request_timeout_seconds: int
    llm_num_predict: int
    output_dir: Path

    @classmethod
    def from_environment(cls, root: Path, model: str | None = None, output_dir: str | None = None) -> "Settings":
        retries = int(os.getenv("MAX_LLM_RETRIES", "2"))
        if retries < 0 or retries > 5:
            raise ValueError("MAX_LLM_RETRIES must be between 0 and 5")
        num_predict = int(os.getenv("OLLAMA_NUM_PREDICT", "800"))
        if not 64 <= num_predict <= 4096:
            raise ValueError("OLLAMA_NUM_PREDICT must be between 64 and 4096")
        resolved_output = (root / (output_dir or os.getenv("AUDIT_OUTPUT_DIR", "site"))).resolve()
        if not resolved_output.is_relative_to(root.resolve()):
            raise ValueError("AUDIT_OUTPUT_DIR/--output must remain inside the project directory")
        return cls(
            root=root,
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/"),
            model=model or os.getenv("HERMES_MODEL", "hermes3:8b"),
            github_token=os.getenv("GITHUB_TOKEN") or None,
            max_llm_retries=retries,
            request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "45")),
            llm_num_predict=num_predict,
            output_dir=resolved_output,
        )


def scope_with_environment(scope: dict) -> dict:
    """Allow safe deployment-specific limits without changing the versioned SDD."""
    result = deepcopy(scope)
    values = {"MAX_REPOSITORY_SIZE_MB": "max_repository_size_mb", "MAX_FILE_SIZE_KB": "max_file_size_kb", "MAX_CONTEXT_CHARS": "max_context_chars"}
    for environment, key in values.items():
        if environment in os.environ:
            value = int(os.environ[environment])
            if value <= 0:
                raise ValueError(f"{environment} must be positive")
            result["limits"][key] = value
    return result
