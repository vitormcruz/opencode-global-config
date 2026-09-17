"""Entrypoint comum das suites de testes-produto."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TextIO

from .interface import Finding, ProductReport, emit_report

Suite = Callable[[Path], ProductReport]


def _utf8(stream: TextIO) -> None:
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8", errors="replace")


def _invalid_arguments(tool: str) -> ProductReport:
    return ProductReport.from_findings(
        [
            Finding(
                "bloqueante",
                tool,
                "a suite nao aceita argumentos; execute sem argumentos",
            )
        ]
    )


def _unexpected_crash(tool: str, error: BaseException) -> ProductReport:
    return ProductReport.from_findings(
        [Finding("bloqueante", tool, f"crash da suite: {error}")]
    )


def run_entrypoint(
    argv: Sequence[str] | None,
    suite: Suite,
    *,
    tool: str,
    output: TextIO | None = None,
    error: TextIO | None = None,
    repo_root: Path | None = None,
) -> int:
    """Aplica o contrato de streams, argumentos, JSON e exit code."""

    output = sys.stdout if output is None else output
    error = sys.stderr if error is None else error
    _utf8(output)
    _utf8(error)
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments:
        report = _invalid_arguments(tool)
    else:
        root = Path(__file__).resolve().parents[3] if repo_root is None else repo_root
        print(f"[{tool}] iniciando suite", file=error, flush=True)
        try:
            report = suite(root)
        except Exception as caught:  # noqa: BLE001
            report = _unexpected_crash(tool, caught)
        print(f"[{tool}] suite concluida: {report.status}", file=error, flush=True)
    emit_report(report, output)
    return 0 if report.status == "pass" else 1
