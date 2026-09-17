"""Agregador puro das suites de especialidade."""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from .interface import (
    Finding,
    ProductReport,
    ReportFormatError,
    decode_report,
    emit_report,
)
from .process import Progress, Runner, run_process

SUITE_NAMES = ("backend", "seguranca")


def _utf8(stream: TextIO) -> None:
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8", errors="replace")


def _suite_failure(name: str, message: str) -> Finding:
    return Finding("bloqueante", f"testes-produto/{name}", message)


def _run_suite(
    root: Path,
    name: str,
    *,
    runner: Runner,
    progress: Progress,
) -> tuple[ProductReport | None, list[Finding]]:
    script = root / "testes-produto" / name
    if not script.is_file():
        return None, [_suite_failure(name, "script da suite ausente")]
    command = [sys.executable, os.fspath(script)]
    try:
        completed = runner(
            command,
            cwd=root,
            progress=progress,
            env=None,
            label=f"testes-produto/{name}",
        )
    except OSError as error:
        return None, [_suite_failure(name, f"crash ao iniciar suite: {error}")]
    if completed.error:
        return None, [_suite_failure(name, f"crash ao iniciar suite: {completed.error}")]
    if completed.returncode not in {0, 1}:
        return None, [
            _suite_failure(
                name,
                f"exit inesperado {completed.returncode}; stderr: "
                f"{' '.join(completed.stderr.split())[-1000:]}",
            )
        ]
    try:
        report = decode_report(completed.stdout)
    except ReportFormatError as error:
        return None, [_suite_failure(name, f"JSON invalido: {error}")]
    if completed.returncode == 0 and report.status == "fail":
        return None, [_suite_failure(name, "suite declarou fail com exit 0")]
    if completed.returncode == 1 and report.status == "pass":
        return None, [_suite_failure(name, "suite declarou pass com exit 1")]
    return report, []


def run_aggregator(
    root: Path,
    *,
    runner: Runner = run_process,
    progress: Progress | None = None,
) -> ProductReport:
    """Chama as suites e consolida findings, sem executar Concordion diretamente."""

    progress = (lambda _message: None) if progress is None else progress
    findings: list[Finding] = []
    declared_failure = False
    for name in SUITE_NAMES:
        progress(f"[testes-produto] executando {name}")
        report, failures = _run_suite(
            root,
            name,
            runner=runner,
            progress=progress,
        )
        findings.extend(failures)
        if report is not None:
            findings.extend(report.findings)
            declared_failure = declared_failure or report.status == "fail"
    return ProductReport(
        tuple(findings),
        declared_status="fail" if declared_failure else None,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Entrypoint do agregador instalado como ``testes-produto``."""

    arguments = list(sys.argv[1:] if argv is None else argv)
    _utf8(sys.stdout)
    _utf8(sys.stderr)
    if arguments:
        report = ProductReport.from_findings(
            [
                Finding(
                    "bloqueante",
                    "testes-produto",
                    "o agregador nao aceita argumentos; execute sem argumentos",
                )
            ]
        )
    else:
        root = Path(__file__).resolve().parents[3]
        report = run_aggregator(
            root,
            progress=lambda message: print(message, file=sys.stderr, flush=True),
        )
    emit_report(report, sys.stdout)
    return 0 if report.status == "pass" else 1
