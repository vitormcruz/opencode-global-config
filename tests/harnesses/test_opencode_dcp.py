"""Testes do destino dcp.jsonc do harness OpenCode.

Cobre a sincronização do config canônico do plugin DCP
(`harness-conf/dcp.jsonc`) para o user-space: symlink POSIX (strategy
OpenCodePosix) e cópia sincronizada Windows com backup (strategy
OpenCodeWindows). Fixa também, no artefato canônico, a configuração
decidida para o plugin (incluindo `autoUpdate: false`) e a spec
pinada no array `plugin` do `opencode.json`.
"""

import json
from io import StringIO
from pathlib import Path

import pytest

from fake_winreg import FakeWinreg
from platform_requirements import requires_symlink
from opencode_config.harnesses import ApplyOptions
from opencode_config.harnesses.opencode import (
    OpenCodeAdapter,
    OpenCodePosix,
    OpenCodeWindows,
)
from opencode_config.lib import windows_env


def make_dcp_repository(root: Path) -> Path:
    repository = root / "repo"
    harness = repository / "harness-conf"
    for directory in ("agents", "commands", "skills"):
        (harness / directory).mkdir(parents=True)
    (repository / "scripts").mkdir()
    (harness / "opencode.json").write_text("{}", encoding="utf-8")
    (harness / "dcp.jsonc").write_text("{}", encoding="utf-8")
    (harness / "AGENTS.base.md").write_text(
        "# Regras Globais\n\nConteudo da base.\n",
        encoding="utf-8",
    )
    return repository


def apply_adapter(
    repository: Path,
    home: Path,
    strategy: OpenCodePosix | OpenCodeWindows,
    timestamp: str = "fixo",
) -> None:
    output = StringIO()
    error = StringIO()
    adapter = OpenCodeAdapter(strategy)
    adapter.apply(
        repository,
        ApplyOptions(
            home=home,
            assume_yes=True,
            timestamp=timestamp,
            output=output,
            error=error,
        ),
    )


def intercept_broadcast(monkeypatch: pytest.MonkeyPatch) -> None:
    """Desarma o broadcast real do Windows durante o teste."""

    monkeypatch.setattr(
        windows_env,
        "broadcast_environment_change",
        lambda: None,
    )


@pytest.mark.unit
def test_canonical_dcp_jsonc_pins_decided_configuration(
    repo_root: Path,
) -> None:
    config = json.loads(
        (repo_root / "harness-conf" / "dcp.jsonc").read_text(
            encoding="utf-8"
        )
    )

    compress = config["compress"]
    assert compress["permission"] == "allow"
    assert compress["mode"] == "range"
    # Compactacao por decisao do agente (design 2026-09-30): sem limite
    # fixo operante; os limites existem so como valores inertes (nunca
    # disparam nudge) e o modo manual fica DESLIGADO, pois ele bloqueia
    # a chamada da tool pelo proprio agente (evidencia da validacao
    # funcional no plugin 3.1.15, ver plano).
    assert compress["maxContextLimit"] == 999999999
    assert compress["minContextLimit"] == 999999999
    assert config.get("manualMode", {}).get("enabled", False) is False
    assert compress["protectUserMessages"] is False
    assert "protectedTools" not in compress
    assert "protectedFilePatterns" not in compress
    assert config["experimental"]["allowSubAgents"] is True
    assert config["autoUpdate"] is False


@pytest.mark.unit
def test_canonical_opencode_json_declares_pinned_dcp_plugin(
    repo_root: Path,
) -> None:
    config = json.loads(
        (repo_root / "harness-conf" / "opencode.json").read_text(
            encoding="utf-8"
        )
    )

    assert "@tarquinen/opencode-dcp@3.1.15" in config["plugin"]


@pytest.mark.integration
@requires_symlink
def test_opencode_posix_materializes_dcp_jsonc_symlink(
    tmp_path: Path,
) -> None:
    repository = make_dcp_repository(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    apply_adapter(repository, home, OpenCodePosix())

    link = home / ".config" / "opencode" / "dcp.jsonc"
    assert link.is_symlink()
    assert link.resolve() == (
        repository / "harness-conf" / "dcp.jsonc"
    ).resolve()


@pytest.mark.unit
def test_opencode_windows_materializes_dcp_jsonc_copy_with_backup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_winreg: FakeWinreg,
) -> None:
    repository = make_dcp_repository(tmp_path)
    home = tmp_path / "home"
    config_dir = home / ".config" / "opencode"
    config_dir.mkdir(parents=True)
    stale = config_dir / "dcp.jsonc"
    stale.write_text('{"autoUpdate": true}', encoding="utf-8")
    intercept_broadcast(monkeypatch)

    apply_adapter(repository, home, OpenCodeWindows())

    destination = config_dir / "dcp.jsonc"
    assert destination.is_file()
    assert not destination.is_symlink()
    assert destination.read_text(encoding="utf-8") == "{}"
    backup = home / ".config" / "opencode-backup" / "fixo" / "dcp.jsonc"
    assert backup.read_text(encoding="utf-8") == '{"autoUpdate": true}'


@pytest.mark.unit
def test_opencode_windows_dcp_jsonc_sync_is_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_winreg: FakeWinreg,
) -> None:
    repository = make_dcp_repository(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    intercept_broadcast(monkeypatch)

    apply_adapter(repository, home, OpenCodeWindows(), timestamp="primeiro")
    apply_adapter(repository, home, OpenCodeWindows(), timestamp="segundo")

    backup_root = home / ".config" / "opencode-backup"
    assert not (backup_root / "segundo").exists()
    destination = home / ".config" / "opencode" / "dcp.jsonc"
    assert destination.read_text(encoding="utf-8") == "{}"
