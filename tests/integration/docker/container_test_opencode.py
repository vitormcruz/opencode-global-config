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
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
CONTAINER_NAME = "opencode-config-test"
IMAGE_NAME = "opencode-config-test:latest"
HOST_PORT = 4196
CONTAINER_PORT = 4096


class ContainerTestError(RuntimeError):
    """Raised when the Docker/OpenCode test prerequisites are not met."""


def _json_scalar(value: Any) -> str:
    """Render a jq ``-r``-like scalar for the uncommon non-string case."""

    if isinstance(value, str):
        return value
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def extract_models_from_config(config_file: str | Path) -> list[str]:
    """Return unique ``provider/model`` names declared by an OpenCode config.

    This mirrors the former jq pipeline: agent models are read from
    ``agent.*.model`` and provider models from ``provider.*.models``.  Invalid
    or missing files intentionally produce an empty result, matching the
    shell helper's silent failure behavior.
    """

    try:
        with Path(config_file).open(encoding="utf-8") as stream:
            config = json.load(stream)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return []

    if not isinstance(config, dict):
        return []

    models: set[str] = set()
    agent = config.get("agent")
    if isinstance(agent, dict):
        agent_entries = agent.values()
    elif isinstance(agent, list):
        agent_entries = agent
    else:
        agent_entries = ()

    for entry in agent_entries:
        if not isinstance(entry, dict):
            continue
        model = entry.get("model")
        # jq's ``// empty`` omits null and false, but preserves an empty string.
        if model is None or model is False:
            continue
        rendered = _json_scalar(model)
        if rendered:
            models.add(rendered)

    provider = config.get("provider")
    if isinstance(provider, dict):
        for provider_name, provider_config in provider.items():
            if not isinstance(provider_config, dict):
                continue
            provider_models = provider_config.get("models")
            if not isinstance(provider_models, dict):
                continue
            for model_name in provider_models:
                models.add(f"{provider_name}/{model_name}")

    # jq's ``unique`` sorts before emitting.
    return sorted(models)


def _log(message: str) -> None:
    print(f"[container-test-opencode] {message}")


def _warn(message: str) -> None:
    print(f"[container-test-opencode] WARN: {message}", file=sys.stderr)


def _model_error() -> ContainerTestError:
    return ContainerTestError(
        "OPENCODE_TEST_MODEL não definido.\n\n"
        "Para executar testes de integração, defina explicitamente o modelo:\n\n"
        "  export OPENCODE_TEST_MODEL='seu-modelo-aqui'\n"
        "  pytest -m opencode\n\n"
        "Exemplos:\n"
        "  - OpenAI:      export OPENCODE_TEST_MODEL='openai/gpt-4'\n"
        "  - Anthropic:   export OPENCODE_TEST_MODEL='anthropic/claude-3-5-sonnet'\n"
        "  - Local (Ollama): export OPENCODE_TEST_MODEL='ollama/llama3.1'\n\n"
        "Para listar modelos disponíveis no ambiente Docker, execute:\n"
        "  python3 tests/integration/docker/container_test_opencode.py --models\n\n"
        "IMPORTANTE: em ambientes corporativos/sensíveis, use apenas modelos "
        "aprovados pela sua organização."
    )


def choose_model_interactively(models: list[str]) -> str:
    """Prompt for one model, retaining the shell helper's numbered workflow."""

    if not models:
        raise ContainerTestError("Nenhum modelo disponível para seleção.")

    print("Modelos disponíveis:", file=sys.stderr)
    for index, model in enumerate(models, start=1):
        print(f"  {index}) {model}", file=sys.stderr)
    print(file=sys.stderr)

    while True:
        try:
            choice = input("Escolha o número do modelo: ")
        except EOFError as error:
            raise _model_error() from error
        if choice.isdigit() and 1 <= int(choice) <= len(models):
            return models[int(choice) - 1]
        print("Escolha inválida. Digite um número da lista.", file=sys.stderr)


def select_model_if_needed(*, interactive: bool) -> str:
    """Resolve the model from the environment or, optionally, config prompt."""

    configured = os.environ.get("OPENCODE_TEST_MODEL", "")
    if configured:
        _log(f"Modelo configurado: {configured}")
        return configured

    config_path = os.environ.get("OPENCODE_CONFIG", "")
    if config_path:
        path = Path(config_path)
        if path.is_file():
            config_models = extract_models_from_config(path)
            if config_models:
                if not interactive:
                    raise _model_error()
                _log(f"Modelos encontrados em OPENCODE_CONFIG ({path}):")
                selected = choose_model_interactively(config_models)
                os.environ["OPENCODE_TEST_MODEL"] = selected
                _log(f"Modelo selecionado: {selected}")
                return selected
            _warn(f"Nenhum modelo encontrado em OPENCODE_CONFIG: {path}")
        else:
            _warn(f"OPENCODE_CONFIG aponta para arquivo inexistente: {path}")

    raise _model_error()


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

    def list_models(self) -> str:
        """List models exposed by the built OpenCode image."""

        return self._checked_docker(
            "run",
            "--rm",
            self.image_name,
            "/root/.opencode/bin/opencode",
            "--pure",
            "models",
        )

    def _container_logs(self) -> str:
        result = self._run_docker("logs", self.container_name)
        lines = (result.stdout or result.stderr).splitlines()
        return "\n".join(lines[-20:])

    def start_container(self) -> None:
        """Start or create the container and wait for OpenCode's HTTP endpoint."""

        if self.container_running():
            _log(f"Container '{self.container_name}' já está em execução. Reusando.")
        elif self.container_exists():
            _log(f"Container '{self.container_name}' existe parado. Reiniciando...")
            self._checked_docker("start", self.container_name)
        else:
            model = os.environ.get("OPENCODE_TEST_MODEL", "")
            if not model:
                raise _model_error()
            _log(f"Criando e iniciando container '{self.container_name}'...")
            docker_env = ["-e", f"OPENCODE_TEST_MODEL={model}"]
            docker_volumes: list[str] = []
            config_path = os.environ.get("OPENCODE_CONFIG", "")
            if config_path and Path(config_path).is_file():
                container_config = "/opt/opencode-config/host-opencode-config.json"
                docker_env.extend(["-e", f"OPENCODE_CONFIG={container_config}"])
                docker_volumes.extend(
                    ["-v", f"{config_path}:{container_config}:ro"]
                )

            host_ca = Path("/etc/ssl/certs/ca-certificates.crt")
            if host_ca.is_file():
                docker_env.extend(
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
                "-p",
                f"{self.host_port}:{self.container_port}",
                *docker_env,
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

    def ensure_up(self, *, rebuild: bool = False, interactive: bool = False) -> None:
        """Build/select/start the container for a CLI or pytest session."""

        self.check_docker()
        select_model_if_needed(interactive=interactive)
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
    actions.add_argument(
        "--models",
        action="store_true",
        help="Lista modelos disponíveis na imagem.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Docker orchestration command."""

    args = _parser().parse_args(argv)
    session = DockerSession()
    try:
        if args.models:
            session.check_docker()
            print(session.list_models(), end="")
        elif args.down:
            session.down()
        else:
            session.ensure_up(rebuild=args.rebuild, interactive=True)
    except ContainerTestError as error:
        print(f"[container-test-opencode] ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
