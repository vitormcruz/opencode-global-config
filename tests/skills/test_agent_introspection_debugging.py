import json
from pathlib import Path

import pytest


@pytest.fixture
def skill_content(repo_root: Path) -> str:
    return (
        repo_root / "harness-conf/skills/agent-introspection-debugging/SKILL.md"
    ).read_text(encoding="utf-8")


@pytest.fixture
def upstream_content(repo_root: Path) -> str:
    return (
        repo_root
        / "harness-conf/skills/agent-introspection-debugging/UPSTREAM.md"
    ).read_text(encoding="utf-8")


@pytest.mark.unit
def test_skill_exists(repo_root: Path):
    assert (
        repo_root / "harness-conf/skills/agent-introspection-debugging/SKILL.md"
    ).is_file()


@pytest.mark.unit
def test_frontmatter_has_name_and_description(skill_content: str):
    frontmatter = skill_content.split("---", 2)[1]

    assert "name: agent-introspection-debugging" in frontmatter
    assert "description:" in frontmatter


@pytest.mark.unit
def test_description_contains_activation_triggers(skill_content: str):
    frontmatter = skill_content.split("---", 2)[1]

    for trigger in (
        "loop de ferramenta",
        "sem progresso",
        "mesma chamada",
        "repeated retries",
        "agent stuck",
        "max tool calls",
    ):
        assert trigger in frontmatter


@pytest.mark.unit
def test_skill_keeps_four_phases(skill_content: str):
    for section in (
        "## Loop de quatro fases",
        "### Fase 1: captura da falha",
        "### Fase 2: diagnóstico por padrão",
        "### Fase 3: recuperação contida",
        "### Fase 4: relatório de autodiagnóstico",
        "## Heurísticas de recuperação",
        "## Padrão de saída",
    ):
        assert section in skill_content


@pytest.mark.unit
def test_diagnosis_table_covers_read_loop_pattern(skill_content: str):
    table = skill_content.split("### Fase 2", 1)[1].split("### Fase 3", 1)[0]

    assert "Mesmo arquivo lido em faixas diferentes" in table
    assert "mesmo comando repetido" in table


@pytest.mark.unit
def test_skill_has_no_dangling_ecc_references(skill_content: str):
    for reference in (
        "verification-loop",
        "continuous-learning-v2",
        "council",
        "workspace-surface-audit",
    ):
        assert reference not in skill_content


@pytest.mark.unit
def test_upstream_references_ecc_repository(upstream_content: str):
    assert "https://github.com/affaan-m/ECC.git" in upstream_content
    assert (
        "commit: d29cf651c795869f733669c33e3d33dfd8307d10" in upstream_content
    )
    assert "MIT License" in upstream_content
    assert "harness-skills sync agent-introspection-debugging" in (
        upstream_content
    )


@pytest.mark.unit
def test_license_file_exists(repo_root: Path):
    assert (
        repo_root
        / "harness-conf/skills/agent-introspection-debugging/LICENSE"
    ).is_file()


@pytest.mark.unit
def test_upstream_documents_ptbr_description_decision(upstream_content: str):
    header = upstream_content.split("## ", 1)[0]

    assert "description_lang: pt-br" in header
    assert "description_note:" in upstream_content


@pytest.mark.unit
def test_skill_lines_respect_width_limit(skill_content: str):
    long_lines = [
        (index + 1, line)
        for index, line in enumerate(skill_content.splitlines())
        if len(line) > 120
    ]

    assert not long_lines, f"linhas acima de 120 colunas: {long_lines}"


@pytest.mark.unit
def test_skill_is_not_denied_globally(repo_root: Path):
    config = json.loads(
        (repo_root / "harness-conf/opencode.json").read_text(encoding="utf-8")
    )
    denied = config.get("permission", {}).get("skill", {})

    assert denied.get("agent-introspection-debugging") != "deny"
