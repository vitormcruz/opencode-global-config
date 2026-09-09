"""Testes do wrapper CLI opencode-adapter sobre o harness OpenCode."""

from pathlib import Path

import pytest

from fake_winreg import FakeWinreg
from opencode_config.lib import windows_env


def make_repository(root: Path) -> Path:
    repository = root / "repo"
    harness = repository / "harness-conf"
    for directory in ("agents", "commands", "skills"):
        (harness / directory).mkdir(parents=True)
    (repository / "scripts").mkdir()
    (harness / "opencode.json").write_text("{}", encoding="utf-8")
    (harness / "AGENTS.base.md").write_text(
        "# Regras Globais\n\nConteudo da base.\n",
        encoding="utf-8",
    )
    return repository


@pytest.mark.unit
def test_opencode_adapter_windows_materializes_copies(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fake_winreg: FakeWinreg,
) -> None:
    """Windows configura com copia sincronizada; recusa por SO saiu (D7)."""

    from opencode_config.adapters import opencode
    from opencode_config.lib.environment import EnvironmentKind

    repository = make_repository(tmp_path)
    home = tmp_path / "userprofile"
    home.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path / "home-venenoso"))
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setattr(
        opencode,
        "detect_environment",
        lambda: EnvironmentKind.WINDOWS,
    )
    broadcasts: list[str] = []
    monkeypatch.setattr(
        windows_env,
        "broadcast_environment_change",
        lambda: broadcasts.append("WM_SETTINGCHANGE"),
    )

    status, _output, error = opencode.run_cli(
        ["--yes", "--repo-root", str(repository)]
    )

    assert status == 0
    assert error == ""
    config_dir = home / ".config" / "opencode"
    for name in ("agents", "commands", "skills"):
        assert (config_dir / name).is_dir()
        assert not (config_dir / name).is_symlink()
    assert (config_dir / "opencode.json").is_file()
    assert (config_dir / "AGENTS.md").is_file()
    assert not (config_dir / "scripts").exists()
    assert not (home / ".bashrc").exists()
    assert fake_winreg.values["OPENCODE_ENABLE_EXA"] == "1"
    assert broadcasts == ["WM_SETTINGCHANGE"]
    assert not (tmp_path / "home-venenoso").exists()


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
def test_opencode_adapter_creates_destinations_via_cli(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
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
        lambda: EnvironmentKind.LINUX,
    )

    status, output, error = opencode.run_cli(
        ["--yes", "--repo-root", str(repository)]
    )

    assert status == 0
    assert error == ""
    assert "Pronto." in output
    config_dir = home / ".config" / "opencode"
    assert (config_dir / "agents").is_symlink()
    assert (config_dir / "AGENTS.md").is_file()


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
