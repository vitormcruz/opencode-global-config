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
def test_curated_test_index_mentions_roles_meta_suite_and_one_table(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "AGENTS.md"

    status, _, _ = run_scaffold("--testes-produto", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    assert "| backend |" in content
    assert "testes-produto/backend" in content
    assert content.count("| Especialidade | Script |") == 1
    assert "Chama as suítes backend e segurança" not in content
    assert "conforme a curadoria do projeto-alvo" in content
    assert "Agregador: `testes-produto`" in content
    assert "agente `qa`" in content
    assert "`curador-produto`" in content
    assert "`testes-produto/tests/`" in content


@pytest.mark.unit
def test_curated_doc_scaffold_references_separate_test_spec(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "README.md"

    status, _, _ = run_scaffold("--doc", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    assert "testes-por-especialidade.md" in content
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
