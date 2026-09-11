"""Testes da taxonomia de markers e do atalho de selecao `all`."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

from taxonomy import translate_all_alias

pytestmark = pytest.mark.unit

COLLECTION_TIMEOUT_SECONDS = 120
NO_TESTS_COLLECTED_EXIT_CODE = 5


def collect_ids(marker_expression: str, repo_root: Path) -> set[str]:
    """Coleta via subprocess os ids selecionados por uma expressao -m.

    Selecao vazia (exit code 5) e resultado valido, nao erro: a expressao
    simplesmente nao casou nenhum teste.
    """

    process = run_collection(marker_expression, repo_root)
    if process.returncode not in (0, NO_TESTS_COLLECTED_EXIT_CODE):
        process.check_returncode()
    return {line for line in process.stdout.splitlines() if "::" in line}


def run_collection(marker_expression: str, repo_root: Path) -> subprocess.CompletedProcess[str]:
    """Executa apenas a coleta com uma expressao -m e devolve o processo."""

    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-m",
            marker_expression,
            "--collect-only",
            "-q",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=COLLECTION_TIMEOUT_SECONDS,
        check=False,
    )


def test_translate_all_expands_the_alias_token() -> None:
    assert translate_all_alias("all") == "(unit or integration)"


def test_translate_all_keeps_expressions_without_the_alias() -> None:
    assert translate_all_alias("unit or agent_eval") == "unit or agent_eval"
    assert translate_all_alias("") == ""
    assert translate_all_alias(None) is None


def test_translate_all_expands_inside_larger_expressions() -> None:
    assert translate_all_alias("all and not integration") == (
        "(unit or integration) and not integration"
    )


def test_all_selects_exactly_unit_plus_integration(repo_root: Path) -> None:
    assert collect_ids("all", repo_root) == collect_ids(
        "unit or integration", repo_root
    )


def test_all_does_not_include_agent_eval(repo_root: Path) -> None:
    assert collect_ids("agent_eval", repo_root).isdisjoint(
        collect_ids("all", repo_root)
    )


def test_unknown_marker_keeps_failing(repo_root: Path) -> None:
    process = run_collection("marker_que_nao_existe", repo_root)

    assert process.returncode == NO_TESTS_COLLECTED_EXIT_CODE
