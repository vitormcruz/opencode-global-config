from pathlib import Path

import pytest


def make_repository(root: Path) -> Path:
    repository = root / "repo"
    for directory in ("agents", "commands", "skills", "scripts"):
        (repository / directory).mkdir(parents=True)
    (repository / "opencode.json").write_text("{}", encoding="utf-8")
    return repository


def run_adapter(
    monkeypatch: pytest.MonkeyPatch,
    repository: Path,
    home: Path,
    arguments: list[str] | None = None,
) -> tuple[int, str, str]:
    from opencode_config.adapters import opencode
    from opencode_config.lib.environment import EnvironmentKind

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(
        opencode,
        "detect_environment",
        lambda: EnvironmentKind.LINUX,
    )
    return opencode.run_cli(
        [*(arguments or ["--yes"]), "--repo-root", str(repository)]
    )


@pytest.mark.opencode
def test_opencode_adapter_creates_canonical_symlinks(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    status, output, error = run_adapter(monkeypatch, repository, home)

    assert status == 0
    assert error == ""
    config_dir = home / ".config" / "opencode"
    for name in ("agents", "commands", "skills", "scripts", "opencode.json"):
        assert (config_dir / name).is_symlink()
        assert (config_dir / name).resolve() == (repository / name).resolve()
    assert not (config_dir / "AGENTS.md").exists()
    assert "Pronto." in output


@pytest.mark.opencode
def test_opencode_adapter_backs_up_existing_destination(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    config_dir = home / ".config" / "opencode"
    config_dir.mkdir(parents=True)
    existing = config_dir / "skills"
    existing.write_text("old configuration", encoding="utf-8")

    status, _, error = run_adapter(monkeypatch, repository, home)

    assert status == 0
    assert error == ""
    backups = list((home / ".config" / "opencode-backup").iterdir())
    assert len(backups) == 1
    assert (backups[0] / "skills").read_text(encoding="utf-8") == (
        "old configuration"
    )
    assert (config_dir / "skills").is_symlink()


@pytest.mark.opencode
def test_opencode_adapter_is_idempotent_without_spurious_backup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    first = run_adapter(monkeypatch, repository, home)
    second = run_adapter(monkeypatch, repository, home)

    assert first[0] == 0
    assert second[0] == 0
    assert not (home / ".config" / "opencode-backup").exists()
    bashrc = (home / ".bashrc").read_text(encoding="utf-8")
    assert bashrc.count("OPENCODE_ENABLE_EXA=1") == 1
    assert bashrc.count('export PATH="$HOME/.local/bin:$PATH"') == 1
    assert ("ba" + "ts").upper() not in bashrc


@pytest.mark.opencode
def test_opencode_adapter_removes_legacy_test_library_block(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    legacy_name = "ba" + "ts"
    (home / ".bashrc").write_text(
        f"# opencode-config: bibliotecas do {legacy_name.upper()}\n"
        f'export {legacy_name.upper()}_LIB_PATH="$HOME/.local/lib/{legacy_name}"\n',
        encoding="utf-8",
    )

    status, _, error = run_adapter(monkeypatch, repository, home)

    assert status == 0
    assert error == ""
    assert legacy_name.upper() not in (
        home / ".bashrc"
    ).read_text(encoding="utf-8")


@pytest.mark.unit
def test_opencode_adapter_rejects_windows(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from opencode_config.adapters import opencode
    from opencode_config.lib.environment import EnvironmentKind

    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(
        opencode,
        "detect_environment",
        lambda: EnvironmentKind.WINDOWS,
    )

    status = opencode.main(
        ["--yes", "--repo-root", str(repository)]
    )

    captured = capsys.readouterr()
    assert status != 0
    assert "Windows" in captured.err
    assert not (home / ".config" / "opencode").exists()


@pytest.mark.unit
def test_opencode_adapter_help_returns_success(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from opencode_config.adapters import opencode

    status = opencode.main(["--help"])

    captured = capsys.readouterr()
    assert status == 0
    assert "opencode-adapter" in captured.out
    assert captured.err == ""


@pytest.mark.opencode
def test_opencode_adapter_accepts_quiet(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    status, output, error = run_adapter(
        monkeypatch,
        repository,
        home,
        arguments=["--yes", "--quiet"],
    )

    assert status == 0
    assert output == ""
    assert error == ""


@pytest.mark.unit
def test_opencode_adapter_uses_skills_cli_for_upstream_sync(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.adapters import opencode
    from opencode_config.lib.process import CommandResult

    repository = make_repository(tmp_path)
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(opencode.shutil, "which", lambda _name: "opencode-skills")

    def fake_run_command(command: list[str], **_kwargs: object) -> CommandResult:
        calls.append(tuple(command))
        stdout = (
            "prompt-improver\n"
            if command[:2] == ["opencode-skills", "list"]
            else ""
        )
        return CommandResult(tuple(command), 0, stdout, "")

    monkeypatch.setattr(opencode, "run_command", fake_run_command)
    output: list[str] = []

    opencode._sync_skills(
        repository,
        output.append,
        {},
    )

    assert calls == [
        (
            "opencode-skills",
            "list",
            "--repo-root",
            str(repository),
        ),
        (
            "opencode-skills",
            "update",
            "prompt-improver",
            "--repo-root",
            str(repository),
        ),
    ]


@pytest.mark.unit
def test_project_registers_opencode_adapter_entrypoint(repo_root: Path) -> None:
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")

    assert (
        'opencode-adapter = "opencode_config.adapters.opencode:main"'
        in pyproject
    )


@pytest.mark.unit
def test_bootstrap_invokes_python_opencode_adapter(repo_root: Path) -> None:
    bootstrap = (
        repo_root / "scripts/bootstrap_repo/configurar-repo.sh"
    ).read_text(encoding="utf-8")

    assert "adapters/opencode/opencode-adapter.sh" not in bootstrap
    assert "opencode_config.bootstrap.main" in bootstrap
