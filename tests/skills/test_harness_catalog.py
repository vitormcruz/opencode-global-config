"""Valida o frontmatter da skill harness-catalog."""

from pathlib import Path

import pytest


@pytest.fixture
def skill_frontmatter(repo_root: Path) -> str:
    skill_content = (
        repo_root / "skills/harness-catalog/SKILL.md"
    ).read_text(encoding="utf-8")
    return skill_content.split("---", 2)[1]


@pytest.mark.unit
def test_harness_catalog_description_avoids_stale_doc_path(
    skill_frontmatter: str,
) -> None:
    assert "/doc/README.md" not in skill_frontmatter
