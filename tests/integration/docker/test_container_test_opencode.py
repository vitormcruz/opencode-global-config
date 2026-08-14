"""Unit tests for DockerSession with the fixed local model configuration."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

import container_test_opencode
from container_test_opencode import NETWORK_NAME, DockerSession


pytestmark = pytest.mark.unit


def test_ensure_up_starts_the_container_without_model_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = DockerSession()
    check_docker = Mock()
    start_container = Mock()
    monkeypatch.setattr(session, "check_docker", check_docker)
    monkeypatch.setattr(session, "network_exists", lambda: True)
    monkeypatch.setattr(session, "container_exists", lambda: True)
    monkeypatch.setattr(session, "start_container", start_container)

    session.ensure_up()

    check_docker.assert_called_once_with()
    start_container.assert_called_once_with()


def test_cli_has_no_model_listing_action() -> None:
    with pytest.raises(SystemExit):
        container_test_opencode._parser().parse_args(["--models"])


def test_ensure_test_network_creates_an_internal_network_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = DockerSession()
    checked_docker = Mock()
    monkeypatch.setattr(session, "network_exists", lambda: False)
    monkeypatch.setattr(session, "_checked_docker", checked_docker)

    session.ensure_test_network()

    checked_docker.assert_called_once_with(
        "network",
        "create",
        "--internal",
        NETWORK_NAME,
    )


def test_start_container_uses_only_the_internal_test_network(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = DockerSession(repo_root=tmp_path, script_dir=tmp_path)
    docker_calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(session, "network_exists", lambda: True)
    monkeypatch.setattr(session, "container_running", lambda: False)
    monkeypatch.setattr(session, "container_exists", lambda: False)
    monkeypatch.setattr(
        session,
        "_checked_docker",
        lambda *arguments: docker_calls.append(arguments) or "",
    )
    monkeypatch.setattr(session, "_wait_until_ready", Mock())

    session.start_container()

    run_command = docker_calls[0]
    assert "--network" in run_command
    assert run_command[run_command.index("--network") + 1] == NETWORK_NAME
    assert "--add-host=host.docker.internal:host-gateway" in run_command
