"""Deteccao sem efeitos colaterais das dependencias do bootstrap."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path
import re
import shutil

from opencode_config.lib.environment import EnvironmentKind, detect_environment
from opencode_config.lib.process import CommandResult, run_command

from .registry import DEPENDENCY_REGISTRY, DependencySpec


class DependencyStatus(str, Enum):
    """Estados possiveis de uma dependencia detectada."""

    PRESENT = "present"
    MISSING = "missing"
    OUTDATED = "outdated"
    ERROR = "error"


@dataclass(frozen=True)
class DependencyDetection:
    """Resultado observavel da deteccao de uma dependencia."""

    spec: DependencySpec
    status: DependencyStatus
    version: str | None
    path: Path | None
    install_method: str
    error: str = ""

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def required(self) -> bool:
        return self.spec.required


Runner = Callable[..., CommandResult]


def _environment_for(
    environment: EnvironmentKind | None,
) -> EnvironmentKind:
    return detect_environment() if environment is None else environment


def _path_value(environment: Mapping[str, str]) -> str | None:
    """Retorna PATH sem depender da capitalização usada pelo sistema."""

    return next(
        (
            value
            for name, value in environment.items()
            if name.casefold() == "path"
        ),
        None,
    )


def _command_environment(
    environment: Mapping[str, str] | None,
) -> tuple[Mapping[str, str] | None, str | None]:
    if environment is None:
        return None, _path_value(os.environ)

    merged = dict(os.environ)
    for name, value in environment.items():
        existing_name = next(
            (
                current_name
                for current_name in merged
                if current_name.casefold() == name.casefold()
            ),
            None,
        )
        merged[existing_name or name] = value
    return merged, _path_value(merged)


def _extract_version(output: str, pattern: str) -> str | None:
    match = re.search(pattern, output)
    if match is None:
        return None
    return match.groupdict().get("version", match.group(0))


def _version_parts(version: str | None) -> tuple[int, ...] | None:
    if not version:
        return None
    numbers = re.findall(r"\d+", version)
    return tuple(int(number) for number in numbers) or None


def _is_below_minimum(
    version: str | None,
    minimum: tuple[int, ...] | None,
) -> bool:
    if minimum is None:
        return False
    current = _version_parts(version)
    if current is None:
        return False
    width = max(len(current), len(minimum))
    return current + (0,) * (width - len(current)) < (
        minimum + (0,) * (width - len(minimum))
    )


def _missing_result(
    spec: DependencySpec,
    environment: EnvironmentKind,
) -> DependencyDetection:
    return DependencyDetection(
        spec=spec,
        status=DependencyStatus.MISSING,
        version=None,
        path=None,
        install_method=spec.install_method_for(environment),
    )


def detect_dependency(
    spec: DependencySpec,
    environment: EnvironmentKind,
    *,
    env: Mapping[str, str] | None = None,
    runner: Runner | None = None,
) -> DependencyDetection:
    """Detecta uma dependencia sem instalar ou alterar o ambiente."""

    command_environment, path_environment = _command_environment(env)
    executable: str | None = None
    for command in spec.commands_for(environment):
        executable = shutil.which(command, path=path_environment)
        if executable is not None:
            break

    if executable is None:
        return _missing_result(spec, environment)

    execute = run_command if runner is None else runner
    result = execute(
        [executable, *spec.version_args],
        env=command_environment,
    )
    if not result.succeeded:
        return DependencyDetection(
            spec=spec,
            status=DependencyStatus.ERROR,
            version=None,
            path=Path(executable),
            install_method=spec.install_method_for(environment),
            error=result.stderr or result.stdout or "comando falhou",
        )

    version = _extract_version(
        f"{result.stdout}\n{result.stderr}",
        spec.version_pattern,
    )
    status = (
        DependencyStatus.OUTDATED
        if _is_below_minimum(version, spec.minimum_version)
        else DependencyStatus.PRESENT
    )
    return DependencyDetection(
        spec=spec,
        status=status,
        version=version,
        path=Path(executable),
        install_method=spec.install_method_for(environment),
    )


def detect_dependencies(
    environment: EnvironmentKind | None = None,
    *,
    specs: Sequence[DependencySpec] = DEPENDENCY_REGISTRY,
    env: Mapping[str, str] | None = None,
    runner: Runner | None = None,
) -> tuple[DependencyDetection, ...]:
    """Percorre um registro declarativo e retorna o estado de cada entrada."""

    selected_environment = _environment_for(environment)
    return tuple(
        detect_dependency(
            spec,
            selected_environment,
            env=env,
            runner=runner,
        )
        for spec in specs
        if (
            spec.supported_environments is None
            or selected_environment in spec.supported_environments
        )
    )
