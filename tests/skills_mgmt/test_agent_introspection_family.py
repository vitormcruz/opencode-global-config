"""Família agent-introspection-debugging no CLI harness-skills."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import subprocess

import pytest

from opencode_config.cli import skills_sync


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _commit_all(repository: Path, message: str) -> None:
    subprocess.run(
        ["git", "-C", str(repository), "add", "--all"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repository), "commit", "--quiet", "-m", message],
        check=True,
    )


def _git_upstream(tmp_path: Path, files: dict[str, str]) -> Path:
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    for relative_path, content in files.items():
        file_path = upstream / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main", str(upstream)],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(upstream), "config", "user.email", "test@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(upstream), "config", "user.name", "Test User"],
        check=True,
    )
    _commit_all(upstream, "base")
    return upstream


def _upstream_with_change(
    tmp_path: Path,
    files: dict[str, str],
    changes: dict[str, str],
) -> tuple[Path, str]:
    upstream = _git_upstream(tmp_path, files)
    base_sha = _git(upstream, "rev-parse", "HEAD")
    for relative_path, content in changes.items():
        file_path = upstream / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
    _commit_all(upstream, "upstream update")
    return upstream, base_sha


def _write_metadata(repo: Path, sha: str) -> Path:
    metadata = (
        repo
        / "harness-conf"
        / "skills"
        / "agent-introspection-debugging"
        / "UPSTREAM.md"
    )
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(
        "\n".join(
            [
                "# Metadados do Upstream",
                "repositorio: fixture",
                "branch: main",
                f"commit: {sha}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return metadata


@pytest.mark.unit
def test_family_registered_in_specs() -> None:
    spec = skills_sync.SPECS["agent-introspection-debugging"]

    assert spec.repository == "https://github.com/affaan-m/ECC.git"
    assert spec.branch == "main"


@pytest.mark.unit
def test_diff_paths_scope_to_skill_subdirectory() -> None:
    assert skills_sync._skill_diff_paths(
        "agent-introspection-debugging", "agent-introspection-debugging"
    ) == (
        "skills/agent-introspection-debugging/",
        "LICENSE",
    )


@pytest.mark.unit
def test_sync_copies_license_and_preserves_adapted_skill_md(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    local_skill = repo / "harness-conf/skills/agent-introspection-debugging"
    local_skill.mkdir(parents=True)
    (local_skill / "SKILL.md").write_text(
        "versao adaptada PT-BR", encoding="utf-8"
    )
    upstream = _git_upstream(
        tmp_path,
        {
            "LICENSE": "MIT License",
            "skills/agent-introspection-debugging/SKILL.md": "versao upstream",
        },
    )

    result = skills_sync.sync_skill(
        "agent-introspection-debugging", repo, upstream
    )

    assert result.status == "success"
    assert (
        (local_skill / "SKILL.md").read_text(encoding="utf-8")
        == "versao adaptada PT-BR"
    )
    assert (
        (local_skill / "LICENSE").read_text(encoding="utf-8")
        == "MIT License"
    )
    metadata = (local_skill / "UPSTREAM.md").read_text(encoding="utf-8")
    assert "repositorio: https://github.com/affaan-m/ECC.git" in metadata
    assert "harness-skills sync agent-introspection-debugging" in metadata
    assert "- LICENSE" in metadata


@pytest.mark.integration
def test_detect_ignores_changes_outside_skill_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    upstream, base_sha = _upstream_with_change(
        tmp_path,
        {
            "LICENSE": "MIT License",
            "skills/agent-introspection-debugging/SKILL.md": "base",
            "skills/outra-skill/SKILL.md": "base",
        },
        {"skills/outra-skill/SKILL.md": "mudou"},
    )
    repo = tmp_path / "repo"
    _write_metadata(repo, base_sha)
    monkeypatch.setitem(
        skills_sync.SPECS,
        "agent-introspection-debugging",
        skills_sync.SyncSpec(
            "agent-introspection-debugging", upstream.as_uri(), "main"
        ),
    )

    output = StringIO()
    error = StringIO()
    status = skills_sync.run(
        [
            "detect",
            "agent-introspection-debugging",
            "--repo-root",
            str(repo),
        ],
        output=output,
        error=error,
    )

    assert status == 0, error.getvalue()
    assert "sem mudanças na família" in output.getvalue()


@pytest.mark.integration
def test_detect_reports_change_inside_skill_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    upstream, base_sha = _upstream_with_change(
        tmp_path,
        {
            "LICENSE": "MIT License",
            "skills/agent-introspection-debugging/SKILL.md": "base",
        },
        {"skills/agent-introspection-debugging/SKILL.md": "mudou"},
    )
    repo = tmp_path / "repo"
    _write_metadata(repo, base_sha)
    monkeypatch.setitem(
        skills_sync.SPECS,
        "agent-introspection-debugging",
        skills_sync.SyncSpec(
            "agent-introspection-debugging", upstream.as_uri(), "main"
        ),
    )

    output = StringIO()
    error = StringIO()
    status = skills_sync.run(
        [
            "detect",
            "agent-introspection-debugging",
            "--repo-root",
            str(repo),
        ],
        output=output,
        error=error,
    )

    assert status == 0, error.getvalue()
    assert "status: mudanças" in output.getvalue()
    assert "skills/agent-introspection-debugging/SKILL.md" in (
        output.getvalue()
    )


@pytest.mark.integration
def test_detect_reports_change_in_root_license(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    upstream, base_sha = _upstream_with_change(
        tmp_path,
        {
            "LICENSE": "MIT License",
            "skills/agent-introspection-debugging/SKILL.md": "base",
        },
        {"LICENSE": "MIT License\n\nCopyright atualizado"},
    )
    repo = tmp_path / "repo"
    _write_metadata(repo, base_sha)
    monkeypatch.setitem(
        skills_sync.SPECS,
        "agent-introspection-debugging",
        skills_sync.SyncSpec(
            "agent-introspection-debugging", upstream.as_uri(), "main"
        ),
    )

    output = StringIO()
    error = StringIO()
    status = skills_sync.run(
        [
            "detect",
            "agent-introspection-debugging",
            "--repo-root",
            str(repo),
        ],
        output=output,
        error=error,
    )

    assert status == 0, error.getvalue()
    assert "status: mudanças" in output.getvalue()
    assert "LICENSE" in output.getvalue()
