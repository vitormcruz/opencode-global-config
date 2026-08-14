"""Docker session tooling for the OpenCode integration tests.

The module is usable both from pytest fixtures and as the command-line
orchestrator that the Makefile invokes.  It deliberately uses only the
standard library so the host does not need an extra Docker client package.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
CONTAINER_NAME = "opencode-config-test"
IMAGE_NAME = "opencode-config-test:latest"
NETWORK_NAME = "opencode-test-net"
HOST_PORT = 4196
CONTAINER_PORT = 4096


class ContainerTestError(RuntimeError):
    """Raised when the Docker/OpenCode test prerequisites are not met."""


def _log(message: str) -> None:
    print(f"[container-test-opencode] {message}")


@dataclass
class DockerSession:
    """Manage the test image and container lifecycle."""

    repo_root: Path = REPO_ROOT
    script_dir: Path = SCRIPT_DIR
    container_name: str = CONTAINER_NAME
    image_name: str = IMAGE_NAME
    host_port: int = HOST_PORT
    container_port: int = CONTAINER_PORT
    ready_retries: int = 45
    ready_interval: float = 2.0
    _docker: str | None = field(default=None, init=False, repr=False)

    def docker_executable(self) -> str:
        """Return Docker's executable or raise an actionable prerequisite error."""

        if self._docker is None:
            self._docker = shutil.which("docker")
        if self._docker is None:
            raise ContainerTestError(
                "Docker não encontrado no PATH.\n"
                "Instale Docker Desktop (ou Docker Engine) e execute novamente:\n"
                "  docker --version\n"
                "  pytest -m opencode"
            )
        return self._docker

    def _run_docker(
        self,
        *arguments: str,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.docker_executable(), *arguments],
            capture_output=capture_output,
            text=True,
            check=False,
        )

    def check_docker(self) -> None:
        """Verify that Docker is installed and its daemon is reachable."""

        result = self._run_docker("info")
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            suffix = f"\nDetalhes: {detail}" if detail else ""
            raise ContainerTestError(
                "Docker daemon não está em execução.\n"
                "Inicie Docker Desktop (ou o serviço Docker) e execute:\n"
                "  docker info\n"
                "  pytest -m opencode"
                f"{suffix}"
            )

    def container_exists(self) -> bool:
        """Return whether the named container exists, running or stopped."""

        result = self._run_docker(
            "ps",
            "-a",
            "--filter",
            f"name=^{self.container_name}$",
            "--format",
            "{{.Names}}",
        )
        return result.returncode == 0 and self.container_name in result.stdout.split()

    def container_running(self) -> bool:
        """Return whether the named container is currently running."""

        result = self._run_docker(
            "ps",
            "--filter",
            f"name=^{self.container_name}$",
            "--format",
            "{{.Names}}",
        )
        return result.returncode == 0 and self.container_name in result.stdout.split()

    def network_exists(self) -> bool:
        """Return whether the dedicated internal test network exists."""

        result = self._run_docker(
            "network",
            "ls",
            "--filter",
            f"name=^{NETWORK_NAME}$",
            "--format",
            "{{.Name}}",
        )
        return result.returncode == 0 and NETWORK_NAME in result.stdout.split()

    def ensure_test_network(self) -> None:
        """Create the isolated test network when it is not already present."""

        if self.network_exists():
            return
        _log(f"Criando rede Docker interna '{NETWORK_NAME}'...")
        self._checked_docker("network", "create", "--internal", NETWORK_NAME)

    def container_uses_test_network(self) -> bool:
        """Return whether the named container is attached only to the test network."""

        result = self._run_docker(
            "inspect",
            "--format",
            "{{json .NetworkSettings.Networks}}",
            self.container_name,
        )
        if result.returncode != 0:
            return False
        try:
            networks = json.loads(result.stdout)
        except json.JSONDecodeError:
            return False
        return isinstance(networks, dict) and set(networks) == {NETWORK_NAME}

    def remove_container_if_exists(self) -> None:
        """Remove the named container when present."""

        if self.container_exists():
            self._run_docker("rm", "-f", self.container_name)

    def _checked_docker(self, *arguments: str) -> str:
        result = self._run_docker(*arguments)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise ContainerTestError(
                f"Comando Docker falhou: docker {' '.join(arguments)}"
                + (f"\nDetalhes: {detail}" if detail else "")
            )
        return result.stdout

    def build_image(self) -> None:
        """Build the dedicated OpenCode test image."""

        _log(f"Construindo imagem Docker '{self.image_name}'...")
        self._checked_docker(
            "build",
            "-t",
            self.image_name,
            "-f",
            str(self.script_dir / "Dockerfile"),
            str(self.repo_root),
        )
        _log("Imagem construída com sucesso.")

    def _container_logs(self) -> str:
        result = self._run_docker("logs", self.container_name)
        lines = (result.stdout or result.stderr).splitlines()
        return "\n".join(lines[-20:])

    def start_container(self) -> None:
        """Start or create the container and wait for OpenCode's HTTP endpoint."""

        self.ensure_test_network()
        if self.container_exists() and not self.container_uses_test_network():
            _log(
                f"Container '{self.container_name}' está fora da rede isolada. "
                "Recriando..."
            )
            self.remove_container_if_exists()

        if self.container_running():
            _log(f"Container '{self.container_name}' já está em execução. Reusando.")
        elif self.container_exists():
            _log(f"Container '{self.container_name}' existe parado. Reiniciando...")
            self._checked_docker("start", self.container_name)
        else:
            _log(f"Criando e iniciando container '{self.container_name}'...")
            docker_options = ["--add-host=host.docker.internal:host-gateway"]
            docker_volumes: list[str] = []
            config_path = os.environ.get("OPENCODE_CONFIG", "")
            if config_path and Path(config_path).is_file():
                container_config = "/opt/opencode-config/host-opencode-config.json"
                docker_options.extend(["-e", f"OPENCODE_CONFIG={container_config}"])
                docker_volumes.extend(
                    ["-v", f"{config_path}:{container_config}:ro"]
                )

            host_ca = Path("/etc/ssl/certs/ca-certificates.crt")
            if host_ca.is_file():
                docker_options.extend(
                    ["-e", "NODE_EXTRA_CA_CERTS=/etc/ssl/certs/host-ca-certificates.crt"]
                )
                docker_volumes.extend(
                    ["-v", f"{host_ca}:/etc/ssl/certs/host-ca-certificates.crt:ro"]
                )

            self._checked_docker(
                "run",
                "-d",
                "--name",
                self.container_name,
                "--network",
                NETWORK_NAME,
                "-p",
                f"{self.host_port}:{self.container_port}",
                *docker_options,
                *docker_volumes,
                self.image_name,
            )

        self._wait_until_ready()

    def _wait_until_ready(self) -> None:
        """Wait for OpenCode and report container logs on startup failure."""

        _log(
            f"Aguardando OpenCode ficar disponível na porta {self.host_port}..."
        )
        url = f"http://127.0.0.1:{self.host_port}/"
        for _ in range(self.ready_retries):
            try:
                with urlopen(url, timeout=2):
                    _log(f"OpenCode disponível em {url}")
                    return
            except (HTTPError, OSError, TimeoutError, URLError):
                if not self.container_running():
                    logs = self._container_logs()
                    detail = f"\n{logs}" if logs else ""
                    raise ContainerTestError(
                        f"Container '{self.container_name}' parou inesperadamente."
                        f"\nLogs do container:{detail}"
                    )
            time.sleep(self.ready_interval)

        logs = self._container_logs()
        detail = f"\n{logs}" if logs else ""
        raise ContainerTestError(
            f"OpenCode não respondeu após "
            f"{int(self.ready_retries * self.ready_interval)}s."
            f"\nLogs do container:{detail}"
        )

    def stop_container(self) -> None:
        """Stop the test container when it is running."""

        if self.container_running():
            _log(f"Parando container '{self.container_name}'...")
            self._checked_docker("stop", self.container_name)
        else:
            _log(f"Container '{self.container_name}' não está em execução.")

    def ensure_up(self, *, rebuild: bool = False) -> None:
        """Build and start the fixed local-model container."""

        self.check_docker()
        self.ensure_test_network()
        if rebuild:
            self.remove_container_if_exists()
            self.build_image()
        elif not self.container_exists():
            self.build_image()

        self.start_container()

    def down(self) -> None:
        """Stop the container, retaining the image and container for reuse."""

        self.check_docker()
        self.stop_container()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gerencia o container Docker dos testes do OpenCode."
    )
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--up", action="store_true", help="Reusa ou cria o container.")
    actions.add_argument(
        "--rebuild",
        action="store_true",
        help="Reconstrói a imagem e recria o container.",
    )
    actions.add_argument("--down", action="store_true", help="Para o container.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Docker orchestration command."""

    args = _parser().parse_args(argv)
    session = DockerSession()
    try:
        if args.down:
            session.down()
        else:
            session.ensure_up(rebuild=args.rebuild)
    except ContainerTestError as error:
        print(f"[container-test-opencode] ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
