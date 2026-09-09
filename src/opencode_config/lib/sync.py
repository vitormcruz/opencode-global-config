"""Utilitarios de sincronizacao de arquivos compartilhados pelos harnesses.

Funcoes puras de backup, copia sincronizada, remocao e criacao de symlink.
Os adapters consomem estes utilitarios; nenhum deles decide sistema
operacional.
"""

from __future__ import annotations

import filecmp
import os
from pathlib import Path
import shutil


def remove_path(path: Path) -> None:
    """Remove arquivo, symlink ou arvore; destino inexistente e no-op."""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def copy_path(source: Path, destination: Path) -> None:
    """Copia arquivo, arvore ou symlink preservando o alvo do link."""
    if source.is_symlink():
        destination.symlink_to(
            os.readlink(source),
            target_is_directory=source.is_dir(),
        )
    elif source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination)


def _next_available_path(path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    candidate = backup_dir / path.name
    index = 1
    while candidate.exists() or candidate.is_symlink():
        candidate = backup_dir / f"{path.name}.{index}"
        index += 1
    return candidate


def backup_copy(path: Path, backup_dir: Path) -> None:
    """Copia um caminho existente para backup_dir; original permanece."""
    if not path.exists() and not path.is_symlink():
        return
    copy_path(path, _next_available_path(path, backup_dir))


def backup_move(path: Path, backup_dir: Path) -> None:
    """Move um caminho existente para backup_dir; original deixa de existir."""
    if not path.exists() and not path.is_symlink():
        return
    path.rename(_next_available_path(path, backup_dir))


def _same_tree(source: Path, destination: Path) -> bool:
    if source.is_symlink():
        return destination.is_symlink() and (
            os.readlink(source) == os.readlink(destination)
        )
    if source.is_dir():
        if not destination.is_dir():
            return False
        source_names = {child.name for child in source.iterdir()}
        destination_names = {child.name for child in destination.iterdir()}
        if source_names != destination_names:
            return False
        return all(
            _same_tree(source / name, destination / name)
            for name in source_names
        )
    return destination.is_file() and filecmp.cmp(
        source,
        destination,
        shallow=False,
    )


def paths_equal(source: Path, destination: Path) -> bool:
    """Informa se destination ja espelha source (arquivo ou arvore)."""
    return _same_tree(source, destination)


def sync_path(
    source: Path,
    destination: Path,
    backup_dir: Path | None = None,
) -> None:
    """Espelha source em destination por copia, apagando entradas extras.

    Destino sincronizado e no-op; destino divergente gera backup em
    backup_dir (quando informado) antes da substituicao.
    """
    if paths_equal(source, destination):
        return
    if destination.exists() or destination.is_symlink():
        if backup_dir is not None:
            backup_copy(destination, backup_dir)
        remove_path(destination)
    copy_path(source, destination)


def resolve_target(path: Path) -> Path:
    """Resolve o caminho final sem falhar quando o alvo nao existe."""
    return path.resolve(strict=False)


def link_target(destination: Path) -> Path | None:
    """Retorna o alvo atual quando destination e symlink; None se nao for."""
    if not destination.is_symlink():
        return None
    try:
        return resolve_target(destination)
    except OSError:
        return None


def link_one(source: Path, destination: Path, backup_dir: Path) -> None:
    """Cria symlink destination -> source com backup do destino divergente."""
    source_resolved = resolve_target(source)
    current = link_target(destination)
    if current is not None and current == source_resolved:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    backup_move(destination, backup_dir)
    destination.symlink_to(
        source_resolved,
        target_is_directory=source_resolved.is_dir(),
    )
