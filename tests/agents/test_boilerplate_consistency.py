"""Valida blocos de boilerplate compartilhados entre agentes do workflow."""

from pathlib import Path

import pytest


def extract_section(path: Path, heading: str, end_marker: str) -> str:
    """Extrai uma seção até a primeira linha que contém o marcador final."""

    lines = path.read_text(encoding="utf-8").replace("\r", "").splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return ""

    try:
        end = next(
            index
            for index in range(start, len(lines))
            if lines[index] == end_marker
        )
    except StopIteration:
        end = len(lines)

    return "\n".join(lines[start : end + 1])


def extract_contrato(path: Path) -> str:
    """Extrai o Contrato Operacional até o separador de seção."""

    return extract_section(path, "## Contrato Operacional", "---")


def extract_evidencias_intro(path: Path) -> str:
    """Extrai a introdução de Evidências de Execução até o bloco de código."""

    lines = path.read_text(encoding="utf-8").replace("\r", "").splitlines()
    try:
        start = lines.index("## Evidências de Execução")
    except ValueError:
        return ""

    intro = []
    for line in lines[start:]:
        if line.startswith("```"):
            break
        intro.append(line)
    return "\n".join(intro)


@pytest.mark.unit
def test_contrato_operacional_is_identical_between_shared_agents(
    repo_root: Path,
) -> None:
    """Contrato Operacional é idêntico entre eng, front, qa e sec."""

    agents_dir = repo_root / "agents"
    baseline = extract_contrato(agents_dir / "eng-software.md")

    for agent in ("front", "qa", "sec"):
        current = extract_contrato(agents_dir / f"{agent}.md")
        assert current == baseline, (
            f"{agent}.md: Contrato Operacional divergiu do baseline "
            "(eng-software.md)"
        )


@pytest.mark.unit
def test_evidencias_intro_is_identical_between_all_workflow_agents(
    repo_root: Path,
) -> None:
    """Introdução de Evidências é idêntica entre os seis agentes."""

    agents_dir = repo_root / "agents"
    baseline = extract_evidencias_intro(agents_dir / "eng-software.md")

    for agent in ("front", "qa", "sec", "dba", "rev"):
        current = extract_evidencias_intro(agents_dir / f"{agent}.md")
        assert current == baseline, (
            f"{agent}.md: Evidências intro divergiu do baseline "
            "(eng-software.md)"
        )

    assert "sem modificações — harness não executado" in baseline
    assert "revisão sem alteração de artefatos" in baseline


@pytest.mark.unit
def test_commit_enabled_agents_use_git_workflow_skill(repo_root: Path) -> None:
    """Agentes que alteram artefatos devem versionar suas próprias mudanças."""

    agents_dir = repo_root / "agents"
    agents = (
        "eng-software",
        "front",
        "qa",
        "rev",
        "sec",
        "val-harness",
        "dba",
        "curador-produto-editor",
    )

    for agent in agents:
        content = (agents_dir / f"{agent}.md").read_text(encoding="utf-8")
        assert "git-workflow-and-versioning" in content
        assert "Não propõe commit" not in content
