"""Instaladores zero-admin e utilitarios de download do bootstrap."""

from collections.abc import Callable, Iterable, Mapping, MutableMapping
from dataclasses import dataclass, field
import hashlib
import io
import os
from pathlib import Path
import shutil
import stat
import sys
import sysconfig
import tarfile
import tempfile
import urllib.request
import zipfile

from opencode_config.lib.config import update_marked_block
from opencode_config.lib.environment import EnvironmentKind
from opencode_config.lib.paths import UserSpacePaths
from opencode_config.lib.process import CommandResult, run_command
from opencode_config.lib.versions import fnm_node_bin_dir

from ..libgomp import (
    LIBGOMP_ARCHITECTURE,
    LIBGOMP_LIBRARY_NAME,
    LIBGOMP_PACKAGE_SHA256,
    LIBGOMP_PACKAGE_URL,
    LIBGOMP_VERSION,
    runtime_directory,
    runtime_is_valid,
    write_runtime_metadata,
)


FNM_VERSION = "1.38.1"
PANDOC_VERSION = "3.7.0.2"
PORTABLE_GIT_VERSION = "2.53.0"
CODEBASE_MEMORY_VERSION = "0.9.0"
AWS_LINUX_INSTALL_URL = "https://awscli.amazonaws.com/v2/install.sh"
AWS_WINDOWS_INSTALL_URL = "https://awscli.amazonaws.com/v2/install.ps1"
INSTALL_COMMAND_TIMEOUT_SECONDS = 1800


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
    persist_paths: bool = True


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
    return ";" if environment is EnvironmentKind.WINDOWS else ":"


def _path_value(environ: Mapping[str, str]) -> str:
    """Retorna PATH sem depender da capitalização usada pelo sistema."""

    return next(
        (
            value
            for name, value in environ.items()
            if name.casefold() == "path"
        ),
        "",
    )


def _same_path(
    first: str,
    second: str,
    environment: EnvironmentKind,
) -> bool:
    if environment is EnvironmentKind.WINDOWS:
        return first.casefold() == second.casefold()
    return first == second


def _persist_windows_user_path(target: str) -> None:
    """Persiste um caminho no PATH do usuário sem exigir elevação."""

    if os.name != "nt":
        return

    import winreg

    access = winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE
    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER,
        "Environment",
        0,
        access,
    ) as key:
        try:
            current, value_type = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current = ""
            value_type = winreg.REG_EXPAND_SZ

        entries = [
            entry for entry in str(current).split(";") if entry
        ]
        if any(entry.casefold() == target.casefold() for entry in entries):
            return

        winreg.SetValueEx(
            key,
            "Path",
            0,
            value_type,
            ";".join([target, *entries]),
        )


def ensure_path_entry(
    path: Path,
    *,
    environment_kind: EnvironmentKind,
    profile_path: Path | None = None,
    environ: MutableMapping[str, str] | None = None,
    persist: bool = True,
) -> None:
    """Adiciona um diretorio ao PATH atual e ao perfil, uma unica vez."""

    target = str(path)
    variables = os.environ if environ is None else environ
    separator = _path_separator(environment_kind)
    path_key = next(
        (
            name
            for name in variables
            if name.casefold() == "path"
        ),
        "PATH",
    )
    entries = [
        entry for entry in variables.get(path_key, "").split(separator) if entry
    ]
    if not any(
        _same_path(entry, target, environment_kind)
        for entry in entries
    ):
        variables[path_key] = separator.join([target, *entries])
    for name in list(variables):
        if name.casefold() == "path" and name != path_key:
            del variables[name]

    if persist and environment_kind is EnvironmentKind.WINDOWS:
        _persist_windows_user_path(target)

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


def _read_deb_members(package: Path) -> dict[str, bytes]:
    """Read ar members from a Debian package using only the stdlib."""

    payload = package.read_bytes()
    if not payload.startswith(b"!<arch>\n"):
        raise InstallerError("pacote libgomp nao e um arquivo Debian valido")
    members: dict[str, bytes] = {}
    offset = 8
    while offset < len(payload):
        header = payload[offset : offset + 60]
        if len(header) != 60 or header[58:60] != b"`\n":
            raise InstallerError("cabecalho ar invalido no pacote libgomp")
        name = header[:16].decode("ascii").strip().rstrip("/")
        try:
            size = int(header[48:58].decode("ascii").strip())
        except ValueError as error:
            raise InstallerError("tamanho invalido no pacote libgomp") from error
        start = offset + 60
        end = start + size
        if end > len(payload):
            raise InstallerError("membro truncado no pacote libgomp")
        members[name] = payload[start:end]
        offset = end + (size % 2)
    return members


def _deb_control_fields(control_archive: bytes) -> dict[str, str]:
    with tarfile.open(fileobj=io.BytesIO(control_archive), mode="r:*") as archive:
        control = next(
            (
                member
                for member in archive.getmembers()
                if member.isfile() and member.name.rsplit("/", 1)[-1] == "control"
            ),
            None,
        )
        if control is None:
            raise InstallerError("controle ausente no pacote libgomp")
        source = archive.extractfile(control)
        if source is None:
            raise InstallerError("nao foi possivel ler o controle do libgomp")
        fields: dict[str, str] = {}
        for line in source.read().decode("utf-8").splitlines():
            if ":" in line:
                name, value = line.split(":", 1)
                fields[name.strip()] = value.strip()
        return fields


def _extract_libgomp_from_deb(package: Path, destination: Path) -> None:
    members = _read_deb_members(package)
    control_name = next(
        (name for name in members if name.startswith("control.tar")),
        None,
    )
    data_name = next((name for name in members if name.startswith("data.tar")), None)
    if control_name is None or data_name is None:
        raise InstallerError("controle ou dados ausentes no pacote libgomp")
    fields = _deb_control_fields(members[control_name])
    if (
        fields.get("Package") != "libgomp1"
        or fields.get("Version") != LIBGOMP_VERSION
        or fields.get("Architecture") != LIBGOMP_ARCHITECTURE
    ):
        raise InstallerError(
            "metadados inesperados no pacote libgomp: "
            f"{fields.get('Package')} {fields.get('Version')} "
            f"{fields.get('Architecture')}"
        )
    with tarfile.open(
        fileobj=io.BytesIO(members[data_name]),
        mode="r:*",
    ) as archive:
        source_member = next(
            (
                member
                for member in archive.getmembers()
                if member.isfile() and member.name.endswith(
                    f"/{LIBGOMP_LIBRARY_NAME}"
                )
            ),
            None,
        )
        if source_member is None:
            raise InstallerError(
                f"{LIBGOMP_LIBRARY_NAME} ausente no pacote libgomp"
            )
        source = archive.extractfile(source_member)
        if source is None:
            raise InstallerError("nao foi possivel extrair libgomp.so.1")
        destination.mkdir(parents=True, exist_ok=True)
        library = destination / LIBGOMP_LIBRARY_NAME
        with source, library.open("wb") as output:
            shutil.copyfileobj(source, output)
        _make_executable(library)
    (destination / "libgomp.so.1").symlink_to(LIBGOMP_LIBRARY_NAME)
    write_runtime_metadata(destination)


def install_libgomp_runtime(
    context: InstallContext,
    *,
    fetcher: Fetcher | None = None,
) -> InstallResult:
    """Provision the fixed x86_64 libgomp copy without touching system paths."""

    if context.environment not in {EnvironmentKind.LINUX, EnvironmentKind.WSL}:
        return InstallResult(
            name="libgomp-runtime",
            success=True,
            changed=False,
            message="runtime libgomp nao se aplica ao Windows",
        )
    home = context.paths.home
    if runtime_is_valid(home):
        return InstallResult(
            name="libgomp-runtime",
            success=True,
            changed=False,
            message=f"runtime libgomp ja valida em {runtime_directory(home)}",
        )
    runtime_root = runtime_directory(home).parent
    runtime_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".libgomp-install-",
        dir=runtime_root,
    ) as temporary:
        package = Path(temporary) / "libgomp.deb"
        extracted = Path(temporary) / "runtime"
        download_file(
            LIBGOMP_PACKAGE_URL,
            package,
            expected_sha256=LIBGOMP_PACKAGE_SHA256,
            fetcher=fetcher,
        )
        _extract_libgomp_from_deb(package, extracted)
        target = runtime_directory(home)
        if target.exists():
            shutil.rmtree(target)
        os.replace(extracted, target)
    if not runtime_is_valid(home):
        shutil.rmtree(target, ignore_errors=True)
        raise InstallerError(
            "runtime libgomp extraida, mas falhou a validacao ELF/SHA-256"
        )
    return InstallResult(
        name="libgomp-runtime",
        success=True,
        changed=True,
        message=f"runtime libgomp instalada em {target}",
    )


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
    timeout: float | None = INSTALL_COMMAND_TIMEOUT_SECONDS,
    extra_env: Mapping[str, str] | None = None,
) -> CommandResult:
    args = [os.fspath(argument) for argument in command]
    execute = run_command if runner is None else runner
    if runner is None and context.environment is EnvironmentKind.WINDOWS:
        executable = shutil.which(
            args[0],
            path=_path_value(context.current_environment),
        )
        if executable is not None:
            args[0] = executable
    env = context.current_environment
    if extra_env:
        env = {**env, **extra_env}
    try:
        result = execute(
            args,
            env=env,
            timeout=timeout,
        )
    except FileNotFoundError as error:
        raise InstallerError(f"Comando nao encontrado: {args[0]}") from error
    if result.timed_out:
        raise InstallerError(
            f"{args[0]} excedeu timeout de {timeout:g}s"
        )
    if not result.succeeded:
        detail = result.stderr or result.stdout or "comando falhou"
        raise InstallerError(f"{args[0]} falhou: {detail.strip()}")
    return result


def _result(name: str, message: str = "") -> InstallResult:
    return InstallResult(name=name, success=True, changed=True, message=message)


def _python_user_scripts_path(
    environment: EnvironmentKind,
) -> Path | None:
    if environment is not EnvironmentKind.WINDOWS:
        return None

    try:
        scripts = sysconfig.get_path("scripts", scheme="nt_user")
    except (KeyError, TypeError, ValueError):
        return None
    return Path(scripts) if scripts else None


def _pipx_bin_path(context: InstallContext) -> Path:
    configured = context.current_environment.get("PIPX_BIN_DIR")
    return Path(configured) if configured else context.paths.pipx_bin


def _ensure_pipx_bin_path(context: InstallContext) -> Path:
    path = _pipx_bin_path(context)
    ensure_path_entry(
        path,
        environment_kind=context.environment,
        profile_path=context.profile_path,
        environ=context.current_environment,
        persist=context.persist_paths,
    )
    return path


def _require_pipx_entrypoint(
    context: InstallContext,
    command_name: str,
    pipx_bin: Path,
) -> None:
    if shutil.which(
        command_name,
        path=_path_value(context.current_environment),
    ) is None:
        raise InstallerError(
            f"{command_name} nao foi exposto pelo pipx em {pipx_bin}"
        )


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
    user_scripts = _python_user_scripts_path(context.environment)
    if user_scripts is not None:
        ensure_path_entry(
            user_scripts,
            environment_kind=context.environment,
            profile_path=context.profile_path,
            environ=context.current_environment,
            persist=context.persist_paths,
        )
    _ensure_pipx_bin_path(context)
    ensure_path_entry(
        context.paths.bin_dir,
        environment_kind=context.environment,
        profile_path=context.profile_path,
        environ=context.current_environment,
        persist=context.persist_paths,
    )
    if shutil.which(
        "pipx",
        path=_path_value(context.current_environment),
    ) is None:
        raise InstallerError(
            "pipx foi instalado, mas o executavel nao ficou disponivel "
            "no PATH do bootstrap"
        )
    return _result("pipx", "pipx instalado em user-space")


def _install_pipx_app(
    context: InstallContext,
    package: str,
    command_name: str,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    pipx_bin = _ensure_pipx_bin_path(context)
    _execute(
        context,
        ["pipx", "install", "--force", package],
        runner=runner,
    )
    _require_pipx_entrypoint(context, command_name, pipx_bin)
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
    pipx_bin = _ensure_pipx_bin_path(context)
    result = _install_pipx_app(context, "crawl4ai", "crwl", runner=runner)
    _require_pipx_entrypoint(context, "crawl4ai-setup", pipx_bin)
    setup = _execute(context, ["crawl4ai-setup"], runner=runner)
    setup_output = f"{setup.stdout}\n{setup.stderr}"
    if "failed to install browsers" in setup_output.casefold():
        raise InstallerError(
            "crawl4ai-setup declarou falha na instalacao dos browsers: "
            f"{setup_output.strip()}"
        )
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
    prefix = (
        context.paths.npm_bin
        if context.environment is EnvironmentKind.WINDOWS
        else context.paths.npm_bin.parent
    )
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
        persist=context.persist_paths,
    )
    return _result(package, f"{package} instalado no prefix user-space")


def fix_chrondb_lib(home: Path) -> None:
    """Normaliza a estrutura nativa extraida pelo codebase-memory-mcp."""

    chrondb_lib = Path(home) / ".chrondb" / "lib"
    temporary = chrondb_lib / ".tmp-extract-runtime"
    if not temporary.is_dir() or not (temporary / "libchrondb.so").is_file():
        return

    for source in temporary.iterdir():
        shutil.move(str(source), str(chrondb_lib / source.name))
    temporary.rmdir()


def install_codebase_memory(
    context: InstallContext,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    result = install_npm_global(
        context,
        f"codebase-memory-mcp@{CODEBASE_MEMORY_VERSION}",
        runner=runner,
    )
    _execute(
        context,
        ["codebase-memory-mcp", "config", "set", "auto_index", "true"],
        runner=runner,
    )
    fix_chrondb_lib(context.paths.home)
    return InstallResult(
        name="codebase-memory-mcp",
        success=True,
        changed=True,
        message=f"{result.message}; auto-index habilitado",
    )


def install_opencode_config(
    context: InstallContext,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    """Instala os entry points deste repositorio via pipx."""

    if context.repo_root is None:
        raise InstallerError("Raiz do repositorio necessaria para instalar o pacote")

    pipx_bin = _ensure_pipx_bin_path(context)
    _execute(
        context,
        [
            "pipx",
            "install",
            "--force",
            "--editable",
            context.repo_root,
        ],
        runner=runner,
    )
    _require_pipx_entrypoint(context, "opencode-config-check", pipx_bin)
    return _result(
        "opencode-config",
        "entry points do repositorio instalados via pipx",
    )


def install_copilot(
    context: InstallContext,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    if context.environment is not EnvironmentKind.WINDOWS:
        raise InstallerError("Copilot CLI user-space e suportado somente no Windows")

    result = install_npm_global(
        context,
        "@github/copilot",
        runner=runner,
    )
    copilot_path = _path_value(context.current_environment)
    if shutil.which("copilot", path=copilot_path) is None:
        raise InstallerError(
            f"copilot nao foi exposto pelo npm em {context.paths.npm_bin}"
        )
    return InstallResult(
        name="copilot",
        success=True,
        changed=result.changed,
        message="Copilot CLI instalado no prefix user-space",
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
        persist=context.persist_paths,
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
        path=_path_value(context.current_environment),
    ) is None:
        install_fnm(
            context,
            url=fnm_url,
            expected_sha256=fnm_expected_sha256,
            fetcher=fetcher,
        )
    _execute(context, ["fnm", "install", "22"], runner=runner)
    node_bin = fnm_node_bin_dir(
        context.paths.home,
        context.current_environment,
        major=22,
    )
    if node_bin is None:
        raise InstallerError("fnm nao expoe o diretorio bin do Node.js 22")
    ensure_path_entry(
        node_bin,
        environment_kind=context.environment,
        profile_path=context.profile_path,
        environ=context.current_environment,
        persist=context.persist_paths,
    )
    return _result("node", "Node.js 22 instalado via fnm")


def _rename_install_result(
    result: InstallResult,
    name: str,
) -> InstallResult:
    return InstallResult(
        name=name,
        success=result.success,
        changed=result.changed,
        message=result.message,
        error=result.error,
    )


def _command_available(
    context: InstallContext,
    command: str,
) -> bool:
    return shutil.which(
        command,
        path=_path_value(context.current_environment),
    ) is not None


def install_npm(
    context: InstallContext,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    return _install_node_entrypoint(context, "npm", runner=runner)


def install_npx(
    context: InstallContext,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    return _install_node_entrypoint(context, "npx", runner=runner)


def _install_node_entrypoint(
    context: InstallContext,
    command: str,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    if _command_available(context, command):
        return _result(command, f"{command} ja disponivel")

    result = _rename_install_result(
        install_node(context, runner=runner),
        command,
    )
    if not result.success:
        return result
    if _command_available(context, command):
        return result
    return InstallResult(
        name=command,
        success=False,
        changed=result.changed,
        message=result.message,
        error=f"{command} nao ficou disponivel apos instalar Node.js",
    )


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
        persist=context.persist_paths,
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
            persist=context.persist_paths,
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


def _venv_python_path(context: InstallContext) -> Path:
    if context.repo_root is None:
        raise InstallerError("Raiz do repositorio necessaria para usar .venv")
    python_name = "Scripts/python.exe" if (
        context.environment is EnvironmentKind.WINDOWS
    ) else "bin/python"
    return context.repo_root / ".venv" / python_name


def is_pytest_environment_ready(context: InstallContext) -> bool:
    """Verifica se a virtualenv consegue importar o pacote do repositorio."""

    if context.repo_root is None:
        return False
    python_path = _venv_python_path(context)
    if not python_path.is_file():
        return False
    environment = {
        name: value
        for name, value in context.current_environment.items()
        if name.casefold() not in {"pythonpath", "pythonhome"}
    }
    result = run_command(
        [
            python_path,
            "-c",
            "import opencode_config; import pytest",
        ],
        cwd=context.repo_root,
        env=environment,
    )
    return result.succeeded


def install_pytest(
    context: InstallContext,
    *,
    runner: Runner | None = None,
) -> InstallResult:
    if context.repo_root is None:
        raise InstallerError("Raiz do repositorio necessaria para criar .venv")
    if is_pytest_environment_ready(context):
        return InstallResult(
            name="pytest",
            success=True,
            changed=False,
            message=f".venv ja configurada em {context.repo_root / '.venv'}",
        )
    venv_path = context.repo_root / ".venv"
    python_path = _venv_python_path(context)
    _execute(
        context,
        [sys.executable, "-m", "venv", venv_path],
        runner=runner,
    )
    requirements = context.repo_root / "requirements-dev.txt"
    if requirements.is_file():
        _execute(
            context,
            [python_path, "-m", "pip", "install", "-r", requirements],
            runner=runner,
        )
    _execute(
        context,
        [
            python_path,
            "-m",
            "pip",
            "install",
            "--editable",
            context.repo_root,
        ],
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
    if linux and shutil.which(
        "unzip",
        path=_path_value(context.current_environment),
    ) is None:
        raise InstallerError(
            "unzip e pre-requisito do instalador oficial da AWS CLI v2 "
            "(ele extrai o bundle interno). Instale com o gerenciador da "
            "sua distro, por exemplo: sudo apt install unzip"
        )
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
            # O install.sh oficial (v2) aceita apenas --version, -s/--system,
            # -q/--quiet e -h/--help. O local de instalacao user-local e
            # controlado pelas variaveis de ambiente XDG_DATA_HOME (raiz; o
            # binario fica em $XDG_DATA_HOME/aws-cli) e XDG_BIN_HOME (onde os
            # symlinks aws/aws_completer sao criados). --update e aplicado
            # automaticamente quando o instalador detecta uma versao anterior.
            command: list[str | os.PathLike[str]] = [
                "bash",
                script,
                "--quiet",
            ]
            if target_version is not None:
                command.extend(["--version", target_version])
            aws_env: dict[str, str] = {
                "XDG_DATA_HOME": os.fspath(context.paths.data_dir),
                "XDG_BIN_HOME": os.fspath(context.paths.bin_dir),
            }
            _execute(context, command, runner=runner, extra_env=aws_env)
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
            persist=context.persist_paths,
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
    "npm": install_npm,
    "npx": install_npx,
    "pipx": install_pipx,
    "crwl": install_crwl,
    "docling": install_docling,
    "codebase-memory-mcp": install_codebase_memory,
    "opencode-config": install_opencode_config,
    "copilot": install_copilot,
    "pandoc": install_pandoc,
    "git": install_git,
    "playwright": install_playwright,
    "pytest": install_pytest,
    "aws-cli": install_aws_cli,
    "libgomp-runtime": install_libgomp_runtime,
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
