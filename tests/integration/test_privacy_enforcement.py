"""Runtime privacy enforcement for the OpenCode Docker integration."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Iterator

import pytest

from model.bonsai_server import get_model_spec


pytestmark = pytest.mark.opencode

CONTAINER_NAME = "opencode-config-test"
NETWORK_NAME = "opencode-test-net"
EFFECTIVE_CONFIG = "/opt/opencode-config/opencode.json"
LOCAL_BASE_URL = "http://host.docker.internal:8080/v1"
LOCAL_REQUEST_TIMEOUT_SECONDS = 600
EXTERNAL_REQUEST_TIMEOUT_SECONDS = 5


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
    timeout: float = LOCAL_REQUEST_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [docker_executable, "exec", CONTAINER_NAME, *arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
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


def test_config_enforcement_allows_only_selected_local_model(
    docker_executable: str,
    local_model: str,
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

    spec = get_model_spec(local_model)
    providers = config.get("provider") if isinstance(config, dict) else None
    if not isinstance(providers, dict):
        pytest.fail(
            "Violação de privacidade: a config efetiva não declara "
            "exatamente um provider local."
        )
    if set(providers) != {spec.provider}:
        pytest.fail(
            "Violação de privacidade: providers externos declarados na config "
            f"efetiva: {sorted(providers)}"
        )
    provider = providers[spec.provider]
    agent_config = config.get("agent") if isinstance(config, dict) else None
    options = provider.get("options") if isinstance(provider, dict) else None
    models = provider.get("models") if isinstance(provider, dict) else None
    model_config = models.get(spec.model_id) if isinstance(models, dict) else None
    plan_config = agent_config.get("plan") if isinstance(agent_config, dict) else None
    build_config = agent_config.get("build") if isinstance(agent_config, dict) else None
    if (
        not isinstance(provider, dict)
        or not isinstance(options, dict)
        or options.get("baseURL") != LOCAL_BASE_URL
        or not isinstance(models, dict)
        or set(models) != {spec.model_id}
        or not isinstance(model_config, dict)
        or model_config.get("name") != spec.display_name
        or not isinstance(agent_config, dict)
        or not isinstance(plan_config, dict)
        or plan_config.get("model") != f"{spec.provider}/{spec.model_id}"
        or not isinstance(build_config, dict)
        or build_config.get("model") != f"{spec.provider}/{spec.model_id}"
    ):
        pytest.fail(
            "Violação de privacidade: a config efetiva não fixa exclusivamente "
            f"{spec.provider}/{spec.model_id} em host.docker.internal:8080/v1."
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
        str(LOCAL_REQUEST_TIMEOUT_SECONDS),
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
    try:
        result = _exec_in_container(
            docker_executable,
            "curl",
            "--silent",
            "--show-error",
            "--noproxy",
            "*",
            "--max-time",
            str(EXTERNAL_REQUEST_TIMEOUT_SECONDS),
            "--output",
            "/dev/null",
            "--write-out",
            "%{http_code}",
            "https://example.com",
            timeout=EXTERNAL_REQUEST_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return
    http_code = result.stdout.strip()
    if result.returncode not in {6, 7, 28} or http_code not in {"", "000"}:
        pytest.fail(
            "Violação de privacidade: o container alcançou a internet. "
            "A rede opencode-test-net deve ser interna e sem proxy externo."
        )
