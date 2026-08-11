"""Renderizacao de SVG para PNG usando o Chromium do Playwright."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from opencode_config.lib.process import run_command

NODE_RENDER_SCRIPT = r"""
const fs = require("fs");
const { chromium } = require("playwright");

const outputPath = process.argv[1];
let browser;

(async () => {
  const svg = fs.readFileSync(0, "utf8");
  const dataUrl = `data:image/svg+xml;base64,${Buffer.from(svg).toString("base64")}`;
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.setContent(
    `<html><body style="margin:0;padding:0"><img id="svg" style="display:block" src="${dataUrl}"></body></html>`,
    { waitUntil: "load" }
  );
  const image = page.locator("#svg");
  await image.evaluate(element => {
    if (element.complete)
      return;
    return new Promise(resolve => element.addEventListener("load", resolve, { once: true }));
  });
  await image.screenshot({
    path: outputPath,
    animations: "disabled",
    omitBackground: true
  });
})().catch(error => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exitCode = 1;
}).finally(async () => {
  if (browser)
    await browser.close();
});
"""


def _find_node() -> str | None:
    return shutil.which("node")


def _find_playwright() -> str | None:
    return shutil.which("playwright")


def _node_environment(playwright: str) -> dict[str, str]:
    """Configura NODE_PATH para o pacote usado pelo launcher do Playwright."""

    executable = Path(playwright).resolve()
    module_paths = [
        executable.parent / "node_modules",
        executable.parent.parent / "node_modules",
        executable.parent / "node_modules" / "@playwright" / "test" / "node_modules",
    ]

    npm = shutil.which("npm")
    if npm:
        npm_root = run_command([npm, "root", "-g"])
        if npm_root.succeeded and npm_root.stdout.strip():
            module_paths.append(Path(npm_root.stdout.strip()))

    paths = [
        os.fspath(path)
        for path in module_paths
        if path.is_dir()
    ]
    existing = os.environ.get("NODE_PATH")
    if existing:
        paths.extend(existing.split(os.pathsep))

    environment = os.environ.copy()
    if paths:
        environment["NODE_PATH"] = os.pathsep.join(paths)
    return environment


def render_svg(svg: str) -> tuple[Path | None, str]:
    """Renderiza SVG e retorna o PNG persistido ou uma mensagem de erro."""

    tool = os.environ.get("SVG2PNG_BIN") or "auto"
    if tool not in {"auto", "playwright"}:
        return None, f"Conversor nao suportado: {tool}"

    node = _find_node()
    playwright = _find_playwright()
    if node is None or playwright is None:
        return (
            None,
            "Playwright nao encontrado. Instale @playwright/test e "
            "execute `npx playwright install chromium`.",
        )

    output_dir = Path(tempfile.mkdtemp(prefix="opencode-svgtoimage-"))
    output_path = output_dir / "diagram.png"
    result = run_command(
        [
            node,
            "-e",
            NODE_RENDER_SCRIPT,
            os.fspath(output_path),
        ],
        input_text=svg,
        env=_node_environment(playwright),
    )

    if not result.succeeded:
        return None, result.stderr or "Falha ao renderizar SVG com Playwright"
    if not output_path.is_file():
        return None, "Playwright nao gerou o arquivo PNG esperado"
    return output_path, ""


def main() -> int:
    """Le SVG do stdin e imprime o caminho da imagem gerada."""

    image_path, error = render_svg(sys.stdin.read())
    if error:
        print(error, file=sys.stderr)
        return 1

    assert image_path is not None
    print(
        json.dumps(
            {
                "imagePath": os.fspath(image_path),
                "markdown": f"![]({image_path})",
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    return 0
