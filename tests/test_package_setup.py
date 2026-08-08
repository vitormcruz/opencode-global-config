from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).parents[1]


@pytest.mark.unit
def test_project_declares_src_package_and_provisional_entry_point():
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text()

    assert "[project]" in pyproject
    assert 'name = "opencode-config"' in pyproject
    assert 'requires-python = ">=3.10"' in pyproject
    assert "[tool.setuptools.packages.find]" in pyproject
    assert 'where = ["src"]' in pyproject
    assert "[project.scripts]" in pyproject
    assert 'opencode-config-check = "opencode_config:main"' in pyproject


@pytest.mark.unit
def test_dev_requirements_include_pytest():
    requirements = (REPOSITORY_ROOT / "requirements-dev.txt").read_text()

    assert any(
        line.strip().lower().startswith("pytest")
        for line in requirements.splitlines()
    )


@pytest.mark.unit
def test_project_registers_required_pytest_markers(pytestconfig):
    registered_markers = set(pytestconfig.getini("markers"))

    for marker in ("unit", "tools", "opencode", "copilot"):
        assert any(entry.startswith(f"{marker}:") for entry in registered_markers)


@pytest.mark.unit
def test_project_registers_doc_extract_entrypoint():
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text()

    assert 'opencode-doc-extract = "opencode_config.cli.doc_extract:main"' in pyproject


@pytest.mark.unit
def test_project_registers_md_export_entrypoint():
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text()

    assert 'opencode-md-export = "opencode_config.cli.md_export:main"' in pyproject


@pytest.mark.unit
def test_project_registers_svgtoimage_entrypoint():
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text()

    assert 'opencode-svgtoimage = "opencode_config.cli.svgtoimage:main"' in pyproject


@pytest.mark.unit
def test_project_registers_browser_test_entrypoint():
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text()

    assert 'opencode-browser-test = "opencode_config.cli.browser_test:main"' in pyproject


@pytest.mark.unit
def test_project_registers_bootstrap_entrypoint():
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text()

    assert (
        'opencode-bootstrap = "opencode_config.bootstrap.main:main"'
        in pyproject
    )


@pytest.mark.unit
def test_python_artifacts_are_ignored():
    gitignore = (REPOSITORY_ROOT / ".gitignore").read_text()

    for pattern in (".venv/", "*.egg-info/", "__pycache__/"):
        assert pattern in gitignore


@pytest.mark.unit
def test_package_imports():
    import opencode_config

    assert opencode_config.__package__ == "opencode_config"
