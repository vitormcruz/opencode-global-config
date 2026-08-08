from io import StringIO
from pathlib import Path

import pytest

from opencode_config.bootstrap.detect import (
    DependencyDetection,
    DependencyStatus,
)
from opencode_config.bootstrap.installers import InstallContext, InstallResult
from opencode_config.lib.environment import EnvironmentKind


def empty_detection() -> tuple[DependencyDetection, ...]:
    return ()


@pytest.mark.unit
def test_shell_entrypoint_is_thin_and_delegates_to_python(repo_root: Path) -> None:
    entrypoint = repo_root / "scripts/bootstrap_repo/configurar-repo.sh"
    lines = entrypoint.read_text(encoding="utf-8").splitlines()

    assert len(lines) <= 40
    assert "opencode_config.bootstrap.main" in entrypoint.read_text(
        encoding="utf-8"
    )
    assert "run_copilot_adapter" not in entrypoint.read_text(encoding="utf-8")
    assert "run_opencode_adapter" not in entrypoint.read_text(encoding="utf-8")


@pytest.mark.unit
def test_powershell_entrypoint_is_thin_and_delegates_to_python(
    repo_root: Path,
) -> None:
    entrypoint = repo_root / "scripts/bootstrap_repo/configurar-repo.ps1"
    content = entrypoint.read_text(encoding="utf-8")

    assert len(content.splitlines()) <= 40
    assert "opencode_config.bootstrap.main" in content
    assert "copilot-adapter" not in content
    assert "opencode-adapter" not in content


@pytest.mark.unit
def test_linux_runs_only_opencode_adapter(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    calls: list[str] = []
    monkeypatch.setattr(
        bootstrap_main,
        "detect_environment",
        lambda: EnvironmentKind.LINUX,
    )
    monkeypatch.setattr(
        bootstrap_main,
        "run_bootstrap",
        lambda **_kwargs: type(
            "Result",
            (),
            {"install_results": ()},
        )(),
    )
    monkeypatch.setattr(
        bootstrap_main,
        "_run_opencode_adapter",
        lambda *_args, **_kwargs: calls.append("opencode") or 0,
    )
    monkeypatch.setattr(
        bootstrap_main,
        "_run_copilot_adapter",
        lambda *_args, **_kwargs: calls.append("copilot") or 0,
    )

    status = bootstrap_main.run(
        ["--yes", "--quiet", "--repo-root", str(tmp_path)],
        output=StringIO(),
        error=StringIO(),
    )

    assert status == 0
    assert calls == ["opencode"]


@pytest.mark.unit
def test_windows_runs_only_copilot_adapter(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    calls: list[str] = []
    monkeypatch.setattr(
        bootstrap_main,
        "detect_environment",
        lambda: EnvironmentKind.WINDOWS,
    )
    monkeypatch.setattr(
        bootstrap_main,
        "run_bootstrap",
        lambda **_kwargs: type(
            "Result",
            (),
            {"install_results": ()},
        )(),
    )
    monkeypatch.setattr(
        bootstrap_main,
        "_run_opencode_adapter",
        lambda *_args, **_kwargs: calls.append("opencode") or 0,
    )
    monkeypatch.setattr(
        bootstrap_main,
        "_run_copilot_adapter",
        lambda *_args, **_kwargs: calls.append("copilot") or 0,
    )

    status = bootstrap_main.run(
        ["--yes", "--repo-root", str(tmp_path)],
        output=StringIO(),
        error=StringIO(),
    )

    assert status == 0
    assert calls == ["copilot"]


@pytest.mark.unit
def test_check_only_does_not_run_an_adapter(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    calls: list[str] = []
    monkeypatch.setattr(
        bootstrap_main,
        "detect_environment",
        lambda: EnvironmentKind.LINUX,
    )
    monkeypatch.setattr(
        bootstrap_main,
        "run_bootstrap",
        lambda **_kwargs: type(
            "Result",
            (),
            {"install_results": ()},
        )(),
    )
    monkeypatch.setattr(
        bootstrap_main,
        "_run_opencode_adapter",
        lambda *_args, **_kwargs: calls.append("opencode") or 0,
    )

    status = bootstrap_main.run(
        ["--check-only", "--repo-root", str(tmp_path)],
        output=StringIO(),
        error=StringIO(),
    )

    assert status == 0
    assert calls == []


@pytest.mark.unit
def test_main_forwards_yes_quiet_and_repo_root_to_adapter(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    adapter_args: list[str] = []
    monkeypatch.setattr(
        bootstrap_main,
        "detect_environment",
        lambda: EnvironmentKind.LINUX,
    )
    monkeypatch.setattr(
        bootstrap_main,
        "run_bootstrap",
        lambda **_kwargs: type(
            "Result",
            (),
            {"install_results": ()},
        )(),
    )
    monkeypatch.setattr(
        bootstrap_main,
        "_run_opencode_adapter",
        lambda _root, args: adapter_args.extend(args) or 0,
    )

    status = bootstrap_main.run(
        [
            "--yes",
            "--quiet",
            "--repo-root",
            str(tmp_path),
        ],
        output=StringIO(),
        error=StringIO(),
    )

    assert status == 0
    assert adapter_args == [
        "--yes",
        "--quiet",
        "--repo-root",
        str(tmp_path),
    ]
