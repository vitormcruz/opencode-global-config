from pathlib import Path

import pytest

from opencode_config.product_tests.concordion import (
    run_concordion_suite,
    translate_junit_reports,
)
from opencode_config.product_tests.process import ProcessResult


@pytest.mark.unit
def test_translate_junit_reports_returns_pass_for_successful_fixture(
    tmp_path: Path,
) -> None:
    (tmp_path / "TEST-backend.xml").write_text(
        """
        <testsuite name="backend" tests="1" failures="0" errors="0" skipped="0">
          <testcase classname="BackendSpec" name="spec" time="0.1" />
        </testsuite>
        """,
        encoding="utf-8",
    )

    report = translate_junit_reports(tmp_path, specialty="backend")

    assert report.to_dict() == {"status": "pass", "findings": []}


@pytest.mark.unit
def test_translate_junit_reports_exposes_fixture_failure_as_blocking_finding(
    tmp_path: Path,
) -> None:
    (tmp_path / "TEST-security.xml").write_text(
        """
        <testsuite name="security" tests="1" failures="1" errors="0" skipped="0">
          <testcase classname="SecuritySpec" name="spec" time="0.1">
            <failure message="veredito inesperado">detalhe</failure>
          </testcase>
        </testsuite>
        """,
        encoding="utf-8",
    )

    report = translate_junit_reports(tmp_path, specialty="seguranca")

    assert report.status == "fail"
    assert report.findings[0].severity == "bloqueante"
    assert report.findings[0].tool == "concordion"
    assert "SecuritySpec.spec" in report.findings[0].message


@pytest.mark.unit
def test_translate_junit_reports_rejects_invalid_xml_as_blocking_finding(
    tmp_path: Path,
) -> None:
    (tmp_path / "TEST-invalid.xml").write_text("<testsuite>", encoding="utf-8")

    report = translate_junit_reports(tmp_path, specialty="backend")

    assert report.status == "fail"
    assert report.findings[0].severity == "bloqueante"
    assert "XML" in report.findings[0].message


@pytest.mark.unit
def test_translate_junit_reports_fails_when_gradle_did_not_write_reports(
    tmp_path: Path,
) -> None:
    report = translate_junit_reports(tmp_path, specialty="backend")

    assert report.status == "fail"
    assert report.findings[0].tool == "concordion"


@pytest.mark.unit
def test_run_concordion_suite_reports_missing_jdk_or_gradle(tmp_path: Path) -> None:
    report = run_concordion_suite(
        tmp_path,
        specialty="backend",
        which=lambda name: None if name == "java" else "/tool/gradle",
        runner=lambda *_args, **_kwargs: pytest.fail("não deveria executar"),
        progress=lambda _message: None,
    )

    assert report.status == "fail"
    assert report.findings[0].tool == "java"


@pytest.mark.unit
def test_run_concordion_suite_translates_a_successful_gradle_report(
    tmp_path: Path,
) -> None:
    observed_environments: list[object] = []

    def runner(command, **kwargs):
        observed_environments.append(kwargs.get("env"))
        report_dir = tmp_path / "build" / "test-results" / "test"
        report_dir.mkdir(parents=True)
        (report_dir / "TEST-backend.xml").write_text(
            '<testsuite tests="1" failures="0" errors="0">'
            '<testcase classname="Backend" name="spec" />'
            "</testsuite>",
            encoding="utf-8",
        )
        return ProcessResult(tuple(str(item) for item in command), 0, "", "")

    report = run_concordion_suite(
        tmp_path,
        specialty="backend",
        which=lambda _name: "/tool/executable",
        runner=runner,
        progress=lambda _message: None,
    )

    assert report.status == "pass"
    for environment in observed_environments:
        assert environment is None or "PRODUCT_TEST_REPO_ROOT" not in environment
