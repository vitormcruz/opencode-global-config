"""Testes da factory de adapters de harness com injeção de strategy."""

from collections.abc import Callable
from pathlib import Path

import pytest

from opencode_config.harnesses import (
    ApplyOptions,
    HarnessAdapter,
    HarnessDefinition,
    criar_adapters,
    selecionar_harnesses,
)
from opencode_config.lib.environment import EnvironmentKind, UnsupportedEnvironmentError


class FakePosixStrategy:
    label = "posix"


class FakeWindowsStrategy:
    label = "windows"


class FakeOpenCodeAdapter:
    """Adapter fake: recebe a strategy pronta e nunca consulta o ambiente."""

    def __init__(self, strategy: object) -> None:
        self.strategy = strategy
        self.applied: list[tuple[Path, ApplyOptions]] = []

    @property
    def name(self) -> str:
        return "opencode-fake"

    def installed(self, environment: EnvironmentKind) -> bool:
        return True

    def apply(self, repository: Path, options: ApplyOptions) -> None:
        self.applied.append((repository, options))


class FakeCopilotAdapter:
    """Adapter fake sem strategy: harness que nao varia por SO."""

    def __init__(self) -> None:
        self.applied: list[tuple[Path, ApplyOptions]] = []

    @property
    def name(self) -> str:
        return "copilot-fake"

    def installed(self, environment: EnvironmentKind) -> bool:
        return False

    def apply(self, repository: Path, options: ApplyOptions) -> None:
        self.applied.append((repository, options))


FAKE_STRATEGIES: dict[
    EnvironmentKind,
    Callable[[], object],
] = {
    EnvironmentKind.LINUX: FakePosixStrategy,
    EnvironmentKind.WSL: FakePosixStrategy,
    EnvironmentKind.WINDOWS: FakeWindowsStrategy,
}


def fake_registry() -> tuple[HarnessDefinition, ...]:
    def create_opencode(environment: EnvironmentKind) -> HarnessAdapter:
        strategy_factory = FAKE_STRATEGIES.get(environment)
        if strategy_factory is None:
            raise UnsupportedEnvironmentError(
                f"Ambiente sem strategy: {environment.value}"
            )
        return FakeOpenCodeAdapter(strategy_factory())

    return (
        HarnessDefinition(
            name="opencode",
            create=create_opencode,
            skip_variable="OPENCODE_SKIP_OPENCODE_ADAPTER",
        ),
        HarnessDefinition(
            name="copilot",
            create=lambda _environment: FakeCopilotAdapter(),
            skip_variable="OPENCODE_SKIP_COPILOT_ADAPTER",
        ),
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "environment",
    (
        EnvironmentKind.LINUX,
        EnvironmentKind.WSL,
        EnvironmentKind.WINDOWS,
    ),
)
def test_factory_injects_strategy_by_environment(
    environment: EnvironmentKind,
) -> None:
    adapters = criar_adapters(environment, registry=fake_registry())

    opencode = adapters[0]
    expected = (
        FakePosixStrategy if environment is not EnvironmentKind.WINDOWS
        else FakeWindowsStrategy
    )
    assert isinstance(opencode, FakeOpenCodeAdapter)
    assert isinstance(opencode.strategy, expected)


@pytest.mark.unit
def test_factory_returns_all_harnesses_by_default() -> None:
    adapters = criar_adapters(
        EnvironmentKind.LINUX,
        registry=fake_registry(),
    )

    assert [adapter.name for adapter in adapters] == [
        "opencode-fake",
        "copilot-fake",
    ]


@pytest.mark.unit
def test_factory_filters_by_selection_keeping_registry_order() -> None:
    adapters = criar_adapters(
        EnvironmentKind.WSL,
        ["copilot", "opencode"],
        registry=fake_registry(),
    )

    assert [adapter.name for adapter in adapters] == [
        "opencode-fake",
        "copilot-fake",
    ]


@pytest.mark.unit
def test_factory_selection_rejects_unknown_harness() -> None:
    with pytest.raises(ValueError, match="harness desconhecido"):
        criar_adapters(
            EnvironmentKind.LINUX,
            ["opencode", "inexistente"],
            registry=fake_registry(),
        )


@pytest.mark.unit
def test_selecionar_harnesses_exposes_skip_variable() -> None:
    definitions = selecionar_harnesses(registry=fake_registry())

    assert [definition.skip_variable for definition in definitions] == [
        "OPENCODE_SKIP_OPENCODE_ADAPTER",
        "OPENCODE_SKIP_COPILOT_ADAPTER",
    ]


@pytest.mark.unit
def test_selecionar_harnesses_empty_selection_returns_all() -> None:
    definitions = selecionar_harnesses([], registry=fake_registry())

    assert [definition.name for definition in definitions] == [
        "opencode",
        "copilot",
    ]


@pytest.mark.unit
def test_fake_adapter_does_not_receive_environment() -> None:
    adapters = criar_adapters(
        EnvironmentKind.WINDOWS,
        ["copilot"],
        registry=fake_registry(),
    )

    assert isinstance(adapters[0], FakeCopilotAdapter)
