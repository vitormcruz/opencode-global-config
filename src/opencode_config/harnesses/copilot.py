"""Harness Copilot CLI: conversao de artefatos e copia sincronizada.

O adapter envolve o synchronize (skills, agents convertidos, commands em
skills, default-artifacts, AGENTS.md base) e nao varia por sistema
operacional: a materializacao e sempre copia sincronizada (D1).
"""

from __future__ import annotations

from collections.abc import Callable, Collection
from datetime import datetime
import json
from pathlib import Path
import re
import shutil
import sys
from typing import TextIO

from opencode_config.harnesses import ApplyOptions, HarnessError
from opencode_config.lib.environment import EnvironmentKind
from opencode_config.lib.paths import HARNESS_CONF_DIR
from opencode_config.lib.sync import backup_copy, copy_path, remove_path

_SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_TOOL_PERMISSIONS = ("edit", "bash", "webfetch", "websearch")
_COPILOT_BUILTIN_AGENT_TYPES = frozenset(
    {
        "code-review",
        "explore",
        "general-purpose",
        "research",
        "security-review",
        "task",
    }
)
_OPENCODE_ONLY_AGENTS = frozenset(
    {
        "worker",
        "revisor",
    }
)
_MODEL_ID = re.compile(
    r"^(?:gpt-\d|claude-(?:sonnet|opus|haiku)-|gemini-\d|"
    r"o\d|kimi-k|grok-\d|mai-code|luna$)",
    re.IGNORECASE,
)
_COMMAND_DESCRIPTIONS = {
    "index-codebase": (
        "Indexa repo no codebase-memory. Ative quando humano pedir "
        "index codebase ou indexar repositorio."
    ),
    "bench-indexing": (
        "Benchmark de indexacao codebase-memory. Ative quando humano "
        "pedir bench indexing."
    ),
    "sync-upstream-skills": (
        "Sincroniza skills com upstream. Ative quando humano pedir "
        "sync upstream skills."
    ),
}


class AdapterError(HarnessError):
    """Erro esperado durante a sincronizacao do harness Copilot."""


def _permission_is_denied(value: str) -> bool:
    """Detecta deny em permissoes simples e regras estruturadas de task."""

    return re.search(r"\bdeny\b", value) is not None


def _allowed_agent_types(
    task_rules: dict[str, str],
    available_agent_types: Collection[str],
) -> list[str]:
    """Converte a política OpenCode em uma allowlist de agent_type."""

    wildcard = task_rules.get("*")
    if wildcard == "deny":
        allowed = {
            agent_type
            for agent_type, decision in task_rules.items()
            if agent_type != "*"
            and decision == "allow"
            and agent_type in available_agent_types
        }
    else:
        allowed = set(available_agent_types)
        for agent_type, decision in task_rules.items():
            if agent_type == "*":
                continue
            if decision == "deny":
                allowed.discard(agent_type)
            elif decision == "allow" and agent_type in available_agent_types:
                allowed.add(agent_type)

    return sorted(allowed)


def _is_agent_type(value: str) -> bool:
    """Impede que identificadores de modelos entrem no vocabulário de agentes."""

    return not _MODEL_ID.match(value)


def _delegation_instructions(allowed_agent_types: Collection[str]) -> list[str]:
    """Descreve a chamada Copilot task sem confundir agente e modelo."""

    if not allowed_agent_types:
        return []

    # O frontmatter do Copilot oferece apenas o alias generico `agent`; a
    # allowlist precisa ser publicada no contrato de delegacao do perfil.
    agent_types = ", ".join(allowed_agent_types)
    return [
        "",
        "## Delegacao de subagentes",
        "",
        "Use a ferramenta `task` somente com estes `agent_type` Copilot:",
        f"`{agent_types}`.",
        "",
        "Os campos `prompt`, `description`, `name` e `mode` "
        "(`sync` ou `background`) sao separados.",
        "O campo `model` e opcional: omita-o para usar o modelo padrao "
        "do agente ou da sessao; quando usado, informe um ID de modelo, "
        "nunca um `agent_type`.",
        "",
        "Formato da chamada:",
        "```text",
        "task(",
        '  agent_type="<um agent_type permitido>",',
        '  prompt="<instrucoes>",',
        '  description="<resumo>",',
        '  name="<nome opcional>",',
        '  mode="sync",',
        '  model="<ID de modelo opcional>",',
        ")",
        "```",
        "",
    ]


def _write_utf8(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def convert_agent_frontmatter(
    content: str,
    *,
    agent_type: str | None = None,
    available_agent_types: Collection[str] | None = None,
) -> str:
    """Converte o frontmatter OpenCode para um perfil Copilot CLI."""

    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return content

    end = next(
        (index for index in range(1, len(lines)) if lines[index].strip() == "---"),
        None,
    )
    if end is None:
        return content

    description: list[str] = []
    in_description = False
    permissions: dict[str, str] = {}
    task_rules: dict[str, str] = {}
    current_permission: str | None = None
    mode: str | None = None

    for line in lines[1:end]:
        if re.match(r"^description:", line):
            description = [line]
            in_description = True
            continue
        if in_description and (line.startswith(" ") or not line.strip()):
            description.append(line)
            continue

        in_description = False
        mode_match = re.match(r"^mode:\s*(\S+)", line)
        if mode_match:
            mode = mode_match.group(1)
            continue

        permission_match = re.match(
            r"^  (edit|bash|webfetch|websearch|task|question):\s*(.*)$",
            line,
        )
        if permission_match:
            current_permission = permission_match.group(1)
            permissions[current_permission] = (
                permission_match.group(2).strip().lower()
            )
            continue

        if current_permission == "task":
            task_match = re.match(
                r'^\s{4}(?:"([^"]+)"|(\*|[A-Za-z0-9._-]+)):\s*'
                r"(allow|deny)\s*$",
                line,
            )
            if task_match:
                task_rules[task_match.group(1) or task_match.group(2)] = (
                    task_match.group(3)
                )
                continue

            scalar_task = permissions.get("task", "")
            if scalar_task in {"allow", "deny"}:
                task_rules["*"] = scalar_task

    # In OpenCode, omitted permissions inherit the default capability. Copilot
    # needs that capability listed explicitly in `tools`; only explicit deny
    # removes it from the converted agent.
    effective_permissions = {
        name: permissions.get(name, "allow") for name in _TOOL_PERMISSIONS
    }

    available_agent_types = (
        {
            value
            for value in available_agent_types
            if _is_agent_type(value)
        }
        if available_agent_types is not None
        else set(_COPILOT_BUILTIN_AGENT_TYPES)
    )
    allowed_agent_types = _allowed_agent_types(
        task_rules,
        available_agent_types,
    )

    tools = ["read"]
    if not _permission_is_denied(effective_permissions["edit"]):
        tools.append("edit")
    if not _permission_is_denied(effective_permissions["bash"]):
        tools.append("execute")
    tools.append("search")
    if (
        not _permission_is_denied(effective_permissions["webfetch"])
        or not _permission_is_denied(effective_permissions["websearch"])
    ):
        tools.append("web")
    if allowed_agent_types:
        tools.append("agent")
    if permissions.get("question") == "allow":
        tools.append("ask_user")

    if not description:
        description = ["description: Agent OpenCode convertido para Copilot CLI"]

    converted = [
        "---",
        "\n".join(description).rstrip(),
    ]
    if agent_type:
        converted.append(f"name: {agent_type}")
    converted.extend(
        [
            f"tools: {json.dumps(tools)}",
        ]
    )
    if mode == "subagent":
        converted.append("user-invocable: false")
    converted.append("---")

    body = "\n".join(lines[end + 1:])
    body_lines = _delegation_instructions(allowed_agent_types)
    if body:
        body_lines.extend(["", body])
    converted.extend(body_lines)
    return "\n".join(converted) + "\n"


def _skill_description(lines: list[str]) -> str:
    paragraph: list[str] = []
    started = False
    for line in lines:
        if not line.strip():
            if started:
                break
            continue
        if not started and line.lstrip().startswith("#"):
            continue
        started = True
        paragraph.append(line.strip())
    description = " ".join(paragraph)
    return re.sub(r"\s+", " ", description)[:1024]


def ensure_skill_frontmatter(skill_name: str, content: str) -> str:
    """Valida e completa o frontmatter de uma skill."""

    if not _SKILL_NAME.fullmatch(skill_name) or len(skill_name) > 64:
        raise AdapterError(f"Nome de skill invalido: {skill_name}")

    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        description = _skill_description(lines) or f"Skill {skill_name}."
        body = content.rstrip("\n")
        return (
            f"---\nname: {skill_name}\n"
            f"description: {description}\n---\n\n{body}\n"
        )

    end = next(
        (index for index in range(1, len(lines)) if lines[index].strip() == "---"),
        None,
    )
    if end is None:
        raise AdapterError(f"Frontmatter invalido: {skill_name}/SKILL.md")

    name_match = next(
        (
            re.match(r"^name:\s*(\S+)\s*$", line)
            for line in lines[1:end]
            if re.match(r"^name:\s*(\S+)\s*$", line)
        ),
        None,
    )
    if name_match and name_match.group(1) != skill_name:
        raise AdapterError(
            f"name nao corresponde ao diretorio: {skill_name}/SKILL.md"
        )
    if name_match:
        return content

    lines.insert(1, f"name: {skill_name}")
    return "\n".join(lines).rstrip("\n") + "\n"


def _copy_skill(
    source: Path,
    destination: Path,
    backup_dir: Path,
) -> None:
    backup_copy(destination, backup_dir)
    if destination.exists() or destination.is_symlink():
        remove_path(destination)
    copy_path(source, destination)

    skill_md = destination / "SKILL.md"
    if skill_md.is_file():
        original = skill_md.read_text(encoding="utf-8")
        adapted = ensure_skill_frontmatter(source.name, original)
        if adapted != original:
            _write_utf8(skill_md, adapted)


def _sync_skills(
    repository: Path,
    skills_dir: Path,
    backup_dir: Path,
    output: Callable[[str], None],
) -> None:
    output("")
    output("--- Skills ---")
    skills_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for source in sorted((repository / HARNESS_CONF_DIR / "skills").iterdir()):
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            continue
        _copy_skill(source, skills_dir / source.name, backup_dir)
        output(f"OK    {source.name}")
        count += 1
    output(f"      {count} skill(s) sincronizada(s)")


def _sync_agents(
    repository: Path,
    agents_dir: Path,
    backup_dir: Path,
    output: Callable[[str], None],
) -> None:
    output("")
    output("--- Agents ---")
    agents_dir.mkdir(parents=True, exist_ok=True)
    sources = sorted((repository / HARNESS_CONF_DIR / "agents").glob("*.md"))
    available_agent_types = _COPILOT_BUILTIN_AGENT_TYPES | {
        source.stem for source in sources
    }
    count = 0
    for source in sources:
        if source.stem in _OPENCODE_ONLY_AGENTS:
            output(f"SKIP  {source.name} (OpenCode-only)")
            continue
        destination = agents_dir / f"{source.stem}.agent.md"
        backup_copy(destination, backup_dir)
        _write_utf8(
            destination,
            convert_agent_frontmatter(
                source.read_text(encoding="utf-8"),
                agent_type=source.stem,
                available_agent_types=available_agent_types,
            ),
        )
        output(f"OK    {destination.name}")
        count += 1
    output(f"      {count} agent(s) sincronizado(s)")


def _command_description(name: str) -> str:
    return _COMMAND_DESCRIPTIONS.get(name, f"Executa o comando {name}.")


def _command_body(content: str) -> str:
    lines = content.splitlines()
    if lines and lines[0].strip() == "---":
        end = next(
            (
                index
                for index in range(1, len(lines))
                if lines[index].strip() == "---"
            ),
            None,
        )
        if end is not None:
            lines = lines[end + 1:]
    return "\n".join(lines).rstrip()


def _sync_commands(
    repository: Path,
    skills_dir: Path,
    backup_dir: Path,
    output: Callable[[str], None],
) -> None:
    output("")
    output("--- Commands ---")
    skills_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for source in sorted(
        (repository / HARNESS_CONF_DIR / "commands").glob("*.md")
    ):
        name = source.stem
        destination = skills_dir / name
        backup_copy(destination, backup_dir)
        if destination.exists() or destination.is_symlink():
            remove_path(destination)
        destination.mkdir(parents=True, exist_ok=True)
        skill = (
            f"---\nname: {name}\n"
            f"description: {_command_description(name)}\n---\n\n"
            f"{_command_body(source.read_text(encoding='utf-8'))}\n"
        )
        _write_utf8(destination / "SKILL.md", skill)
        output(f"OK    {name}/SKILL.md")
        count += 1
    output(f"      {count} command(s) convertido(s) em skills")


def _sync_default_artifacts(
    repository: Path,
    agents_dir: Path,
    backup_dir: Path,
    output: Callable[[str], None],
) -> None:
    output("")
    output("--- Default Artifacts ---")
    source = repository / HARNESS_CONF_DIR / "agents" / "default-artifacts"
    if not source.is_dir():
        output("AVISO agents/default-artifacts nao encontrado")
        return

    destination = agents_dir / "default-artifacts"
    agents_dir.mkdir(parents=True, exist_ok=True)
    backup_copy(destination, backup_dir)
    if destination.exists() or destination.is_symlink():
        remove_path(destination)
    copy_path(source, destination)
    count = sum(1 for path in destination.rglob("*") if path.is_file())
    output(f"OK    default-artifacts ({count} arquivo(s))")


def _sync_agents_base(
    repository: Path,
    copilot_dir: Path,
    backup_dir: Path,
    output: Callable[[str], None],
) -> None:
    output("")
    output("--- AGENTS.md base ---")
    source = repository / HARNESS_CONF_DIR / "AGENTS.base.md"
    if not source.is_file():
        output("AVISO harness-conf/AGENTS.base.md nao encontrado")
        return

    destination = copilot_dir / "AGENTS.md"
    backup_copy(destination, backup_dir)
    if destination.exists() or destination.is_symlink():
        remove_path(destination)
    copy_path(source, destination)
    output("OK    AGENTS.md (base global)")


def _print_plan(
    repository: Path,
    skills_dir: Path,
    agents_dir: Path,
    output: Callable[[str], None],
) -> None:
    skill_count = sum(
        1
        for path in (repository / HARNESS_CONF_DIR / "skills").iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )
    agent_count = sum(
        1
        for path in (repository / HARNESS_CONF_DIR / "agents").glob("*.md")
        if path.stem not in _OPENCODE_ONLY_AGENTS
    )
    command_count = len(
        list((repository / HARNESS_CONF_DIR / "commands").glob("*.md"))
    )
    output(f"Repo:         {repository}")
    output(f"Skills:       {skills_dir}")
    output(f"Agents:       {agents_dir}")
    output("")
    output("Plano:")
    output(f"  - Copiar {skill_count} skill(s) para .copilot/skills/")
    output(f"  - Converter {agent_count} agent(s) para .agent.md")
    output(f"  - Converter {command_count} command(s) em skills")
    output(
        "  - Copiar agents/default-artifacts para "
        ".copilot/agents/default-artifacts/"
    )
    output(
        "  - Copiar harness-conf/AGENTS.base.md para .copilot/AGENTS.md"
    )


def _confirm(
    assume_yes: bool,
    input_stream: TextIO,
    output: TextIO,
    error: TextIO,
) -> None:
    if assume_yes:
        return
    if not input_stream.isatty() or not output.isatty():
        error.write("Sem TTY para confirmacao; use --yes\n")
        raise AdapterError("confirmacao sem TTY")
    output.write("Aplicar estas alteracoes? [y/N] ")
    if input_stream.readline().strip().lower() not in {"y", "yes"}:
        output.write("Cancelado.\n")
        raise AdapterError("operacao cancelada")


def synchronize(
    repository: Path,
    dest_root: Path,
    *,
    assume_yes: bool,
    quiet: bool,
    timestamp: str | None = None,
    input_stream: TextIO | None = None,
    output: TextIO | None = None,
    error: TextIO | None = None,
) -> None:
    """Sincroniza todos os artefatos sem reescrever scripts de skills."""

    input_stream = sys.stdin if input_stream is None else input_stream
    output = sys.stdout if output is None else output
    error = sys.stderr if error is None else error
    say = (lambda message: output.write(f"{message}\n")) if not quiet else lambda _: None

    resolved_repository = repository.expanduser().resolve()
    resolved_dest_root = dest_root.expanduser().resolve()
    copilot_dir = resolved_dest_root / ".copilot"
    skills_dir = copilot_dir / "skills"
    agents_dir = copilot_dir / "agents"
    backup_name = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = (
        resolved_dest_root / ".config" / "copilot-backup" / backup_name
    )

    _print_plan(
        resolved_repository,
        skills_dir,
        agents_dir,
        say,
    )
    _confirm(assume_yes, input_stream, output, error)
    _sync_skills(resolved_repository, skills_dir, backup_dir, say)
    _sync_agents(resolved_repository, agents_dir, backup_dir, say)
    _sync_commands(resolved_repository, skills_dir, backup_dir, say)
    _sync_default_artifacts(
        resolved_repository,
        agents_dir,
        backup_dir,
        say,
    )
    _sync_agents_base(
        resolved_repository,
        copilot_dir,
        backup_dir,
        say,
    )
    say("")
    say("Pronto.")


class CopilotAdapter:
    """Aplica a configuracao do Copilot CLI via copia sincronizada."""

    @property
    def name(self) -> str:
        return "copilot"

    def installed(self, environment: EnvironmentKind) -> bool:
        return shutil.which("copilot") is not None

    def apply(self, repository: Path, options: ApplyOptions) -> None:
        synchronize(
            repository,
            options.home,
            assume_yes=options.assume_yes,
            quiet=options.quiet,
            timestamp=options.timestamp,
            input_stream=sys.stdin,
            output=options.output,
            error=options.error,
        )
