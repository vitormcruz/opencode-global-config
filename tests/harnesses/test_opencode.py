"""Testes do harness OpenCode: adapter de fluxo e strategies por SO."""

import inspect
from io import StringIO
import os
from pathlib import Path

import pytest

from fake_winreg import FakeWinreg
from opencode_config.harnesses import ApplyOptions
from opencode_config.harnesses.opencode import (
    OpenCodeAdapter,
    OpenCodeEnvStrategy,
    OpenCodePosix,
    OpenCodeWindows,
)
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


def apply_adapter(
    repository: Path,
    home: Path,
    *,
    quiet: bool = False,
    strategy: OpenCodeEnvStrategy | None = None,
    timestamp: str = "fixo",
) -> tuple[str, str]:
    output = StringIO()
    error = StringIO()
    adapter = OpenCodeAdapter(strategy or OpenCodePosix())
    adapter.apply(
        repository,
        ApplyOptions(
            home=home,
            assume_yes=True,
            quiet=quiet,
            timestamp=timestamp,
            output=output,
            error=error,
        ),
    )
    return output.getvalue(), error.getvalue()


@pytest.mark.unit
def test_opencode_creates_canonical_symlinks(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    output, _ = apply_adapter(repository, home)

    config_dir = home / ".config" / "opencode"
    for name in ("agents", "commands", "skills", "opencode.json"):
        assert (config_dir / name).is_symlink()
        assert (config_dir / name).resolve() == (
            repository / "harness-conf" / name
        ).resolve()
    assert (config_dir / "scripts").is_symlink()
    assert (config_dir / "scripts").resolve() == (
        repository / "scripts"
    ).resolve()
    agents_md = config_dir / "AGENTS.md"
    assert agents_md.is_file()
    assert not agents_md.is_symlink()
    assert (
        agents_md.read_text(encoding="utf-8") == "# Regras Globais\n\n"
        "Conteudo da base.\n"
    )
    assert "Pronto." in output


@pytest.mark.unit
def test_opencode_agents_md_preserves_managed_blocks(
    tmp_path: Path,
) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    config_dir = home / ".config" / "opencode"
    config_dir.mkdir(parents=True)
    managed_block = (
        "<!-- codebase-memory-mcp:start -->\n"
        "conteudo gerenciado pela ferramenta\n"
        "<!-- codebase-memory-mcp:end -->"
    )
    (config_dir / "AGENTS.md").write_text(
        "BASE ANTIGA\n\n" + managed_block + "\n",
        encoding="utf-8",
    )

    apply_adapter(repository, home)

    content = (config_dir / "AGENTS.md").read_text(encoding="utf-8")
    assert content.startswith("# Regras Globais\n\nConteudo da base.\n")
    assert "BASE ANTIGA" not in content
    assert managed_block in content
    backups = list((home / ".config" / "opencode-backup").iterdir())
    assert len(backups) == 1
    assert "BASE ANTIGA" in (backups[0] / "AGENTS.md").read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_opencode_agents_md_is_idempotent(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    apply_adapter(repository, home, timestamp="primeiro")
    apply_adapter(repository, home, timestamp="segundo")

    backup_root = home / ".config" / "opencode-backup"
    assert not backup_root.exists() or not any(backup_root.iterdir())


@pytest.mark.unit
def test_opencode_backs_up_existing_destination(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    config_dir = home / ".config" / "opencode"
    config_dir.mkdir(parents=True)
    existing = config_dir / "skills"
    existing.write_text("old configuration", encoding="utf-8")

    apply_adapter(repository, home)

    backups = list((home / ".config" / "opencode-backup").iterdir())
    assert len(backups) == 1
    assert (backups[0] / "skills").read_text(encoding="utf-8") == (
        "old configuration"
    )
    assert (config_dir / "skills").is_symlink()


@pytest.mark.unit
def test_opencode_is_idempotent_without_spurious_backup(
    tmp_path: Path,
) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    apply_adapter(repository, home, timestamp="primeiro")
    apply_adapter(repository, home, timestamp="segundo")

    assert not (home / ".config" / "opencode-backup").exists()
    bashrc = (home / ".bashrc").read_text(encoding="utf-8")
    assert bashrc.count("OPENCODE_ENABLE_EXA=1") == 1
    assert bashrc.count('export PATH="$HOME/.local/bin:$PATH"') == 1
    assert "LIB_PATH" not in bashrc


@pytest.mark.unit
def test_opencode_does_not_mutate_repository(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    marker = repository / "mutation.txt"
    fake_skills_cli = fake_bin / "opencode-skills"
    fake_skills_cli.write_text(
        "#!/usr/bin/env python3\n"
        "import os\n"
        "from pathlib import Path\n"
        "import sys\n"
        "if sys.argv[1] == 'list':\n"
        "    print('prompt-improver')\n"
        "elif sys.argv[1] == 'update':\n"
        "    Path(os.environ['MUTATION_MARKER']).write_text('mutated')\n",
        encoding="utf-8",
    )
    fake_skills_cli.chmod(0o755)

    monkeypatch.setenv(
        "PATH",
        f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
    )
    monkeypatch.setenv("MUTATION_MARKER", str(marker))

    apply_adapter(repository, home)

    assert not marker.exists()


@pytest.mark.unit
def test_opencode_removes_legacy_test_library_block(
    tmp_path: Path,
) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    legacy_name = "legacytest"
    (home / ".bashrc").write_text(
        f"# opencode-config: bibliotecas do {legacy_name.upper()}\n"
        f'export {legacy_name.upper()}_LIB_PATH="$HOME/.local/lib/{legacy_name}"\n',
        encoding="utf-8",
    )

    apply_adapter(repository, home)

    assert legacy_name.upper() not in (
        home / ".bashrc"
    ).read_text(encoding="utf-8")


@pytest.mark.unit
def test_opencode_removes_legacy_local_binary_comment(
    tmp_path: Path,
) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    (home / ".bashrc").write_text(
        "# opencode-config: binarios locais (legacy-tool etc.)\n"
        'export PATH="$HOME/.local/bin:$PATH"\n',
        encoding="utf-8",
    )

    apply_adapter(repository, home)

    assert "legacy-tool" not in (
        home / ".bashrc"
    ).read_text(encoding="utf-8")


@pytest.mark.unit
def test_opencode_accepts_quiet(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    output, _ = apply_adapter(repository, home, quiet=True)

    assert output == ""


@pytest.mark.unit
def test_opencode_adapter_is_blind_to_operating_system() -> None:
    """Fluxo do adapter nao decide por ambiente nem escolhe strategy (D7)."""

    apply_source = inspect.getsource(OpenCodeAdapter.apply)
    assert "EnvironmentKind" not in apply_source
    assert "detect_environment" not in apply_source
    assert "WINDOWS" not in apply_source

    parameters = inspect.signature(OpenCodeAdapter.__init__).parameters
    assert "strategy" in parameters


@pytest.mark.unit
def test_opencode_installed_uses_path_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from opencode_config.lib.environment import EnvironmentKind

    adapter = OpenCodeAdapter(OpenCodePosix())
    monkeypatch.setattr(
        "opencode_config.harnesses.opencode.shutil.which",
        lambda command, **_kwargs: f"/usr/bin/{command}",
    )
    assert adapter.installed(EnvironmentKind.LINUX) is True

    monkeypatch.setattr(
        "opencode_config.harnesses.opencode.shutil.which",
        lambda _command, **_kwargs: None,
    )
    assert adapter.installed(EnvironmentKind.LINUX) is False


def intercept_broadcast(
    monkeypatch: pytest.MonkeyPatch,
) -> list[str]:
    """Desarma o broadcast real e registra as chamadas."""

    broadcasts: list[str] = []
    monkeypatch.setattr(
        windows_env,
        "broadcast_environment_change",
        lambda: broadcasts.append("WM_SETTINGCHANGE"),
    )
    return broadcasts


@pytest.mark.unit
def test_opencode_windows_materializes_copies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_winreg: FakeWinreg,
) -> None:
    repository = make_repository(tmp_path)
    (repository / "harness-conf" / "agents" / "worker.md").write_text(
        "agente", encoding="utf-8"
    )
    home = tmp_path / "home"
    home.mkdir()
    broadcasts = intercept_broadcast(monkeypatch)

    output, _ = apply_adapter(repository, home, strategy=OpenCodeWindows())

    config_dir = home / ".config" / "opencode"
    for name in ("agents", "commands", "skills"):
        destination = config_dir / name
        assert destination.is_dir()
        assert not destination.is_symlink()
    assert (config_dir / "agents" / "worker.md").read_text(
        encoding="utf-8"
    ) == "agente"
    assert (config_dir / "opencode.json").is_file()
    assert not (config_dir / "opencode.json").is_symlink()
    assert not (config_dir / "scripts").exists()
    assert (config_dir / "AGENTS.md").is_file()
    assert not (home / ".bashrc").exists()
    assert fake_winreg.values["OPENCODE_ENABLE_EXA"] == "1"
    assert broadcasts == ["WM_SETTINGCHANGE"]
    assert "Pronto." in output


@pytest.mark.unit
def test_opencode_windows_copy_removes_stale_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_winreg: FakeWinreg,
) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    config_dir = home / ".config" / "opencode"
    stale = config_dir / "skills" / "velha"
    stale.parent.mkdir(parents=True)
    stale.write_text("sobrou de sync anterior", encoding="utf-8")
    intercept_broadcast(monkeypatch)

    apply_adapter(repository, home, strategy=OpenCodeWindows())

    assert not stale.exists()
    assert (config_dir / "skills").is_dir()


@pytest.mark.unit
def test_opencode_windows_is_idempotent_without_backup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_winreg: FakeWinreg,
) -> None:
    repository = make_repository(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    intercept_broadcast(monkeypatch)

    apply_adapter(
        repository, home, strategy=OpenCodeWindows(), timestamp="primeiro"
    )
    apply_adapter(
        repository, home, strategy=OpenCodeWindows(), timestamp="segundo"
    )

    backup_root = home / ".config" / "opencode-backup"
    assert not backup_root.exists()
    assert fake_winreg.set_calls == [("OPENCODE_ENABLE_EXA", "1")]


@pytest.mark.unit
def test_opencode_windows_env_status_reports_missing_variable(
    fake_winreg: FakeWinreg,
    tmp_path: Path,
) -> None:
    lines = OpenCodeWindows().env_status(tmp_path, {})

    assert lines == [r"ENV   HKCU\Environment << OPENCODE_ENABLE_EXA=1"]


@pytest.mark.unit
def test_opencode_windows_env_status_reports_persisted_variable(
    fake_winreg: FakeWinreg,
    tmp_path: Path,
) -> None:
    fake_winreg.values["OPENCODE_ENABLE_EXA"] = "1"

    lines = OpenCodeWindows().env_status(tmp_path, {})

    assert lines == [r"OK    HKCU\Environment OPENCODE_ENABLE_EXA=1"]
