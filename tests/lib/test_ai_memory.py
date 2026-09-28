"""Testes dos helpers ai-memory compartilhados pelo bootstrap e adapters."""

import json
from pathlib import Path

import pytest

from opencode_config.lib.ai_memory import (
    AI_MEMORY_MCP_URL,
    AiMemoryProvisionError,
    ai_memory_mcp_url,
    configure_ai_memory_mcp_url,
    filter_ai_memory_config,
    is_ai_memory_provisioned,
)


@pytest.mark.unit
def test_filter_ai_memory_config_preserves_other_servers() -> None:
    content = json.dumps(
        {
            "mcp": {
                "ai-memory": {"url": "http://127.0.0.1:49374/mcp"},
                "user-server": {"url": "http://localhost:49375/mcp"},
            },
            "otherSetting": "preserved",
        }
    )

    filtered = json.loads(filter_ai_memory_config(content))

    assert filtered == {
        "mcp": {"user-server": {"url": "http://localhost:49375/mcp"}},
        "otherSetting": "preserved",
    }


@pytest.mark.unit
def test_filter_ai_memory_config_removes_empty_mcp_section() -> None:
    content = json.dumps({"mcp": {"ai-memory": {}}, "otherSetting": True})

    filtered = json.loads(filter_ai_memory_config(content))

    assert filtered == {"otherSetting": True}


@pytest.mark.unit
def test_filter_ai_memory_config_rejects_invalid_json() -> None:
    with pytest.raises(AiMemoryProvisionError, match="JSON inválido"):
        filter_ai_memory_config("{")


@pytest.mark.unit
def test_configure_ai_memory_mcp_url_preserves_other_servers() -> None:
    content = json.dumps(
        {
            "mcp": {
                "ai-memory": {"url": AI_MEMORY_MCP_URL},
                "user-server": {"url": "http://localhost:49375/mcp"},
            }
        }
    )

    configured = json.loads(
        configure_ai_memory_mcp_url(content, "http://172.30.0.2:49374/mcp")
    )

    assert configured["mcp"]["ai-memory"]["url"] == "http://172.30.0.2:49374/mcp"
    assert configured["mcp"]["user-server"]["url"] == "http://localhost:49375/mcp"


@pytest.mark.unit
def test_is_ai_memory_provisioned_requires_ready_marker(tmp_path: Path) -> None:
    assert not is_ai_memory_provisioned(tmp_path)

    marker = (
        tmp_path / ".local" / "share" / "ai-memory" / ".bootstrap-provisioned"
    )
    marker.parent.mkdir(parents=True)
    marker.write_text("ready", encoding="utf-8")

    assert is_ai_memory_provisioned(tmp_path)


@pytest.mark.unit
def test_ai_memory_mcp_url_uses_marker_only_after_provisioning(
    tmp_path: Path,
) -> None:
    url_marker = (
        tmp_path / ".local" / "state" / "ai-memory" / ".bootstrap-mcp-url"
    )
    url_marker.parent.mkdir(parents=True)
    url_marker.write_text("http://172.30.0.2:49374/mcp\n", encoding="utf-8")

    assert ai_memory_mcp_url(tmp_path) == AI_MEMORY_MCP_URL

    ready_marker = (
        tmp_path / ".local" / "share" / "ai-memory" / ".bootstrap-provisioned"
    )
    ready_marker.parent.mkdir(parents=True)
    ready_marker.write_text("ready", encoding="utf-8")

    assert ai_memory_mcp_url(tmp_path) == "http://172.30.0.2:49374/mcp"


@pytest.mark.unit
def test_harness_adapters_import_ai_memory_helpers_from_shared_library(
    repo_root: Path,
) -> None:
    adapter_paths = (
        repo_root / "src" / "opencode_config" / "harnesses" / "opencode.py",
        repo_root / "src" / "opencode_config" / "harnesses" / "copilot.py",
    )

    for adapter_path in adapter_paths:
        source = adapter_path.read_text(encoding="utf-8")
        assert "from opencode_config.lib.ai_memory import (" in source
        assert "from opencode_config.bootstrap.ai_memory import (" not in source
