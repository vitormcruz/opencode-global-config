"""Suite backend do testes-produto."""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

from .concordion import run_concordion_suite
from .interface import Finding, ProductReport
from .process import ProcessResult, Progress, Runner, run_process

Which = Callable[[str], str | None]


def _progress(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _source_paths(repo_root: Path) -> tuple[Path, ...]:
    return tuple(
        path
        for path in (
            repo_root / "src",
            repo_root / "scripts",
            repo_root / "testes-produto",
        )
        if path.exists()
    )


def _python_executable(repo_root: Path) -> Path | None:
    candidates = (
        repo_root / ".venv" / "bin" / "python",
        repo_root / ".venv" / "Scripts" / "python.exe",
    )
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def _short_process_message(result: ProcessResult) -> str:
    text = result.error or result.stderr or result.stdout
    compact = " ".join(text.split())
    return compact[-1500:] or f"processo terminou com exit {result.returncode}"


def _run_check(
    executable: str,
    arguments: Iterable[str | os.PathLike[str]],
    *,
    repo_root: Path,
    tool: str,
    runner: Runner,
    progress: Progress,
) -> list[Finding]:
    command = [executable, *[os.fspath(argument) for argument in arguments]]
    result = runner(command, cwd=repo_root, progress=progress, env=None, label=tool)
    if result.succeeded:
        return []
    return [Finding("bloqueante", tool, _short_process_message(result))]


def _pytest_findings(
    repo_root: Path,
    *,
    runner: Runner,
    progress: Progress,
) -> list[Finding]:
    python = _python_executable(repo_root)
    if python is None:
        return [
            Finding(
                "bloqueante",
                "pytest",
                "executavel da .venv ausente; execute o bootstrap user-space",
            )
        ]

    arguments = [
        "-m",
        "pytest",
        "-m",
        "all",
        "--cov=src",
        "--cov=scripts",
        "--cov=testes-produto",
        "--cov-report=term-missing",
        "--cov-fail-under=70",
    ]
    return _run_check(
        os.fspath(python),
        arguments,
        repo_root=repo_root,
        tool="pytest",
        runner=runner,
        progress=progress,
    )


def _lint_findings(
    repo_root: Path,
    *,
    which: Which,
    runner: Runner,
    progress: Progress,
) -> list[Finding]:
    findings: list[Finding] = []
    sources = _source_paths(repo_root)

    ruff = which("ruff")
    if ruff is None:
        findings.append(
            Finding("bloqueante", "ruff", "ferramenta ausente; instale via pipx")
        )
    else:
        findings.extend(
            _run_check(
                ruff,
                ["check", *sources],
                repo_root=repo_root,
                tool="ruff",
                runner=runner,
                progress=progress,
            )
        )

    scripts_directory = repo_root / "scripts"
    shell_files = sorted(scripts_directory.rglob("*.sh")) if scripts_directory.exists() else []
    shellcheck = which("shellcheck")
    if shellcheck is None:
        findings.append(
            Finding(
                "bloqueante",
                "shellcheck",
                "ferramenta ausente; instale em user-space, inclusive no Windows",
            )
        )
    elif shell_files:
        findings.extend(
            _run_check(
                shellcheck,
                shell_files,
                repo_root=repo_root,
                tool="shellcheck",
                runner=runner,
                progress=progress,
            )
        )

    powershell_files = (
        sorted(scripts_directory.rglob("*.ps1"))
        if scripts_directory.exists()
        else []
    )
    pwsh = which("pwsh")
    if pwsh is None:
        findings.append(
            Finding(
                "bloqueante",
                "PSScriptAnalyzer",
                "pwsh ausente; instale PowerShell Core em user-space",
            )
        )
    elif powershell_files:
        probe = runner(
            [
                pwsh,
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "Import-Module PSScriptAnalyzer -ErrorAction Stop",
            ],
            cwd=repo_root,
            progress=progress,
            env=None,
            label="PSScriptAnalyzer",
        )
        if probe.error or probe.returncode != 0:
            findings.append(
                Finding(
                    "bloqueante",
                    "PSScriptAnalyzer",
                    "modulo PSScriptAnalyzer ausente ou nao carregavel; instale "
                    "com Install-Module PSScriptAnalyzer -Scope CurrentUser",
                )
            )
        else:
            findings.extend(
                _analyze_powershell_scripts(
                    repo_root,
                    pwsh=pwsh,
                    scripts=powershell_files,
                    runner=runner,
                    progress=progress,
                )
            )
    return findings


def _analyze_powershell_scripts(
    repo_root: Path,
    *,
    pwsh: str,
    scripts: list[Path],
    runner: Runner,
    progress: Progress,
) -> list[Finding]:
    findings: list[Finding] = []
    for script in scripts:
        escaped = os.fspath(script).replace("'", "''")
        command = [
            pwsh,
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            (
                "Import-Module PSScriptAnalyzer -ErrorAction Stop; "
                f"$items = Invoke-ScriptAnalyzer -LiteralPath '{escaped}'; "
                "$items | ConvertTo-Json -Compress"
            ),
        ]
        result = runner(
            command,
            cwd=repo_root,
            progress=progress,
            env=None,
            label="PSScriptAnalyzer",
        )
        if result.error or result.returncode != 0:
            findings.append(
                Finding(
                    "bloqueante",
                    "PSScriptAnalyzer",
                    f"falha de execucao do analyzer em "
                    f"{script.relative_to(repo_root)}: "
                    f"{_short_process_message(result)}",
                )
            )
            continue
        if result.stdout.strip() and result.stdout.strip() not in {"null", "[]"}:
            findings.append(
                Finding(
                    "bloqueante",
                    "PSScriptAnalyzer",
                    f"violacoes encontradas em {script.relative_to(repo_root)}",
                )
            )
    return findings


def run_backend_suite(
    repo_root: Path,
    *,
    which: Which = shutil.which,
    runner: Runner = run_process,
    progress: Progress = _progress,
) -> ProductReport:
    """Executa checks backend, incluindo as specs Concordion da especialidade."""

    findings = _pytest_findings(repo_root, runner=runner, progress=progress)
    findings.extend(
        _lint_findings(
            repo_root,
            which=which,
            runner=runner,
            progress=progress,
        )
    )
    findings.extend(
        run_concordion_suite(
            repo_root,
            specialty="backend",
            which=which,
            runner=runner,
            progress=progress,
        ).findings
    )
    return ProductReport.from_findings(findings)


def main(argv: list[str] | None = None) -> int:
    """Entrypoint sem argumentos da suite backend."""

    from .runner import run_entrypoint

    return run_entrypoint(
        argv,
        lambda root: run_backend_suite(root),
        tool="backend",
    )
