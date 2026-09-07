from io import StringIO
from pathlib import Path

import pytest

from opencode_config.cli import skills_sync


def write_upstream_metadata(
    repo: Path,
    skill: str,
    *,
    update_command: str | None = "opencode-skills sync prompt-improver",
    check_command: str | None = "opencode-skills sync prompt-improver --check-only",
) -> Path:
    skill_dir = repo / "harness-conf" / "skills" / skill
    skill_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Metadados do Upstream",
        "",
        "## Como atualizar",
        "",
    ]
    if update_command is not None:
        lines.append(f"    {update_command}")
    if check_command is not None:
        lines.extend(["", f"    {check_command}"])
    upstream = skill_dir / "UPSTREAM.md"
    upstream.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return upstream


@pytest.mark.unit
def test_list_help_returns_success(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        skills_sync.main(["list", "--help"])

    assert raised.value.code == 0
    assert "lista skills" in capsys.readouterr().out


@pytest.mark.unit
def test_list_invalid_option_returns_exit_two() -> None:
    with pytest.raises(SystemExit) as raised:
        skills_sync.main(["list", "--invalid"])

    assert raised.value.code == 2


@pytest.mark.unit
def test_list_includes_prompt_improver(repo_root: Path) -> None:
    assert "prompt-improver" in skills_sync.list_updatable(repo_root)


@pytest.mark.unit
def test_list_includes_addyosmani_skills(repo_root: Path) -> None:
    listed = skills_sync.list_updatable(repo_root)

    for skill_name in skills_sync.ADDYOSMANI_SKILLS:
        assert skill_name in listed


@pytest.mark.unit
def test_list_includes_accessibility_audit(repo_root: Path) -> None:
    assert "accessibility-audit" in skills_sync.list_updatable(repo_root)


@pytest.mark.unit
def test_list_excludes_skills_without_upstream_metadata(repo_root: Path) -> None:
    listed = skills_sync.list_updatable(repo_root)

    assert "doc-extract" not in listed
    assert "md-export" not in listed


@pytest.mark.unit
def test_list_count_matches_upstream_metadata_files(repo_root: Path) -> None:
    expected = len(
        list((repo_root / "harness-conf" / "skills").glob("*/UPSTREAM.md"))
    )

    assert len(skills_sync.list_updatable(repo_root)) == expected


@pytest.mark.unit
def test_list_output_is_alphabetical(repo_root: Path) -> None:
    listed = skills_sync.list_updatable(repo_root)

    assert listed
    assert listed == sorted(listed)


@pytest.mark.unit
def test_list_outputs_only_upstream_skills_in_alphabetical_order(
    tmp_path: Path,
) -> None:
    for skill in ("prompt-improver", "accessibility-audit", "test-driven-development"):
        write_upstream_metadata(tmp_path, skill)
    (tmp_path / "harness-conf/skills/doc-extract").mkdir(parents=True)

    output = StringIO()
    status = skills_sync.run(
        ["list", "--repo-root", str(tmp_path)],
        output=output,
        error=StringIO(),
    )

    assert status == 0
    assert output.getvalue().splitlines() == [
        "accessibility-audit",
        "prompt-improver",
        "test-driven-development",
    ]
    assert "doc-extract" not in output.getvalue()


@pytest.mark.unit
def test_update_help_returns_success(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        skills_sync.main(["update", "--help"])

    assert raised.value.code == 0
    assert "atualiza uma skill" in capsys.readouterr().out


@pytest.mark.unit
def test_update_help_mentions_update_flow(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        skills_sync.main(["update", "--help"])

    assert "UPSTREAM.md" in capsys.readouterr().out


@pytest.mark.unit
def test_update_without_skill_returns_exit_two() -> None:
    with pytest.raises(SystemExit) as raised:
        skills_sync.main(["update"])

    assert raised.value.code == 2


@pytest.mark.unit
def test_update_missing_upstream_reports_no_clear_update_flow(
    tmp_path: Path,
) -> None:
    result = skills_sync.update_skill(tmp_path, "skill-que-nao-existe-xyz")

    assert result.status == "no-clear-update-flow"
    assert "skill-que-nao-existe-xyz" in result.output


@pytest.mark.unit
def test_update_missing_upstream_reports_skill_name(tmp_path: Path) -> None:
    result = skills_sync.update_skill(tmp_path, "skill-que-nao-existe-xyz")

    assert "skill: skill-que-nao-existe-xyz" in result.output


@pytest.mark.unit
def test_update_without_documented_command_reports_no_clear_update_flow(
    tmp_path: Path,
) -> None:
    upstream = write_upstream_metadata(
        tmp_path,
        "prompt-improver",
        update_command=None,
        check_command="opencode-skills sync prompt-improver --check-only",
    )

    result = skills_sync.update_skill(tmp_path, "prompt-improver")

    assert result.status == "no-clear-update-flow"
    assert upstream.read_text(encoding="utf-8").endswith(
        "opencode-skills sync prompt-improver --check-only\n"
    )


@pytest.mark.unit
def test_update_with_multiple_commands_reports_ambiguous_flow(tmp_path: Path) -> None:
    skill_dir = tmp_path / "harness-conf/skills/prompt-improver"
    skill_dir.mkdir(parents=True)
    (skill_dir / "UPSTREAM.md").write_text(
        "\n".join(
            [
                "## Como atualizar",
                "",
                "    opencode-skills sync prompt-improver",
                "    opencode-skills sync prompt-improver --yes",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = skills_sync.update_skill(tmp_path, "prompt-improver")

    assert result.status == "ambiguous-update-flow"
    assert "opencode-skills sync prompt-improver" in result.output


@pytest.mark.unit
def test_update_dry_run_reports_dry_run_and_preserves_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    upstream = write_upstream_metadata(tmp_path, "prompt-improver")
    before = upstream.read_bytes()
    monkeypatch.setattr(
        skills_sync,
        "_run_documented_command",
        lambda _command, _repo: (0, "Atualizacao disponivel"),
    )

    result = skills_sync.update_skill(
        tmp_path,
        "prompt-improver",
        dry_run=True,
    )

    assert result.status == "dry-run"
    assert "skill: prompt-improver" in result.output
    assert upstream.read_bytes() == before


@pytest.mark.unit
def test_update_already_up_to_date_reports_status(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    write_upstream_metadata(tmp_path, "prompt-improver")
    monkeypatch.setattr(
        skills_sync,
        "_run_documented_command",
        lambda _command, _repo: (0, "Ja esta atualizado"),
    )

    result = skills_sync.update_skill(tmp_path, "prompt-improver")

    assert result.status == "already-up-to-date"


@pytest.mark.unit
def test_update_dry_run_stays_non_destructive_when_already_up_to_date(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    upstream = write_upstream_metadata(tmp_path, "prompt-improver")
    before = upstream.read_bytes()
    monkeypatch.setattr(
        skills_sync,
        "_run_documented_command",
        lambda _command, _repo: (0, "Ja esta atualizado"),
    )

    result = skills_sync.update_skill(
        tmp_path,
        "prompt-improver",
        dry_run=True,
    )

    assert result.status == "dry-run"
    assert upstream.read_bytes() == before


@pytest.mark.unit
def test_update_requires_non_interactive_mode_when_yes_is_unsupported(
    tmp_path: Path,
) -> None:
    write_upstream_metadata(
        tmp_path,
        "prompt-improver",
        update_command="python scripts/update.py",
        check_command=None,
    )

    result = skills_sync.update_skill(tmp_path, "prompt-improver")

    assert result.status == "non-interactive-mode-not-found"


@pytest.mark.unit
def test_update_appends_yes_to_native_command(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    write_upstream_metadata(tmp_path, "prompt-improver", check_command=None)
    commands: list[str] = []

    def fake_runner(command: str, _repo: Path) -> tuple[int, str]:
        commands.append(command)
        return 0, "updated"

    monkeypatch.setattr(skills_sync, "_run_documented_command", fake_runner)

    result = skills_sync.update_skill(tmp_path, "prompt-improver")

    assert result.status == "success"
    assert commands == ["opencode-skills sync prompt-improver --yes"]


@pytest.mark.unit
def test_update_success_reports_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    write_upstream_metadata(tmp_path, "prompt-improver", check_command=None)
    monkeypatch.setattr(
        skills_sync,
        "_run_documented_command",
        lambda _command, _repo: (0, "updated"),
    )

    result = skills_sync.update_skill(tmp_path, "prompt-improver")

    assert result.status == "success"
    assert "updated" in result.output


@pytest.mark.unit
def test_update_error_restores_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    upstream = write_upstream_metadata(tmp_path, "prompt-improver", check_command=None)
    before = upstream.read_bytes()

    def failing_runner(_command: str, _repo: Path) -> tuple[int, str]:
        upstream.write_text("changed by failed command\n", encoding="utf-8")
        return 1, "failure"

    monkeypatch.setattr(skills_sync, "_run_documented_command", failing_runner)

    result = skills_sync.update_skill(tmp_path, "prompt-improver")

    assert result.status == "error"
    assert upstream.read_bytes() == before
    assert "failure" in result.output
