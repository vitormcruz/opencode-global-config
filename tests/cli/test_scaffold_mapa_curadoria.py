from io import StringIO
from pathlib import Path

import pytest

from opencode_config.cli import scaffold_mapa


def run_scaffold(*arguments: str) -> tuple[int, str, str]:
    output = StringIO()
    error = StringIO()
    status = scaffold_mapa.run(
        list(arguments),
        output=output,
        error=error,
    )
    return status, output.getvalue(), error.getvalue()


@pytest.mark.unit
def test_curated_test_index_only_references_the_separate_spec(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "AGENTS.md"

    status, _, _ = run_scaffold("--testes-produto", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    assert "docs/testes-por-especialidade.md" in content
    assert "| Especialidade | Script |" not in content
    assert "testes-produto/backend" not in content
    assert "agente `qa`" not in content
    assert "`curador-produto`" not in content


@pytest.mark.unit
def test_curated_doc_scaffold_references_separate_test_spec(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "README.md"

    status, _, _ = run_scaffold("--doc", str(destination))
    content = destination.read_text(encoding="utf-8")
    tests_spec = tmp_path / "testes-por-especialidade.md"

    assert status == 0
    assert "testes-por-especialidade.md" in content
    assert tests_spec.is_file()
    assert "# Testes por Especialidade" in tests_spec.read_text(encoding="utf-8")
    assert "Concordion-Markdown" not in content
    assert "testes-produto/backend" not in content
    assert "testes-produto/seguranca" not in content


@pytest.mark.unit
def test_curated_doc_scaffold_does_not_embed_suite_list(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "README.md"

    status, _, _ = run_scaffold("--doc", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    assert "testes-por-especialidade.md" in content
    assert "- dados: `testes-produto/dados`" not in content
    assert "- frontend: `testes-produto/frontend`" not in content
    assert "- backend: `testes-produto/backend`" not in content
    assert "- segurança: `testes-produto/seguranca`" not in content
    assert "- Agregador: `testes-produto`" not in content
