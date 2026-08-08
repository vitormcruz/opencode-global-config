"""Sincronização das skills externas e de seus metadados de upstream."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import TextIO


class SyncError(RuntimeError):
    """Indica que um upstream não pode ser sincronizado com segurança."""


@dataclass(frozen=True)
class SyncResult:
    """Resultado resumido de uma sincronização."""

    status: str


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
        )
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
        )
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

    list_parser = subparsers.add_parser("list", help="lista skills atualizaveis")
    list_parser.add_argument("--repo-root", type=Path, default=None)

    sync_parser = subparsers.add_parser("sync", help="sincroniza um upstream")
    sync_parser.add_argument("name", choices=tuple(SPECS))
    sync_parser.add_argument("--yes", action="store_true")
    sync_parser.add_argument("--check-only", action="store_true")
    sync_parser.add_argument("--repo-root", type=Path, default=None)
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
            output.write("\n".join(list_updatable(repo_root)))
            if list_updatable(repo_root):
                output.write("\n")
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
