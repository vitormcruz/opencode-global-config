"""Provision and manage the local Qwen3-0.6B model server.

The utility intentionally uses only Python's standard library.  The model is
downloaded once to the user's cache and the llama-server process can be reused
by successive pytest executions.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
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

from opencode_config.bootstrap.libgomp import (
    runtime_directory,
    runtime_validation_error,
)


@dataclass(frozen=True)
class LocalModelSpec:
    """Fixed artifact and OpenCode contract for the Qwen3-0.6B model."""

    name: str
    repository: str
    file_name: str
    provider: str
    model_id: str
    display_name: str
    sha256: str | None = None

    @property
    def base_url(self) -> str:
        return f"https://huggingface.co/{self.repository}/resolve/main"


MODEL_SPEC = LocalModelSpec(
    name="qwen3-0.6b",
    repository="Qwen/Qwen3-0.6B-GGUF",
    file_name="Qwen3-0.6B-Q8_0.gguf",
    provider="qwen-local",
    model_id="qwen3-0.6b",
    display_name="Qwen3 0.6B Q8_0",
    sha256=(
        "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
    ),
)
DEFAULT_MODEL = MODEL_SPEC.model_id
MODEL_REPOSITORY = MODEL_SPEC.repository
MODEL_FILE = MODEL_SPEC.file_name
MODEL_BASE_URL = MODEL_SPEC.base_url
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "opencode-config" / "models"
LLAMA_RELEASE_TAG = "prism-b9596-9fcaed7"
LLAMA_RELEASE_BASE_URL = (
    "https://github.com/PrismML-Eng/llama.cpp/releases/download/"
    f"{LLAMA_RELEASE_TAG}"
)
DEFAULT_LLAMA_CACHE_DIR = Path.home() / ".cache" / "opencode-config" / "llama"
LLAMA_RELEASE_MARKER = ".llama_release"
LLAMA_BACKEND_MARKER = ".llama_backend"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_BIND_HOST = "0.0.0.0"
DEFAULT_PORT = 8080
IDLE_SECONDS = 600
DETERMINISTIC_SEED = 42
CONTEXT_SIZE = 16_384
PID_FILE_NAME = "llama-server.pid"
DOWNLOAD_TIMEOUT_SECONDS = 600
LOCAL_REQUEST_TIMEOUT_SECONDS = 600


class LocalModelServerError(RuntimeError):
    """Raised when the local Qwen server cannot be provisioned or reached."""


def _log(message: str) -> None:
    print(f"[qwen-server] {message}")


@dataclass
class LocalModelServer:
    """Manage a persistent llama-server process for the fixed Qwen model."""
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
    request_timeout: float = LOCAL_REQUEST_TIMEOUT_SECONDS
    _process: subprocess.Popen[bytes] | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _owns_process: bool = field(default=False, init=False, repr=False)

    @property
    def model_path(self) -> Path:
        """Return the fixed path of the Qwen model weights."""

        return self.cache_dir / MODEL_SPEC.file_name

    @property
    def model_spec(self) -> LocalModelSpec:
        """Return the immutable Qwen model contract."""

        return MODEL_SPEC

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
                raise LocalModelServerError(f"Download vazio recebido de {url}")
            os.replace(temporary_path, destination)
        except LocalModelServerError:
            self._remove_if_exists(temporary_path)
            raise
        except (HTTPError, OSError, TimeoutError, URLError) as error:
            self._remove_if_exists(temporary_path)
            raise LocalModelServerError(
                f"Falha ao baixar o artefato do Qwen: {url}\n"
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
            raise LocalModelServerError(
                f"Arquitetura Linux não suportada para o llama-server: {architecture}."
            )

        cuda_version = cls._cuda_version()
        if cuda_version is not None:
            if not cls._cuda_runtime_available():
                backend = (
                    "Vulkan" if shutil.which("vulkaninfo") is not None else "CPU"
                )
                _log(
                    "CUDA ignorado: runtime ausente "
                    "(libcudart.so.12/libcublas.so.12). "
                    f"Usando backend {backend}; nenhum pacote de sistema será instalado."
                )
                if backend == "Vulkan":
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
                raise LocalModelServerError(
                    f"Arquivo inseguro no pacote do llama-server: {member.name}"
                )
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise LocalModelServerError(
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
            raise LocalModelServerError(
                f"Tipo de arquivo não suportado no pacote do llama-server: "
                f"{member.name}"
            )

        for member in link_members:
            target = (destination / member.name).resolve()
            if target.exists() or target.is_symlink():
                raise LocalModelServerError(
                    f"Arquivo duplicado no pacote do llama-server: {member.name}"
                )
            target.parent.mkdir(parents=True, exist_ok=True)
            link_target = Path(member.linkname)
            if member.issym():
                if link_target.is_absolute():
                    raise LocalModelServerError(
                        f"Link absoluto no pacote do llama-server: {member.name}"
                    )
                resolved_link = (target.parent / link_target).resolve()
                if resolved_link != root and root not in resolved_link.parents:
                    raise LocalModelServerError(
                        f"Link inseguro no pacote do llama-server: {member.name}"
                    )
                target.symlink_to(member.linkname)
                continue
            resolved_link = (destination / link_target).resolve()
            if resolved_link != root and root not in resolved_link.parents:
                raise LocalModelServerError(
                    f"Hard link inseguro no pacote do llama-server: {member.name}"
                )
            if not resolved_link.is_file() or resolved_link.is_symlink():
                raise LocalModelServerError(
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
                raise LocalModelServerError(
                    "O pacote do llama-server não contém um executável "
                    "`llama-server`."
                )
            if self.llama_cache_dir.exists():
                shutil.rmtree(self.llama_cache_dir)
            os.replace(extraction_dir, self.llama_cache_dir)
            binary = self._find_binary(self.llama_cache_dir)
            if binary is None:
                raise LocalModelServerError(
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
        except LocalModelServerError:
            raise
        except (OSError, tarfile.TarError, ValueError) as error:
            raise LocalModelServerError(
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
        spec = self.model_spec
        artifacts = ((spec.file_name, self.model_path),)
        for filename, destination in artifacts:
            if destination.is_file() and destination.stat().st_size > 0:
                self._validate_artifact(destination, spec)
                continue
            _log(f"Baixando {filename}...")
            self._download_file(f"{spec.base_url}/{filename}", destination)
            self._validate_artifact(destination, spec)

    @staticmethod
    def _validate_artifact(path: Path, spec: LocalModelSpec) -> None:
        if spec.sha256 is None:
            return
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != spec.sha256:
            raise LocalModelServerError(
                f"Checksum SHA-256 inválido para {spec.file_name}: {digest}."
            )

    def _command(self, executable: str) -> list[str]:
        return [
            executable,
            "--model",
            str(self.model_path),
            "--ctx-size",
            str(CONTEXT_SIZE),
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

    @staticmethod
    def _dynamic_loader() -> Path:
        if platform.machine().lower() not in {"x86_64", "amd64"}:
            raise LocalModelServerError(
                "O carregador ELF da runtime Prism suporta somente Linux x86_64."
            )
        candidates = (
            Path("/lib64/ld-linux-x86-64.so.2"),
            Path("/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2"),
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        raise LocalModelServerError(
            "Carregador ELF ld-linux-x86-64.so.2 ausente; "
            "execute o bootstrap em uma distribuicao Linux/WSL suportada."
        )

    def _ensure_libgomp_runtime(self) -> Path:
        error = runtime_validation_error()
        if error is not None:
            raise LocalModelServerError(
                "Dependencia libgomp.so.1 ausente, invalida ou incompativel "
                f"({error}).\n"
                "Execute o bootstrap WSL/Linux para provisionar a runtime "
                "user-space:\n"
                "  opencode-bootstrap --yes"
            )
        return runtime_directory()

    def _launch_command(self, executable: str) -> list[str]:
        """Use the ELF interpreter's library path, never LD_LIBRARY_PATH."""

        runtime = self._ensure_libgomp_runtime()
        system_paths = (
            Path(executable).resolve().parent,
            Path("/lib/x86_64-linux-gnu"),
            Path("/usr/lib/x86_64-linux-gnu"),
            Path("/lib64"),
            Path("/usr/lib64"),
        )
        library_paths = [
            str(path)
            for path in (runtime, *system_paths)
            if path.is_dir()
        ]
        return [
            str(self._dynamic_loader()),
            "--library-path",
            ":".join(library_paths),
            executable,
            *self._command(executable)[1:],
        ]

    def _start_process(self, executable: str) -> subprocess.Popen[bytes]:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        process = subprocess.Popen(
            self._launch_command(executable),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            cwd=Path(executable).resolve().parent,
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
        raise LocalModelServerError(
            f"llama-server nao esta disponivel em {self._models_url()}.\n"
            "Suba o servidor localmente antes dos testes:\n"
            "  python3 tests/integration/model/local_model_server.py --up"
        )

    def _endpoint_matches_model(self) -> bool:
        try:
            with urlopen(self._models_url(), timeout=self.request_timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, OSError, TimeoutError, URLError, json.JSONDecodeError):
            return False

        entries = payload.get("data", []) if isinstance(payload, dict) else []
        if not isinstance(entries, list):
            return False
        expected = self.model_spec.file_name
        return any(
            isinstance(entry, dict)
            and expected in {entry.get("id"), entry.get("model"), entry.get("name")}
            for entry in entries
        )

    def _pid_file_process_is_owned(self, pid: int) -> bool:
        """Check that a persisted PID is one of this runner's llama servers."""

        if pid == os.getpid() or not self._pid_is_alive(pid):
            return False
        try:
            command = [
                argument.decode("utf-8", errors="replace")
                for argument in (Path("/proc") / str(pid) / "cmdline")
                .read_bytes()
                .split(b"\0")
                if argument
            ]
        except OSError:
            return False
        if not command or Path(command[0]).name != "llama-server":
            return False

        try:
            model_argument = command[command.index("--model") + 1]
            port_argument = command[command.index("--port") + 1]
            host_argument = command[command.index("--host") + 1]
        except (ValueError, IndexError):
            return False

        model_path = Path(model_argument).resolve()
        cache_dir = self.cache_dir.resolve()
        known_model_paths = {(cache_dir / MODEL_SPEC.file_name).resolve()}
        return (
            model_path in known_model_paths
            and port_argument == str(self.port)
            and host_argument == self.bind_host
        )

    def _reconcile_mismatched_endpoint(self) -> None:
        """Stop only an owned server before replacing its model on the fixed port."""

        if self._process is not None and self._owns_process:
            self.stop()
        else:
            pid = self._read_pid()
            if pid is None or not self._pid_file_process_is_owned(pid):
                raise LocalModelServerError(
                    f"llama-server expõe outro modelo em {self._models_url()}, "
                    "mas o processo não pertence a este runner; "
                    "não será encerrado nem substituído."
                )
            if not self._terminate_pid_file_process():
                raise LocalModelServerError(
                    "Não foi possível reconciliar o llama-server persistido "
                    "com segurança."
                )

        if self._endpoint_responds():
            raise LocalModelServerError(
                f"A porta {self.port} continua ocupada após encerrar o "
                "llama-server pertencente a este runner."
            )

    def _wait_until_ready(self) -> None:
        for _ in range(self.ready_retries):
            if self._endpoint_responds():
                return
            if self._process is not None and self._process.poll() is not None:
                raise LocalModelServerError(
                    "llama-server encerrou antes de responder a /v1/models."
                )
            time.sleep(self.ready_interval)
        raise LocalModelServerError(
            f"llama-server nao respondeu em {self._models_url()} apos "
            f"{int(self.ready_retries * self.ready_interval)}s."
        )

    def ensure_up(self) -> LocalModelServer:
        """Reuse a running server or download and start one."""

        try:
            self.require_available()
        except LocalModelServerError:
            pass
        else:
            if self._endpoint_matches_model():
                return self
            self._reconcile_mismatched_endpoint()

        executable = self._find_executable()
        self._ensure_model_files()
        self._process = self._start_process(executable)
        self._owns_process = True
        try:
            self._wait_until_ready()
        except LocalModelServerError:
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

    def _terminate_pid_file_process(self) -> bool:
        pid = self._read_pid()
        if pid is None or pid == os.getpid():
            self._remove_if_exists(self.pid_path)
            return False
        if not self._pid_file_process_is_owned(pid):
            return False
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError as error:
            raise LocalModelServerError(
                f"Nao foi possivel encerrar o llama-server (PID {pid})."
            ) from error
        self._remove_if_exists(self.pid_path)
        return True

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
        description="Gerencia o llama-server local do Qwen3-0.6B."
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
    """Run the Qwen server command-line utility."""

    args = _parser().parse_args(argv)
    server = LocalModelServer()
    try:
        if args.up:
            server.ensure_up()
            print(f"OK: llama-server disponivel em {server._models_url()}")
        elif args.down:
            server.stop(force=True)
            print("OK: llama-server encerrado.")
        elif args.status:
            if not server.status():
                raise LocalModelServerError(
                    f"llama-server nao esta disponivel em {server._models_url()}."
                )
            print(f"OK: llama-server disponivel em {server._models_url()}")
    except LocalModelServerError as error:
        print(f"[qwen-server] ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
