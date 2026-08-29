"""Valida consistencia entre workflow, agentes e skills (D11).

Detecta:
- Agente fantasma: workflow cita agente inexistente em ``agents/``.
- Skill inexistente: agente ou workflow cita skill sem diretorio em
  ``skills/``.
- Permission orfa: ``task: X: allow`` aponta para agente inexistente.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Coleta de inventario
# ---------------------------------------------------------------------------


def _collect_agent_names(agents_dir: Path) -> set[str]:
    """Retorna nomes de agentes raiz (``agents/*.md``), sem subpastas."""

    return {
        p.stem
        for p in agents_dir.glob("*.md")
        if p.is_file()
    }


def _collect_skill_names(skills_dir: Path) -> set[str]:
    """Retorna nomes de skills (diretorios com ``SKILL.md``)."""

    return {
        p.parent.name
        for p in skills_dir.glob("*/SKILL.md")
        if p.is_file()
    }


# ---------------------------------------------------------------------------
# Parsing de frontmatter (sem PyYAML)
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---", re.DOTALL)


def _extract_frontmatter(text: str) -> str:
    """Retorna o bloco YAML entre os marcadores ``---``."""

    match = _FRONTMATTER_RE.match(text)
    return match.group(1) if match else ""


def _extract_task_allow_agents(frontmatter: str) -> list[str]:
    """Extrai nomes com ``allow`` na secao ``task:`` do frontmatter.

    Ignora a entrada especial ``"*"`` (wildcard).
    """

    allowed: list[str] = []
    in_task = False

    for raw_line in frontmatter.splitlines():
        stripped = raw_line.rstrip()

        # Detecta inicio do bloco task (indentacao de 4 espacos sob permission)
        if re.match(r"^\s+task:\s*$", stripped):
            in_task = True
            continue

        if in_task:
            # Linha mais indentada que task: → entrada de task
            entry_match = re.match(
                r"^\s{6,}([\w*-]+):\s*(allow|deny)\s*$", stripped
            )
            if entry_match:
                name, value = entry_match.group(1), entry_match.group(2)
                if name != "*" and value == "allow":
                    allowed.append(name)
                continue

            # Linha com indentacao menor ou igual a task: → fim do bloco
            if stripped and not stripped.startswith("      "):
                in_task = False

    return allowed


# ---------------------------------------------------------------------------
# Parsing de referencias em tabelas de skills
# ---------------------------------------------------------------------------

_SKILL_TABLE_ROW_RE = re.compile(
    r"^\|\s*([a-z][a-z-]+)\s*\|", re.MULTILINE
)
_SKILL_HEADING_RE = re.compile(r"^#{1,4}\s+.*[Ss]kill", re.MULTILINE)
_ANY_HEADING_RE = re.compile(r"^#{1,4}\s+", re.MULTILINE)


def _extract_skills_from_tables(text: str) -> list[str]:
    """Extrai nomes de skills de tabelas sob headings ``## Skills``.

    Ignora tabelas fora de secoes de skills (ex.: tabelas de agentes
    no curador-produto).
    """

    skills: list[str] = []
    lines = text.splitlines()

    in_skills_section = False

    for line in lines:
        # Detecta inicio de secao de skills
        if re.match(r"^#{1,4}\s+.*[Ss]kill", line):
            in_skills_section = True
            continue

        # Detecta fim da secao (novo heading de mesmo ou maior nivel)
        if in_skills_section and re.match(r"^#{1,3}\s+", line):
            if not re.match(r"^#{1,4}\s+.*[Ss]kill", line):
                in_skills_section = False
                continue

        if in_skills_section:
            match = re.match(r"^\|\s*([a-z][a-z-]+)\s*\|", line)
            if match:
                name = match.group(1)
                # Ignora linhas de separacao de tabela
                if not all(c in "-| " for c in line):
                    skills.append(name)

    return skills


# ---------------------------------------------------------------------------
# Parsing de referencias em backticks (workflow docs e agentes)
# ---------------------------------------------------------------------------

_BACKTICK_RE = re.compile(r"`([a-z][a-z-]+)`")

# Termos que aparecem em backticks mas NAO sao agentes nem skills.
# Manutencao: adicionar aqui quando novo termo de codigo aparecer.
_NON_AGENT_NON_SKILL_TERMS: set[str] = {
    "dev",           # abreviacao de developer/devflow em prosa
    "fail",          # status de teste
    "pass",          # status de teste
    "findings",      # termo de codigo
    "prompt",        # termo de codigo
    "status",        # campo de frontmatter
    "build",         # termo de codigo
    "websearch",     # nome de tool
    "model",         # campo de frontmatter
    "bloqueante",    # severidade de achado (rev)
    "melhoria",      # severidade de achado (rev)
    "nenhum",        # severidade de achado (rev)
}


def _extract_backtick_references(text: str) -> set[str]:
    """Extrai identificadores em backticks que parecem nomes de agente/skill.

    Filtra termos conhecidos de codigo e identificadores que nao seguem
    o padrao de nomes de agentes/skills (lowercase com hifens).
    """

    raw = set(_BACKTICK_RE.findall(text))
    return raw - _NON_AGENT_NON_SKILL_TERMS


# ---------------------------------------------------------------------------
# Helpers de leitura
# ---------------------------------------------------------------------------


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r", "")


def _read_workflow_docs(docs_dir: Path) -> dict[str, str]:
    """Retorna {nome_arquivo: conteudo} dos workflow docs."""

    return {
        p.name: _read_text(p)
        for p in sorted(docs_dir.glob("workflow-*.md"))
        if p.is_file()
    }


def _read_agent_files(agents_dir: Path) -> dict[str, str]:
    """Retorna {nome_agente: conteudo} dos agentes raiz."""

    return {
        p.stem: _read_text(p)
        for p in sorted(agents_dir.glob("*.md"))
        if p.is_file()
    }


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_task_permissions_point_to_existing_agents(repo_root: Path) -> None:
    """Agentes com ``task: X: allow`` apontam para agente existente."""

    agents_dir = repo_root / "agents"
    known_agents = _collect_agent_names(agents_dir)
    orphans: list[str] = []

    for agent_name, content in _read_agent_files(agents_dir).items():
        frontmatter = _extract_frontmatter(content)
        for target in _extract_task_allow_agents(frontmatter):
            if target not in known_agents:
                orphans.append(f"{agent_name} -> task: {target}: allow")

    assert orphans == [], (
        f"Permissions orfas (task: allow aponta para agente inexistente):\n"
        + "\n".join(f"  - {o}" for o in orphans)
    )


@pytest.mark.unit
def test_skill_tables_reference_existing_skills(repo_root: Path) -> None:
    """Tabelas de skills em agentes referenciam skills existentes."""

    agents_dir = repo_root / "agents"
    skills_dir = repo_root / "skills"
    known_skills = _collect_skill_names(skills_dir)
    missing: list[str] = []

    for agent_name, content in _read_agent_files(agents_dir).items():
        for skill_ref in _extract_skills_from_tables(content):
            if skill_ref not in known_skills:
                missing.append(f"{agent_name} -> skill: {skill_ref}")

    assert missing == [], (
        f"Skills inexistentes referenciadas em tabelas de agentes:\n"
        + "\n".join(f"  - {m}" for m in missing)
    )


@pytest.mark.unit
def test_workflow_agent_references_exist(repo_root: Path) -> None:
    """Workflows nao citam agentes fantasmas (removidos/inexistentes)."""

    agents_dir = repo_root / "agents"
    skills_dir = repo_root / "skills"
    docs_dir = repo_root / "docs"

    known_agents = _collect_agent_names(agents_dir)
    known_skills = _collect_skill_names(skills_dir)
    ghosts: list[str] = []

    for doc_name, content in _read_workflow_docs(docs_dir).items():
        refs = _extract_backtick_references(content)
        for ref in refs:
            # Se esta em known_agents ou known_skills, e valido
            if ref in known_agents or ref in known_skills:
                continue
            # Se parece nome de agente/skill (tem hifen ou eh nome
            # conhecido removido), e referencia orfa
            if "-" in ref or ref in {
                "curador-produto-editor",
                "val-harness",
            }:
                ghosts.append(f"{doc_name} -> `{ref}`")

    assert ghosts == [], (
        f"Referencias fantasmas em workflow docs "
        f"(agente/skill inexistente):\n"
        + "\n".join(f"  - {g}" for g in ghosts)
    )


@pytest.mark.unit
def test_workflow_skill_references_exist(repo_root: Path) -> None:
    """Workflows nao citam skills inexistentes."""

    agents_dir = repo_root / "agents"
    skills_dir = repo_root / "skills"
    docs_dir = repo_root / "docs"

    known_agents = _collect_agent_names(agents_dir)
    known_skills = _collect_skill_names(skills_dir)
    missing: list[str] = []

    for doc_name, content in _read_workflow_docs(docs_dir).items():
        # Skills em tabelas dentro de workflow docs
        for skill_ref in _extract_skills_from_tables(content):
            if skill_ref not in known_skills:
                missing.append(f"{doc_name} (tabela) -> skill: {skill_ref}")

        # Skills referenciadas por backtick que NAO sao agentes
        refs = _extract_backtick_references(content)
        for ref in refs:
            if ref in known_skills:
                continue
            if ref in known_agents:
                continue
            # Se tem hifen e nao eh agente, pode ser skill orfa
            # (ja coberto pelo teste de agentes fantasma acima)

    assert missing == [], (
        f"Skills inexistentes referenciadas em workflow docs:\n"
        + "\n".join(f"  - {m}" for m in missing)
    )


@pytest.mark.unit
def test_agent_backtick_skill_references_exist(repo_root: Path) -> None:
    """Agentes nao citam skills inexistentes em backticks fora de tabelas."""

    agents_dir = repo_root / "agents"
    skills_dir = repo_root / "skills"

    known_agents = _collect_agent_names(agents_dir)
    known_skills = _collect_skill_names(skills_dir)
    missing: list[str] = []

    for agent_name, content in _read_agent_files(agents_dir).items():
        refs = _extract_backtick_references(content)
        for ref in refs:
            if ref in known_agents or ref in known_skills:
                continue
            # Nao e agente nem skill conhecida — se parece skill
            # (tem hifen), e potencial referencia orfa
            if "-" in ref:
                missing.append(f"{agent_name} -> `{ref}`")

    assert missing == [], (
        f"Referencias de skill/agent inexistentes em backticks "
        f"de agentes:\n"
        + "\n".join(f"  - {m}" for m in missing)
    )


@pytest.mark.unit
def test_removed_agents_not_referenced(repo_root: Path) -> None:
    """Agentes removidos (D4) nao sao referenciados em nenhum lugar."""

    removed_agents = {"curador-produto-editor", "val-harness"}
    removed_docs = {"workflow-curadoria.md"}

    agents_dir = repo_root / "agents"
    docs_dir = repo_root / "docs"

    violations: list[str] = []

    # Verifica agentes
    for agent_name, content in _read_agent_files(agents_dir).items():
        for removed in removed_agents:
            if removed in content:
                violations.append(
                    f"agents/{agent_name}.md contem '{removed}'"
                )

    # Verifica workflow docs
    for doc_name, content in _read_workflow_docs(docs_dir).items():
        for removed in removed_agents:
            if removed in content:
                violations.append(
                    f"docs/{doc_name} contem '{removed}'"
                )
        for removed_doc in removed_docs:
            if removed_doc in content:
                violations.append(
                    f"docs/{doc_name} contem '{removed_doc}'"
                )

    assert violations == [], (
        f"Referencias a agentes/docs removidos ainda presentes:\n"
        + "\n".join(f"  - {v}" for v in violations)
    )
