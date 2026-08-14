"""Valida o estado do repositorio depois de executar o adapter OpenCode."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys
from collections.abc import Iterator
from uuid import uuid4

import pytest


pytestmark = pytest.mark.opencode


@dataclass(frozen=True)
class RepoState:
    repository: Path
    home: Path
    config_dir: Path
    bashrc: Path
    environment: dict[str, str]


@pytest.fixture(scope="module")
def bootstrapped_repo_state(
    repo_root: Path,
) -> Iterator[RepoState]:
    home = repo_root / f".pytest-repo-state-home-{os.getpid()}-{uuid4().hex}"
    home.mkdir()
    try:
        bashrc = home / ".bashrc"
        bashrc.touch()
        environment = os.environ.copy()
        environment.update(
            {
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "OPENCODE_SKIP_DEPS": "1",
                "OPENCODE_SKIP_CRAWL4AI": "1",
                "OPENCODE_SKIP_CODEBASE_MEMORY": "1",
                "OPENCODE_SKIP_DOCTREE": "1",
                "PYTHONPATH": str(repo_root / "src"),
            }
        )

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "opencode_config.adapters.opencode",
                    "--yes",
                    "--repo-root",
                    str(repo_root),
                ],
                cwd=repo_root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as problem:
            pytest.fail(
                "Nao foi possivel executar o adapter OpenCode com Python 3.10+: "
                f"{problem}. Instale Python 3.10+ e execute pytest no ambiente "
                "configurado."
            )

        if result.returncode != 0:
            pytest.fail(
                "O bootstrap inicial do adapter OpenCode falhou "
                f"(codigo {result.returncode}).\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

        yield RepoState(
            repository=repo_root,
            home=home,
            config_dir=home / ".config" / "opencode",
            bashrc=bashrc,
            environment=environment,
        )
    finally:
        shutil.rmtree(home, ignore_errors=True)


def _run_opencode_adapter(state: RepoState) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "opencode_config.adapters.opencode",
                "--yes",
                "--repo-root",
                str(state.repository),
            ],
            cwd=state.repository,
            env=state.environment,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as problem:
        pytest.fail(
            "Nao foi possivel executar o adapter OpenCode com Python 3.10+: "
            f"{problem}. Instale Python 3.10+ e execute pytest no ambiente "
            "configurado."
        )


def test_repo_state_opencode_adapter_yes_succeeds(
    bootstrapped_repo_state: RepoState,
) -> None:
    result = _run_opencode_adapter(bootstrapped_repo_state)

    assert result.returncode == 0, (
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_repo_state_config_directory_exists(
    bootstrapped_repo_state: RepoState,
) -> None:
    assert bootstrapped_repo_state.config_dir.is_dir()


def test_repo_state_agents_symlink_points_to_repo(
    bootstrapped_repo_state: RepoState,
) -> None:
    destination = bootstrapped_repo_state.config_dir / "agents"
    assert destination.is_symlink() and destination.resolve() == (
        bootstrapped_repo_state.repository / "agents"
    ).resolve()


def test_repo_state_commands_symlink_points_to_repo(
    bootstrapped_repo_state: RepoState,
) -> None:
    destination = bootstrapped_repo_state.config_dir / "commands"
    assert destination.is_symlink() and destination.resolve() == (
        bootstrapped_repo_state.repository / "commands"
    ).resolve()


def test_repo_state_opencode_json_symlink_points_to_repo(
    bootstrapped_repo_state: RepoState,
) -> None:
    destination = bootstrapped_repo_state.config_dir / "opencode.json"
    assert destination.is_symlink() and destination.resolve() == (
        bootstrapped_repo_state.repository / "opencode.json"
    ).resolve()


def test_repo_state_skills_symlink_points_to_repo(
    bootstrapped_repo_state: RepoState,
) -> None:
    destination = bootstrapped_repo_state.config_dir / "skills"
    assert destination.is_symlink() and destination.resolve() == (
        bootstrapped_repo_state.repository / "skills"
    ).resolve()


def test_repo_state_scripts_symlink_points_to_repo(
    bootstrapped_repo_state: RepoState,
) -> None:
    destination = bootstrapped_repo_state.config_dir / "scripts"
    assert destination.is_symlink() and destination.resolve() == (
        bootstrapped_repo_state.repository / "scripts"
    ).resolve()


def test_repo_state_global_agents_file_does_not_exist(
    bootstrapped_repo_state: RepoState,
) -> None:
    assert not (bootstrapped_repo_state.config_dir / "AGENTS.md").exists()


def test_repo_state_bashrc_enables_exa(
    bootstrapped_repo_state: RepoState,
) -> None:
    assert "OPENCODE_ENABLE_EXA=1" in bootstrapped_repo_state.bashrc.read_text(
        encoding="utf-8"
    )


def test_repo_state_does_not_create_legacy_test_library_directory(
    bootstrapped_repo_state: RepoState,
) -> None:
    legacy_directory = "ba" + "ts"
    assert not (
        bootstrapped_repo_state.home / ".local" / "lib" / legacy_directory
    ).exists()


def test_repo_state_doctree_instruction_does_not_exist(
    bootstrapped_repo_state: RepoState,
) -> None:
    assert not (
        bootstrapped_repo_state.repository
        / ".github"
        / "copilot-doctree.instructions.md"
    ).exists()


def test_repo_state_opencode_json_is_readable_via_symlink(
    bootstrapped_repo_state: RepoState,
) -> None:
    assert (bootstrapped_repo_state.config_dir / "opencode.json").is_file()


def _strip_jsonc_line_comments(source: str) -> str:
    result: list[str] = []
    in_string = False
    index = 0
    while index < len(source):
        character = source[index]
        if not in_string and character == '"':
            in_string = True
            result.append(character)
            index += 1
            continue
        if in_string and character == "\\":
            result.append(character)
            if index + 1 < len(source):
                result.append(source[index + 1])
            index += 2
            continue
        if in_string and character == '"':
            in_string = False
            result.append(character)
            index += 1
            continue
        if (
            not in_string
            and character == "/"
            and index + 1 < len(source)
            and source[index + 1] == "/"
        ):
            while index < len(source) and source[index] != "\n":
                index += 1
            continue
        result.append(character)
        index += 1
    return "".join(result)


def _jsonc_validation_output(path: Path) -> tuple[bool, str]:
    import json

    try:
        json.loads(
            _strip_jsonc_line_comments(path.read_text(encoding="utf-8"))
        )
    except (OSError, ValueError):
        return False, ""
    return True, "valid"


def test_repo_state_opencode_json_is_valid_jsonc(
    bootstrapped_repo_state: RepoState,
) -> None:
    success, output = _jsonc_validation_output(
        bootstrapped_repo_state.config_dir / "opencode.json"
    )

    assert success
    assert output == "valid"


def test_repo_state_skills_symlink_contains_a_skill(
    bootstrapped_repo_state: RepoState,
) -> None:
    skills_dir = bootstrapped_repo_state.config_dir / "skills"
    try:
        entries = list(skills_dir.iterdir())
        success = True
    except OSError:
        entries = []
        success = False
    assert success
    assert entries


def test_repo_state_each_accessible_skill_has_skill_file(
    bootstrapped_repo_state: RepoState,
) -> None:
    skills_dir = bootstrapped_repo_state.config_dir / "skills"
    skill_directories = list(skills_dir.glob("*/"))
    missing = [
        skill_dir
        for skill_dir in skill_directories
        if not (skill_dir / "SKILL.md").is_file()
    ]

    if not skill_directories:
        missing.append(skills_dir / "*/")
    assert not missing, f"SKILL.md ausente em: {missing[0]}"
