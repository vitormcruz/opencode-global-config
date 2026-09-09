"""Testes dos utilitarios de sincronizacao compartilhados pelos harnesses."""

from pathlib import Path

import pytest

from opencode_config.lib.sync import (
    backup_copy,
    backup_move,
    copy_path,
    link_one,
    link_target,
    paths_equal,
    remove_path,
    sync_path,
)


def make_tree(root: Path) -> tuple[Path, Path]:
    source = root / "source"
    (source / "inner").mkdir(parents=True)
    (source / "a.txt").write_text("conteudo a", encoding="utf-8")
    (source / "inner" / "b.txt").write_text("conteudo b", encoding="utf-8")
    return source, source / "a.txt"


@pytest.mark.unit
def test_backup_move_replaces_file_content_and_removes_original(
    tmp_path: Path,
) -> None:
    target = tmp_path / "alvo.txt"
    target.write_text("original", encoding="utf-8")
    backup_dir = tmp_path / "backup"

    backup_move(target, backup_dir)

    assert not target.exists()
    saved = backup_dir / "alvo.txt"
    assert saved.read_text(encoding="utf-8") == "original"


@pytest.mark.unit
def test_backup_copy_keeps_original(tmp_path: Path) -> None:
    target = tmp_path / "alvo.txt"
    target.write_text("original", encoding="utf-8")
    backup_dir = tmp_path / "backup"

    backup_copy(target, backup_dir)

    assert target.read_text(encoding="utf-8") == "original"
    assert (backup_dir / "alvo.txt").read_text(encoding="utf-8") == "original"


@pytest.mark.unit
def test_backup_of_missing_path_is_noop(tmp_path: Path) -> None:
    backup_dir = tmp_path / "backup"

    backup_move(tmp_path / "inexistente", backup_dir)
    backup_copy(tmp_path / "inexistente", backup_dir)

    assert not backup_dir.exists()


@pytest.mark.unit
def test_backup_uses_incremental_suffix_when_name_is_taken(
    tmp_path: Path,
) -> None:
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    (backup_dir / "alvo.txt").write_text("primeiro", encoding="utf-8")
    target = tmp_path / "alvo.txt"
    target.write_text("segundo", encoding="utf-8")

    backup_move(target, backup_dir)

    assert (backup_dir / "alvo.txt.1").read_text(encoding="utf-8") == "segundo"


@pytest.mark.unit
def test_backup_accepts_symlink_destination(tmp_path: Path) -> None:
    real = tmp_path / "real.txt"
    real.write_text("conteudo", encoding="utf-8")
    link = tmp_path / "atalho"
    link.symlink_to(real)
    backup_dir = tmp_path / "backup"

    backup_move(link, backup_dir)

    assert not link.exists()
    assert (backup_dir / "atalho").is_symlink()


@pytest.mark.unit
def test_copy_path_reproduces_tree_and_file(tmp_path: Path) -> None:
    source, _ = make_tree(tmp_path)

    copy_path(source, tmp_path / "copia-arvore")
    copy_path(source / "a.txt", tmp_path / "copia-arquivo.txt")

    assert (tmp_path / "copia-arvore" / "inner" / "b.txt").read_text(
        encoding="utf-8"
    ) == "conteudo b"
    assert (tmp_path / "copia-arquivo.txt").read_text(
        encoding="utf-8"
    ) == "conteudo a"


@pytest.mark.unit
def test_copy_path_preserves_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real.txt"
    real.write_text("conteudo", encoding="utf-8")
    source = tmp_path / "atalho"
    source.symlink_to(real)

    copy_path(source, tmp_path / "copia-do-atalho")

    copied = tmp_path / "copia-do-atalho"
    assert copied.is_symlink()
    assert copied.resolve() == real.resolve()


@pytest.mark.unit
def test_remove_path_handles_file_symlink_and_directory(
    tmp_path: Path,
) -> None:
    file = tmp_path / "arquivo.txt"
    file.write_text("x", encoding="utf-8")
    remove_path(file)
    assert not file.exists()

    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "atalho"
    link.symlink_to(real, target_is_directory=True)
    remove_path(link)
    assert not link.is_symlink()
    assert real.is_dir()

    remove_path(real)
    assert not real.exists()


@pytest.mark.unit
def test_sync_path_copies_tree_and_deletes_extra_entries(tmp_path: Path) -> None:
    source, _ = make_tree(tmp_path)
    destination = tmp_path / "destino"
    destination.mkdir()
    (destination / "extra.txt").write_text("velho", encoding="utf-8")

    sync_path(source, destination)

    assert (destination / "a.txt").read_text(encoding="utf-8") == "conteudo a"
    assert (destination / "inner" / "b.txt").read_text(
        encoding="utf-8"
    ) == "conteudo b"
    assert not (destination / "extra.txt").exists()


@pytest.mark.unit
def test_sync_path_is_idempotent_without_new_backup(tmp_path: Path) -> None:
    source, _ = make_tree(tmp_path)
    destination = tmp_path / "destino"
    backup_dir = tmp_path / "backup"

    sync_path(source, destination, backup_dir)
    sync_path(source, destination, backup_dir)

    assert not backup_dir.exists()
    assert paths_equal(source, destination)


@pytest.mark.unit
def test_sync_path_updates_changed_file_and_backs_up_previous(
    tmp_path: Path,
) -> None:
    source = tmp_path / "arquivo.txt"
    source.write_text("novo conteudo", encoding="utf-8")
    destination = tmp_path / "destino.txt"
    destination.write_text("conteudo antigo", encoding="utf-8")
    backup_dir = tmp_path / "backup"

    sync_path(source, destination, backup_dir)

    assert destination.read_text(encoding="utf-8") == "novo conteudo"
    assert (backup_dir / "destino.txt").read_text(
        encoding="utf-8"
    ) == "conteudo antigo"


@pytest.mark.unit
def test_paths_equal_detects_content_difference(tmp_path: Path) -> None:
    source = tmp_path / "fonte.txt"
    source.write_text("igual", encoding="utf-8")
    same = tmp_path / "igual.txt"
    same.write_text("igual", encoding="utf-8")
    other = tmp_path / "diferente.txt"
    other.write_text("diferente", encoding="utf-8")

    assert paths_equal(source, same)
    assert not paths_equal(source, other)
    assert not paths_equal(source, tmp_path / "inexistente.txt")


@pytest.mark.unit
def test_paths_equal_detects_extra_entry_in_tree(tmp_path: Path) -> None:
    source, _ = make_tree(tmp_path)
    destination = tmp_path / "destino"
    copy_path(source, destination)
    (destination / "extra.txt").write_text("extra", encoding="utf-8")

    assert not paths_equal(source, destination)


@pytest.mark.unit
def test_link_one_creates_symlink_and_backs_up_divergent_destination(
    tmp_path: Path,
) -> None:
    source = tmp_path / "fonte"
    source.mkdir()
    destination = tmp_path / "destino"
    destination.write_text("arquivo antigo", encoding="utf-8")
    backup_dir = tmp_path / "backup"

    link_one(source, destination, backup_dir)

    assert destination.is_symlink()
    assert destination.resolve() == source.resolve()
    assert (backup_dir / "destino").read_text(
        encoding="utf-8"
    ) == "arquivo antigo"


@pytest.mark.unit
def test_link_one_is_noop_when_already_pointing_to_source(
    tmp_path: Path,
) -> None:
    source = tmp_path / "fonte"
    source.mkdir()
    destination = tmp_path / "destino"
    destination.symlink_to(source, target_is_directory=True)
    backup_dir = tmp_path / "backup"

    link_one(source, destination, backup_dir)

    assert not backup_dir.exists()
    assert link_target(destination) == source.resolve()


@pytest.mark.unit
def test_link_target_returns_none_for_regular_paths(tmp_path: Path) -> None:
    arquivo = tmp_path / "arquivo.txt"
    arquivo.write_text("x", encoding="utf-8")

    assert link_target(arquivo) is None
    assert link_target(tmp_path / "inexistente") is None
