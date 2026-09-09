from io import StringIO
from pathlib import Path
import re

import pytest

from opencode_config.bootstrap.detect import (
    DependencyDetection,
    DependencyStatus,
)
from opencode_config.bootstrap.installers import InstallContext, InstallResult
from opencode_config.harnesses import ApplyOptions, HarnessDefinition, HarnessError
from opencode_config.lib.environment import EnvironmentKind


def empty_detection() -> tuple[DependencyDetection, ...]:
    return ()


class RecordingHarness:
    """Harness fake que registra aplicacoes sem tocar no disco."""

    def __init__(
        self,
        name: str,
        *,
        installed: bool = True,
        failure: str | None = None,
    ) -> None:
        self._name = name
        self._installed = installed
        self._failure = failure
        self.applied: list[tuple[Path, ApplyOptions]] = []

    @property
    def name(self) -> str:
        return self._name

    def installed(self, environment: EnvironmentKind) -> bool:
        return self._installed

    def apply(self, repository: Path, options: ApplyOptions) -> None:
        if self._failure is not None:
            raise HarnessError(self._failure)
        self.applied.append((repository, options))


def install_fake_harnesses(
    monkeypatch: pytest.MonkeyPatch,
    *harnesses: RecordingHarness,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    definitions = tuple(
        HarnessDefinition(
            name=harness.name,
            create=lambda _environment, harness=harness: harness,
            skip_variable=f"OPENCODE_SKIP_{harness.name.upper()}_ADAPTER",
        )
        for harness in harnesses
    )
    monkeypatch.setattr(
        bootstrap_main,
        "selecionar_harnesses",
        lambda selecao=None, *, registry=definitions: definitions,
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


@pytest.mark.unit
def test_bootstrap_applies_all_installed_harnesses(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    opencode = RecordingHarness("opencode")
    copilot = RecordingHarness("copilot")
    install_fake_harnesses(monkeypatch, opencode, copilot)
    monkeypatch.setattr(
        bootstrap_main,
        "detect_environment",
        lambda: EnvironmentKind.LINUX,
    )

    status = bootstrap_main.run(
        ["--yes", "--quiet", "--repo-root", str(tmp_path)],
        output=StringIO(),
        error=StringIO(),
    )

    assert status == 0
    assert [harness.name for harness in (opencode, copilot) if harness.applied]
    assert len(opencode.applied) == 1
    assert len(copilot.applied) == 1
    assert opencode.applied[0][0] == tmp_path.resolve()


@pytest.mark.unit
def test_harness_not_installed_warns_and_skips(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    opencode = RecordingHarness("opencode")
    copilot = RecordingHarness("copilot", installed=False)
    install_fake_harnesses(monkeypatch, opencode, copilot)
    monkeypatch.setattr(
        bootstrap_main,
        "detect_environment",
        lambda: EnvironmentKind.WSL,
    )
    output = StringIO()

    status = bootstrap_main.run(
        ["--yes", "--quiet", "--repo-root", str(tmp_path)],
        output=output,
        error=StringIO(),
    )

    assert status == 0
    assert len(opencode.applied) == 1
    assert copilot.applied == []
    assert "copilot nao instalado" in output.getvalue()


@pytest.mark.unit
def test_harness_flag_restricts_selection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    opencode = RecordingHarness("opencode")
    copilot = RecordingHarness("copilot")
    definitions = tuple(
        HarnessDefinition(
            name=harness.name,
            create=lambda _environment, harness=harness: harness,
            skip_variable="OPENCODE_SKIP_UNUSED",
        )
        for harness in (opencode, copilot)
    )
    monkeypatch.setattr(
        bootstrap_main,
        "selecionar_harnesses",
        lambda selecao=None, *, registry=definitions: tuple(
            definition
            for definition in definitions
            if selecao is None or definition.name in selecao
        ),
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
        "detect_environment",
        lambda: EnvironmentKind.LINUX,
    )

    status = bootstrap_main.run(
        [
            "--yes",
            "--quiet",
            "--repo-root",
            str(tmp_path),
            "--harness",
            "copilot",
        ],
        output=StringIO(),
        error=StringIO(),
    )

    assert status == 0
    assert opencode.applied == []
    assert len(copilot.applied) == 1


@pytest.mark.unit
def test_skip_environment_variable_skips_harness(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    opencode = RecordingHarness("opencode")
    copilot = RecordingHarness("copilot")
    install_fake_harnesses(monkeypatch, opencode, copilot)
    monkeypatch.setattr(
        bootstrap_main,
        "detect_environment",
        lambda: EnvironmentKind.LINUX,
    )
    monkeypatch.setenv("OPENCODE_SKIP_COPILOT_ADAPTER", "1")

    status = bootstrap_main.run(
        ["--yes", "--quiet", "--repo-root", str(tmp_path)],
        output=StringIO(),
        error=StringIO(),
    )

    assert status == 0
    assert len(opencode.applied) == 1
    assert copilot.applied == []


@pytest.mark.unit
def test_harness_failure_reports_error_and_keeps_going(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    opencode = RecordingHarness("opencode", failure="quebrou")
    copilot = RecordingHarness("copilot")
    install_fake_harnesses(monkeypatch, opencode, copilot)
    monkeypatch.setattr(
        bootstrap_main,
        "detect_environment",
        lambda: EnvironmentKind.LINUX,
    )
    error = StringIO()

    status = bootstrap_main.run(
        ["--yes", "--quiet", "--repo-root", str(tmp_path)],
        output=StringIO(),
        error=error,
    )

    assert status == 1
    assert "ERRO: harness opencode: quebrou" in error.getvalue()
    assert len(copilot.applied) == 1


@pytest.mark.unit
def test_check_only_does_not_apply_harnesses(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    opencode = RecordingHarness("opencode")
    install_fake_harnesses(monkeypatch, opencode)
    monkeypatch.setattr(
        bootstrap_main,
        "detect_environment",
        lambda: EnvironmentKind.LINUX,
    )

    status = bootstrap_main.run(
        ["--check-only", "--repo-root", str(tmp_path)],
        output=StringIO(),
        error=StringIO(),
    )

    assert status == 0
    assert opencode.applied == []


@pytest.mark.unit
def test_apply_forwards_yes_quiet_and_repo_to_harness(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    opencode = RecordingHarness("opencode")
    install_fake_harnesses(monkeypatch, opencode)
    monkeypatch.setattr(
        bootstrap_main,
        "detect_environment",
        lambda: EnvironmentKind.LINUX,
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
    repository, options = opencode.applied[0]
    assert repository == tmp_path.resolve()
    assert options.assume_yes is True
    assert options.quiet is True


@pytest.mark.unit
def test_help_documents_harness_flag() -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    output = StringIO()

    status = bootstrap_main.run(["--help"], output=output, error=StringIO())

    assert status == 0
    assert "--harness" in output.getvalue()


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
    assert '[Environment]::GetEnvironmentVariable("Path", "User")' in content
    assert "copilot-adapter" not in content
    assert "opencode-adapter" not in content


@pytest.mark.unit
def test_source_environment_variables_are_documented(repo_root: Path) -> None:
    source_root = repo_root / "src/opencode_config"
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in source_root.rglob("*.py")
    )
    documentation = "\n".join(
        (repo_root / name).read_text(encoding="utf-8")
        for name in ("README.md", "AGENTS.md")
    )

    variables = set(re.findall(r"\bOPENCODE_[A-Z_]+\b", source))
    documented = set(re.findall(r"\bOPENCODE_[A-Z_]+\b", documentation))

    assert variables <= documented


@pytest.mark.unit
def test_windows_context_includes_pipx_bin_before_dependency_detection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    monkeypatch.setenv("Path", r"C:\Windows\System32")
    context = bootstrap_main._context_for(EnvironmentKind.WINDOWS, tmp_path)
    path_value = next(
        value
        for name, value in context.current_environment.items()
        if name.casefold() == "path"
    )

    assert str(context.paths.pipx_bin) in path_value


@pytest.mark.unit
def test_windows_context_imports_persisted_user_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    monkeypatch.setattr(
        bootstrap_main,
        "_read_windows_user_path",
        lambda: r"C:\Users\tester\.local\bin;C:\Users\tester\AppData\npm",
    )
    monkeypatch.setenv("Path", r"C:\Windows\System32")

    context = bootstrap_main._context_for(EnvironmentKind.WINDOWS, tmp_path)
    path_value = next(
        value
        for name, value in context.current_environment.items()
        if name.casefold() == "path"
    )

    entries = path_value.split(";")
    assert r"C:\Users\tester\.local\bin" in entries
    assert r"C:\Users\tester\AppData\npm" in entries

