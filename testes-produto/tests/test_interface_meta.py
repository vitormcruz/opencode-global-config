from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SUITE_PATHS = (
    REPOSITORY_ROOT / "testes-produto" / "backend",
    REPOSITORY_ROOT / "testes-produto" / "seguranca",
)


def run_script(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(path)],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


@pytest.mark.unit
def test_specialty_scripts_are_argumentless_and_return_normative_json() -> None:
    for path in SUITE_PATHS:
        completed = run_script(path)
        report = json.loads(completed.stdout)
        assert set(report) == {"status", "findings"}
        assert report["status"] in {"pass", "fail"}
        assert isinstance(report["findings"], list)
        assert completed.returncode in {0, 1}


@pytest.mark.unit
def test_specialty_scripts_reject_arguments_with_json_finding() -> None:
    for path in SUITE_PATHS:
        completed = subprocess.run(
            [sys.executable, str(path), "unexpected"],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        report = json.loads(completed.stdout)
        assert completed.returncode == 1
        assert report["status"] == "fail"
        assert report["findings"][0]["severity"] == "bloqueante"


@pytest.mark.unit
def test_aggregator_returns_the_same_normative_json_contract() -> None:
    completed = subprocess.run(
        [sys.executable, str(REPOSITORY_ROOT / "testes-produto")],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    report = json.loads(completed.stdout)
    assert set(report) == {"status", "findings"}
    assert report["status"] in {"pass", "fail"}
    assert isinstance(report["findings"], list)
    assert completed.returncode in {0, 1}


@pytest.mark.unit
def test_aggregator_rejects_arguments_with_a_blocking_finding() -> None:
    completed = subprocess.run(
        [sys.executable, str(REPOSITORY_ROOT / "testes-produto"), "unexpected"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    report = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert report["status"] == "fail"
    assert report["findings"][0]["severity"] == "bloqueante"


@pytest.mark.unit
def test_aggregator_is_separate_from_the_meta_suite() -> None:
    assert (REPOSITORY_ROOT / "testes-produto" / "tests").is_dir()
    assert (REPOSITORY_ROOT / "testes-produto" / "__main__.py").is_file()
