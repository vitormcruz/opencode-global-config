"""Provisionamento e rollback user-space do ai-memory."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import queue
import shutil
import socket
import subprocess  # nosec B404 - comandos Docker e wrapper fixados no código
import tempfile
import threading
import time
from typing import TextIO
import urllib.request

from opencode_config.bootstrap.installers import (
    InstallContext,
    InstallerError,
    download_file,
)
from opencode_config.lib.environment import EnvironmentKind
from opencode_config.lib.paths import UserSpacePaths
from opencode_config.lib.process import CommandResult
from opencode_config.lib.sync import backup_copy, backup_move

AI_MEMORY_IMAGE_TAG = "akitaonrails/ai-memory:latest"
AI_MEMORY_IMAGE_MANIFEST_SHA256 = (
    "a626d115e0350afe934954c02c9064d30b708c58316763a9c6674ef5d0c8e3d9"
)
AI_MEMORY_IMAGE_LINUX_AMD64_SHA256 = (
    "5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e"
)
AI_MEMORY_IMAGE = f"{AI_MEMORY_IMAGE_TAG}@sha256:{AI_MEMORY_IMAGE_LINUX_AMD64_SHA256}"
AI_MEMORY_NETWORK = "ai-memory-internal"
AI_MEMORY_HOST = "127.0.0.1"
AI_MEMORY_PORT = 49374
AI_MEMORY_MCP_URL = "http://127.0.0.1:49374/mcp"
AI_MEMORY_DATA_NAME = "ai-memory"
AI_MEMORY_READY_MARKER = ".bootstrap-provisioned"
AI_MEMORY_NETWORK_MARKER = ".bootstrap-network-created"
AI_MEMORY_WRAPPER_VERSION = "v2.4.1"
AI_MEMORY_WRAPPER_URL = (
    "https://github.com/akitaonrails/ai-memory/releases/download/"
    f"{AI_MEMORY_WRAPPER_VERSION}/ai-memory-wrapper"
)
AI_MEMORY_WRAPPER_SHA256 = (
    "49c965a0319dbe9c525d552a9a4c8b3464e5dd278e36d5dc7a03edee8b5502e6"
)
AI_MEMORY_WINDOWS_WRAPPERS = (
    (
        "ai-memory-wrapper.cmd",
        "6a91c44ffa2e85d3b5a6ce26a4ccff0286b91d08d276d2bb4d47c346b036ee8b",
    ),
    (
        "ai-memory-wrapper.ps1",
        "f4912fadae3f7aa0fa2f1612b40c8a915462330c217a6e7780cdd7be5ce5b068",
    ),
)
AI_MEMORY_COMMAND_TIMEOUT_SECONDS = 1800
# Docker pull emits layer progress. Two idle minutes allow registry pauses;
# the existing installer ceiling bounds the total without hiding progress.
AI_MEMORY_COMMAND_IDLE_TIMEOUT_SECONDS = 120
_DOWNLOAD_IDLE_TIMEOUT_SECONDS = 30
_MAX_WRAPPER_BYTES = 1024 * 1024

Runner = Callable[..., CommandResult]
Fetcher = Callable[[str, Path], None]
PortProbe = Callable[[str, int], bool]


class AiMemoryProvisionError(RuntimeError):
    """Falha acionável no provisionamento do ai-memory."""


@dataclass(frozen=True)
class AiMemoryProvisionResult:
    """Estado final do provisionamento do ai-memory."""

    provisioned: bool
    changed: bool
    message: str
    failed: bool = False


def ai_memory_data_directory(paths: UserSpacePaths) -> Path:
    """Retorna o diretório persistente do ai-memory no espaço do usuário."""

    return paths.home / ".local" / "share" / AI_MEMORY_DATA_NAME


def ai_memory_ready_marker(paths: UserSpacePaths) -> Path:
    """Retorna o marcador gravado somente após provisionamento completo."""

    return ai_memory_data_directory(paths) / AI_MEMORY_READY_MARKER


def is_ai_memory_provisioned(home: Path) -> bool:
    """Informa se o bootstrap concluiu a integração para esta home."""

    return ai_memory_ready_marker(_paths_for_home(home)).is_file()


def filter_ai_memory_config(content: str) -> str:
    """Remove apenas o servidor ai-memory e preserva os demais campos JSON."""

    try:
        configuration = json.loads(content)
    except json.JSONDecodeError as error:
        raise AiMemoryProvisionError(
            "JSON inválido na configuração OpenCode; o arquivo foi preservado."
        ) from error
    if not isinstance(configuration, dict):
        raise AiMemoryProvisionError(
            "A raiz da configuração OpenCode precisa ser um objeto JSON."
        )
    servers = configuration.get("mcp")
    if isinstance(servers, dict):
        servers.pop("ai-memory", None)
        if not servers:
            configuration.pop("mcp", None)
    return json.dumps(configuration, indent=4, ensure_ascii=False) + "\n"


def provision_ai_memory(
    context: InstallContext,
    *,
    runner: Runner | None = None,
    fetcher: Fetcher | None = None,
    port_is_in_use: PortProbe | None = None,
    output: TextIO | None = None,
) -> AiMemoryProvisionResult:
    """Provisiona wrapper, servidor, volume e hooks antes de habilitar MCP."""

    stream = output
    try:
        network_was_created = _marker_created_network(context.paths)
        _remove_ready_marker(context.paths)
        _backup_legacy_jsonc(context.paths.home)
    except OSError as error:
        return _deactivate_incomplete_setup(
            context,
            f"Não foi possível preparar a configuração: {error}",
            output=stream,
        )

    docker = _docker_executable(context)
    if docker is None:
        return _deactivate_incomplete_setup(
            context,
            _docker_installation_guidance(context.environment),
            output=stream,
            failed=False,
        )

    execute = run_streaming_command if runner is None else runner
    try:
        _require_docker_daemon(docker, context, execute, stream)
        data_directory = ai_memory_data_directory(context.paths)
        network_created_now = _ensure_container_network(
            docker,
            context,
            execute,
            stream,
        )
        if network_created_now:
            _write_network_marker(context.paths)
        network_is_owned = network_was_created or network_created_now
        container = _inspect_container(docker, context, execute, stream)
        if container is None:
            probe = _port_is_in_use if port_is_in_use is None else port_is_in_use
            if probe(AI_MEMORY_HOST, AI_MEMORY_PORT):
                raise AiMemoryProvisionError(
                    f"A porta {AI_MEMORY_HOST}:{AI_MEMORY_PORT} já está ocupada. "
                    "Identifique o processo e libere a porta antes de reexecutar."
                )
        else:
            _validate_existing_container(
                container,
                ai_memory_data_directory(context.paths),
                docker,
                context,
                execute,
                stream,
            )

        _secure_data_directory(data_directory, context.environment)
        _ensure_wrappers(context, fetcher)
        if container is None:
            _ensure_image(docker, context, execute, stream)
            _run_server(docker, data_directory, context, execute, stream)
        else:
            state = container.get("State", {})
            if isinstance(state, dict) and not state.get("Running"):
                _require_success(
                    _execute(
                        [docker, "start", AI_MEMORY_DATA_NAME],
                        context,
                        execute,
                        stream,
                    ),
                    "Reinício do container ai-memory",
                )
        _verify_container_running(docker, context, execute, stream)
        plugin_hash_before = _sha256_file(_plugin_path(context.paths.home))
        _install_hooks(context, execute, stream)
        plugin_path = _plugin_path(context.paths.home)
        if not plugin_path.is_file():
            raise AiMemoryProvisionError(
                f"O instalador oficial não gerou o plugin esperado: {plugin_path}"
            )
        plugin_hash_after = _sha256_file(plugin_path)
        if plugin_hash_before and plugin_hash_before != plugin_hash_after:
            _write(
                stream,
                "AVISO: o hash de ai-memory.ts mudou após install-hooks; "
                f"anote o drift do gerador ({plugin_hash_before} -> "
                f"{plugin_hash_after}).",
            )

        _write_ready_marker(context.paths, network_is_owned)
        message = "ai-memory provisionado; declaração MCP habilitada nos harnesses."
        _write(stream, message)
        return AiMemoryProvisionResult(True, True, message)
    except (AiMemoryProvisionError, InstallerError, OSError, ValueError) as error:
        return _deactivate_incomplete_setup(context, str(error), output=stream)


def disable_ai_memory(
    context: InstallContext,
    *,
    reason: str,
    output: TextIO | None = None,
) -> AiMemoryProvisionResult:
    """Remove qualquer estado ativo sem iniciar downloads ou containers."""

    return _deactivate_incomplete_setup(
        context,
        reason,
        output=output,
        failed=False,
    )


def rollback_ai_memory(
    context: InstallContext,
    *,
    runner: Runner | None = None,
    output: TextIO | None = None,
) -> AiMemoryProvisionResult:
    """Desativa os harnesses e remove o servidor sem apagar os dados."""

    execute = run_streaming_command if runner is None else runner
    errors: list[str] = []
    try:
        network_is_owned = _marker_created_network(context.paths)
        _remove_ready_marker(context.paths)
    except OSError as error:
        network_is_owned = False
        errors.append(f"Não foi possível remover o marcador: {error}")
    docker = _docker_executable(context)
    if docker is None:
        errors.append(
            "Docker ausente; instale/inicie o runtime e reexecute o rollback "
            "para parar e remover o container."
        )
    else:
        try:
            container = _inspect_container(docker, context, execute, output)
        except AiMemoryProvisionError as error:
            errors.append(str(error))
            container = None
        if container is not None:
            if container.get("State", {}).get("Running"):
                _run_cleanup_command(
                    [docker, "stop", AI_MEMORY_DATA_NAME],
                    context,
                    execute,
                    errors,
                )
            _run_cleanup_command(
                [docker, "rm", AI_MEMORY_DATA_NAME],
                context,
                execute,
                errors,
            )
        if network_is_owned:
            existing_errors = len(errors)
            _run_cleanup_command(
                [docker, "network", "rm", AI_MEMORY_NETWORK],
                context,
                execute,
                errors,
            )
            if len(errors) == existing_errors:
                try:
                    _remove_network_marker(context.paths)
                except OSError as error:
                    errors.append(str(error))

    cleanup_steps = (
        lambda: _remove_generated_plugin(context.paths.home),
        lambda: _remove_opencode_server(context.paths.home),
        lambda: _remove_copilot_server(context.paths.home),
        lambda: _remove_wrapper_artifacts(context.paths),
        lambda: _restore_legacy_jsonc(context.paths.home),
    )
    for cleanup in cleanup_steps:
        try:
            cleanup()
        except (AiMemoryProvisionError, OSError) as error:
            errors.append(str(error))
    data_directory = ai_memory_data_directory(context.paths)
    if data_directory.is_dir():
        _write(output, f"Dados preservados em {data_directory}.")

    if errors:
        message = "Rollback parcial: " + " | ".join(errors)
        _write(output, message)
        return AiMemoryProvisionResult(False, True, message, failed=True)

    message = "Rollback concluído; o volume de dados foi preservado."
    _write(output, message)
    return AiMemoryProvisionResult(False, True, message)


def _paths_for_home(home: Path) -> UserSpacePaths:
    return UserSpacePaths(
        home=home,
        config_dir=home / ".config",
        data_dir=home / ".local" / "share",
        bin_dir=home / ".local" / "bin",
        pipx_bin=home / ".local" / "bin",
        npm_bin=home / ".local" / "bin",
    )


def _docker_executable(context: InstallContext) -> str | None:
    return shutil.which("docker", path=context.current_environment.get("PATH"))


def _docker_installation_guidance(environment: EnvironmentKind) -> str:
    if environment is EnvironmentKind.WINDOWS:
        return (
            "Docker ausente. Instale Docker Desktop em escopo do usuário, "
            "inicie o runtime e reexecute o bootstrap; não use sudo."
        )
    if environment is EnvironmentKind.WSL:
        return (
            "Docker ausente. Instale Docker Desktop no Windows, habilite a "
            "integração WSL e reexecute o bootstrap; não use sudo."
        )
    return (
        "Docker ausente. Instale e inicie Docker rootless em user-space, "
        "depois reexecute o bootstrap; não use sudo."
    )


def _command_environment(
    context: InstallContext,
    data_directory: Path,
) -> dict[str, str]:
    return {
        **context.current_environment,
        "AI_MEMORY_DATA_DIR": str(data_directory),
        "AI_MEMORY_DOCKER": _docker_executable(context) or "docker",
        "AI_MEMORY_IMAGE": AI_MEMORY_IMAGE,
    }


def _write(stream: TextIO | None, message: str) -> None:
    if stream is None:
        return
    stream.write(f"{message}\n")
    stream.flush()


def _require_success(result: CommandResult, label: str) -> None:
    if result.timed_out:
        raise AiMemoryProvisionError(f"{label} excedeu o limite de execução.")
    if not result.succeeded:
        detail = result.stderr or result.stdout or "comando falhou sem detalhe"
        raise AiMemoryProvisionError(f"{label} falhou: {detail.strip()}")


def _execute(
    command: Sequence[str],
    context: InstallContext,
    runner: Runner,
    output: TextIO | None,
) -> CommandResult:
    _write(output, f"Executando: {' '.join(command)}")
    environment = _command_environment(
        context,
        ai_memory_data_directory(context.paths),
    )
    if runner is run_streaming_command:
        result = runner(
            command,
            env=environment,
            timeout=AI_MEMORY_COMMAND_TIMEOUT_SECONDS,
            output=output,
        )
    else:
        result = runner(
            command,
            env=environment,
            timeout=AI_MEMORY_COMMAND_TIMEOUT_SECONDS,
        )
    if runner is not run_streaming_command:
        for line in (result.stdout + result.stderr).splitlines():
            _write(output, line)
    return result


def _require_docker_daemon(
    docker: str,
    context: InstallContext,
    runner: Runner,
    output: TextIO | None,
) -> None:
    result = _execute([docker, "info"], context, runner, output)
    _require_success(
        result,
        "Docker indisponível. Inicie o runtime em user-space e reexecute",
    )


def _ensure_container_network(
    docker: str,
    context: InstallContext,
    runner: Runner,
    output: TextIO | None,
) -> bool:
    inspected = _execute(
        [docker, "network", "inspect", "--format", "{{.Internal}}", AI_MEMORY_NETWORK],
        context,
        runner,
        output,
    )
    if inspected.succeeded:
        if inspected.stdout.strip().lower() != "true":
            raise AiMemoryProvisionError(
                f"A rede {AI_MEMORY_NETWORK} existe sem isolamento internal. "
                "Remova-a após verificar seus usuários e reexecute o bootstrap."
            )
        return False

    created = _execute(
        [
            docker,
            "network",
            "create",
            "--driver",
            "bridge",
            "--internal",
            AI_MEMORY_NETWORK,
        ],
        context,
        runner,
        output,
    )
    _require_success(created, "Criação da rede Docker internal")
    return True


def _inspect_container(
    docker: str,
    context: InstallContext,
    runner: Runner,
    output: TextIO | None,
) -> dict[str, object] | None:
    inspected = _execute(
        [docker, "inspect", "--format", "{{json .}}", AI_MEMORY_DATA_NAME],
        context,
        runner,
        output,
    )
    if not inspected.succeeded:
        detail = f"{inspected.stderr} {inspected.stdout}".lower()
        if "not found" in detail or "no such" in detail:
            return None
        _require_success(inspected, "Inspeção do container ai-memory")
    try:
        result = json.loads(inspected.stdout)
    except json.JSONDecodeError as error:
        raise AiMemoryProvisionError(
            "Docker retornou dados inválidos ao inspecionar ai-memory."
        ) from error
    if not isinstance(result, dict):
        raise AiMemoryProvisionError("Docker retornou inspeção inválida de ai-memory.")
    return result


def _validate_existing_container(
    container: dict[str, object],
    data_directory: Path,
    docker: str,
    context: InstallContext,
    runner: Runner,
    output: TextIO | None,
) -> None:
    configuration = container.get("Config", {})
    host_config = container.get("HostConfig", {})
    mounts = container.get("Mounts", [])
    if (
        not isinstance(configuration, dict)
        or configuration.get("Image") != AI_MEMORY_IMAGE
    ):
        raise AiMemoryProvisionError(
            f"O container ai-memory existente não usa a imagem autorizada "
            f"{AI_MEMORY_IMAGE}; preserve os dados e revise o container antes "
            "de reexecutar."
        )
    bindings = (
        host_config.get("PortBindings", {}) if isinstance(host_config, dict) else {}
    )
    published_ports = (
        bindings.get("49374/tcp", []) if isinstance(bindings, dict) else []
    )
    has_loopback_binding = any(
        isinstance(binding, dict)
        and binding.get("HostIp") == AI_MEMORY_HOST
        and binding.get("HostPort") == str(AI_MEMORY_PORT)
        for binding in published_ports
    ) and (
        isinstance(bindings, dict)
        and set(bindings) == {"49374/tcp"}
        and len(published_ports) == 1
    )
    has_data_mount = (
        any(
            isinstance(mount, dict)
            and mount.get("Type") == "bind"
            and Path(str(mount.get("Source", ""))).resolve() == data_directory.resolve()
            and mount.get("Destination") == "/data"
            for mount in mounts
        )
        if isinstance(mounts, list) and len(mounts) == 1
        else False
    )
    network_mode = (
        host_config.get("NetworkMode") if isinstance(host_config, dict) else None
    )

    if not (
        has_loopback_binding and has_data_mount and network_mode == AI_MEMORY_NETWORK
    ):
        raise AiMemoryProvisionError(
            "O container ai-memory existente não atende ao bind loopback, "
            "volume ou rede internal exigidos. Preserve os dados, faça backup "
            "do container e siga o caminho de upgrade documentado antes de reexecutar."
        )

    network = _execute(
        [docker, "network", "inspect", "--format", "{{.Internal}}", AI_MEMORY_NETWORK],
        context,
        runner,
        output,
    )
    _require_success(network, "Inspeção da rede internal ai-memory")
    if network.stdout.strip().lower() != "true":
        raise AiMemoryProvisionError(
            f"A rede existente {AI_MEMORY_NETWORK} não é internal; "
            "o MCP permanecerá desabilitado."
        )


def _ensure_image(
    docker: str,
    context: InstallContext,
    runner: Runner,
    output: TextIO | None,
) -> None:
    inspected = _execute(
        [docker, "image", "inspect", AI_MEMORY_IMAGE],
        context,
        runner,
        output,
    )
    if inspected.succeeded:
        return
    _require_success(
        _execute([docker, "pull", AI_MEMORY_IMAGE], context, runner, output),
        f"Download da imagem {AI_MEMORY_IMAGE}",
    )


def _run_server(
    docker: str,
    data_directory: Path,
    context: InstallContext,
    runner: Runner,
    output: TextIO | None,
) -> None:
    command = [
        docker,
        "run",
        "--detach",
        "--name",
        AI_MEMORY_DATA_NAME,
        "--restart",
        "unless-stopped",
        "--publish",
        f"{AI_MEMORY_HOST}:{AI_MEMORY_PORT}:{AI_MEMORY_PORT}",
        "--network",
        AI_MEMORY_NETWORK,
        "--volume",
        f"{data_directory.resolve()}:/data",
        "--label",
        "opencode-config.ai-memory=managed",
        AI_MEMORY_IMAGE,
    ]
    _require_success(
        _execute(command, context, runner, output),
        "Inicialização do container ai-memory",
    )


def _secure_data_directory(
    data_directory: Path,
    environment: EnvironmentKind,
) -> None:
    if data_directory.is_symlink():
        raise AiMemoryProvisionError(
            f"O diretório de dados não pode ser symlink: {data_directory}"
        )
    data_directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if environment is not EnvironmentKind.WINDOWS:
        data_directory.chmod(0o700)


def _verify_container_running(
    docker: str,
    context: InstallContext,
    runner: Runner,
    output: TextIO | None,
) -> None:
    container = _inspect_container(docker, context, runner, output)
    state = container.get("State", {}) if container is not None else {}
    if not isinstance(state, dict) or not state.get("Running"):
        raise AiMemoryProvisionError(
            "O container ai-memory encerrou durante a inicialização. "
            "Consulte `docker logs ai-memory` antes de reexecutar."
        )


def _ensure_wrappers(context: InstallContext, fetcher: Fetcher | None) -> None:
    context.paths.bin_dir.mkdir(parents=True, exist_ok=True)
    if context.environment is EnvironmentKind.WINDOWS:
        assets = AI_MEMORY_WINDOWS_WRAPPERS
    else:
        assets = (("ai-memory", AI_MEMORY_WRAPPER_SHA256),)

    for asset, expected_hash in assets:
        destination = context.paths.bin_dir / asset
        if destination.is_file():
            actual_hash = _sha256_file(destination)
            if actual_hash != expected_hash:
                raise AiMemoryProvisionError(
                    f"O wrapper existente {destination} tem SHA-256 divergente "
                    f"(esperado {expected_hash}, encontrado {actual_hash}). "
                    f"Faça backup de {destination}, remova o arquivo e reexecute "
                    "o bootstrap para atualizar o wrapper."
                )
            continue

        url = _wrapper_url(asset, context.environment)
        with tempfile.NamedTemporaryFile(
            prefix="ai-memory-wrapper-",
            dir=context.paths.bin_dir,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
        try:
            download_file(
                url,
                temporary_path,
                expected_sha256=expected_hash,
                fetcher=_fetch_wrapper if fetcher is None else fetcher,
            )
            if temporary_path.stat().st_size > _MAX_WRAPPER_BYTES:
                raise AiMemoryProvisionError(
                    f"O wrapper {asset} excede o limite de {_MAX_WRAPPER_BYTES} bytes."
                )
            if context.environment is not EnvironmentKind.WINDOWS:
                temporary_path.chmod(0o755)
            os.replace(temporary_path, destination)
        finally:
            temporary_path.unlink(missing_ok=True)


def _wrapper_url(asset: str, environment: EnvironmentKind) -> str:
    if environment is EnvironmentKind.WINDOWS:
        return (
            "https://github.com/akitaonrails/ai-memory/releases/latest/download/"
            f"{asset}"
        )
    return AI_MEMORY_WRAPPER_URL


def _fetch_wrapper(url: str, destination: Path) -> None:
    with urllib.request.urlopen(
        url,
        timeout=_DOWNLOAD_IDLE_TIMEOUT_SECONDS,
    ) as response:  # nosec B310
        with destination.open("wb") as downloaded:
            total_bytes = 0
            while block := response.read(64 * 1024):
                total_bytes += len(block)
                if total_bytes > _MAX_WRAPPER_BYTES:
                    raise AiMemoryProvisionError(
                        f"O wrapper excede o limite de {_MAX_WRAPPER_BYTES} bytes."
                    )
                downloaded.write(block)


def _install_hooks(
    context: InstallContext,
    runner: Runner,
    output: TextIO | None,
) -> None:
    if context.environment is EnvironmentKind.WINDOWS:
        powershell = shutil.which(
            "powershell.exe",
            path=context.current_environment.get("PATH"),
        )
        if powershell is None:
            raise AiMemoryProvisionError(
                "powershell.exe ausente no PATH; instale PowerShell no escopo "
                "do usuário e reexecute o bootstrap."
            )
        wrapper = context.paths.bin_dir / "ai-memory-wrapper.ps1"
        command = [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(wrapper),
            "install-hooks",
            "--agent",
            "opencode",
            "--apply",
        ]
    else:
        command = [
            str(context.paths.bin_dir / "ai-memory"),
            "install-hooks",
            "--agent",
            "opencode",
            "--apply",
        ]
    _require_success(
        _execute(command, context, runner, output),
        "Instalação dos hooks oficiais ai-memory",
    )


def _plugin_path(home: Path) -> Path:
    return home / ".config" / "opencode" / "plugins" / "ai-memory.ts"


def _sha256_file(path: Path) -> str:
    if not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(64 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _backup_directory(home: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return home / ".config" / "opencode-backup" / timestamp


def _backup_legacy_jsonc(home: Path) -> None:
    path = home / ".config" / "opencode" / "opencode.jsonc"
    if path.exists() or path.is_symlink():
        backup_move(path, _backup_directory(home))


def _remove_ready_marker(paths: UserSpacePaths) -> None:
    ai_memory_ready_marker(paths).unlink(missing_ok=True)


def _marker_created_network(paths: UserSpacePaths) -> bool:
    if _network_marker(paths).is_file():
        return True
    marker = ai_memory_ready_marker(paths)
    if not marker.is_file():
        return False
    try:
        metadata = json.loads(marker.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return isinstance(metadata, dict) and metadata.get("network_created") is True


def _network_marker(paths: UserSpacePaths) -> Path:
    return ai_memory_data_directory(paths) / AI_MEMORY_NETWORK_MARKER


def _write_network_marker(paths: UserSpacePaths) -> None:
    marker = _network_marker(paths)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("created\n", encoding="utf-8")


def _remove_network_marker(paths: UserSpacePaths) -> None:
    _network_marker(paths).unlink(missing_ok=True)


def _write_ready_marker(
    paths: UserSpacePaths,
    network_created: bool,
) -> None:
    marker = ai_memory_ready_marker(paths)
    marker.parent.mkdir(parents=True, exist_ok=True)
    temporary = marker.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(
            {"complete": True, "network_created": network_created},
        )
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, marker)


def _deactivate_incomplete_setup(
    context: InstallContext,
    reason: str,
    *,
    output: TextIO | None = None,
    failed: bool = True,
) -> AiMemoryProvisionResult:
    cleanup_errors: list[str] = []
    cleanup_steps = (
        lambda: _remove_ready_marker(context.paths),
        lambda: _backup_legacy_jsonc(context.paths.home),
        lambda: _remove_generated_plugin(context.paths.home),
        lambda: _remove_opencode_server(context.paths.home),
        lambda: _remove_copilot_server(context.paths.home),
    )
    for cleanup in cleanup_steps:
        try:
            cleanup()
        except (AiMemoryProvisionError, OSError) as error:
            cleanup_errors.append(str(error))
    if cleanup_errors:
        reason = f"{reason} {' | '.join(cleanup_errors)}"
        failed = True
    message = (
        f"ai-memory não provisionado: {reason} "
        "O bloco MCP foi desabilitado nos harnesses."
    )
    _write(output, message)
    return AiMemoryProvisionResult(False, True, message, failed=failed)


def _remove_generated_plugin(home: Path) -> None:
    plugin = _plugin_path(home)
    if plugin.exists() or plugin.is_symlink():
        backup_copy(plugin, _backup_directory(home))
        plugin.unlink()


def _remove_copilot_server(home: Path) -> None:
    config_path = home / ".copilot" / "mcp-config.json"
    if not config_path.is_file():
        return
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise AiMemoryProvisionError(
            f"JSON inválido em {config_path}; o rollback preservou o arquivo."
        ) from error
    if not isinstance(config, dict):
        raise AiMemoryProvisionError(
            f"A raiz de {config_path} precisa ser um objeto JSON."
        )
    servers = config.get("mcpServers")
    if not isinstance(servers, dict):
        return
    if servers.get("ai-memory") != {
        "type": "http",
        "url": AI_MEMORY_MCP_URL,
    }:
        return
    del servers["ai-memory"]
    backup_copy(config_path, _backup_directory(home))
    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _remove_opencode_server(home: Path) -> None:
    config_path = home / ".config" / "opencode" / "opencode.json"
    if not config_path.is_file():
        return
    content = config_path.read_text(encoding="utf-8")
    filtered = filter_ai_memory_config(content)
    if filtered == content and not config_path.is_symlink():
        return
    if config_path.is_symlink():
        backup_move(config_path, _backup_directory(home))
    else:
        backup_copy(config_path, _backup_directory(home))
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(filtered, encoding="utf-8")


def _remove_wrapper_artifacts(paths: UserSpacePaths) -> None:
    if paths.home.is_dir():
        candidates = [
            paths.bin_dir / "ai-memory",
            *(paths.bin_dir / asset for asset, _hash in AI_MEMORY_WINDOWS_WRAPPERS),
        ]
        for wrapper in candidates:
            if wrapper.exists() or wrapper.is_symlink():
                backup_copy(wrapper, _backup_directory(paths.home))
                wrapper.unlink()


def _restore_legacy_jsonc(home: Path) -> None:
    target = home / ".config" / "opencode" / "opencode.jsonc"
    if target.exists() or target.is_symlink():
        return
    backups = sorted(
        (home / ".config" / "opencode-backup").glob("*/opencode.jsonc"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if backups:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backups[0], target)


def _run_cleanup_command(
    command: Sequence[str],
    context: InstallContext,
    runner: Runner,
    errors: list[str],
) -> None:
    try:
        result = runner(
            command,
            env=_command_environment(
                context,
                ai_memory_data_directory(context.paths),
            ),
            timeout=AI_MEMORY_COMMAND_TIMEOUT_SECONDS,
        )
    except (AiMemoryProvisionError, OSError) as error:
        errors.append(f"{' '.join(command)}: {error}")
        return
    if not result.succeeded:
        detail = result.stderr or result.stdout or "comando falhou"
        if "not found" not in detail.lower() and "no such" not in detail.lower():
            errors.append(f"{' '.join(command)}: {detail.strip()}")


def _port_is_in_use(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def run_streaming_command(
    command: Sequence[str],
    *,
    env: Mapping[str, str],
    timeout: float,
    output: TextIO | None = None,
) -> CommandResult:
    """Executa processo com saída incremental e limites de inatividade e total."""

    arguments = tuple(os.fspath(argument) for argument in command)
    process = subprocess.Popen(  # nosec B603 - comandos fixados no chamador
        arguments,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=dict(env),
    )
    if process.stdout is None:
        raise AiMemoryProvisionError("Não foi possível abrir a saída do processo.")

    chunks: queue.Queue[str | None] = queue.Queue()
    reader = threading.Thread(
        target=_read_process_output,
        args=(process.stdout, chunks),
        daemon=True,
    )
    reader.start()
    started = time.monotonic()
    last_output = started
    captured: list[str] = []
    reader_finished = False

    while process.poll() is None or not reader_finished:
        try:
            chunk = chunks.get(timeout=1)
        except queue.Empty:
            now = time.monotonic()
            if now - last_output > AI_MEMORY_COMMAND_IDLE_TIMEOUT_SECONDS:
                _terminate_streaming_process(process, reader)
                raise AiMemoryProvisionError(
                    f"{' '.join(arguments)} não produziu saída por "
                    f"{AI_MEMORY_COMMAND_IDLE_TIMEOUT_SECONDS} s."
                )
            if now - started > timeout:
                _terminate_streaming_process(process, reader)
                raise AiMemoryProvisionError(
                    f"{' '.join(arguments)} excedeu o limite total de {timeout:g} s."
                )
            continue
        if chunk is None:
            reader_finished = True
            continue
        captured.append(chunk)
        now = time.monotonic()
        if now - started > timeout:
            _terminate_streaming_process(process, reader)
            raise AiMemoryProvisionError(
                f"{' '.join(arguments)} excedeu o limite total de {timeout:g} s."
            )
        last_output = now
        _write(output, chunk.rstrip("\r\n"))

    reader.join()
    process.stdout.close()
    returncode = process.wait()
    text = "".join(captured)
    return CommandResult(
        args=arguments,
        returncode=returncode,
        stdout=text,
        stderr="",
    )


def _terminate_streaming_process(
    process: subprocess.Popen[str],
    reader: threading.Thread,
) -> None:
    if process.poll() is None:
        process.kill()
    process.wait()
    reader.join()
    if process.stdout is not None:
        process.stdout.close()


def _read_process_output(stream, chunks: queue.Queue[str | None]) -> None:
    buffer: list[str] = []
    while character := stream.read(1):
        buffer.append(character)
        if character in "\r\n" or len(buffer) >= 4096:
            chunks.put("".join(buffer))
            buffer.clear()
    if buffer:
        chunks.put("".join(buffer))
    chunks.put(None)
