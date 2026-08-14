"""Provision and manage the local Bonsai model server.

The utility intentionally uses only Python's standard library.  The model is
downloaded once to the user's cache and the llama-server process can be reused
by successive pytest executions.
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


MODEL_REPOSITORY = "prism-ml/Bonsai-27B-gguf"
MODEL_FILE = "Bonsai-27B-Q1_0.gguf"
MMPROJ_FILE = "Bonsai-27B-mmproj-Q8_0.gguf"
MODEL_BASE_URL = f"https://huggingface.co/{MODEL_REPOSITORY}/resolve/main"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "opencode-config" / "models"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_BIND_HOST = "0.0.0.0"
DEFAULT_PORT = 8080
IDLE_SECONDS = 600
PID_FILE_NAME = "llama-server.pid"


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
    def mmproj_path(self) -> Path:
        """Return the fixed path of the multimodal projector weights."""

        return self.cache_dir / MMPROJ_FILE

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
        executable = self.executable or shutil.which("llama-server")
        if executable is None:
            raise BonsaiServerError(
                "llama-server nao encontrado no PATH. "
                "Instale o llama.cpp e verifique:\n"
                "  llama-server --version\n"
                "Depois execute:\n"
                "  python3 tests/integration/model/bonsai_server.py --up"
            )
        return executable

    def _download_file(self, url: str, destination: Path) -> None:
        """Download one model artifact atomically."""

        temporary_path = destination.with_name(f".{destination.name}.part")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            with urlopen(url, timeout=60) as response:
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
    def _copy_response(response: BinaryIO, output: BinaryIO) -> None:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                return
            output.write(chunk)

    @staticmethod
    def _remove_if_exists(path: Path) -> None:
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    def _ensure_model_files(self) -> None:
        artifacts = (
            (MODEL_FILE, self.model_path),
            (MMPROJ_FILE, self.mmproj_path),
        )
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
            "--mmproj",
            str(self.mmproj_path),
            "--host",
            self.bind_host,
            "--port",
            str(self.port),
            "--jinja",
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

        self._ensure_model_files()
        executable = self._find_executable()
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
