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
def test_registry_declares_managed_dependencies_and_install_methods() -> None:
    names = {spec.name for spec in DEPENDENCY_REGISTRY}

    assert names == {
        "python",
        "node",
        "npm",
        "npx",
        "pipx",
        "crwl",
        "docling",
        "codebase-memory-mcp",
        "pandoc",
        "git",
        "playwright",
        "pytest",
        "aws-cli",
        "opencode-config",
    }
    assert all(spec.commands for spec in DEPENDENCY_REGISTRY)
    assert all(spec.install_methods for spec in DEPENDENCY_REGISTRY)
    assert all(
        set(spec.install_methods) == set(EnvironmentKind)
        for spec in DEPENDENCY_REGISTRY
    )
    package_spec = next(
        spec for spec in DEPENDENCY_REGISTRY if spec.name == "opencode-config"
    )
    assert package_spec.commands == ("opencode-config-check",)


@pytest.mark.unit
def test_registry_tracks_npm_and_npx_separately_from_node() -> None:
    npm_spec = next(item for item in DEPENDENCY_REGISTRY if item.name == "npm")
    npx_spec = next(item for item in DEPENDENCY_REGISTRY if item.name == "npx")

    assert npm_spec.commands == ("npm",)
    assert npx_spec.commands == ("npx",)
    assert npm_spec.install_method_for(EnvironmentKind.WINDOWS)
    assert npx_spec.install_method_for(EnvironmentKind.WINDOWS)


@pytest.mark.unit
def test_windows_python_detection_prefers_python_over_python3(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = next(item for item in DEPENDENCY_REGISTRY if item.name == "python")
    calls: list[tuple[str, ...]] = []

    def fake_which(command: str, path: str | None = None) -> str:
        del path
        return f"C:/Python/{command}.exe"

    def fake_runner(command: list[str], **_: object) -> CommandResult:
        calls.append(tuple(command))
        return CommandResult(
            args=tuple(command),
            returncode=0,
            stdout="Python 3.14.0\n",
            stderr="",
        )

    monkeypatch.setattr("opencode_config.bootstrap.detect.shutil.which", fake_which)

    result = detect_dependency(
        spec,
        EnvironmentKind.WINDOWS,
        runner=fake_runner,
    )

    assert result.status is DependencyStatus.PRESENT
    assert calls == [("C:/Python/python.exe", "--version")]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("name", "stdout"),
    [
        ("node", "v18.20.0\n"),
        ("aws-cli", "aws-cli/1.32.0 Python/3.11.0\n"),
    ],
)
def test_registry_marks_unsupported_major_versions_as_outdated(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    stdout: str,
) -> None:
    spec = next(item for item in DEPENDENCY_REGISTRY if item.name == name)
    monkeypatch.setattr(
        "opencode_config.bootstrap.detect.shutil.which",
        lambda *_args, **_kwargs: f"/mock/bin/{name}",
    )

    result = detect_dependency(
        spec,
        EnvironmentKind.WINDOWS,
        runner=lambda command, **_: CommandResult(
            args=tuple(command),
            returncode=0,
            stdout=stdout,
            stderr="",
        ),
    )

    assert result.status is DependencyStatus.OUTDATED


@pytest.mark.unit
def test_npm_is_missing_even_when_node_is_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = next(item for item in DEPENDENCY_REGISTRY if item.name == "npm")
    monkeypatch.setattr(
        "opencode_config.bootstrap.detect.shutil.which",
        lambda command, path=None: (
            "/mock/bin/node" if command == "node" else None
        ),
    )

    result = detect_dependency(
        spec,
        EnvironmentKind.WINDOWS,
        runner=lambda command, **_: CommandResult(
            args=tuple(command),
            returncode=0,
            stdout="",
            stderr="",
        ),
    )

    assert result.status is DependencyStatus.MISSING


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
def test_detect_dependency_reads_windows_path_case_insensitively(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = make_spec()
    observed_paths: list[str | None] = []

    def fake_which(command: str, path: str | None = None) -> str:
        observed_paths.append(path)
        return f"C:/tools/{command}.exe"

    monkeypatch.setattr("opencode_config.bootstrap.detect.shutil.which", fake_which)

    result = detect_dependency(
        spec,
        EnvironmentKind.WINDOWS,
        env={"Path": "C:/tools"},
        runner=lambda command, **_: CommandResult(
            args=tuple(command),
            returncode=0,
            stdout="fake-tool 1.2.3\n",
            stderr="",
        ),
    )

    assert result.status is DependencyStatus.PRESENT
    assert observed_paths == ["C:/tools"]


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
