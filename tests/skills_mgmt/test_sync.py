import json
import shutil
import subprocess
from io import StringIO
from pathlib import Path

import pytest

from opencode_config.cli import skills_sync


def git_upstream(tmp_path: Path, files: dict[str, str]) -> Path:
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    for relative_path, content in files.items():
        file_path = upstream / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    subprocess.run(["git", "init", "-q", str(upstream)], check=True)
    subprocess.run(
        ["git", "-C", str(upstream), "config", "user.email", "test@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(upstream), "config", "user.name", "Test User"],
        check=True,
    )
    subprocess.run(["git", "-C", str(upstream), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(upstream), "commit", "-qm", "upstream"],
        check=True,
    )
    return upstream


@pytest.mark.unit
def test_opencode_skills_entrypoint_is_registered(repo_root: Path) -> None:
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")

    assert 'opencode-skills = "opencode_config.cli.skills_sync:main"' in pyproject


@pytest.mark.unit
def test_sync_help_returns_success(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        skills_sync.main(["--help"])

    assert raised.value.code == 0
    assert "opencode-skills" in capsys.readouterr().out


@pytest.mark.unit
def test_sync_help_mentions_accessibility_target(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        skills_sync.main(["sync", "--help"])

    assert "accessibility-audit" in capsys.readouterr().out


@pytest.mark.unit
def test_sync_invalid_option_returns_exit_two() -> None:
    with pytest.raises(SystemExit) as raised:
        skills_sync.main(["sync", "accessibility-audit", "--invalid"])

    assert raised.value.code == 2


@pytest.mark.unit
def test_documented_skill_command_has_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("git", 1)

    monkeypatch.setattr(skills_sync.subprocess, "run", timeout)

    status, output = skills_sync._run_documented_command(
        "python -c 'print(1)'",
        tmp_path,
    )

    assert status == 1
    assert "tempo limite" in output


@pytest.mark.unit
def test_documented_command_runs_without_shell(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs

        class Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        return Completed()

    monkeypatch.setattr(skills_sync.subprocess, "run", fake_run)

    status, _ = skills_sync._run_documented_command(
        "python3 scripts/update.py --flag 'valor com espaco'",
        tmp_path,
    )

    assert status == 0
    assert captured["argv"] == [
        "python3",
        "scripts/update.py",
        "--flag",
        "valor com espaco",
    ]
    kwargs = captured["kwargs"]
    assert kwargs.get("shell") is not True
    assert kwargs.get("capture_output") is True
    assert kwargs.get("text") is True
    assert (
        kwargs.get("timeout") == skills_sync.SKILL_COMMAND_TIMEOUT_SECONDS
    )


@pytest.mark.unit
def test_documented_command_rejects_executable_outside_whitelist(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def forbidden(*_args, **_kwargs):
        pytest.fail("subprocess.run nao deveria ser chamado")

    monkeypatch.setattr(skills_sync.subprocess, "run", forbidden)

    status, output = skills_sync._run_documented_command(
        "comando-nao-documentado --flag",
        tmp_path,
    )

    assert status == 1
    assert "fora da lista permitida" in output


@pytest.mark.unit
@pytest.mark.skipif(
    shutil.which("bash") is None,
    reason="exige bash (POSIX)",
)
def test_documented_command_preserves_quoted_arguments(tmp_path: Path) -> None:
    script = tmp_path / "echo_args.sh"
    script.write_text(
        '#!/bin/bash\nfor arg in "$@"; do printf \'%s\\n\' "$arg"; done\n',
        encoding="utf-8",
    )
    script.chmod(0o755)

    status, output = skills_sync._run_documented_command(
        f"bash {script} 'primeiro argumento' segundo",
        tmp_path,
    )

    assert status == 0
    assert "primeiro argumento" in output
    assert "segundo" in output


@pytest.mark.integration
def test_skills_sync_has_no_bandit_shell_true_finding(repo_root: Path) -> None:
    bandit = shutil.which("bandit")
    if bandit is None:
        pytest.fail(
            "bandit nao encontrado no PATH; instale em user-space com: "
            "pipx install bandit"
        )
    target = repo_root / "src" / "opencode_config" / "cli" / "skills_sync.py"
    try:
        completed = subprocess.run(
            [bandit, "-q", "-f", "json", str(target)],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as problem:
        pytest.fail(f"bandit excedeu o tempo limite de 120s: {problem}")
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as problem:
        pytest.fail(
            "bandit nao produziu relatorio JSON valido "
            f"(exit {completed.returncode}): {problem}; stderr: "
            f"{completed.stderr.strip()}"
        )
    shell_findings = [
        result
        for result in report.get("results", [])
        if result.get("test_id") == "B602"
    ]
    locations = ", ".join(
        f"{result.get('filename')}:{result.get('line_number')}"
        for result in shell_findings
    )
    assert shell_findings == [], (
        "bandit B602 (subprocess com shell=True) deve ser eliminado de "
        f"skills_sync.py; encontrados: {locations}"
    )


@pytest.mark.unit
def test_upstream_clone_has_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("git clone", 1)

    monkeypatch.setattr(skills_sync.subprocess, "run", timeout)
    spec = skills_sync.SPECS["prompt-improver"]

    with pytest.raises(skills_sync.SyncError, match="tempo limite"):
        skills_sync._clone_upstream(spec)


@pytest.mark.unit
def test_sync_check_only_returns_non_argument_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    upstream = git_upstream(tmp_path, {"LICENSE": "MIT License"})

    class Temporary:
        def cleanup(self) -> None:
            pass

    monkeypatch.setattr(
        skills_sync,
        "_clone_upstream",
        lambda _spec: (Temporary(), upstream),
    )
    status = skills_sync.run(
        [
            "sync",
            "accessibility-audit",
            "--check-only",
            "--repo-root",
            str(tmp_path / "repo"),
        ],
        output=StringIO(),
        error=StringIO(),
    )

    assert status == 0


@pytest.mark.unit
def test_sync_yes_skips_interactive_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    upstream = git_upstream(
        tmp_path,
        {
            "LICENSE": "MIT License",
            "skills/accessibility-compliance-accessibility-audit/SKILL.md": "skill",
        },
    )

    class Temporary:
        def cleanup(self) -> None:
            pass

    monkeypatch.setattr(
        skills_sync,
        "_clone_upstream",
        lambda _spec: (Temporary(), upstream),
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt: pytest.fail("--yes nao deveria pedir confirmacao"),
    )
    status = skills_sync.run(
        [
            "sync",
            "accessibility-audit",
            "--yes",
            "--repo-root",
            str(tmp_path / "repo"),
        ],
        output=StringIO(),
        error=StringIO(),
    )

    assert status == 0


@pytest.mark.unit
def test_accessibility_skill_file_exists(repo_root: Path) -> None:
    assert (
        repo_root / "harness-conf" / "skills/accessibility-audit/SKILL.md"
    ).is_file()


@pytest.mark.unit
def test_accessibility_upstream_file_exists(repo_root: Path) -> None:
    assert (
        repo_root / "harness-conf" / "skills/accessibility-audit/UPSTREAM.md"
    ).is_file()


@pytest.mark.unit
def test_accessibility_playbook_exists(repo_root: Path) -> None:
    assert (
        repo_root
        / "harness-conf"
        / "skills/accessibility-audit/resources/implementation-playbook.md"
    ).is_file()


@pytest.mark.unit
def test_accessibility_upstream_references_expected_repository(repo_root: Path) -> None:
    metadata = (
        repo_root / "harness-conf" / "skills/accessibility-audit/UPSTREAM.md"
    ).read_text(encoding="utf-8")

    assert "sickn33/antigravity-awesome-skills" in metadata


@pytest.mark.unit
def test_accessibility_upstream_documents_license(repo_root: Path) -> None:
    metadata = (
        repo_root / "harness-conf" / "skills/accessibility-audit/UPSTREAM.md"
    ).read_text(encoding="utf-8")

    assert "CC BY" in metadata


@pytest.mark.unit
def test_accessibility_skill_contains_portuguese_triggers(repo_root: Path) -> None:
    skill = (
        repo_root / "harness-conf" / "skills/accessibility-audit/SKILL.md"
    ).read_text(
        encoding="utf-8"
    )

    assert any(trigger in skill for trigger in ("acessibilidade", "WCAG", "a11y"))


@pytest.mark.unit
def test_accessibility_metadata_preserves_description_adaptation(
    repo_root: Path,
) -> None:
    metadata = (
        repo_root / "harness-conf" / "skills/accessibility-audit/UPSTREAM.md"
    ).read_text(encoding="utf-8")

    assert "Adaptacao da description" in metadata


@pytest.mark.unit
def test_list_updatable_returns_sorted_skills_with_upstream_metadata(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    (repo / "harness-conf/skills/without-upstream").mkdir(parents=True)
    (repo / "harness-conf/skills/with-z/UPSTREAM.md").parent.mkdir(parents=True)
    (repo / "harness-conf/skills/with-z/UPSTREAM.md").write_text(
        "metadata", encoding="utf-8"
    )
    (repo / "harness-conf/skills/with-a/UPSTREAM.md").parent.mkdir(parents=True)
    (repo / "harness-conf/skills/with-a/UPSTREAM.md").write_text(
        "metadata", encoding="utf-8"
    )

    assert skills_sync.list_updatable(repo) == ["with-a", "with-z"]


@pytest.mark.unit
def test_addyosmani_help_mentions_target(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        skills_sync.main(["sync", "--help"])

    assert "addyosmani" in capsys.readouterr().out


@pytest.mark.unit
def test_addyosmani_skill_files_exist(repo_root: Path) -> None:
    for skill_name in skills_sync.ADDYOSMANI_SKILLS:
        assert (
            repo_root / "harness-conf" / "skills" / skill_name / "SKILL.md"
        ).is_file()


@pytest.mark.unit
def test_addyosmani_upstream_files_exist(repo_root: Path) -> None:
    for skill_name in skills_sync.ADDYOSMANI_SKILLS:
        assert (
            repo_root / "harness-conf" / "skills" / skill_name / "UPSTREAM.md"
        ).is_file()


@pytest.mark.unit
def test_addyosmani_metadata_references_expected_repository(repo_root: Path) -> None:
    for skill_name in (
        "test-driven-development",
        "security-and-hardening",
    ):
        metadata = (
            repo_root / "harness-conf" / "skills" / skill_name / "UPSTREAM.md"
        ).read_text(encoding="utf-8")
        assert "addyosmani/agent-skills" in metadata


@pytest.mark.unit
def test_addyosmani_reference_files_exist(repo_root: Path) -> None:
    for skill_name, reference_name in skills_sync.ADDYOSMANI_REFERENCES.items():
        assert (
            repo_root
            / "harness-conf"
            / "skills"
            / skill_name
            / "references"
            / reference_name
        ).is_file()


@pytest.mark.unit
def test_addyosmani_metadata_preserves_description_adaptation(
    repo_root: Path,
) -> None:
    for skill_name in skills_sync.ADDYOSMANI_SKILLS:
        metadata = (
            repo_root / "harness-conf" / "skills" / skill_name / "UPSTREAM.md"
        ).read_text(encoding="utf-8")
        assert "Adaptacao da description" in metadata


@pytest.mark.unit
def test_check_only_does_not_change_local_skill_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    local_skill = repo / "harness-conf/skills/accessibility-audit"
    local_skill.mkdir(parents=True)
    (local_skill / "SKILL.md").write_text("local skill", encoding="utf-8")
    (local_skill / "UPSTREAM.md").write_text(
        "local metadata\n## Adaptacao da description\ncustom\n",
        encoding="utf-8",
    )
    upstream = git_upstream(
        tmp_path,
        {
            "LICENSE": "MIT License",
            "skills/accessibility-compliance-accessibility-audit/SKILL.md": (
                "upstream skill"
            ),
            (
                "skills/accessibility-compliance-accessibility-audit/"
                "resources/implementation-playbook.md"
            ): "playbook",
        },
    )
    before = {
        path.relative_to(repo): path.read_bytes()
        for path in repo.rglob("*")
        if path.is_file()
    }

    result = skills_sync.sync_skill(
        "accessibility-audit",
        repo,
        upstream,
        check_only=True,
    )

    after = {
        path.relative_to(repo): path.read_bytes()
        for path in repo.rglob("*")
        if path.is_file()
    }
    assert result.status == "check-only"
    assert after == before


@pytest.mark.unit
def test_accessibility_sync_preserves_skill_and_description_adaptation(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    local_skill = repo / "harness-conf/skills/accessibility-audit"
    local_skill.mkdir(parents=True)
    (local_skill / "SKILL.md").write_text("adapted skill", encoding="utf-8")
    (local_skill / "UPSTREAM.md").write_text(
        "old metadata\n## Adaptacao da description\ncustom adaptation\n",
        encoding="utf-8",
    )
    upstream = git_upstream(
        tmp_path,
        {
            "LICENSE": "MIT License",
            "skills/accessibility-compliance-accessibility-audit/SKILL.md": (
                "upstream skill"
            ),
            (
                "skills/accessibility-compliance-accessibility-audit/"
                "resources/implementation-playbook.md"
            ): "playbook",
        },
    )

    result = skills_sync.sync_skill("accessibility-audit", repo, upstream)

    assert result.status == "success"
    assert (local_skill / "SKILL.md").read_text(encoding="utf-8") == "adapted skill"
    assert (
        local_skill / "resources/implementation-playbook.md"
    ).read_text(encoding="utf-8") == "playbook"
    metadata = (local_skill / "UPSTREAM.md").read_text(encoding="utf-8")
    assert "commit:" in metadata
    assert "data_commit:" in metadata
    assert "sincronizado_em:" in metadata
    assert "## Adaptacao da description" in metadata
    assert "custom adaptation" in metadata


@pytest.mark.unit
def test_addyosmani_sync_copies_references_without_overwriting_skill(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    local_skill = repo / "harness-conf/skills/test-driven-development"
    local_skill.mkdir(parents=True)
    (local_skill / "SKILL.md").write_text("adapted skill", encoding="utf-8")
    (local_skill / "UPSTREAM.md").write_text(
        "old metadata\n## Adaptacao da description\ncustom adaptation\n",
        encoding="utf-8",
    )
    upstream = git_upstream(
        tmp_path,
        {
            "LICENSE": "MIT License",
            "skills/test-driven-development/SKILL.md": "upstream skill",
            "references/testing-patterns.md": "patterns",
        },
    )

    result = skills_sync.sync_skill("addyosmani", repo, upstream)

    assert result.status == "success"
    assert (local_skill / "SKILL.md").read_text(encoding="utf-8") == "adapted skill"
    assert (
        local_skill / "references/testing-patterns.md"
    ).read_text(encoding="utf-8") == "patterns"
    metadata = (local_skill / "UPSTREAM.md").read_text(encoding="utf-8")
    assert "## Adaptacao da description" in metadata
    assert "custom adaptation" in metadata


@pytest.mark.unit
def test_prompt_improver_sync_copies_assets_references_scripts_and_license(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    local_skill = repo / "harness-conf/skills/prompt-improver"
    local_skill.mkdir(parents=True)
    (local_skill / "SKILL.md").write_text("adapted skill", encoding="utf-8")
    upstream = git_upstream(
        tmp_path,
        {
            "LICENSE": "MIT License",
            "package.json": '{"version": "9.9.9"}',
            "prompt-architect/SKILL.md": "upstream skill",
            "prompt-architect/references/reference.md": "reference",
            "prompt-architect/assets/template.txt": "template",
            "prompt-architect/scripts/helper.py": "print('ok')",
        },
    )

    result = skills_sync.sync_skill("prompt-improver", repo, upstream)

    assert result.status == "success"
    assert (local_skill / "SKILL.md").read_text(encoding="utf-8") == "adapted skill"
    assert (
        local_skill / "references/reference.md"
    ).read_text(encoding="utf-8") == "reference"
    assert (local_skill / "assets/template.txt").exists()
    assert (local_skill / "scripts/helper.py").exists()
    assert (local_skill / "LICENSE").read_text(encoding="utf-8") == "MIT License"
    assert "versao: 9.9.9" in (
        local_skill / "UPSTREAM.md"
    ).read_text(encoding="utf-8")


@pytest.mark.unit
def test_sync_rejects_upstream_without_mit_license(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    upstream = git_upstream(tmp_path, {"LICENSE": "Apache License"})

    with pytest.raises(skills_sync.SyncError, match="MIT"):
        skills_sync.sync_skill("accessibility-audit", repo, upstream)


@pytest.mark.unit
def test_sync_help_mentions_writing_skills_targets(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        skills_sync.main(["sync", "--help"])

    output = capsys.readouterr().out
    assert "humanizer-br" in output
    assert "portugues-tecnico-controlado" in output


@pytest.mark.unit
def test_list_includes_writing_skills(repo_root: Path) -> None:
    listed = skills_sync.list_updatable(repo_root)

    assert "humanizer-br" in listed
    assert "portugues-tecnico-controlado" in listed


@pytest.mark.unit
def test_portugues_tecnico_controlado_files_exist(repo_root: Path) -> None:
    skill_dir = (
        repo_root / "harness-conf" / "skills" / "portugues-tecnico-controlado"
    )

    assert (skill_dir / "SKILL.md").is_file()
    assert (skill_dir / "UPSTREAM.md").is_file()
    for reference in ("ingles.md", "lexico.md", "ortografia-ptbr.md"):
        assert (skill_dir / "references" / reference).is_file()


@pytest.mark.unit
def test_portugues_tecnico_controlado_upstream_documents_repository(
    repo_root: Path,
) -> None:
    metadata = (
        repo_root
        / "harness-conf"
        / "skills"
        / "portugues-tecnico-controlado"
        / "UPSTREAM.md"
    ).read_text(encoding="utf-8")

    assert "kayquer/portugues-tecnico-controlado" in metadata
    assert "MIT" in metadata
    assert "description_lang: pt-br" in metadata


@pytest.mark.unit
def test_portugues_tecnico_controlado_sync_copies_references(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    local_skill = (
        repo / "harness-conf" / "skills" / "portugues-tecnico-controlado"
    )
    local_skill.mkdir(parents=True)
    (local_skill / "SKILL.md").write_text("adapted skill", encoding="utf-8")
    upstream = git_upstream(
        tmp_path,
        {
            "LICENSE": "MIT License",
            "SKILL.md": "upstream skill",
            "references/lexico.md": "lexico",
            "references/ortografia-ptbr.md": "ortografia",
            "references/ingles.md": "ingles",
        },
    )

    result = skills_sync.sync_skill(
        "portugues-tecnico-controlado",
        repo,
        upstream,
    )

    assert result.status == "success"
    assert (local_skill / "SKILL.md").read_text(encoding="utf-8") == (
        "adapted skill"
    )
    for reference in ("ingles.md", "lexico.md", "ortografia-ptbr.md"):
        assert (local_skill / "references" / reference).is_file()
    metadata = (local_skill / "UPSTREAM.md").read_text(encoding="utf-8")
    assert "opencode-skills sync portugues-tecnico-controlado" in metadata
    assert "references/lexico.md" in metadata


@pytest.mark.unit
def test_humanizer_br_files_exist(repo_root: Path) -> None:
    skill_dir = repo_root / "harness-conf" / "skills" / "humanizer-br"

    assert (skill_dir / "SKILL.md").is_file()
    assert (skill_dir / "UPSTREAM.md").is_file()
    assert (skill_dir / "LICENSE").is_file()
    assert (skill_dir / "references" / "aprofundador.md").is_file()


@pytest.mark.unit
def test_humanizer_br_upstream_documents_repository(
    repo_root: Path,
) -> None:
    metadata = (
        repo_root / "harness-conf" / "skills" / "humanizer-br" / "UPSTREAM.md"
    ).read_text(encoding="utf-8")

    assert "carlosafjr-dev/humanizer-br" in metadata
    assert "MIT" in metadata
    assert "description_lang: pt-br" in metadata


@pytest.mark.unit
def test_humanizer_br_description_has_explicit_triggers(
    repo_root: Path,
) -> None:
    skill = (
        repo_root / "harness-conf" / "skills" / "humanizer-br" / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "humanizar" in skill
    assert "anti-IA" in skill
    assert "texto parece IA" in skill


@pytest.mark.unit
def test_humanizer_br_sync_copies_aprofundador_and_license(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    local_skill = repo / "harness-conf" / "skills" / "humanizer-br"
    local_skill.mkdir(parents=True)
    (local_skill / "SKILL.md").write_text("adapted skill", encoding="utf-8")
    upstream = git_upstream(
        tmp_path,
        {
            "LICENSE": "MIT License",
            "skills/humanizer-br/SKILL.md": "upstream skill",
            "skills/aprofundador/SKILL.md": "aprofundador content",
        },
    )

    result = skills_sync.sync_skill("humanizer-br", repo, upstream)

    assert result.status == "success"
    assert (local_skill / "SKILL.md").read_text(encoding="utf-8") == (
        "adapted skill"
    )
    assert (
        local_skill / "references" / "aprofundador.md"
    ).read_text(encoding="utf-8") == "aprofundador content"
    assert (local_skill / "LICENSE").read_text(encoding="utf-8") == (
        "MIT License"
    )
    metadata = (local_skill / "UPSTREAM.md").read_text(encoding="utf-8")
    assert "opencode-skills sync humanizer-br" in metadata
    assert "references/aprofundador.md" in metadata
