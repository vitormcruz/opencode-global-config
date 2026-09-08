"""Unit tests for the fixed local Qwen model server utility."""

from __future__ import annotations

import io
import json
import shutil
import tarfile
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock
from urllib.error import URLError

import pytest

import local_model_server
from local_model_server import (
    MODEL_SPEC,
    LocalModelServer,
    LocalModelServerError,
)


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
    server = LocalModelServer(cache_dir=tmp_path)

    assert server.model_path == tmp_path / "Qwen3-0.6B-Q8_0.gguf"
    assert not hasattr(server, "mmproj_path")
    assert server.endpoint_url == "http://127.0.0.1:8080"


def test_qwen_model_contract_is_fixed_to_the_approved_gguf() -> None:
    spec = MODEL_SPEC

    assert spec.repository == "Qwen/Qwen3-0.6B-GGUF"
    assert spec.file_name == "Qwen3-0.6B-Q8_0.gguf"
    assert spec.provider == "qwen-local"
    assert spec.model_id == "qwen3-0.6b"
    assert spec.sha256 == (
        "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
    )


def test_qwen_artifact_checksum_is_enforced(tmp_path: Path) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    server.model_path.write_bytes(b"not-the-qwen-artifact")

    with pytest.raises(LocalModelServerError, match="Checksum SHA-256"):
        server._ensure_model_files()


def test_server_cli_rejects_model_selection() -> None:
    with pytest.raises(SystemExit):
        local_model_server.main(["--up", "--model", "qwen3-0.6b"])


@pytest.mark.parametrize("exposed_model", ["Qwen3-0.6B-Q8_0.gguf", "other.gguf"])
def test_endpoint_identity_is_checked_before_reusing_server(
    monkeypatch: pytest.MonkeyPatch,
    exposed_model: str,
) -> None:
    server = LocalModelServer()
    response = MagicMock()
    response.read.return_value = json.dumps(
        {"data": [{"id": exposed_model}]}
    ).encode("utf-8")
    response.__enter__.return_value = response
    monkeypatch.setattr(local_model_server, "urlopen", lambda *args, **kwargs: response)

    assert server._endpoint_matches_model() is (exposed_model == server.model_spec.file_name)


@pytest.mark.parametrize(
    ("cuda_version", "expected_asset"),
    [
        ((12, 8), "cuda-12.8-x64"),
        ((13, 0), "cuda-12.8-x64"),
        ((12, 7), "cuda-12.4-x64"),
    ],
)
def test_select_llama_asset_maps_cuda_to_fixed_release(
    monkeypatch: pytest.MonkeyPatch,
    cuda_version: tuple[int, int],
    expected_asset: str,
) -> None:
    monkeypatch.setattr(local_model_server.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(
        LocalModelServer,
        "_cuda_version",
        classmethod(lambda cls: cuda_version),
    )
    monkeypatch.setattr(local_model_server.ctypes, "CDLL", lambda library: object())

    asset = LocalModelServer._select_llama_asset()

    assert expected_asset in asset
    assert asset.startswith("llama-prism-b9596-9fcaed7-bin-linux-")


def test_select_llama_asset_probes_both_cuda_runtime_libraries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    loaded: list[str] = []

    def fake_cdll(library: str) -> object:
        loaded.append(library)
        return object()

    monkeypatch.setattr(local_model_server.ctypes, "CDLL", fake_cdll)

    assert LocalModelServer._cuda_runtime_available()
    assert loaded == ["libcudart.so.12", "libcublas.so.12"]


def test_missing_cuda_runtime_rebaixa_to_vulkan_with_one_notice(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(local_model_server.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(
        LocalModelServer,
        "_cuda_version",
        classmethod(lambda cls: (12, 8)),
    )
    monkeypatch.setattr(
        local_model_server.ctypes,
        "CDLL",
        Mock(side_effect=OSError("runtime CUDA ausente")),
    )
    monkeypatch.setattr(
        local_model_server.shutil,
        "which",
        lambda command: "/usr/bin/vulkaninfo" if command == "vulkaninfo" else None,
    )

    asset = LocalModelServer._select_llama_asset()

    assert "ubuntu-vulkan-x64" in asset
    output = capsys.readouterr().out.strip().splitlines()
    assert len(output) == 1
    assert "Usando backend Vulkan" in output[0]


def test_missing_cuda_runtime_rebaixa_to_cpu_without_vulkan(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(local_model_server.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(
        LocalModelServer,
        "_cuda_version",
        classmethod(lambda cls: (12, 8)),
    )
    monkeypatch.setattr(
        local_model_server.ctypes,
        "CDLL",
        Mock(side_effect=OSError("runtime CUDA ausente")),
    )
    monkeypatch.setattr(local_model_server.shutil, "which", lambda command: None)

    asset = LocalModelServer._select_llama_asset()

    assert asset.endswith("bin-ubuntu-x64.tar.gz")
    output = capsys.readouterr().out.strip().splitlines()
    assert len(output) == 1
    assert "Usando backend CPU" in output[0]


@pytest.mark.parametrize(
    ("available_command", "expected_fragment"),
    [
        ("rocminfo", "ubuntu-rocm-7.2-x64"),
        ("vulkaninfo", "ubuntu-vulkan-x64"),
        (None, "ubuntu-x64"),
    ],
)
def test_select_llama_asset_detects_non_cuda_backends(
    monkeypatch: pytest.MonkeyPatch,
    available_command: str | None,
    expected_fragment: str,
) -> None:
    monkeypatch.setattr(local_model_server.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(
        LocalModelServer,
        "_cuda_version",
        classmethod(lambda cls: None),
    )
    monkeypatch.setattr(
        local_model_server.shutil,
        "which",
        lambda command: "/usr/bin/tool" if command == available_command else None,
    )

    assert expected_fragment in LocalModelServer._select_llama_asset()


def test_find_executable_downloads_and_extracts_cached_release(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_archive = tmp_path / "source.tar.gz"
    with tarfile.open(source_archive, mode="w:gz") as archive:
        info = tarfile.TarInfo("bundle/llama-server")
        info.mode = 0o755
        payload = b"fake llama server"
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))

    server = LocalModelServer(
        cache_dir=tmp_path / "models",
        llama_cache_dir=tmp_path / "llama",
    )
    monkeypatch.setattr(
        server,
        "_select_llama_asset",
        lambda: "llama-prism-b9596-9fcaed7-bin-ubuntu-x64.tar.gz",
    )

    def fake_download(url: str, destination: Path) -> None:
        shutil.copyfile(source_archive, destination)

    monkeypatch.setattr(server, "_download_file", fake_download)
    monkeypatch.setattr(server, "_validate_artifact", Mock())

    executable = Path(server._find_executable())

    assert executable == tmp_path / "llama" / "bundle" / "llama-server"
    assert executable.read_bytes() == b"fake llama server"
    assert executable.stat().st_mode & 0o100
    assert (
        (tmp_path / "llama" / local_model_server.LLAMA_RELEASE_MARKER).read_text(
            encoding="ascii"
        )
        == f"{local_model_server.LLAMA_RELEASE_TAG}\n"
    )


def test_find_executable_reuses_cached_binary_without_download(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executable = tmp_path / "llama" / "llama-server"
    executable.parent.mkdir()
    executable.write_bytes(b"cached")
    server = LocalModelServer(
        cache_dir=tmp_path / "models",
        llama_cache_dir=tmp_path / "llama",
    )
    monkeypatch.setattr(
        server,
        "_select_llama_asset",
        lambda: "llama-prism-b9596-9fcaed7-bin-ubuntu-x64.tar.gz",
    )
    monkeypatch.setattr(
        server,
        "_download_llama_binary",
        Mock(side_effect=AssertionError("binário já está no cache")),
    )

    assert server._find_executable() == str(executable)


def test_find_executable_replaces_cache_when_backend_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_dir = tmp_path / "llama"
    executable = cache_dir / "llama-server"
    cache_dir.mkdir()
    executable.write_bytes(b"old-cuda")
    (cache_dir / local_model_server.LLAMA_RELEASE_MARKER).write_text(
        local_model_server.LLAMA_RELEASE_TAG,
        encoding="ascii",
    )
    (cache_dir / local_model_server.LLAMA_BACKEND_MARKER).write_text(
        "cuda",
        encoding="ascii",
    )
    server = LocalModelServer(
        cache_dir=tmp_path / "models",
        llama_cache_dir=cache_dir,
    )
    monkeypatch.setattr(
        server,
        "_select_llama_asset",
        lambda: "llama-prism-b9596-9fcaed7-bin-ubuntu-x64.tar.gz",
    )
    download = Mock(return_value="new-llama-server")
    monkeypatch.setattr(server, "_download_llama_binary", download)

    assert server._find_executable() == "new-llama-server"
    download.assert_called_once_with(
        "llama-prism-b9596-9fcaed7-bin-ubuntu-x64.tar.gz"
    )


def test_find_executable_rejects_unsafe_binary_archive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_archive = tmp_path / "source-unsafe.tar.gz"
    with tarfile.open(source_archive, mode="w:gz") as archive:
        info = tarfile.TarInfo("../outside")
        info.size = 1
        archive.addfile(info, io.BytesIO(b"x"))

    server = LocalModelServer(
        cache_dir=tmp_path / "models",
        llama_cache_dir=tmp_path / "llama",
    )
    monkeypatch.setattr(server, "_select_llama_asset", lambda: "unsafe.tar.gz")
    monkeypatch.setattr(
        server,
        "_download_file",
        lambda url, destination: shutil.copyfile(source_archive, destination),
    )

    with pytest.raises(LocalModelServerError, match="Arquivo inseguro"):
        server._find_executable()


def test_ensure_up_reuses_an_available_server_without_starting_process(
    tmp_path: Path,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    server.require_available = Mock()
    server._endpoint_matches_model = Mock(return_value=True)
    server._start_process = Mock(side_effect=AssertionError("server must be reused"))

    result = server.ensure_up()

    assert result is server
    server.require_available.assert_called_once_with()
    server._start_process.assert_not_called()


def test_ensure_up_reuses_server_after_slow_health_response(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    response = MagicMock(status=200)
    response.__enter__.return_value = response
    start_process = Mock(side_effect=AssertionError("server must be reused"))

    def slow_urlopen(url: str, *, timeout: float) -> Mock:
        time.sleep(0.01)
        assert timeout == local_model_server.LOCAL_REQUEST_TIMEOUT_SECONDS
        return response

    monkeypatch.setattr(local_model_server, "urlopen", slow_urlopen)
    server._start_process = start_process
    server._endpoint_matches_model = Mock(return_value=True)

    result = server.ensure_up()

    assert result is server
    start_process.assert_not_called()


def test_ensure_up_reconciles_an_owned_server_with_a_different_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    process = FakeProcess()
    server.require_available = Mock()
    server._endpoint_matches_model = Mock(return_value=False)
    server._read_pid = Mock(return_value=process.pid)
    server._pid_file_process_is_owned = Mock(return_value=True)
    server._pid_is_alive = Mock(return_value=False)
    server._endpoint_responds = Mock(return_value=False)
    server._find_executable = Mock(return_value="llama-server")
    server._ensure_model_files = Mock()
    server._start_process = Mock(return_value=process)
    server._wait_until_ready = Mock()
    kill = Mock()
    monkeypatch.setattr(local_model_server.os, "kill", kill)

    server.ensure_up()

    kill.assert_called_once_with(process.pid, local_model_server.signal.SIGTERM)
    server._start_process.assert_called_once_with("llama-server")


def test_ensure_up_does_not_kill_or_start_over_an_unowned_server(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    server.require_available = Mock()
    server._endpoint_matches_model = Mock(return_value=False)
    server._read_pid = Mock(return_value=12345)
    server._pid_file_process_is_owned = Mock(return_value=False)
    server._start_process = Mock(
        side_effect=AssertionError("não deve iniciar sobre porta ocupada")
    )
    kill = Mock()
    monkeypatch.setattr(local_model_server.os, "kill", kill)

    with pytest.raises(LocalModelServerError, match="não pertence"):
        server.ensure_up()

    server._pid_file_process_is_owned.assert_called_once_with(12345)
    kill.assert_not_called()


def test_pid_file_ownership_requires_a_known_llama_server_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    server._pid_is_alive = Mock(return_value=True)
    command = (
        f"/opt/llama-server\0--model\0{server.model_path}\0"
        f"--host\0{server.bind_host}\0--port\0{server.port}\0"
    ).encode("utf-8")
    monkeypatch.setattr(Path, "read_bytes", Mock(return_value=command))

    assert server._pid_file_process_is_owned(12345)

    foreign_command = b"/usr/bin/python\0--model\0" + str(server.model_path).encode()
    monkeypatch.setattr(Path, "read_bytes", Mock(return_value=foreign_command))
    assert not server._pid_file_process_is_owned(12345)


def test_ensure_up_downloads_missing_files_and_waits_for_readiness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    server.require_available = Mock(side_effect=LocalModelServerError("offline"))
    process = FakeProcess()
    downloaded: list[tuple[str, Path]] = []

    def fake_download(url: str, destination: Path) -> None:
        downloaded.append((url, destination))
        destination.write_bytes(b"model")

    monkeypatch.setattr(server, "_download_file", fake_download)
    monkeypatch.setattr(server, "_validate_artifact", Mock())
    monkeypatch.setattr(server, "_find_executable", lambda: "llama-server")
    monkeypatch.setattr(server, "_start_process", lambda executable: process)
    monkeypatch.setattr(server, "_wait_until_ready", Mock())

    result = server.ensure_up()

    assert result is server
    assert [path for _, path in downloaded] == [server.model_path]
    assert all(url.startswith("https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/")
               for url, _ in downloaded)
    assert server._process is process


def test_ensure_up_checks_llama_server_before_downloading(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    server.require_available = Mock(side_effect=LocalModelServerError("offline"))
    monkeypatch.setattr(
        server,
        "_find_executable",
        Mock(side_effect=LocalModelServerError("llama-server ausente")),
    )
    monkeypatch.setattr(
        server,
        "_ensure_model_files",
        Mock(side_effect=AssertionError("não deve baixar sem executável")),
    )

    with pytest.raises(LocalModelServerError, match="llama-server ausente"):
        server.ensure_up()


def test_ensure_up_does_not_download_present_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    server.model_path.write_bytes(b"model")
    server.require_available = Mock(side_effect=LocalModelServerError("offline"))
    monkeypatch.setattr(
        server,
        "_download_file",
        Mock(side_effect=AssertionError("artifacts are already cached")),
    )
    monkeypatch.setattr(server, "_validate_artifact", Mock())
    monkeypatch.setattr(server, "_find_executable", lambda: "llama-server")
    monkeypatch.setattr(server, "_start_process", lambda executable: FakeProcess())
    monkeypatch.setattr(server, "_wait_until_ready", Mock())

    server.ensure_up()


def test_start_process_uses_jinja_and_native_idle_sleep(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    popen = Mock(return_value=FakeProcess())
    monkeypatch.setattr("local_model_server.subprocess.Popen", popen)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    monkeypatch.setattr(server, "_ensure_libgomp_runtime", lambda: runtime)
    loader = tmp_path / "ld-linux-x86-64.so.2"
    loader.write_bytes(b"loader")
    monkeypatch.setattr(server, "_dynamic_loader", lambda: loader)

    server._start_process("llama-server")

    command = popen.call_args.args[0]
    assert command[:2] == [str(loader), "--library-path"]
    assert str(runtime) in command[2].split(":")
    assert command[3:5] == ["llama-server", "--model"]
    assert "--mmproj" not in command
    temp_index = command.index("--temp")
    assert command[temp_index + 1] == "0"
    seed_index = command.index("--seed")
    assert command[seed_index + 1] == str(local_model_server.DETERMINISTIC_SEED)
    context_index = command.index("--ctx-size")
    assert command[context_index + 1] == str(local_model_server.CONTEXT_SIZE)
    assert "--jinja" in command
    assert "--sleep-idle-seconds" in command
    assert "600" in command
    assert popen.call_args.kwargs["start_new_session"] is True


def test_start_process_fails_before_prism_when_libgomp_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    popen = Mock()
    monkeypatch.setattr("local_model_server.subprocess.Popen", popen)
    monkeypatch.setattr(
        "local_model_server.runtime_validation_error",
        lambda: "arquivo ausente",
    )

    with pytest.raises(LocalModelServerError, match="libgomp.so.1") as failure:
        server._start_process("llama-server")

    assert "opencode-bootstrap --yes" in str(failure.value)
    popen.assert_not_called()


def test_launch_command_uses_elf_library_path_without_ld_library_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    loader = tmp_path / "ld-linux-x86-64.so.2"
    loader.write_bytes(b"loader")
    monkeypatch.setattr(server, "_ensure_libgomp_runtime", lambda: runtime)
    monkeypatch.setattr(server, "_dynamic_loader", lambda: loader)

    command = server._launch_command("llama-server")

    assert "--library-path" in command
    assert "LD_LIBRARY_PATH" not in command


def test_require_available_raises_actionable_error_when_endpoint_is_unreachable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    monkeypatch.setattr(
        "local_model_server.urlopen",
        Mock(side_effect=URLError("connection refused")),
    )

    with pytest.raises(LocalModelServerError, match="--up"):
        server.require_available()


def test_wait_until_ready_returns_after_models_endpoint_responds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path, ready_retries=1)
    monkeypatch.setattr(server, "_endpoint_responds", lambda: True)

    server._wait_until_ready()


# --- Health-check antes do lote opencode (item 5.6) ---


def test_ensure_healthy_returns_without_restart_when_health_responds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    restart = Mock(side_effect=AssertionError("servidor saudável não reinicia"))
    monkeypatch.setattr(server, "_health_responds", Mock(return_value=True))
    monkeypatch.setattr(server, "stop", restart)
    monkeypatch.setattr(server, "ensure_up", restart)

    result = server.ensure_healthy()

    assert result is server


def test_ensure_healthy_restarts_once_and_recovers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    health_results = iter([False, True])
    monkeypatch.setattr(
        server, "_health_responds", lambda: next(health_results)
    )
    stop = Mock()
    ensure_up = Mock()
    monkeypatch.setattr(server, "stop", stop)
    monkeypatch.setattr(server, "ensure_up", ensure_up)

    result = server.ensure_healthy()

    assert result is server
    stop.assert_called_once_with(force=True)
    ensure_up.assert_called_once_with()


def test_ensure_healthy_fails_fast_with_actionable_error_when_still_sick(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    monkeypatch.setattr(server, "_health_responds", Mock(return_value=False))
    monkeypatch.setattr(server, "stop", Mock())
    monkeypatch.setattr(server, "ensure_up", Mock())

    with pytest.raises(LocalModelServerError, match="--up") as failure:
        server.ensure_healthy()

    assert "local_model_server.py --up" in str(failure.value)


def test_health_check_uses_short_justified_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Health local responde em milissegundos; o teto curto detecta
    servidor doente sem esperar o timeout de inferência."""

    server = LocalModelServer(cache_dir=tmp_path)
    observed: dict[str, object] = {}

    def fake_urlopen(url: str, *, timeout: float) -> MagicMock:
        observed["url"] = url
        observed["timeout"] = timeout
        response = MagicMock(status=200)
        response.__enter__.return_value = response
        return response

    monkeypatch.setattr(local_model_server, "urlopen", fake_urlopen)

    assert server._health_responds()
    assert observed["url"] == f"{server.endpoint_url}/health"
    assert observed["timeout"] == local_model_server.HEALTH_TIMEOUT_SECONDS
    assert observed["timeout"] < local_model_server.LOCAL_REQUEST_TIMEOUT_SECONDS


def test_qwen_fixture_health_checks_before_yield(repo_root: Path) -> None:
    """A fixture session-scoped valida a saúde ANTES de servir o lote."""

    conftest = (repo_root / "tests" / "integration" / "conftest.py").read_text(
        encoding="utf-8"
    )

    assert "ensure_healthy()" in conftest
    assert conftest.index("ensure_healthy()") < conftest.index("yield server")


def test_stop_terminates_only_a_process_started_by_this_instance(
    tmp_path: Path,
) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
    process = FakeProcess()
    server._process = process
    server._owns_process = True

    server.stop()

    assert process.terminate_calls == 1
    assert process.wait_calls == 1
    assert server._process is None


def test_stop_does_not_terminate_a_reused_server(tmp_path: Path) -> None:
    server = LocalModelServer(cache_dir=tmp_path)
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
    monkeypatch.setattr(local_model_server, "LocalModelServer", lambda **_: fake)

    assert local_model_server.main(arguments) == 0
    assert getattr(fake, attribute) == 1
