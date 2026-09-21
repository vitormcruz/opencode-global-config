"""Integracao com Gradle/Concordion e traducao de XML JUnit."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path
from xml.etree import ElementTree  # nosec B405 - XML gerado localmente pelo Gradle (JUnit), nao input externo

from .interface import Finding, ProductReport
from .process import (
    ProcessResult,
    Progress,
    Runner,
    run_process,
    run_with_network_retry,
)


def _failure_message(testcase: ElementTree.Element, detail: str) -> str:
    class_name = testcase.attrib.get("classname", "fixture")
    test_name = testcase.attrib.get("name", "spec")
    return f"{class_name}.{test_name}: {detail}"


def _testcase_findings(
    testcase: ElementTree.Element,
) -> list[Finding]:
    findings: list[Finding] = []
    for element_name in ("failure", "error"):
        for element in testcase.findall(element_name):
            detail = element.attrib.get("message") or (
                " ".join((element.text or "").split())
            ) or element_name
            findings.append(
                Finding(
                    "bloqueante",
                    "concordion",
                    _failure_message(testcase, detail),
                )
            )
    if testcase.find("skipped") is not None:
        findings.append(
            Finding(
                "bloqueante",
                "concordion",
                _failure_message(testcase, "spec nao executada"),
            )
        )
    return findings


def _reported_failures(root: ElementTree.Element) -> int | None:
    try:
        return int(root.attrib.get("failures", "0") or "0") + int(
            root.attrib.get("errors", "0") or "0"
        )
    except ValueError:
        return None


def translate_junit_reports(
    report_directory: Path,
    *,
    specialty: str,
) -> ProductReport:
    """Traduz todos os XML JUnit da execucao de uma especialidade."""

    report_files = sorted(report_directory.glob("TEST-*.xml"))
    if not report_files:
        report_files = sorted(report_directory.glob("*.xml"))
    if not report_files:
        return ProductReport.from_findings(
            [
                Finding(
                    "bloqueante",
                    "concordion",
                    f"nenhum relatorio XML JUnit foi gerado para {specialty}",
                )
            ]
        )

    findings: list[Finding] = []
    for report_file in report_files:
        try:
            # nosec B314 - relatorio XML JUnit produzido pelo build local do
            # Gradle no cache do repo; conteudo vira finding, nunca e executado.
            root = ElementTree.parse(report_file).getroot()  # nosec B314
        except (ElementTree.ParseError, OSError) as error:
            findings.append(
                Finding(
                    "bloqueante",
                    "concordion",
                    f"XML JUnit invalido em {report_file.name}: {error}",
                )
            )
            continue

        testcases = root.findall(".//testcase")
        findings.extend(
            finding
            for testcase in testcases
            for finding in _testcase_findings(testcase)
        )
        reported_failures = _reported_failures(root)
        if reported_failures is None:
            findings.append(
                Finding(
                    "bloqueante",
                    "concordion",
                    f"XML JUnit invalido em {report_file.name}: contagem invalida",
                )
            )
        elif not testcases and reported_failures:
            findings.append(
                Finding(
                    "bloqueante",
                    "concordion",
                    f"relatorio XML JUnit de {specialty} indica falha sem testcase",
                )
            )

    return ProductReport.from_findings(findings)


def _missing_tool(tool: str, instruction: str) -> ProductReport:
    return ProductReport.from_findings(
        [Finding("bloqueante", tool, f"ferramenta ausente; {instruction}")]
    )


def _process_finding(tool: str, result: ProcessResult) -> Finding:
    detail = result.error or result.stderr or result.stdout
    detail = " ".join(detail.split())[-1500:]
    if not detail:
        detail = f"processo terminou com exit {result.returncode}"
    return Finding("bloqueante", tool, detail)


def run_concordion_suite(
    repo_root: Path,
    *,
    specialty: str,
    which: Callable[[str], str | None] = shutil.which,
    runner: Runner = run_process,
    progress: Progress,
) -> ProductReport:
    """Executa somente a fixture Concordion da especialidade informada."""

    java = which("java")
    gradle = which("gradle")
    if java is None:
        return _missing_tool("java", "instale um JDK em user-space")
    if gradle is None:
        return _missing_tool("gradle", "instale Gradle em user-space")

    command = [
        gradle,
        "clean",
        "test",
        "--no-daemon",
        f"-PproductSpecialty={specialty}",
    ]
    progress(f"[{specialty}] executando Concordion via Gradle")
    result = run_with_network_retry(
        command,
        cwd=repo_root,
        progress=progress,
        runner=runner,
        label="gradle",
    )

    report = translate_junit_reports(
        repo_root / "build" / "test-results" / "test",
        specialty=specialty,
    )
    if result.error or (result.returncode not in {0, 1}):
        return ProductReport(
            report.findings + (_process_finding("gradle", result),),
            declared_status="fail",
        )
    if result.returncode == 1:
        reports_missing = all(
            "nenhum relatorio XML" in finding.message for finding in report.findings
        )
        gradle_detail = result.stderr or result.stdout
        if reports_missing and gradle_detail.strip():
            # Exit 1 sem XML: a causa raiz (build, toolchain, rede) esta no
            # stderr; sem este anexo o finding "nenhum relatorio" esconde o
            # diagnostico (ex.: Gradle incompativel com o JDK).
            return ProductReport.from_findings(
                [*report.findings, _process_finding("gradle", result)]
            )
        if not report.findings:
            return ProductReport.from_findings([_process_finding("gradle", result)])
    return report


def load_json_output(result: ProcessResult, *, tool: str) -> object:
    """Converte stdout JSON ou levanta erro com contexto do processo."""

    if result.error:
        raise ValueError(result.error)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ValueError(f"JSON invalido de {tool}: {error.msg}") from error
