"""Pytest fixtures for the Docker-backed OpenCode integration session."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from container_test_opencode import ContainerTestError, DockerSession


@pytest.fixture(scope="session")
def docker_session() -> Iterator[DockerSession]:
    """Start OpenCode once and fail clearly when prerequisites are unavailable."""

    session = DockerSession()
    try:
        session.ensure_up(interactive=False)
    except ContainerTestError as error:
        pytest.fail(
            f"{error}\n"
            "Instale/inicie Docker, defina OPENCODE_TEST_MODEL e execute "
            "novamente a suíte pytest de integração.",
            pytrace=False,
        )

    try:
        yield session
    finally:
        try:
            session.stop_container()
        except ContainerTestError as error:
            pytest.fail(
                f"Falha ao encerrar a sessão Docker: {error}",
                pytrace=False,
            )
