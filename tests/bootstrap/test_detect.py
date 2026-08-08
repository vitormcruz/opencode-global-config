from pathlib import Path

import pytest

from opencode_config.bootstrap.detect import (
    DependencySpec,
    DependencyStatus,
    detect_dependencies,
    detect_dependency,
)
from opencode_config.bootstrap.registry import DEPENDENCY_REGISTRY
from opencode_config.lib.environment import EnvironmentKind
from opencode_config.lib.process import CommandResult


def make_spec(
    *,
    name: str = "fake-tool",
    minimum_version: tuple[int, ...] | None = None,
) -> DependencySpec:
    return DependencySpec(
        name=name,
        commands=("fake-tool",),
        install_methods={
            EnvironmentKind.LINUX: "metodo Linux",
            EnvironmentKind.WSL: "metodo WSL",
            EnvironmentKind.WINDOWS: "metodo Windows",
        },
        required=False,
        minimum_version=minimum_version,
    )


@pytest.mark.unit
def test_registry_declares_all_ad9_dependencies_and_install_methods() -> None:
    names = {spec.name for spec in DEPENDENCY_REGISTRY}

    assert names == {
        "python",
        "node",
        "pipx",
        "crwl",
        "docling",
        "codebase-memory-mcp",
        "pandoc",
        "git",
        "playwright",
        "pytest",
        "aws-cli",
    }
    assert all(spec.commands for spec in DEPENDENCY_REGISTRY)
    assert all(spec.install_methods for spec in DEPENDENCY_REGISTRY)
    assert all(
        set(spec.install_methods) == set(EnvironmentKind)
        for spec in DEPENDENCY_REGISTRY
    )


@pytest.mark.unit
def test_detect_dependency_reports_present_version_path_and_method(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = make_spec()
    calls: list[tuple[str, ...]] = []

    def fake_which(command: str, path: str | None = None) -> str | None:
        assert path == "/mock/bin"
        return f"/mock/bin/{command}"

    def fake_runner(command: list[str], **_: object) -> CommandResult:
        calls.append(tuple(command))
        return CommandResult(
            args=tuple(command),
            returncode=0,
            stdout="fake-tool 1.2.3\n",
            stderr="",
        )

    monkeypatch.setenv("PATH", "/mock/bin")
    monkeypatch.setattr("opencode_config.bootstrap.detect.shutil.which", fake_which)

    result = detect_dependency(
        spec,
        EnvironmentKind.LINUX,
        runner=fake_runner,
    )

    assert result.status is DependencyStatus.PRESENT
    assert result.name == "fake-tool"
    assert result.version == "1.2.3"
    assert result.path == Path("/mock/bin/fake-tool")
    assert result.install_method == "metodo Linux"
    assert result.required is False
    assert calls == [("/mock/bin/fake-tool", "--version")]


@pytest.mark.unit
def test_detect_dependency_reports_missing_without_running_installation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = make_spec()
    runner_called = False

    def fake_runner(*_: object, **__: object) -> CommandResult:
        nonlocal runner_called
        runner_called = True
        raise AssertionError("missing commands must not be executed")

    monkeypatch.setattr(
        "opencode_config.bootstrap.detect.shutil.which",
        lambda *_args, **_kwargs: None,
    )

    result = detect_dependency(
        spec,
        EnvironmentKind.WINDOWS,
        runner=fake_runner,
    )

    assert result.status is DependencyStatus.MISSING
    assert result.version is None
    assert result.path is None
    assert result.install_method == "metodo Windows"
    assert not runner_called


@pytest.mark.unit
def test_detect_dependency_marks_version_below_minimum_as_outdated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = make_spec(minimum_version=(3, 10))
    monkeypatch.setattr(
        "opencode_config.bootstrap.detect.shutil.which",
        lambda *_args, **_kwargs: "/mock/bin/fake-tool",
    )

    result = detect_dependency(
        spec,
        EnvironmentKind.LINUX,
        runner=lambda command, **_: CommandResult(
            args=tuple(command),
            returncode=0,
            stdout="fake-tool 3.9.18",
            stderr="",
        ),
    )

    assert result.status is DependencyStatus.OUTDATED
    assert result.version == "3.9.18"


@pytest.mark.unit
def test_detect_dependency_reports_command_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = make_spec()
    monkeypatch.setattr(
        "opencode_config.bootstrap.detect.shutil.which",
        lambda *_args, **_kwargs: "/mock/bin/fake-tool",
    )

    result = detect_dependency(
        spec,
        EnvironmentKind.LINUX,
        runner=lambda command, **_: CommandResult(
            args=tuple(command),
            returncode=2,
            stdout="",
            stderr="broken installation",
        ),
    )

    assert result.status is DependencyStatus.ERROR
    assert result.version is None
    assert result.error == "broken installation"


@pytest.mark.unit
def test_detect_dependencies_uses_only_declarative_specs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    specs = (make_spec(name="one"), make_spec(name="two"))
    monkeypatch.setattr(
        "opencode_config.bootstrap.detect.shutil.which",
        lambda command, **_: f"/mock/bin/{command}",
    )

    results = detect_dependencies(
        EnvironmentKind.WSL,
        specs=specs,
        runner=lambda command, **_: CommandResult(
            args=tuple(command),
            returncode=0,
            stdout="tool 9.8.7",
            stderr="",
        ),
    )

    assert [result.name for result in results] == ["one", "two"]
    assert all(result.status is DependencyStatus.PRESENT for result in results)
    assert all(result.install_method == "metodo WSL" for result in results)
