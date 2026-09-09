"""Factory de adapters de harness com injecao de strategy por ambiente."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from opencode_config.harnesses import HarnessAdapter, HarnessDefinition
from opencode_config.harnesses.copilot import CopilotAdapter
from opencode_config.harnesses.opencode import (
    OpenCodeAdapter,
    OpenCodeEnvStrategy,
    OpenCodePosix,
    OpenCodeWindows,
)
from opencode_config.lib.environment import (
    EnvironmentKind,
    UnsupportedEnvironmentError,
)

_OPENCODE_STRATEGIES: Mapping[
    EnvironmentKind,
    Callable[[], OpenCodeEnvStrategy],
] = {
    EnvironmentKind.LINUX: OpenCodePosix,
    EnvironmentKind.WSL: OpenCodePosix,
    EnvironmentKind.WINDOWS: OpenCodeWindows,
}


def _create_opencode(environment: EnvironmentKind) -> HarnessAdapter:
    strategy_class = _OPENCODE_STRATEGIES.get(environment)
    if strategy_class is None:
        raise UnsupportedEnvironmentError(
            "O harness opencode nao possui strategy para o ambiente "
            f"{environment.name}"
        )
    return OpenCodeAdapter(strategy=strategy_class())


def _create_copilot(_environment: EnvironmentKind) -> HarnessAdapter:
    return CopilotAdapter()


HARNESSES: tuple[HarnessDefinition, ...] = (
    HarnessDefinition(
        name="opencode",
        create=_create_opencode,
        skip_variable="OPENCODE_SKIP_OPENCODE_ADAPTER",
    ),
    HarnessDefinition(
        name="copilot",
        create=_create_copilot,
        skip_variable="OPENCODE_SKIP_COPILOT_ADAPTER",
    ),
)


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
    environment: EnvironmentKind,
    selecao: Sequence[str] | None = None,
    *,
    registry: Sequence[HarnessDefinition] = HARNESSES,
) -> list[HarnessAdapter]:
    """Instancia os adapters selecionados com a strategy do ambiente."""

    if environment not in set(EnvironmentKind):
        raise ValueError(f"Ambiente nao suportado: {environment}")

    return [
        definition.create(environment)
        for definition in selecionar_harnesses(selecao, registry=registry)
    ]
