"""Validação do spawn dinâmico de subagentes com modelo por chamada.

Exercita o caminho real de uso (headless): um agente primário criado por
`opencode run` chama a tool `task` — estendida pelo plugin
`opencode-task-model` — passando `model` explícito em duas chamadas e
nenhum argumento na terceira. O modelo efetivo de cada child é verificado
no storage local de sessões do OpenCode (coluna `model` da tabela
`session`). O consumo dos providers acontece dentro do OpenCode: o teste
nunca chama API de provider diretamente nem cria sessão child fora da
tool `task`.

Como o plugin é carregado: o config global do OpenCode
(`~/.config/opencode/opencode.json`, symlink para
`harness-conf/opencode.json` nas instalações POSIX feitas pelo bootstrap)
já declara o plugin pinado, então o subprocess herda o ambiente real do
usuário sem qualquer alteração global. O teste não usa o
`integration_context` padrão porque ele zera `config["plugin"]`.

Diretório de trabalho do run: o OpenCode desta máquina recusa cwd/projeto
sob `/tmp` ("Failed to change directory"), e o fixture autouse
`isolated_home` aponta HOME para um tmp. O run usa um scratch único sob o
HOME real, removido ao final.
"""

from __future__ import annotations

import json
import os
import queue
import shutil
import sqlite3
import subprocess
import threading
import time
import uuid
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

# Modelos da validação (provider já configurado no ambiente do usuário).
MODEL_FLASH = "zai-coding-plan/glm-5.3-flash"
MODEL_PRO = "zai-coding-plan/glm-5.3"
PLUGIN_NAME = "opencode-task-model"

# Um run = agente primário + 3 spawns sequenciais (2 com `model` explícito,
# 1 sem). Ensaio manual mediu ~71 s de duração total. Os limites abaixo são
# redes de segurança ancoradas em sinal (saída do processo), não critério de
# desempenho: sem nenhum byte novo em 300 s o processo está travado; 900 s
# no total dá ~12x a duração observada antes de desistir.
OPENCODE_IDLE_TIMEOUT_S = 300
OPENCODE_TOTAL_TIMEOUT_S = 900

# Granularidade da checagem dos limites acima (não é limite próprio): o
# loop consulta a fila de saída com esse passo e avalia idle/total a cada
# retorno. Sentinel marca EOF na fila (str de linha | sentinel | None).
_EOF_SENTINEL = object()
_WATCHDOG_POLL_S = 1.0

# Avaliado na coleta do módulo, antes de o fixture autouse `isolated_home`
# trocar HOME para um diretório temporário.
_REAL_HOME = Path.home()

PROMPT = (
    "Use a tool task exatamente 3 vezes, em sequência, e nenhuma outra tool. "
    "Chamada 1: subagent_type=general, description='spawn flash', "
    f"model='{MODEL_FLASH}', prompt='Responda apenas com o texto: PONG-FLASH'. "
    "Chamada 2: subagent_type=general, description='spawn pro', "
    f"model='{MODEL_PRO}', prompt='Responda apenas com o texto: PONG-PRO'. "
    "Chamada 3: subagent_type=general, description='spawn nativo', SEM o "
    "argumento model, prompt='Responda apenas com o texto: PONG-NATIVE'. "
    "Ao terminar, responda apenas: DONE."
)


def _fail(motivo: str) -> None:
    pytest.fail(motivo, pytrace=False)


def test_watchdog_mata_processo_silencioso(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Processo vivo e sem saída dispara o limite de inatividade.

    Reprodução do defeito: o loop antigo avaliava os limites só depois
    de `readline()` retornar, então um `opencode run` vivo e silencioso
    pendurava o teste. Aqui o processo falso (`sleep`) não escreve nada;
    o watchdog precisa matá-lo pelo limite de idle encurtado.
    """

    monkeypatch.setattr(f"{__name__}.OPENCODE_IDLE_TIMEOUT_S", 1)
    monkeypatch.setattr(f"{__name__}.OPENCODE_TOTAL_TIMEOUT_S", 30)
    real_popen = subprocess.Popen

    def fake_popen(command: list[str], **kwargs: object) -> subprocess.Popen:
        del command
        return real_popen(
            ["sleep", "15"],
            cwd=str(tmp_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

    monkeypatch.setattr(f"{__name__}.subprocess.Popen", fake_popen)

    start = time.monotonic()
    with pytest.raises(pytest.fail.Exception, match="sem saída"):
        _run_opencode("opencode", tmp_path, "watchdog-fake")
    assert time.monotonic() - start < 10, (
        "Watchdog demorou mais que o idle encurtado: o limite de "
        "inatividade não disparou com processo vivo e silencioso."
    )


def _require_opencode_binary() -> str:
    binary = shutil.which("opencode")
    if not binary:
        _fail(
            "Binário `opencode` não encontrado no PATH. Instale o OpenCode "
            "(~/.opencode/bin) ou ajuste o PATH e execute novamente."
        )
    return binary


def _require_pinned_plugin(repo_root: Path) -> str:
    config_path = repo_root / "harness-conf" / "opencode.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"Config canônica ilegível ({config_path}): {error}")
    entries = [
        entry
        for entry in config.get("plugin", [])
        if isinstance(entry, str) and entry.split("@")[0] == PLUGIN_NAME
    ]
    if not entries:
        _fail(
            f"Plugin {PLUGIN_NAME} ausente em {config_path}. Execute o ciclo "
            "de aplicação do plugin antes desta validação."
        )
    if "@" not in entries[0]:
        _fail(
            f"Plugin {PLUGIN_NAME} sem pin exato em {config_path}: "
            f"'{entries[0]}'. Corrija o pin antes desta validação."
        )
    return entries[0]


def _require_global_config_with_plugin(pin: str) -> Path:
    global_config = _REAL_HOME / ".config" / "opencode" / "opencode.json"
    try:
        config = json.loads(global_config.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(
            f"Config global do OpenCode ilegível ({global_config}): {error}. "
            "Rode o bootstrap do repo: "
            "./scripts/bootstrap_repo/configurar-repo.sh --yes"
        )
    if pin not in config.get("plugin", []):
        _fail(
            f"Config global ({global_config}) não declara '{pin}'. Rode o "
            "bootstrap do repo para materializar a config canônica: "
            "./scripts/bootstrap_repo/configurar-repo.sh --yes"
        )
    return global_config


def _require_zai_provider() -> None:
    auth_path = _REAL_HOME / ".local" / "share" / "opencode" / "auth.json"
    try:
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(
            f"Credenciais do OpenCode ilegíveis ({auth_path}): {error}. "
            "Configure o provider zai-coding-plan antes desta validação."
        )
    if MODEL_FLASH.split("/")[0] not in auth:
        _fail(
            f"Provider '{MODEL_FLASH.split('/')[0]}' sem credenciais em "
            f"{auth_path}. Faça login do provider (opencode auth login ou "
            "equivalente do plano z.ai) e execute novamente."
        )


def _pump_stdout(
    process: subprocess.Popen, output_queue: "queue.Queue[object]"
) -> None:
    """Move linhas do stdout para a fila; sinaliza EOF com o sentinel."""

    assert process.stdout is not None
    try:
        while True:
            line = process.stdout.readline()
            if not line:
                break
            output_queue.put(line)
    finally:
        output_queue.put(_EOF_SENTINEL)


def _fail_timeout(chunks: list[str], limite_s: int, motivo: str) -> None:
    ultima_saida = "".join(chunks)[-2000:]
    pytest.fail(
        f"`opencode run` {motivo} ({limite_s}s). Última saída: "
        f"{ultima_saida}",
        pytrace=False,
    )


def _run_opencode(binary: str, scratch: Path, title: str) -> subprocess.CompletedProcess:
    """Executa `opencode run` com rede de segurança de inatividade + total.

    A leitura do stdout roda em thread dedicada alimentando uma fila: os
    limites são avaliados por `queue.get(timeout=...)`, então um processo
    vivo e silencioso dispara o watchdog em vez de pendurar o teste.
    """

    env = dict(os.environ)
    env["HOME"] = str(_REAL_HOME)
    env["XDG_CONFIG_HOME"] = str(_REAL_HOME / ".config")
    env["USERPROFILE"] = str(_REAL_HOME)
    command = [
        binary,
        "run",
        "--model",
        MODEL_FLASH,
        "--title",
        title,
        "--dir",
        str(scratch),
        PROMPT,
    ]
    process = subprocess.Popen(
        command,
        cwd=scratch,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    output_queue: "queue.Queue[object]" = queue.Queue()
    reader = threading.Thread(
        target=_pump_stdout, args=(process, output_queue), daemon=True
    )
    reader.start()

    start = time.monotonic()
    last_output = start
    chunks: list[str] = []
    try:
        while True:
            try:
                item = output_queue.get(timeout=_WATCHDOG_POLL_S)
            except queue.Empty:
                item = None
            now = time.monotonic()
            if item is _EOF_SENTINEL:
                break
            if item:
                chunks.append(str(item))
                last_output = now
            if now - last_output > OPENCODE_IDLE_TIMEOUT_S:
                process.kill()
                _fail_timeout(chunks, OPENCODE_IDLE_TIMEOUT_S, "sem saída")
            if now - start > OPENCODE_TOTAL_TIMEOUT_S:
                process.kill()
                _fail_timeout(
                    chunks, OPENCODE_TOTAL_TIMEOUT_S, "excedeu o total"
                )
    finally:
        process.wait(timeout=30)
        reader.join(timeout=30)
    return subprocess.CompletedProcess(
        command, process.returncode, stdout="".join(chunks)
    )


def _open_session_db() -> sqlite3.Connection:
    data_root = Path(
        os.environ.get("XDG_DATA_HOME") or (_REAL_HOME / ".local" / "share")
    )
    db_path = data_root / "opencode" / "opencode.db"
    if not db_path.is_file():
        _fail(
            f"Storage de sessões do OpenCode não encontrado ({db_path}). "
            "Confirme a instalação do OpenCode no ambiente do usuário."
        )
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def _session_rows(
    cursor: sqlite3.Cursor, scratch: Path, since_ms: int
) -> list[dict]:
    rows = cursor.execute(
        "SELECT id, parent_id, agent, model, cost, time_created, time_updated "
        "FROM session WHERE directory LIKE ? AND time_created >= ? "
        "ORDER BY time_created",
        (f"{scratch}%", since_ms),
    ).fetchall()
    sessions = []
    for row in rows:
        model = json.loads(row[3]) if row[3] else None
        sessions.append(
            {
                "id": row[0],
                "parent_id": row[1],
                "agent": row[2],
                "provider": model.get("providerID") if model else None,
                "model": model.get("id") if model else None,
                "cost": row[4],
                "created": row[5],
                "updated": row[6],
            }
        )
    return sessions


def _child_text(cursor: sqlite3.Cursor, session_id: str) -> str:
    rows = cursor.execute(
        "SELECT data FROM part WHERE session_id = ?", (session_id,)
    ).fetchall()
    texts = [
        data.get("text", "")
        for (raw,) in rows
        if isinstance(data := json.loads(raw), dict) and data.get("type") == "text"
    ]
    return "\n".join(texts)


def test_spawn_dinamico_com_modelos_distintos_via_task(repo_root: Path) -> None:
    pin = _require_pinned_plugin(repo_root)
    _require_global_config_with_plugin(pin)
    _require_zai_provider()
    binary = _require_opencode_binary()

    scratch = (
        _REAL_HOME
        / ".local"
        / "state"
        / "opencode-task-model-it"
        / uuid.uuid4().hex[:8]
    )
    scratch.mkdir(parents=True)
    title = f"it-task-model-{uuid.uuid4().hex[:8]}"
    try:
        since_ms = int(time.time() * 1000)
        result = _run_opencode(binary, scratch, title)
        if result.returncode != 0:
            _fail(
                f"`opencode run` terminou com código {result.returncode}. "
                f"Saída final: {result.stdout[-2000:]}"
            )

        connection = _open_session_db()
        try:
            cursor = connection.cursor()
            sessions = _session_rows(cursor, scratch, since_ms)
        finally:
            connection.close()
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    parents = [s for s in sessions if s["parent_id"] is None]
    children = [s for s in sessions if s["parent_id"] is not None]
    if len(parents) != 1:
        _fail(
            f"Esperava 1 sessão pai do run '{title}', encontrei "
            f"{len(parents)}: {[s['id'] for s in parents]}."
        )
    parent = parents[0]
    if len(children) != 3:
        _fail(
            "Esperava 3 children spawnados via tool task, encontrei "
            f"{len(children)}: {children}. O plugin está carregado e a tool "
            "`task` aceitou o argumento `model`?"
        )

    flash_child, pro_child, native_child = children
    expected = [
        (flash_child, "glm-5.3-flash", "PONG-FLASH", "model explícito flash"),
        (pro_child, "glm-5.3", "PONG-PRO", "model explícito glm-5.3"),
        (native_child, "glm-5.3-flash", "PONG-NATIVE", "sem model (herda do pai)"),
    ]
    for child, model_id, token, label in expected:
        assert (child["provider"], child["model"]) == (
            MODEL_FLASH.split("/")[0],
            model_id,
        ), (
            f"Spawn {label}: modelo efetivo divergente. "
            f"Esperado {model_id}, encontrado "
            f"{child['provider']}/{child['model']} (sessão {child['id']}). "
            "O plugin opencode-task-model está ativo no run?"
        )
        connection = _open_session_db()
        try:
            text = _child_text(connection.cursor(), child["id"])
        finally:
            connection.close()
        assert token in text, (
            f"Spawn {label} (sessão {child['id']}) não devolveu o token "
            f"'{token}'. Resposta: {text[:500]}"
        )

    assert (parent["provider"], parent["model"]) == (
        MODEL_FLASH.split("/")[0],
        "glm-5.3-flash",
    ), f"Sessão pai com modelo inesperado: {parent}"

    duration_s = (max(s["updated"] for s in sessions) - since_ms) / 1000
    total_cost = sum(s["cost"] for s in sessions)
    print(
        "\n[evidência] title={title}\n"
        "[evidência] pai: {pid} {pprovider}/{pmodel}\n"
        "[evidência] flash: {fid} -> {fmodel}\n"
        "[evidência] pro: {prid} -> {prmodel}\n"
        "[evidência] nativo (sem model): {nid} -> {nmodel} (herdado do pai)\n"
        "[evidência] duração={duration:.0f}s custo_total={cost:.4f}".format(
            title=title,
            pid=parent["id"],
            pprovider=parent["provider"],
            pmodel=parent["model"],
            fid=flash_child["id"],
            fmodel=flash_child["model"],
            prid=pro_child["id"],
            prmodel=pro_child["model"],
            nid=native_child["id"],
            nmodel=native_child["model"],
            duration=duration_s,
            cost=total_cost,
        )
    )
