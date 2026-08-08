"""Contrato pytest do entry point opencode-browser-test."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

import pytest


def invoke(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
) -> tuple[int, str, str]:
    """Executa o entry point com argumentos controlados."""

    from opencode_config.cli.browser_test import main

    monkeypatch.setattr(sys, "argv", ["opencode-browser-test", *arguments])
    status = main()
    captured = capsys.readouterr()
    return status, captured.out, captured.err


def assert_browser_runtime_available() -> None:
    if shutil.which("node") is None:
        pytest.fail(
            "node nao instalado — instale Node.js para executar este teste"
        )
    if shutil.which("playwright") is None:
        pytest.fail(
            "playwright nao instalado — instale @playwright/test para executar este teste"
        )


@pytest.mark.tools
def test_browser_test_help_returns_success(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    status, output, error = invoke(monkeypatch, capsys, ["--help"])

    assert status == 0
    assert "opencode-browser-test" in output
    assert not error


@pytest.mark.tools
def test_browser_test_without_argument_returns_json_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    status, output, _ = invoke(monkeypatch, capsys, [])
    result = json.loads(output)

    assert status != 0
    assert result["ok"] is False
    assert "Uso:" in result["error"]


@pytest.mark.tools
def test_browser_test_with_missing_file_returns_json_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    status, output, _ = invoke(
        monkeypatch,
        capsys,
        ["/tmp/nao-existe-xyz-123.js"],
    )
    result = json.loads(output)

    assert status != 0
    assert result["ok"] is False
    assert "nao encontrado" in result["error"]


@pytest.mark.tools
def test_browser_test_rejects_non_javascript_file(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    script = tmp_path / "browser-test.txt"
    script.write_text("console.log('hello')", encoding="utf-8")

    status, output, _ = invoke(monkeypatch, capsys, [str(script)])
    result = json.loads(output)

    assert status != 0
    assert result["ok"] is False
    assert ".js" in result["error"]
    assert script.is_file()


@pytest.mark.tools
def test_browser_test_without_node_returns_json_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    script = tmp_path / "browser-test.js"
    script.write_text("console.log('hello')", encoding="utf-8")
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    monkeypatch.setenv("PATH", str(empty_bin))

    status, output, _ = invoke(monkeypatch, capsys, [str(script)])
    result = json.loads(output)

    assert status != 0
    assert result["ok"] is False
    assert "node" in result["error"]
    assert "opencode-bootstrap" in result["error"]
    assert not script.exists()


@pytest.mark.tools
def test_browser_test_deletes_script_after_success(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    assert_browser_runtime_available()
    script = tmp_path / "browser-test.js"
    script.write_text(
        "console.log(JSON.stringify({ok:true,screenshots:[],"
        'console:["test"],errors:[],duration_ms:0}));',
        encoding="utf-8",
    )

    status, output, _ = invoke(monkeypatch, capsys, [str(script)])
    result = json.loads(output)

    assert status == 0
    assert result["ok"] is True
    assert not script.exists()


@pytest.mark.tools
def test_browser_test_deletes_script_after_node_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    assert_browser_runtime_available()
    script = tmp_path / "browser-test.js"
    script.write_text(
        "throw new Error('deliberate failure');",
        encoding="utf-8",
    )

    status, output, _ = invoke(monkeypatch, capsys, [str(script)])
    result = json.loads(output)

    assert status != 0
    assert result["ok"] is False
    assert not script.exists()


@pytest.mark.tools
def test_browser_test_runs_real_playwright_script(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    assert_browser_runtime_available()
    script = tmp_path / "browser-test.js"
    script.write_text(
        """
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({headless: true});
  const page = await browser.newPage();
  await page.setContent("<title>browser-test</title>");
  console.log(JSON.stringify({
    ok: (await page.title()) === "browser-test",
    screenshots: [],
    console: ["real-playwright"],
    errors: [],
    duration_ms: 0
  }));
  await browser.close();
})().catch(error => {
  console.error(error.stack || String(error));
  process.exit(1);
});
""",
        encoding="utf-8",
    )

    status, output, _ = invoke(monkeypatch, capsys, [str(script)])
    result = json.loads(output)

    assert status == 0
    assert result["ok"] is True
    assert "real-playwright" in result["console"]
    assert not script.exists()
