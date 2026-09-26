"""Testes do array `plugin` do opencode.json e da documentação associada.

Cobertura: pin exato de versão por entry, paridade entre os plugins do
config e a seção "Plugins" do README.md, e integridade do registro de
revisão de segurança (UPSTREAM.md) do plugin provisório.
"""

import json
import re
from pathlib import Path

import pytest


PROVISORY_PLUGIN = "opencode-task-model"
PLUGIN_DIR = "harness-conf/plugins"
UPSTREAM_REQUIRED_FIELDS = (
    "plugin:",
    "versao_pinada:",
    "repositorio:",
    "commit:",
    "revisado_em:",
    "decisao:",
)


def load_plugin_entries(repo_root: Path) -> list[str]:
    config = json.loads(
        (repo_root / "harness-conf" / "opencode.json").read_text(
            encoding="utf-8"
        )
    )
    entries = config.get("plugin", [])
    assert entries, "opencode.json sem array 'plugin' ou array vazio"
    return entries


def split_spec(entry: str) -> tuple[str, str | None]:
    """Separa nome e versão de um spec npm.

    `@` só inicia a versão quando não é o primeiro caractere: em pacotes
    escoped ele abre o nome (`@scope/name`). A versão é o trecho após o
    último `@` que vem depois da posição 0.
    """

    marker = entry.rfind("@")
    if marker <= 0:
        return entry, None
    return entry[:marker], entry[marker + 1 :]


def plugins_section(readme: str) -> str:
    match = re.search(r"^## Plugins$(.*?)(?=^## |\Z)", readme, re.M | re.S)
    assert match, "README.md sem a seção '## Plugins'"
    return match.group(1)


@pytest.mark.unit
def test_plugins_are_pinned_to_exact_versions(repo_root: Path):
    for entry in load_plugin_entries(repo_root):
        name, version = split_spec(entry)
        if version is None:
            # Sem versão só é aceitável em pacote escoped (@scope/name),
            # onde o nome já evita resolução ambígua; pacote solto sem
            # pin flutuaria a cada restart.
            assert name.startswith("@"), (
                f"plugin não-escoped sem pin exato: {entry}"
            )
            continue
        assert re.fullmatch(r"\d+\.\d+\.\d+", version), (
            f"plugin sem pin exato semver (aceite apenas X.Y.Z; "
            f"rejeite @latest, range ou dist-tag): {entry}"
        )


@pytest.mark.unit
def test_provisory_task_model_plugin_is_documented(repo_root: Path):
    entries = load_plugin_entries(repo_root)
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    section = plugins_section(readme)

    names = [split_spec(entry)[0] for entry in entries]
    in_config = PROVISORY_PLUGIN in names
    in_readme = PROVISORY_PLUGIN in section and "PROVISÓRIO" in section
    assert in_config == in_readme, (
        f"paridade quebrada: {PROVISORY_PLUGIN} no config={in_config}, "
        f"documentado com PROVISÓRIO no README={in_readme}. "
        "O lembrete de remoção depende do par config+README consistente."
    )
    assert in_config, (
        f"{PROVISORY_PLUGIN} ausente do config e do README: se a remoção "
        "foi intencional (suporte nativo), atualize este teste junto."
    )


@pytest.mark.unit
def test_provisory_plugin_has_upstream_review(repo_root: Path):
    upstream = (
        repo_root / PLUGIN_DIR / PROVISORY_PLUGIN / "UPSTREAM.md"
    )
    assert upstream.is_file(), (
        f"UPSTREAM.md ausente em {PLUGIN_DIR}/{PROVISORY_PLUGIN}/: "
        "import externo exige revisão de segurança registrada"
    )
    content = upstream.read_text(encoding="utf-8")
    for field in UPSTREAM_REQUIRED_FIELDS:
        assert field in content, (
            f"UPSTREAM.md sem o campo obrigatório '{field}'"
        )
    assert re.search(r"^decisao: GO\b", content, re.M), (
        "UPSTREAM.md sem decisão GO registrada; revisão pendente ou "
        "bloqueada"
    )
    pin = re.search(r"^versao_pinada:\s*(\S+)", content, re.M)
    assert pin, "UPSTREAM.md sem versão pinada legível"
    entries = load_plugin_entries(repo_root)
    pinned = [
        entry
        for entry in entries
        if split_spec(entry)[0] == PROVISORY_PLUGIN
    ]
    assert pinned, (
        f"{PROVISORY_PLUGIN} sumiu do config; remova ou revise o UPSTREAM.md"
    )
    _, version = split_spec(pinned[0])
    assert version == pin.group(1), (
        f"pin do config ({version}) diverge do UPSTREAM.md "
        f"({pin.group(1)}); nova versão exige nova revisão registrada"
    )
