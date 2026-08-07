"""Extracao de documentos via Docling com contrato JSON stdin/stdout."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any

from opencode_config.lib.contract import ToolResult
from opencode_config.lib.environment import EnvironmentKind, detect_environment
from opencode_config.lib.process import run_command

SUPPORTED_FORMATS = frozenset({"md", "markdown", "json", "text", "txt", "html"})
DOCS_URL = "https://github.com/docling-project/docling"


def _installation_hint() -> str:
    """Retorna instrucoes de instalacao adequadas ao sistema operacional."""

    if detect_environment() is EnvironmentKind.WINDOWS:
        return (
            "Recomendado: py -m pip install --user pipx && pipx ensurepath && "
            "pipx install docling | Alternativa: py -m pip install --user docling | "
            f"Docs: {DOCS_URL}"
        )

    return (
        "Recomendado: pipx install docling | Se pipx nao instalado: "
        "pip install --user pipx && pipx ensurepath | Ubuntu/WSL: "
        "sudo apt-get install -y pipx && pipx install docling | "
        f"Docs: {DOCS_URL}"
    )


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _is_false(value: Any) -> bool:
    return value is False or str(value) in {"false", "False", "0"}


def _read_payload() -> tuple[Mapping[str, Any], str]:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        return {}, f"Entrada JSON invalida: {error}"

    if not isinstance(payload, Mapping):
        return {}, "Entrada JSON invalida: esperado um objeto"
    return payload, ""


def _failure(
    stderr: str,
    *,
    hint: str = "",
    stdout: str = "",
) -> ToolResult:
    return ToolResult.failure(
        engine="docling",
        stderr=stderr,
        stdout=stdout,
        hint=hint,
    )


def _collect_artifacts(
    output_dir: Path,
    output_dir_text: str,
    output_format: str,
) -> list[str]:
    extension = output_format
    if output_format in {"md", "markdown"}:
        extension = "md"
    elif output_format == "text":
        extension = "txt"

    if not output_dir.is_dir():
        return []

    return [
        os.path.join(output_dir_text, path.name)
        for path in sorted(output_dir.iterdir())
        if path.is_file() and path.name.endswith(f".{extension}")
    ]


def extract_document(payload: Mapping[str, Any]) -> ToolResult:
    """Executa Docling para um payload JSON ja validado."""

    docling = shutil.which("docling")
    if docling is None:
        return _failure(
            "docling nao encontrado no PATH",
            hint=_installation_hint(),
        )

    source_file = _string_value(payload.get("source"))
    if not source_file:
        return _failure("Campo 'source' e obrigatorio")

    is_url = source_file.startswith(("http://", "https://"))
    source_path = Path(source_file)
    if not is_url and not source_path.is_file():
        return _failure(f"Arquivo fonte nao encontrado: {source_file}")

    output_format = _string_value(payload.get("to")) or "md"
    if output_format not in SUPPORTED_FORMATS:
        return _failure(
            f"Formato 'to' invalido: '{output_format}'. "
            "Use: md, json, text ou html"
        )
    if output_format == "txt":
        output_format = "text"

    output_dir_value = _string_value(payload.get("outputDir"))
    if output_dir_value:
        output_dir_text = output_dir_value
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir_text = f"./out/doc-extract/{timestamp}"
    output_dir = Path(output_dir_text)

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        return _failure(f"Nao foi possivel criar o diretorio de saida: {error}")

    args = ["--to", output_format, "--output", output_dir_text]
    if _is_false(payload.get("ocr")):
        args.append("--no-ocr")
    if _is_false(payload.get("tables")):
        args.append("--no-table-structure")

    image_export_mode = _string_value(payload.get("imageExportMode"))
    if image_export_mode:
        args.extend(["--image-export-mode", image_export_mode])

    device = _string_value(payload.get("device")) or "cpu"
    args.extend(["--device", device])

    extra_args = payload.get("extraArgs")
    if isinstance(extra_args, list):
        args.extend(_string_value(argument) for argument in extra_args)

    args.append(source_file)

    try:
        command_result = run_command([docling, *args])
    except OSError as error:
        return _failure(f"Nao foi possivel executar docling: {error}")

    if not command_result.succeeded:
        return _failure(
            command_result.stderr,
            stdout=command_result.stdout,
        )

    try:
        artifacts = _collect_artifacts(
            output_dir,
            output_dir_text,
            output_format,
        )
    except OSError as error:
        return _failure(
            f"Nao foi possivel listar os artefatos gerados: {error}",
            stdout=command_result.stdout,
        )

    return ToolResult.success(
        engine="docling",
        artifacts=artifacts,
        stdout=command_result.stdout,
        stderr=command_result.stderr,
    )


def main() -> int:
    """Le stdin, executa a extracao e imprime uma unica resposta JSON."""

    payload, parse_error = _read_payload()
    result = _failure(parse_error) if parse_error else extract_document(payload)
    print(result.to_json())
    return 0
