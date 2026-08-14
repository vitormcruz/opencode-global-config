"""Fixtures shared by non-Docker integration suites."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from behavioral_helper import OpenCodeClient
from docker.container_test_opencode import ContainerTestError, DockerSession
from model.bonsai_server import BonsaiServer, BonsaiServerError


@pytest.fixture(scope="module")
def opencode(docker_session: DockerSession) -> OpenCodeClient:
    """Provide an OpenCode client after checking the service is available."""

    client = OpenCodeClient()
    client.require_available()
    return client


@pytest.fixture(scope="session")
def bonsai_server() -> Iterator[BonsaiServer]:
    """Start or reuse Bonsai once for every OpenCode integration test."""

    server = BonsaiServer()
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
def docker_session(bonsai_server: BonsaiServer) -> Iterator[DockerSession]:
    """Start OpenCode after Bonsai is available and stop only the container."""

    session = DockerSession()
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
