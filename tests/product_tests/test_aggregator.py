from pathlib import Path

import pytest

from opencode_config.product_tests.aggregator import run_aggregator
from opencode_config.product_tests.process import ProcessResult


def successful_suite(name: str) -> ProcessResult:
    return ProcessResult(
        command=(name,),
        returncode=0,
        stdout='{"status":"pass","findings":[]}',
        stderr="",
    )


@pytest.mark.unit
def test_aggregator_consolidates_findings_without_running_concordion(
    tmp_path: Path,
) -> None:
    (tmp_path / "testes-produto").mkdir()
    for name in ("backend", "seguranca"):
        (tmp_path / "testes-produto" / name).touch()
    commands: list[tuple[str, ...]] = []

    def runner(command, **_kwargs):
        commands.append(tuple(str(item) for item in command))
        if command[-1].endswith("backend"):
            return ProcessResult(
                command=tuple(str(item) for item in command),
                returncode=1,
                stdout=(
                    '{"status":"fail","findings":[{"severity":"bloqueante",'
                    '"tool":"pytest","message":"falhou"}]}'
                ),
                stderr="",
            )
        return successful_suite("seguranca")

    report = run_aggregator(tmp_path, runner=runner)

    assert report.status == "fail"
    assert report.findings[0].tool == "pytest"
    assert all("concordion" not in command for command in commands)


@pytest.mark.unit
def test_aggregator_turns_invalid_child_json_into_blocking_finding(
    tmp_path: Path,
) -> None:
    suites = tmp_path / "testes-produto"
    suites.mkdir()
    (suites / "backend").touch()
    (suites / "seguranca").touch()

    def runner(command, **_kwargs):
        return ProcessResult(tuple(str(item) for item in command), 0, "{}", "")

    report = run_aggregator(tmp_path, runner=runner)

    assert report.status == "fail"
    assert all(finding.severity == "bloqueante" for finding in report.findings)
    assert "JSON invalido" in report.findings[0].message


@pytest.mark.unit
def test_aggregator_reports_a_crashed_child(tmp_path: Path) -> None:
    suites = tmp_path / "testes-produto"
    suites.mkdir()
    (suites / "backend").touch()
    (suites / "seguranca").touch()

    def runner(command, **_kwargs):
        return ProcessResult(tuple(str(item) for item in command), None, "", "", "crash")

    report = run_aggregator(tmp_path, runner=runner)

    assert report.status == "fail"
    assert report.findings[0].severity == "bloqueante"
