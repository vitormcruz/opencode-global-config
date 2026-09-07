"""Unit tests for the per-test OpenCode context builder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from integration_context import prepare_test_context


pytestmark = pytest.mark.unit


def _repository(root: Path) -> Path:
    repository = root / "repository"
    (repository / "tests" / "integration" / "config").mkdir(parents=True)
    (repository / "harness-conf" / "agents").mkdir(parents=True)
    (repository / "harness-conf" / "commands").mkdir(parents=True)
    (repository / "harness-conf" / "skills" / "target-skill").mkdir(parents=True)
    (repository / "harness-conf" / "skills" / "other-skill").mkdir(parents=True)
    (repository / "harness-conf/agents/target-agent.md").write_text(
        "target", encoding="utf-8"
    )
    (repository / "harness-conf/agents/other-agent.md").write_text(
        "other", encoding="utf-8"
    )
    (repository / "harness-conf" / "commands" / "target-command.md").write_text(
        "target", encoding="utf-8"
    )
    (repository / "harness-conf" / "commands" / "other-command.md").write_text(
        "other", encoding="utf-8"
    )
    (repository / "harness-conf" / "skills" / "target-skill" / "SKILL.md").write_text(
        "target", encoding="utf-8"
    )
    (repository / "harness-conf" / "skills" / "other-skill" / "SKILL.md").write_text(
        "other", encoding="utf-8"
    )
    (repository / "tests" / "integration" / "config" / "opencode.test.json").write_text(
        json.dumps(
            {
                "plugin": ["external-plugin"],
                "provider": {"qwen-local": {"models": {"qwen3-0.6b": {}}}},
                "agent": {"build": {"model": "qwen-local/qwen3-0.6b"}},
            }
        ),
        encoding="utf-8",
    )
    return repository


def test_prepare_skill_context_copies_only_the_requested_skill(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)

    context = prepare_test_context(
        repository,
        tmp_path / "context",
        kind="skill",
        name="target-skill",
    )

    assert (context / "skills" / "target-skill" / "SKILL.md").is_file()
    assert not (context / "skills" / "other-skill").exists()
    assert not (context / "agents").exists()
    assert not (context / "commands").exists()

    config = json.loads((context / "opencode.json").read_text(encoding="utf-8"))
    assert config["plugin"] == []
    assert config["permission"]["skill"] == {
        "*": "deny",
        "target-skill": "allow",
    }
    assert config["agent"]["build"]["tools"] == {"*": False, "skill": True}


@pytest.mark.parametrize(
    ("kind", "name", "directory"),
    [
        ("agent", "target-agent", "agents"),
        ("command", "target-command", "commands"),
    ],
)
def test_prepare_context_copies_only_the_requested_artifact(
    tmp_path: Path,
    kind: str,
    name: str,
    directory: str,
) -> None:
    repository = _repository(tmp_path)

    context = prepare_test_context(
        repository,
        tmp_path / f"{kind}-context",
        kind=kind,
        name=name,
    )

    assert (context / directory / f"{name}.md").is_file()
    assert len(list((context / directory).iterdir())) == 1
    assert not (context / "skills").exists()


def test_prepare_empty_context_contains_no_repository_artifacts(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)

    context = prepare_test_context(
        repository,
        tmp_path / "empty-context",
        kind="empty",
    )

    assert (context / "opencode.json").is_file()
    assert not (context / "agents").exists()
    assert not (context / "commands").exists()
    assert not (context / "skills").exists()


def test_prepare_context_fixes_the_qwen_provider(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)

    context = prepare_test_context(
        repository,
        tmp_path / "qwen-context",
        kind="empty",
    )

    config = json.loads((context / "opencode.json").read_text(encoding="utf-8"))
    assert set(config["provider"]) == {"qwen-local"}
    assert config["provider"]["qwen-local"]["models"]["qwen3-0.6b"] == {
        "name": "Qwen3 0.6B Q8_0",
        "options": {"chat_template_kwargs": {"enable_thinking": False}},
    }
    assert config["agent"]["plan"]["model"] == "qwen-local/qwen3-0.6b"
    assert config["agent"]["build"]["model"] == "qwen-local/qwen3-0.6b"


def test_prepare_context_replaces_artifacts_in_a_reused_directory(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    context = tmp_path / "reused-context"

    prepare_test_context(
        repository,
        context,
        kind="skill",
        name="target-skill",
    )
    prepare_test_context(
        repository,
        context,
        kind="agent",
        name="target-agent",
    )

    assert (context / "agents" / "target-agent.md").is_file()
    assert not (context / "skills").exists()
