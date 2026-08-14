#!/usr/bin/env python3
"""Configure and start the OpenCode server inside the test image."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


CONFIG_FILE = Path("/opt/opencode-config/opencode.json")
OPENCODE_BINARY = "/root/.opencode/bin/opencode"


def _read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"configuração JSON inválida: {path}")
    return value


def _write_json(path: Path, value: dict) -> None:
    """Replace a JSON file atomically without writing to a system temp folder."""

    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = temporary.name
            json.dump(value, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            try:
                Path(temporary_path).unlink()
            except FileNotFoundError:
                pass


def _merge_json(base: object, override: object) -> object:
    """Implement jq's recursive object merge used for provider settings."""

    if isinstance(base, dict) and isinstance(override, dict):
        merged = dict(base)
        for key, value in override.items():
            merged[key] = _merge_json(merged[key], value) if key in merged else value
        return merged
    return override


def _merge_host_provider(config: dict, host_config_file: Path) -> dict:
    try:
        host_config = _read_json(host_config_file)
    except (OSError, ValueError, json.JSONDecodeError):
        return config

    host_provider = host_config.get("provider")
    if host_provider is None or host_provider is False:
        return config

    config["provider"] = _merge_json(config.get("provider", {}), host_provider)
    return config


def configure() -> None:
    """Apply the optional host provider overlay without changing the model."""

    config = _read_json(CONFIG_FILE)
    host_config = os.environ.get("OPENCODE_CONFIG", "")
    if host_config:
        host_config_file = Path(host_config)
        if host_config_file.is_file():
            try:
                host_config_data = _read_json(host_config_file)
            except (OSError, ValueError, json.JSONDecodeError):
                host_config_data = {}
            host_provider = host_config_data.get("provider")
            if host_provider is not None and host_provider is not False:
                print(
                    "[entrypoint] Mesclando provider de OPENCODE_CONFIG...",
                    flush=True,
                )
                _write_json(
                    CONFIG_FILE,
                    _merge_host_provider(config, host_config_file),
                )


def main() -> None:
    """Configure the image and replace this process with OpenCode."""

    configure()
    os.execv(
        OPENCODE_BINARY,
        [
            OPENCODE_BINARY,
            "--pure",
            "serve",
            "--hostname",
            "0.0.0.0",
            "--port",
            "4096",
        ],
    )


if __name__ == "__main__":
    main()
