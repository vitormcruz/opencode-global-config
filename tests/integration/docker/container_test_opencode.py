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
import signal
import socket
import subprocess
import sys
import tempfile
import threading
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


def _forward_socket(source: socket.socket, destination: socket.socket) -> None:
    """Forward bytes in one direction until either socket closes."""

    try:
        while True:
            payload = source.recv(64 * 1024)
            if not payload:
                return
            destination.sendall(payload)
    except OSError:
        return
    finally:
        try:
            destination.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def _proxy_connection(
    client: socket.socket,
    target_host: str,
    target_port: int,
) -> None:
    """Bridge one host connection to the container's internal OpenCode port."""

    try:
        target = socket.create_connection((target_host, target_port), timeout=5)
    except OSError:
        client.close()
        return

    with client, target:
        threads = [
            threading.Thread(
                target=_forward_socket,
                args=(client, target),
                daemon=True,
            ),
            threading.Thread(
                target=_forward_socket,
                args=(target, client),
                daemon=True,
            ),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()


def _run_tcp_proxy(
    bind_host: str,
    bind_port: int,
    target_host: str,
    target_port: int,
    pid_file: Path,
) -> None:
    """Run the localhost-only proxy used with Docker internal networks."""

    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()), encoding="ascii")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((bind_host, bind_port))
            listener.listen()
            while True:
                client, _ = listener.accept()
                threading.Thread(
                    target=_proxy_connection,
                    args=(client, target_host, target_port),
                    daemon=True,
                ).start()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            pid_file.unlink()
        except FileNotFoundError:
            pass


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

    def network_is_internal(self) -> bool:
        """Return whether the dedicated network has Docker internal isolation."""

        result = self._run_docker(
            "network",
            "inspect",
            "--format",
            "{{.Internal}}",
            NETWORK_NAME,
        )
        return result.returncode == 0 and result.stdout.strip().lower() == "true"

    def network_gateway(self) -> str:
        """Return the IPv4 gateway assigned to the dedicated test network."""

        result = self._run_docker(
            "network",
            "inspect",
            "--format",
            "{{(index .IPAM.Config 0).Gateway}}",
            NETWORK_NAME,
        )
        gateway = result.stdout.strip()
        if result.returncode != 0 or not gateway:
            detail = (result.stderr or result.stdout).strip()
            raise ContainerTestError(
                f"Não foi possível descobrir o gateway da rede '{NETWORK_NAME}'."
                + (f"\nDetalhes: {detail}" if detail else "")
            )
        return gateway

    def ensure_test_network(self) -> None:
        """Create the isolated test network when it is not already present."""

        if self.network_exists():
            if self.network_is_internal():
                return
            _log(
                f"A rede '{NETWORK_NAME}' não é interna. "
                "Recriando a rede dedicada..."
            )
            self.remove_container_if_exists()
            self._checked_docker("network", "rm", NETWORK_NAME)
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

    def container_ip(self) -> str:
        """Return the container IP on the dedicated internal network."""

        result = self._run_docker(
            "inspect",
            "--format",
            "{{json .NetworkSettings.Networks}}",
            self.container_name,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise ContainerTestError(
                f"Não foi possível inspecionar o container '{self.container_name}'."
                + (f"\nDetalhes: {detail}" if detail else "")
            )
        try:
            networks = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise ContainerTestError(
                f"Configuração de rede inválida no container '{self.container_name}'."
            )
        network = networks.get(NETWORK_NAME) if isinstance(networks, dict) else None
        ip_address = network.get("IPAddress") if isinstance(network, dict) else None
        if not isinstance(ip_address, str) or not ip_address:
            raise ContainerTestError(
                f"O container '{self.container_name}' não possui IP em "
                f"'{NETWORK_NAME}'."
            )
        return ip_address

    @property
    def proxy_pid_path(self) -> Path:
        """Return the state path for the host-side localhost proxy."""

        return Path(tempfile.gettempdir()) / f"{self.container_name}-proxy.pid"

    def _read_proxy_pid(self) -> int | None:
        try:
            pid = int(self.proxy_pid_path.read_text(encoding="ascii").strip())
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

    def stop_proxy(self) -> None:
        """Stop a previous proxy process and remove its state file."""

        pid = self._read_proxy_pid()
        if pid is not None and self._pid_is_alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            deadline = time.monotonic() + 5
            while self._pid_is_alive(pid) and time.monotonic() < deadline:
                time.sleep(0.05)
        try:
            self.proxy_pid_path.unlink()
        except FileNotFoundError:
            pass

    def start_proxy(self, target_host: str) -> None:
        """Start a localhost proxy to the container's internal API port."""

        self.stop_proxy()
        subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--proxy",
                "--proxy-bind-host",
                "127.0.0.1",
                "--proxy-bind-port",
                str(self.host_port),
                "--proxy-target-host",
                target_host,
                "--proxy-target-port",
                str(self.container_port),
                "--proxy-pid-file",
                str(self.proxy_pid_path),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        for _ in range(100):
            pid = self._read_proxy_pid()
            if pid is not None and self._pid_is_alive(pid):
                return
            time.sleep(0.05)
        raise ContainerTestError(
            f"O proxy local não iniciou em 127.0.0.1:{self.host_port}."
        )

    def container_has_host_gateway(self, gateway: str) -> bool:
        """Return whether the container maps the model host to this network gateway."""

        result = self._run_docker(
            "inspect",
            "--format",
            "{{json .HostConfig.ExtraHosts}}",
            self.container_name,
        )
        if result.returncode != 0:
            return False
        try:
            extra_hosts = json.loads(result.stdout)
        except json.JSONDecodeError:
            return False
        expected = f"host.docker.internal:{gateway}"
        return isinstance(extra_hosts, list) and expected in extra_hosts

    def container_is_compatible(self, gateway: str) -> bool:
        """Return whether an existing container matches the fixed runtime topology."""

        return (
            self.container_uses_test_network()
            and self.container_has_host_gateway(gateway)
        )

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
        gateway = self.network_gateway()
        self.stop_proxy()
        if self.container_exists() and not self.container_is_compatible(gateway):
            _log(
                f"Container '{self.container_name}' não corresponde à topologia "
                "isolada atual. Recriando..."
            )
            self.remove_container_if_exists()

        if self.container_running():
            _log(f"Container '{self.container_name}' já está em execução. Reusando.")
        elif self.container_exists():
            _log(f"Container '{self.container_name}' existe parado. Reiniciando...")
            self._checked_docker("start", self.container_name)
        else:
            _log(f"Criando e iniciando container '{self.container_name}'...")
            docker_options = [f"--add-host=host.docker.internal:{gateway}"]
            docker_volumes: list[str] = []

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
                *docker_options,
                *docker_volumes,
                self.image_name,
            )

        self.start_proxy(self.container_ip())
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

        self.stop_proxy()
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
            self.stop_proxy()
            self.remove_container_if_exists()
            self.build_image()
        elif not self.container_exists():
            self.build_image()

        self.start_container()

    def down(self) -> None:
        """Stop the container, retaining the image and container for reuse."""

        self.check_docker()
        self.stop_proxy()
        self.stop_container()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gerencia o container Docker dos testes do OpenCode."
    )
    actions = parser.add_mutually_exclusive_group(required=False)
    actions.add_argument("--up", action="store_true", help="Reusa ou cria o container.")
    actions.add_argument(
        "--rebuild",
        action="store_true",
        help="Reconstrói a imagem e recria o container.",
    )
    actions.add_argument("--down", action="store_true", help="Para o container.")
    parser.add_argument("--proxy", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--proxy-bind-host", help=argparse.SUPPRESS)
    parser.add_argument("--proxy-bind-port", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--proxy-target-host", help=argparse.SUPPRESS)
    parser.add_argument("--proxy-target-port", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--proxy-pid-file", type=Path, help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Docker orchestration command."""

    args = _parser().parse_args(argv)
    if args.proxy:
        proxy_arguments = (
            args.proxy_bind_host,
            args.proxy_bind_port,
            args.proxy_target_host,
            args.proxy_target_port,
            args.proxy_pid_file,
        )
        if any(argument is None for argument in proxy_arguments):
            _parser().error("os argumentos internos do proxy são obrigatórios")
        _run_tcp_proxy(
            args.proxy_bind_host,
            args.proxy_bind_port,
            args.proxy_target_host,
            args.proxy_target_port,
            args.proxy_pid_file,
        )
        return 0
    if not (args.up or args.rebuild or args.down):
        _parser().error("informe uma ação: --up, --rebuild ou --down")

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
