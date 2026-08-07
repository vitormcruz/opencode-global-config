"""Fixtures compartilhadas das suites pytest."""

from collections.abc import Callable, Mapping
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Retorna a raiz do repositorio sob teste."""

    return Path(__file__).resolve().parents[1]


@pytest.fixture
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Cria HOME temporario e ajusta aliases usados nos dois SOs."""

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    return home


@pytest.fixture
def fake_repo(tmp_path: Path) -> Callable[[Mapping[str, str] | None], Path]:
    """Retorna factory para repositorios falsos isolados por teste."""

    created_repositories = 0

    def create(files: Mapping[str, str] | None = None) -> Path:
        nonlocal created_repositories
        repository = tmp_path / f"fake-repo-{created_repositories}"
        created_repositories += 1
        repository.mkdir()

        for relative_path, content in (files or {}).items():
            file_path = repository / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

        return repository

    return create
