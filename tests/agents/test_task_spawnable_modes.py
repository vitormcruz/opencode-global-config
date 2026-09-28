"""Guarda: todo alvo de ``task: X: allow`` tem mode spawnável.

Um ``task: X: allow`` só funciona se o agente alvo puder ser
spawnado via task. No OpenCode, ``mode: primary`` não é spawnável
(rodar como primary); apenas ``mode: subagent`` e ``mode: all``
são. Sem esta guarda, uma permissão de spawn apontando para agente
primary é silenciosamente inefetiva.

Segunda guarda: nenhum agente pode ter ``permission.task["*"] ==
"allow"``. Permissão ampla não é auditável e a delegação a agente
``mode: primary`` falha em runtime ("Unknown subagent type"). O
wildcard ``"*": deny`` continua permitido (padrão de deny
explícito do repo).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---", re.DOTALL)
_SPAWNABLE_MODES = {"subagent", "all"}


def _extract_frontmatter(text: str) -> str:
    """Retorna o bloco YAML entre os marcadores ``---``."""

    match = _FRONTMATTER_RE.match(text)
    return match.group(1) if match else ""


def _extract_mode(frontmatter: str) -> str | None:
    """Retorna o valor de ``mode:`` do frontmatter, se presente."""

    match = re.search(r"^mode:\s*(\S+)\s*$", frontmatter, re.MULTILINE)
    return match.group(1) if match else None


def _extract_task_allow_agents(frontmatter: str) -> list[str]:
    """Extrai nomes com ``allow`` na seção ``task:`` do frontmatter.

    Ignora a entrada especial ``"*"`` (wildcard).
    """

    allowed: list[str] = []
    in_task = False

    for raw_line in frontmatter.splitlines():
        stripped = raw_line.rstrip()

        if re.match(r"^\s+task:\s*$", stripped):
            in_task = True
            continue

        if in_task:
            entry_match = re.match(
                r'^\s{4,}([\w*-]+|"[^"]+"):\s*(allow|deny)\s*$', stripped
            )
            if entry_match:
                name = entry_match.group(1).strip('"')
                if name != "*" and entry_match.group(2) == "allow":
                    allowed.append(name)
                continue

            if stripped and not stripped.startswith("    "):
                in_task = False

    return allowed


def _extract_task_wildcard_permission(frontmatter: str) -> str | None:
    """Retorna a permissão do wildcard ``"*"`` na seção ``task:``.

    Retorna ``"allow"``, ``"deny"`` ou ``None`` (seção ou entrada
    ausente).
    """

    in_task = False

    for raw_line in frontmatter.splitlines():
        stripped = raw_line.rstrip()

        if re.match(r"^\s+task:\s*$", stripped):
            in_task = True
            continue

        if in_task:
            entry_match = re.match(
                r'^\s{4,}([\w*-]+|"[^"]+"):\s*(allow|deny)\s*$', stripped
            )
            if entry_match:
                name = entry_match.group(1).strip('"')
                if name == "*":
                    return entry_match.group(2)
                continue

            if stripped and not stripped.startswith("    "):
                in_task = False

    return None


def _find_wildcard_allow_agents(agents_dir: Path) -> list[str]:
    """Retorna agentes com ``permission.task["*"] == "allow"``."""

    offenders: list[str] = []
    for path in sorted(agents_dir.glob("*.md")):
        frontmatter = _extract_frontmatter(
            path.read_text(encoding="utf-8")
        )
        if _extract_task_wildcard_permission(frontmatter) == "allow":
            offenders.append(path.stem)

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
        for target in _extract_task_allow_agents(frontmatter):
            total += 1
            if modes.get(target) not in _SPAWNABLE_MODES:
                offenders.append(
                    f"{path.stem} -> task: {target}: allow "
                    f"(mode: {modes.get(target)})"
                )

    return offenders, total


@pytest.mark.unit
def test_task_allow_targets_are_spawnable(repo_root: Path) -> None:
    """Todo ``task: X: allow`` aponta para agente spawnável."""

    agents_dir = repo_root / "harness-conf" / "agents"
    offenders, total = _find_unspawnable_targets(agents_dir)

    # Guarda contra regressão à trivialidade do parser (estado atual:
    # 17 alvos entre devflow, analista, curador-produto e
    # smart-planner; worker e revisor foram excluídos em 2026-09-28).
    assert total >= 12, (
        f"Parser extraiu apenas {total} alvos de task: allow "
        f"(esperado >= 12); possível regressão à trivialidade"
    )

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


@pytest.mark.unit
def test_task_wildcard_allow_is_forbidden(repo_root: Path) -> None:
    """Nenhum agente pode ter ``permission.task["*"] == "allow"``."""

    agents_dir = repo_root / "harness-conf" / "agents"
    offenders = _find_wildcard_allow_agents(agents_dir)

    assert offenders == [], (
        "Agentes com permissão ampla task[\"*\"] = allow:\n"
        + "\n".join(f"  - {o}" for o in offenders)
        + "\n\nMotivo: permissão ampla não é auditável e a delegação a"
        " agente mode: primary falha em runtime"
        " (\"Unknown subagent type\").\n"
        "Correção: substitua o wildcard pela lista nomeada dos agentes"
        " spawnáveis (mode: subagent ou all)."
    )


@pytest.mark.unit
def test_task_wildcard_allow_is_detected(tmp_path: Path) -> None:
    """Fixture violante: wildcard ``\"*\": allow`` é detectado."""

    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "planejador.md").write_text(
        "---\n"
        "mode: primary\n"
        "permission:\n"
        "  task:\n"
        '    "*": allow\n'
        "---\n",
        encoding="utf-8",
    )
    (agents_dir / "orquestrador.md").write_text(
        "---\n"
        "mode: primary\n"
        "permission:\n"
        "  task:\n"
        '    "*": deny\n'
        "---\n",
        encoding="utf-8",
    )

    assert _find_wildcard_allow_agents(agents_dir) == ["planejador"], (
        "Fixture com task[\"*\"] = allow não detectada (ou \"*\": deny "
        "falsamente ofensor)"
    )
