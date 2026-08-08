"""Instaladores zero-admin e utilitarios de download do bootstrap."""

from collections.abc import Callable, Iterable, Mapping, MutableMapping
from dataclasses import dataclass, field
import hashlib
import os
from pathlib import Path
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

from opencode_config.lib.config import update_marked_block
from opencode_config.lib.environment import EnvironmentKind
from opencode_config.lib.paths import UserSpacePaths
from opencode_config.lib.process import CommandResult, run_command


FNM_VERSION = "1.38.1"
PANDOC_VERSION = "3.7.0.2"
PORTABLE_GIT_VERSION = "2.53.0"
AWS_LINUX_INSTALL_URL = "https://awscli.amazonaws.com/v2/install.sh"
AWS_WINDOWS_INSTALL_URL = "https://awscli.amazonaws.com/v2/install.ps1"


class InstallerError(RuntimeError):
    """Erro acionavel durante uma instalacao user-space."""


@dataclass
class InstallContext:
    """Contexto explicito compartilhado pelos instaladores."""

    environment: EnvironmentKind
    paths: UserSpacePaths
    repo_root: Path | None = None
    profile_path: Path | None = None
    current_environment: MutableMapping[str, str] = field(
        default_factory=lambda: dict(os.environ)
    )


@dataclass(frozen=True)
class InstallResult:
    """Resultado de uma tentativa de instalacao."""

    name: str
    success: bool
    changed: bool
    message: str = ""
    error: str = ""


Runner = Callable[..., CommandResult]
Fetcher = Callable[[str, Path], None]
DependencyInstaller = Callable[[InstallContext], InstallResult]


def _path_separator(environment: EnvironmentKind) -> str:
    return ";" if environment is EnvironmentKind.WINDOWS else os.pathsep


def ensure_path_entry(
    path: Path,
    *,
    environment_kind: EnvironmentKind,
    profile_path: Path | None = None,
    environ: MutableMapping[str, str] | None = None,
) -> None:
    """Adiciona um diretorio ao PATH atual e ao perfil, uma unica vez."""

    target = str(path)
    variables = os.environ if environ is None else environ
    separator = _path_separator(environment_kind)
    entries = [
        entry for entry in variables.get("PATH", "").split(separator) if entry
    ]
    if target not in entries:
        variables["PATH"] = separator.join([target, *entries])

    if profile_path is None:
        return

    if environment_kind is EnvironmentKind.WINDOWS:
        content = f'$env:Path = "{target};$env:Path"'
    else:
        content = f'export PATH="{target}:$PATH"'
    update_marked_block(profile_path, "bootstrap-path", content)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _fetch_url(url: str, destination: Path) -> None:
    with urllib.request.urlopen(url) as response, destination.open("wb") as target:
        shutil.copyfileobj(response, target)


def download_file(
    url: str,
    destination: Path,
    *,
    expected_sha256: str | None = None,
    fetcher: Fetcher | None = None,
) -> Path:
    """Baixa um arquivo localmente e verifica SHA-256 quando informado."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    if url.startswith("file://"):
        shutil.copyfile(url[7:], destination)
    elif Path(url).is_file():
        shutil.copyfile(url, destination)
    else:
        (fetcher or _fetch_url)(url, destination)

    if expected_sha256 is not None:
        actual_sha256 = _sha256(destination)
        if actual_sha256.lower() != expected_sha256.lower():
            destination.unlink(missing_ok=True)
            raise InstallerError(
                "SHA256 divergente: "
                f"esperado {expected_sha256}, encontrado {actual_sha256}"
            )
    return destination


def _safe_extract_path(root: Path, member_name: str) -> Path:
    destination = (root / member_name).resolve()
    resolved_root = root.resolve()
    if destination != resolved_root and resolved_root not in destination.parents:
        raise InstallerError(f"Arquivo fora do destino de extracao: {member_name}")
    return destination


def _extract_archive(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as source:
            for member in source.infolist():
                target = _safe_extract_path(destination, member.filename)
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.open(member) as input_file, target.open("wb") as output:
                    shutil.copyfileobj(input_file, output)
        return

    if tarfile.is_tarfile(archive):
        with tarfile.open(archive) as source:
            for member in source.getmembers():
                target = _safe_extract_path(destination, member.name)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                if not member.isfile():
                    raise InstallerError(
                        f"Tipo de arquivo nao suportado no arquivo: {member.name}"
                    )
                target.parent.mkdir(parents=True, exist_ok=True)
                input_file = source.extractfile(member)
                if input_file is None:
                    raise InstallerError(f"Falha ao extrair: {member.name}")
                with input_file, target.open("wb") as output:
                    shutil.copyfileobj(input_file, output)
        return

    raise InstallerError(f"Formato de arquivo nao suportado: {archive.name}")


def _find_file(root: Path, names: Iterable[str]) -> Path:
    candidates = set(names)
    for path in root.rglob("*"):
        if path.is_file() and path.name in candidates:
            return path
    raise InstallerError(
        f"Nenhum dos arquivos esperados foi encontrado em {root}: "
        f"{', '.join(sorted(candidates))}"
    )


def _make_executable(path: Path) -> None:
    if os.name != "nt":
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)


def _execute(
    context: InstallContext,
    command: Iterable[str | os.PathLike[str]],
    *,
    runner: Runner | None = None,
) -> CommandResult:
    args = [os.fspath(argument) for argument in command]
    execute = run_command if runner is None else runner
    try:
        result = execute(args, env=context.current_environment)
    except FileNotFoundError as error:
        raise InstallerError(f"Comando nao encontrado: {args[0]}") from error
    if not result.succeeded:
        detail = result.stderr or result.stdout or "comando falhou"
        raise InstallerError(f"{args[0]} falhou: {detail.strip()}")
    return result


def _result(name: str, message: str = "") -> InstallResult:
    return InstallResult(name=name, success=True, changed=True, message=message)


def install_pipx(
    context: InstallContext,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    """Instala pipx com o interpretador que executa o bootstrap."""

    context.paths.bin_dir.mkdir(parents=True, exist_ok=True)
    _execute(
        context,
        [sys.executable, "-m", "pip", "install", "--user", "pipx"],
        runner=runner,
    )
    ensure_path_entry(
        context.paths.bin_dir,
        environment_kind=context.environment,
        profile_path=context.profile_path,
        environ=context.current_environment,
    )
    return _result("pipx", "pipx instalado em user-space")


def _install_pipx_app(
    context: InstallContext,
    package: str,
    command_name: str,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    _execute(context, ["pipx", "install", package], runner=runner)
    ensure_path_entry(
        context.paths.pipx_bin,
        environment_kind=context.environment,
        profile_path=context.profile_path,
        environ=context.current_environment,
    )
    return _result(command_name, f"{package} instalado via pipx")


def install_docling(
    context: InstallContext,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    return _install_pipx_app(context, "docling", "docling", runner=runner)


def install_crwl(
    context: InstallContext,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    result = _install_pipx_app(context, "crawl4ai", "crwl", runner=runner)
    _execute(context, ["crawl4ai-setup"], runner=runner)
    return InstallResult(
        name=result.name,
        success=True,
        changed=True,
        message="crawl4ai instalado e browser preparado",
    )


def install_npm_global(
    context: InstallContext,
    package: str,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    prefix = context.paths.npm_bin.parent
    prefix.mkdir(parents=True, exist_ok=True)
    _execute(
        context,
        [
            "npm",
            "install",
            "--global",
            "--prefix",
            str(prefix),
            package,
        ],
        runner=runner,
    )
    ensure_path_entry(
        context.paths.npm_bin,
        environment_kind=context.environment,
        profile_path=context.profile_path,
        environ=context.current_environment,
    )
    return _result(package, f"{package} instalado no prefix user-space")


def install_codebase_memory(
    context: InstallContext,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    return install_npm_global(
        context,
        "codebase-memory-mcp",
        runner=runner,
    )


def install_fnm(
    context: InstallContext,
    *,
    url: str | None = None,
    expected_sha256: str | None = None,
    fetcher: Fetcher | None = None,
) -> InstallResult:
    """Instala o binario fnm no diretorio binario user-space."""

    archive_url = url or (
        "https://github.com/Schniz/fnm/releases/download/"
        f"v{FNM_VERSION}/fnm-windows.zip"
        if context.environment is EnvironmentKind.WINDOWS
        else "https://github.com/Schniz/fnm/releases/download/"
        f"v{FNM_VERSION}/fnm-linux.zip"
    )
    with tempfile.TemporaryDirectory(prefix="opencode-fnm-") as temporary:
        archive = Path(temporary) / "fnm.zip"
        extracted = Path(temporary) / "extract"
        download_file(
            archive_url,
            archive,
            expected_sha256=expected_sha256,
            fetcher=fetcher,
        )
        _extract_archive(archive, extracted)
        source = _find_file(extracted, {"fnm", "fnm.exe"})
        context.paths.bin_dir.mkdir(parents=True, exist_ok=True)
        destination = context.paths.bin_dir / source.name
        shutil.copyfile(source, destination)
        _make_executable(destination)
    ensure_path_entry(
        context.paths.bin_dir,
        environment_kind=context.environment,
        profile_path=context.profile_path,
        environ=context.current_environment,
    )
    return _result("fnm", f"fnm instalado em {context.paths.bin_dir}")


def install_node(
    context: InstallContext,
    *,
    fnm_url: str | None = None,
    fnm_expected_sha256: str | None = None,
    fetcher: Fetcher | None = None,
    runner: Runner | None = None,
) -> InstallResult:
    if shutil.which(
        "fnm",
        path=context.current_environment.get("PATH"),
    ) is None:
        install_fnm(
            context,
            url=fnm_url,
            expected_sha256=fnm_expected_sha256,
            fetcher=fetcher,
        )
    _execute(context, ["fnm", "install", "22"], runner=runner)
    return _result("node", "Node.js 22 instalado via fnm")


def _install_binary_archive(
    context: InstallContext,
    *,
    name: str,
    url: str,
    executable_names: set[str],
    expected_sha256: str | None = None,
    fetcher: Fetcher | None = None,
) -> InstallResult:
    with tempfile.TemporaryDirectory(prefix=f"opencode-{name}-") as temporary:
        archive = Path(temporary) / Path(url).name
        extracted = Path(temporary) / "extract"
        download_file(
            url,
            archive,
            expected_sha256=expected_sha256,
            fetcher=fetcher,
        )
        _extract_archive(archive, extracted)
        source = _find_file(extracted, executable_names)
        context.paths.bin_dir.mkdir(parents=True, exist_ok=True)
        destination = context.paths.bin_dir / source.name
        shutil.copyfile(source, destination)
        _make_executable(destination)
    ensure_path_entry(
        context.paths.bin_dir,
        environment_kind=context.environment,
        profile_path=context.profile_path,
        environ=context.current_environment,
    )
    return _result(name, f"{name} instalado em {context.paths.bin_dir}")


def install_pandoc(
    context: InstallContext,
    *,
    url: str | None = None,
    expected_sha256: str | None = None,
    fetcher: Fetcher | None = None,
) -> InstallResult:
    archive_url = url or (
        "https://github.com/jgm/pandoc/releases/download/"
        f"{PANDOC_VERSION}/pandoc-{PANDOC_VERSION}-windows-x86_64.zip"
        if context.environment is EnvironmentKind.WINDOWS
        else "https://github.com/jgm/pandoc/releases/download/"
        f"{PANDOC_VERSION}/pandoc-{PANDOC_VERSION}-linux-amd64.tar.gz"
    )
    return _install_binary_archive(
        context,
        name="pandoc",
        url=archive_url,
        executable_names={"pandoc", "pandoc.exe"},
        expected_sha256=expected_sha256,
        fetcher=fetcher,
    )


def install_git(
    context: InstallContext,
    *,
    url: str | None = None,
    expected_sha256: str | None = None,
    runner: Runner | None = None,
    fetcher: Fetcher | None = None,
) -> InstallResult:
    if context.environment is not EnvironmentKind.WINDOWS:
        return InstallResult(
            name="git",
            success=True,
            changed=False,
            message="Git e pre-requisito do ambiente Linux",
        )

    archive_url = url or (
        "https://github.com/git-for-windows/git/releases/download/"
        f"v{PORTABLE_GIT_VERSION}.windows.1/"
        f"PortableGit-{PORTABLE_GIT_VERSION}-64-bit.7z.exe"
    )
    with tempfile.TemporaryDirectory(prefix="opencode-git-") as temporary:
        archive = Path(temporary) / Path(archive_url).name
        download_file(
            archive_url,
            archive,
            expected_sha256=expected_sha256,
            fetcher=fetcher,
        )
        install_dir = context.paths.data_dir / "PortableGit"
        install_dir.mkdir(parents=True, exist_ok=True)
        if zipfile.is_zipfile(archive) or tarfile.is_tarfile(archive):
            _extract_archive(archive, install_dir)
        else:
            _execute(
                context,
                [archive, "-y", f"-o{install_dir}"],
                runner=runner,
            )
        ensure_path_entry(
            install_dir / "cmd",
            environment_kind=context.environment,
            profile_path=context.profile_path,
            environ=context.current_environment,
        )
    return _result("git", f"PortableGit instalado em {install_dir}")


def install_playwright(
    context: InstallContext,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    install_npm_global(context, "@playwright/test", runner=runner)
    _execute(
        context,
        ["npx", "--yes", "playwright", "install", "chromium"],
        runner=runner,
    )
    return _result("playwright", "Playwright e Chromium instalados")


def install_pytest(
    context: InstallContext,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    if context.repo_root is None:
        raise InstallerError("Raiz do repositorio necessaria para criar .venv")
    venv_path = context.repo_root / ".venv"
    _execute(
        context,
        [sys.executable, "-m", "venv", venv_path],
        runner=runner,
    )
    requirements = context.repo_root / "requirements-dev.txt"
    if requirements.is_file():
        python_name = "Scripts/python.exe" if (
            context.environment is EnvironmentKind.WINDOWS
        ) else "bin/python"
        _execute(
            context,
            [venv_path / python_name, "-m", "pip", "install", "-r", requirements],
            runner=runner,
        )
    return _result("pytest", f".venv criada em {venv_path}")


def install_aws_cli(
    context: InstallContext,
    *,
    target_version: str | None = None,
    current_version: str | None = None,
    script_url: str | None = None,
    expected_sha256: str | None = None,
    runner: Runner | None = None,
    fetcher: Fetcher | None = None,
) -> InstallResult:
    """Executa o instalador oficial da AWS sempre em modo user-local."""

    if target_version is not None and current_version == target_version:
        return InstallResult(
            name="aws-cli",
            success=True,
            changed=False,
            message="AWS CLI ja esta na versao alvo",
        )

    linux = context.environment is not EnvironmentKind.WINDOWS
    source_url = script_url or (AWS_LINUX_INSTALL_URL if linux else AWS_WINDOWS_INSTALL_URL)
    suffix = ".sh" if linux else ".ps1"
    with tempfile.TemporaryDirectory(prefix="opencode-aws-") as temporary:
        script = Path(temporary) / f"install{suffix}"
        download_file(
            source_url,
            script,
            expected_sha256=expected_sha256,
            fetcher=fetcher,
        )
        if linux:
            command: list[str | os.PathLike[str]] = [
                "bash",
                script,
                "--install-dir",
                context.paths.data_dir / "aws-cli",
                "--bin-dir",
                context.paths.bin_dir,
                "--update",
                "--quiet",
            ]
            if target_version is not None:
                command.extend(["--version", target_version])
        else:
            command = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                script,
                "-Quiet",
            ]
            if target_version is not None:
                command.extend(["-Version", target_version])
        _execute(context, command, runner=runner)

    if linux:
        ensure_path_entry(
            context.paths.bin_dir,
            environment_kind=context.environment,
            profile_path=context.profile_path,
            environ=context.current_environment,
        )
    return _result("aws-cli", "AWS CLI instalado em user-space")


def _manual_prerequisite(name: str) -> DependencyInstaller:
    def install(_context: InstallContext) -> InstallResult:
        return InstallResult(
            name=name,
            success=False,
            changed=False,
            error=f"{name} e pre-requisito; instale manualmente",
        )

    return install


INSTALLERS: Mapping[str, DependencyInstaller] = {
    "python": _manual_prerequisite("python"),
    "node": install_node,
    "pipx": install_pipx,
    "crwl": install_crwl,
    "docling": install_docling,
    "codebase-memory-mcp": install_codebase_memory,
    "pandoc": install_pandoc,
    "git": install_git,
    "playwright": install_playwright,
    "pytest": install_pytest,
    "aws-cli": install_aws_cli,
}


def install_dependencies(
    names: Iterable[str],
    context: InstallContext,
    *,
    installers: Mapping[str, DependencyInstaller] = INSTALLERS,
) -> tuple[InstallResult, ...]:
    """Instala todos os selecionados, reportando falhas sem abortar o lote."""

    results: list[InstallResult] = []
    for name in names:
        installer = installers.get(name)
        if installer is None:
            results.append(
                InstallResult(
                    name=name,
                    success=False,
                    changed=False,
                    error=f"Instalador nao registrado: {name}",
                )
            )
            continue
        try:
            results.append(installer(context))
        except (InstallerError, OSError) as error:
            results.append(
                InstallResult(
                    name=name,
                    success=False,
                    changed=False,
                    error=str(error),
                )
            )
    return tuple(results)
