---
name: reliable-async-operations
description: >
  Use ao escrever ou revisar código com subprocess, fetch/HTTP, async/await,
  polling, retry, lock, fila em background, WebSocket ou stream, ao
  investigar operação travada ou sem progresso, e ao definir, ajustar ou
  aumentar timeout. Padrão para operação de duração desconhecida ou
  variável, em qualquer linguagem: exponha sinal de progresso,
  cancelamento ou conclusão antes de decidir a espera; proíbe timeout
  genérico com número mágico. Triggers: "processo externo", "subprocess",
  "child_process", "ProcessBuilder", "execSync", "waitFor", "spawn",
  "async", "await", "Promise", "asyncio", "fetch sem timeout",
  "AbortController", "race condition", "polling", "retry", "backoff",
  "fila assíncrona", "job em background", "lock", "mutex", "WebSocket",
  "stream", "chamada de rede", "timeout de rede", "timeout genérico",
  "definir timeout", "ajustar timeout", "aumentar timeout", "processo
  travado", "sem saída", "hang", "timeout mágico", "número mágico de
  timeout", "espera bloqueante", "promise pendurada", "spinner infinito",
  "loading infinito", "heartbeat", "sinal de vida", "keep-alive".
---

# Operações Assíncronas Confiáveis

## Causa raiz

Toda operação de duração desconhecida ou variável (processo externo,
chamada de rede, promise, job, lock, stream) falha do mesmo modo quando o
código a trata como síncrona e atômica: a única pergunta disponível é
"quanto tempo já passou?", e daí nasce o timeout de relógio chutado ou, na
ausência de timeout, a espera infinita (`fetch` sem `AbortController`,
subprocess pendurado, lock sem prazo, spinner eterno). A pergunta certa é
"quanto tempo faz que nada acontece?" — só respondível com sinal
observável de progresso ou conclusão (stream, evento, callback, poll de
status, promise resolvida). Subprocess é um caso particular do problema.

## Regra central

**Nunca trate uma operação de duração incerta como bloqueio opaco.** Exponha
sempre um sinal de progresso, cancelamento ou conclusão (stream, callback,
evento, `AbortSignal`, poll de status) antes de decidir quanto tempo esperar
por ela — em qualquer linguagem, backend ou frontend.

## Proibição de definir ou ajustar timeouts

- **PROIBIDO definir ou ajustar timeouts genéricos ou por conveniência**:
  timeout não mascara travamento, não impõe desempenho e não vira critério
  de falha.
- **Exceções** — as únicas: recurso contínuo com inatividade já comprovada,
  ou confirmação explícita prévia do humano, com justificativa do recurso e
  do valor.
- **Não troque timeout proibido por valor alto**: remova o timeout ou
  consulte o humano. Timeout existente fora das exceções: informe ao humano;
  não altere silenciosamente.

Essa proibição não revoga o requisito de timeout explícito em toda chamada
de rede (seção "Padrões por categoria" abaixo) — os dois se completam: o
alvo da proibição é o número chutado como desencargo de consciência; o
timeout exigido é rede de segurança ancorada a sinal de vida — tempo de
inatividade — com valor justificado pelo recurso e pela operação, derivado
do pior caso conhecido. O timeout permitido funciona como teto de segurança,
nunca como número mágico ou substituto do sinal de conclusão. Espera cega ou
infinita continua proibida.

## Ordem de preferência (do melhor para o pior)

Escolha o mecanismo mais alto disponível — nunca pule direto para timeout:

1. **Callback / evento / pub-sub** — o chamador é notificado da conclusão;
   nenhuma espera ativa. Sempre que a API/broker/biblioteca oferecer
   (webhook, event emitter, `on('done')`), use-o em vez de qualquer espera.
2. **Polling orientado a condição, com backoff** — só sem pub/sub. Verifica
   uma condição real ("terminou?"), não o tempo decorrido.
3. **Heartbeat** — piso mínimo quando a operação não expõe nem evento nem
   estado consultável (ver item 7 do contrato abaixo).
4. **Timeout de relógio isolado** — último recurso, só como rede de
   segurança (inatividade/total) por trás de um mecanismo acima, nunca como
   único instrumento de decisão.

A distinção de escopo importa: esta skill rege o **código que o agente
escreve** para lidar com operações de duração incerta. Quando for o
próprio agente esperando por *suas* chamadas de ferramenta, vale o mesmo
princípio — espere por um sinal determinístico de conclusão (evento,
callback, polling de condição, resultado observável), nunca por uma
estimativa de tempo. Faça esperas progressivas em incrementos de 30 s. Antes
de ultrapassar 30 s acumulados, peça confirmação ao humano. Uma delegação
explícita de autonomia pode autorizar continuações sem nova confirmação.

## Contrato mínimo (qualquer linguagem, qualquer tipo de operação)

1. Nunca bloquear em espera sem sinal observável de progresso ou mecanismo
   de cancelamento.
2. Separar **timeout de inatividade** (idle — tempo sem novo sinal) de
   **timeout total** (duração máxima absoluta). Nunca um único número
   mágico para os dois.
3. Duração desconhecida ou variável (builds, rede, jobs, streams): aplicar
   a ordem de preferência — nunca timeout de relógio quando pub/sub,
   evento ou polling condicional estiverem disponíveis.
4. Nunca engolir erro, rejeição ou timeout em `catch`/`except` silencioso —
   propagar causa e contexto.
5. Registrar timestamp da última atividade: travamento é ausência de
   progresso, não tempo total decorrido. Em streams e logs, cada linha nova
   sinaliza atividade e atualiza esse timestamp. A falha ocorre quando a
   inatividade ultrapassa o limite definido, não pelo tempo total decorrido.
6. Em UI: toda chamada assíncrona visível ao usuário (spinner, loading)
   precisa de timeout + tratamento de erro — nunca um estado de
   carregamento sem saída.
7. **Heartbeat quando não há saída natural**: operação longa sem output
   incremental (cálculo pesado, API que só responde no fim) emite
   heartbeat periódico próprio em vez de silêncio. **Heartbeat prova que o
   processo não morreu — não que está avançando.** Prefira sinal de
   progresso real; heartbeat é piso mínimo.

## Padrões por categoria (copiar, não reinventar)

Exemplos completos de implementação estão em
[Exemplos por categoria](references/exemplos-por-categoria.md). As regras
por categoria seguem abaixo.

### 1. Processo externo (subprocess/exec/spawn/ProcessBuilder)

Os exemplos em Python, Node.js, Bash, PowerShell e Java/Groovy estão na
referência acima.

### 2. Chamada de rede / HTTP

Toda chamada de rede precisa de timeout explícito + cancelamento — o
default de muitos clientes HTTP é espera infinita.

Os exemplos de `fetch` e `httpx` estão na referência acima.

Retry em rede: sempre com **backoff exponencial + teto de tentativas**,
nunca retry infinito ou em loop apertado.

### 3. `async`/`await`, Promises, `asyncio`

`await` sem prazo herda a falha do que aguarda: promise que nunca resolve
deixa o `await` pendurado. Corra contra um timeout quando a duração não é
garantida:

Os exemplos de JavaScript e Python estão na referência acima.

"Loading infinito" na UI é o subprocess pendurado em roupa visual: mesma
causa raiz, sinal de conclusão que nunca chega. Guarde também para
**race conditions** entre requisições concorrentes (resposta antiga
sobrescrevendo estado mais novo): descarte respostas obsoletas com um
token/id de requisição.

### 4. Fila / job em background

Nunca bloqueie esperando job de fila terminar. Publique e retorne um
identificador; consulte status via polling com backoff ou via callback/
webhook de conclusão:

O fluxo de exemplo está na referência acima.

### 5. Lock / mutex / semáforo

Lock sem prazo é espera infinita disfarçada de exclusão mútua. Adquirir
sempre com timeout e liberar em `finally`/`try-with-resources`:

O exemplo de Python está na referência acima.

### 6. Polling

Polling sem backoff nem teto vira busy-wait silencioso. Sempre com
intervalo crescente e número máximo de tentativas:

O exemplo de Python está na referência acima.

## Anti-padrões proibidos

- `consumeProcessOutput()` sem argumentos (Groovy) — descarta a saída.
- `waitFor()` sem timeout (Java/Groovy) — espera para sempre.
- `execSync`/`subprocess.run(..., capture_output=True)` em comando de
  duração desconhecida — bloqueia o chamador sem sinal.
- `fetch`/HTTP client sem timeout — depende do default do socket (minutos
  ou infinito).
- `await`/`Promise` sem corrida contra timeout quando a duração não é
  garantida — o subprocess pendurado em roupa de async/await.
- Estado de `loading` na UI sem timeout que leve a estado de erro visível.
- Lock/mutex adquirido sem timeout.
- Polling sem backoff e sem teto de tentativas.
- Timeout único de relógio sem separar inatividade de duração total.
- `catch (e) {}` / `except Exception: pass` em chamada assíncrona —
  mascara falha real.

## Critério de revisão (uma linha, verificável)

**Reprovar se uma operação de duração incerta (processo, rede, promise,
fila, lock, polling) for tratada sem timeout de inatividade/total
explícito, sem sinal de progresso ou cancelamento observável, ou com
erro/timeout engolido silenciosamente.**

## Ver também

- `debugging-and-error-recovery` — diagnóstico quando a operação já
  travou em produção.
