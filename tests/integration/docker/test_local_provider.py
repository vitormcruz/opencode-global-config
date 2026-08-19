"""Unit tests for the fixed local Qwen OpenCode provider."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

import entrypoint
from container_test_opencode import DockerSession


pytestmark = pytest.mark.unit


CONFIG_FILE = (
    Path(__file__).resolve().parents[1] / "config" / "opencode.test.json"
)


def _read_test_config() -> dict:
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def test_test_config_declares_only_the_local_qwen_provider() -> None:
    config = _read_test_config()

    assert set(config["provider"]) == {"qwen-local"}
    provider = config["provider"]["qwen-local"]
    assert provider["npm"] == "@ai-sdk/openai-compatible"
    assert provider["options"]["baseURL"] == "http://host.docker.internal:8080/v1"
    assert provider["models"]["qwen3-0.6b"]["name"] == "Qwen3 0.6B Q8_0"
    assert provider["models"]["qwen3-0.6b"]["options"] == {
        "chat_template_kwargs": {"enable_thinking": False}
    }
    assert config["agent"]["plan"]["model"] == "qwen-local/qwen3-0.6b"
    assert config["agent"]["build"]["model"] == "qwen-local/qwen3-0.6b"


def test_start_container_uses_host_gateway_without_model_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = DockerSession(repo_root=tmp_path, script_dir=tmp_path)
    docker_calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(session, "network_exists", lambda: True)
    monkeypatch.setattr(session, "network_is_internal", lambda: True)
    monkeypatch.setattr(session, "network_gateway", lambda: "172.18.0.1")
    monkeypatch.setattr(session, "container_ip", lambda: "172.18.0.2")
    overlay_variable = "OPENCODE" + "_CONFIG"
    monkeypatch.setenv(overlay_variable, str(tmp_path / "host.json"))
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

    assert len(docker_calls) == 1
    command = docker_calls[0]
    assert command[command.index("--network") + 1] == "opencode-test-net"
    assert "--add-host=host.docker.internal:172.18.0.1" in command
    assert "-p" not in command
    assert overlay_variable not in command


def test_entrypoint_ignores_host_config_overlay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    overlay_variable = "OPENCODE" + "_CONFIG"
    monkeypatch.setenv(overlay_variable, "/tmp/host-opencode.json")
    exec_arguments: list[tuple[str, list[str]]] = []
    monkeypatch.setattr(
        entrypoint.os,
        "execv",
        lambda path, arguments: exec_arguments.append((path, arguments)),
    )

    entrypoint.main()

    assert exec_arguments == [
        (
            entrypoint.OPENCODE_BINARY,
            [
                entrypoint.OPENCODE_BINARY,
                "--pure",
                "serve",
                "--hostname",
                "0.0.0.0",
                "--port",
                "4096",
            ],
        )
    ]
