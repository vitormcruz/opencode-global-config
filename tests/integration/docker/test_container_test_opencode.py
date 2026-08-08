"""Unit tests for OpenCode model discovery used by the Docker session."""

from __future__ import annotations

import json

import pytest

from container_test_opencode import extract_models_from_config


pytestmark = pytest.mark.unit


def _write_config(tmp_path, config: dict) -> str:
    config_file = tmp_path / "opencode.json"
    config_file.write_text(
        json.dumps(config, ensure_ascii=False),
        encoding="utf-8",
    )
    return str(config_file)


def test_extracts_models_from_valid_config_with_two_agents(tmp_path):
    config_file = _write_config(
        tmp_path,
        {
            "agent": {
                "plan": {"model": "provider/model-a"},
                "build": {"model": "provider/model-b"},
            }
        },
    )

    models = extract_models_from_config(config_file)

    assert "provider/model-a" in models
    assert "provider/model-b" in models


def test_extracts_unique_models_when_duplicates_exist(tmp_path):
    config_file = _write_config(
        tmp_path,
        {
            "agent": {
                "plan": {"model": "opencode/big-pickle"},
                "build": {"model": "opencode/big-pickle"},
            }
        },
    )

    models = extract_models_from_config(config_file)

    assert models == ["opencode/big-pickle"]


def test_extracts_models_from_provider_models(tmp_path):
    config_file = _write_config(
        tmp_path,
        {
            "provider": {
                "my-provider": {
                    "models": {
                        "model-x": {"name": "Model X"},
                        "model-y": {"name": "Model Y"},
                    }
                }
            }
        },
    )

    models = extract_models_from_config(config_file)

    assert "my-provider/model-x" in models
    assert "my-provider/model-y" in models


def test_combines_agent_and_provider_models_without_duplicates(tmp_path):
    config_file = _write_config(
        tmp_path,
        {
            "agent": {"plan": {"model": "prov/model-a"}},
            "provider": {
                "prov": {
                    "models": {
                        "model-a": {},
                        "model-b": {},
                    }
                }
            },
        },
    )

    models = extract_models_from_config(config_file)

    assert "prov/model-a" in models
    assert "prov/model-b" in models
    assert models.count("prov/model-a") == 1


def test_returns_empty_when_config_has_no_agent_or_provider(tmp_path):
    config_file = _write_config(tmp_path, {"mcp": {}})

    assert extract_models_from_config(config_file) == []


def test_returns_empty_when_agent_has_no_model(tmp_path):
    config_file = _write_config(
        tmp_path,
        {"agent": {"plan": {"permission": {}}}},
    )

    assert extract_models_from_config(config_file) == []


def test_returns_empty_for_missing_file(tmp_path):
    assert extract_models_from_config(tmp_path / "nao-existe.json") == []


def test_without_opencode_config_does_not_extract_missing_file(
    monkeypatch,
    tmp_path,
):
    monkeypatch.delenv("OPENCODE_CONFIG", raising=False)

    assert extract_models_from_config(tmp_path / "nao-existe.json") == []


def test_opencode_config_with_missing_file_does_not_break_extraction(
    monkeypatch,
    tmp_path,
):
    config_file = tmp_path / "inexistente.json"
    monkeypatch.setenv("OPENCODE_CONFIG", str(config_file))

    assert extract_models_from_config(config_file) == []


def test_opencode_config_with_agent_models_returns_only_agent_models(
    monkeypatch,
    tmp_path,
):
    config_file = _write_config(
        tmp_path,
        {
            "agent": {
                "plan": {"model": "opencode/big-pickle"},
                "build": {"model": "opencode/big-pickle"},
            }
        },
    )
    monkeypatch.setenv("OPENCODE_CONFIG", config_file)

    assert extract_models_from_config(config_file) == ["opencode/big-pickle"]


def test_opencode_config_with_provider_only_returns_provider_models(
    monkeypatch,
    tmp_path,
):
    config_file = _write_config(
        tmp_path,
        {
            "provider": {
                "corp-llm": {
                    "models": {
                        "modelo-interno": {},
                    }
                }
            }
        },
    )
    monkeypatch.setenv("OPENCODE_CONFIG", config_file)

    assert extract_models_from_config(config_file) == ["corp-llm/modelo-interno"]
