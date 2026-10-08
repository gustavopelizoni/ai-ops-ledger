from pathlib import Path

import pytest

from skills.github_collector import parse_repository, read_repository_list


def test_parse_repository_accepts_owner_and_name():
    assert parse_repository("langchain-ai/langchain") == ("langchain-ai", "langchain")


@pytest.mark.parametrize("value", ["repo", "owner/repo/extra", "https://github.com/a/b", "owner/"])
def test_parse_repository_rejects_non_slug(value):
    with pytest.raises(ValueError):
        parse_repository(value)


def test_read_repository_list_ignores_comments_and_deduplicates(tmp_path: Path):
    source = tmp_path / "repos.txt"
    source.write_text("# public projects\norg/repo\n\nORG/REPO\nother/project\n", encoding="utf-8")
    assert read_repository_list(str(source)) == ["org/repo", "other/project"]
