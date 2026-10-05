"""Fixtures compartilhadas das suites pytest."""

from collections.abc import Callable, Mapping
import os
from pathlib import Path
import sys

import pytest

from fake_winreg import FakeWinreg
from environment_guard import environment_problem, normalize_windows_path
from taxonomy import translate_all_alias


def pytest_configure(config: pytest.Config) -> None:
    """Traduz o atalho `-m all` antes da selecao de testes.

    A traducao e literal (ver `taxonomy.translate_all_alias`): o token
    `all` vira `unit or integration` e o restante da expressao pedida
    permanece inalterado.
    """

    config.option.markexpr = translate_all_alias(config.option.markexpr)


def pytest_sessionstart(session: pytest.Session) -> None:
    """Recusa rodar fora da .venv do checkout ou com pacote de outro clone."""

    if os.name == "nt":
        os.environ["PATH"] = normalize_windows_path(os.environ.get("PATH", ""))

    import opencode_config

    problem = environment_problem(
        repo_root=Path(__file__).resolve().parents[1],
        package_file=Path(opencode_config.__file__),
        prefix=Path(sys.prefix),
    )
    if problem is not None:
        pytest.exit(problem, returncode=3)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Retorna a raiz do repositorio sob teste."""

    return Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def fake_winreg(monkeypatch: pytest.MonkeyPatch) -> FakeWinreg:
    """Injeta um winreg falso em sys.modules; nenhum registro real e tocado."""

    fake = FakeWinreg()
    monkeypatch.setitem(sys.modules, "winreg", fake)
    return fake


@pytest.fixture(autouse=True)
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Cria HOME temporario e ajusta aliases usados nos dois SOs."""

    original_home = Path.home()
    original_local_app_data = os.environ.get("LOCALAPPDATA")
    home = tmp_path / ".isolated-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("LOCALAPPDATA", str(home / "AppData" / "Local"))
    monkeypatch.setenv("APPDATA", str(home / "AppData" / "Roaming"))
    if "PLAYWRIGHT_BROWSERS_PATH" not in os.environ:
        browser_cache = (
            Path(original_local_app_data) / "ms-playwright"
            if original_local_app_data
            else original_home / ".cache" / "ms-playwright"
        )
        if browser_cache.is_dir():
            monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    if "HF_HOME" not in os.environ:
        huggingface_cache = original_home / ".cache" / "huggingface"
        if huggingface_cache.is_dir():
            monkeypatch.setenv("HF_HOME", str(huggingface_cache))
    if "GRADLE_USER_HOME" not in os.environ:
        gradle_cache = original_home / ".gradle"
        if gradle_cache.is_dir():
            monkeypatch.setenv("GRADLE_USER_HOME", str(gradle_cache))
    if "GRADLE_MAVEN_MIRROR" not in os.environ:
        m2_settings = original_home / ".m2" / "settings.xml"
        if m2_settings.is_file():
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(m2_settings)
                root = tree.getroot()
                for mirror in root.findall(".//{*}mirror"):
                    mirror_of = mirror.find("{*}mirrorOf")
                    url = mirror.find("{*}url")
                    if (
                        mirror_of is not None
                        and mirror_of.text in ("*", "central")
                        and url is not None
                        and url.text
                    ):
                        monkeypatch.setenv("GRADLE_MAVEN_MIRROR", url.text.strip())
                        break
            except Exception:
                pass
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
