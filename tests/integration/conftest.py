"""Fixtures shared by non-Docker integration suites."""

from collections.abc import Iterator
from pathlib import Path
import socket

import pytest

from behavioral_helper import OpenCodeClient
from docker.container_test_opencode import ContainerTestError, DockerSession
from integration_context import prepare_test_context
from model.bonsai_server import BonsaiServer, BonsaiServerError


@pytest.fixture(scope="module")
def opencode(docker_session: DockerSession) -> OpenCodeClient:
    """Provide an OpenCode client after checking the service is available."""

    client = OpenCodeClient()
    client.require_available()
    return client


def _free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


@pytest.fixture
def isolated_opencode(
    request: pytest.FixtureRequest,
    repo_root: Path,
    isolated_opencode_session: DockerSession,
    monkeypatch: pytest.MonkeyPatch,
    local_model: str,
) -> Iterator[OpenCodeClient]:
    """Run OpenCode against only the artifacts declared by the current test."""

    marker = request.node.get_closest_marker("opencode_context")
    if marker is None:
        kind = "empty"
        name = None
    else:
        kind = marker.kwargs.get("kind")
        name = marker.kwargs.get("name")
    if not isinstance(kind, str):
        pytest.fail("O marcador opencode_context exige kind textual.")

    context_dir = prepare_test_context(
        repo_root,
        isolated_opencode_session.context_dir,
        kind=kind,
        name=name,
        model=local_model,
    )
    try:
        if isolated_opencode_session.container_running():
            isolated_opencode_session.restart_opencode()
        else:
            isolated_opencode_session.ensure_up()
        monkeypatch.setenv("OPENCODE_PORT", str(isolated_opencode_session.host_port))
        client = OpenCodeClient()
        client.require_available()
        yield client
    except ContainerTestError as error:
        pytest.fail(
            f"{error}\n"
            "Instale/inicie Docker e execute novamente os testes OpenCode.",
            pytrace=False,
        )


@pytest.fixture(scope="session")
def isolated_opencode_session(
    tmp_path_factory: pytest.TempPathFactory,
    repo_root: Path,
    bonsai_server: BonsaiServer,
) -> Iterator[DockerSession]:
    """Reuse one container while replacing its mounted context per test."""

    session = DockerSession(
        repo_root=repo_root,
        context_dir=tmp_path_factory.mktemp("opencode-context"),
        container_name="opencode-context-test",
        host_port=_free_tcp_port(),
    )
    try:
        yield session
    finally:
        session.stop_container()
        session.remove_container_if_exists()


@pytest.fixture(scope="session")
def bonsai_server(local_model: str) -> Iterator[BonsaiServer]:
    """Start or reuse the selected local model for every OpenCode test."""

    server = BonsaiServer(model=local_model)
    try:
        server.ensure_up()
    except BonsaiServerError as error:
        pytest.fail(
            f"{error}\n"
            "Confirme o acesso ao release do llama-server e execute novamente:\n"
            "  python3 tests/integration/model/bonsai_server.py --up",
            pytrace=False,
        )

    yield server


@pytest.fixture(scope="session")
def docker_session(
    bonsai_server: BonsaiServer,
    repo_root: Path,
    tmp_path_factory: pytest.TempPathFactory,
    local_model: str,
) -> Iterator[DockerSession]:
    """Start OpenCode with the selected model and stop only the container."""

    context_dir = prepare_test_context(
        repo_root,
        tmp_path_factory.mktemp("opencode-shared-context"),
        kind="empty",
        model=local_model,
    )
    session = DockerSession(repo_root=repo_root, context_dir=context_dir)
    try:
        session.ensure_up()
    except ContainerTestError as error:
        pytest.fail(
            f"{error}\n"
            "Instale/inicie Docker, suba o llama-server local e execute "
            "novamente a suite pytest de integracao.",
            pytrace=False,
        )

    try:
        yield session
    finally:
        try:
            session.stop_container()
        except ContainerTestError as error:
            pytest.fail(
                f"Falha ao encerrar a sessao Docker: {error}",
                pytrace=False,
            )


@pytest.fixture
def copilot_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate Copilot CLI configuration for the smoke tests."""

    home = tmp_path / "home"
    home.mkdir()
    (home / ".bashrc").touch()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    return home
