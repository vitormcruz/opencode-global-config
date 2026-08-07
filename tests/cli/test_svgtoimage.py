"""Contrato pytest do entry point opencode-svgtoimage."""

from __future__ import annotations

import io
import json
from pathlib import Path
import shutil
import struct
import sys

import pytest


def invoke_cli(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    svg: str,
) -> tuple[int, str, str]:
    """Executa o entry point com SVG controlado no stdin."""

    from opencode_config.cli.svgtoimage import main

    monkeypatch.setattr(sys, "stdin", io.StringIO(svg))
    status = main()
    captured = capsys.readouterr()
    return status, captured.out, captured.err


def assert_playwright_available() -> None:
    if shutil.which("node") is None or shutil.which("playwright") is None:
        pytest.fail(
            "Playwright nao disponivel neste ambiente — instale "
            "@playwright/test e rode `npx playwright install chromium`"
        )


def isolate_playwright_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Mantem Node e Playwright no PATH, excluindo conversores legados."""

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    for command in ("node", "playwright"):
        executable = shutil.which(command)
        if executable is None:
            pytest.fail(
                f"{command} nao disponivel neste ambiente — instale Playwright"
            )
        (fake_bin / command).symlink_to(executable)
    monkeypatch.setenv("PATH", str(fake_bin))


def png_dimensions(path: Path) -> tuple[int, int]:
    """Le largura e altura do cabecalho PNG sem dependencia adicional."""

    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


@pytest.mark.tools
def test_svgtoimage_with_unsupported_override_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
) -> None:
    monkeypatch.setenv("SVG2PNG_BIN", "conversor_inexistente_xyz")

    status, output, error = invoke_cli(
        monkeypatch,
        capsys,
        (repo_root / "tests/test-resources/sample.svg").read_text(),
    )

    assert status != 0
    assert not output
    assert "Conversor nao suportado" in error


@pytest.mark.tools
def test_svgtoimage_without_playwright_fails_with_hint(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SVG2PNG_BIN", "auto")
    monkeypatch.setenv("PATH", str(tmp_path))

    status, output, error = invoke_cli(
        monkeypatch,
        capsys,
        (repo_root / "tests/test-resources/sample.svg").read_text(),
    )

    assert status != 0
    assert not output
    assert "Playwright" in error


@pytest.mark.tools
def test_svgtoimage_generates_png_with_correct_dimensions(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    tmp_path: Path,
) -> None:
    assert_playwright_available()
    isolate_playwright_path(monkeypatch, tmp_path)

    status, output, error = invoke_cli(
        monkeypatch,
        capsys,
        (repo_root / "tests/test-resources/sample.svg").read_text(),
    )
    result = json.loads(output)
    image_path = Path(result["imagePath"])

    assert status == 0
    assert not error
    assert image_path.is_file()
    assert png_dimensions(image_path) == (100, 100)


@pytest.mark.tools
def test_svgtoimage_returns_markdown_path(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
) -> None:
    assert_playwright_available()

    status, output, _ = invoke_cli(
        monkeypatch,
        capsys,
        (repo_root / "tests/test-resources/sample.svg").read_text(),
    )
    result = json.loads(output)

    assert status == 0
    assert result["markdown"] == f"![]({result['imagePath']})"


@pytest.mark.tools
def test_svgtoimage_output_is_valid_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
) -> None:
    assert_playwright_available()

    status, output, _ = invoke_cli(
        monkeypatch,
        capsys,
        (repo_root / "tests/test-resources/sample.svg").read_text(),
    )
    result = json.loads(output)

    assert status == 0
    assert set(result) == {"imagePath", "markdown"}
