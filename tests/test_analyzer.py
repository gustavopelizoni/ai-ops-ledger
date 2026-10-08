from agent.models import CollectedRepository, RepositoryFile, RepositoryTarget
from skills.code_analyzer import CodeAnalyzer


def test_analyzer_redacts_and_respects_context_limit():
    scope = {
        "limits": {"max_files": 2, "max_context_chars": 100, "max_file_size_kb": 1},
        "selection_priority": {"filenames": ["README.md"], "path_keywords": ["agent"]},
    }
    repo = CollectedRepository(
        RepositoryTarget("org", "repo", "https://github.com/org/repo", "explicit"),
        [RepositoryFile("agent.py", "token = 'super-secret'\nprint('x')", 40), RepositoryFile("README.md", "overview", 8)],
        {},
    )
    result = CodeAnalyzer(scope).select(repo)
    assert len(result.files) == 2
    assert "super-secret" not in result.text()
    assert "<REDACTED>" in result.text()
