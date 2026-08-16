"""Unit tests for the local Bonsai model server utility."""

from __future__ import annotations

import io
import shutil
import tarfile
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
    assert not hasattr(server, "mmproj_path")
    assert server.endpoint_url == "http://127.0.0.1:8080"


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
    monkeypatch.setattr(bonsai_server.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(
        BonsaiServer,
        "_cuda_version",
        classmethod(lambda cls: cuda_version),
    )
    monkeypatch.setattr(bonsai_server.ctypes, "CDLL", lambda library: object())

    asset = BonsaiServer._select_llama_asset()

    assert expected_asset in asset
    assert asset.startswith("llama-prism-b9596-9fcaed7-bin-linux-")


def test_select_llama_asset_probes_both_cuda_runtime_libraries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    loaded: list[str] = []

    def fake_cdll(library: str) -> object:
        loaded.append(library)
        return object()

    monkeypatch.setattr(bonsai_server.ctypes, "CDLL", fake_cdll)

    assert BonsaiServer._cuda_runtime_available()
    assert loaded == ["libcudart.so.12", "libcublas.so.12"]


def test_missing_cuda_runtime_rebaixa_to_vulkan_with_one_notice(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(bonsai_server.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(
        BonsaiServer,
        "_cuda_version",
        classmethod(lambda cls: (12, 8)),
    )
    monkeypatch.setattr(
        bonsai_server.ctypes,
        "CDLL",
        Mock(side_effect=OSError("runtime CUDA ausente")),
    )
    monkeypatch.setattr(
        bonsai_server.shutil,
        "which",
        lambda command: "/usr/bin/vulkaninfo" if command == "vulkaninfo" else None,
    )

    asset = BonsaiServer._select_llama_asset()

    assert "ubuntu-vulkan-x64" in asset
    output = capsys.readouterr().out.strip().splitlines()
    assert len(output) == 1
    assert "sudo apt install" in output[0]


def test_missing_cuda_runtime_rebaixa_to_cpu_without_vulkan(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(bonsai_server.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(
        BonsaiServer,
        "_cuda_version",
        classmethod(lambda cls: (12, 8)),
    )
    monkeypatch.setattr(
        bonsai_server.ctypes,
        "CDLL",
        Mock(side_effect=OSError("runtime CUDA ausente")),
    )
    monkeypatch.setattr(bonsai_server.shutil, "which", lambda command: None)

    asset = BonsaiServer._select_llama_asset()

    assert asset.endswith("bin-ubuntu-x64.tar.gz")
    output = capsys.readouterr().out.strip().splitlines()
    assert len(output) == 1
    assert "CUDA ignorado" in output[0]


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
    monkeypatch.setattr(bonsai_server.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(
        BonsaiServer,
        "_cuda_version",
        classmethod(lambda cls: None),
    )
    monkeypatch.setattr(
        bonsai_server.shutil,
        "which",
        lambda command: "/usr/bin/tool" if command == available_command else None,
    )

    assert expected_fragment in BonsaiServer._select_llama_asset()


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

    server = BonsaiServer(
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

    executable = Path(server._find_executable())

    assert executable == tmp_path / "llama" / "bundle" / "llama-server"
    assert executable.read_bytes() == b"fake llama server"
    assert executable.stat().st_mode & 0o100
    assert (
        (tmp_path / "llama" / bonsai_server.LLAMA_RELEASE_MARKER).read_text(
            encoding="ascii"
        )
        == f"{bonsai_server.LLAMA_RELEASE_TAG}\n"
    )


def test_find_executable_reuses_cached_binary_without_download(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executable = tmp_path / "llama" / "llama-server"
    executable.parent.mkdir()
    executable.write_bytes(b"cached")
    server = BonsaiServer(
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
    (cache_dir / bonsai_server.LLAMA_RELEASE_MARKER).write_text(
        bonsai_server.LLAMA_RELEASE_TAG,
        encoding="ascii",
    )
    (cache_dir / bonsai_server.LLAMA_BACKEND_MARKER).write_text(
        "cuda",
        encoding="ascii",
    )
    server = BonsaiServer(
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

    server = BonsaiServer(
        cache_dir=tmp_path / "models",
        llama_cache_dir=tmp_path / "llama",
    )
    monkeypatch.setattr(server, "_select_llama_asset", lambda: "unsafe.tar.gz")
    monkeypatch.setattr(
        server,
        "_download_file",
        lambda url, destination: shutil.copyfile(source_archive, destination),
    )

    with pytest.raises(BonsaiServerError, match="Arquivo inseguro"):
        server._find_executable()


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
    assert [path for _, path in downloaded] == [server.model_path]
    assert all(url.startswith("https://huggingface.co/prism-ml/Bonsai-27B-gguf/")
               for url, _ in downloaded)
    assert server._process is process


def test_ensure_up_checks_llama_server_before_downloading(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = BonsaiServer(cache_dir=tmp_path)
    server.require_available = Mock(side_effect=BonsaiServerError("offline"))
    monkeypatch.setattr(
        server,
        "_find_executable",
        Mock(side_effect=BonsaiServerError("llama-server ausente")),
    )
    monkeypatch.setattr(
        server,
        "_ensure_model_files",
        Mock(side_effect=AssertionError("não deve baixar sem executável")),
    )

    with pytest.raises(BonsaiServerError, match="llama-server ausente"):
        server.ensure_up()


def test_ensure_up_does_not_download_present_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = BonsaiServer(cache_dir=tmp_path)
    server.model_path.write_bytes(b"model")
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
    assert "--mmproj" not in command
    temp_index = command.index("--temp")
    assert command[temp_index + 1] == "0"
    seed_index = command.index("--seed")
    assert command[seed_index + 1] == str(bonsai_server.DETERMINISTIC_SEED)
    context_index = command.index("--ctx-size")
    assert command[context_index + 1] == str(bonsai_server.CONTEXT_SIZE)
    assert "--jinja" in command
    assert "--sleep-idle-seconds" in command
    assert "600" in command
    assert popen.call_args.kwargs["start_new_session"] is True


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
