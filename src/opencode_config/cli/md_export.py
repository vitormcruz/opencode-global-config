"""Exportacao de Markdown via Pandoc com contrato JSON stdin/stdout."""

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

SUPPORTED_FORMATS = frozenset({"docx", "pptx", "xlsx"})
DOCS_URL = "https://pandoc.org/installing.html"


def _installation_hint() -> str:
    """Retorna instrucoes de instalacao sem exigir privilegio elevado."""

    portable = (
        "Recomendado: baixe o ZIP portatil oficial e extraia em "
        "tools/pandoc/ no repositorio"
    )
    if detect_environment() is EnvironmentKind.WINDOWS:
        return (
            f"{portable} | Windows: use o executavel pandoc.exe do ZIP "
            f"portatil | Docs: {DOCS_URL}"
        )

    return (
        f"{portable} | Linux/WSL: instale no user-space ou use o ZIP portatil | "
        f"macOS: use o ZIP portatil ou Homebrew | Docs: {DOCS_URL}"
    )


def _repository_roots() -> tuple[Path, ...]:
    """Retorna o diretorio atual e a raiz do repositorio do pacote."""

    package_root = Path(__file__).resolve().parents[3]
    current_root = Path.cwd()
    if current_root == package_root:
        return (current_root,)
    return (current_root, package_root)


def _portable_pandoc_candidates() -> list[Path]:
    candidates: list[Path] = []
    for repository_root in _repository_roots():
        for directory_name in ("tools", ".tools", "portable", "bin"):
            directory = repository_root / directory_name
            if not directory.is_dir():
                continue
            candidates.extend(
                path
                for path in sorted(directory.rglob("*"))
                if path.is_file() and path.name.lower() in {"pandoc", "pandoc.exe"}
            )
    return candidates


def _find_pandoc() -> str | None:
    """Localiza Pandoc primeiro no PATH e depois no armazenamento portatil."""

    in_path = shutil.which("pandoc")
    if in_path:
        return in_path

    for candidate in _portable_pandoc_candidates():
        if os.name == "nt" or os.access(candidate, os.X_OK):
            return os.fspath(candidate)
    return None


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _is_true(value: Any) -> bool:
    return value is True or str(value) in {"true", "True", "1"}


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
        engine="pandoc",
        stderr=stderr,
        stdout=stdout,
        hint=hint,
    )


def export_markdown(payload: Mapping[str, Any]) -> ToolResult:
    """Executa Pandoc para um payload JSON ja validado."""

    pandoc = _find_pandoc()
    if pandoc is None:
        return _failure(
            "pandoc nao encontrado no PATH",
            hint=_installation_hint(),
        )

    source_file = _string_value(payload.get("source"))
    if not source_file:
        return _failure("Campo 'source' e obrigatorio")

    output_format = _string_value(payload.get("to"))
    if not output_format:
        return _failure("Campo 'to' e obrigatorio (docx | pptx | xlsx)")
    if output_format not in SUPPORTED_FORMATS:
        return _failure(
            f"Formato 'to' invalido: '{output_format}'. "
            "Use: docx, pptx ou xlsx"
        )

    if not Path(source_file).is_file():
        return _failure(f"Arquivo fonte nao encontrado: {source_file}")

    output_path_value = _string_value(payload.get("outputPath"))
    output_dir_value = _string_value(payload.get("outputDir"))
    if output_path_value:
        output_path_text = output_path_value
    else:
        if not output_dir_value:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_dir_value = f"./out/md-export/{timestamp}"
        source_name = Path(source_file).name
        base_name = source_name[:-3] if source_name.endswith(".md") else source_name
        output_path_text = os.path.join(
            output_dir_value,
            f"{base_name}.{output_format}",
        )

    extra_args = payload.get("extraArgs")
    internal_force = (
        isinstance(extra_args, list)
        and any(
            _string_value(argument) in {"--force", "--overwrite"}
            for argument in extra_args
        )
    )

    output_path = Path(output_path_text)
    if output_path.is_file() and not internal_force:
        return _failure(
            f"Arquivo de saida ja existe: {output_path_text}. "
            'Passe extraArgs: ["--overwrite"] para sobrescrever.'
        )

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        return _failure(f"Nao foi possivel criar o diretorio de saida: {error}")

    args: list[str] = []
    from_format = _string_value(payload.get("from"))
    args.append(f"--from={from_format or 'gfm'}")
    args.append(f"--to={output_format}")
    args.append(f"--output={output_path_text}")

    template = _string_value(payload.get("template"))
    if template:
        if not Path(template).is_file():
            return _failure(f"Template nao encontrado: {template}")
        args.append(f"--reference-doc={template}")

    if _is_true(payload.get("toc")):
        args.append("--toc")

    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        for key, value in metadata.items():
            args.extend(["-M", f"{key}={value}"])

    if isinstance(extra_args, list):
        args.extend(
            _string_value(argument)
            for argument in extra_args
            if _string_value(argument) not in {"--force", "--overwrite"}
        )

    args.append(source_file)

    try:
        command_result = run_command([pandoc, *args])
    except OSError as error:
        return _failure(f"Nao foi possivel executar pandoc: {error}")

    output_path = Path(output_path_text)
    if not command_result.succeeded or not output_path.is_file():
        return _failure(
            command_result.stderr,
            stdout=command_result.stdout,
        )

    return ToolResult.success(
        engine="pandoc",
        artifacts=[output_path_text],
        stdout=command_result.stdout,
        stderr=command_result.stderr,
    )


def main() -> int:
    """Le stdin, executa a exportacao e imprime uma unica resposta JSON."""

    payload, parse_error = _read_payload()
    result = _failure(parse_error) if parse_error else export_markdown(payload)
    print(result.to_json())
    return 0
