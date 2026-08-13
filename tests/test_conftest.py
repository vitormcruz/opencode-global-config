import os
from pathlib import Path

import pytest


REAL_HOME = Path.home()


@pytest.mark.unit
def test_repo_root_fixture_points_to_repository(repo_root):
    assert repo_root == Path(__file__).parents[1]
    assert (repo_root / "pyproject.toml").is_file()


@pytest.mark.unit
def test_isolated_home_fixture_does_not_use_real_home(isolated_home):
    assert isolated_home.is_dir()
    assert Path(os.environ["HOME"]) == isolated_home
    assert Path.home() == isolated_home
    assert isolated_home != REAL_HOME


@pytest.mark.unit
def test_playwright_cache_override_never_points_to_isolated_home(
    isolated_home,
):
    cache = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")

    if cache:
        assert Path(cache) != isolated_home / ".cache" / "ms-playwright"


@pytest.mark.unit
def test_huggingface_cache_override_reuses_existing_cache(
    isolated_home,
):
    configured_cache = os.environ.get("HF_HOME")
    default_cache = REAL_HOME / ".cache" / "huggingface"

    if default_cache.is_dir() and configured_cache is None:
        pytest.fail("HF_HOME nao aponta para o cache Hugging Face existente")

    if configured_cache:
        assert Path(configured_cache) != isolated_home / ".cache" / "huggingface"


@pytest.mark.unit
def test_every_test_uses_an_isolated_home():
    assert Path.home() != REAL_HOME


@pytest.mark.unit
def test_fake_repo_fixture_creates_files_in_isolated_tree(fake_repo):
    repository = fake_repo(
        {
            "agents/example.md": "# Agent",
            "skills/example/SKILL.md": "---\nname: example\n---\n",
        }
    )

    assert repository.is_dir()
    assert (repository / "agents/example.md").read_text() == "# Agent"
    assert (repository / "skills/example/SKILL.md").is_file()
