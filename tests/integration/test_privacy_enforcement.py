"""Runtime privacy enforcement for the OpenCode Docker integration."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Iterator

import pytest


pytestmark = pytest.mark.opencode

CONTAINER_NAME = "opencode-config-test"
NETWORK_NAME = "opencode-test-net"
EFFECTIVE_CONFIG = "/opt/opencode-config/opencode.json"
LOCAL_BASE_URL = "http://host.docker.internal:8080/v1"
LOCAL_MODEL = "bonsai-local/bonsai-27b"


def _require_docker() -> str:
    executable = shutil.which("docker")
    if executable is None:
        pytest.fail(
            "Docker não encontrado no PATH. Inicie o Docker antes de executar "
            "os testes de enforcement."
        )
    return executable


@pytest.fixture(scope="module")
def docker_executable(docker_session) -> Iterator[str]:
    executable = _require_docker()
    result = subprocess.run(
        [executable, "inspect", "--format", "{{.State.Running}}", CONTAINER_NAME],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or result.stdout.strip().lower() != "true":
        detail = (result.stderr or result.stdout).strip()
        pytest.fail(
            "Container de integração não está em execução. Execute:\n"
            "  python3 tests/integration/docker/container_test_opencode.py --up"
            + (f"\nDetalhes: {detail}" if detail else "")
        )
    yield executable


def _exec_in_container(
    docker_executable: str,
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [docker_executable, "exec", CONTAINER_NAME, *arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )


def test_network_is_internal(docker_executable: str) -> None:
    result = subprocess.run(
        [
            docker_executable,
            "network",
            "inspect",
            "--format",
            "{{.Internal}}",
            NETWORK_NAME,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or result.stdout.strip().lower() != "true":
        pytest.fail(
            f"Violação de privacidade: a rede {NETWORK_NAME} não é interna.\n"
            f"{(result.stderr or result.stdout).strip()}"
        )


def test_config_enforcement_allows_only_bonsai_local(
    docker_executable: str,
) -> None:
    result = _exec_in_container(docker_executable, "cat", EFFECTIVE_CONFIG)
    if result.returncode != 0:
        pytest.fail(
            "Violação de privacidade: não foi possível ler a config efetiva "
            f"do OpenCode.\n{result.stderr.strip()}"
        )
    try:
        config = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        pytest.fail(f"Violação de privacidade: config efetiva inválida: {error}")

    providers = config.get("provider") if isinstance(config, dict) else None
    if not isinstance(providers, dict):
        pytest.fail(
            "Violação de privacidade: a config efetiva não declara "
            "exatamente o provider bonsai-local."
        )
    if set(providers) != {"bonsai-local"}:
        pytest.fail(
            "Violação de privacidade: providers externos declarados na config "
            f"efetiva: {sorted(providers)}"
        )
    provider = providers["bonsai-local"]
    agent_config = config.get("agent") if isinstance(config, dict) else None
    options = provider.get("options") if isinstance(provider, dict) else None
    models = provider.get("models") if isinstance(provider, dict) else None
    model_config = models.get("bonsai-27b") if isinstance(models, dict) else None
    plan_config = agent_config.get("plan") if isinstance(agent_config, dict) else None
    build_config = agent_config.get("build") if isinstance(agent_config, dict) else None
    if (
        not isinstance(provider, dict)
        or not isinstance(options, dict)
        or options.get("baseURL") != LOCAL_BASE_URL
        or not isinstance(models, dict)
        or set(models) != {"bonsai-27b"}
        or not isinstance(model_config, dict)
        or model_config.get("name") != "Bonsai 27B 1-bit"
        or not isinstance(agent_config, dict)
        or not isinstance(plan_config, dict)
        or plan_config.get("model") != LOCAL_MODEL
        or not isinstance(build_config, dict)
        or build_config.get("model") != LOCAL_MODEL
    ):
        pytest.fail(
            "Violação de privacidade: a config efetiva não fixa exclusivamente "
            "bonsai-local/bonsai-27b em host.docker.internal:8080/v1."
        )


def test_local_bonsai_endpoint_is_reachable(
    docker_executable: str,
) -> None:
    result = _exec_in_container(
        docker_executable,
        "curl",
        "-fsS",
        "--noproxy",
        "*",
        "--max-time",
        "10",
        "http://host.docker.internal:8080/v1/models",
    )
    if result.returncode != 0 or not result.stdout.strip():
        pytest.fail(
            "O container não alcança o llama-server local em "
            "host.docker.internal:8080.\n"
            f"{result.stderr.strip()}"
        )


def test_network_enforcement_blocks_external_access(
    docker_executable: str,
) -> None:
    result = _exec_in_container(
        docker_executable,
        "curl",
        "--silent",
        "--show-error",
        "--noproxy",
        "*",
        "--max-time",
        "5",
        "--output",
        "/dev/null",
        "--write-out",
        "%{http_code}",
        "https://example.com",
    )
    http_code = result.stdout.strip()
    if result.returncode not in {6, 7, 28} or http_code not in {"", "000"}:
        pytest.fail(
            "Violação de privacidade: o container alcançou a internet. "
            "A rede opencode-test-net deve ser interna e sem proxy externo."
        )
