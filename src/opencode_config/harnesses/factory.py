"""Factory de adapters de harness com injecao de strategy por ambiente."""

from __future__ import annotations

from collections.abc import Sequence

from opencode_config.harnesses import HarnessAdapter, HarnessDefinition

HARNESSES: tuple[HarnessDefinition, ...] = ()


def selecionar_harnesses(
    selecao: Sequence[str] | None = None,
    *,
    registry: Sequence[HarnessDefinition] = HARNESSES,
) -> tuple[HarnessDefinition, ...]:
    """Filtra o registry pela selecao, preservando a ordem do registry."""

    names = (
        ()
        if selecao is None
        else tuple(name.strip() for name in selecao if name.strip())
    )
    definitions = {definition.name: definition for definition in registry}
    unknown = [name for name in names if name not in definitions]
    if unknown:
        raise ValueError(f"harness desconhecido: {', '.join(unknown)}")
    if not names:
        return tuple(registry)
    selected = set(names)
    return tuple(
        definition for definition in registry if definition.name in selected
    )


def criar_adapters(
    environment,
    selecao: Sequence[str] | None = None,
    *,
    registry: Sequence[HarnessDefinition] = HARNESSES,
) -> list[HarnessAdapter]:
    """Instancia os adapters selecionados com a strategy do ambiente."""

    from opencode_config.lib.environment import EnvironmentKind

    if environment not in set(EnvironmentKind):
        raise ValueError(f"Ambiente nao suportado: {environment}")

    return [
        definition.create(environment)
        for definition in selecionar_harnesses(selecao, registry=registry)
    ]
