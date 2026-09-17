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
def test_curated_test_index_mentions_roles_meta_suite_and_selected_suites(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "AGENTS.md"

    status, _, _ = run_scaffold("--testes-produto", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    assert "| backend | `testes-produto/backend` |" in content
    assert "| segurança | `testes-produto/seguranca` |" in content
    assert "Agregador: `testes-produto`" in content
    assert "agente `qa`" in content
    assert "`curador-produto`" in content
    assert "`testes-produto/tests/`" in content


@pytest.mark.unit
def test_curated_doc_scaffold_describes_specialty_specs_and_concordion(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "README.md"

    status, _, _ = run_scaffold("--doc", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    assert "Concordion-Markdown" in content
    assert "Specs executáveis da especialidade backend" in content
    assert "Specs executáveis da especialidade segurança" in content
    assert "tradutor Python" in content
