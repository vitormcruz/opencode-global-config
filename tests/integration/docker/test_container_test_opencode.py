"""Unit tests for DockerSession with the fixed local model configuration."""

from __future__ import annotations

from unittest.mock import Mock, call

import pytest

import container_test_opencode
from container_test_opencode import NETWORK_NAME, DockerSession


pytestmark = pytest.mark.unit


def test_ensure_up_starts_the_container_without_model_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = DockerSession()
    check_docker = Mock()
    image_exists = Mock(return_value=False)
    build_image = Mock()
    start_container = Mock()
    monkeypatch.setattr(session, "check_docker", check_docker)
    monkeypatch.setattr(session, "network_exists", lambda: True)
    monkeypatch.setattr(session, "network_is_internal", lambda: True)
    monkeypatch.setattr(session, "container_exists", lambda: True)
    monkeypatch.setattr(session, "image_exists", image_exists)
    monkeypatch.setattr(session, "build_image", build_image)
    monkeypatch.setattr(session, "start_container", start_container)

    session.ensure_up()

    check_docker.assert_called_once_with()
    image_exists.assert_called_once_with()
    build_image.assert_called_once_with()
    start_container.assert_called_once_with()


def test_ensure_up_reuses_a_cached_image_without_rebuilding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = DockerSession()
    session.check_docker = Mock()
    session.ensure_test_network = Mock()
    session.container_exists = Mock(return_value=False)
    session.image_exists = Mock(return_value=True)
    session.build_image = Mock()
    session.start_container = Mock()

    session.ensure_up()

    session.build_image.assert_not_called()
    session.start_container.assert_called_once_with()


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
    monkeypatch.setattr(session, "network_is_internal", lambda: True)
    monkeypatch.setattr(session, "network_gateway", lambda: "172.18.0.1")
    monkeypatch.setattr(session, "container_ip", lambda: "172.18.0.2")
    monkeypatch.setattr(session, "container_running", lambda: False)
    monkeypatch.setattr(session, "container_exists", lambda: False)
    start_proxy = Mock()
    monkeypatch.setattr(session, "start_proxy", start_proxy)
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
    assert "--add-host=host.docker.internal:172.18.0.1" in run_command
    assert "-p" not in run_command
    start_proxy.assert_called_once_with("172.18.0.2")


def test_context_container_mounts_only_the_prepared_context(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    session = DockerSession(
        repo_root=tmp_path,
        script_dir=tmp_path,
        context_dir=context_dir,
    )
    docker_calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(session, "network_exists", lambda: True)
    monkeypatch.setattr(session, "network_is_internal", lambda: True)
    monkeypatch.setattr(session, "network_gateway", lambda: "172.18.0.1")
    monkeypatch.setattr(session, "container_ip", lambda: "172.18.0.2")
    monkeypatch.setattr(session, "container_running", lambda: False)
    monkeypatch.setattr(session, "container_exists", lambda: False)
    monkeypatch.setattr(session, "start_proxy", Mock())
    monkeypatch.setattr(
        session,
        "_checked_docker",
        lambda *arguments: docker_calls.append(arguments) or "",
    )
    monkeypatch.setattr(session, "_wait_until_ready", Mock())

    session.start_container()

    command = docker_calls[0]
    assert "-v" in command
    assert f"{context_dir}:/opt/opencode-config" in command
    assert command[-7:] == (
        "/root/.opencode/bin/opencode",
        "--pure",
        "serve",
        "--hostname",
        "0.0.0.0",
        "--port",
        "4096",
    )


def test_restart_opencode_reuses_the_existing_container(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = DockerSession()
    checked_docker = Mock()
    start_proxy = Mock()
    wait_until_ready = Mock()
    monkeypatch.setattr(session, "container_running", lambda: True)
    monkeypatch.setattr(session, "stop_proxy", Mock())
    monkeypatch.setattr(session, "_checked_docker", checked_docker)
    monkeypatch.setattr(session, "container_ip", lambda: "172.18.0.2")
    monkeypatch.setattr(session, "start_proxy", start_proxy)
    monkeypatch.setattr(session, "_wait_until_ready", wait_until_ready)

    session.restart_opencode()

    checked_docker.assert_called_once_with("restart", session.container_name)
    start_proxy.assert_called_once_with("172.18.0.2")
    wait_until_ready.assert_called_once_with()


def test_start_proxy_detaches_from_the_cli_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = DockerSession()
    popen = Mock()
    monkeypatch.setattr(session, "stop_proxy", Mock())
    monkeypatch.setattr(session, "_read_proxy_pid", lambda: 12345)
    monkeypatch.setattr(session, "_pid_is_alive", lambda pid: True)
    monkeypatch.setattr(container_test_opencode.subprocess, "Popen", popen)

    session.start_proxy("172.18.0.2")

    assert popen.call_args.kwargs["start_new_session"] is True


def test_start_container_stops_proxy_when_readiness_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = DockerSession()
    stop_proxy = Mock()
    start_proxy = Mock()
    monkeypatch.setattr(session, "ensure_test_network", Mock())
    monkeypatch.setattr(session, "network_gateway", lambda: "172.18.0.1")
    monkeypatch.setattr(session, "container_exists", lambda: False)
    monkeypatch.setattr(session, "container_running", lambda: False)
    monkeypatch.setattr(session, "container_ip", lambda: "172.18.0.2")
    monkeypatch.setattr(session, "_checked_docker", Mock())
    monkeypatch.setattr(session, "stop_proxy", stop_proxy)
    monkeypatch.setattr(session, "start_proxy", start_proxy)
    monkeypatch.setattr(
        session,
        "_wait_until_ready",
        Mock(side_effect=container_test_opencode.ContainerTestError("OpenCode down")),
    )

    with pytest.raises(container_test_opencode.ContainerTestError, match="OpenCode down"):
        session.start_container()

    assert stop_proxy.call_count == 2


def test_existing_network_is_recreated_when_not_internal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = DockerSession()
    checked_docker = Mock()
    monkeypatch.setattr(session, "network_exists", lambda: True)
    monkeypatch.setattr(session, "network_is_internal", lambda: False)
    monkeypatch.setattr(session, "container_exists", lambda: False)
    monkeypatch.setattr(session, "_checked_docker", checked_docker)

    session.ensure_test_network()

    assert checked_docker.call_args_list == [
        call("network", "rm", NETWORK_NAME),
        call("network", "create", "--internal", NETWORK_NAME),
    ]


def test_container_reuses_only_matching_runtime_topology(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = DockerSession()
    monkeypatch.setattr(session, "container_uses_test_network", lambda: True)
    monkeypatch.setattr(
        session,
        "container_has_host_gateway",
        lambda gateway: gateway == "172.18.0.1",
    )

    assert session.container_is_compatible("172.18.0.1")
    assert not session.container_is_compatible("172.19.0.1")
