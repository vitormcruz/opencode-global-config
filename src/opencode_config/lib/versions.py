"""Utilidades para comparar e localizar versoes instaladas pelo fnm."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path


def natural_version_key(value: str) -> tuple[tuple[int, int | str], ...]:
    """Chave de ordenacao natural para nomes como ``v22.23.2``."""

    return tuple(
        (0, int(part)) if part.isdigit() else (1, part)
        for part in re.split(r"([0-9]+)", value)
        if part
    )


def _major_version(name: str) -> int | None:
    """Extrai o segmento major de um nome de versao do fnm (``v22.23.2``)."""

    match = re.search(r"(\d+)", name)
    return int(match.group(1)) if match else None


def fnm_node_bin_dir(
    home: Path,
    environment: Mapping[str, str],
    *,
    major: int | None = None,
) -> Path | None:
    """Retorna o diretorio bin do Node.js instalado pelo fnm.

    Localiza o layout ``$FNM_DIR/node-versions/vX.Y.Z/installation/bin``
    (ou ``installation`` no Windows). Quando ``major`` e informado, restringe
    a busca as versoes daquela linha major (ex.: 22), evitando selecionar
    uma versao major diferente recem-instalada por acidente.
    """

    fnm_dir = Path(environment.get("FNM_DIR") or home / ".local" / "share" / "fnm")
    versions_dir = fnm_dir / "node-versions"
    if not versions_dir.is_dir():
        return None

    versions = [item for item in versions_dir.iterdir() if item.is_dir()]
    if major is not None:
        versions = [
            item for item in versions if _major_version(item.name) == major
        ]
    if not versions:
        return None

    latest = max(versions, key=lambda item: natural_version_key(item.name))
    bin_dir = latest / "installation" / "bin"
    if bin_dir.is_dir():
        return bin_dir
    installation = latest / "installation"
    return installation if installation.is_dir() else None
