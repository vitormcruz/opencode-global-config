"""Guardas da infra Concordion que executa as asserções dos ADRs.

Os 6 ADRs declaram fixtures com ``executarVerificacoes()`` e ``veredito``.
Estes testes garantem que o build Gradle renomeia as specs de ``docs/adr/``
para nomes de fixture válidos, inclui cada fixture na suíte da especialidade
correta e que as fixtures existem com os métodos declarados.
"""

from __future__ import annotations

from pathlib import Path
import re

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
GROOVY_DIR = REPOSITORY_ROOT / "src" / "test" / "groovy"


def numbered_adrs(repo_root: Path) -> list[tuple[str, str]]:
    return [
        (path.name[:4], f"Adr{path.name[:4]}Fixture")
        for path in sorted(repo_root.joinpath("docs", "adr").glob("[0-9][0-9][0-9][0-9]-*.md"))
    ]


@pytest.mark.unit
def test_build_renders_adr_specs_with_fixture_names(repo_root: Path) -> None:
    build = (repo_root / "build.gradle").read_text(encoding="utf-8")

    assert "renderAdrSpecs" in build
    assert "docs/adr" in build
    assert "Adr" in build


@pytest.mark.integration
def test_render_adr_specs_task_derives_every_numbered_adr_spec(
    repo_root: Path,
) -> None:
    """Guarda comportamental: a task deriva as specs numeradas, sem diagramas.

    Executa ``gradle renderAdrSpecs`` do build real (validação dirigida do
    build; não executa suítes de teste) e exige as saídas derivadas e a
    ausência dos diagramas C4 no classpath. Um include que não case nada
    (task NO-SOURCE silenciosa) ou que copie diagramas faz este teste falhar.
    """

    import os
    import shutil
    import subprocess

    gradle = shutil.which("gradle")
    if gradle is None:
        pytest.fail(
            "gradle ausente no PATH; execute o bootstrap user-space "
            "(install_gradle)"
        )
    java_home = os.environ.get("JAVA_HOME", "")
    if not java_home or not Path(java_home, "bin", "java").exists():
        pytest.fail(
            "JAVA_HOME ausente ou invalido; execute o bootstrap user-space "
            "(install_java) e carregue o PATH persistido no .bashrc"
        )

    environment = {**os.environ, "JAVA_HOME": java_home}
    completed = subprocess.run(
        [gradle, "-q", "renderAdrSpecs", "--no-daemon"],
        cwd=repo_root,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr

    generated = repo_root / "build" / "generated" / "adr-specs"
    derived = sorted(path.name for path in generated.glob("*.md"))
    assert derived == [f"Adr{number}.md" for number, _ in numbered_adrs(repo_root)]
    assert list(generated.glob("diagrama-*")) == []


@pytest.mark.unit
@pytest.mark.parametrize(
    ("adr_number", "fixture"),
    numbered_adrs(REPOSITORY_ROOT),
)
def test_build_registers_each_adr_fixture_in_one_specialty_suite(
    repo_root: Path,
    adr_number: str,
    fixture: str,
) -> None:
    build = (repo_root / "build.gradle").read_text(encoding="utf-8")

    assert re.search(rf"'{fixture}'", build)
    assert build.count(f"'{fixture}'") == 1
    assert f"Adr{adr_number}" == fixture.removesuffix("Fixture")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("adr_number", "fixture"),
    numbered_adrs(REPOSITORY_ROOT),
)
def test_every_adr_has_a_real_fixture_with_the_declared_api(
    adr_number: str,
    fixture: str,
) -> None:
    adr = next((REPOSITORY_ROOT / "docs" / "adr").glob(f"{adr_number}-*.md"))
    fixture_file = GROOVY_DIR / f"{fixture}.groovy"

    assert adr.is_file()
    assert "executarVerificacoes()" in adr.read_text(encoding="utf-8")
    assert fixture_file.is_file()

    body = fixture_file.read_text(encoding="utf-8")
    assert "executarVerificacoes()" in body
    assert "getVeredito" in body
    assert "ConcordionRunner" in body


@pytest.mark.unit
def test_fixtures_check_real_repository_artifacts() -> None:
    """Cada fixture verifica artefatos reais; nenhuma retorna veredito fixo."""

    for fixture_file in sorted(GROOVY_DIR.glob("Adr*.groovy")):
        body = fixture_file.read_text(encoding="utf-8")
        assert "repo.root" in body, fixture_file.name
        assert "Files.isRegularFile" in body or "JsonSlurper" in body, (
            fixture_file.name
        )


def _adr_table_literals(spec: str) -> list[str]:
    values: list[str] = []
    for line in spec.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 2 or cells[0] in {"Entrada", "Veredito"}:
            continue
        literal = re.fullmatch(r"`([^`]+)`", cells[1])
        if literal:
            values.append(literal.group(1))
    return values


@pytest.mark.unit
@pytest.mark.parametrize(
    ("adr_number", "fixture_name", "criteria"),
    [
        ("0006", "Adr0006Fixture", ("MCP-01",)),
        ("0008", "Adr0008Fixture", ("A8-01", "A8-02", "A8-03")),
    ],
)
def test_mcp_adrs_execute_spec_tables_through_their_fixtures(
    adr_number: str,
    fixture_name: str,
    criteria: tuple[str, ...],
) -> None:
    adr = next((REPOSITORY_ROOT / "docs" / "adr").glob(f"{adr_number}-*.md"))
    fixture_file = GROOVY_DIR / f"{fixture_name}.groovy"
    spec = adr.read_text(encoding="utf-8")
    fixture = fixture_file.read_text(encoding="utf-8")

    assert "#execute=" not in spec
    assert "#assertEquals=" not in spec
    assert re.search(r'\[[^\]]+\]\(- "[A-Za-z]\w*\(\)"\)', spec)
    assert re.search(r'\[[^\]]+\]\(- "\?=veredito[^\"]*"\)', spec)
    assert "| Entrada | Resultado esperado |" in spec
    for criterion in criteria:
        assert f"### {criterion}:" in spec

    assert f"SPEC = 'docs/adr/{adr.name}'" in fixture
    assert "lerValoresEsperados(" in fixture
    assert "valorEsperado(" in fixture
    for value in _adr_table_literals(spec):
        assert f"'{value}'" not in fixture and f'"{value}"' not in fixture, (
            f"{fixture_name} duplica valor da spec: {value}"
        )


@pytest.mark.unit
def test_adr0006_fixture_checks_canonical_config_for_mcp_entries() -> None:
    body = (GROOVY_DIR / "Adr0006Fixture.groovy").read_text(encoding="utf-8")

    assert "opencode.json" in body
    assert "JsonSlurper" in body


@pytest.mark.unit
def test_adr0007_fixture_checks_upstream_detection() -> None:
    body = (GROOVY_DIR / "Adr0007Fixture.groovy").read_text(encoding="utf-8")
    build = (REPOSITORY_ROOT / "build.gradle").read_text(encoding="utf-8")
    backend_fixtures = re.search(r"backend\s*:\s*\[(.*?)\]", build, re.DOTALL)

    assert backend_fixtures is not None
    assert "Adr0007Fixture" in backend_fixtures.group(1)
    assert "harness-skills detect" in body
    assert "test_upstream_detect.py" in body
