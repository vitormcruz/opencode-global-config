from hashlib import sha256
from pathlib import Path
import zipfile

import pytest

from opencode_config.bootstrap.installers import (
    InstallContext,
    InstallResult,
    InstallerError,
    ensure_path_entry,
    download_file,
    install_aws_cli,
    install_dependencies,
    install_fnm,
    install_npm_global,
    install_node,
    install_pipx,
)
from opencode_config.lib.environment import EnvironmentKind
from opencode_config.lib.paths import resolve_user_space_paths
from opencode_config.lib.process import CommandResult


def make_context(
    tmp_path: Path,
    environment: EnvironmentKind = EnvironmentKind.LINUX,
) -> InstallContext:
    paths = resolve_user_space_paths(environment, home=tmp_path)
    return InstallContext(
        environment=environment,
        paths=paths,
        repo_root=tmp_path,
        profile_path=tmp_path / ".profile",
    )


def successful_runner(commands: list[tuple[str, ...]]):
    def run(command, **_kwargs):
        commands.append(tuple(command))
        return CommandResult(
            args=tuple(command),
            returncode=0,
            stdout="",
            stderr="",
        )

    return run


@pytest.mark.unit
def test_ensure_path_entry_is_idempotent_for_profile_and_process(
    tmp_path: Path,
) -> None:
    profile = tmp_path / ".profile"
    environment = {"PATH": "/usr/bin"}

    ensure_path_entry(
        tmp_path / "bin",
        environment_kind=EnvironmentKind.LINUX,
        profile_path=profile,
        environ=environment,
    )
    first_content = profile.read_text(encoding="utf-8")
    ensure_path_entry(
        tmp_path / "bin",
        environment_kind=EnvironmentKind.LINUX,
        profile_path=profile,
        environ=environment,
    )

    assert profile.read_text(encoding="utf-8") == first_content
    assert environment["PATH"] == f"{tmp_path / 'bin'}:/usr/bin"
    assert first_content.count("opencode-config:bootstrap-path") == 2


@pytest.mark.unit
def test_download_file_verifies_expected_sha256(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    destination = tmp_path / "downloads" / "target.bin"
    source.write_bytes(b"trusted payload")
    expected = sha256(source.read_bytes()).hexdigest()

    result = download_file(
        str(source),
        destination,
        expected_sha256=expected,
    )

    assert result == destination
    assert destination.read_bytes() == b"trusted payload"


@pytest.mark.unit
def test_download_file_rejects_hash_mismatch_with_both_hashes(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.bin"
    destination = tmp_path / "target.bin"
    source.write_bytes(b"untrusted payload")

    with pytest.raises(InstallerError, match="esperado .* encontrado"):
        download_file(
            str(source),
            destination,
            expected_sha256="0" * 64,
        )

    assert not destination.exists()


@pytest.mark.unit
def test_install_pipx_is_user_local_and_does_not_use_sudo(
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path)
    commands: list[tuple[str, ...]] = []

    result = install_pipx(context, runner=successful_runner(commands))

    assert result.success
    command = commands[0]
    assert "--user" in command
    assert "sudo" not in command
    assert str(context.paths.bin_dir) in context.current_environment["PATH"]


@pytest.mark.unit
def test_install_npm_global_uses_user_prefix(tmp_path: Path) -> None:
    context = make_context(tmp_path)
    commands: list[tuple[str, ...]] = []

    result = install_npm_global(
        context,
        "codebase-memory-mcp",
        runner=successful_runner(commands),
    )

    assert result.success
    command = commands[0]
    assert command[:3] == ("npm", "install", "--global")
    assert "--prefix" in command
    assert str(context.paths.npm_bin.parent) in command
    assert "--system" not in command


@pytest.mark.unit
def test_install_fnm_extracts_binary_to_user_bin_and_updates_path(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "fnm.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("release/fnm", "binary")
    context = make_context(tmp_path)

    result = install_fnm(
        context,
        url=f"file://{archive}",
    )

    assert result.success
    assert (context.paths.bin_dir / "fnm").read_text(encoding="utf-8") == "binary"
    assert str(context.paths.bin_dir) in context.current_environment["PATH"]


@pytest.mark.unit
def test_install_node_bootstraps_fnm_before_installing_node(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "fnm.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("release/fnm", "binary")
    context = make_context(tmp_path)
    commands: list[tuple[str, ...]] = []

    result = install_node(
        context,
        fnm_url=f"file://{archive}",
        runner=successful_runner(commands),
    )

    assert result.success
    assert (context.paths.bin_dir / "fnm").is_file()
    assert commands[-1] == ("fnm", "install", "22")


@pytest.mark.unit
def test_install_aws_cli_uses_quiet_user_local_linux_script(
    tmp_path: Path,
) -> None:
    script = tmp_path / "aws-install.sh"
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    context = make_context(tmp_path)
    commands: list[tuple[str, ...]] = []

    result = install_aws_cli(
        context,
        script_url=f"file://{script}",
        runner=successful_runner(commands),
    )

    assert result.success
    command = commands[0]
    assert "--quiet" in command
    assert "--system" not in command
    assert str(context.paths.data_dir / "aws-cli") in command
    assert str(context.paths.bin_dir) in command


@pytest.mark.unit
def test_install_aws_cli_is_noop_for_matching_target_version(
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path)

    result = install_aws_cli(
        context,
        target_version="2.0.0",
        current_version="2.0.0",
        runner=lambda *_args, **_kwargs: pytest.fail("must not execute"),
    )

    assert result.success
    assert not result.changed


@pytest.mark.unit
def test_install_aws_cli_windows_uses_quiet_without_system(
    tmp_path: Path,
) -> None:
    script = tmp_path / "aws-install.ps1"
    script.write_text("Write-Output installed\n", encoding="utf-8")
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)
    commands: list[tuple[str, ...]] = []

    result = install_aws_cli(
        context,
        script_url=f"file://{script}",
        runner=successful_runner(commands),
    )

    assert result.success
    command = commands[0]
    assert "-Quiet" in command
    assert "-System" not in command
    assert "sudo" not in command


@pytest.mark.unit
def test_install_dependencies_continues_after_one_installer_fails(
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path)

    def fail(_context: InstallContext) -> InstallResult:
        raise InstallerError("network unavailable")

    def succeed(_context: InstallContext) -> InstallResult:
        return InstallResult(name="second", success=True, changed=True)

    results = install_dependencies(
        ("first", "second"),
        context,
        installers={"first": fail, "second": succeed},
    )

    assert [result.name for result in results] == ["first", "second"]
    assert not results[0].success
    assert "network unavailable" in results[0].error
    assert results[1].success
