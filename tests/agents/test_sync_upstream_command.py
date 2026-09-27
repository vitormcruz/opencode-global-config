from pathlib import Path

import pytest


@pytest.mark.unit
def test_sync_upstream_command_detects_and_waits_for_human_decision(
    repo_root: Path,
) -> None:
    command = (
        repo_root / "harness-conf" / "commands" / "sync-upstream-skills.md"
    ).read_text(encoding="utf-8")
    normalized_command = " ".join(command.split())

    detect_position = normalized_command.index("opencode-skills detect")
    sync_position = normalized_command.index("opencode-skills sync")

    assert detect_position < sync_position
    assert "NÃO CONFIÁVEL" in normalized_command
    assert "writing-for-agents" in normalized_command
    assert "aprovação explícita do humano" in normalized_command
    assert "recusa sem congelamento mantém o SHA anterior" in normalized_command
    assert "opencode-skills update" not in normalized_command
