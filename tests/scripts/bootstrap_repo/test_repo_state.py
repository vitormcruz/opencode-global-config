"""Valida o estado do repositorio depois de executar o adapter OpenCode."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from collections.abc import Iterator
from unittest.mock import patch
from uuid import uuid4

import pytest

from fake_winreg import FakeWinreg
from platform_requirements import requires_windows
from opencode_config.adapters import opencode as opencode_cli
from opencode_config.lib import windows_env
from opencode_config.lib.sync import paths_equal


pytestmark = pytest.mark.integration


@dataclass(frozen=True)
class RepoState:
    repository: Path
    home: Path
    config_dir: Path
    bashrc: Path
    environment: dict[str, str]
    registry: FakeWinreg | None


@pytest.fixture(scope="module")
def bootstrapped_repo_state(
    repo_root: Path,
) -> Iterator[RepoState]:
    home = repo_root / f".pytest-repo-state-home-{os.getpid()}-{uuid4().hex}"
    home.mkdir()
    try:
        bashrc = home / ".bashrc"
        if os.name == "posix":
            bashrc.touch()
        environment = os.environ.copy()
        fake_bin = home / "bin"
        fake_bin.mkdir()
        fake_opencode = fake_bin / (
            "opencode.cmd" if os.name == "nt" else "opencode"
        )
        if os.name == "nt":
            fake_opencode.write_text("@echo off\r\nexit /b 0\r\n", encoding="ascii")
        else:
            fake_opencode.write_text("#!/bin/sh\nexit 0\n", encoding="ascii")
            fake_opencode.chmod(0o755)
        environment.update(
            {
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "OPENCODE_SKIP_DEPS": "1",
                "OPENCODE_SKIP_CRAWL4AI": "1",
                "OPENCODE_SKIP_CODEBASE_MEMORY": "1",
                "OPENCODE_SKIP_DOCTREE": "1",
                "PYTHONPATH": str(repo_root / "src"),
                "PATH": f"{fake_bin}{os.pathsep}{environment.get('PATH', '')}",
            }
        )

        state = RepoState(
            repository=repo_root,
            home=home,
            config_dir=home / ".config" / "opencode",
            bashrc=bashrc,
            environment=environment,
            registry=FakeWinreg() if os.name == "nt" else None,
        )
        result = _run_opencode_adapter(state)

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
            registry=state.registry,
        )
    finally:
        shutil.rmtree(home, ignore_errors=True)


def _run_opencode_adapter(state: RepoState) -> subprocess.CompletedProcess[str]:
    if os.name == "nt":
        if state.registry is None:
            pytest.fail("O teste Windows precisa de um registro falso.")
        with (
            patch.dict(sys.modules, {"winreg": state.registry}),
            patch.object(Path, "home", return_value=state.home),
            patch(
                "opencode_config.harnesses.opencode.shutil.which",
                return_value=str(state.home / "bin" / "opencode.cmd"),
            ),
            patch.object(
                windows_env,
                "broadcast_environment_change",
                return_value=None,
            ),
        ):
            status, stdout, stderr = opencode_cli.run_cli(
                [
                    "--yes",
                    "--repo-root",
                    str(state.repository),
                ]
            )
        return subprocess.CompletedProcess(
            args=[],
            returncode=status,
            stdout=stdout,
            stderr=stderr,
        )

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


def _assert_materialized_path(destination: Path, source: Path) -> None:
    if os.name == "posix":
        assert destination.is_symlink()
        assert destination.resolve() == source.resolve()
        return

    assert destination.exists()
    assert not destination.is_symlink()
    assert paths_equal(source, destination)


def test_repo_state_agents_materialization_matches_platform(
    bootstrapped_repo_state: RepoState,
) -> None:
    destination = bootstrapped_repo_state.config_dir / "agents"
    _assert_materialized_path(
        destination,
        bootstrapped_repo_state.repository / "harness-conf" / "agents",
    )


def test_repo_state_commands_materialization_matches_platform(
    bootstrapped_repo_state: RepoState,
) -> None:
    destination = bootstrapped_repo_state.config_dir / "commands"
    _assert_materialized_path(
        destination,
        bootstrapped_repo_state.repository / "harness-conf" / "commands",
    )


def test_repo_state_opencode_json_matches_a_valid_provisioning_state(
    bootstrapped_repo_state: RepoState,
) -> None:
    destination = bootstrapped_repo_state.config_dir / "opencode.json"
    canonical_config = (
        bootstrapped_repo_state.repository / "harness-conf" / "opencode.json"
    )

    if destination.is_symlink():
        assert destination.resolve() == canonical_config.resolve()
        return

    assert destination.is_file()
    assert not destination.is_symlink()
    canonical = json.loads(canonical_config.read_text(encoding="utf-8"))
    expected = dict(canonical)
    if isinstance(expected.get("mcp"), dict):
        filtered_servers = {
            name: server
            for name, server in expected["mcp"].items()
            if name != "ai-memory"
        }
        if filtered_servers:
            expected["mcp"] = filtered_servers
        else:
            expected.pop("mcp")
    actual = json.loads(destination.read_text(encoding="utf-8"))

    assert actual == expected
    assert "ai-memory" not in actual.get("mcp", {})


def test_repo_state_skills_materialization_matches_platform(
    bootstrapped_repo_state: RepoState,
) -> None:
    destination = bootstrapped_repo_state.config_dir / "skills"
    _assert_materialized_path(
        destination,
        bootstrapped_repo_state.repository / "harness-conf" / "skills",
    )


def test_repo_state_scripts_materialization_matches_platform(
    bootstrapped_repo_state: RepoState,
) -> None:
    destination = bootstrapped_repo_state.config_dir / "scripts"
    if os.name == "posix":
        assert destination.is_symlink()
        assert destination.resolve() == (
            bootstrapped_repo_state.repository / "scripts"
        ).resolve()
    else:
        assert not destination.exists()


def test_repo_state_global_agents_file_is_not_a_symlink(
    bootstrapped_repo_state: RepoState,
) -> None:
    destination = bootstrapped_repo_state.config_dir / "AGENTS.md"
    assert destination.exists()
    assert not destination.is_symlink()


def test_repo_state_bashrc_enables_exa(
    bootstrapped_repo_state: RepoState,
) -> None:
    if os.name == "posix":
        assert "OPENCODE_ENABLE_EXA=1" in (
            bootstrapped_repo_state.bashrc.read_text(encoding="utf-8")
        )
    else:
        assert not bootstrapped_repo_state.bashrc.exists()


@requires_windows
def test_repo_state_windows_persists_exa_in_fake_registry(
    bootstrapped_repo_state: RepoState,
) -> None:
    assert bootstrapped_repo_state.registry is not None
    assert bootstrapped_repo_state.registry.values["OPENCODE_ENABLE_EXA"] == "1"


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


def test_repo_state_opencode_json_is_readable(
    bootstrapped_repo_state: RepoState,
) -> None:
    assert (bootstrapped_repo_state.config_dir / "opencode.json").is_file()


def test_repo_state_agents_md_is_regular_file_with_base_content(
    bootstrapped_repo_state: RepoState,
) -> None:
    agents_md = bootstrapped_repo_state.config_dir / "AGENTS.md"

    assert agents_md.is_file()
    assert not agents_md.is_symlink()
    content = agents_md.read_text(encoding="utf-8")
    assert content.startswith("# Regras Globais")
    assert "## Comunicação" in content


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
