"""Harness Copilot CLI: conversao de artefatos e copia sincronizada.

O adapter envolve o synchronize (skills, agents convertidos, commands em
skills, default-artifacts, AGENTS.md base) e nao varia por sistema
operacional: a materializacao e sempre copia sincronizada (ADR-0004).
"""

from __future__ import annotations

from collections.abc import Callable, Collection
from dataclasses import dataclass
from datetime import datetime
from fnmatch import fnmatchcase
import json
from pathlib import Path
import re
import shutil
import sys
from typing import TextIO

from opencode_config.bootstrap.ai_memory import (
    AI_MEMORY_MCP_URL,
    is_ai_memory_provisioned,
)
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
# Nomes de agentes raiz que o adapter já materializou como `.agent.md`
# em alguma execução (histórico de `harness-conf/agents/*.md`).
#
# LIMITAÇÃO do prune de órfãos: os arquivos `.agent.md` não carregam
# marcador confiável que distinga conteúdo gerado pelo adapter de
# arquivo criado pelo usuário. O prune só remove arquivos cujo stem
# está nesta lista e que deixaram de ser sincronizados (agente
# removido do repo ou tornado OpenCode-only). Consequências:
# - Arquivos `.agent.md` do usuário com nomes fora desta lista nunca
#   são removidos.
# - Agente novo adicionado ao repo e removido depois exige inclusão
#   manual do nome nesta lista para o prune cobri-lo.
_HISTORICALLY_SYNCED_AGENTS = frozenset(
    {
        "analista",
        "aws-analista",
        "curador-produto",
        "dba",
        "devflow",
        "eng-software",
        "front",
        "qa",
        "rev",
        "revisor-historia",
        "revisor",
        "sec",
        "smart-planner",
        "worker",
    }
)
_MODEL_ID = re.compile(
    r"^(?:gpt-\d|claude-(?:sonnet|opus|haiku)-|gemini-\d|"
    r"o\d|kimi-k|grok-\d|mai-code|luna$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SkillRoute:
    """Destinos atual e anterior de uma skill sincronizada."""

    source: Path
    destination: Path
    stale_destination: Path


@dataclass(frozen=True)
class CopilotSkillPlan:
    """Plano de roteamento de skills derivado das permissions globais."""

    discovery_directory: Path
    auxiliary_directory: Path
    routes: tuple[SkillRoute, ...]

    @property
    def global_count(self) -> int:
        return sum(
            route.destination == self.discovery_directory
            for route in self.routes
        )

    @property
    def domain_count(self) -> int:
        return len(self.routes) - self.global_count


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
    "otimizar-agents-md": (
        "Analisa e otimiza arquivos AGENTS.md. Ative quando humano pedir "
        "otimizar, enxugar ou revisar AGENTS.md."
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
    elif mode == "primary":
        # Espelha a semântica OpenCode: agente primary não é spawnável
        # via task no Copilot, então não pode ser invocado por modelo.
        converted.append("disable-model-invocation: true")
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


def _load_skill_permission_map(repository: Path) -> dict[str, str]:
    opencode_json = repository / HARNESS_CONF_DIR / "opencode.json"
    configuration = json.loads(opencode_json.read_text(encoding="utf-8"))
    skill_permissions = configuration.get("permission", {}).get("skill", {})
    return {
        str(pattern): str(action)
        for pattern, action in skill_permissions.items()
    }


def _is_domain_skill(
    skill_name: str,
    skill_permissions: dict[str, str],
) -> bool:
    return any(
        action == "deny" and fnmatchcase(skill_name, pattern)
        for pattern, action in skill_permissions.items()
    )


def _build_skill_plan(repository: Path, copilot_dir: Path) -> CopilotSkillPlan:
    discovery_directory = copilot_dir / "skills"
    auxiliary_directory = copilot_dir / "referencias" / "skills"
    source_directory = repository / HARNESS_CONF_DIR / "skills"
    skill_permissions = _load_skill_permission_map(repository)
    routes: list[SkillRoute] = []

    for source in sorted(source_directory.iterdir()):
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            continue
        is_domain_skill = _is_domain_skill(source.name, skill_permissions)
        destination_directory = (
            auxiliary_directory if is_domain_skill else discovery_directory
        )
        stale_directory = (
            discovery_directory if is_domain_skill else auxiliary_directory
        )
        routes.append(
            SkillRoute(
                source=source,
                destination=destination_directory / source.name,
                stale_destination=stale_directory / source.name,
            )
        )

    return CopilotSkillPlan(
        discovery_directory=discovery_directory,
        auxiliary_directory=auxiliary_directory,
        routes=tuple(routes),
    )


def _sync_skills(
    skill_plan: CopilotSkillPlan,
    backup_dir: Path,
    output: Callable[[str], None],
) -> None:
    output("")
    output("--- Skills ---")
    skill_plan.discovery_directory.mkdir(parents=True, exist_ok=True)
    skill_plan.auxiliary_directory.mkdir(parents=True, exist_ok=True)
    for route in skill_plan.routes:
        if route.stale_destination.exists() or route.stale_destination.is_symlink():
            backup_copy(route.stale_destination, backup_dir)
            remove_path(route.stale_destination)
        _copy_skill(route.source, route.destination, backup_dir)
        output(f"OK    {route.source.name}")
    output(f"      {len(skill_plan.routes)} skill(s) sincronizada(s)")


def _prune_orphan_agents(
    agents_dir: Path,
    synced_names: Collection[str],
    backup_dir: Path,
    output: Callable[[str], None],
) -> int:
    """Remove `.agent.md` órfãos de nomes que o adapter já materializou.

    Só toca em arquivos cujo stem está em ``_HISTORICALLY_SYNCED_AGENTS``
    e que não são mais sincronizados (ver limitação na constante).
    """

    pruned = 0
    for path in sorted(agents_dir.glob("*.agent.md")):
        stem = path.name.removesuffix(".agent.md")
        if stem not in _HISTORICALLY_SYNCED_AGENTS:
            continue
        if stem in synced_names:
            continue
        backup_copy(path, backup_dir)
        remove_path(path)
        output(f"PRUNE {path.name} (orfa: agente nao sincronizado)")
        pruned += 1
    return pruned


def _agent_skill_allow_patterns(agent_content: str) -> list[str]:
    lines = agent_content.splitlines()
    if not lines or lines[0].strip() != "---":
        return []

    frontmatter_end = next(
        (index for index in range(1, len(lines)) if lines[index].strip() == "---"),
        None,
    )
    if frontmatter_end is None:
        return []

    frontmatter = lines[1:frontmatter_end]
    permission_start = next(
        (
            index
            for index, line in enumerate(frontmatter)
            if line == "permission:"
        ),
        None,
    )
    if permission_start is None:
        return []

    permission_end = next(
        (
            index
            for index in range(permission_start + 1, len(frontmatter))
            if frontmatter[index].strip()
            and not frontmatter[index].startswith((" ", "\t"))
        ),
        len(frontmatter),
    )
    skill_header = next(
        (
            index
            for index in range(permission_start + 1, permission_end)
            if frontmatter[index] == "  skill:"
        ),
        None,
    )
    if skill_header is None:
        return []

    patterns: list[str] = []
    for line in frontmatter[skill_header + 1:permission_end]:
        if not line.strip():
            continue
        if not line.startswith("    "):
            break
        match = re.match(
            r'^    (?:"([^"]+)"|([^:\s]+)):\s*(allow|deny)\s*$',
            line,
        )
        if match and match.group(3) == "allow":
            patterns.append(match.group(1) or match.group(2))
    return patterns


def _read_skill_description(skill_file: Path) -> str:
    lines = skill_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise AdapterError(f"Frontmatter ausente: {skill_file}")

    frontmatter_end = next(
        (index for index in range(1, len(lines)) if lines[index].strip() == "---"),
        None,
    )
    if frontmatter_end is None:
        raise AdapterError(f"Frontmatter invalido: {skill_file}")

    description_start = next(
        (
            index
            for index, line in enumerate(lines[1:frontmatter_end], start=1)
            if line.startswith("description:")
        ),
        None,
    )
    if description_start is None:
        raise AdapterError(f"Description ausente: {skill_file}")

    first_value = lines[description_start].partition(":")[2].strip()
    if first_value in {">", "|", ">-", "|-", ">+", "|+"}:
        description_lines: list[str] = []
        for line in lines[description_start + 1:frontmatter_end]:
            if line.strip() and not line.startswith((" ", "\t")):
                break
            description_lines.append(line.strip())
    else:
        description_lines = [first_value]

    description = re.sub(r"\s+", " ", " ".join(description_lines)).strip()
    if len(description) >= 2 and description[0] == description[-1] == '"':
        description = description[1:-1]
    elif len(description) >= 2 and description[0] == description[-1] == "'":
        description = description[1:-1]
    if not description:
        raise AdapterError(f"Description vazia: {skill_file}")
    return description


def _skill_reference_block(
    agent_content: str,
    skill_plan: CopilotSkillPlan,
) -> str:
    allow_patterns = _agent_skill_allow_patterns(agent_content)
    allowed_routes = [
        route
        for route in skill_plan.routes
        if route.destination.parent == skill_plan.auxiliary_directory
        and any(
            fnmatchcase(route.source.name, pattern)
            for pattern in allow_patterns
        )
    ]
    if not allowed_routes:
        return ""

    lines = [
        "<!-- BEGIN COPILOT GENERATED SKILLS -->",
        "## Skills de domínio autorizadas",
        "",
        "Leia cada skill pelo caminho absoluto quando precisar aplicar seu método.",
        "",
    ]
    for route in allowed_routes:
        skill_file = route.source / "SKILL.md"
        description = _read_skill_description(skill_file)
        path = (route.destination / "SKILL.md").resolve()
        lines.extend(
            [
                f"- **{route.source.name}**: {description}",
                f"  Arquivo: `{path}`",
            ]
        )
    lines.extend(["", "<!-- END COPILOT GENERATED SKILLS -->"])
    return "\n".join(lines)


def _append_skill_reference_block(profile: str, block: str) -> str:
    if not block:
        return profile
    return f"{profile.rstrip()}\n\n{block}\n"


def _sync_agents(
    repository: Path,
    agents_dir: Path,
    backup_dir: Path,
    skill_plan: CopilotSkillPlan,
    output: Callable[[str], None],
) -> None:
    output("")
    output("--- Agents ---")
    agents_dir.mkdir(parents=True, exist_ok=True)
    sources = sorted((repository / HARNESS_CONF_DIR / "agents").glob("*.md"))
    # Agentes OpenCode-only não existem no Copilot: ficam fora do
    # vocabulário de delegação publicado na prosa dos perfis.
    available_agent_types = _COPILOT_BUILTIN_AGENT_TYPES | {
        source.stem
        for source in sources
        if source.stem not in _OPENCODE_ONLY_AGENTS
    }
    count = 0
    synced_names: set[str] = set()
    for source in sources:
        if source.stem in _OPENCODE_ONLY_AGENTS:
            output(f"SKIP  {source.name} (OpenCode-only)")
            continue
        destination = agents_dir / f"{source.stem}.agent.md"
        backup_copy(destination, backup_dir)
        source_content = source.read_text(encoding="utf-8")
        converted_profile = convert_agent_frontmatter(
            source_content,
            agent_type=source.stem,
            available_agent_types=available_agent_types,
        )
        skill_references = _skill_reference_block(source_content, skill_plan)
        _write_utf8(
            destination,
            _append_skill_reference_block(converted_profile, skill_references),
        )
        output(f"OK    {destination.name}")
        synced_names.add(source.stem)
        count += 1
    pruned = _prune_orphan_agents(
        agents_dir,
        synced_names,
        backup_dir,
        output,
    )
    if pruned:
        output(f"      {pruned} agent(s) orfao(s) removido(s)")
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


def _sync_mcp_config(
    repository: Path,
    home: Path,
    backup_dir: Path,
    *,
    ai_memory_enabled: bool,
    output: Callable[[str], None],
) -> None:
    destination = home / ".copilot" / "mcp-config.json"
    existing: dict[str, object] = {}
    if destination.is_file():
        try:
            loaded = json.loads(destination.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise AdapterError(f"JSON inválido em {destination}; a configuração foi preservada.") from error
        if not isinstance(loaded, dict):
            raise AdapterError(f"A raiz de {destination} precisa ser um objeto JSON.")
        existing = loaded

    servers = existing.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise AdapterError(f"mcpServers em {destination} precisa ser um objeto JSON.")

    if ai_memory_enabled:
        canonical_path = repository / HARNESS_CONF_DIR / "opencode.json"
        try:
            canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AdapterError(
                f"Não foi possível ler a config canônica {canonical_path}: {error}"
            ) from error
        canonical_servers = canonical.get("mcp") if isinstance(canonical, dict) else None
        canonical_server = (
            canonical_servers.get("ai-memory")
            if isinstance(canonical_servers, dict)
            else None
        )
        if (
            not isinstance(canonical_server, dict)
            or canonical_server.get("url") != AI_MEMORY_MCP_URL
        ):
            raise AdapterError("harness-conf/opencode.json não declara mcp.ai-memory.")
        desired = {
            "type": "http",
            "url": AI_MEMORY_MCP_URL,
        }
        current = servers.get("ai-memory")
        if current is not None and current != desired:
            raise AdapterError(
                f"mcpServers.ai-memory já existe em {destination} com outro "
                "destino. Preserve a entrada ou remova-a após backup explícito."
            )
        if current == desired:
            return
        servers["ai-memory"] = desired
    elif servers.get("ai-memory") == {
        "type": "http",
        "url": AI_MEMORY_MCP_URL,
    }:
        del servers["ai-memory"]
    else:
        return

    if servers:
        existing["mcpServers"] = servers
    else:
        existing.pop("mcpServers", None)
    backup_copy(destination, backup_dir)
    _write_utf8(
        destination,
        json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
    )
    action = "declarado" if ai_memory_enabled else "removido"
    output(f"OK    MCP ai-memory {action} em {destination}")


def _print_plan(
    repository: Path,
    skill_plan: CopilotSkillPlan,
    agents_dir: Path,
    output: Callable[[str], None],
) -> None:
    agent_count = sum(
        1
        for path in (repository / HARNESS_CONF_DIR / "agents").glob("*.md")
        if path.stem not in _OPENCODE_ONLY_AGENTS
    )
    command_count = len(
        list((repository / HARNESS_CONF_DIR / "commands").glob("*.md"))
    )
    output(f"Repo:         {repository}")
    output(f"Skills:       {skill_plan.discovery_directory}")
    output(f"Referências:  {skill_plan.auxiliary_directory}")
    output(f"Agents:       {agents_dir}")
    output("")
    output("Plano:")
    output(
        f"  - Copiar {skill_plan.global_count} skill(s) global(is) para "
        ".copilot/skills/"
    )
    output(
        f"  - Copiar {skill_plan.domain_count} skill(s) de domínio para "
        ".copilot/referencias/skills/"
    )
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
    ai_memory_enabled: bool | None = None,
) -> None:
    """Sincroniza todos os artefatos sem reescrever scripts de skills."""

    input_stream = sys.stdin if input_stream is None else input_stream
    output = sys.stdout if output is None else output
    error = sys.stderr if error is None else error
    say = (lambda message: output.write(f"{message}\n")) if not quiet else lambda _: None

    resolved_repository = repository.expanduser().resolve()
    resolved_dest_root = dest_root.expanduser().resolve()
    copilot_dir = resolved_dest_root / ".copilot"
    include_ai_memory = (
        is_ai_memory_provisioned(resolved_dest_root)
        if ai_memory_enabled is None
        else ai_memory_enabled
    )
    skill_plan = _build_skill_plan(resolved_repository, copilot_dir)
    skills_dir = skill_plan.discovery_directory
    agents_dir = copilot_dir / "agents"
    backup_name = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = (
        resolved_dest_root / ".config" / "copilot-backup" / backup_name
    )

    _print_plan(
        resolved_repository,
        skill_plan,
        agents_dir,
        say,
    )
    _confirm(assume_yes, input_stream, output, error)
    _sync_skills(skill_plan, backup_dir, say)
    _sync_agents(resolved_repository, agents_dir, backup_dir, skill_plan, say)
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
    _sync_mcp_config(
        resolved_repository,
        resolved_dest_root,
        backup_dir,
        ai_memory_enabled=include_ai_memory,
        output=say,
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
        ai_memory_enabled = (
            is_ai_memory_provisioned(options.home)
            if options.ai_memory_enabled is None
            else options.ai_memory_enabled
        )
        synchronize(
            repository,
            options.home,
            assume_yes=options.assume_yes,
            quiet=options.quiet,
            timestamp=options.timestamp,
            input_stream=sys.stdin,
            output=options.output,
            error=options.error,
            ai_memory_enabled=ai_memory_enabled,
        )
