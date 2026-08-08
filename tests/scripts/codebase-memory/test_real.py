"""Testes do binario real codebase-memory-mcp."""

from __future__ import annotations

import shutil
import subprocess

import pytest


pytestmark = pytest.mark.tools


def _require_codebase_memory() -> str:
    executable = shutil.which("codebase-memory-mcp")
    if executable is None:
        pytest.fail(
            "codebase-memory-mcp nao disponivel neste ambiente — "
            "instale codebase-memory-mcp para executar este teste"
        )

    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        pytest.fail(
            "codebase-memory-mcp existe no PATH mas nao executa: "
            f"{error}"
        )

    if result.returncode != 0:
        pytest.fail(
            "codebase-memory-mcp existe no PATH mas nao executa. "
            f"Saida: {result.stdout or result.stderr}"
        )
    return executable


def test_codebase_memory_binary_responds_to_help() -> None:
    executable = _require_codebase_memory()
    result = subprocess.run(
        [executable, "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0


def test_codebase_memory_binary_accepts_version_command() -> None:
    executable = _require_codebase_memory()
    result = subprocess.run(
        [executable, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
