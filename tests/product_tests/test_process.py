import pytest
import sys
from pathlib import Path

from opencode_config.product_tests.process import (
    ProcessResult,
    is_transient_network_failure,
    run_process,
    run_with_network_retry,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "message",
    [
        "Temporary failure in name resolution",
        "connection reset by peer",
        "TLS handshake timeout",
    ],
)
def test_network_failures_are_retryable(message: str) -> None:
    result = ProcessResult(
        command=("tool",),
        returncode=1,
        stdout="",
        stderr=message,
    )

    assert is_transient_network_failure(result)


@pytest.mark.unit
def test_tool_violation_is_not_classified_as_network_failure() -> None:
    result = ProcessResult(
        command=("ruff",),
        returncode=1,
        stdout="E501 line too long",
        stderr="",
    )

    assert not is_transient_network_failure(result)


@pytest.mark.unit
def test_run_process_captures_utf8_output_and_emits_progress(tmp_path: Path) -> None:
    progress: list[str] = []

    result = run_process(
        [sys.executable, "-c", "print('olá')"],
        cwd=tmp_path,
        progress=progress.append,
    )

    assert result.succeeded
    assert result.stdout.strip() == "olá"
    assert progress == []


@pytest.mark.unit
def test_run_process_reports_missing_command_without_throwing(tmp_path: Path) -> None:
    result = run_process(
        [str(tmp_path / "missing-tool")],
        cwd=tmp_path,
        progress=lambda _message: None,
    )

    assert not result.succeeded
    assert result.error


@pytest.mark.unit
def test_network_retry_stops_after_successful_attempt(tmp_path: Path) -> None:
    attempts = 0

    def runner(command, **_kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return ProcessResult(tuple(command), 1, "", "connection reset")
        return ProcessResult(tuple(command), 0, "ok", "")

    result = run_with_network_retry(
        ["network-tool"],
        cwd=tmp_path,
        progress=lambda _message: None,
        runner=runner,
    )

    assert result.succeeded
    assert attempts == 2
