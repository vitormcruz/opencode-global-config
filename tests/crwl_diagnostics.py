from collections.abc import Callable, Mapping, Sequence
import ctypes
import os
import shlex
import subprocess


MEMORY_PRESSURE_THRESHOLD_PERCENT = 95.0
MAX_PARTIAL_OUTPUT_LENGTH = 4000


class CrwlTimeoutError(TimeoutError):
    """Timeout do crwl com diagnóstico legível para o agente e o humano."""


def run_crwl(
    executable: str,
    arguments: Sequence[str],
    *,
    timeout_seconds: float,
    environment: Mapping[str, str],
    run_process: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    memory_usage_reader: Callable[[], float | None] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [executable, "crawl", *arguments]
    try:
        return run_process(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            env=environment,
        )
    except subprocess.TimeoutExpired as error:
        memory_usage = (
            get_memory_usage_percent()
            if memory_usage_reader is None
            else memory_usage_reader()
        )
        message = format_timeout_message(
            command=command,
            timeout_seconds=timeout_seconds,
            memory_usage_percent=memory_usage,
            stdout=error.stdout,
            stderr=error.stderr,
        )
        raise CrwlTimeoutError(message) from error


def format_timeout_message(
    *,
    command: Sequence[str],
    timeout_seconds: float,
    memory_usage_percent: float | None,
    stdout: str | bytes | None,
    stderr: str | bytes | None,
) -> str:
    deep_crawl = _uses_deep_crawl(command)
    memory_pressure = (
        deep_crawl
        and memory_usage_percent is not None
        and memory_usage_percent >= MEMORY_PRESSURE_THRESHOLD_PERCENT
    )

    if memory_pressure:
        lines = [
            "ATENÇÃO: o Crawl4AI não conseguiu concluir o deep-crawl "
            "porque o computador estava sob forte pressão de memória.",
            "",
            f"O teste aguardou {_format_timeout(timeout_seconds)} segundos e expirou.",
            f"Memória utilizada no momento: {_format_memory(memory_usage_percent)}.",
            "A memória atingiu ou ultrapassou o limite de 95% usado pelo "
            "Crawl4AI para controlar novas páginas.",
            "",
            "AÇÃO PARA O AGENTE: avise o humano que o teste foi impedido "
            "pela memória disponível no computador. Não remova o teste, "
            "não use skip e não aumente o timeout sem autorização.",
            "",
            "Detalhe técnico: MemoryAdaptiveDispatcher.",
        ]
    else:
        lines = [
            "ATENÇÃO: o teste do Crawl4AI excedeu o tempo limite, mas não "
            "há evidência suficiente para atribuir o problema à memória "
            "do computador.",
            "",
            f"O teste aguardou {_format_timeout(timeout_seconds)} segundos e expirou.",
            f"Memória utilizada no momento: {_format_memory(memory_usage_percent)}.",
            "",
            "AÇÃO PARA O AGENTE: avise o humano sobre o timeout e preserve "
            "a falha para investigação.",
        ]

    lines.extend(
        [
            "",
            f"Comando executado: {shlex.join(command)}",
        ]
    )
    _append_partial_output(lines, "stdout", stdout)
    _append_partial_output(lines, "stderr", stderr)
    return "\n".join(lines)


def get_memory_usage_percent() -> float | None:
    if os.name == "nt":
        return _get_windows_memory_usage_percent()

    linux_memory = _get_linux_memory_usage_percent()
    if linux_memory is not None:
        return linux_memory
    return _get_sysconf_memory_usage_percent()


def _uses_deep_crawl(arguments: Sequence[str]) -> bool:
    return any(
        argument == "--deep-crawl" or argument.startswith("--deep-crawl=")
        for argument in arguments
    )


def _append_partial_output(
    lines: list[str],
    stream_name: str,
    output: str | bytes | None,
) -> None:
    if output is None:
        return

    text = _as_text(output)
    if not text:
        return

    lines.extend(
        [
            "",
            f"Saída parcial ({stream_name}):",
            _truncate_output(text),
        ]
    )


def _as_text(output: str | bytes) -> str:
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output


def _truncate_output(output: str) -> str:
    if len(output) <= MAX_PARTIAL_OUTPUT_LENGTH:
        return output
    return (
        output[:MAX_PARTIAL_OUTPUT_LENGTH]
        + "\n[saída parcial truncada]"
    )


def _format_timeout(timeout_seconds: float) -> str:
    return f"{timeout_seconds:g}"


def _format_memory(memory_usage_percent: float | None) -> str:
    if memory_usage_percent is None:
        return "não foi possível medir"
    return f"{memory_usage_percent:.2f}%".replace(".", ",")


class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def _get_windows_memory_usage_percent() -> float | None:
    status = _MemoryStatusEx()
    status.dwLength = ctypes.sizeof(_MemoryStatusEx)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None
    if status.ullTotalPhys == 0:
        return None
    return (
        (status.ullTotalPhys - status.ullAvailPhys)
        / status.ullTotalPhys
        * 100
    )


def _get_linux_memory_usage_percent() -> float | None:
    try:
        with open("/proc/meminfo", encoding="ascii") as meminfo:
            values = {
                line.split(":", 1)[0]: float(line.split(":", 1)[1].split()[0])
                for line in meminfo
                if ":" in line and line.split(":", 1)[1].split()
            }
    except (OSError, ValueError):
        return None

    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    if total is None or available is None or total <= 0:
        return None
    return (total - available) / total * 100


def _get_sysconf_memory_usage_percent() -> float | None:
    try:
        total_pages = os.sysconf("SC_PHYS_PAGES")
        available_pages = os.sysconf("SC_AVPHYS_PAGES")
    except (OSError, ValueError):
        return None
    if total_pages <= 0:
        return None
    return (total_pages - available_pages) / total_pages * 100
