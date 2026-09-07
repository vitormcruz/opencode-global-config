"""Adapter multiplataforma para sincronizar artefatos do GitHub Copilot CLI."""

from __future__ import annotations

from collections.abc import Callable, Collection, Sequence
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
import json
from io import StringIO
import os
from pathlib import Path
import re
import shutil
import sys
from typing import TextIO

from opencode_config.lib.paths import HARNESS_CONF_DIR

HELP_TEXT = """opencode-copilot-adapter

Sincroniza a fonte canonica deste repositorio com o Copilot CLI.

Uso:
  opencode-copilot-adapter [--yes] [--quiet] [--repo-root PATH]
                           [--dest-root PATH]

Opcoes:
  --yes             Nao pede confirmacao
  --quiet           Suprime saidas detalhadas
  --repo-root PATH  Define a raiz do repositorio
  --dest-root PATH  Substitui a raiz de destino (usado em testes)
  --help            Mostra esta ajuda
"""

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


class AdapterError(RuntimeError):
    """Erro esperado durante a sincronizacao do adapter."""


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


def _resolve_repo_root(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))

    configured = os.environ.get("OPENCODE_CONFIG_REPO")
    if configured:
        candidates.append(Path(configured))

    candidates.append(Path.cwd())
    candidates.append(Path(__file__).resolve().parents[3])

    for candidate in candidates:
        root = candidate.expanduser().resolve()
        harness = root / HARNESS_CONF_DIR
        if (
            (harness / "agents").is_dir()
            and (harness / "commands").is_dir()
            and (harness / "skills").is_dir()
        ):
            return root

    raise AdapterError(
        "Raiz do repositorio nao encontrada; use --repo-root PATH"
    )


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _copy_path(source: Path, destination: Path) -> None:
    if source.is_symlink():
        destination.symlink_to(
            os.readlink(source),
            target_is_directory=source.is_dir(),
        )
    elif source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination)


def _backup_if_exists(
    path: Path,
    backup_dir: Path,
) -> None:
    if not path.exists() and not path.is_symlink():
        return

    backup_dir.mkdir(parents=True, exist_ok=True)
    base = backup_dir / path.name
    output = base
    index = 1
    while output.exists() or output.is_symlink():
        output = backup_dir / f"{path.name}.{index}"
        index += 1
    _copy_path(path, output)


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
            r"^  (edit|bash|webfetch|websearch|task):\s*(.*)$",
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
    _backup_if_exists(destination, backup_dir)
    if destination.exists() or destination.is_symlink():
        _remove_path(destination)
    _copy_path(source, destination)

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
        _backup_if_exists(destination, backup_dir)
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
        _backup_if_exists(destination, backup_dir)
        if destination.exists() or destination.is_symlink():
            _remove_path(destination)
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
    _backup_if_exists(destination, backup_dir)
    if destination.exists() or destination.is_symlink():
        _remove_path(destination)
    _copy_path(source, destination)
    count = sum(1 for path in destination.rglob("*") if path.is_file())
    output(f"OK    default-artifacts ({count} arquivo(s))")


def _sync_instructions(
    repository: Path,
    instructions_dir: Path,
    backup_dir: Path,
    output: Callable[[str], None],
) -> None:
    output("")
    output("--- Instructions ---")
    source = repository / ".github" / "copilot-specific.instructions.md"
    if not source.is_file():
        output("AVISO .github/copilot-specific.instructions.md nao encontrado")
        return

    destination = instructions_dir / "copilot-specific.instructions.md"
    instructions_dir.mkdir(parents=True, exist_ok=True)
    _backup_if_exists(destination, backup_dir)
    _copy_path(source, destination)
    output("OK    copilot-specific.instructions.md (user global)")


def _print_plan(
    repository: Path,
    skills_dir: Path,
    instructions_dir: Path,
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
    output(f"Instructions: {instructions_dir}")
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
        "  - Copiar .github/copilot-specific.instructions.md para "
        ".copilot/instructions/"
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
    instructions_dir = copilot_dir / "instructions"
    agents_dir = copilot_dir / "agents"
    backup_name = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = (
        resolved_dest_root / ".config" / "copilot-backup" / backup_name
    )

    _print_plan(
        resolved_repository,
        skills_dir,
        instructions_dir,
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
    _sync_instructions(
        resolved_repository,
        instructions_dir,
        backup_dir,
        say,
    )
    say("")
    say("Pronto.")


def _parse_arguments(
    arguments: Sequence[str],
) -> tuple[bool, bool, str | None, str | None]:
    assume_yes = False
    quiet = False
    repository: str | None = None
    destination: str | None = None
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--yes":
            assume_yes = True
        elif argument == "--quiet":
            quiet = True
        elif argument in {"--help", "-h"}:
            raise SystemExit(0)
        elif argument in {"--repo-root", "--dest-root"}:
            index += 1
            if index >= len(arguments):
                raise AdapterError(f"{argument} exige um caminho")
            if argument == "--repo-root":
                repository = arguments[index]
            else:
                destination = arguments[index]
        elif argument.startswith("--repo-root="):
            repository = argument.split("=", 1)[1]
        elif argument.startswith("--dest-root="):
            destination = argument.split("=", 1)[1]
        else:
            raise AdapterError(f"Opcao desconhecida: {argument}")
        index += 1
    return assume_yes, quiet, repository, destination


def _default_dest_root() -> Path:
    return Path(
        os.environ.get("DestRoot")
        or os.environ.get("DEST_ROOT")
        or os.environ.get("USERPROFILE")
        or os.environ.get("HOME")
        or Path.home()
    )


def _dispatch(
    arguments: Sequence[str],
    output: TextIO,
    error: TextIO,
) -> int:
    try:
        assume_yes, quiet, repository_arg, destination_arg = _parse_arguments(
            arguments
        )
    except SystemExit:
        output.write(HELP_TEXT)
        return 0
    except AdapterError as problem:
        error.write(f"ERRO: {problem}\n")
        error.write(HELP_TEXT)
        return 2

    try:
        synchronize(
            _resolve_repo_root(repository_arg),
            Path(destination_arg) if destination_arg else _default_dest_root(),
            assume_yes=assume_yes,
            quiet=quiet,
            output=output,
            error=error,
        )
    except (AdapterError, OSError) as problem:
        error.write(f"ERRO: {problem}\n")
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Executa o adapter usando os streams reais do processo."""

    return _dispatch(
        list(sys.argv[1:] if argv is None else argv),
        sys.stdout,
        sys.stderr,
    )


def run_cli(argv: Sequence[str]) -> tuple[int, str, str]:
    """Executa o CLI com streams capturados para testes e integrações."""

    output = StringIO()
    error = StringIO()
    with redirect_stdout(output), redirect_stderr(error):
        status = _dispatch(list(argv), output, error)
    return status, output.getvalue(), error.getvalue()


if __name__ == "__main__":
    raise SystemExit(main())
