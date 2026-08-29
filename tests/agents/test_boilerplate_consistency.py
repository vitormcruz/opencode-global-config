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


def extract_regras_inviolaveis(path: Path) -> str:
    """Extrai o bloco Regras Invioláveis até o próximo heading ou separador."""

    lines = path.read_text(encoding="utf-8").replace("\r", "").splitlines()
    try:
        start = lines.index("## Regras Invioláveis")
    except ValueError:
        return ""

    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line.startswith("## ") or line == "---":
            end = index
            break

    return "\n".join(lines[start:end])


@pytest.mark.unit
def test_contrato_operacional_is_identical_between_specialists(
    repo_root: Path,
) -> None:
    """Contrato Operacional é idêntico entre especialistas (front, qa, sec)."""

    agents_dir = repo_root / "agents"
    baseline = extract_contrato(agents_dir / "front.md")

    for agent in ("qa", "sec"):
        current = extract_contrato(agents_dir / f"{agent}.md")
        assert current == baseline, (
            f"{agent}.md: Contrato Operacional divergiu do baseline "
            "(front.md)"
        )


@pytest.mark.unit
def test_specialists_have_subagent_no_commit_rule(repo_root: Path) -> None:
    """Especialistas têm regra de subagente — não commitar."""

    agents_dir = repo_root / "agents"
    specialists = ("dba", "front", "qa", "sec", "rev")

    for agent in specialists:
        content = (agents_dir / f"{agent}.md").read_text(encoding="utf-8")
        assert "Subagente — não commitar" in content, (
            f"{agent}.md: falta regra 'Subagente — não commitar' "
            "no Contrato Operacional"
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
def test_commit_enabled_agents_reference_git_workflow_skill(
    repo_root: Path,
) -> None:
    """Agentes referenciam git-workflow (obrigatória ou condicional)."""

    agents_dir = repo_root / "agents"
    agents = (
        "eng-software",
        "front",
        "qa",
        "rev",
        "sec",
        "dba",
    )

    for agent in agents:
        content = (agents_dir / f"{agent}.md").read_text(encoding="utf-8")
        assert "git-workflow-and-versioning" in content, (
            f"{agent}.md: não referencia git-workflow-and-versioning"
        )


@pytest.mark.unit
def test_specialists_do_not_have_git_workflow_in_mandatory(
    repo_root: Path,
) -> None:
    """Especialistas não têm git-workflow na tabela de obrigatórias."""

    agents_dir = repo_root / "agents"
    specialists = ("dba", "front", "qa", "sec", "rev")

    for agent in specialists:
        content = (agents_dir / f"{agent}.md").read_text(encoding="utf-8")
        lines = content.replace("\r", "").splitlines()

        try:
            start = lines.index(
                "### Obrigatórias (carregar ANTES da capacidade indicada)"
            )
        except ValueError:
            continue

        end = len(lines)
        for index in range(start + 1, len(lines)):
            if lines[index].startswith("### "):
                end = index
                break

        mandatory_section = "\n".join(lines[start:end])
        assert "git-workflow-and-versioning" not in mandatory_section, (
            f"{agent}.md: git-workflow-and-versioning não deve estar "
            "na tabela de obrigatórias (especialistas não commitam)"
        )


@pytest.mark.unit
def test_specialists_have_regras_inviolaveis_block(repo_root: Path) -> None:
    """Agentes do workflow têm bloco Regras Invioláveis com ≤10 linhas."""

    agents_dir = repo_root / "agents"
    agents = ("dba", "front", "qa", "sec", "rev", "eng-software")

    for agent in agents:
        path = agents_dir / f"{agent}.md"
        block = extract_regras_inviolaveis(path)
        assert block, (
            f"{agent}.md: falta bloco '## Regras Invioláveis'"
        )

        rule_lines = [
            line
            for line in block.splitlines()
            if line.strip() and not line.startswith("## ")
        ]
        assert len(rule_lines) <= 10, (
            f"{agent}.md: Regras Invioláveis tem {len(rule_lines)} "
            "linhas (máximo 10)"
        )


@pytest.mark.unit
def test_dba_references_data_modeling_skill(repo_root: Path) -> None:
    """dba referencia a skill data-modeling."""

    content = (repo_root / "agents/dba.md").read_text(encoding="utf-8")
    assert "data-modeling" in content


@pytest.mark.unit
def test_rev_has_domain_skill_anchors(repo_root: Path) -> None:
    """rev tem âncoras às skills de domínio para revisão."""

    content = (repo_root / "agents/rev.md").read_text(encoding="utf-8")
    domain_skills = (
        "security-and-hardening",
        "data-modeling",
        "frontend-ui-engineering",
        "accessibility-audit",
        "tests-as-spec",
        "api-and-interface-design",
        "documentation-and-adrs",
    )

    for skill in domain_skills:
        assert skill in content, (
            f"rev.md: falta âncora à skill '{skill}'"
        )


@pytest.mark.unit
def test_rev_is_read_only(repo_root: Path) -> None:
    """rev é read-only — nunca edita código em revisão."""

    content = (repo_root / "agents/rev.md").read_text(encoding="utf-8")
    assert "Read-only" in content or "read-only" in content
    assert "nunca editar código" in content or "nunca corrige" in content


@pytest.mark.unit
def test_eng_software_has_committer_unico_rule(repo_root: Path) -> None:
    """eng-software é o committer único do workflow."""

    content = (repo_root / "agents/eng-software.md").read_text(
        encoding="utf-8"
    )
    assert "Committer único" in content
    assert "git-workflow-and-versioning" in content
