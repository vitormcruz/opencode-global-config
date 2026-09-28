# Exemplos por categoria

Os trechos abaixo complementam as regras de
`reliable-async-operations`. Os exemplos não alteram o
contrato da skill.

Os valores numéricos são ilustrativos. Derive cada timeout do pior caso
conhecido da operação e não copie valores sem justificativa.

## Processo externo

### Python

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

### Node.js

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

### Bash

```bash
# timeout total protege o total; tee mantém a saída observável em log
timeout --signal=TERM 600s ./build.sh 2>&1 | tee build.log
# idle real (sem byte novo por N s) exige um watcher separado lendo o
# mtime de build.log — não existe flag nativa de idle-timeout no `timeout`.
```

### PowerShell

```powershell
$job = Start-Job { & ./build.ps1 }
do {
    Start-Sleep -Seconds 5
    Receive-Job $job -Keep | Write-Host   # emite progresso incremental
} while ($job.State -eq 'Running')
Receive-Job $job
```

### Java / Groovy

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

## Chamada de rede / HTTP

### JavaScript

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

### Python

```python
import httpx
# connect timeout ≠ read timeout ≠ total: nunca deixe implícito
httpx.get(url, timeout=httpx.Timeout(connect=5, read=15, write=5, pool=5))
```

## async/await, Promises e asyncio

### JavaScript

```js
function withTimeout(promise, ms, label) {
  const timeout = new Promise((_, reject) =>
    setTimeout(() => reject(new Error(`timeout: ${label} > ${ms}ms`)), ms));
  return Promise.race([promise, timeout]);
}

await withTimeout(fetchUserProfile(id), 8000, "fetchUserProfile");
```

### Python

```python
import asyncio
await asyncio.wait_for(fetch_user_profile(id), timeout=8)
```

## Fila / job em background

```text
enqueue(job) -> job_id
poll: status(job_id) -> queued | running | done | failed   (com backoff)
ou: registrar callback/webhook chamado quando o job concluir
```

## Lock / mutex / semáforo

```python
acquired = lock.acquire(timeout=30)
if not acquired:
    raise TimeoutError("lock não adquirido em 30s")
try:
    ...
finally:
    lock.release()
```

## Polling

```python
delay = 1
for attempt in range(max_attempts):
    if is_done(job_id):
        return get_result(job_id)
    time.sleep(delay)
    delay = min(delay * 2, 30)
raise TimeoutError(f"job {job_id} não concluiu em {max_attempts} tentativas")
```
