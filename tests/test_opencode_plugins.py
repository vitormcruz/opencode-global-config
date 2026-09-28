"""Testes do array `plugin` do opencode.json e da documentação associada.

Cobertura: pin exato de versão por entry, paridade entre os plugins do
config e a seção "Plugins" do README.md, integridade do registro de
revisão de segurança (UPSTREAM.md) do plugin provisório e aviso de
flutuação de versão do plugin de quota (ratificado sem pin).
"""

import json
import re
import shutil
import subprocess
import warnings
from pathlib import Path

import pytest


PROVISORY_PLUGIN = "opencode-task-model"
QUOTA_PLUGIN = "@slkiser/opencode-quota"
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


def _quota_rated_version(repo_root: Path) -> str:
    """Lê `versao_ratificada` do UPSTREAM.md do plugin de quota."""

    upstream = repo_root / PLUGIN_DIR / "opencode-quota" / "UPSTREAM.md"
    assert upstream.is_file(), (
        f"UPSTREAM.md ausente em {PLUGIN_DIR}/opencode-quota/: o plugin "
        "de quota exige registro de ratificação com versao_ratificada"
    )
    content = upstream.read_text(encoding="utf-8")
    match = re.search(r"^versao_ratificada:\s*(\S+)", content, re.M)
    assert match, (
        f"UPSTREAM.md do quota sem versao_ratificada legível ({upstream})"
    )
    return match.group(1)


def _query_npm_version(package: str) -> str:
    """Consulta a versão mais recente do pacote no registro npm."""

    npm = shutil.which("npm")
    if not npm:
        pytest.fail(
            "npm não encontrado no PATH. Instale o Node.js/npm no "
            "ambiente do usuário e execute novamente.",
            pytrace=False,
        )
    # 60 s é rede de segurança sobre consulta que costuma levar poucos
    # segundos; estouro vira fail acionável, nunca espera infinita.
    try:
        result = subprocess.run(
            [npm, "view", package, "version"],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )
    except FileNotFoundError:
        pytest.fail(
            "npm não pôde ser executado; verifique a instalação do "
            "Node.js no ambiente do usuário.",
            pytrace=False,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(
            f"`npm view {package} version` excedeu 60s (processo morto). "
            "Verifique rede/registro npm e execute novamente.",
            pytrace=False,
        )
    except subprocess.CalledProcessError as error:
        stderr = (error.stderr or "").strip()[-500:]
        pytest.fail(
            f"`npm view {package} version` falhou. Saída de erro: "
            f"{stderr}. Verifique rede/registro npm e execute novamente.",
            pytrace=False,
        )
    version = result.stdout.strip()
    assert version, f"`npm view {package} version` devolveu saída vazia"
    return version


def _check_quota_flutuacao(ratified: str, current: str) -> None:
    """Versão atual diferente da ratificada emite warning (não falha)."""

    if current == ratified:
        return
    warnings.warn(
        f"{QUOTA_PLUGIN} flutuou: versao_ratificada {ratified}, versão "
        f"atual {current}. Pergunte ao humano se quer validação de "
        "segurança antes de ratificar a nova versão "
        f"({PLUGIN_DIR}/opencode-quota/UPSTREAM.md).",
        stacklevel=2,
    )


@pytest.mark.unit
def test_quota_flutuacao_mesma_versao_nao_avisa() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _check_quota_flutuacao("4.10.6", "4.10.6")


@pytest.mark.unit
def test_quota_flutuacao_emite_warning_com_instrucao() -> None:
    with pytest.warns(UserWarning, match="Pergunte ao humano"):
        _check_quota_flutuacao("4.10.6", "5.0.0")


@pytest.mark.integration
def test_quota_plugin_version_vigiada(repo_root: Path) -> None:
    ratified = _quota_rated_version(repo_root)
    current = _query_npm_version(QUOTA_PLUGIN)
    _check_quota_flutuacao(ratified, current)
