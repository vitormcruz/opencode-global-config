import pytest

from opencode_config.bootstrap.registry import (
    PRODUCT_DEPENDENCY_REGISTRY,
)
from opencode_config.bootstrap.installers import (
    GITLEAKS_SHA256_LINUX,
    GITLEAKS_SHA256_WINDOWS,
    GRADLE_SHA256,
    InstallContext,
    JDK_SHA256_LINUX,
    JDK_SHA256_WINDOWS,
    POWERSHELL_SHA256_LINUX,
    POWERSHELL_SHA256_WINDOWS,
    SHELLCHECK_SHA256_WINDOWS,
    install_gradle,
    install_java,
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


PINNED_CHECKSUMS = {
    "GRADLE_SHA256": GRADLE_SHA256,
    "POWERSHELL_SHA256_LINUX": POWERSHELL_SHA256_LINUX,
    "POWERSHELL_SHA256_WINDOWS": POWERSHELL_SHA256_WINDOWS,
    "GITLEAKS_SHA256_LINUX": GITLEAKS_SHA256_LINUX,
    "GITLEAKS_SHA256_WINDOWS": GITLEAKS_SHA256_WINDOWS,
    "SHELLCHECK_SHA256_WINDOWS": SHELLCHECK_SHA256_WINDOWS,
    "JDK_SHA256_LINUX": JDK_SHA256_LINUX,
    "JDK_SHA256_WINDOWS": JDK_SHA256_WINDOWS,
}


@pytest.mark.unit
@pytest.mark.parametrize("constant_name", sorted(PINNED_CHECKSUMS))
def test_portable_downloads_pin_the_official_sha256(constant_name: str) -> None:
    import re

    checksum = PINNED_CHECKSUMS[constant_name]

    assert re.fullmatch(r"[0-9a-f]{64}", checksum), (
        f"{constant_name} precisa do SHA-256 fixado do release oficial"
    )


@pytest.mark.unit
def test_install_gradle_extracts_a_complete_user_space_distribution(tmp_path) -> None:
    import zipfile
    from hashlib import sha256

    archive = tmp_path / "gradle.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("gradle-8.10.2/bin/gradle", "#!/bin/sh\n")
    context = make_context(tmp_path)

    result = install_gradle(
        context,
        url=f"file://{archive}",
        expected_sha256=sha256(archive.read_bytes()).hexdigest(),
    )

    assert result.success
    assert (context.paths.data_dir / "gradle" / "bin" / "gradle").is_file()
    assert str(context.paths.data_dir / "gradle" / "bin") in (
        context.current_environment["PATH"]
    )


@pytest.mark.unit
def test_install_gradle_rejects_a_checksum_mismatch(tmp_path) -> None:
    import zipfile

    archive = tmp_path / "gradle.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("gradle-8.10.2/bin/gradle", "#!/bin/sh\n")
    context = make_context(tmp_path)

    with pytest.raises(Exception, match="SHA256 divergente"):
        install_gradle(
            context,
            url=f"file://{archive}",
            expected_sha256="0" * 64,
        )


@pytest.mark.unit
def test_install_shellcheck_uses_the_official_archive_on_windows(tmp_path) -> None:
    import zipfile
    from hashlib import sha256

    archive = tmp_path / "shellcheck.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("shellcheck-v0.10.0/shellcheck.exe", "binary")
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)

    result = install_shellcheck(
        context,
        url=f"file://{archive}",
        expected_sha256=sha256(archive.read_bytes()).hexdigest(),
    )

    assert result.success
    assert (context.paths.data_dir / "shellcheck" / "shellcheck.exe").is_file()


def build_tar_with_symlink(tmp_path, link_name, link_target):
    import io
    import tarfile

    archive = tmp_path / "jdk.tar.gz"
    with tarfile.open(archive, "w:gz") as output:
        directory = tarfile.TarInfo("jdk-21")
        directory.type = tarfile.DIRTYPE
        output.addfile(directory)
        payload = b"binary"
        library = tarfile.TarInfo("jdk-21/lib/libjvm.so")
        library.size = len(payload)
        output.addfile(library, io.BytesIO(payload))
        symlink = tarfile.TarInfo(link_name)
        symlink.type = tarfile.SYMTYPE
        symlink.linkname = link_target
        output.addfile(symlink)
    return archive


@pytest.mark.unit
def test_extract_archive_accepts_symlinks_inside_the_jdk_tarball(
    tmp_path,
    monkeypatch,
) -> None:
    import tarfile

    from opencode_config.bootstrap.installers.core import _extract_archive

    monkeypatch.setattr(
        tarfile,
        "is_tarfile",
        lambda _archive: True,
        raising=False,
    )
    archive = build_tar_with_symlink(
        tmp_path,
        "jdk-21/bin/server-link",
        "../lib/libjvm.so",
    )
    destination = tmp_path / "extracted"

    _extract_archive(archive, destination)

    link = destination / "jdk-21" / "bin" / "server-link"
    assert link.is_symlink()
    assert link.resolve() == (
        destination / "jdk-21" / "lib" / "libjvm.so"
    ).resolve()


@pytest.mark.unit
def test_extract_archive_rejects_symlink_escape(tmp_path, monkeypatch) -> None:
    import tarfile

    import pytest

    from opencode_config.bootstrap.installers.core import InstallerError
    from opencode_config.bootstrap.installers.core import _extract_archive

    monkeypatch.setattr(
        tarfile,
        "is_tarfile",
        lambda _archive: True,
        raising=False,
    )
    archive = build_tar_with_symlink(
        tmp_path,
        "jdk-21/escape",
        "../../../outside",
    )
    destination = tmp_path / "extracted"

    with pytest.raises(InstallerError, match="Symlink fora do destino"):
        _extract_archive(archive, destination)


def build_jdk_tarball(destination) -> None:
    import io
    import tarfile

    with tarfile.open(destination, "w:gz") as output:
        directory = tarfile.TarInfo("jdk-21.0.6+7/bin")
        directory.type = tarfile.DIRTYPE
        output.addfile(directory)
        payload = b"#!/bin/sh\n"
        executable = tarfile.TarInfo("jdk-21.0.6+7/bin/java")
        executable.size = len(payload)
        output.addfile(executable, io.BytesIO(payload))


@pytest.mark.unit
def test_install_java_falls_back_to_github_mirror_keeping_checksum(tmp_path) -> None:
    from hashlib import sha256

    context = make_context(tmp_path)
    fetched_urls = []
    payload = tmp_path / "payload.tar.gz"
    build_jdk_tarball(payload)

    def fetcher(url, destination):
        fetched_urls.append(url)
        if "api.adoptium.net" in url:
            raise OSError("HTTP 403")
        destination.write_bytes(payload.read_bytes())

    result = install_java(
        context,
        expected_sha256=sha256(payload.read_bytes()).hexdigest(),
        fetcher=fetcher,
    )

    assert result.success
    assert len(fetched_urls) == 2
    assert "api.adoptium.net" in fetched_urls[0]
    assert "github.com/adoptium" in fetched_urls[1]
    assert (
        context.paths.data_dir / "jdk" / "bin" / "java"
    ).is_file()


@pytest.mark.unit
def test_install_java_with_explicit_url_does_not_mirror(tmp_path) -> None:
    from hashlib import sha256

    payload = tmp_path / "payload.tar.gz"
    build_jdk_tarball(payload)
    context = make_context(tmp_path)
    fetched_urls = []

    def fetcher(url, destination):
        fetched_urls.append(url)
        destination.write_bytes(payload.read_bytes())

    result = install_java(
        context,
        url=f"file://{payload}",
        expected_sha256=sha256(payload.read_bytes()).hexdigest(),
        fetcher=fetcher,
    )

    assert result.success
    assert fetched_urls == []
    assert (
        context.paths.data_dir / "jdk" / "bin" / "java"
    ).is_file()


@pytest.mark.unit
def test_install_java_persists_java_home_in_posix_profile(tmp_path) -> None:
    import io
    import tarfile

    payload = tmp_path / "jdk.tar.gz"
    with tarfile.open(payload, "w:gz") as output:
        directory = tarfile.TarInfo("jdk-21.0.6+7/bin")
        directory.type = tarfile.DIRTYPE
        output.addfile(directory)
        executable_payload = b"#!/bin/sh\n"
        executable = tarfile.TarInfo("jdk-21.0.6+7/bin/java")
        executable.size = len(executable_payload)
        output.addfile(executable, io.BytesIO(executable_payload))
    profile = tmp_path / ".bashrc"
    context = make_context(tmp_path)
    context.profile_path = profile

    result = install_java(
        context,
        url=f"file://{payload}",
        expected_sha256=__import__("hashlib")
        .sha256(payload.read_bytes())
        .hexdigest(),
    )

    assert result.success
    persisted = profile.read_text(encoding="utf-8")
    assert 'export JAVA_HOME="' in persisted
    assert str(context.paths.data_dir / "jdk") in persisted


@pytest.mark.unit
def test_install_java_persists_java_home_for_powershell_profile(tmp_path) -> None:
    import zipfile
    from hashlib import sha256

    payload = tmp_path / "jdk.zip"
    with zipfile.ZipFile(payload, "w") as output:
        output.writestr("jdk-21.0.6+7/bin/java.exe", "#!/bin/sh\n")
    profile = tmp_path / "profile.ps1"
    context = make_context(tmp_path, EnvironmentKind.WINDOWS)
    context.profile_path = profile

    result = install_java(
        context,
        url=f"file://{payload}",
        expected_sha256=sha256(payload.read_bytes()).hexdigest(),
    )

    assert result.success
    persisted = profile.read_text(encoding="utf-8")
    assert "$env:JAVA_HOME =" in persisted
    assert str(context.paths.data_dir / "jdk") in persisted


@pytest.mark.unit
def test_install_java_without_profile_skips_persistence(tmp_path) -> None:
    import io
    import tarfile
    from hashlib import sha256

    payload = tmp_path / "jdk.tar.gz"
    with tarfile.open(payload, "w:gz") as output:
        directory = tarfile.TarInfo("jdk-21.0.6+7/bin")
        directory.type = tarfile.DIRTYPE
        output.addfile(directory)
        executable_payload = b"#!/bin/sh\n"
        executable = tarfile.TarInfo("jdk-21.0.6+7/bin/java")
        executable.size = len(executable_payload)
        output.addfile(executable, io.BytesIO(executable_payload))
    profile = tmp_path / ".bashrc"
    context = make_context(tmp_path)
    context.profile_path = None

    result = install_java(
        context,
        url=f"file://{payload}",
        expected_sha256=sha256(payload.read_bytes()).hexdigest(),
    )

    assert result.success
    assert not profile.exists()
