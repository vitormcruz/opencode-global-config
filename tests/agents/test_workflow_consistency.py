"""Valida consistência entre workflow, agentes e skills (D11).

Detecta:
- Agente fantasma: workflow cita agente inexistente em ``agents/``.
- Skill inexistente: agente ou workflow cita skill sem diretório em
  ``skills/``.
- Permission órfã: ``task: X: allow`` aponta para agente inexistente.

Mapa de permissions de skills (Task 8 do plano
``plan/otimizacao-custo-contexto.md``):
- Skill órfã: skill com deny global e nenhum allow em agente nenhum
  (invisível a todos).
- Allow de skill inexistente: ``skill: X: allow`` sem pasta em
  ``skills/`` nem wildcard que case.
- Skill de domínio sem deny global (escapou do corte).
- Agente fantasma no ``opencode.json``: seção ``agent`` cita agente
  inexistente em ``agents/``.
"""

from __future__ import annotations

import json
import re
from fnmatch import fnmatchcase
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Coleta de inventário
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
    """Extrai nomes com ``allow`` na seção ``task:`` do frontmatter.

    Ignora a entrada especial ``"*"`` (wildcard).
    """

    allowed: list[str] = []
    in_task = False

    for raw_line in frontmatter.splitlines():
        stripped = raw_line.rstrip()

        # Detecta início do bloco task (indentação de 2 espaços sob permission)
        if re.match(r"^\s+task:\s*$", stripped):
            in_task = True
            continue

        if in_task:
            # Linha mais indentada que task: → entrada de task (4 espaços)
            entry_match = re.match(
                r"^\s{4,}([\w*-]+):\s*(allow|deny)\s*$", stripped
            )
            if entry_match:
                name, value = entry_match.group(1), entry_match.group(2)
                if name != "*" and value == "allow":
                    allowed.append(name)
                continue

            # Linha com indentação menor ou igual a task: → fim do bloco
            if stripped and not stripped.startswith("    "):
                in_task = False

    return allowed


def _extract_task_entries(frontmatter: str) -> list[tuple[str, str]]:
    """Extrai entradas ``(nome, acao)`` da seção ``task:``, preservando ordem.

    Ignora a entrada especial ``"*"`` (wildcard) apenas na filtragem; ela
    é mantida aqui porque a posição dela importa para o teste de ordem.
    """

    entries: list[tuple[str, str]] = []
    in_task = False

    for raw_line in frontmatter.splitlines():
        stripped = raw_line.rstrip()

        if re.match(r"^\s+task:\s*$", stripped):
            in_task = True
            continue

        if in_task:
            entry_match = re.match(
                r"^\s{4,}([\w*-]+|\"[\w*]+\"):\s*(allow|deny)\s*$", stripped
            )
            if entry_match:
                name = entry_match.group(1).strip('"')
                entries.append((name, entry_match.group(2)))
                continue

            if stripped and not stripped.startswith("    "):
                in_task = False

    return entries


def _has_question_allow_permission(frontmatter: str) -> bool:
    """Detecta a permissão shorthand ``question: allow`` no frontmatter."""

    return re.search(r"^\s{2}question:\s*allow\s*$", frontmatter, re.MULTILINE) is not None


# ---------------------------------------------------------------------------
# Parsing de referências em tabelas de skills
# ---------------------------------------------------------------------------

_SKILL_TABLE_ROW_RE = re.compile(
    r"^\|\s*([a-z][a-z-]+)\s*\|", re.MULTILINE
)
_SKILL_HEADING_RE = re.compile(r"^#{1,4}\s+.*[Ss]kill", re.MULTILINE)
_ANY_HEADING_RE = re.compile(r"^#{1,4}\s+", re.MULTILINE)


def _extract_skills_from_tables(text: str) -> list[str]:
    """Extrai nomes de skills de tabelas sob headings ``## Skills``.

    Ignora tabelas fora de seções de skills (ex.: tabelas de agentes
    no curador-produto).
    """

    skills: list[str] = []
    lines = text.splitlines()

    in_skills_section = False

    for line in lines:
        # Detecta início de seção de skills
        if re.match(r"^#{1,4}\s+.*[Ss]kill", line):
            in_skills_section = True
            continue

        # Detecta fim da seção (novo heading de mesmo ou maior nível)
        if in_skills_section and re.match(r"^#{1,3}\s+", line):
            if not re.match(r"^#{1,4}\s+.*[Ss]kill", line):
                in_skills_section = False
                continue

        if in_skills_section:
            match = re.match(r"^\|\s*([a-z][a-z-]+)\s*\|", line)
            if match:
                name = match.group(1)
                # Ignora linhas de separação de tabela
                if not all(c in "-| " for c in line):
                    skills.append(name)

    return skills


# ---------------------------------------------------------------------------
# Parsing de referências em backticks (workflow docs e agentes)
# ---------------------------------------------------------------------------

_BACKTICK_RE = re.compile(r"`([a-z][a-z-]+)`")

# Termos que aparecem em backticks mas NÃO são agentes nem skills.
# Manutenção: adicionar aqui quando novo termo de código aparecer.
_NON_AGENT_NON_SKILL_TERMS: set[str] = {
    "dev",           # abreviação de developer/devflow em prosa
    "fail",          # status de teste
    "pass",          # status de teste
    "findings",      # termo de código
    "prompt",        # termo de código
    "status",        # campo de frontmatter
    "build",         # termo de código
    "websearch",     # nome de tool
    "model",         # campo de frontmatter
    "bloqueante",    # severidade de achado (rev)
    "melhoria",      # severidade de achado (rev)
    "nenhum",        # severidade de achado (rev)
    "testes-produto",  # agregador das suítes por especialidade
}


def _extract_backtick_references(text: str) -> set[str]:
    """Extrai identificadores em backticks que parecem nomes de agente/skill.

    Filtra termos conhecidos de código e identificadores que não seguem
    o padrão de nomes de agentes/skills (lowercase com hifens).
    """

    raw = set(_BACKTICK_RE.findall(text))
    return raw - _NON_AGENT_NON_SKILL_TERMS


# ---------------------------------------------------------------------------
# Helpers de leitura
# ---------------------------------------------------------------------------


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r", "")


def _read_workflow_docs(docs_dir: Path) -> dict[str, str]:
    """Retorna {nome_arquivo: conteúdo} dos workflow docs."""

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
# Permissions de skills (mapa v4: deny global + allow por agente)
# ---------------------------------------------------------------------------

# Skills globais aprovadas: visiveis a todos, SEM deny global (mapa v4
# do plano plan/otimizacao-custo-contexto.md, Task 8). Manutencao: skill
# global nova entra aqui; skill de dominio nova entra no deny global do
# ``harness-conf/opencode.json``. Toda skill em ``harness-conf/skills/``
# deve estar em exatamente um dos dois conjuntos.
_GLOBAL_SKILLS: set[str] = {
    "git-workflow-and-versioning",
    "humanizer-br",
    "portugues-tecnico-controlado",
    "question-orchestration",
    "reliable-async-operations",
    "doc-extract",
    "md-export",
    "tls-certificate-recovery",
    "svg-to-image",
    "web-research-exa-crawl4ai",
}


def _extract_skill_permission_entries(frontmatter: str) -> list[tuple[str, str]]:
    """Extrai entradas ``(padrao, acao)`` da seção ``permission: skill:``.

    Padrões podem vir entre aspas (``"aws-*"``). A entrada especial
    ``*`` é mantida porque o matching é por wildcard.
    """

    entries: list[tuple[str, str]] = []
    in_skill = False

    for raw_line in frontmatter.splitlines():
        stripped = raw_line.rstrip()

        if re.match(r"^\s+skill:\s*$", stripped):
            in_skill = True
            continue

        if in_skill:
            entry_match = re.match(
                r"^\s{4,}(\"[\w*-]+\"|[\w*-]+):\s*(allow|deny)\s*$", stripped
            )
            if entry_match:
                name = entry_match.group(1).strip('"')
                entries.append((name, entry_match.group(2)))
                continue

            # Linha com indentação menor ou igual a skill: → fim do bloco
            if stripped and not stripped.startswith("    "):
                in_skill = False

    return entries


def _load_skill_permission_map(opencode_json: Path) -> dict[str, str]:
    """Retorna ``{padrao: acao}`` da seção ``permission.skill`` do JSON."""

    data = json.loads(_read_text(opencode_json))
    skill_map = data.get("permission", {}).get("skill", {})
    return {str(pattern): str(action) for pattern, action in skill_map.items()}


def _load_opencode_agents(opencode_json: Path) -> list[str]:
    """Retorna os agentes referenciados na seção ``agent`` do JSON."""

    data = json.loads(_read_text(opencode_json))
    return [str(name) for name in data.get("agent", {})]


def _denies_skill(deny_map: dict[str, str], skill_name: str) -> bool:
    """Verifica se a skill está coberta por algum padrão deny global."""

    return any(
        fnmatchcase(skill_name, pattern)
        for pattern, action in deny_map.items()
        if action == "deny"
    )


def _count_skill_allows(agents_dir: Path) -> int:
    """Conta entradas ``allow`` em seções ``permission: skill:``."""

    total = 0
    for content in _read_agent_files(agents_dir).values():
        entries = _extract_skill_permission_entries(_extract_frontmatter(content))
        total += sum(1 for _, action in entries if action == "allow")
    return total


def _find_denied_skills_without_allow(
    skills_dir: Path, agents_dir: Path, opencode_json: Path
) -> list[str]:
    """Skills com deny global e nenhum allow em agente nenhum (órfãs)."""

    deny_map = _load_skill_permission_map(opencode_json)
    agent_permissions = {
        agent_name: _extract_skill_permission_entries(_extract_frontmatter(content))
        for agent_name, content in _read_agent_files(agents_dir).items()
    }

    orphans: list[str] = []
    for skill in sorted(_collect_skill_names(skills_dir)):
        if not _denies_skill(deny_map, skill):
            continue
        has_allow = any(
            action == "allow" and fnmatchcase(skill, pattern)
            for entries in agent_permissions.values()
            for pattern, action in entries
        )
        if not has_allow:
            orphans.append(skill)

    return orphans


def _find_skill_allows_without_match(
    skills_dir: Path, agents_dir: Path, opencode_json: Path
) -> list[str]:
    """Allows cujo padrão não casa com nenhuma skill existente."""

    known_skills = _collect_skill_names(skills_dir)
    missing: list[str] = []

    for agent_name, content in _read_agent_files(agents_dir).items():
        entries = _extract_skill_permission_entries(_extract_frontmatter(content))
        for pattern, action in entries:
            if action != "allow":
                continue
            if not any(fnmatchcase(skill, pattern) for skill in known_skills):
                missing.append(f"{agent_name} -> skill: {pattern}: allow")

    return missing


def _find_skills_without_deny_or_global(
    skills_dir: Path, opencode_json: Path
) -> list[str]:
    """Skills existentes sem deny global e fora da whitelist global."""

    deny_map = _load_skill_permission_map(opencode_json)
    escaped: list[str] = []

    for skill in sorted(_collect_skill_names(skills_dir)):
        if skill in _GLOBAL_SKILLS:
            continue
        if _denies_skill(deny_map, skill):
            continue
        escaped.append(skill)

    return escaped


def _find_opencode_agent_ghosts(
    agents_dir: Path, opencode_json: Path
) -> list[str]:
    """Agentes citados na seção ``agent`` do JSON sem arquivo em agents/."""

    known_agents = _collect_agent_names(agents_dir)
    return [
        f"opencode.json agent: {name}"
        for name in sorted(_load_opencode_agents(opencode_json))
        if name not in known_agents
    ]


# ---------------------------------------------------------------------------
# Fixtures sintéticas (trees falsas em tmp_path)
# ---------------------------------------------------------------------------


def _make_agent_frontmatter(skill_entries: list[tuple[str, str]]) -> str:
    """Monta frontmatter sintético com seções ``skill:`` e ``task:``."""

    lines = ["---", "mode: primary", "permission:", "  skill:"]
    lines += [
        f'    "{pattern}": {action}' if "*" in pattern else f"    {pattern}: {action}"
        for pattern, action in skill_entries
    ]
    lines += ["  task:", '    "*": deny', "---", ""]
    return "\n".join(lines)


def _make_skill_map_tree(
    tmp_path: Path,
    *,
    skills: list[str],
    agents: dict[str, list[tuple[str, str]]],
    permission_skill: dict[str, str],
    opencode_agents: dict[str, dict] | None = None,
) -> tuple[Path, Path, Path]:
    """Cria tree falsa de ``harness-conf`` em tmp_path.

    Retorna ``(skills_dir, agents_dir, opencode_json)`` para uso nas
    funções de verificação.
    """

    skills_dir = tmp_path / "skills"
    agents_dir = tmp_path / "agents"
    skills_dir.mkdir()
    agents_dir.mkdir()

    for skill in skills:
        skill_dir = skills_dir / skill
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")

    for agent_name, entries in agents.items():
        (agents_dir / f"{agent_name}.md").write_text(
            _make_agent_frontmatter(entries), encoding="utf-8"
        )

    data: dict = {"permission": {"skill": permission_skill}}
    if opencode_agents is not None:
        data["agent"] = opencode_agents
    opencode_json = tmp_path / "opencode.json"
    opencode_json.write_text(json.dumps(data), encoding="utf-8")

    return skills_dir, agents_dir, opencode_json


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_task_permissions_point_to_existing_agents(repo_root: Path) -> None:
    """Agentes com ``task: X: allow`` apontam para agente existente."""

    agents_dir = repo_root / "harness-conf" / "agents"
    known_agents = _collect_agent_names(agents_dir)
    orphans: list[str] = []
    total_extracted = 0

    for agent_name, content in _read_agent_files(agents_dir).items():
        frontmatter = _extract_frontmatter(content)
        extracted = _extract_task_allow_agents(frontmatter)
        total_extracted += len(extracted)
        for target in extracted:
            if target not in known_agents:
                orphans.append(f"{agent_name} -> task: {target}: allow")

    # Garante que o parser extraiu permissions reais (devflow tem 7 allows)
    assert total_extracted >= 7, (
        f"Parser extraiu apenas {total_extracted} permissions "
        f"(esperado >= 7); possível regressão à trivialidade"
    )

    assert orphans == [], (
        f"Permissions órfãs (task: allow aponta para agente inexistente):\n"
        + "\n".join(f"  - {o}" for o in orphans)
    )


@pytest.mark.unit
def test_extract_task_allow_agents_detects_synthetic_orphan() -> None:
    """Parser detecta permission sintética com indentação real (4 espaços)."""

    frontmatter = (
        "mode: primary\n"
        "permission:\n"
        "  task:\n"
        "    agente-fantasma: allow\n"
        "    eng-software: allow\n"
    )
    extracted = _extract_task_allow_agents(frontmatter)
    assert "agente-fantasma" in extracted, (
        "Parser não detectou 'agente-fantasma: allow' com 4 espaços"
    )
    assert "eng-software" in extracted


@pytest.mark.unit
def test_task_wildcard_deny_must_precede_allows(repo_root: Path) -> None:
    """Agentes que spawnam subagentes não podem fechar o bloco com ``*: deny``.

    O OpenCode remove a tool ``task`` inteira quando a última regra do
    bloco é ``*: deny`` (``Permission.disabled`` usa ``findLast``). A
    wildcard deny deve vir antes dos ``allow``.
    """

    agents_dir = repo_root / "harness-conf" / "agents"
    offenders: list[str] = []

    for agent_name, content in _read_agent_files(agents_dir).items():
        entries = _extract_task_entries(_extract_frontmatter(content))
        has_allow = any(action == "allow" for _, action in entries)
        if not has_allow:
            continue
        if entries and entries[-1] == ("*", "deny"):
            offenders.append(agent_name)

    assert offenders == [], (
        "Agentes com `*: deny` no fim do bloco `task:` (a tool task é "
        "removida nessa ordem; mova `*: deny` para antes dos allow):\n"
        + "\n".join(f"  - {agent_name}" for agent_name in offenders)
    )


@pytest.mark.unit
def test_task_wildcard_deny_order_detects_synthetic_offender() -> None:
    """Parser detecta ``*: deny`` no fim com entrada sintética."""

    frontmatter = (
        "mode: primary\n"
        "permission:\n"
        "  task:\n"
        "    eng-software: allow\n"
        "    \"*\": deny\n"
    )
    entries = _extract_task_entries(frontmatter)
    assert entries[-1] == ("*", "deny")


@pytest.mark.unit
def test_question_orchestration_agents_allow_question_tool(repo_root: Path) -> None:
    """Agentes que usam question-orchestration permitem a tool question."""

    agents_dir = repo_root / "harness-conf" / "agents"
    missing: list[str] = []

    for agent_name, content in _read_agent_files(agents_dir).items():
        references_skill = (
            "question-orchestration" in content
            and (
                "`question-orchestration`" in content
                or "| question-orchestration |" in content
            )
        )
        if references_skill and not _has_question_allow_permission(
            _extract_frontmatter(content)
        ):
            missing.append(agent_name)

    assert missing == [], (
        "Agentes que referenciam question-orchestration sem "
        "question: allow:\n"
        + "\n".join(f"  - {agent_name}" for agent_name in missing)
    )


@pytest.mark.unit
def test_question_permission_parser_detects_synthetic_missing() -> None:
    """Parser detecta ausência sintética de ``question: allow``."""

    frontmatter = "mode: primary\npermission:\n  edit: allow\n"
    assert not _has_question_allow_permission(frontmatter)


@pytest.mark.unit
def test_skill_tables_reference_existing_skills(repo_root: Path) -> None:
    """Tabelas de skills em agentes referenciam skills existentes."""

    agents_dir = repo_root / "harness-conf" / "agents"
    skills_dir = repo_root / "harness-conf" / "skills"
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
    """Workflows não citam agentes fantasmas (removidos/inexistentes)."""

    agents_dir = repo_root / "harness-conf" / "agents"
    skills_dir = repo_root / "harness-conf" / "skills"
    docs_dir = repo_root / "docs"

    known_agents = _collect_agent_names(agents_dir)
    known_skills = _collect_skill_names(skills_dir)
    ghosts: list[str] = []

    for doc_name, content in _read_workflow_docs(docs_dir).items():
        refs = _extract_backtick_references(content)
        for ref in refs:
            # Se está em known_agents ou known_skills, é válido
            if ref in known_agents or ref in known_skills:
                continue
            # Se parece nome de agente/skill (tem hífen ou é nome
            # conhecido removido), é referência órfã
            if "-" in ref or ref in {
                "curador-produto-editor",
                "val-harness",
            }:
                ghosts.append(f"{doc_name} -> `{ref}`")

    assert ghosts == [], (
        f"Referências fantasmas em workflow docs "
        f"(agente/skill inexistente):\n"
        + "\n".join(f"  - {g}" for g in ghosts)
    )


@pytest.mark.unit
def test_workflow_skill_references_exist(repo_root: Path) -> None:
    """Workflows não citam skills inexistentes."""

    agents_dir = repo_root / "harness-conf" / "agents"
    skills_dir = repo_root / "harness-conf" / "skills"
    docs_dir = repo_root / "docs"

    known_agents = _collect_agent_names(agents_dir)
    known_skills = _collect_skill_names(skills_dir)
    missing: list[str] = []

    for doc_name, content in _read_workflow_docs(docs_dir).items():
        # Skills em tabelas dentro de workflow docs
        for skill_ref in _extract_skills_from_tables(content):
            if skill_ref not in known_skills:
                missing.append(f"{doc_name} (tabela) -> skill: {skill_ref}")

        # Skills referenciadas por backtick que NÃO são agentes
        refs = _extract_backtick_references(content)
        for ref in refs:
            if ref in known_skills:
                continue
            if ref in known_agents:
                continue
            # Se tem hífen e não é agente, pode ser skill órfã
            # (já coberto pelo teste de agentes fantasma acima)

    assert missing == [], (
        f"Skills inexistentes referenciadas em workflow docs:\n"
        + "\n".join(f"  - {m}" for m in missing)
    )


@pytest.mark.unit
def test_agent_backtick_skill_references_exist(repo_root: Path) -> None:
    """Agentes não citam skills inexistentes em backticks fora de tabelas."""

    agents_dir = repo_root / "harness-conf" / "agents"
    skills_dir = repo_root / "harness-conf" / "skills"

    known_agents = _collect_agent_names(agents_dir)
    known_skills = _collect_skill_names(skills_dir)
    missing: list[str] = []

    for agent_name, content in _read_agent_files(agents_dir).items():
        refs = _extract_backtick_references(content)
        for ref in refs:
            if ref in known_agents or ref in known_skills:
                continue
            # Não é agente nem skill conhecida — se parece skill
            # (tem hífen), é potencial referência órfã
            if "-" in ref:
                missing.append(f"{agent_name} -> `{ref}`")

    assert missing == [], (
        f"Referências de skill/agent inexistentes em backticks "
        f"de agentes:\n"
        + "\n".join(f"  - {m}" for m in missing)
    )


@pytest.mark.unit
def test_removed_agents_not_referenced(repo_root: Path) -> None:
    """Agentes removidos (D4) não são referenciados em nenhum lugar."""

    removed_agents = {"curador-produto-editor", "val-harness"}
    removed_docs = {"workflow-curadoria.md"}

    agents_dir = repo_root / "harness-conf" / "agents"
    docs_dir = repo_root / "docs"

    violations: list[str] = []

    # Verifica agentes
    for agent_name, content in _read_agent_files(agents_dir).items():
        for removed in removed_agents:
            if removed in content:
                violations.append(
                    f"agents/{agent_name}.md contém '{removed}'"
                )

    # Verifica workflow docs
    for doc_name, content in _read_workflow_docs(docs_dir).items():
        for removed in removed_agents:
            if removed in content:
                violations.append(
                    f"docs/{doc_name} contém '{removed}'"
                )
        for removed_doc in removed_docs:
            if removed_doc in content:
                violations.append(
                    f"docs/{doc_name} contém '{removed_doc}'"
                )

    assert violations == [], (
        f"Referências a agentes/docs removidos ainda presentes:\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


# ---------------------------------------------------------------------------
# Testes: mapa de permissions de skills (Task 8/9)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_denied_skills_have_at_least_one_allow(repo_root: Path) -> None:
    """Skill com deny global tem allow em algum agente (não fica órfã)."""

    harness_dir = repo_root / "harness-conf"
    agents_dir = harness_dir / "agents"

    # Guarda contra regressão à trivialidade do parser (mapa v4: 69
    # allows em 11 agentes).
    total_allows = _count_skill_allows(agents_dir)
    assert total_allows >= 69, (
        f"Parser extraiu apenas {total_allows} allows de skill "
        f"(esperado >= 69); possível regressão à trivialidade"
    )

    orphans = _find_denied_skills_without_allow(
        harness_dir / "skills", agents_dir, harness_dir / "opencode.json"
    )
    assert orphans == [], (
        f"Skills órfãs (deny global sem nenhum allow, invisíveis a "
        f"todos os agentes):\n"
        + "\n".join(f"  - {o}" for o in orphans)
    )


@pytest.mark.unit
def test_denied_skill_without_allow_is_detected(tmp_path: Path) -> None:
    """Fixture violante: skill negada globalmente sem allow em agente."""

    skills_dir, agents_dir, opencode_json = _make_skill_map_tree(
        tmp_path,
        skills=["skill-orfa"],
        agents={
            "agente-a": [("skill-orfa", "deny"), ("outra-skill", "allow")],
        },
        permission_skill={"skill-orfa": "deny", "outra-skill": "deny"},
    )
    orphans = _find_denied_skills_without_allow(
        skills_dir, agents_dir, opencode_json
    )
    assert orphans == ["skill-orfa"], (
        f"Fixture violante não detectado; orphans = {orphans}"
    )


@pytest.mark.unit
def test_skill_allows_reference_existing_skills(repo_root: Path) -> None:
    """Todo ``skill: X: allow`` casa com skill existente (ou wildcard)."""

    harness_dir = repo_root / "harness-conf"
    missing = _find_skill_allows_without_match(
        harness_dir / "skills",
        harness_dir / "agents",
        harness_dir / "opencode.json",
    )
    assert missing == [], (
        f"Allow de skill inexistente (sem pasta em skills/ e sem "
        f"wildcard que case):\n"
        + "\n".join(f"  - {m}" for m in missing)
    )


@pytest.mark.unit
def test_allow_to_missing_skill_is_detected(tmp_path: Path) -> None:
    """Fixture violante: allow aponta para skill sem diretório."""

    skills_dir, agents_dir, opencode_json = _make_skill_map_tree(
        tmp_path,
        skills=["skill-real"],
        agents={
            "agente-a": [
                ("skill-fantasma", "allow"),
                ("skill-real", "allow"),
            ],
        },
        permission_skill={"skill-real": "deny"},
    )
    missing = _find_skill_allows_without_match(
        skills_dir, agents_dir, opencode_json
    )
    assert missing == ["agente-a -> skill: skill-fantasma: allow"], (
        f"Fixture violante não detectado; missing = {missing}"
    )


@pytest.mark.unit
def test_domain_skills_have_global_deny(repo_root: Path) -> None:
    """Toda skill está em deny global ou na whitelist de skills globais.

    Skill fora dos dois conjuntos é skill de domínio que escapou do
    corte (visível a todos sem pass pelo mapa).
    """

    harness_dir = repo_root / "harness-conf"
    escaped = _find_skills_without_deny_or_global(
        harness_dir / "skills", harness_dir / "opencode.json"
    )
    assert escaped == [], (
        f"Skills de domínio sem deny global (escaparam do corte; "
        f"adicione ao deny global ou mova para _GLOBAL_SKILLS com "
        f"decisão do humano):\n"
        + "\n".join(f"  - {s}" for s in escaped)
    )


@pytest.mark.unit
def test_domain_skill_without_global_deny_is_detected(tmp_path: Path) -> None:
    """Fixture violante: skill existente sem deny e fora da whitelist."""

    skills_dir, agents_dir, opencode_json = _make_skill_map_tree(
        tmp_path,
        skills=["skill-escapada"],
        agents={},
        permission_skill={},
    )
    escaped = _find_skills_without_deny_or_global(
        skills_dir, opencode_json
    )
    assert escaped == ["skill-escapada"], (
        f"Fixture violante não detectado; escaped = {escaped}"
    )


@pytest.mark.unit
def test_opencode_agent_references_exist(repo_root: Path) -> None:
    """Seção ``agent`` do opencode.json cita agentes existentes."""

    harness_dir = repo_root / "harness-conf"
    ghosts = _find_opencode_agent_ghosts(
        harness_dir / "agents", harness_dir / "opencode.json"
    )
    assert ghosts == [], (
        f"Agente fantasma na seção agent do opencode.json (sem arquivo "
        f"em harness-conf/agents/):\n"
        + "\n".join(f"  - {g}" for g in ghosts)
    )


@pytest.mark.unit
def test_opencode_agent_ghost_reference_is_detected(tmp_path: Path) -> None:
    """Fixture violante: seção agent cita agente inexistente."""

    skills_dir, agents_dir, opencode_json = _make_skill_map_tree(
        tmp_path,
        skills=["skill-real"],
        agents={"agente-a": []},
        permission_skill={"skill-real": "deny"},
        opencode_agents={"agente-fantasma": {"reasoningEffort": "max"}},
    )
    ghosts = _find_opencode_agent_ghosts(agents_dir, opencode_json)
    assert ghosts == ["opencode.json agent: agente-fantasma"], (
        f"Fixture violante não detectado; ghosts = {ghosts}"
    )


@pytest.mark.unit
def test_extract_skill_permission_entries_parses_quoted_wildcard() -> None:
    """Parser lê wildcard entre aspas e fecha o bloco em ``task:``."""

    frontmatter = (
        "mode: primary\n"
        "permission:\n"
        "  skill:\n"
        '    "aws-*": allow\n'
        "    debugging-and-error-recovery: allow\n"
        "  task:\n"
        '    "*": deny\n'
    )
    entries = _extract_skill_permission_entries(frontmatter)
    assert entries == [
        ("aws-*", "allow"),
        ("debugging-and-error-recovery", "allow"),
    ], f"Parser extraiu entradas erradas: {entries}"
