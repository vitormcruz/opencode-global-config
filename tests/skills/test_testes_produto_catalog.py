"""Catálogo de suítes por especialidade, não por executor."""

from pathlib import Path
import re

import pytest


@pytest.fixture
def catalog(repo_root: Path) -> str:
    return (repo_root / "harness-conf/skills/testes-produto-catalog/SKILL.md").read_text(
        encoding="utf-8"
    )


@pytest.fixture
def skill_frontmatter(catalog: str) -> str:
    return catalog.split("---", 2)[1]


@pytest.mark.unit
def test_catalog_description_avoids_stale_doc_path(
    skill_frontmatter: str,
) -> None:
    assert "name: testes-produto-catalog" in skill_frontmatter
    assert "/doc/README.md" not in skill_frontmatter


@pytest.mark.unit
def test_catalog_suggests_tools_by_specialty(catalog: str) -> None:
    for specialty in ("backend", "dados", "segurança", "frontend"):
        assert f"## {specialty}" in catalog
    for agent_heading in ("## eng-software", "## dba", "## qa"):
        assert agent_heading not in catalog
    assert re.search(r"^## front\s*$", catalog, re.MULTILINE) is None
    assert "testes-produto" in catalog
    assert "harness/agregar" not in catalog
    assert '"prompt"' not in catalog
    assert "docs/testes-produto.md" in catalog


@pytest.mark.unit
def test_catalog_keeps_frontend_a11y_options(catalog: str) -> None:
    assert "pa11y" in catalog
    assert "axe-core" in catalog


@pytest.mark.unit
def test_catalog_does_not_cite_plan_ids(catalog: str) -> None:
    assert re.search(r"\bD(?:[1-9]|1[0-2])\b", catalog) is None
