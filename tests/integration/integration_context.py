"""Build minimal project trees for OpenCode integration cases."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Literal


ContextKind = Literal["agent", "command", "empty", "skill"]
_CONTEXT_KINDS = {"agent", "command", "empty", "skill"}


def _artifact_source(repository: Path, kind: str, name: str) -> Path:
    if kind == "agent":
        return repository / "agents" / f"{name}.md"
    if kind == "command":
        return repository / "commands" / f"{name}.md"
    return repository / "skills" / name


def prepare_test_context(
    repository: Path,
    destination: Path,
    *,
    kind: ContextKind | str,
    name: str | None = None,
) -> Path:
    """Copy only the repository artifact required by one integration test."""

    if kind not in _CONTEXT_KINDS:
        raise ValueError(f"Tipo de contexto desconhecido: {kind}")
    if kind == "empty" and name is not None:
        raise ValueError("O contexto vazio não aceita um nome de artefato.")
    if kind != "empty" and not name:
        raise ValueError(f"O contexto {kind} exige um nome de artefato.")

    destination.mkdir(parents=True, exist_ok=True)
    for child in destination.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()

    config_source = (
        repository / "tests" / "integration" / "config" / "opencode.test.json"
    )
    config = json.loads(config_source.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("A configuração de teste do OpenCode deve ser um objeto.")

    config["plugin"] = []
    config["permission"] = {"skill": {"*": "deny"}}
    tools = {"*": False}
    if kind == "skill":
        tools["skill"] = True
    config["agent"] = {
        "plan": {
            "model": "bonsai-local/bonsai-27b",
            "prompt": "Responda somente ao pedido do teste.",
            "tools": dict(tools),
        },
        "build": {
            "model": "bonsai-local/bonsai-27b",
            "prompt": "Responda somente ao pedido do teste.",
            "tools": dict(tools),
        },
    }
    if kind == "skill":
        assert name is not None
        config["permission"]["skill"][name] = "allow"

    (destination / "opencode.json").write_text(
        json.dumps(config, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )

    if kind == "empty":
        return destination

    assert name is not None
    source = _artifact_source(repository, kind, name)
    if not source.is_dir() and not source.is_file():
        raise FileNotFoundError(f"Artefato de teste não encontrado: {source}")
    target = destination / {
        "agent": "agents",
        "command": "commands",
        "skill": "skills",
    }[kind]
    target.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target / source.name)
    else:
        shutil.copy2(source, target / source.name)
    return destination
