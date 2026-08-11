"""Selecao interativa e orquestracao do bootstrap."""

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from io import TextIOBase
from pathlib import Path
import sys

from opencode_config.lib.environment import EnvironmentKind, detect_environment
from opencode_config.lib.paths import resolve_user_space_paths

from .detect import DependencyDetection, DependencyStatus, detect_dependencies
from .installers import (
    InstallContext,
    InstallResult,
    install_dependencies,
    is_pytest_environment_ready,
)


class InteractiveError(RuntimeError):
    """Indica que a selecao interativa nao pode prosseguir."""


@dataclass(frozen=True)
class BootstrapResult:
    """Resultado completo da deteccao, selecao e instalacao."""

    detections: tuple[DependencyDetection, ...]
    selected: tuple[str, ...]
    install_results: tuple[InstallResult, ...]
    manual: tuple[str, ...]


Detector = Callable[..., tuple[DependencyDetection, ...]]
Installer = Callable[
    [Iterable[str], InstallContext],
    tuple[InstallResult, ...],
]


def _needs_install(detection: DependencyDetection) -> bool:
    return detection.status in {
        DependencyStatus.MISSING,
        DependencyStatus.OUTDATED,
        DependencyStatus.ERROR,
    }


def render_detection_table(
    detections: Sequence[DependencyDetection],
) -> str:
    """Renderiza a tabela sem depender de biblioteca externa."""

    lines = ["nome | status | versao | metodo"]
    lines.append("-----|--------|---------|-------")
    for detection in detections:
        version = detection.version or "-"
        lines.append(
            f"{detection.name} | {detection.status.value} | "
            f"{version} | {detection.install_method}"
        )
    return "\n".join(lines) + "\n"


def _is_tty(stream: TextIOBase) -> bool:
    return bool(getattr(stream, "isatty", lambda: False)())


def _select_missing(
    missing: Sequence[DependencyDetection],
    *,
    assume_yes: bool,
    input_stream: TextIOBase,
    output: TextIOBase,
) -> tuple[str, ...]:
    if not missing:
        return ()
    if assume_yes:
        return tuple(detection.name for detection in missing)

    if not _is_tty(input_stream) or not _is_tty(output):
        raise InteractiveError(
            "Sem TTY para selecao; execute novamente com --yes"
        )

    selected: list[str] = []
    for detection in missing:
        default = detection.required
        suffix = "[Y/n]" if default else "[y/N]"
        while True:
            output.write(f"Instalar {detection.name}? {suffix} ")
            answer = input_stream.readline().strip().lower()
            if not answer:
                accepted = default
                break
            if answer in {"y", "yes"}:
                accepted = True
                break
            if answer in {"n", "no"}:
                accepted = False
                break
            output.write("Responda y ou n.\n")
        if accepted:
            selected.append(detection.name)
    return tuple(selected)


def _manual_block(
    detections: Sequence[DependencyDetection],
    output: TextIOBase,
    errors: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    pending = tuple(detection.name for detection in detections)
    if not pending:
        return ()

    output.write("\nComandos manuais pendentes:\n```text\n")
    for detection in detections:
        output.write(f"# {detection.name}\n{detection.install_method}\n")
        detail = (errors or {}).get(detection.name) or detection.error
        if detail:
            output.write(f"erro: {detail}\n")
            guidance = _tls_guidance(detail)
            if guidance:
                output.write(f"{guidance}\n")
    output.write("```\n")
    return pending


def _tls_guidance(detail: str) -> str:
    """Orienta o agente sem desativar TLS ou inventar CA corporativa."""

    normalized = detail.casefold()
    indicators = (
        "certificate",
        "cert chain",
        "self-signed",
        "ssl",
        "tls",
        "x509",
    )
    if not any(indicator in normalized for indicator in indicators):
        return ""

    return (
        "orientacao para agente: converse com o humano e confirme CA PEM "
        "corporativa aprovada ou mirror oficial do ambiente; depois, use "
        "variaveis temporarias da sessao, como NODE_EXTRA_CA_CERTS, "
        "SSL_CERT_FILE e REQUESTS_CA_BUNDLE. Nunca use strict-ssl=false, "
        "NODE_TLS_REJECT_UNAUTHORIZED=0, ignore-certificate-errors ou grave "
        "CA/URL corporativa no repositorio."
    )


def _docling_model_guidance(
    environment: EnvironmentKind,
    output: TextIOBase,
) -> None:
    if environment is EnvironmentKind.WINDOWS:
        command = (
            'docling-tools models download --output-dir '
            '"$env:USERPROFILE\\.cache\\docling\\models"'
        )
    else:
        command = (
            'docling-tools models download --output-dir '
            '"$HOME/.cache/docling/models"'
        )

    output.write(
        "\nOrientacao Docling:\n"
        "O bootstrap instalou o pacote, mas nao baixa modelos automaticamente.\n"
        "Para provisionar modelos locais, em sessao aprovada pelo humano, execute:\n"
        f"  {command}\n"
        "Depois, opencode-doc-extract usa somente cache local e nao baixa "
        "modelos.\n"
        "Se a rede exigir CA ou mirror corporativo, confirme-os com o humano; "
        "nao desative TLS.\n"
    )


def _default_context(
    environment: EnvironmentKind,
    repo_root: Path | None,
) -> InstallContext:
    root = Path.cwd() if repo_root is None else repo_root
    return InstallContext(
        environment=environment,
        paths=resolve_user_space_paths(environment),
        repo_root=root,
    )


def _ensure_pytest_detection(
    detections: Sequence[DependencyDetection],
    context: InstallContext,
) -> tuple[DependencyDetection, ...]:
    if not any(detection.name == "pytest" for detection in detections):
        return tuple(detections)
    if is_pytest_environment_ready(context):
        return tuple(
            replace(
                detection,
                status=DependencyStatus.PRESENT,
                error="",
            )
            if detection.name == "pytest"
            else detection
            for detection in detections
        )
    return tuple(
        replace(
            detection,
            status=DependencyStatus.MISSING,
            version=None,
            path=None,
        )
        if detection.name == "pytest"
        and detection.status is DependencyStatus.PRESENT
        else detection
        for detection in detections
    )


def run_bootstrap(
    *,
    context: InstallContext | None = None,
    repo_root: Path | None = None,
    environment: EnvironmentKind | None = None,
    detections: Sequence[DependencyDetection] | None = None,
    detector: Detector = detect_dependencies,
    installer: Installer = install_dependencies,
    assume_yes: bool = False,
    check_only: bool = False,
    quiet: bool = False,
    input_stream: TextIOBase | None = None,
    output: TextIOBase | None = None,
) -> BootstrapResult:
    """Executa os passos AD-10 sem instalar em modo ``check_only``."""

    input_stream = sys.stdin if input_stream is None else input_stream
    output = sys.stdout if output is None else output
    selected_environment = (
        detect_environment() if environment is None else environment
    )
    active_context = context or _default_context(
        selected_environment,
        repo_root,
    )
    found = tuple(
        detections
        if detections is not None
        else detector(
            selected_environment,
            env=active_context.current_environment,
        )
    )
    found = _ensure_pytest_detection(found, active_context)
    if not quiet:
        output.write(render_detection_table(found))

    missing = tuple(filter(_needs_install, found))
    if check_only:
        manual = _manual_block(missing, output)
        return BootstrapResult(found, (), (), manual)

    selected = _select_missing(
        missing,
        assume_yes=assume_yes,
        input_stream=input_stream,
        output=output,
    )
    for name in selected:
        output.write(f"Instalando {name}...\n")
        output.flush()
    install_results = tuple(installer(selected, active_context))
    installation_errors = {
        result.name: result.error
        for result in install_results
        if result.error
    }
    successful = {
        result.name for result in install_results if result.success
    }
    pending = tuple(
        detection
        for detection in missing
        if detection.name not in successful
    )
    manual = _manual_block(
        pending,
        output,
        errors=installation_errors,
    )
    docling_available = any(
        detection.name == "docling"
        and detection.status is DependencyStatus.PRESENT
        for detection in found
    ) or any(
        result.name == "docling" and result.success
        for result in install_results
    )
    if docling_available:
        _docling_model_guidance(selected_environment, output)
    return BootstrapResult(found, selected, install_results, manual)
