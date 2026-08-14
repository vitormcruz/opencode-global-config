"""Unit tests for the local Bonsai model server utility."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock
from urllib.error import URLError

import pytest

import bonsai_server
from bonsai_server import BonsaiServer, BonsaiServerError


pytestmark = pytest.mark.unit


class FakeProcess:
    """Minimal process double for lifecycle assertions."""

    def __init__(self, returncode: int | None = None) -> None:
        self.pid = 12345
        self.returncode = returncode
        self.terminate_calls = 0
        self.wait_calls = 0
        self.kill_calls = 0

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminate_calls += 1
        self.returncode = 0

    def wait(self, timeout: float | None = None) -> int:
        self.wait_calls += 1
        return self.returncode or 0

    def kill(self) -> None:
        self.kill_calls += 1
        self.returncode = -9


def test_model_paths_use_the_fixed_cache_layout(tmp_path: Path) -> None:
    server = BonsaiServer(cache_dir=tmp_path)

    assert server.model_path == tmp_path / "Bonsai-27B-Q1_0.gguf"
    assert server.mmproj_path == tmp_path / "Bonsai-27B-mmproj-Q8_0.gguf"
    assert server.endpoint_url == "http://127.0.0.1:8080"


def test_ensure_up_reuses_an_available_server_without_starting_process(
    tmp_path: Path,
) -> None:
    server = BonsaiServer(cache_dir=tmp_path)
    server.require_available = Mock()
    server._start_process = Mock(side_effect=AssertionError("server must be reused"))

    result = server.ensure_up()

    assert result is server
    server.require_available.assert_called_once_with()
    server._start_process.assert_not_called()


def test_ensure_up_downloads_missing_files_and_waits_for_readiness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = BonsaiServer(cache_dir=tmp_path)
    server.require_available = Mock(side_effect=BonsaiServerError("offline"))
    process = FakeProcess()
    downloaded: list[tuple[str, Path]] = []

    def fake_download(url: str, destination: Path) -> None:
        downloaded.append((url, destination))
        destination.write_bytes(b"model")

    monkeypatch.setattr(server, "_download_file", fake_download)
    monkeypatch.setattr(server, "_find_executable", lambda: "llama-server")
    monkeypatch.setattr(server, "_start_process", lambda executable: process)
    monkeypatch.setattr(server, "_wait_until_ready", Mock())

    result = server.ensure_up()

    assert result is server
    assert [path for _, path in downloaded] == [
        server.model_path,
        server.mmproj_path,
    ]
    assert all(url.startswith("https://huggingface.co/prism-ml/Bonsai-27B-gguf/")
               for url, _ in downloaded)
    assert server._process is process


def test_ensure_up_does_not_download_present_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = BonsaiServer(cache_dir=tmp_path)
    server.model_path.write_bytes(b"model")
    server.mmproj_path.write_bytes(b"mmproj")
    server.require_available = Mock(side_effect=BonsaiServerError("offline"))
    monkeypatch.setattr(
        server,
        "_download_file",
        Mock(side_effect=AssertionError("artifacts are already cached")),
    )
    monkeypatch.setattr(server, "_find_executable", lambda: "llama-server")
    monkeypatch.setattr(server, "_start_process", lambda executable: FakeProcess())
    monkeypatch.setattr(server, "_wait_until_ready", Mock())

    server.ensure_up()


def test_start_process_uses_jinja_and_native_idle_sleep(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = BonsaiServer(cache_dir=tmp_path)
    popen = Mock(return_value=FakeProcess())
    monkeypatch.setattr("bonsai_server.subprocess.Popen", popen)

    server._start_process("llama-server")

    command = popen.call_args.args[0]
    assert command[:2] == ["llama-server", "--model"]
    assert "--mmproj" in command
    assert "--jinja" in command
    assert "--sleep-idle-seconds" in command
    assert "600" in command


def test_require_available_raises_actionable_error_when_endpoint_is_unreachable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = BonsaiServer(cache_dir=tmp_path)
    monkeypatch.setattr(
        "bonsai_server.urlopen",
        Mock(side_effect=URLError("connection refused")),
    )

    with pytest.raises(BonsaiServerError, match="--up"):
        server.require_available()


def test_wait_until_ready_returns_after_models_endpoint_responds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = BonsaiServer(cache_dir=tmp_path, ready_retries=1)
    monkeypatch.setattr(server, "_endpoint_responds", lambda: True)

    server._wait_until_ready()


def test_stop_terminates_only_a_process_started_by_this_instance(
    tmp_path: Path,
) -> None:
    server = BonsaiServer(cache_dir=tmp_path)
    process = FakeProcess()
    server._process = process
    server._owns_process = True

    server.stop()

    assert process.terminate_calls == 1
    assert process.wait_calls == 1
    assert server._process is None


def test_stop_does_not_terminate_a_reused_server(tmp_path: Path) -> None:
    server = BonsaiServer(cache_dir=tmp_path)
    server._process = None
    server._owns_process = False

    server.stop()


class FakeCliServer:
    """Server double for CLI action tests."""

    def __init__(self) -> None:
        self.up_calls = 0
        self.down_calls = 0
        self.status_calls = 0

    def ensure_up(self) -> None:
        self.up_calls += 1

    def stop(self, *, force: bool = False) -> None:
        assert force
        self.down_calls += 1

    def status(self) -> bool:
        self.status_calls += 1
        return True

    def _models_url(self) -> str:
        return "http://127.0.0.1:8080/v1/models"


@pytest.mark.parametrize(
    ("arguments", "attribute"),
    [
        (["--up"], "up_calls"),
        (["--down"], "down_calls"),
        (["--status"], "status_calls"),
    ],
)
def test_cli_actions_are_available(
    monkeypatch: pytest.MonkeyPatch,
    arguments: list[str],
    attribute: str,
) -> None:
    fake = FakeCliServer()
    monkeypatch.setattr(bonsai_server, "BonsaiServer", lambda: fake)

    assert bonsai_server.main(arguments) == 0
    assert getattr(fake, attribute) == 1
