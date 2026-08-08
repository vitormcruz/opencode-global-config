#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "${script_dir}/../.." && pwd -P)"
python_bin="${OPENCODE_PYTHON:-python3}"

if ! command -v "$python_bin" >/dev/null 2>&1; then
  printf 'ERRO: Python 3.10+ nao encontrado. Instale Python por usuario.\n' >&2
  exit 1
fi

if ! "$python_bin" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' \
  >/dev/null 2>&1; then
  version="$("$python_bin" --version 2>&1 || printf 'versao desconhecida')"
  printf 'ERRO: %s encontrado; requer Python 3.10+.\n' "$version" >&2
  printf 'Instale Python por usuario e execute novamente.\n' >&2
  exit 1
fi

export PYTHONPATH="${repo_root}/src${PYTHONPATH:+:${PYTHONPATH}}"
exec "$python_bin" -m opencode_config.bootstrap.main \
  --repo-root "$repo_root" "$@"
