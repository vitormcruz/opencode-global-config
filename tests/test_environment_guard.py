"""Contrato do guarda que exige a .venv do próprio checkout."""

import os
from pathlib import Path

import pytest

from environment_guard import environment_problem, normalize_windows_path


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    (tmp_path / "src" / "opencode_config").mkdir(parents=True)
    (tmp_path / ".venv").mkdir()
    return tmp_path


@pytest.mark.unit
def test_environment_guard_accepts_checkout_venv_and_checkout_package(
    checkout: Path,
) -> None:
    problem = environment_problem(
        repo_root=checkout,
        package_file=checkout / "src" / "opencode_config" / "__init__.py",
        prefix=checkout / ".venv",
    )

    assert problem is None


@pytest.mark.unit
def test_environment_guard_rejects_package_from_another_clone(
    checkout: Path,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    other = tmp_path_factory.mktemp("other-clone")
    package_file = other / "src" / "opencode_config" / "__init__.py"

    problem = environment_problem(
        repo_root=checkout,
        package_file=package_file,
        prefix=checkout / ".venv",
    )

    assert problem is not None
    assert str(package_file) in problem
    assert str(checkout / "src") in problem
    assert "pip install -e ." in problem


@pytest.mark.unit
def test_environment_guard_rejects_interpreter_outside_checkout_venv(
    checkout: Path,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    global_prefix = tmp_path_factory.mktemp("global-python")

    problem = environment_problem(
        repo_root=checkout,
        package_file=checkout / "src" / "opencode_config" / "__init__.py",
        prefix=global_prefix,
    )

    assert problem is not None
    assert str(global_prefix) in problem
    assert str(checkout / ".venv") in problem
    assert "python -m venv .venv" in problem


@pytest.mark.unit
def test_windows_path_normalization_drops_missing_entries_above_cmd_limit(
    tmp_path: Path,
) -> None:
    existing = tmp_path / "node"
    existing.mkdir()
    inherited = os.pathsep.join(
        [str(existing), *(str(tmp_path / f"missing-{index}") for index in range(3))]
    )

    normalized = normalize_windows_path(
        inherited,
        path_limit=len(str(existing)),
    )

    assert normalized == str(existing)


@pytest.mark.unit
def test_windows_path_normalization_preserves_entries_below_cmd_limit(
    tmp_path: Path,
) -> None:
    inherited = os.pathsep.join(
        [str(tmp_path / "missing-a"), str(tmp_path / "missing-b")]
    )

    normalized = normalize_windows_path(inherited, path_limit=len(inherited))

    assert normalized == inherited
