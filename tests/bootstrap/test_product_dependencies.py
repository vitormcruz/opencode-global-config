import pytest

from opencode_config.bootstrap.registry import (
    PRODUCT_DEPENDENCY_REGISTRY,
)
from opencode_config.bootstrap.installers import (
    InstallContext,
    install_gradle,
    install_psscriptanalyzer,
    install_ruff,
    install_shellcheck,
)
from opencode_config.lib.environment import EnvironmentKind
from opencode_config.lib.paths import resolve_user_space_paths
from opencode_config.lib.process import CommandResult


def make_context(tmp_path, environment=EnvironmentKind.LINUX):
    return InstallContext(
        environment=environment,
        paths=resolve_user_space_paths(environment, home=tmp_path),
        repo_root=tmp_path,
        profile_path=tmp_path / ".profile",
        persist_paths=False,
    )


@pytest.mark.unit
def test_product_dependency_registry_contains_approved_tools_and_runtime() -> None:
    names = {spec.name for spec in PRODUCT_DEPENDENCY_REGISTRY}

    assert {
        "ruff",
        "shellcheck",
        "pwsh",
        "PSScriptAnalyzer",
        "pytest-cov",
        "gitleaks",
        "pip-audit",
        "bandit",
        "java",
        "gradle",
    } <= names


@pytest.mark.unit
def test_shellcheck_is_declared_on_windows_and_pwsh_on_wsl() -> None:
    by_name = {spec.name: spec for spec in PRODUCT_DEPENDENCY_REGISTRY}

    assert EnvironmentKind.WINDOWS in (
        by_name["shellcheck"].supported_environments
        or frozenset()
    )
    assert EnvironmentKind.WSL in (
        by_name["pwsh"].supported_environments
        or frozenset()
    )


@pytest.mark.unit
def test_product_dependency_methods_are_user_space_commands() -> None:
    forbidden = ("sudo", "apt install", "winget install")

    for spec in PRODUCT_DEPENDENCY_REGISTRY:
        for environment in EnvironmentKind:
            command = spec.manual_command_for(environment).casefold()
            assert not any(token in command for token in forbidden)


@pytest.mark.unit
def test_install_ruff_uses_pipx_and_checks_the_user_entrypoint(tmp_path, monkeypatch) -> None:
    context = make_context(tmp_path)
    commands = []

    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.shutil.which",
        lambda command, path=None: (
            str(context.paths.pipx_bin / command)
            if command in {"pipx", "ruff"}
            else None
        ),
    )

    result = install_ruff(
        context,
        runner=lambda command, **_kwargs: (
            commands.append(tuple(command))
            or CommandResult(tuple(command), 0, "", "")
        ),
    )

    assert result.success
    assert commands == [("pipx", "install", "--force", "ruff")]


@pytest.mark.unit
def test_install_psscriptanalyzer_uses_current_user_scope(tmp_path) -> None:
    context = make_context(tmp_path)
    commands = []

    result = install_psscriptanalyzer(
        context,
        runner=lambda command, **_kwargs: (
            commands.append(tuple(command))
            or CommandResult(tuple(command), 0, "", "")
        ),
    )

    assert result.success
    assert any("-Scope" in part for part in commands[0])
    assert any("CurrentUser" in part for part in commands[0])
    assert all("sudo" not in part.casefold() for command in commands for part in command)


@pytest.mark.unit
def test_install_gradle_extracts_a_complete_user_space_distribution(tmp_path) -> None:
    import zipfile

    archive = tmp_path / "gradle.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("gradle-8.10.2/bin/gradle", "#!/bin/sh\n")
    context = make_context(tmp_path)

    result = install_gradle(context, url=f"file://{archive}")

    assert result.success
    assert (context.paths.data_dir / "gradle" / "bin" / "gradle").is_file()
    assert str(context.paths.data_dir / "gradle" / "bin") in (
        context.current_environment["PATH"]
    )


@pytest.mark.unit
def test_install_shellcheck_uses_the_official_archive_on_windows(tmp_path) -> None:
    import zipfile

    archive = tmp_path / "shellcheck.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("shellcheck-v0.10.0/shellcheck.exe", "binary")
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)

    result = install_shellcheck(context, url=f"file://{archive}")

    assert result.success
    assert (context.paths.data_dir / "shellcheck" / "shellcheck.exe").is_file()
