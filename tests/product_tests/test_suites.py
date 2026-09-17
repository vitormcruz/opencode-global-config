from pathlib import Path
import json

import pytest

from opencode_config.product_tests.backend import run_backend_suite
from opencode_config.product_tests.process import ProcessResult
from opencode_config.product_tests.security import (
    findings_from_bandit,
    findings_from_pip_audit,
    run_security_suite,
)


def missing_tool(_name: str) -> None:
    return None


@pytest.mark.unit
def test_backend_reports_missing_checks_as_blocking_findings(
    tmp_path: Path,
) -> None:
    report = run_backend_suite(
        tmp_path,
        which=missing_tool,
        runner=lambda *_args, **_kwargs: pytest.fail("não deveria executar"),
        progress=lambda _message: None,
    )

    assert report.status == "fail"
    tools = {finding.tool for finding in report.findings}
    assert {"pytest", "ruff", "shellcheck", "PSScriptAnalyzer"} <= tools


@pytest.mark.unit
def test_pip_audit_high_severity_is_blocking_and_low_is_improvement() -> None:
    findings = findings_from_pip_audit(
        {
            "dependencies": [
                {
                    "name": "high-package",
                    "vulns": [
                        {"id": "CVE-1", "severity": "high"},
                    ],
                },
                {
                    "name": "low-package",
                    "vulns": [
                        {"id": "CVE-2", "severity": "low"},
                    ],
                },
            ]
        }
    )

    assert [finding.severity for finding in findings] == [
        "bloqueante",
        "melhoria",
    ]


@pytest.mark.unit
def test_bandit_high_severity_is_blocking() -> None:
    findings = findings_from_bandit(
        {
            "results": [
                {
                    "filename": "src/example.py",
                    "line_number": 4,
                    "issue_text": "uso inseguro",
                    "issue_severity": "HIGH",
                }
            ]
        }
    )

    assert findings[0].severity == "bloqueante"
    assert findings[0].tool == "bandit"


@pytest.mark.unit
def test_unknown_security_severity_is_blocking() -> None:
    findings = findings_from_pip_audit(
        {
            "dependencies": [
                {"name": "package", "vulns": [{"id": "CVE-unknown"}]}
            ]
        }
    )

    assert findings[0].severity == "bloqueante"


@pytest.mark.unit
def test_security_json_parser_reports_unexpected_shape_as_blocking() -> None:
    findings = findings_from_pip_audit({"unexpected": []})

    assert findings[0].severity == "bloqueante"
    assert "JSON" in findings[0].message


@pytest.mark.unit
def test_process_result_can_be_used_by_suite_fakes() -> None:
    result = ProcessResult(
        command=("ruff", "check"),
        returncode=0,
        stdout="",
        stderr="",
    )

    assert result.succeeded


@pytest.mark.unit
def test_backend_runs_all_available_checks_and_concordion(
    tmp_path: Path,
) -> None:
    (tmp_path / ".venv" / "bin").mkdir(parents=True)
    (tmp_path / ".venv" / "bin" / "python").touch()
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "check.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (scripts / "check.ps1").write_text("Write-Output ok\n", encoding="utf-8")
    commands: list[tuple[str, ...]] = []

    def runner(command, **_kwargs):
        normalized = tuple(str(item) for item in command)
        commands.append(normalized)
        if normalized[0] == "/tool/gradle":
            report_dir = tmp_path / "build" / "test-results" / "test"
            report_dir.mkdir(parents=True)
            (report_dir / "TEST-backend.xml").write_text(
                '<testsuite tests="1" failures="0" errors="0">'
                '<testcase classname="Backend" name="spec" />'
                "</testsuite>",
                encoding="utf-8",
            )
        return ProcessResult(normalized, 0, "", "")

    report = run_backend_suite(
        tmp_path,
        which=lambda name: f"/tool/{name}",
        runner=runner,
        progress=lambda _message: None,
    )

    assert report.status == "pass"
    assert any(command[0] == "/tool/ruff" for command in commands)
    assert any(command[0] == "/tool/pwsh" for command in commands)
    assert any(command[0] == "/tool/gradle" for command in commands)


@pytest.mark.unit
def test_security_suite_keeps_low_findings_as_improvements(
    tmp_path: Path,
) -> None:
    commands: list[tuple[str, ...]] = []

    def runner(command, **_kwargs):
        normalized = tuple(str(item) for item in command)
        commands.append(normalized)
        executable = normalized[0]
        if executable == "/tool/pip-audit":
            return ProcessResult(
                normalized,
                1,
                json.dumps(
                    {
                        "dependencies": [
                            {
                                "name": "package",
                                "vulns": [{"id": "CVE-1", "severity": "low"}],
                            }
                        ]
                    }
                ),
                "",
            )
        if executable == "/tool/bandit":
            return ProcessResult(
                normalized,
                1,
                json.dumps(
                    {
                        "results": [
                            {
                                "filename": "src/example.py",
                                "line_number": 1,
                                "issue_text": "melhoria",
                                "issue_severity": "LOW",
                            }
                        ]
                    }
                ),
                "",
            )
        if executable == "/tool/gradle":
            report_dir = tmp_path / "build" / "test-results" / "test"
            report_dir.mkdir(parents=True)
            (report_dir / "TEST-security.xml").write_text(
                '<testsuite tests="1" failures="0" errors="0">'
                '<testcase classname="Security" name="spec" />'
                "</testsuite>",
                encoding="utf-8",
            )
        return ProcessResult(normalized, 0, "", "")

    report = run_security_suite(
        tmp_path,
        which=lambda name: f"/tool/{name}",
        runner=runner,
        progress=lambda _message: None,
    )

    assert report.status == "pass"
    assert {finding.severity for finding in report.findings} == {"melhoria"}
    assert any(command[0] == "/tool/gitleaks" for command in commands)
