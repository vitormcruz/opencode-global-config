"""Unit tests for the fixed local Bonsai OpenCode provider."""

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


def test_test_config_declares_only_the_local_bonsai_provider() -> None:
    config = _read_test_config()

    assert set(config["provider"]) == {"bonsai-local"}
    provider = config["provider"]["bonsai-local"]
    assert provider["npm"] == "@ai-sdk/openai-compatible"
    assert provider["options"]["baseURL"] == "http://host.docker.internal:8080/v1"
    assert provider["models"]["bonsai-27b"]["name"] == "Bonsai 27B 1-bit"
    assert config["agent"]["plan"]["model"] == "bonsai-local/bonsai-27b"
    assert config["agent"]["build"]["model"] == "bonsai-local/bonsai-27b"


def test_start_container_uses_host_gateway_without_model_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = DockerSession(repo_root=tmp_path, script_dir=tmp_path)
    docker_calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(session, "network_exists", lambda: True)
    monkeypatch.delenv("OPENCODE_CONFIG", raising=False)
    monkeypatch.setattr(session, "container_running", lambda: False)
    monkeypatch.setattr(session, "container_exists", lambda: False)
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
    assert "--add-host=host.docker.internal:host-gateway" in command
    assert not any(argument.startswith("OPENCODE_") for argument in command)


def test_entrypoint_keeps_the_fixed_model_configuration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "opencode.json"
    config_path.write_text(
        json.dumps(
            {
                "agent": {
                    "plan": {"model": "bonsai-local/bonsai-27b"},
                    "build": {"model": "bonsai-local/bonsai-27b"},
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(entrypoint, "CONFIG_FILE", config_path)
    monkeypatch.delenv("OPENCODE_CONFIG", raising=False)

    entrypoint.configure()

    result = json.loads(config_path.read_text(encoding="utf-8"))
    assert result["agent"]["plan"]["model"] == "bonsai-local/bonsai-27b"
