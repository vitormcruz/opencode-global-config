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


@pytest.mark.unit
def test_sync_skips_frozen_addyosmani_skill_and_reports_it(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    frozen_skill = repo / "harness-conf/skills/code-review-and-quality"
    frozen_skill.mkdir(parents=True)
    (frozen_skill / "SKILL.md").write_text("adapted frozen skill", encoding="utf-8")
    (frozen_skill / "UPSTREAM.md").write_text(
        "# Metadados do Upstream\n"
        "repositorio: upstream\n"
        "sincronizacao: congelada\n",
        encoding="utf-8",
    )
    frozen_before = {
        path.relative_to(frozen_skill): path.read_bytes()
        for path in frozen_skill.rglob("*")
        if path.is_file()
    }
    upstream = git_upstream(
        tmp_path,
        {
            "LICENSE": "MIT License",
            "skills/test-driven-development/SKILL.md": "upstream tdd skill",
            "skills/code-review-and-quality/SKILL.md": "upstream review skill",
            "references/testing-patterns.md": "updated patterns",
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
    output = StringIO()
    status = skills_sync.run(
        ["sync", "addyosmani", "--yes", "--repo-root", str(repo)],
        output=output,
        error=StringIO(),
    )

    assert status == 0
    assert "skipped_skill: code-review-and-quality" in output.getvalue()
    assert {
        path.relative_to(frozen_skill): path.read_bytes()
        for path in frozen_skill.rglob("*")
        if path.is_file()
    } == frozen_before
    synchronized_skill = repo / "harness-conf/skills/test-driven-development"
    assert (
        synchronized_skill / "references/testing-patterns.md"
    ).read_text(encoding="utf-8") == "updated patterns"
    assert "sincronizacao:" not in (
        synchronized_skill / "UPSTREAM.md"
    ).read_text(encoding="utf-8")


@pytest.mark.unit
def test_update_skips_frozen_skill_without_running_commands(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    frozen_metadata = repo / "harness-conf/skills/frozen/UPSTREAM.md"
    frozen_metadata.parent.mkdir(parents=True)
    frozen_metadata.write_text(
        "# Metadados do Upstream\n"
        "repositorio: upstream\n"
        "sincronizacao: congelada\n"
        "\n"
        "## Como atualizar\n"
        "\n"
        "    opencode-skills sync accessibility-audit\n"
        "    opencode-skills sync accessibility-audit --check-only\n",
        encoding="utf-8",
    )
    frozen_before = frozen_metadata.read_bytes()
    unfrozen_metadata = repo / "harness-conf/skills/unfrozen/UPSTREAM.md"
    unfrozen_metadata.parent.mkdir(parents=True)
    unfrozen_metadata.write_text(
        "# Metadados do Upstream\n"
        "repositorio: upstream\n"
        "\n"
        "## Como atualizar\n"
        "\n"
        "    opencode-skills sync accessibility-audit\n"
        "    opencode-skills sync accessibility-audit --check-only\n",
        encoding="utf-8",
    )

    def forbidden_command(*_args, **_kwargs):
        pytest.fail("skill congelada nao deve executar comandos")

    monkeypatch.setattr(
        skills_sync,
        "_run_documented_command",
        forbidden_command,
    )
    output = StringIO()
    status = skills_sync.run(
        ["update", "frozen", "--repo-root", str(repo)],
        output=output,
        error=StringIO(),
    )
    assert status == 0
    assert "status: frozen" in output.getvalue()
    assert "congelada" in output.getvalue()
    assert frozen_metadata.read_bytes() == frozen_before

    def run_documented_command(command: str, _repo_root: Path) -> tuple[int, str]:
        if "--check-only" in command:
            return 1, "atualizacao necessaria"
        return 0, "atualizada"

    monkeypatch.setattr(
        skills_sync,
        "_run_documented_command",
        run_documented_command,
    )
    unfrozen_status = skills_sync.run(
        ["update", "unfrozen", "--repo-root", str(repo)],
        output=StringIO(),
        error=StringIO(),
    )

    assert unfrozen_status == 0
    assert "sincronizacao:" not in unfrozen_metadata.read_text(encoding="utf-8")


@pytest.mark.unit
def test_list_marks_frozen_skills_without_changing_metadata(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    frozen_metadata = repo / "harness-conf/skills/frozen/UPSTREAM.md"
    frozen_metadata.parent.mkdir(parents=True)
    frozen_metadata.write_text(
        "# Metadados do Upstream\n"
        "repositorio: upstream\n"
        "sincronizacao: congelada\n",
        encoding="utf-8",
    )
    frozen_before = frozen_metadata.read_bytes()
    unfrozen_metadata = repo / "harness-conf/skills/unfrozen/UPSTREAM.md"
    unfrozen_metadata.parent.mkdir(parents=True)
    unfrozen_metadata.write_text(
        "# Metadados do Upstream\nrepositorio: upstream\n",
        encoding="utf-8",
    )
    unfrozen_before = unfrozen_metadata.read_bytes()
    output = StringIO()

    status = skills_sync.run(
        ["list", "--repo-root", str(repo)],
        output=output,
        error=StringIO(),
    )

    assert status == 0
    assert "frozen (congelada)" in output.getvalue()
    assert "\nunfrozen\n" in f"\n{output.getvalue()}"
    assert frozen_metadata.read_bytes() == frozen_before
    assert unfrozen_metadata.read_bytes() == unfrozen_before
    assert "sincronizacao:" not in unfrozen_metadata.read_text(encoding="utf-8")


@pytest.mark.unit
def test_upstream_regeneration_preserves_synchronization_field(
    tmp_path: Path,
) -> None:
    local_skill = tmp_path / "skill"
    local_skill.mkdir()
    upstream_metadata = local_skill / "UPSTREAM.md"
    upstream_metadata.write_text(
        "# Metadados do Upstream\n"
        "repositorio: upstream\n"
        "sincronizacao: congelada\n",
        encoding="utf-8",
    )

    skills_sync._write_upstream(
        local_skill,
        metadata={"sha": "abc123", "date": "2026-09-27", "synced": "today"},
        repository="https://example.invalid/upstream.git",
        branch="main",
        files=["references/example.md"],
        update_command="opencode-skills sync example",
        license_text="MIT License",
    )

    assert "sincronizacao: congelada" in upstream_metadata.read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_writing_for_agents_sync_preserves_local_skill_and_notes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    local_skill = repo / "harness-conf/skills/writing-for-agents"
    local_skill.mkdir(parents=True)
    local_skill_file = local_skill / "SKILL.md"
    local_skill_file.write_text("adapted local skill", encoding="utf-8")
    local_metadata = local_skill / "UPSTREAM.md"
    security_review = (
        "Conteúdo total revisado na importação (commit citado acima):\n\n"
        "- `SKILL.md`: texto metodológico sobre escrita para agentes.\n"
        "- `SKILL-MECHANICS.md`: texto sobre frontmatter e invocação.\n"
        "  Mesmo perfil, limpo.\n"
    )
    local_metadata.write_text(
        "# Metadados do Upstream\n\n"
        "repositorio: https://github.com/mattpocock/skills\n"
        "branch: main\n"
        "commit: c55ee46073ed923f86ce59a5eb3b6d895095d1b7\n"
        "data_commit: 2026-09-18 11:12:29 +0100\n"
        "sincronizado_em: 2026-09-22 23:30 UTC\n\n"
        "## Como atualizar\n\n"
        "Fluxo manual via bash em linha única, removido pelo sync.\n\n"
        "## Segurança na importação (2026-09-22)\n\n"
        f"{security_review}\n"
        "## Licenca\n\n"
        "MIT License - Copyright (c) 2026 Matt Pocock\n\n"
        "## Adaptacao da description\n\n"
        "Description convertida para PT-BR; corpo mantido em inglês.\n",
        encoding="utf-8",
    )
    upstream = git_upstream(
        tmp_path,
        {
            "LICENSE": "MIT License\nCopyright (c) Matt Pocock\n",
            "skills/productivity/writing-for-agents/SKILL.md": "upstream skill",
            "skills/productivity/writing-for-agents/SKILL-MECHANICS.md": (
                "upstream mechanics"
            ),
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
    sync_arguments = [
        "sync",
        "writing-for-agents",
        "--yes",
        "--repo-root",
        str(repo),
    ]
    status = skills_sync.run(
        sync_arguments,
        output=StringIO(),
        error=StringIO(),
    )
    second_status = skills_sync.run(
        sync_arguments,
        output=StringIO(),
        error=StringIO(),
    )

    assert status == 0
    assert second_status == 0
    assert skills_sync.list_updatable(repo) == ["writing-for-agents"]
    assert local_skill_file.read_text(encoding="utf-8") == "adapted local skill"
    assert (local_skill / "SKILL-MECHANICS.md").read_text(
        encoding="utf-8"
    ) == "upstream mechanics"
    regenerated_metadata = local_metadata.read_text(encoding="utf-8")
    assert "description_lang: pt-br" in regenerated_metadata
    assert (
        "description_note: Converted to Brazilian Portuguese and enriched with trigger terms."
        in regenerated_metadata
    )
    assert "SKILL-MECHANICS.md" in regenerated_metadata
    assert "## Notas locais" in regenerated_metadata
    assert security_review in regenerated_metadata
    assert "## Segurança na importação" not in regenerated_metadata
    assert "Fluxo manual via bash em linha única" not in regenerated_metadata
    assert "## Adaptacao da description" in regenerated_metadata

    list_output = StringIO()
    list_status = skills_sync.run(
        ["list", "--repo-root", str(repo)],
        output=list_output,
        error=StringIO(),
    )
    assert list_status == 0
    assert "writing-for-agents" in list_output.getvalue()


@pytest.mark.unit
def test_sync_table_documents_every_cli_family(repo_root: Path) -> None:
    agents_rules = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    sync_table = agents_rules.split("### Scripts de sync disponíveis", 1)[1].split(
        "\n### ", 1
    )[0]
    documented_families = {
        row.split("opencode-skills sync ", 1)[1].split("`", 1)[0]
        for row in sync_table.splitlines()
        if "opencode-skills sync " in row
    }
    cli_families = set(skills_sync.SPECS)

    assert "writing-for-agents" in cli_families
    assert cli_families <= documented_families, (
        "famílias do CLI ausentes da tabela de sync do AGENTS.md: "
        f"{sorted(cli_families - documented_families)}"
    )


@pytest.mark.integration
def test_sync_records_new_sha_and_verifies_declared_files_after_upstream_change(
    tmp_path: Path,
) -> None:
    if shutil.which("git") is None:
        pytest.fail("git é necessário para criar o upstream local de dois commits")

    upstream_skill = "skills/accessibility-compliance-accessibility-audit"
    synced_relative_path = "resources/implementation-playbook.md"
    upstream = git_upstream(
        tmp_path,
        {
            "LICENSE": "MIT License\n",
            f"{upstream_skill}/SKILL.md": "upstream skill v1\n",
            f"{upstream_skill}/{synced_relative_path}": "playbook v1\n",
        },
    )
    base_sha = subprocess.run(
        ["git", "-C", str(upstream), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    upstream_skill_file = upstream / upstream_skill / "SKILL.md"
    upstream_skill_file.write_text("upstream skill v2\n", encoding="utf-8")
    upstream_synced_file = upstream / upstream_skill / synced_relative_path
    upstream_synced_file.write_text("playbook v2\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(upstream), "add", "."],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(upstream), "commit", "-qm", "advance upstream"],
        check=True,
    )
    new_sha = subprocess.run(
        ["git", "-C", str(upstream), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    repo = tmp_path / "repo"
    local_skill = repo / "harness-conf/skills/accessibility-audit"
    local_skill.mkdir(parents=True)
    local_skill_file = local_skill / "SKILL.md"
    local_skill_file.write_text("adapted local skill\n", encoding="utf-8")
    (local_skill / "UPSTREAM.md").write_text(
        "# Metadados do Upstream\n"
        "repositorio: https://example.invalid/upstream.git\n"
        "branch: main\n"
        f"commit: {base_sha}\n\n"
        "## Arquivos sincronizados\n\n"
        f"- {synced_relative_path}\n",
        encoding="utf-8",
    )

    result = skills_sync.sync_skill("accessibility-audit", repo, upstream)

    regenerated_metadata = (local_skill / "UPSTREAM.md").read_text(
        encoding="utf-8"
    )
    synchronized_file = local_skill / synced_relative_path
    assert result.status == "success"
    assert f"commit: {new_sha}" in regenerated_metadata
    assert f"- {synced_relative_path}" in regenerated_metadata
    assert synchronized_file.is_file()
    assert synchronized_file.read_bytes() == upstream_synced_file.read_bytes()
    assert local_skill_file.read_text(encoding="utf-8") == "adapted local skill\n"


@pytest.mark.unit
def test_post_sync_checklist_marks_security_review_as_manual(
    repo_root: Path,
) -> None:
    agents_rules = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    _, heading_found, checklist = agents_rules.partition("### Checklist pós-sync")

    assert heading_found, "AGENTS.md deve manter a seção Checklist pós-sync"
    assert "**Verificações automáticas (guardadas por testes):**" in checklist
    assert "**Verificações manuais (não automatizáveis):**" in checklist
    assert "a revisão de segurança do conteúdo novo" in checklist.lower()
