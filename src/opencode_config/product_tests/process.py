"""Execucao observavel de ferramentas externas das suites de produto."""

from __future__ import annotations

import os
import queue
import subprocess
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

Progress = Callable[[str], None]


@dataclass(frozen=True)
class ProcessResult:
    """Resultado de um processo, incluindo falhas de inicializacao."""

    command: tuple[str, ...]
    returncode: int | None
    stdout: str
    stderr: str
    error: str = ""

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0 and not self.error


Runner = Callable[..., ProcessResult]


def _read_stream(
    stream: object,
    name: str,
    events: queue.Queue[tuple[str, str | None]],
) -> None:
    try:
        for line in stream:  # type: ignore[union-attr]
            events.put((name, line))
    finally:
        events.put((name, None))


def run_process(
    command: Sequence[str | os.PathLike[str]],
    *,
    cwd: Path,
    progress: Progress,
    env: Mapping[str, str] | None = None,
    label: str | None = None,
) -> ProcessResult:
    """Executa um processo com streams drenados e heartbeat de progresso.

    A operacao nao usa timeout de relogio como criterio de sucesso. Enquanto o
    processo estiver vivo, a fila de streams e consultada e o chamador recebe
    heartbeats, evitando uma espera opaca sem sinal de vida.
    """

    arguments = tuple(os.fspath(argument) for argument in command)
    process_label = label or arguments[0]
    try:
        process = subprocess.Popen(
            arguments,
            cwd=cwd,
            env=None if env is None else dict(env),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except OSError as error:
        return ProcessResult(arguments, None, "", "", str(error))

    events: queue.Queue[tuple[str, str | None]] = queue.Queue()
    threads = [
        threading.Thread(
            target=_read_stream,
            args=(stream, name, events),
            daemon=True,
        )
        for stream, name in (
            (process.stdout, "stdout"),
            (process.stderr, "stderr"),
        )
    ]
    for thread in threads:
        thread.start()

    output: list[str] = []
    errors: list[str] = []
    closed_streams = 0
    while closed_streams < len(threads):
        try:
            stream_name, line = events.get(timeout=1)
        except queue.Empty:
            if process.poll() is None:
                progress(f"{process_label}: aguardando conclusao")
            continue

        if line is None:
            closed_streams += 1
            continue
        if stream_name == "stdout":
            output.append(line)
        else:
            errors.append(line)

    return ProcessResult(
        arguments,
        process.wait(),
        "".join(output),
        "".join(errors),
    )


def is_transient_network_failure(result: ProcessResult) -> bool:
    """Identifica sinais conhecidos de falha transitoria de rede."""

    text = f"{result.stdout}\n{result.stderr}".casefold()
    indicators = (
        "temporary failure",
        "name resolution",
        "connection reset",
        "connection refused",
        "connection timed out",
        "network is unreachable",
        "tls handshake",
        "certificate verify failed",
        "could not resolve",
        "timed out",
    )
    return any(indicator in text for indicator in indicators)


def run_with_network_retry(
    command: Sequence[str | os.PathLike[str]],
    *,
    cwd: Path,
    progress: Progress,
    runner: Runner = run_process,
    env: Mapping[str, str] | None = None,
    label: str | None = None,
    attempts: int = 3,
) -> ProcessResult:
    """Executa comando de rede no maximo tres vezes quando a falha e transitoria."""

    if attempts < 1:
        raise ValueError("attempts deve ser positivo")

    result = runner(
        command,
        cwd=cwd,
        progress=progress,
        env=env,
        label=label,
    )
    for attempt in range(2, attempts + 1):
        if result.succeeded or not is_transient_network_failure(result):
            break
        progress(f"{label or command[0]}: nova tentativa {attempt}/{attempts}")
        result = runner(
            command,
            cwd=cwd,
            progress=progress,
            env=env,
            label=label,
        )
    return result
