"""Guardas da infra Concordion que executa as asserções dos ADRs.

Os 6 ADRs declaram fixtures com ``executarVerificacoes()`` e ``veredito``.
Estes testes garantem que o build Gradle renomeia as specs de ``docs/adr/``
para nomes de fixture válidos, inclui cada fixture na suíte da especialidade
correta e que as fixtures existem com os métodos declarados.
"""

from __future__ import annotations

from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
GROOVY_DIR = REPOSITORY_ROOT / "src" / "test" / "groovy"

SPECIALTY_ADRS = {
    "backend": ("Adr0001Fixture", "Adr0002Fixture", "Adr0003Fixture",
                "Adr0004Fixture", "Adr0005Fixture"),
    "seguranca": ("Adr0006Fixture",),
}


@pytest.mark.unit
def test_build_renders_adr_specs_with_fixture_names(repo_root: Path) -> None:
    build = (repo_root / "build.gradle").read_text(encoding="utf-8")

    assert "renderAdrSpecs" in build
    assert "docs/adr" in build
    assert "Adr" in build


@pytest.mark.unit
def test_render_adr_specs_glob_does_not_match_the_c4_diagrams(
    repo_root: Path,
) -> None:
    build = (repo_root / "build.gradle").read_text(encoding="utf-8")

    assert "[0-9][0-9][0-9][0-9]-*.md" in build
    assert "include '*-*.md'" not in build


@pytest.mark.unit
@pytest.mark.parametrize(
    ("specialty", "fixtures"),
    sorted(SPECIALTY_ADRS.items()),
)
def test_build_includes_adr_fixtures_in_the_specialty_suite(
    repo_root: Path,
    specialty: str,
    fixtures: tuple[str, ...],
) -> None:
    build = (repo_root / "build.gradle").read_text(encoding="utf-8")

    assert specialty in build
    for fixture in fixtures:
        assert fixture in build


@pytest.mark.unit
@pytest.mark.parametrize(
    ("adr_number", "fixture"),
    [
        ("0001", "Adr0001Fixture"),
        ("0002", "Adr0002Fixture"),
        ("0003", "Adr0003Fixture"),
        ("0004", "Adr0004Fixture"),
        ("0005", "Adr0005Fixture"),
        ("0006", "Adr0006Fixture"),
    ],
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


@pytest.mark.unit
def test_adr0006_fixture_checks_canonical_config_for_mcp_entries() -> None:
    body = (GROOVY_DIR / "Adr0006Fixture.groovy").read_text(encoding="utf-8")

    assert "opencode.json" in body
    assert "JsonSlurper" in body
