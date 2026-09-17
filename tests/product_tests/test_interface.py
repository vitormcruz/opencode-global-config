import io
import json

import pytest

from opencode_config.product_tests.interface import (
    Finding,
    ProductReport,
    ReportFormatError,
    decode_report,
    emit_report,
)


@pytest.mark.unit
def test_report_serializes_the_normative_findings_schema() -> None:
    report = ProductReport.from_findings(
        [Finding("melhoria", "ruff", "há uma melhoria")]
    )

    assert report.to_dict() == {
        "status": "pass",
        "findings": [
            {
                "severity": "melhoria",
                "tool": "ruff",
                "message": "há uma melhoria",
            }
        ],
    }


@pytest.mark.unit
def test_blocking_finding_changes_the_report_status() -> None:
    report = ProductReport.from_findings(
        [Finding("bloqueante", "pytest", "a suíte falhou")]
    )

    assert report.status == "fail"


@pytest.mark.unit
def test_emit_report_writes_only_utf8_json_to_stdout() -> None:
    output = io.StringIO()

    emit_report(ProductReport.from_findings([]), output)

    assert json.loads(output.getvalue()) == {
        "status": "pass",
        "findings": [],
    }
    assert "\n" in output.getvalue()


@pytest.mark.unit
def test_decode_report_rejects_invalid_json_shape() -> None:
    with pytest.raises(ReportFormatError, match="findings"):
        decode_report('{"status":"pass","findings":{}}')


@pytest.mark.unit
def test_decode_report_rejects_unknown_finding_severity() -> None:
    payload = json.dumps(
        {
            "status": "pass",
            "findings": [
                {"severity": "warning", "tool": "ruff", "message": "x"}
            ],
        }
    )

    with pytest.raises(ReportFormatError, match="severity"):
        decode_report(payload)
