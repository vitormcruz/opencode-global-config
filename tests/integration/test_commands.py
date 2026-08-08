"""Behavioral tests for slash commands exposed by OpenCode."""

import pytest


pytestmark = pytest.mark.opencode


def test_get_command_returns_status_200(opencode):
    result = opencode.get_status("/command")
    assert result.returncode == 0
    assert result.stdout == "200"


def test_get_command_lists_sync_upstream_skills(opencode):
    result = opencode.get("/command")
    commands = result.json() if result.returncode == 0 else []
    names = [command.get("name") for command in commands]
    assert result.returncode == 0 and "sync-upstream-skills" in names


def test_sync_upstream_skills_has_description_field(opencode):
    result = opencode.get("/command")
    commands = result.json() if result.returncode == 0 else []
    matching = [
        command for command in commands if command.get("name") == "sync-upstream-skills"
    ]
    assert result.returncode == 0 and any("description" in command for command in matching)


def test_get_command_lists_bench_indexing(opencode):
    result = opencode.get("/command")
    commands = result.json() if result.returncode == 0 else []
    names = [command.get("name") for command in commands]
    assert result.returncode == 0 and "bench-indexing" in names


def test_bench_indexing_has_description_field(opencode):
    result = opencode.get("/command")
    commands = result.json() if result.returncode == 0 else []
    matching = [
        command for command in commands if command.get("name") == "bench-indexing"
    ]
    assert result.returncode == 0 and any("description" in command for command in matching)
