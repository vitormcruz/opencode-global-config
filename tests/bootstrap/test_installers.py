from hashlib import sha256
from pathlib import Path
import sys
import zipfile

import pytest

from opencode_config.bootstrap.installers import (
    InstallContext,
    InstallResult,
    InstallerError,
    ensure_path_entry,
    download_file,
    install_aws_cli,
    install_codebase_memory,
    install_copilot,
    install_crwl,
    install_dependencies,
    install_fnm,
    install_npm,
    install_npm_global,
    install_node,
    install_npx,
    install_opencode_config,
    install_libgomp_runtime,
    install_pipx,
    install_playwright,
    install_pytest,
    is_pytest_environment_ready,
    fix_chrondb_lib,
)
from opencode_config.bootstrap.libgomp import (
    LIBGOMP_PACKAGE_SHA256,
    LIBGOMP_PACKAGE_URL,
    LIBGOMP_LIBRARY_SHA256,
    LIBGOMP_VERSION,
    runtime_validation_error,
    runtime_directory,
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
        persist_paths=False,
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
    linux_bin = Path("/tmp/opencode-config-test-bin")

    ensure_path_entry(
        linux_bin,
        environment_kind=EnvironmentKind.LINUX,
        profile_path=profile,
        environ=environment,
    )
    first_content = profile.read_text(encoding="utf-8")
    ensure_path_entry(
        linux_bin,
        environment_kind=EnvironmentKind.LINUX,
        profile_path=profile,
        environ=environment,
    )

    assert profile.read_text(encoding="utf-8") == first_content
    assert environment["PATH"] == f"{linux_bin}:/usr/bin"
    assert first_content.count("opencode-config:bootstrap-path") == 2


@pytest.mark.unit
def test_ensure_path_entry_preserves_linux_case_sensitive_paths(
    tmp_path: Path,
) -> None:
    environment = {"PATH": "/opt/tool"}

    ensure_path_entry(
        tmp_path / "Tool",
        environment_kind=EnvironmentKind.LINUX,
        environ=environment,
    )

    assert environment["PATH"] == f"{tmp_path / 'Tool'}:/opt/tool"


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
def test_libgomp_runtime_rejects_a_package_checksum_mismatch(
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path)

    def fetcher(_url: str, destination: Path) -> None:
        destination.write_bytes(b"not-the-fixed-debian-package")

    with pytest.raises(InstallerError, match="SHA256 divergente"):
        install_libgomp_runtime(context, fetcher=fetcher)


@pytest.mark.unit
def test_libgomp_runtime_reuses_a_valid_cache_without_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(tmp_path)
    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.runtime_is_valid",
        lambda _home: True,
    )
    result = install_libgomp_runtime(
        context,
        fetcher=lambda *_args: pytest.fail("cache valido nao deve baixar"),
    )

    assert result.success
    assert not result.changed
    assert str(runtime_directory(tmp_path)) in result.message
    assert LIBGOMP_PACKAGE_URL.startswith("https://snapshot.debian.org/")
    assert len(LIBGOMP_PACKAGE_SHA256) == 64
    assert LIBGOMP_VERSION in result.message


@pytest.mark.unit
def test_libgomp_runtime_rejects_missing_provenance_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    library = tmp_path / "libgomp.so.1.0.0"
    library.write_bytes(b"valid-library-placeholder")
    (tmp_path / "libgomp.so.1").symlink_to(library)
    monkeypatch.setattr(
        "opencode_config.bootstrap.libgomp.runtime_library_path",
        lambda _home=None: library,
    )
    monkeypatch.setattr(
        "opencode_config.bootstrap.libgomp.platform.machine",
        lambda: "x86_64",
    )
    monkeypatch.setattr(
        "opencode_config.bootstrap.libgomp._sha256",
        lambda _path: LIBGOMP_LIBRARY_SHA256,
    )

    error = runtime_validation_error(tmp_path, load_library=False)

    assert error is not None
    assert "metadados ausentes ou invalidos" in error


@pytest.mark.unit
def test_install_pipx_is_user_local(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(tmp_path)
    commands: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.shutil.which",
        lambda command, path=None: "/mock/pipx" if command == "pipx" else None,
    )

    result = install_pipx(context, runner=successful_runner(commands))

    assert result.success
    command = commands[0]
    assert command == (
        sys.executable,
        "-m",
        "pip",
        "install",
        "--user",
        "pipx",
    )
    assert "--user" in command
    assert str(context.paths.bin_dir) in context.current_environment["PATH"]


@pytest.mark.unit
def test_install_pipx_windows_adds_python_user_scripts_to_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)
    commands: list[tuple[str, ...]] = []
    user_scripts = tmp_path / "AppData" / "Roaming" / "Python" / "Scripts"
    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.sysconfig.get_path",
        lambda *_args, **_kwargs: str(user_scripts),
    )
    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.shutil.which",
        lambda command, path=None: (
            str(user_scripts / "pipx.exe") if command == "pipx" else None
        ),
    )

    result = install_pipx(context, runner=successful_runner(commands))

    assert result.success
    assert str(user_scripts) in context.current_environment["PATH"].split(";")


@pytest.mark.unit
def test_windows_path_entry_is_persisted_for_future_processes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    persisted: list[str] = []
    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core._persist_windows_user_path",
        persisted.append,
    )
    environment = {"Path": r"C:\Windows\System32"}

    ensure_path_entry(
        tmp_path / "bin",
        environment_kind=EnvironmentKind.WINDOWS,
        environ=environment,
    )

    assert persisted == [str(tmp_path / "bin")]
    assert environment["Path"] == (
        f"{tmp_path / 'bin'};C:\\Windows\\System32"
    )
    assert "PATH" not in environment


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
def test_install_npm_global_windows_uses_npm_bin_as_prefix(tmp_path: Path) -> None:
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)
    commands: list[tuple[str, ...]] = []

    result = install_npm_global(
        context,
        "codebase-memory-mcp",
        runner=successful_runner(commands),
    )

    assert result.success
    command = commands[0]
    assert str(context.paths.npm_bin) in command
    assert str(context.paths.npm_bin.parent) not in command


@pytest.mark.unit
def test_windows_real_executor_resolves_cmd_entrypoints(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)
    observed: list[tuple[str, ...]] = []

    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.shutil.which",
        lambda command, path=None: (
            r"C:\Node\npm.CMD" if command == "npm" else None
        ),
    )
    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.run_command",
        lambda command, **_kwargs: (
            observed.append(tuple(command))
            or CommandResult(tuple(command), 0, "", "")
        ),
    )

    install_npm_global(context, "codebase-memory-mcp")

    assert observed[0][0] == r"C:\Node\npm.CMD"


@pytest.mark.unit
def test_install_crwl_uses_pipx_bin_and_checks_entrypoints(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)
    commands: list[tuple[str, ...]] = []

    def runner(command, **_kwargs):
        commands.append(tuple(command))
        return CommandResult(
            args=tuple(command),
            returncode=0,
            stdout="",
            stderr="",
        )

    def which(command: str, path: str | None = None) -> str | None:
        del path
        if command in {"pipx", "crwl", "crawl4ai-setup"}:
            return str(context.paths.pipx_bin / f"{command}.exe")
        return None

    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.shutil.which",
        which,
    )

    result = install_crwl(context, runner=runner)

    assert result.success
    assert commands == [
        ("pipx", "install", "--force", "crawl4ai"),
        ("crawl4ai-setup",),
    ]
    assert str(context.paths.pipx_bin) in context.current_environment["PATH"]


@pytest.mark.unit
def test_install_crwl_fails_when_pipx_does_not_expose_entrypoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)

    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.shutil.which",
        lambda command, path=None: (
            "/mock/pipx" if command == "pipx" else None
        ),
    )

    with pytest.raises(InstallerError, match="crwl"):
        install_crwl(context, runner=successful_runner([]))


@pytest.mark.unit
def test_install_crwl_rejects_false_success_from_browser_setup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)

    def runner(command, **_kwargs):
        if tuple(command) == ("crawl4ai-setup",):
            return CommandResult(
                args=tuple(command),
                returncode=0,
                stdout="Failed to install browsers",
                stderr="",
            )
        return CommandResult(
            args=tuple(command),
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.shutil.which",
        lambda command, path=None: (
            str(context.paths.pipx_bin / f"{command}.exe")
            if command in {"pipx", "crwl", "crawl4ai-setup"}
            else None
        ),
    )

    with pytest.raises(InstallerError, match="Failed to install browsers"):
        install_crwl(context, runner=runner)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("name", "installer"),
    [("npm", install_npm), ("npx", install_npx)],
)
def test_node_runtime_entrypoint_installers_rename_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    installer,
) -> None:
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)
    available = False

    def which(command, **_kwargs):
        return f"/mock/bin/{command}" if available and command == name else None

    def install_runtime(*_args, **_kwargs):
        nonlocal available
        available = True
        return InstallResult(
            name="node",
            success=True,
            changed=True,
            message="node instalado",
        )

    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.shutil.which",
        which,
    )
    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.install_node",
        install_runtime,
    )

    result = installer(context)

    assert result.name == name
    assert result.success


@pytest.mark.unit
def test_node_runtime_entrypoint_installers_report_missing_entrypoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)
    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.shutil.which",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.install_node",
        lambda *_args, **_kwargs: InstallResult(
            name="node",
            success=True,
            changed=True,
            message="node instalado",
        ),
    )

    result = install_npm(context)

    assert result.name == "npm"
    assert not result.success
    assert "npm" in result.error


@pytest.mark.unit
def test_install_opencode_config_uses_editable_repo_with_pipx(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)
    commands: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.shutil.which",
        lambda command, path=None: (
            "/mock/opencode-config-check"
            if command == "opencode-config-check"
            else None
        ),
    )

    result = install_opencode_config(
        context,
        runner=successful_runner(commands),
    )

    assert result.success
    assert commands[0] == (
        "pipx",
        "install",
        "--force",
        "--editable",
        str(tmp_path),
    )


@pytest.mark.unit
def test_install_codebase_memory_enables_auto_index(
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path)
    commands: list[tuple[str, ...]] = []
    temporary = tmp_path / ".chrondb/lib/.tmp-extract-runtime"
    temporary.mkdir(parents=True)
    (temporary / "libchrondb.so").write_text("\x00", encoding="utf-8")

    result = install_codebase_memory(
        context,
        runner=successful_runner(commands),
    )

    assert result.success
    assert result.name == "codebase-memory-mcp"
    assert commands[0][-1] == "codebase-memory-mcp@0.9.0"
    assert commands[-1] == (
        "codebase-memory-mcp",
        "config",
        "set",
        "auto_index",
        "true",
    )
    assert (tmp_path / ".chrondb/lib/libchrondb.so").is_file()
    assert not temporary.exists()


@pytest.mark.unit
def test_fix_chrondb_lib_moves_runtime_files_from_temp_directory(
    tmp_path: Path,
) -> None:
    chrondb_lib = tmp_path / ".chrondb/lib"
    temporary = chrondb_lib / ".tmp-extract-runtime"
    temporary.mkdir(parents=True)
    for name, content in {
        "libchrondb.h": "#define CHRONDB 1",
        "libchrondb.so": "\x00",
        "graal_isolate.h": "header",
        "graal_isolate_dynamic.h": "header",
        "libchrondb_dynamic.h": "header",
    }.items():
        (temporary / name).write_text(content, encoding="utf-8")

    fix_chrondb_lib(tmp_path)

    assert all((chrondb_lib / name).is_file() for name in (
        "libchrondb.h",
        "libchrondb.so",
        "graal_isolate.h",
        "graal_isolate_dynamic.h",
        "libchrondb_dynamic.h",
    ))
    assert not temporary.exists()


@pytest.mark.unit
def test_fix_chrondb_lib_is_idempotent_when_temp_directory_is_missing(
    tmp_path: Path,
) -> None:
    fix_chrondb_lib(tmp_path)

    assert not (tmp_path / ".chrondb/lib/.tmp-extract-runtime").exists()


@pytest.mark.unit
def test_fix_chrondb_lib_preserves_existing_runtime_files(
    tmp_path: Path,
) -> None:
    chrondb_lib = tmp_path / ".chrondb/lib"
    chrondb_lib.mkdir(parents=True)
    existing = chrondb_lib / "libchrondb.so"
    existing.write_text("existing", encoding="utf-8")

    fix_chrondb_lib(tmp_path)

    assert existing.read_text(encoding="utf-8") == "existing"


@pytest.mark.unit
def test_fix_chrondb_lib_is_exposed_by_bootstrap_installers() -> None:
    assert callable(fix_chrondb_lib)


@pytest.mark.unit
def test_install_copilot_uses_user_npm_prefix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)
    commands: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.shutil.which",
        lambda command, path=None: (
            str(context.paths.npm_bin / "copilot.cmd")
            if command == "copilot"
            else None
        ),
    )

    result = install_copilot(
        context,
        runner=successful_runner(commands),
    )

    assert result.success
    assert commands[0][-1] == "@github/copilot"
    assert str(context.paths.npm_bin) in commands[0]


@pytest.mark.unit
def test_install_playwright_installs_package_and_chromium(
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path)
    commands: list[tuple[str, ...]] = []

    result = install_playwright(
        context,
        runner=successful_runner(commands),
    )

    assert result.success
    assert commands[0] == (
        "npm",
        "install",
        "--global",
        "--prefix",
        str(context.paths.npm_bin.parent),
        "@playwright/test",
    )
    assert commands[1] == (
        "npx",
        "--yes",
        "playwright",
        "install",
        "chromium",
    )


@pytest.mark.unit
def test_install_pytest_installs_the_repository_in_the_virtualenv(
    tmp_path: Path,
) -> None:
    (tmp_path / "requirements-dev.txt").write_text(
        "pytest>=8,<10\n",
        encoding="utf-8",
    )
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)
    commands: list[tuple[str, ...]] = []

    result = install_pytest(
        context,
        runner=successful_runner(commands),
    )

    assert result.success
    assert commands[-1] == (
        str(tmp_path / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "pip",
        "install",
        "--editable",
        str(tmp_path),
    )


@pytest.mark.unit
def test_pytest_environment_check_ignores_bootstrap_pythonpath(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)
    python_path = tmp_path / ".venv" / "Scripts" / "python.exe"
    python_path.parent.mkdir(parents=True)
    python_path.touch()
    context.current_environment["PYTHONPATH"] = str(tmp_path / "src")
    observed_environment: dict[str, str] = {}
    observed_command: list[str] = []

    def successful_import(command, *, cwd, env):
        del cwd
        observed_command.extend(command)
        observed_environment.update(env)
        return CommandResult(
            args=(str(python_path),),
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.run_command",
        successful_import,
    )

    assert is_pytest_environment_ready(context)
    assert observed_command[-1] == "import opencode_config; import pytest"
    assert "PYTHONPATH" not in observed_environment
    assert "PYTHONHOME" not in observed_environment


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
@pytest.mark.parametrize(
    ("relative_bin", "expected_tail"),
    [
        ("installation/bin", "installation/bin"),      # layout Linux/WSL
        ("installation", "installation"),              # layout Windows
    ],
)
def test_fnm_node_bin_dir_resolves_layout_por_plataforma(
    tmp_path: Path,
    relative_bin: str,
    expected_tail: str,
) -> None:
    from opencode_config.lib.versions import fnm_node_bin_dir

    fnm_dir = tmp_path / "fnm"
    version_dir = fnm_dir / "node-versions" / "v22.23.2"
    node_bin = version_dir / relative_bin
    node_bin.mkdir(parents=True)
    (node_bin / "node").write_text("node", encoding="utf-8")

    result = fnm_node_bin_dir(tmp_path, {"FNM_DIR": str(fnm_dir)}, major=22)

    assert result is not None
    assert result.is_dir()
    assert result.parts[-len(Path(expected_tail).parts):] == Path(
        expected_tail
    ).parts


@pytest.mark.unit
def test_fnm_node_bin_dir_filtra_por_major_e_ordena_mais_recente(
    tmp_path: Path,
) -> None:
    from opencode_config.lib.versions import fnm_node_bin_dir

    fnm_dir = tmp_path / "fnm"
    versions = fnm_dir / "node-versions"
    for name in ("v20.11.1", "v22.3.0", "v22.23.2"):
        node_bin = versions / name / "installation" / "bin"
        node_bin.mkdir(parents=True)
        (node_bin / "node").write_text("node", encoding="utf-8")

    result = fnm_node_bin_dir(tmp_path, {"FNM_DIR": str(fnm_dir)}, major=22)

    assert result is not None
    assert result.name == "bin"
    assert result.parent.parent.name == "v22.23.2"


@pytest.mark.unit
def test_install_node_bootstraps_fnm_before_installing_node(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = tmp_path / "fnm.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("release/fnm", "binary")
    context = make_context(tmp_path)
    # O fnm grava cada versao em $FNM_DIR/node-versions/vX.Y.Z/installation/bin.
    # Apontamos FNM_DIR para um diretorio controlado e criamos o layout real
    # que install_node deve descobrir (sem depender do subcomando `fnm which`,
    # removido nas versoes atuais do fnm).
    fnm_dir = tmp_path / "fnm"
    node_bin = (
        fnm_dir
        / "node-versions"
        / "v22.23.2"
        / "installation"
        / "bin"
    )
    node_bin.mkdir(parents=True)
    (node_bin / "node").write_text("node", encoding="utf-8")
    context.current_environment["FNM_DIR"] = str(fnm_dir)
    # Garante que o bootstrap nao enxergue um fnm/node pre-existente no PATH do
    # ambiente de desenvolvimento, forcando a instalacao user-space completa.
    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.shutil.which",
        lambda *_args, **_kwargs: None,
    )
    commands: list[tuple[str, ...]] = []

    def runner(command, **_kwargs):
        commands.append(tuple(command))
        return CommandResult(
            args=tuple(command),
            returncode=0,
            stdout="",
            stderr="",
        )

    result = install_node(
        context,
        fnm_url=f"file://{archive}",
        runner=runner,
    )

    assert result.success
    assert (context.paths.bin_dir / "fnm").is_file()
    assert ("fnm", "install", "22") in commands
    assert ("fnm", "which", "22") not in commands
    assert str(node_bin) in context.current_environment["PATH"]


@pytest.mark.unit
def test_install_aws_cli_uses_quiet_user_local_linux_script(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script = tmp_path / "aws-install.sh"
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    context = make_context(tmp_path)
    # Simula unzip presente (pre-requisito do instalador oficial da AWS).
    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.shutil.which",
        lambda *_args, **_kwargs: "/usr/bin/unzip",
    )
    captured: list[tuple[tuple[str, ...], dict[str, str]]] = []

    def runner(command, *, env=None, **_kwargs):
        captured.append((tuple(command), dict(env or {})))
        return CommandResult(
            args=tuple(command),
            returncode=0,
            stdout="",
            stderr="",
        )

    result = install_aws_cli(
        context,
        script_url=f"file://{script}",
        runner=runner,
    )

    assert result.success
    command, env = captured[0]
    # O install.sh oficial (v2) aceita apenas --version/--system/--quiet/--help;
    # o local de instalacao user-local e controlado por variaveis XDG.
    assert "--quiet" in command
    assert "--system" not in command
    assert "--install-dir" not in command
    assert "--bin-dir" not in command
    assert "--update" not in command
    assert env["XDG_DATA_HOME"] == str(context.paths.data_dir)
    assert env["XDG_BIN_HOME"] == str(context.paths.bin_dir)


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
def test_install_aws_cli_requires_unzip_on_linux(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(tmp_path)
    monkeypatch.setattr(
        "opencode_config.bootstrap.installers.core.shutil.which",
        lambda *_args, **_kwargs: None,
    )

    with pytest.raises(InstallerError, match="unzip"):
        install_aws_cli(
            context,
            script_url=f"file://{tmp_path / 'unused.sh'}",
            runner=lambda *_args, **_kwargs: pytest.fail(
                "nao deve baixar/rodar o instalador sem unzip"
            ),
        )


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
