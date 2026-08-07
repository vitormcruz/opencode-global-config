"""Contrato pytest do entry point opencode-doc-extract."""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
import shutil
import sys

import pytest


def invoke_cli(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    payload: object,
) -> dict[str, object]:
    """Executa o entry point com JSON controlado no stdin."""

    from opencode_config.cli.doc_extract import main

    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    status = main()
    captured = capsys.readouterr()

    assert status == 0
    return json.loads(captured.out)


def install_fake_docling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Coloca um executavel docling fake no PATH para validar pre-processamento."""

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    executable = fake_bin / "docling"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}/usr/bin:/bin")


@pytest.mark.tools
def test_doc_extract_without_source_returns_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = invoke_cli(monkeypatch, capsys, {})

    assert result["ok"] is False
    assert "obrigatorio" in result["stderr"]


@pytest.mark.tools
def test_doc_extract_without_source_includes_required_message(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = invoke_cli(monkeypatch, capsys, {})

    assert result["ok"] is False
    assert "Campo 'source'" in result["stderr"]


@pytest.mark.tools
def test_doc_extract_invalid_format_returns_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    repo_root: Path,
) -> None:
    install_fake_docling(tmp_path, monkeypatch)
    result = invoke_cli(
        monkeypatch,
        capsys,
        {"source": str(repo_root / "tests/test-resources/sample.pdf"), "to": "xyz"},
    )

    assert result["ok"] is False
    assert "invalido" in result["stderr"]


@pytest.mark.tools
def test_doc_extract_missing_source_file_returns_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    install_fake_docling(tmp_path, monkeypatch)
    result = invoke_cli(
        monkeypatch,
        capsys,
        {"source": "/tmp/nao-existe-xyz.pdf"},
    )

    assert result["ok"] is False


@pytest.mark.tools
def test_doc_extract_without_docling_returns_install_hint(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    repo_root: Path,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}/usr/bin:/bin")

    result = invoke_cli(
        monkeypatch,
        capsys,
        {"source": str(repo_root / "tests/test-resources/sample.pdf")},
    )

    assert result["ok"] is False
    assert "hint" in result


@pytest.mark.tools
def test_doc_extract_without_docling_includes_install_hint(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    repo_root: Path,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}/usr/bin:/bin")

    result = invoke_cli(
        monkeypatch,
        capsys,
        {"source": str(repo_root / "tests/test-resources/sample.pdf")},
    )

    assert "pipx" in result["hint"]


@pytest.mark.tools
def test_doc_extract_without_docling_uses_windows_hint(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    repo_root: Path,
) -> None:
    from opencode_config.lib import environment

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}/usr/bin:/bin")
    monkeypatch.setattr(environment.platform, "system", lambda: "Windows")

    result = invoke_cli(
        monkeypatch,
        capsys,
        {"source": str(repo_root / "tests/test-resources/sample.pdf")},
    )

    assert "py -m pip" in result["hint"]
    assert "sudo apt-get" not in result["hint"]


@pytest.mark.tools
def test_doc_extract_with_pdf_returns_success(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    repo_root: Path,
) -> None:
    if shutil.which("docling") is None:
        pytest.fail(
            "docling nao disponivel neste ambiente — instale docling para executar este teste"
        )

    output_dir = tmp_path / "out"
    result = invoke_cli(
        monkeypatch,
        capsys,
        {
            "source": str(repo_root / "tests/test-resources/sample.pdf"),
            "outputDir": str(output_dir),
        },
    )

    assert result["ok"] is True


@pytest.mark.tools
def test_doc_extract_with_pdf_generates_artifact(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    repo_root: Path,
) -> None:
    if shutil.which("docling") is None:
        pytest.fail(
            "docling nao disponivel neste ambiente — instale docling para executar este teste"
        )

    output_dir = tmp_path / "out"
    result = invoke_cli(
        monkeypatch,
        capsys,
        {
            "source": str(repo_root / "tests/test-resources/sample.pdf"),
            "outputDir": str(output_dir),
        },
    )

    assert result["artifacts"]


@pytest.mark.tools
def test_doc_extract_error_output_is_valid_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = invoke_cli(monkeypatch, capsys, {})

    assert isinstance(result, dict)
    assert result["ok"] is False
