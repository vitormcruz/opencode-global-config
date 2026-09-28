"""Helpers ai-memory compartilhados pelo bootstrap e pelos adapters."""

from __future__ import annotations

import json
from pathlib import Path

from opencode_config.lib.paths import UserSpacePaths

AI_MEMORY_MCP_URL = "http://127.0.0.1:49374/mcp"
AI_MEMORY_DATA_NAME = "ai-memory"
AI_MEMORY_READY_MARKER = ".bootstrap-provisioned"
AI_MEMORY_URL_MARKER = ".bootstrap-mcp-url"


class AiMemoryProvisionError(RuntimeError):
    """Falha acionável ao consultar ou editar a configuração ai-memory."""


def ai_memory_data_directory(paths: UserSpacePaths) -> Path:
    """Retorna o diretório persistente do ai-memory no espaço do usuário."""

    return paths.home / ".local" / "share" / AI_MEMORY_DATA_NAME


def ai_memory_ready_marker(paths: UserSpacePaths) -> Path:
    """Retorna o marcador gravado somente após provisionamento completo."""

    return ai_memory_data_directory(paths) / AI_MEMORY_READY_MARKER


def is_ai_memory_provisioned(home: Path) -> bool:
    """Informa se o bootstrap concluiu a integração para esta home."""

    return ai_memory_ready_marker(_paths_for_home(home)).is_file()


def ai_memory_mcp_url(home: Path) -> str:
    """Retorna o endpoint atual registrado pelo provisionamento."""

    return _read_ready_mcp_url(_paths_for_home(home)) or AI_MEMORY_MCP_URL


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


def configure_ai_memory_mcp_url(content: str, mcp_url: str) -> str:
    """Retorna a configuração OpenCode com o endpoint provisionado."""

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
    server = servers.get("ai-memory") if isinstance(servers, dict) else None
    if not isinstance(server, dict):
        raise AiMemoryProvisionError(
            "A configuração OpenCode não declara mcp.ai-memory."
        )
    server["url"] = mcp_url
    return json.dumps(configuration, indent=4, ensure_ascii=False) + "\n"


def _paths_for_home(home: Path) -> UserSpacePaths:
    return UserSpacePaths(
        home=home,
        config_dir=home / ".config",
        data_dir=home / ".local" / "share",
        bin_dir=home / ".local" / "bin",
        pipx_bin=home / ".local" / "bin",
        npm_bin=home / ".local" / "bin",
    )


def _read_ready_mcp_url(paths: UserSpacePaths) -> str | None:
    if not ai_memory_ready_marker(paths).is_file():
        return None
    for marker in (_mcp_url_marker(paths), _legacy_mcp_url_marker(paths)):
        try:
            mcp_url = marker.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if mcp_url:
            return mcp_url
    return None


def _mcp_url_marker(paths: UserSpacePaths) -> Path:
    return paths.home / ".local" / "state" / "ai-memory" / AI_MEMORY_URL_MARKER


def _legacy_mcp_url_marker(paths: UserSpacePaths) -> Path:
    return ai_memory_data_directory(paths) / AI_MEMORY_URL_MARKER
