from __future__ import annotations

import pytest

from skills.skill_collector import SkillCollector, SkillCollectorError


def test_validate_skill_valid_references():
    collector = SkillCollector(timeout=10, scope={})
    
    # owner/repo/path format
    target = collector.validate_skill("mattpocock/skills/setup-matt-pocock-skills")
    assert target.owner == "mattpocock"
    assert target.name == "skill-skills"
    assert target.selection_mode == "skill"
    assert "mattpocock/skills" in target.url

    # skills.sh URL format
    target2 = collector.validate_skill("https://www.skills.sh/mattpocock/skills/setup-matt-pocock-skills")
    assert target2.owner == "mattpocock"
    assert target2.selection_mode == "skill"


@pytest.mark.parametrize("value", ["", "   ", "just-one-part"])
def test_validate_skill_invalid_references(value):
    collector = SkillCollector(timeout=10, scope={})
    with pytest.raises(SkillCollectorError):
        collector.validate_skill(value)
