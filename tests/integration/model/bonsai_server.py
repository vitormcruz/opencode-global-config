"""Provision and manage the local Bonsai model server.

The utility intentionally uses only Python's standard library.  The model is
downloaded once to the user's cache and the llama-server process can be reused
by successive pytest executions.
"""

from __future__ import annotations

import argparse
import ctypes
import os
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


MODEL_REPOSITORY = "prism-ml/Bonsai-27B-gguf"
MODEL_FILE = "Bonsai-27B-Q1_0.gguf"
MODEL_BASE_URL = f"https://huggingface.co/{MODEL_REPOSITORY}/resolve/main"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "opencode-config" / "models"
LLAMA_RELEASE_TAG = "prism-b9596-9fcaed7"
LLAMA_RELEASE_BASE_URL = (
    "https://github.com/PrismML-Eng/llama.cpp/releases/download/"
    f"{LLAMA_RELEASE_TAG}"
)
DEFAULT_LLAMA_CACHE_DIR = Path.home() / ".cache" / "opencode-config" / "llama"
LLAMA_RELEASE_MARKER = ".llama_release"
LLAMA_BACKEND_MARKER = ".llama_backend"
CUDA_RUNTIME_INSTALL_COMMAND = (
    "sudo apt install cuda-cudart-12-8 libcublas-12-8"
)
DEFAULT_HOST = "127.0.0.1"
DEFAULT_BIND_HOST = "0.0.0.0"
DEFAULT_PORT = 8080
IDLE_SECONDS = 600
DETERMINISTIC_SEED = 42
PID_FILE_NAME = "llama-server.pid"
DOWNLOAD_TIMEOUT_SECONDS = 600


class BonsaiServerError(RuntimeError):
    """Raised when the local Bonsai server cannot be provisioned or reached."""


def _log(message: str) -> None:
    print(f"[bonsai-server] {message}")


@dataclass
class BonsaiServer:
    """Manage a persistent llama-server process for the Bonsai 27B model."""

    cache_dir: Path = field(
        default_factory=lambda: Path.home() / ".cache" / "opencode-config" / "models"
    )
    llama_cache_dir: Path = field(
        default_factory=lambda: Path.home() / ".cache" / "opencode-config" / "llama"
    )
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    bind_host: str = DEFAULT_BIND_HOST
    executable: str | None = None
    ready_retries: int = 90
    ready_interval: float = 2.0
    request_timeout: float = 5.0
    _process: subprocess.Popen[bytes] | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _owns_process: bool = field(default=False, init=False, repr=False)

    @property
    def model_path(self) -> Path:
        """Return the fixed path of the Bonsai model weights."""

        return self.cache_dir / MODEL_FILE

    @property
    def pid_path(self) -> Path:
        """Return the state file used by the ``--down`` command."""

        return self.cache_dir / PID_FILE_NAME

    @property
    def endpoint_url(self) -> str:
        """Return the local base URL used for health checks."""

        return f"http://{self.host}:{self.port}"

    def _models_url(self) -> str:
        return f"{self.endpoint_url}/v1/models"

    def _find_executable(self) -> str:
        if self.executable is not None:
            return self.executable
        return self._ensure_llama_binary()

    def _download_file(self, url: str, destination: Path) -> None:
        """Download one model artifact atomically."""

        temporary_path = destination.with_name(f".{destination.name}.part")
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with urlopen(url, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
                with temporary_path.open("wb") as output:
                    self._copy_response(response, output)
            if temporary_path.stat().st_size == 0:
                raise BonsaiServerError(f"Download vazio recebido de {url}")
            os.replace(temporary_path, destination)
        except BonsaiServerError:
            self._remove_if_exists(temporary_path)
            raise
        except (HTTPError, OSError, TimeoutError, URLError) as error:
            self._remove_if_exists(temporary_path)
            raise BonsaiServerError(
                f"Falha ao baixar o artefato do Bonsai: {url}\n"
                "Verifique a conectividade e tente novamente."
            ) from error

    @staticmethod
    def _command_output(command: list[str]) -> str:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return ""
        return f"{result.stdout}\n{result.stderr}"

    @classmethod
    def _cuda_version(cls) -> tuple[int, int] | None:
        for command in ("nvcc", "nvidia-smi"):
            executable = shutil.which(command)
            if executable is None:
                continue
            arguments = ["--version"] if command == "nvcc" else []
            output = cls._command_output([executable, *arguments])
            match = re.search(r"(?:release|CUDA Version:)\s*(\d+)\.(\d+)", output)
            if match is None:
                return (12, 4)
            return int(match.group(1)), int(match.group(2))
        return None

    @staticmethod
    def _cuda_runtime_available() -> bool:
        for library in ("libcudart.so.12", "libcublas.so.12"):
            try:
                ctypes.CDLL(library)
            except OSError:
                return False
        return True

    @classmethod
    def _select_llama_asset(cls) -> str:
        architecture = platform.machine().lower()
        if architecture not in {"x86_64", "amd64"}:
            raise BonsaiServerError(
                f"Arquitetura Linux não suportada para o llama-server: {architecture}."
            )

        cuda_version = cls._cuda_version()
        if cuda_version is not None:
            if not cls._cuda_runtime_available():
                _log(
                    "CUDA ignorado: runtime ausente "
                    "(libcudart.so.12/libcublas.so.12). Para habilitar GPU: "
                    f"{CUDA_RUNTIME_INSTALL_COMMAND}"
                )
                if shutil.which("vulkaninfo") is not None:
                    return f"llama-{LLAMA_RELEASE_TAG}-bin-ubuntu-vulkan-x64.tar.gz"
                return f"llama-{LLAMA_RELEASE_TAG}-bin-ubuntu-x64.tar.gz"
            major, minor = cuda_version
            cuda_tag = "12.8" if major > 12 or (major == 12 and minor >= 8) else "12.4"
            return f"llama-{LLAMA_RELEASE_TAG}-bin-linux-cuda-{cuda_tag}-x64.tar.gz"

        if any(shutil.which(command) for command in ("rocminfo", "rocm-smi", "hipcc")):
            return (
                f"llama-{LLAMA_RELEASE_TAG}-bin-ubuntu-rocm-7.2-x64.tar.gz"
            )

        if shutil.which("vulkaninfo") is not None:
            return f"llama-{LLAMA_RELEASE_TAG}-bin-ubuntu-vulkan-x64.tar.gz"

        return f"llama-{LLAMA_RELEASE_TAG}-bin-ubuntu-x64.tar.gz"

    @staticmethod
    def _find_binary(root: Path) -> Path | None:
        direct_path = root / "llama-server"
        if direct_path.is_file():
            return direct_path
        for path in root.rglob("llama-server"):
            if path.is_file():
                return path
        return None

    def _cached_llama_binary(self) -> Path | None:
        if not self.llama_cache_dir.is_dir():
            return None
        return self._find_binary(self.llama_cache_dir)

    def _cached_release(self) -> str | None:
        try:
            return (
                self.llama_cache_dir / LLAMA_RELEASE_MARKER
            ).read_text(encoding="ascii").strip()
        except (FileNotFoundError, OSError):
            return None

    def _cached_backend(self) -> str | None:
        try:
            return (
                self.llama_cache_dir / LLAMA_BACKEND_MARKER
            ).read_text(encoding="ascii").strip()
        except (FileNotFoundError, OSError):
            return None

    def _inferred_cached_backend(self) -> str:
        backend_markers = (
            ("cuda", "libggml-cuda.so"),
            ("rocm", "libggml-rocm.so"),
            ("vulkan", "libggml-vulkan.so"),
        )
        for backend, marker in backend_markers:
            if any(self.llama_cache_dir.rglob(marker + "*")):
                return backend
        return "cpu"

    @staticmethod
    def _asset_backend(asset: str) -> str:
        if "-cuda-" in asset:
            return "cuda"
        if "-rocm-" in asset:
            return "rocm"
        if "-vulkan-" in asset:
            return "vulkan"
        return "cpu"

    @staticmethod
    def _safe_extract(archive: tarfile.TarFile, destination: Path) -> None:
        root = destination.resolve()
        members = archive.getmembers()
        link_members: list[tarfile.TarInfo] = []
        for member in members:
            target = (destination / member.name).resolve()
            if target != root and root not in target.parents:
                raise BonsaiServerError(
                    f"Arquivo inseguro no pacote do llama-server: {member.name}"
                )
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise BonsaiServerError(
                        "Não foi possível extrair o arquivo do llama-server: "
                        f"{member.name}"
                    )
                with source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
                target.chmod(member.mode & 0o777)
                continue
            if member.issym() or member.islnk():
                link_members.append(member)
                continue
            raise BonsaiServerError(
                f"Tipo de arquivo não suportado no pacote do llama-server: "
                f"{member.name}"
            )

        for member in link_members:
            target = (destination / member.name).resolve()
            if target.exists() or target.is_symlink():
                raise BonsaiServerError(
                    f"Arquivo duplicado no pacote do llama-server: {member.name}"
                )
            target.parent.mkdir(parents=True, exist_ok=True)
            link_target = Path(member.linkname)
            if member.issym():
                if link_target.is_absolute():
                    raise BonsaiServerError(
                        f"Link absoluto no pacote do llama-server: {member.name}"
                    )
                resolved_link = (target.parent / link_target).resolve()
                if resolved_link != root and root not in resolved_link.parents:
                    raise BonsaiServerError(
                        f"Link inseguro no pacote do llama-server: {member.name}"
                    )
                target.symlink_to(member.linkname)
                continue
            resolved_link = (destination / link_target).resolve()
            if resolved_link != root and root not in resolved_link.parents:
                raise BonsaiServerError(
                    f"Hard link inseguro no pacote do llama-server: {member.name}"
                )
            if not resolved_link.is_file() or resolved_link.is_symlink():
                raise BonsaiServerError(
                    f"Destino ausente para hard link do llama-server: {member.name}"
                )
            target.hardlink_to(resolved_link)

    def _download_llama_binary(self, asset: str | None = None) -> str:
        asset = asset or self._select_llama_asset()
        backend = self._asset_backend(asset)
        archive_path = self.llama_cache_dir.parent / asset
        extraction_dir = self.llama_cache_dir.parent / (
            f".{self.llama_cache_dir.name}.extract-{os.getpid()}"
        )
        url = f"{LLAMA_RELEASE_BASE_URL}/{asset}"
        self._remove_if_exists(archive_path)
        if extraction_dir.exists():
            shutil.rmtree(extraction_dir)

        try:
            _log(f"Baixando o binário {asset}...")
            self._download_file(url, archive_path)
            extraction_dir.mkdir(parents=True, exist_ok=True)
            with tarfile.open(archive_path, mode="r:gz") as archive:
                self._safe_extract(archive, extraction_dir)
            binary = self._find_binary(extraction_dir)
            if binary is None:
                raise BonsaiServerError(
                    "O pacote do llama-server não contém um executável "
                    "`llama-server`."
                )
            if self.llama_cache_dir.exists():
                shutil.rmtree(self.llama_cache_dir)
            os.replace(extraction_dir, self.llama_cache_dir)
            binary = self._find_binary(self.llama_cache_dir)
            if binary is None:
                raise BonsaiServerError(
                    "O executável `llama-server` desapareceu após a instalação."
                )
            binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
            (self.llama_cache_dir / LLAMA_RELEASE_MARKER).write_text(
                f"{LLAMA_RELEASE_TAG}\n",
                encoding="ascii",
            )
            (self.llama_cache_dir / LLAMA_BACKEND_MARKER).write_text(
                f"{backend}\n",
                encoding="ascii",
            )
            return str(binary)
        except BonsaiServerError:
            raise
        except (OSError, tarfile.TarError, ValueError) as error:
            raise BonsaiServerError(
                f"Falha ao instalar o binário do llama-server a partir de {url}."
            ) from error
        finally:
            self._remove_if_exists(archive_path)
            if extraction_dir.exists():
                shutil.rmtree(extraction_dir)

    def _ensure_llama_binary(self) -> str:
        asset = self._select_llama_asset()
        backend = self._asset_backend(asset)
        cached_binary = self._cached_llama_binary()
        cached_backend = self._cached_backend() or (
            self._inferred_cached_backend() if cached_binary is not None else None
        )
        if (
            cached_binary is not None
            and self._cached_release() in {None, LLAMA_RELEASE_TAG}
            and cached_backend == backend
        ):
            cached_binary.chmod(cached_binary.stat().st_mode | stat.S_IXUSR)
            return str(cached_binary)
        return self._download_llama_binary(asset)

    @staticmethod
    def _copy_response(response: BinaryIO, output: BinaryIO) -> None:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                return
            output.write(chunk)

    @staticmethod
    def _remove_if_exists(path: Path) -> None:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except FileNotFoundError:
            pass

    def _ensure_model_files(self) -> None:
        artifacts = ((MODEL_FILE, self.model_path),)
        for filename, destination in artifacts:
            if destination.is_file() and destination.stat().st_size > 0:
                continue
            _log(f"Baixando {filename}...")
            self._download_file(f"{MODEL_BASE_URL}/{filename}", destination)

    def _command(self, executable: str) -> list[str]:
        return [
            executable,
            "--model",
            str(self.model_path),
            "--host",
            self.bind_host,
            "--port",
            str(self.port),
            "--jinja",
            "--temp",
            "0",
            "--seed",
            str(DETERMINISTIC_SEED),
            "--sleep-idle-seconds",
            str(IDLE_SECONDS),
        ]

    def _start_process(self, executable: str) -> subprocess.Popen[bytes]:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        process = subprocess.Popen(
            self._command(executable),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        self.pid_path.write_text(str(process.pid), encoding="ascii")
        return process

    def _endpoint_responds(self) -> bool:
        try:
            with urlopen(self._models_url(), timeout=self.request_timeout) as response:
                return response.status == 200
        except (HTTPError, OSError, TimeoutError, URLError):
            return False

    def require_available(self) -> None:
        """Raise an actionable error unless ``/v1/models`` returns HTTP 200."""

        if self._endpoint_responds():
            return
        raise BonsaiServerError(
            f"llama-server nao esta disponivel em {self._models_url()}.\n"
            "Suba o servidor localmente antes dos testes:\n"
            "  python3 tests/integration/model/bonsai_server.py --up"
        )

    def _wait_until_ready(self) -> None:
        for _ in range(self.ready_retries):
            if self._endpoint_responds():
                return
            if self._process is not None and self._process.poll() is not None:
                raise BonsaiServerError(
                    "llama-server encerrou antes de responder a /v1/models."
                )
            time.sleep(self.ready_interval)
        raise BonsaiServerError(
            f"llama-server nao respondeu em {self._models_url()} apos "
            f"{int(self.ready_retries * self.ready_interval)}s."
        )

    def ensure_up(self) -> BonsaiServer:
        """Reuse a running server or download and start one."""

        try:
            self.require_available()
        except BonsaiServerError:
            pass
        else:
            return self

        executable = self._find_executable()
        self._ensure_model_files()
        self._process = self._start_process(executable)
        self._owns_process = True
        try:
            self._wait_until_ready()
        except BonsaiServerError:
            self.stop()
            raise
        _log(f"llama-server disponivel em {self._models_url()}")
        return self

    def _read_pid(self) -> int | None:
        try:
            value = self.pid_path.read_text(encoding="ascii").strip()
            pid = int(value)
        except (FileNotFoundError, OSError, ValueError):
            return None
        return pid if pid > 0 else None

    @staticmethod
    def _pid_is_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except (OSError, ProcessLookupError):
            return False
        return True

    def _terminate_process(self, process: subprocess.Popen[bytes]) -> None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)

    def _terminate_pid_file_process(self) -> None:
        pid = self._read_pid()
        if pid is None or pid == os.getpid():
            self._remove_if_exists(self.pid_path)
            return
        if self._pid_is_alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError as error:
                raise BonsaiServerError(
                    f"Nao foi possivel encerrar o llama-server (PID {pid})."
                ) from error
        self._remove_if_exists(self.pid_path)

    def stop(self, *, force: bool = False) -> None:
        """Stop a process started here, or a persisted process with ``force``."""

        if self._process is not None and self._owns_process:
            self._terminate_process(self._process)
            self._process = None
            self._owns_process = False
            self._remove_if_exists(self.pid_path)
            return
        if force:
            self._terminate_pid_file_process()

    def status(self) -> bool:
        """Return whether the local endpoint is currently responding."""

        return self._endpoint_responds()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gerencia o llama-server local do Bonsai 27B."
    )
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--up", action="store_true", help="Baixa e sobe o servidor.")
    actions.add_argument("--down", action="store_true", help="Encerra o servidor.")
    actions.add_argument(
        "--status",
        action="store_true",
        help="Verifica se o endpoint local esta respondendo.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Bonsai server command-line utility."""

    args = _parser().parse_args(argv)
    server = BonsaiServer()
    try:
        if args.up:
            server.ensure_up()
            print(f"OK: llama-server disponivel em {server._models_url()}")
        elif args.down:
            server.stop(force=True)
            print("OK: llama-server encerrado.")
        elif args.status:
            if not server.status():
                raise BonsaiServerError(
                    f"llama-server nao esta disponivel em {server._models_url()}."
                )
            print(f"OK: llama-server disponivel em {server._models_url()}")
    except BonsaiServerError as error:
        print(f"[bonsai-server] ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
