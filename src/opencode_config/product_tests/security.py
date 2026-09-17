"""Suite de seguranca do testes-produto."""

from __future__ import annotations

import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from .concordion import load_json_output, run_concordion_suite
from .interface import Finding, ProductReport
from .process import (
    ProcessResult,
    Progress,
    Runner,
    run_process,
    run_with_network_retry,
)

Which = Callable[[str], str | None]


def _progress(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _short_process_message(result: ProcessResult) -> str:
    text = result.error or result.stderr or result.stdout
    return " ".join(text.split())[-1500:] or (
        f"processo terminou com exit {result.returncode}"
    )


def _json_failure(tool: str, error: Exception) -> Finding:
    return Finding("bloqueante", tool, f"JSON invalido: {error}")


def _severity(value: object) -> str:
    normalized = str(value or "").casefold()
    if normalized in {"high", "critical"}:
        return "bloqueante"
    if normalized in {"low", "moderate", "medium", "info", "informational"}:
        return "melhoria"
    return "bloqueante"


def findings_from_pip_audit(payload: object) -> list[Finding]:
    """Converte o formato JSON do pip-audit no schema da suite."""

    dependencies: object
    if isinstance(payload, dict):
        dependencies = payload.get("dependencies")
    else:
        dependencies = payload
    if not isinstance(dependencies, list):
        return [Finding("bloqueante", "pip-audit", "JSON invalido: dependencies")]

    findings: list[Finding] = []
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            return [Finding("bloqueante", "pip-audit", "JSON invalido: dependencia")]
        package = dependency.get("name", "pacote desconhecido")
        vulnerabilities = dependency.get("vulns", [])
        if not isinstance(vulnerabilities, list):
            return [Finding("bloqueante", "pip-audit", "JSON invalido: vulns")]
        for vulnerability in vulnerabilities:
            if not isinstance(vulnerability, dict):
                return [
                    Finding("bloqueante", "pip-audit", "JSON invalido: vulnerabilidade")
                ]
            identifier = vulnerability.get("id", "identificador ausente")
            severity = _severity(vulnerability.get("severity"))
            findings.append(
                Finding(
                    severity,
                    "pip-audit",
                    f"{package}: {identifier} ({severity})",
                )
            )
    return findings


def findings_from_bandit(payload: object) -> list[Finding]:
    """Converte o JSON do Bandit preservando severidade como bloqueante/melhoria."""

    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        return [Finding("bloqueante", "bandit", "JSON invalido: results")]

    findings: list[Finding] = []
    for result in payload["results"]:
        if not isinstance(result, dict):
            return [Finding("bloqueante", "bandit", "JSON invalido: result")]
        filename = result.get("filename", "arquivo desconhecido")
        line = result.get("line_number", "?")
        issue = result.get("issue_text", "achado sem descricao")
        findings.append(
            Finding(
                _severity(result.get("issue_severity")),
                "bandit",
                f"{filename}:{line}: {issue}",
            )
        )
    return findings


def _run_gitleaks(
    repo_root: Path,
    *,
    which: Which,
    runner: Runner,
    progress: Progress,
) -> list[Finding]:
    executable = which("gitleaks")
    if executable is None:
        return [Finding("bloqueante", "gitleaks", "ferramenta ausente; instale em user-space")]
    result = runner(
        [executable, "detect", "--source", str(repo_root), "--no-banner", "--redact", "--exit-code", "1"],
        cwd=repo_root,
        progress=progress,
        env=None,
        label="gitleaks",
    )
    if result.succeeded:
        return []
    return [
        Finding(
            "bloqueante",
            "gitleaks",
            "segredo detectado ou execução do scan falhou; verifique a saída local",
        )
    ]


def _run_pip_audit(
    repo_root: Path,
    *,
    which: Which,
    runner: Runner,
    progress: Progress,
) -> list[Finding]:
    executable = which("pip-audit")
    if executable is None:
        return [Finding("bloqueante", "pip-audit", "ferramenta ausente; instale via pipx")]
    result = run_with_network_retry(
        [executable, "--local", "--format=json"],
        cwd=repo_root,
        progress=progress,
        runner=runner,
        label="pip-audit",
    )
    if result.error:
        return [Finding("bloqueante", "pip-audit", _short_process_message(result))]
    try:
        payload = load_json_output(result, tool="pip-audit")
    except ValueError as error:
        return [_json_failure("pip-audit", error)]
    return findings_from_pip_audit(payload)


def _run_bandit(
    repo_root: Path,
    *,
    which: Which,
    runner: Runner,
    progress: Progress,
) -> list[Finding]:
    executable = which("bandit")
    if executable is None:
        return [Finding("bloqueante", "bandit", "ferramenta ausente; instale via pipx")]
    sources = [
        path
        for path in (
            repo_root / "src",
            repo_root / "scripts",
            repo_root / "testes-produto",
        )
        if path.exists()
    ]
    result = runner(
        [executable, "-r", *[str(path) for path in sources], "-f", "json"],
        cwd=repo_root,
        progress=progress,
        env=None,
        label="bandit",
    )
    if result.error:
        return [Finding("bloqueante", "bandit", _short_process_message(result))]
    try:
        payload = load_json_output(result, tool="bandit")
    except ValueError as error:
        return [_json_failure("bandit", error)]
    return findings_from_bandit(payload)


def run_security_suite(
    repo_root: Path,
    *,
    which: Which = shutil.which,
    runner: Runner = run_process,
    progress: Progress = _progress,
) -> ProductReport:
    """Executa secrets scan, dependency audit, SAST e specs Concordion."""

    findings = _run_gitleaks(
        repo_root,
        which=which,
        runner=runner,
        progress=progress,
    )
    findings.extend(
        _run_pip_audit(
            repo_root,
            which=which,
            runner=runner,
            progress=progress,
        )
    )
    findings.extend(
        _run_bandit(
            repo_root,
            which=which,
            runner=runner,
            progress=progress,
        )
    )
    findings.extend(
        run_concordion_suite(
            repo_root,
            specialty="seguranca",
            which=which,
            runner=runner,
            progress=progress,
        ).findings
    )
    return ProductReport.from_findings(findings)


def main(argv: list[str] | None = None) -> int:
    """Entrypoint sem argumentos da suite de seguranca."""

    from .runner import run_entrypoint

    return run_entrypoint(
        argv,
        lambda root: run_security_suite(root),
        tool="seguranca",
    )
