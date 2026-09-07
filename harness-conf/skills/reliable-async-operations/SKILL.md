---
name: reliable-async-operations
description: >
  Padrão obrigatório para qualquer código que dependa de uma operação de
  duração desconhecida ou variável — processo externo, chamada de rede/HTTP,
  promise/async-await, fila/job em background, lock, polling, WebSocket/stream
  — em qualquer linguagem, backend ou frontend. Corrige a causa raiz de
  agentes escreverem código que fica bloqueado esperando sem sinal de
  progresso, ou que usa timeout de relógio com número mágico. Não é
  específico de subprocess: aplica-se a qualquer chamada assíncrona.
  Use quando: escrever ou revisar código com subprocess/child_process/
  ProcessBuilder/exec/spawn; escrever ou revisar `fetch`/HTTP client/API
  call; escrever `async`/`await`/Promise/asyncio sem timeout ou cancelamento;
  escrever polling, retry, backoff, lock, mutex, semáforo, fila/job
  assíncrono, WebSocket ou stream; investigar operação que trava, não
  responde ou não emite progresso; decidir timeout para qualquer chamada
  assíncrona. Triggers: "processo externo", "subprocess", "child_process",
  "ProcessBuilder", "execSync", "waitFor", "spawn", "async", "await",
  "Promise", "asyncio", "fetch sem timeout", "AbortController", "race
  condition", "polling", "retry", "backoff", "fila assíncrona", "job em
  background", "lock", "mutex", "WebSocket", "stream", "chamada de rede",
  "timeout de rede", "processo travado", "sem saída", "hang", "timeout
  mágico", "número mágico de timeout", "espera bloqueante", "promise
    pendurada", "spinner infinito", "loading infinito", "heartbeat",
    "sinal de vida", "keep-alive".
---

# Operações Assíncronas Confiáveis

## Causa raiz (geral, não só subprocess)

Qualquer operação de duração desconhecida ou variável — processo externo,
chamada de rede, promise, job de fila, lock, stream — vira um problema do
mesmo tipo quando o código a trata como **síncrona e atômica**: "chamo,
espero, uso o resultado". Sob esse modelo, a única pergunta possível diante
da demora é "quanto tempo já passou?", e daí nasce o timeout de relógio com
número escolhido do nada — ou, na ausência de qualquer timeout, a espera
infinita (subprocess pendurado, `await` sem prazo, `fetch` sem
`AbortController`, lock nunca liberado, spinner que não sai da tela).

A pergunta certa é "quanto tempo faz que nada acontece?" ou "isso ainda está
em andamento?" — só respondível se houver sinal observável de progresso ou
conclusão (stream de saída, evento, callback, poll de status, promise
resolvida). **Subprocess é só um caso particular** desse problema; a mesma
falha aparece em `fetch` sem timeout, `await` sem cancelamento, filas sem
callback de conclusão, locks sem prazo, polling sem teto.

## Regra central

**Nunca trate uma operação de duração incerta como bloqueio opaco.** Exponha
sempre um sinal de progresso, cancelamento ou conclusão (stream, callback,
evento, `AbortSignal`, poll de status) antes de decidir quanto tempo esperar
por ela — em qualquer linguagem, backend ou frontend.

## Ordem de preferência (do melhor para o pior)

Ao integrar com uma operação de duração incerta, escolha o mecanismo mais
alto nesta lista que estiver disponível — nunca pule direto para timeout:

1. **Callback / evento / pub-sub** — o chamador é notificado quando a
   operação termina; nenhuma espera ativa é necessária. Sempre que a
   API/broker/biblioteca oferecer isso (webhook, event emitter, message
   broker, `on('done')`), use-o em vez de qualquer forma de espera.
2. **Polling orientado a condição, com backoff** — só quando pub/sub não
   estiver disponível. Verifica uma condição real ("terminou?"), não
   apenas o tempo decorrido.
3. **Heartbeat** — piso mínimo apenas quando a operação não expõe nem
   evento nem estado consultável (ver item 7 do contrato abaixo).
4. **Timeout de relógio isolado** — último recurso, e mesmo assim só como
   rede de segurança (timeout de inatividade/total) por trás de um dos
   mecanismos acima, nunca como único instrumento de decisão.

Esta ordem espelha a regra "Espera de tarefas: preferir determinismo a
timeout" do AGENTS.md global — lá para como o agente espera por *suas*
chamadas de ferramenta, aqui para o código que o agente **escreve**.

## Contrato mínimo (qualquer linguagem, qualquer tipo de operação)

1. Nunca bloquear em espera sem um sinal observável de progresso ou um
   mecanismo de cancelamento.
2. Separar **timeout de inatividade** (idle — tempo sem novo sinal) de
   **timeout total** (duração máxima absoluta). Nunca usar um único número
   mágico para os dois.
3. Se a duração for desconhecida ou variável (builds, chamadas de rede,
   jobs de fila, streams), aplicar a ordem de preferência acima — nunca
   escolher timeout de relógio quando pub/sub, evento ou polling
   condicional estiverem disponíveis.
4. Nunca engolir erro, rejeição de promise ou timeout em `catch`/`except`
   silencioso — propagar causa e contexto.
5. Registrar timestamp da última atividade; travamento é ausência de
   progresso, não tempo total decorrido.
6. Em UI (frontend): toda chamada assíncrona exibida ao usuário (spinner,
   loading state) precisa de timeout + tratamento de erro — nunca deixe um
   estado de carregamento sem saída possível.
7. **Heartbeat quando não há saída natural**: se a operação for longa mas
   não produz output incremental por si (ex.: cálculo pesado, chamada a
   uma API que só responde no fim), emita um heartbeat periódico próprio
   ("ainda vivo, decorridos Ns") em vez de silêncio total. **Heartbeat
   prova que o processo não morreu — não prova que está avançando.**
   Prefira sinal de progresso real (linha de log, evento, delta de
   estado) sempre que existir; use heartbeat como piso mínimo quando não
   houver nada melhor para observar.

## Padrões por categoria (copiar, não reinventar)

### 1. Processo externo (subprocess/exec/spawn/ProcessBuilder)

#### Python

```python
import subprocess, time

def run_streaming(cmd, idle_timeout=30, total_timeout=600):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, bufsize=1)
    start = last_output = time.monotonic()
    while True:
        line = proc.stdout.readline()
        if line:
            print(line, end="")
            last_output = time.monotonic()
        elif proc.poll() is not None:
            break
        now = time.monotonic()
        if now - last_output > idle_timeout:
            proc.kill()
            raise TimeoutError(f"sem saída por {idle_timeout}s")
        if now - start > total_timeout:
            proc.kill()
            raise TimeoutError(f"excedeu {total_timeout}s no total")
    return proc.wait()
```

#### Node.js

```js
const { spawn } = require("child_process");

function runStreaming(cmd, args, { idleTimeoutMs = 30000, totalTimeoutMs = 600000 } = {}) {
  return new Promise((resolve, reject) => {
    const proc = spawn(cmd, args, { stdio: ["ignore", "pipe", "pipe"] });
    let lastOutput = Date.now();
    const idle = setInterval(() => {
      if (Date.now() - lastOutput > idleTimeoutMs) {
        proc.kill("SIGKILL");
        clearInterval(idle);
        reject(new Error(`sem saída por ${idleTimeoutMs}ms`));
      }
    }, 1000);
    proc.stdout.on("data", (d) => { process.stdout.write(d); lastOutput = Date.now(); });
    proc.stderr.on("data", (d) => { process.stderr.write(d); lastOutput = Date.now(); });
    proc.on("close", (code) => {
      clearInterval(idle);
      code === 0 ? resolve(code) : reject(new Error(`exit ${code}`));
    });
    setTimeout(() => {
      proc.kill("SIGKILL"); clearInterval(idle); reject(new Error("timeout total"));
    }, totalTimeoutMs);
  });
}
```

#### Bash

```bash
# timeout total protege o total; tee mantém a saída observável em log
timeout --signal=TERM 600s ./build.sh 2>&1 | tee build.log
# idle real (sem byte novo por N s) exige um watcher separado lendo o
# mtime de build.log — não existe flag nativa de idle-timeout no `timeout`.
```

#### PowerShell

```powershell
$job = Start-Job { & ./build.ps1 }
do {
    Start-Sleep -Seconds 5
    Receive-Job $job -Keep | Write-Host   # emite progresso incremental
} while ($job.State -eq 'Running')
Receive-Job $job
```

#### Java / Groovy

```groovy
def proc = new ProcessBuilder(cmdList).redirectErrorStream(true).start()
def reader = proc.inputStream.newReader()
def line
while ((line = reader.readLine()) != null) {
    println line   // nunca use consumeProcessOutput() sem buffer/callback
}
if (!proc.waitFor(30, TimeUnit.SECONDS)) {   // só após EOF do stream
    proc.destroyForcibly()
    throw new TimeoutException("processo não finalizou após EOF do stream")
}
```

### 2. Chamada de rede / HTTP

Toda chamada de rede precisa de timeout explícito + cancelamento — o
default de muitos clientes HTTP é **sem timeout** (espera infinita).

```js
// fetch (browser/Node 18+): AbortController separa timeout de cancelamento manual
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort("timeout"), 10_000);
try {
  const res = await fetch(url, { signal: controller.signal });
  return await res.json();
} finally {
  clearTimeout(timeoutId);
}
```

```python
import httpx
# connect timeout ≠ read timeout ≠ total: nunca deixe implícito
httpx.get(url, timeout=httpx.Timeout(connect=5, read=15, write=5, pool=5))
```

Retry em chamada de rede: sempre com **backoff exponencial + teto de
tentativas**, nunca retry infinito ou em loop apertado.

### 3. `async`/`await`, Promises, `asyncio`

`await` sem prazo herda a falha do que está sendo aguardado — se a
promise nunca resolve, o `await` nunca retorna. Sempre corrida contra um
timeout quando a duração não é garantida:

```js
function withTimeout(promise, ms, label) {
  const timeout = new Promise((_, reject) =>
    setTimeout(() => reject(new Error(`timeout: ${label} > ${ms}ms`)), ms));
  return Promise.race([promise, timeout]);
}

await withTimeout(fetchUserProfile(id), 8000, "fetchUserProfile");
```

```python
import asyncio
await asyncio.wait_for(fetch_user_profile(id), timeout=8)
```

Em UI: todo estado de `loading`/spinner disparado por uma chamada
assíncrona precisa de um caminho de saída (timeout → estado de erro
visível). "Loading infinito" é o equivalente visual do subprocess
pendurado — mesma causa raiz, sinal de conclusão nunca chega à UI.
Cuidado também com **race conditions** entre requisições concorrentes
(ex.: resposta antiga sobrescrevendo estado mais novo) — use um token/id
de requisição para descartar respostas obsoletas.

### 4. Fila / job em background

Nunca bloqueie esperando um job de fila terminar. Publique e retorne um
identificador; consulte status via polling com backoff ou via callback/
webhook de conclusão:

```text
enqueue(job) -> job_id
poll: status(job_id) -> queued | running | done | failed   (com backoff)
ou: registrar callback/webhook chamado quando o job concluir
```

### 5. Lock / mutex / semáforo

Lock sem prazo é espera infinita disfarçada de exclusão mútua. Sempre
adquirir com timeout e liberar em `finally`/`try-with-resources`:

```python
acquired = lock.acquire(timeout=30)
if not acquired:
    raise TimeoutError("lock não adquirido em 30s")
try:
    ...
finally:
    lock.release()
```

### 6. Polling

Polling sem backoff nem teto vira busy-wait silencioso. Sempre com
intervalo crescente e número máximo de tentativas:

```python
delay = 1
for attempt in range(max_attempts):
    if is_done(job_id):
        return get_result(job_id)
    time.sleep(delay)
    delay = min(delay * 2, 30)
raise TimeoutError(f"job {job_id} não concluiu em {max_attempts} tentativas")
```

## Anti-padrões proibidos

- `consumeProcessOutput()` sem argumentos (Groovy) — descarta a saída.
- `waitFor()` sem timeout (Java/Groovy) — espera para sempre.
- `execSync`/`subprocess.run(..., capture_output=True)` em comando de
  duração desconhecida — bloqueia o processo chamador sem sinal.
- `fetch`/HTTP client sem timeout configurado — depende do default do
  socket (pode ser minutos ou infinito).
- `await`/`Promise` sem corrida contra timeout quando a duração não é
  garantida — mesmo problema do subprocess, em roupa de async/await.
- Estado de `loading` na UI sem timeout que leve a um estado de erro
  visível — "spinner infinito".
- Lock/mutex adquirido sem timeout.
- Polling sem backoff e sem número máximo de tentativas.
- Timeout único de relógio (`waitFor(600, SECONDS)`, um único `setTimeout`
  cobrindo tudo) sem separar inatividade de duração total.
- `catch (e) {}` / `except Exception: pass` ao redor de qualquer chamada
  assíncrona — mascara falha real.

## Critério de revisão (uma linha, verificável)

**Reprovar se uma operação de duração incerta (processo, rede, promise,
fila, lock, polling) for tratada sem timeout de inatividade/total
explícito, sem sinal de progresso ou cancelamento observável, ou com
erro/timeout engolido silenciosamente.**

## Ver também

- `debugging-and-error-recovery` — diagnóstico quando a operação já
  travou em produção.
- Seção "Espera de tarefas: preferir determinismo a timeout" no
  AGENTS.md global — trata de como o próprio agente espera por *suas*
  chamadas de ferramenta; esta skill trata do código que o agente
  **escreve** para lidar com qualquer operação assíncrona ou de duração
  incerta.

