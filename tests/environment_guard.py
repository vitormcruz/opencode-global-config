"""Guarda do ambiente de testes: .venv do checkout e pacote do checkout."""

import os
from pathlib import Path

WINDOWS_CMD_PATH_LIMIT = 8191

_CREATE_VENV = (
    "Crie a .venv do checkout: `python -m venv .venv` e, nela, "
    "`python -m pip install -r requirements-dev.txt -e .` "
    "(Linux/WSL: .venv/bin/python; Windows: .\\.venv\\Scripts\\python.exe). "
    "Depois rode .venv/bin/pytest (Windows: .\\.venv\\Scripts\\pytest.exe)."
)


def environment_problem(
    *,
    repo_root: Path,
    package_file: Path,
    prefix: Path,
) -> str | None:
    """Devolve a mensagem de erro acionável ou None se o ambiente é válido."""

    source_root = (repo_root / "src").resolve()
    venv_root = (repo_root / ".venv").resolve()

    if not package_file.resolve().is_relative_to(source_root):
        return (
            f"opencode_config foi importado de {package_file}, fora de "
            f"{source_root}: outro clone está instalado em modo editável "
            f"(pip install -e .). {_CREATE_VENV}"
        )
    if prefix.resolve() != venv_root:
        return (
            f"Os testes devem rodar na .venv do checkout ({venv_root}); "
            f"o interpretador atual é {prefix}. {_CREATE_VENV}"
        )
    return None


def normalize_windows_path(
    path_value: str,
    *,
    path_limit: int = WINDOWS_CMD_PATH_LIMIT,
) -> str:
    """Remove entradas inexistentes quando o PATH excede o limite do cmd."""

    if len(path_value) <= path_limit:
        return path_value

    normalized_entries: list[str] = []
    seen_entries: set[str] = set()
    for entry in path_value.split(os.pathsep):
        if not entry:
            continue
        expanded_entry = os.path.expandvars(entry)
        if not os.path.isdir(expanded_entry):
            continue
        entry_key = os.path.normcase(os.path.normpath(expanded_entry))
        if entry_key in seen_entries:
            continue
        seen_entries.add(entry_key)
        normalized_entries.append(entry)

    normalized_path = os.pathsep.join(normalized_entries)
    if len(normalized_path) > path_limit:
        raise ValueError(
            "O PATH continua acima do limite de "
            f"{path_limit} caracteres após remover entradas inexistentes."
        )
    return normalized_path
