from io import StringIO
from pathlib import Path

import pytest

from opencode_config.product_tests.interface import ProductReport
from opencode_config.product_tests.runner import run_entrypoint


@pytest.mark.unit
def test_run_entrypoint_emits_json_and_progress_for_a_passing_suite(
    tmp_path: Path,
) -> None:
    output = StringIO()
    error = StringIO()

    status = run_entrypoint(
        [],
        lambda _root: ProductReport.from_findings([]),
        tool="fake",
        output=output,
        error=error,
        repo_root=tmp_path,
    )

    assert status == 0
    assert '"status":"pass"' in output.getvalue()
    assert "iniciando suite" in error.getvalue()


@pytest.mark.unit
def test_run_entrypoint_rejects_arguments_without_calling_suite(
    tmp_path: Path,
) -> None:
    called = False

    def suite(_root: Path) -> ProductReport:
        nonlocal called
        called = True
        return ProductReport.from_findings([])

    output = StringIO()
    status = run_entrypoint(
        ["unexpected"],
        suite,
        tool="fake",
        output=output,
        error=StringIO(),
        repo_root=tmp_path,
    )

    assert status == 1
    assert not called
    assert '"status":"fail"' in output.getvalue()


@pytest.mark.unit
def test_run_entrypoint_converts_a_suite_crash_to_a_blocking_finding(
    tmp_path: Path,
) -> None:
    output = StringIO()

    def crash(_root: Path) -> ProductReport:
        raise RuntimeError("quebrou")

    status = run_entrypoint(
        [],
        crash,
        tool="fake",
        output=output,
        error=StringIO(),
        repo_root=tmp_path,
    )

    assert status == 1
    assert "crash da suite" in output.getvalue()
