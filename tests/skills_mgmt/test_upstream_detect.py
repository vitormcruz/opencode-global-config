"""Testes da detecção read-only de mudanças em upstreams de skills."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import shutil
import subprocess

import pytest

from opencode_config.cli import skills_sync


def require_git() -> None:
    if shutil.which("git") is None:
        pytest.fail("git ausente no PATH; instale Git para executar os testes de integração")


def git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def upstream_with_change(
    tmp_path: Path,
    files: dict[str, str],
    changes: dict[str, str],
) -> tuple[Path, str, str]:
    require_git()
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
    git(upstream, "config", "user.email", "test@example.com")
    git(upstream, "config", "user.name", "Test User")
    git(upstream, "add", ".")
    git(upstream, "commit", "--quiet", "-m", "base")
    base_sha = git(upstream, "rev-parse", "HEAD")

    if changes:
        for relative_path, content in changes.items():
            file_path = upstream / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        git(upstream, "add", "--all")
        git(upstream, "commit", "--quiet", "-m", "upstream update")
    return upstream, base_sha, git(upstream, "rev-parse", "HEAD")


def write_metadata(
    repo: Path,
    skill: str,
    sha: str | None,
    *,
    frozen: bool = False,
) -> Path:
    metadata = repo / "harness-conf" / "skills" / skill / "UPSTREAM.md"
    metadata.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Metadados do Upstream", "repositorio: fixture", "branch: main"]
    if sha is not None:
        lines.append(f"commit: {sha}")
    if frozen:
        lines.append("sincronizacao: congelada")
    metadata.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return metadata


def set_upstream_spec(
    monkeypatch: pytest.MonkeyPatch,
    family: str,
    upstream: Path,
) -> None:
    monkeypatch.setitem(
        skills_sync.SPECS,
        family,
        skills_sync.SyncSpec(family, upstream.as_uri(), "main"),
    )


def run_detect(repo: Path, family: str = "fixture") -> tuple[int, str, str]:
    output = StringIO()
    error = StringIO()
    status = skills_sync.run(
        ["detect", family, "--repo-root", str(repo)],
        output=output,
        error=error,
    )
    return status, output.getvalue(), error.getvalue()


def repository_snapshot(repo: Path) -> dict[Path, bytes]:
    return {
        path.relative_to(repo): path.read_bytes()
        for path in repo.rglob("*")
        if path.is_file()
    }


@pytest.mark.integration
def test_detect_reports_exact_upstream_changes_by_skill(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    upstream, base_sha, head_sha = upstream_with_change(
        tmp_path,
        {
            "LICENSE": "MIT License\n",
            "skills/fixture/SKILL.md": "conteúdo antigo\n",
            "references/exemplo.md": "referência antiga\n",
        },
        {
            "skills/fixture/SKILL.md": "conteúdo novo\n",
            "references/exemplo.md": "referência nova\n",
        },
    )
    repo = tmp_path / "repo"
    metadata = write_metadata(repo, "fixture", base_sha)
    set_upstream_spec(monkeypatch, "fixture", upstream)

    status, output, error = run_detect(repo)

    assert status == 0, error
    assert "skill: fixture" in output
    assert f"SHA base: {base_sha}" in output
    assert f"SHA upstream: {head_sha}" in output
    assert "skills/fixture/SKILL.md" in output
    assert "references/exemplo.md" in output
    assert "conteúdo antigo" in output
    assert "conteúdo novo" in output
    assert "referência antiga" in output
    assert "referência nova" in output
    assert "NÃO CONFIÁVEL" in output
    assert "aplicação assistida" in output
    assert "writing-for-agents" in output
    assert metadata.read_text(encoding="utf-8").find(base_sha) >= 0


@pytest.mark.integration
def test_detect_is_read_only_repeats_refused_changes_and_cleans_clone(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    upstream, base_sha, head_sha = upstream_with_change(
        tmp_path,
        {"skills/fixture/SKILL.md": "antes\n"},
        {"skills/fixture/SKILL.md": "depois\n"},
    )
    repo = tmp_path / "repo"
    metadata = write_metadata(repo, "fixture", base_sha)
    set_upstream_spec(monkeypatch, "fixture", upstream)
    before = repository_snapshot(repo)
    clone_upstream = skills_sync._clone_upstream
    temporary_paths: list[Path] = []
    clone_commands: list[list[str]] = []
    run_subprocess = subprocess.run

    def record_clone_command(command, *arguments, **options):
        if command[:2] == ["git", "clone"]:
            clone_commands.append(command)
        return run_subprocess(command, *arguments, **options)

    def clone_and_record(spec, **options):
        temporary, clone = clone_upstream(spec, **options)
        temporary_paths.append(Path(temporary.name))
        return temporary, clone

    monkeypatch.setattr(skills_sync.subprocess, "run", record_clone_command)
    monkeypatch.setattr(skills_sync, "_clone_upstream", clone_and_record)

    first_status, first_output, first_error = run_detect(repo)
    second_status, second_output, second_error = run_detect(repo)

    assert first_status == second_status == 0
    assert first_error == second_error == ""
    assert first_output == second_output
    assert f"SHA base: {base_sha}" in first_output
    assert f"SHA upstream: {head_sha}" in first_output
    assert repository_snapshot(repo) == before
    assert metadata.read_text(encoding="utf-8").find(base_sha) >= 0
    assert len(temporary_paths) == 2
    assert all(repo not in temporary.parents for temporary in temporary_paths)
    assert all(not temporary.exists() for temporary in temporary_paths)
    assert len(clone_commands) == 2
    assert all("--no-recurse-submodules" in command for command in clone_commands)
    assert all("--recurse-submodules" not in command for command in clone_commands)


@pytest.mark.integration
def test_detect_keeps_unfrozen_skill_without_freeze_field(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    upstream, base_sha, _ = upstream_with_change(
        tmp_path,
        {"skills/fixture/SKILL.md": "conteúdo anterior\n"},
        {"skills/fixture/SKILL.md": "conteúdo atual\n"},
    )
    repo = tmp_path / "repo"
    metadata = write_metadata(repo, "fixture", base_sha)
    before = metadata.read_bytes()
    set_upstream_spec(monkeypatch, "fixture", upstream)

    status, _output, error = run_detect(repo)

    assert status == 0, error
    assert metadata.read_bytes() == before
    assert "sincronizacao:" not in metadata.read_text(encoding="utf-8")


@pytest.mark.integration
def test_detect_omits_frozen_skills_from_family_changes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    upstream, base_sha, _ = upstream_with_change(
        tmp_path,
        {
            "LICENSE": "MIT License\n",
            "skills/test-driven-development/SKILL.md": "tdd antigo\n",
            "skills/code-review-and-quality/SKILL.md": "review antigo\n",
        },
        {
            "skills/test-driven-development/SKILL.md": "tdd novo\n",
            "skills/code-review-and-quality/SKILL.md": "review novo\n",
        },
    )
    repo = tmp_path / "repo"
    write_metadata(repo, "test-driven-development", base_sha)
    write_metadata(repo, "code-review-and-quality", base_sha, frozen=True)
    set_upstream_spec(monkeypatch, "addyosmani", upstream)

    status, output, error = run_detect(repo, "addyosmani")

    assert status == 0, error
    assert "skill: test-driven-development" in output
    assert "tdd novo" in output
    assert "code-review-and-quality" not in output
    assert "review novo" not in output


@pytest.mark.integration
def test_detect_reports_no_changes_when_base_matches_upstream_head(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    upstream, base_sha, head_sha = upstream_with_change(
        tmp_path,
        {"skills/fixture/SKILL.md": "conteúdo atual\n"},
        {},
    )
    repo = tmp_path / "repo"
    write_metadata(repo, "fixture", head_sha)
    set_upstream_spec(monkeypatch, "fixture", upstream)

    status, output, error = run_detect(repo)

    assert base_sha == head_sha
    assert status == 0, error
    assert "sem mudanças" in output.lower()
    assert "NÃO CONFIÁVEL" not in output


@pytest.mark.parametrize("sha", [None, "sha-invalido"])
@pytest.mark.integration
def test_detect_rejects_missing_or_invalid_base_sha(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sha: str | None,
) -> None:
    repo = tmp_path / "repo"
    write_metadata(repo, "fixture", sha)
    set_upstream_spec(monkeypatch, "fixture", tmp_path / "unused-upstream")

    def clone_not_allowed(_spec, **_options):
        pytest.fail("a detecção validou o SHA antes de clonar o upstream")

    monkeypatch.setattr(skills_sync, "_clone_upstream", clone_not_allowed)

    status, output, error = run_detect(repo)

    assert status == 1
    assert "SHA base" in error
    assert "UPSTREAM.md" in error
    assert "git rev-parse" in error
    assert output == ""


@pytest.mark.integration
def test_detect_expands_shallow_clone_when_base_sha_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    upstream, base_sha, head_sha = upstream_with_change(
        tmp_path,
        {"skills/fixture/SKILL.md": "conteúdo anterior\n"},
        {"skills/fixture/SKILL.md": "conteúdo atual\n"},
    )
    repo = tmp_path / "repo"
    write_metadata(repo, "fixture", base_sha)
    set_upstream_spec(monkeypatch, "fixture", upstream)
    run_git = skills_sync._run_git
    expanded_fetches: list[tuple[str, ...]] = []

    def record_full_clone(repository: Path, *arguments: str) -> str:
        if arguments[0] == "fetch" and "--unshallow" in arguments:
            expanded_fetches.append(arguments)
        return run_git(repository, *arguments)

    monkeypatch.setattr(skills_sync, "_run_git", record_full_clone)

    status, output, error = run_detect(repo)

    assert status == 0, error
    assert expanded_fetches
    assert "--no-recurse-submodules" in expanded_fetches[0]
    assert "--recurse-submodules" not in expanded_fetches[0]
    assert f"SHA upstream: {head_sha}" in output
    assert "conteúdo atual" in output
