"""Guarda da política aberta de delegação (tool task).

A política de delegação é aberta: todo agente pode spawnar
qualquer agente via ``permission.task["*"] == "allow"``. A
decisão, o contexto (agentes de projetos consumidores bloqueados
pela allowlist estática) e a revogação do hardening anterior
estão registrados na ADR
``docs/adr/0012-permissoes-task-abertas.md``.

Guardas desta suíte:

1. Nenhuma entrada ``deny`` em ``permission.task``, wildcard ou
   nomeada. Um deny reintroduz a allowlist estática que impedia
   projetos consumidores de spawnar agentes próprios.
2. ``"*": allow`` é a forma sancionada do bloco; a guarda aprova.
3. Allows nomeados residuais continuam validados: o alvo precisa
   ter ``mode`` spawnável (``subagent`` ou ``all``). Apontar para
   ``mode: primary`` falha em runtime ("Unknown subagent type").
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---", re.DOTALL)
_SPAWNABLE_MODES = {"subagent", "all"}
_TASK_ENTRY_RE = re.compile(
    r'^\s{4,}([\w*-]+|"[^"]+"):\s*(allow|deny)\s*$'
)


def _extract_frontmatter(text: str) -> str:
    """Retorna o bloco YAML entre os marcadores ``---``."""

    match = _FRONTMATTER_RE.match(text)
    return match.group(1) if match else ""


def _extract_mode(frontmatter: str) -> str | None:
    """Retorna o valor de ``mode:`` do frontmatter, se presente."""

    match = re.search(r"^mode:\s*(\S+)\s*$", frontmatter, re.MULTILINE)
    return match.group(1) if match else None


def _task_entries(frontmatter: str) -> list[tuple[str, str]]:
    """Retorna ``(nome, decisão)`` das entradas da seção ``task:``."""

    entries: list[tuple[str, str]] = []
    in_task = False

    for raw_line in frontmatter.splitlines():
        stripped = raw_line.rstrip()

        if re.match(r"^\s+task:\s*$", stripped):
            in_task = True
            continue

        if in_task:
            entry_match = _TASK_ENTRY_RE.match(stripped)
            if entry_match:
                name = entry_match.group(1).strip('"')
                entries.append((name, entry_match.group(2)))
                continue

            if stripped and not stripped.startswith("    "):
                in_task = False

    return entries


def _find_task_deny_entries(agents_dir: Path) -> list[str]:
    """Retorna ofensores: qualquer ``deny`` na seção ``task:``.

    Ofensor é entrada wildcard (``"*": deny``) ou nomeada
    (``X: deny``), reportada como ``agente -> task: X: deny``.
    """

    offenders: list[str] = []
    for path in sorted(agents_dir.glob("*.md")):
        frontmatter = _extract_frontmatter(
            path.read_text(encoding="utf-8")
        )
        for name, decision in _task_entries(frontmatter):
            if decision == "deny":
                offenders.append(f"{path.stem} -> task: {name}: deny")

    return offenders


def _find_unspawnable_targets(
    agents_dir: Path,
) -> tuple[list[str], int]:
    """Retorna ``(ofensores, total_de_alvos)`` dos ``task: allow``.

    Ofensor: alvo de ``task: X: allow`` cujo ``mode`` não é spawnável
    (ou agente alvo inexistente).
    """

    modes: dict[str, str | None] = {}
    for path in agents_dir.glob("*.md"):
        frontmatter = _extract_frontmatter(
            path.read_text(encoding="utf-8")
        )
        modes[path.stem] = _extract_mode(frontmatter)

    offenders: list[str] = []
    total = 0
    for path in sorted(agents_dir.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        frontmatter = _extract_frontmatter(content)
        for name, decision in _task_entries(frontmatter):
            if decision != "allow" or name == "*":
                continue
            total += 1
            if modes.get(name) not in _SPAWNABLE_MODES:
                offenders.append(
                    f"{path.stem} -> task: {name}: allow "
                    f"(mode: {modes.get(name)})"
                )

    return offenders, total


@pytest.mark.unit
def test_task_deny_is_absent(repo_root: Path) -> None:
    """Nenhum agente tem ``deny`` em ``permission.task``.

    Qualquer deny (wildcard ou nomeado) reintroduz a allowlist
    estática revogada na ADR
    ``docs/adr/0012-permissoes-task-abertas.md``.
    """

    agents_dir = repo_root / "harness-conf" / "agents"
    offenders = _find_task_deny_entries(agents_dir)

    assert offenders == [], (
        "Entradas deny em permission.task (política aberta "
        "revogada pela ADR docs/adr/0012-permissoes-task-abertas.md):\n"
        + "\n".join(f"  - {o}" for o in offenders)
        + "\n\nCorreção: substitua o bloco por `task:` com `\"*\": "
        "allow` (ver ADR)."
    )


@pytest.mark.unit
def test_task_wildcard_allow_is_the_standing_policy(
    repo_root: Path,
) -> None:
    """Todo agente com seção ``task:`` usa o wildcard ``allow``.

    Sanciona a forma do bloco decidida na ADR
    ``docs/adr/0012-permissoes-task-abertas.md``.
    """

    agents_dir = repo_root / "harness-conf" / "agents"
    offenders: list[str] = []
    for path in sorted(agents_dir.glob("*.md")):
        frontmatter = _extract_frontmatter(
            path.read_text(encoding="utf-8")
        )
        entries = dict(_task_entries(frontmatter))
        if entries and entries.get("*") != "allow":
            offenders.append(f"{path.stem} -> task: {entries}")

    assert offenders == [], (
        "Agentes com seção task sem o wildcard \"*\": allow:\n"
        + "\n".join(f"  - {o}" for o in offenders)
        + "\n\nPolítica vigente: docs/adr/0012-permissoes-"
        "task-abertas.md"
    )


@pytest.mark.unit
def test_task_deny_entries_are_detected(tmp_path: Path) -> None:
    """Fixture violante: deny wildcard e nomeado são detectados.

    Confirma também que ``"*": allow`` não é ofensor (a guarda
    aprova o wildcard da política aberta).
    """

    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "a-wildcard-deny.md").write_text(
        "---\n"
        "mode: primary\n"
        "permission:\n"
        "  task:\n"
        '    "*": deny\n'
        "---\n",
        encoding="utf-8",
    )
    (agents_dir / "b-nomeado-deny.md").write_text(
        "---\n"
        "mode: primary\n"
        "permission:\n"
        "  task:\n"
        '    "*": allow\n'
        "    legado: deny\n"
        "---\n",
        encoding="utf-8",
    )
    (agents_dir / "c-wildcard-allow.md").write_text(
        "---\n"
        "mode: primary\n"
        "permission:\n"
        "  task:\n"
        '    "*": allow\n'
        "---\n",
        encoding="utf-8",
    )

    offenders = _find_task_deny_entries(agents_dir)

    assert offenders == [
        "a-wildcard-deny -> task: *: deny",
        "b-nomeado-deny -> task: legado: deny",
    ], (
        "Guarda não distinguiu deny (ofensor) de wildcard allow "
        f"(esperado como aprovado); offenders = {offenders}"
    )


@pytest.mark.unit
def test_task_allow_targets_are_spawnable(repo_root: Path) -> None:
    """Todo ``task: X: allow`` aponta para agente spawnável.

    Guarda residual: sob a política aberta os blocos usam o
    wildcard, mas um allow nomeado que reapareça continua
    precisando de alvo spawnável (ver ADR
    ``docs/adr/0012-permissoes-task-abertas.md``).
    """

    agents_dir = repo_root / "harness-conf" / "agents"
    offenders, _total = _find_unspawnable_targets(agents_dir)

    assert offenders == [], (
        "Alvos de task: allow sem mode spawnável (subagent ou all):\n"
        + "\n".join(f"  - {o}" for o in offenders)
    )


@pytest.mark.unit
def test_task_allow_target_with_primary_mode_is_detected(
    tmp_path: Path,
) -> None:
    """Fixture violante: alvo de spawn com ``mode: primary``."""

    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "orquestrador.md").write_text(
        "---\n"
        "mode: primary\n"
        "permission:\n"
        "  task:\n"
        '    "*": deny\n'
        "    especialista: allow\n"
        "---\n",
        encoding="utf-8",
    )
    (agents_dir / "especialista.md").write_text(
        "---\nmode: primary\n---\n",
        encoding="utf-8",
    )

    offenders, total = _find_unspawnable_targets(agents_dir)

    assert total == 1
    assert offenders == [
        "orquestrador -> task: especialista: allow (mode: primary)"
    ], f"Fixture violante não detectada; offenders = {offenders}"
