"""Executor de scripts Playwright com cleanup garantido."""

from __future__ import annotations

from collections.abc import Sequence
import json
from pathlib import Path
import shutil
import sys
import time

from opencode_config.cli.svgtoimage import _find_playwright, _node_environment
from opencode_config.lib.process import run_command

HELP_TEXT = """opencode-browser-test

Executa um script Playwright .js e retorna resultado em JSON.

Uso:
  opencode-browser-test <path/to/script.js>

O script e deletado apos execucao (cleanup automatico).
"""


def _legacy_error(message: str) -> str:
    return json.dumps(
        {
            "ok": False,
            "error": message,
            "screenshots": [],
            "console": [],
            "errors": [message],
            "duration_ms": 0,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _emit_error(message: str) -> int:
    print(_legacy_error(message))
    return 1


def _playwright_available() -> str | None:
    launcher = _find_playwright()
    if launcher:
        return launcher

    npm = shutil.which("npm")
    if npm is None:
        return None

    result = run_command([npm, "list", "-g", "@playwright/test", "--depth=0"])
    return "" if result.succeeded else None


def _format_execution(
    *,
    stdout: str,
    stderr: str,
    returncode: int | None,
    duration_ms: int,
) -> tuple[int, str]:
    output = stdout + stderr
    if returncode == 0:
        first_line = output.splitlines()[0] if output.splitlines() else ""
        if first_line.startswith("{"):
            return 0, output.rstrip("\n") + "\n"
        return (
            0,
            json.dumps(
                {
                    "ok": True,
                    "screenshots": [],
                    "console": [output.replace("\n", " ")],
                    "errors": [],
                    "duration_ms": duration_ms,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n",
        )

    return (
        1,
        json.dumps(
            {
                "ok": False,
                "screenshots": [],
                "console": [],
                "errors": [output.replace("\n", " ")],
                "duration_ms": duration_ms,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n",
    )


def _execute_script(script_path: Path) -> tuple[int, str]:
    node = shutil.which("node")
    if node is None:
        return 1, _legacy_error(
            "node nao encontrado no PATH. Execute opencode-bootstrap --yes"
        )

    playwright = _playwright_available()
    if playwright is None:
        return 1, _legacy_error(
            "playwright nao instalado. Execute opencode-bootstrap --yes"
        )

    started = time.monotonic()
    try:
        result = run_command(
            [node, str(script_path)],
            env=_node_environment(playwright) if playwright else None,
        )
    except OSError as error:
        duration_ms = int((time.monotonic() - started) * 1000)
        return 1, _legacy_error(f"Nao foi possivel executar node: {error}")

    duration_ms = int((time.monotonic() - started) * 1000)
    return _format_execution(
        stdout=result.stdout,
        stderr=result.stderr,
        returncode=result.returncode,
        duration_ms=duration_ms,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Valida, executa e remove o script JavaScript informado."""

    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        return _emit_error("Uso: opencode-browser-test <script.js>")

    script_argument = arguments[0]
    if script_argument in {"--help", "-h"}:
        print(HELP_TEXT, end="")
        return 0

    script_path = Path(script_argument)
    if not script_argument.endswith(".js"):
        return _emit_error(f"Arquivo deve ter extensao .js: {script_argument}")
    if not script_path.is_file():
        return _emit_error(f"Arquivo nao encontrado: {script_argument}")

    try:
        status, output = _execute_script(script_path)
        print(output, end="")
        return status
    finally:
        script_path.unlink(missing_ok=True)
