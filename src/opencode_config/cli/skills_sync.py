"""Sincronização das skills externas e de seus metadados de upstream."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from typing import TextIO

SKILL_COMMAND_TIMEOUT_SECONDS = 300


class SyncError(RuntimeError):
    """Indica que um upstream não pode ser sincronizado com segurança."""


@dataclass(frozen=True)
class SyncResult:
    """Resultado resumido de uma sincronização."""

    status: str


@dataclass(frozen=True)
class UpdateResult:
    """Resultado serializável da atualização de uma skill."""

    status: str
    output: str


@dataclass(frozen=True)
class SyncSpec:
    """Metadados do repositório upstream de uma família de skills."""

    name: str
    repository: str
    branch: str


SPECS = {
    "accessibility-audit": SyncSpec(
        "accessibility-audit",
        "https://github.com/sickn33/antigravity-awesome-skills.git",
        "main",
    ),
    "addyosmani": SyncSpec(
        "addyosmani",
        "https://github.com/addyosmani/agent-skills.git",
        "main",
    ),
    "prompt-improver": SyncSpec(
        "prompt-improver",
        "https://github.com/ckelsoe/prompt-architect.git",
        "main",
    ),
}

ADDYOSMANI_SKILLS = (
    "test-driven-development",
    "code-review-and-quality",
    "code-simplification",
    "security-and-hardening",
    "documentation-and-adrs",
    "debugging-and-error-recovery",
    "git-workflow-and-versioning",
    "spec-driven-development",
    "planning-and-task-breakdown",
    "api-and-interface-design",
    "performance-optimization",
    "frontend-ui-engineering",
)

ADDYOSMANI_REFERENCES = {
    "test-driven-development": "testing-patterns.md",
    "security-and-hardening": "security-checklist.md",
    "performance-optimization": "performance-checklist.md",
    "frontend-ui-engineering": "accessibility-checklist.md",
}


def list_updatable(repo_root: Path) -> list[str]:
    """Lista, em ordem alfabética, as skills com metadados de upstream."""

    skills_root = repo_root / "skills"
    return sorted(
        upstream.parent.name
        for upstream in skills_root.glob("*/UPSTREAM.md")
        if upstream.is_file()
    )


def _run_git(upstream_dir: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(upstream_dir), *arguments],
            check=True,
            capture_output=True,
            text=True,
            timeout=SKILL_COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as problem:
        raise SyncError(
            "tempo limite ao ler metadados Git do upstream "
            f"({SKILL_COMMAND_TIMEOUT_SECONDS}s)"
        ) from problem
    except (OSError, subprocess.CalledProcessError) as problem:
        raise SyncError(f"falha ao ler metadados Git do upstream: {problem}") from problem
    return completed.stdout.strip()


def _validate_license(upstream_dir: Path) -> None:
    license_file = upstream_dir / "LICENSE"
    if not license_file.is_file():
        raise SyncError("LICENSE nao encontrado no upstream.")
    if "mit" not in license_file.read_text(encoding="utf-8").lower():
        raise SyncError("Licenca do upstream nao e MIT.")


def _metadata(upstream_dir: Path) -> dict[str, str]:
    return {
        "sha": _run_git(upstream_dir, "rev-parse", "HEAD"),
        "date": _run_git(upstream_dir, "log", "-1", "--format=%ci", "HEAD"),
        "synced": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def _adaptation_section(upstream_file: Path) -> str:
    if not upstream_file.is_file():
        return ""
    content = upstream_file.read_text(encoding="utf-8")
    match = re.search(
        r"^## Adaptacao da description\s*$.*?(?=^##\s|\Z)",
        content,
        flags=re.MULTILINE | re.DOTALL,
    )
    return "" if match is None else match.group(0).rstrip()


def _copy_skill_md(upstream_skill: Path, local_skill: Path) -> None:
    local_skill.mkdir(parents=True, exist_ok=True)
    destination = local_skill / "SKILL.md"
    if not destination.exists():
        shutil.copy2(upstream_skill / "SKILL.md", destination)


def _write_upstream(
    local_skill: Path,
    *,
    metadata: dict[str, str],
    repository: str,
    branch: str,
    files: list[str],
    update_command: str,
    license_text: str,
    extra_fields: list[str] | None = None,
) -> None:
    adaptation = _adaptation_section(local_skill / "UPSTREAM.md")
    lines = [
        "# Metadados do Upstream",
        "",
        f"repositorio: {repository}",
        f"branch: {branch}",
    ]
    if extra_fields:
        lines.extend(extra_fields)
    lines.extend(
        [
            f"commit: {metadata['sha']}",
            f"data_commit: {metadata['date']}",
            f"sincronizado_em: {metadata['synced']}",
            "",
            "## Arquivos sincronizados",
            "",
        ]
    )
    lines.extend(f"- {file}" for file in files)
    lines.extend(
        [
            "",
            "## Nao sincronizado",
            "",
            "- SKILL.md  (versao adaptada para OpenCode - mantenha manualmente)",
            "",
            "## Como atualizar",
            "",
            "Execute a partir da raiz do repo:",
            "",
            f"    {update_command}",
            "",
            "Para verificar se ha atualizacoes sem sincronizar:",
            "",
            f"    {update_command} --check-only",
            "",
            "## Licenca",
            "",
            license_text,
        ]
    )
    if adaptation:
        lines.extend(["", adaptation])
    (local_skill / "UPSTREAM.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _sync_accessibility(
    repo_root: Path,
    upstream_dir: Path,
    metadata: dict[str, str],
) -> None:
    upstream_skill = (
        upstream_dir
        / "skills"
        / "accessibility-compliance-accessibility-audit"
    )
    if not (upstream_skill / "SKILL.md").is_file():
        raise SyncError("Path upstream da accessibility-audit nao encontrado.")

    local_skill = repo_root / "skills" / "accessibility-audit"
    _copy_skill_md(upstream_skill, local_skill)
    playbook = upstream_skill / "resources" / "implementation-playbook.md"
    if playbook.is_file():
        resources = local_skill / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        shutil.copy2(playbook, resources / playbook.name)

    _write_upstream(
        local_skill,
        metadata=metadata,
        repository=SPECS["accessibility-audit"].repository,
        branch=SPECS["accessibility-audit"].branch,
        files=["resources/implementation-playbook.md"],
        update_command="opencode-skills sync accessibility-audit",
        license_text=(
            "MIT License + CC BY 4.0\n"
            "- MIT: Copyright (c) sickn33/antigravity-awesome-skills\n"
            "- CC BY 4.0 se aplica ao conteudo das skills\n"
            "- https://github.com/sickn33/antigravity-awesome-skills/blob/main/LICENSE"
        ),
    )


def _sync_addyosmani(
    repo_root: Path,
    upstream_dir: Path,
    metadata: dict[str, str],
) -> None:
    license_text = (
        "MIT License - Copyright (c) Addy Osmani\n"
        "https://github.com/addyosmani/agent-skills/blob/main/LICENSE"
    )
    for skill_name in ADDYOSMANI_SKILLS:
        upstream_skill = upstream_dir / "skills" / skill_name
        if not (upstream_skill / "SKILL.md").is_file():
            continue

        local_skill = repo_root / "skills" / skill_name
        _copy_skill_md(upstream_skill, local_skill)
        files = [f"skills/{skill_name}/SKILL.md  (copiado apenas na criacao inicial)"]

        reference_name = ADDYOSMANI_REFERENCES.get(skill_name)
        if reference_name:
            reference = upstream_dir / "references" / reference_name
            if reference.is_file():
                references = local_skill / "references"
                references.mkdir(parents=True, exist_ok=True)
                shutil.copy2(reference, references / reference_name)
                files.append(f"references/{reference_name}")

        _write_upstream(
            local_skill,
            metadata=metadata,
            repository=SPECS["addyosmani"].repository,
            branch=SPECS["addyosmani"].branch,
            files=files,
            update_command="opencode-skills sync addyosmani",
            license_text=license_text,
        )


def _prompt_skill_dir(upstream_dir: Path) -> Path:
    for candidate in (
        upstream_dir / "skills" / "prompt-architect",
        upstream_dir / "prompt-architect",
    ):
        if candidate.is_dir():
            return candidate
    raise SyncError("Diretorio da skill prompt-improver nao encontrado.")


def _replace_directory(source: Path, destination: Path) -> None:
    if not source.is_dir():
        return
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def _sync_prompt_improver(
    repo_root: Path,
    upstream_dir: Path,
    metadata: dict[str, str],
) -> None:
    upstream_skill = _prompt_skill_dir(upstream_dir)
    if not (upstream_skill / "SKILL.md").is_file():
        raise SyncError("SKILL.md da prompt-improver nao encontrado.")

    local_skill = repo_root / "skills" / "prompt-improver"
    _copy_skill_md(upstream_skill, local_skill)
    for directory in ("references", "assets", "scripts"):
        _replace_directory(
            upstream_skill / directory,
            local_skill / directory,
        )

    license_file = upstream_dir / "LICENSE"
    shutil.copy2(license_file, local_skill / "LICENSE")
    version = ""
    package_file = upstream_dir / "package.json"
    if package_file.is_file():
        package = json.loads(package_file.read_text(encoding="utf-8"))
        version = str(package.get("version", ""))

    files = [
        "references/ (copiado do upstream)",
        "assets/ (copiado do upstream)",
        "scripts/ (copiado do upstream)",
        "LICENSE",
    ]
    extra_fields = [f"versao: {version}"] if version else None
    _write_upstream(
        local_skill,
        metadata=metadata,
        repository=SPECS["prompt-improver"].repository,
        branch=SPECS["prompt-improver"].branch,
        files=files,
        update_command="opencode-skills sync prompt-improver",
        license_text=(
            "MIT License - Copyright (c) 2025-2026 prompt-architect contributors\n"
            "Autoria original: Charles Kelsoe\n"
        ),
        extra_fields=extra_fields,
    )


def sync_skill(
    name: str,
    repo_root: Path,
    upstream_dir: Path,
    *,
    check_only: bool = False,
) -> SyncResult:
    """Sincroniza um upstream já clonado em um repositório local."""

    if name not in SPECS:
        raise SyncError(f"Upstream desconhecido: {name}")
    _validate_license(upstream_dir)
    metadata = _metadata(upstream_dir)
    if check_only:
        return SyncResult("check-only")

    if name == "accessibility-audit":
        _sync_accessibility(repo_root, upstream_dir, metadata)
    elif name == "addyosmani":
        _sync_addyosmani(repo_root, upstream_dir, metadata)
    else:
        _sync_prompt_improver(repo_root, upstream_dir, metadata)
    return SyncResult("success")


def _documented_commands(upstream_file: Path) -> list[str]:
    section = False
    fenced = False
    commands: list[str] = []
    for raw_line in upstream_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not section and re.fullmatch(r"##\s+Como atualizar", line):
            section = True
            continue
        if not section:
            continue
        if not fenced and re.match(r"^##\s+", line):
            break
        if line.startswith("```"):
            fenced = not fenced
            continue

        candidate = ""
        if fenced:
            candidate = line.strip()
        elif line.startswith("    "):
            candidate = line[4:].strip()
        elif line.startswith("\t"):
            candidate = line.lstrip("\t").strip()
        if not candidate:
            continue
        try:
            first = shlex.split(candidate)[0]
        except ValueError:
            continue
        if first in {"bash", "sh", "python", "python3", "opencode-skills"}:
            commands.append(candidate)
        elif first.startswith("./") or first.startswith("scripts/"):
            commands.append(candidate)
    return commands


def _run_documented_command(
    command: str,
    repo_root: Path,
) -> tuple[int, str]:
    try:
        tokens = shlex.split(command)
        if not tokens:
            return 1, ""
        if tokens[0] == "opencode-skills":
            executable = shutil.which("opencode-skills")
            if executable:
                argv = [executable, *tokens[1:]]
            else:
                argv = [
                    sys.executable,
                    "-m",
                    "opencode_config.cli.skills_sync",
                    *tokens[1:],
                ]
            completed = subprocess.run(
                argv,
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=SKILL_COMMAND_TIMEOUT_SECONDS,
            )
        else:
            completed = subprocess.run(
                command,
                cwd=repo_root,
                shell=True,
                capture_output=True,
                text=True,
                timeout=SKILL_COMMAND_TIMEOUT_SECONDS,
            )
    except subprocess.TimeoutExpired as problem:
        return (
            1,
            "comando de atualizacao excedeu o tempo limite de "
            f"{SKILL_COMMAND_TIMEOUT_SECONDS}s: {problem}",
        )
    except (OSError, ValueError) as problem:
        return 1, str(problem)
    return completed.returncode, completed.stdout + completed.stderr


def _supports_assume_yes(command: str, repo_root: Path) -> bool:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    if "--yes" in tokens:
        return True
    if len(tokens) >= 2 and tokens[:2] == ["opencode-skills", "sync"]:
        return True
    if not tokens:
        return False

    local_script: Path | None = None
    if tokens[0] in {"bash", "sh", "python", "python3"} and len(tokens) >= 2:
        local_script = Path(tokens[1])
    elif tokens[0].startswith("./") or tokens[0].startswith("scripts/"):
        local_script = Path(tokens[0])
    if local_script is None:
        return False
    if not local_script.is_absolute():
        local_script = repo_root / local_script
    if not local_script.is_file():
        return False
    return "--yes" in local_script.read_text(encoding="utf-8")


def _format_update_result(
    skill_name: str,
    status: str,
    summary: str,
    *,
    details: str = "",
) -> UpdateResult:
    lines = [
        f"skill: {skill_name}",
        f"status: {status}",
        f"summary: {summary}",
    ]
    if details:
        lines.extend(["output:", details])
    return UpdateResult(status, "\n".join(lines))


def update_skill(
    repo_root: Path,
    skill_name: str,
    *,
    dry_run: bool = False,
) -> UpdateResult:
    """Executa o fluxo documentado de atualização de uma skill."""

    upstream_file = repo_root / "skills" / skill_name / "UPSTREAM.md"
    if not upstream_file.is_file():
        return _format_update_result(
            skill_name,
            "no-clear-update-flow",
            "skill sem UPSTREAM.md; nao e considerada atualizavel",
        )

    commands = _documented_commands(upstream_file)
    update_commands = [
        command for command in commands if "--check-only" not in command
    ]
    check_commands = [
        command for command in commands if "--check-only" in command
    ]
    if not update_commands:
        return _format_update_result(
            skill_name,
            "no-clear-update-flow",
            "UPSTREAM.md encontrado, mas sem comando de atualizacao "
            "claramente identificavel",
        )
    if len(update_commands) > 1:
        candidates = "\n".join(
            f"candidate_update_command: {command}" for command in update_commands
        )
        return _format_update_result(
            skill_name,
            "ambiguous-update-flow",
            "UPSTREAM.md possui multiplos comandos candidatos de atualizacao",
            details=candidates,
        )

    update_command = update_commands[0]
    check_summary = "nao executado"
    if check_commands:
        check_code, check_output = _run_documented_command(
            check_commands[0],
            repo_root,
        )
        if check_code == 0 and "Ja esta atualizado" in check_output:
            check_summary = "ja estava atualizada"
            if dry_run:
                return _format_update_result(
                    skill_name,
                    "dry-run",
                    "modo dry-run — check-only confirma que a skill ja esta atualizada",
                    details=check_output,
                )
            return _format_update_result(
                skill_name,
                "already-up-to-date",
                "nenhuma atualizacao necessaria",
                details=check_output,
            )
        if check_code == 0 and "Atualizacao disponivel" in check_output:
            check_summary = "ha atualizacao disponivel"
        else:
            check_summary = "check-only falhou; update sera tentado mesmo assim"

    if not _supports_assume_yes(update_command, repo_root):
        return _format_update_result(
            skill_name,
            "non-interactive-mode-not-found",
            "fluxo encontrado, mas nao ha modo nao interativo claramente "
            "identificavel para executar com seguranca",
        )

    executed_command = (
        update_command
        if "--yes" in shlex.split(update_command)
        else f"{update_command} --yes"
    )
    if dry_run:
        return _format_update_result(
            skill_name,
            "dry-run",
            "modo dry-run - nenhuma atualizacao foi executada",
            details=f"executed_command: (nao executado) {executed_command}",
        )

    previous_metadata = upstream_file.read_bytes()
    update_code, update_output = _run_documented_command(
        executed_command,
        repo_root,
    )
    if update_code == 0:
        return _format_update_result(
            skill_name,
            "success",
            "skill atualizada com sucesso",
            details=update_output,
        )

    upstream_file.write_bytes(previous_metadata)
    return _format_update_result(
        skill_name,
        "error",
        "erro ao executar a atualizacao da skill; UPSTREAM.md restaurado",
        details=update_output,
    )


def _clone_upstream(spec: SyncSpec) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temporary = tempfile.TemporaryDirectory(prefix="opencode-skills-")
    destination = Path(temporary.name) / "upstream"
    try:
        subprocess.run(
            [
                "git",
                "clone",
                "--depth=1",
                "--branch",
                spec.branch,
                spec.repository,
                str(destination),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=SKILL_COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as problem:
        temporary.cleanup()
        raise SyncError(
            "tempo limite ao clonar upstream "
            f"({SKILL_COMMAND_TIMEOUT_SECONDS}s)"
        ) from problem
    except (OSError, subprocess.CalledProcessError) as problem:
        temporary.cleanup()
        raise SyncError(f"falha ao clonar upstream: {problem}") from problem
    return temporary, destination


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opencode-skills",
        description="Sincroniza skills externas e lista skills atualizaveis.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list",
        help="lista skills atualizaveis",
        description="lista skills atualizaveis deste repositorio.",
    )
    list_parser.add_argument("--repo-root", type=Path, default=None)

    sync_parser = subparsers.add_parser("sync", help="sincroniza um upstream")
    sync_parser.add_argument("name", choices=tuple(SPECS))
    sync_parser.add_argument("--yes", action="store_true")
    sync_parser.add_argument("--check-only", action="store_true")
    sync_parser.add_argument("--repo-root", type=Path, default=None)
    update_parser = subparsers.add_parser(
        "update",
        help="atualiza uma skill pelo UPSTREAM.md",
        description="atualiza uma skill usando o fluxo documentado no UPSTREAM.md.",
    )
    update_parser.add_argument("skill")
    update_parser.add_argument("--dry-run", action="store_true")
    update_parser.add_argument("--repo-root", type=Path, default=None)
    return parser


def run(
    arguments: list[str],
    *,
    output: TextIO,
    error: TextIO,
) -> int:
    try:
        parsed = _build_parser().parse_args(arguments)
        repo_root = (
            Path(__file__).resolve().parents[3]
            if parsed.repo_root is None
            else parsed.repo_root.expanduser().resolve()
        )
        if parsed.command == "list":
            skills = list_updatable(repo_root)
            output.write("\n".join(skills))
            if skills:
                output.write("\n")
            return 0
        if parsed.command == "update":
            result = update_skill(
                repo_root,
                parsed.skill,
                dry_run=parsed.dry_run,
            )
            output.write(f"{result.output}\n")
            return 0

        if not parsed.check_only and not parsed.yes:
            answer = input("Confirma a sincronizacao? [s/N] ").strip().lower()
            if answer not in {"s", "sim", "y", "yes"}:
                output.write("Cancelado.\n")
                return 0

        spec = SPECS[parsed.name]
        temporary, upstream_dir = _clone_upstream(spec)
        try:
            result = sync_skill(
                parsed.name,
                repo_root,
                upstream_dir,
                check_only=parsed.check_only,
            )
        finally:
            temporary.cleanup()
        output.write(f"status: {result.status}\n")
        return 0
    except (SyncError, OSError, ValueError) as problem:
        error.write(f"ERRO: {problem}\n")
        return 1


def main(argv: list[str] | None = None) -> int:
    """Executa o entrypoint `opencode-skills`."""

    return run(
        list(sys.argv[1:] if argv is None else argv),
        output=sys.stdout,
        error=sys.stderr,
    )


if __name__ == "__main__":
    raise SystemExit(main())
