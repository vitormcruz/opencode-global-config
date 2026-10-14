"""Guards for executable skill paths documented in AGENTS.md."""

from __future__ import annotations

import re
from pathlib import Path

import pytest


@pytest.mark.unit
def test_agents_md_skill_paths_reference_existing_skills(repo_root: Path) -> None:
    """Every concrete skills/<name> path in AGENTS.md must resolve locally."""

    agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    skill_names = sorted(set(re.findall(r"skills/([a-z0-9][a-z0-9-]*)", agents)))

    for skill_name in skill_names:
        skill_file = repo_root / "harness-conf" / "skills" / skill_name / "SKILL.md"
        assert skill_file.is_file(), (
            f"AGENTS.md referencia skills/{skill_name}, "
            f"mas {skill_file} nao existe"
        )


@pytest.mark.unit
def test_agents_references_product_guidelines(repo_root: Path) -> None:
    agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")

    assert "[`docs/README.md`](docs/README.md)" in agents
    assert (repo_root / "docs" / "README.md").is_file()


@pytest.mark.unit
def test_agents_contains_specialty_tests_index_without_base_reference(
    repo_root: Path,
) -> None:
    agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")

    assert "### Testes por Especialidade" in agents
    assert "| Especialidade | Script |" in agents
    assert "testes-produto/backend" in agents
    assert "testes-produto/seguranca" in agents
    assert "Agregador: `testes-produto`" in agents
    assert (
        "[`docs/README.md#testes-por-especialidade`]"
        "(docs/README.md#testes-por-especialidade)"
    ) in agents
    assert "### Instruções por Agente" in agents
    assert "AGENTS.base.md" not in agents
