"""Contrato pytest do entry point opencode-md-export."""

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

    from opencode_config.cli.md_export import main

    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    status = main()
    captured = capsys.readouterr()

    assert status == 0
    return json.loads(captured.out)


def install_fake_pandoc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Instala Pandoc portatil fake dentro do repositorio de teste."""

    portable_dir = tmp_path / "tools" / "pandoc"
    portable_dir.mkdir(parents=True)
    executable = portable_dir / "pandoc"
    executable.write_text(
        "#!/bin/sh\n"
        "for arg in \"$@\"; do\n"
        "  case \"$arg\" in\n"
        "    --output=*) touch \"${arg#--output=}\" ;;\n"
        "  esac\n"
        "done\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path / 'empty-bin'}")
    return executable


@pytest.mark.tools
def test_md_export_without_source_returns_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = invoke_cli(monkeypatch, capsys, {"to": "docx"})

    assert result["ok"] is False
    assert "obrigatorio" in result["stderr"]


@pytest.mark.tools
def test_md_export_without_to_returns_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
) -> None:
    result = invoke_cli(
        monkeypatch,
        capsys,
        {"source": str(repo_root / "tests/test-resources/sample.md")},
    )

    assert result["ok"] is False
    assert "obrigatorio" in result["stderr"]


@pytest.mark.tools
def test_md_export_invalid_format_returns_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    tmp_path: Path,
) -> None:
    install_fake_pandoc(tmp_path, monkeypatch)
    result = invoke_cli(
        monkeypatch,
        capsys,
        {"source": str(repo_root / "tests/test-resources/sample.md"), "to": "pdf"},
    )

    assert result["ok"] is False
    assert "invalido" in result["stderr"]


@pytest.mark.tools
def test_md_export_missing_source_file_returns_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    install_fake_pandoc(tmp_path, monkeypatch)
    result = invoke_cli(
        monkeypatch,
        capsys,
        {"source": "/tmp/nao-existe-xyz.md", "to": "docx"},
    )

    assert result["ok"] is False


@pytest.mark.tools
def test_md_export_without_pandoc_returns_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    tmp_path: Path,
) -> None:
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    monkeypatch.setenv("PATH", str(empty_bin))

    result = invoke_cli(
        monkeypatch,
        capsys,
        {"source": str(repo_root / "tests/test-resources/sample.md"), "to": "docx"},
    )

    assert result["ok"] is False


@pytest.mark.tools
def test_md_export_without_pandoc_includes_install_hint(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    tmp_path: Path,
) -> None:
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    monkeypatch.setenv("PATH", str(empty_bin))

    result = invoke_cli(
        monkeypatch,
        capsys,
        {"source": str(repo_root / "tests/test-resources/sample.md"), "to": "docx"},
    )

    assert "pandoc" in result["hint"]


@pytest.mark.tools
def test_md_export_does_not_overwrite_without_overwrite(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    tmp_path: Path,
) -> None:
    install_fake_pandoc(tmp_path, monkeypatch)
    output_path = tmp_path / "sample.docx"
    output_path.touch()

    result = invoke_cli(
        monkeypatch,
        capsys,
        {
            "source": str(repo_root / "tests/test-resources/sample.md"),
            "to": "docx",
            "outputPath": str(output_path),
        },
    )

    assert result["ok"] is False
    assert "ja existe" in result["stderr"]


@pytest.mark.tools
def test_md_export_with_markdown_generates_docx(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    tmp_path: Path,
) -> None:
    if shutil.which("pandoc") is None:
        pytest.fail(
            "pandoc nao disponivel neste ambiente — instale pandoc para executar este teste"
        )

    output_dir = tmp_path / "out"
    result = invoke_cli(
        monkeypatch,
        capsys,
        {
            "source": str(repo_root / "tests/test-resources/sample.md"),
            "to": "docx",
            "outputDir": str(output_dir),
        },
    )

    assert result["ok"] is True


@pytest.mark.tools
def test_md_export_artifact_exists_on_disk(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    tmp_path: Path,
) -> None:
    if shutil.which("pandoc") is None:
        pytest.fail(
            "pandoc nao disponivel neste ambiente — instale pandoc para executar este teste"
        )

    output_dir = tmp_path / "out"
    result = invoke_cli(
        monkeypatch,
        capsys,
        {
            "source": str(repo_root / "tests/test-resources/sample.md"),
            "to": "docx",
            "outputDir": str(output_dir),
        },
    )

    assert result["artifacts"]
    assert Path(result["artifacts"][0]).is_file()


@pytest.mark.tools
def test_md_export_error_output_is_valid_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = invoke_cli(monkeypatch, capsys, {})

    assert isinstance(result, dict)
    assert result["ok"] is False
