# Otimização do tempo da suíte de integração on-premises

## Overview

A suíte de integração OpenCode com o Bonsai 27B roda em ~24 minutos, com cerca
de 55 s por teste comportamental. O ADR-0002 já consolidou as decisões D1–D21
(AD-1 a AD-21), incluindo o `--ctx-size` fixo que eliminou o thrashing de swap.

Esta rodada trata exclusivamente do tempo restante. Ela parte de medições feitas
diretamente contra o `llama-server` em execução, não de estimativas.

O objetivo não é atingir um tempo alvo. O objetivo é remover desperdício
comprovado e, ao final, saber com evidência qual parte do tempo é teto de
hardware e qual parte era ineficiência corrigível.

## Medições de base

Colhidas em 2026-08-17, no WSL, contra o `llama-server` já ajustado por D18/D20.

| Medição | Valor | Como foi obtida |
|---|---|---|
| Geração | 6,3 tok/s | `timings.predicted_per_second` |
| Prompt eval (16 tok) | 6,1 tok/s | `timings.prompt_per_second` |
| Prompt eval (2.357 tok) | 6,3 tok/s | prompt de preenchimento; 377 s de parede |
| `cached_tokens` | 0 | `usage.prompt_tokens_details` em toda chamada |
| RSS do servidor | 1,28 GB | `ps`, após D20 |
| Swap em uso | 141 MB de 4.096 | `free -m` |
| Backend efetivo | `cpu` | marcador `.llama_backend` |
| Slots do servidor | **4** | `GET /slots` |
| CPU | i7-13800H, AVX2, sem AVX-512 | `/proc/cpuinfo` |

Comparação de raciocínio, mesmo prompt e mesmo servidor:

| Configuração | Parede | Tokens gerados | `content` |
|---|---|---|---|
| Sem flag | 85,6 s | 400 (teto) | vazio |
| `chat_template_kwargs.enable_thinking=false` | **1,5 s** | 2 | `Sim` |
| `reasoning_budget: 0` | 82,7 s | 400 (teto) | vazio |

### Leitura das medições

O achado central é que **prompt eval e geração têm a mesma velocidade**. Em CPU,
a avaliação de prompt normalmente é uma a duas ordens de grandeza mais rápida que
a geração, porque processa tokens em lote. Aqui não é. Isso indica que o kernel
do quant ternário `Q1_0` não tem caminho em lote nesta build, e cada token de
prompt custa aproximadamente o mesmo que um token gerado.

Consequência prática: **cada 100 tokens de prompt custam cerca de 16 segundos**.
Com isso, o tempo de um teste é dominado pelo tamanho do prompt enviado, e
qualquer token de prompt reprocessado desnecessariamente é desperdício direto.

O `reasoning_budget: 0` não funciona nesta build; apenas o
`chat_template_kwargs` desliga o raciocínio.

## Architecture Decisions

### D22 — Reaproveitar o prefixo de prompt entre testes

`cached_tokens` é 0 em todas as chamadas medidas. Os testes de ativação de skill
enviam prompts quase idênticos, diferindo apenas no nome da skill. Como cada
token de prompt custa o mesmo que um token gerado, reprocessar o prefixo comum a
cada teste é o maior desperdício identificado.

A fixture `isolated_opencode` chama `restart_opencode()` e troca o contexto
montado a cada teste. Isso é necessário para o isolamento exigido pelos testes e
**não será removido**. O que se busca é que o servidor reaproveite o prefixo
compartilhado do prompt, o que é uma propriedade do `llama-server`, não do
cliente.

Decisão: medir primeiro qual é o prefixo efetivamente compartilhado entre duas
chamadas consecutivas de testes distintos e, só então, decidir se há prefixo
estável a reaproveitar.

Esta decisão é deliberadamente condicional. Não há evidência ainda de que o
prefixo seja estável; há apenas evidência de que ele não está sendo reusado. Se
a medição mostrar que o prompt diverge nos primeiros tokens, o reuso é
impossível e a decisão se encerra sem mudança de código.

### D23 — Definir threads de forma derivada da máquina

O `llama-server` sobe sem `-t`. O padrão do llama.cpp tenta contar núcleos de
performance, o que em CPUs híbridas pode deixar os núcleos de eficiência
ociosos. A máquina atual tem 6 P-cores e 8 E-cores.

Decisão: definir `-t` explicitamente, com o valor **derivado da máquina em tempo
de execução**, nunca fixo no código.

Isto preserva a repetibilidade exigida: a suíte continua rodando em qualquer
máquina sem edição, e o valor se adapta ao hardware. Um número fixo tornaria a
suíte dependente da máquina onde foi escrita, contrariando AD-19.

O valor só será adotado se a medição comprovar ganho. Se não houver ganho
mensurável, a flag não é adicionada — configuração sem efeito é ruído.

### D24 — Tornar o raciocínio desligado uma asserção, não uma suposição

Está comprovado que `enable_thinking=false` reduz uma resposta de 85,6 s para
1,5 s, e que sem ele o campo `content` volta **vazio**. A configuração de teste
já declara esse parâmetro.

O que não está comprovado é que o OpenCode o repassa ao servidor. A dedução
atual é indireta: os testes levam 55 s, e só o raciocínio já consumiria 85 s,
portanto ele aparentemente está desligado.

Decisão: substituir essa dedução por uma verificação executável. Se o repasse
falhar em alguma atualização do OpenCode ou do provider, a suíte deve acusar
explicitamente, e não degradar em silêncio para 85 s por chamada.

O modo de falha é traiçoeiro: sem o repasse, `content` vem vazio e as asserções
de conteúdo falham com uma mensagem que não aponta para a causa real.

### D25 — Reduzir o paralelismo do servidor a um slot

Achado do replan: o `llama-server` sobe com **quatro slots**, confirmado em
`/slots`. Cada slot mantém seu próprio cache de prefixo.

Como os testes de integração são sequenciais, no máximo um slot trabalha por
vez. Os outros três reservam contexto e fragmentam o cache: duas chamadas com o
mesmo prefixo podem cair em slots distintos e nenhuma delas aproveita a leitura
da outra.

Isso é pré-condição de D22. Enquanto o prefixo estiver espalhado por quatro
caches, o reuso não se sustenta mesmo que o prompt seja estável.

Decisão: fixar o paralelismo em um slot, mediante medição que comprove ganho ou
que comprove o reuso de cache viabilizado.

Esta decisão é barata de testar e independente de conhecer o tamanho exato do
prompt, por isso é executada antes da instrumentação de log.

### D26 — Capturar o prompt pelo log do próprio servidor

O plano original mandava usar o proxy TCP existente como ponto de captura. Isso
estava **errado**: aquele proxy fica entre o cliente de teste e o OpenCode, e as
chamadas a `/v1/chat/completions` seguem do container para o `llama-server`, sem
passar por ele.

Duas alternativas foram consideradas. Interpor um novo proxy no caminho do
modelo exigiria código novo apenas para medir, com risco de vazar para o caminho
de produção — risco já registrado nesta rodada. A verbosidade de log do próprio
`llama-server` obtém o mesmo dado sem componente novo e sem alterar a topologia.

Decisão: capturar o prompt pela verbosidade de log do `llama-server`, como
ajuste temporário de diagnóstico, revertido ao fim da Fase 1.

A captura só é necessária se D25 não resolver sozinha. Ela existe para obter o
tamanho exato do prefixo comum quando o ganho do slot único for insuficiente.


### Fase 1 — Medição

Nenhuma mudança permanente de comportamento nesta fase. Ela existe para que as
decisões D22, D23 e D25 sejam tomadas com dados, não com hipótese.

A ordem é deliberada: a Task 1A é barata e pode entregar o ganho sozinha,
tornando a instrumentação da Task 1B desnecessária.

**Task 1A — Medir o efeito do slot único**

Subir o `llama-server` com paralelismo de um slot e medir o efeito em duas
chamadas consecutivas com o mesmo prefixo longo e sufixos diferentes.

Entregar: `cached_tokens` da segunda chamada, tempo de parede de cada uma e
comparação com o comportamento de quatro slots. Confirmar em `/slots` que o
servidor passou a expor um único slot.

Se o reuso de cache passar a funcionar, reportar antes de seguir.

**Task 1B — Capturar o prompt real pelo log do servidor**

Executar somente se a Task 1A não evidenciar reuso, ou se o ganho for
insuficiente.

Subir o `llama-server` com verbosidade de log suficiente para registrar o prompt
recebido e executar dois testes comportamentais consecutivos e distintos.
Registrar o número de tokens de prompt de cada chamada e o tamanho do prefixo
idêntico entre elas.

Entregar: contagem de tokens por chamada, tamanho do prefixo comum e se
`chat_template_kwargs` aparece no corpo recebido.

A verbosidade é ajuste temporário de diagnóstico e deve ser revertida ao fim da
fase. Não deixar a flag no caminho de produção.

**Task 2 — Medir o efeito de `-t` no throughput**

Subir o `llama-server` com valores distintos de `-t` e medir
`prompt_per_second` e `predicted_per_second` com prompt de tamanho realista,
obtido na Task 1A ou 1B.

Cobrir ao menos: padrão atual sem a flag, número de P-cores, e total de núcleos
físicos. Reportar a tabela completa, inclusive resultados negativos.

**Task 3 — Verificar o reuso de cache com prefixo estável**

Emitir duas chamadas consecutivas ao servidor com o mesmo prefixo longo e
sufixos diferentes. Confirmar se `cached_tokens` fica maior que zero e medir a
redução de tempo. Isto isola a capacidade do servidor da questão de o OpenCode
produzir ou não um prefixo estável.

Executar com o paralelismo definido pela Task 1A, para que o resultado não seja
mascarado por fragmentação entre slots.

### Fase 2 — Implementação

Cada task desta fase é condicional ao resultado correspondente da Fase 1.

**Task 3B — Fixar o paralelismo em um slot, se houver ganho**

Somente se a Task 1A comprovar ganho de tempo ou viabilizar o reuso de cache.
Fixar o paralelismo no comando do `BonsaiServer`, com teste automatizado que
verifique a flag no comando construído.

Se não houver ganho nem reuso viabilizado, registrar a medição e não alterar o
comando.

**Task 4 — Aplicar `-t` derivado, se houver ganho**

Somente se a Task 2 comprovar ganho. O valor deve ser calculado a partir da
topologia da máquina, com a biblioteca padrão. Não introduzir dependência nova.

Se não houver ganho, registrar a medição e não alterar o comando.

**Task 5 — Habilitar o reuso de prefixo, se for viável**

Somente se as Tasks 1A, 1B e 3 mostrarem prefixo comum relevante e reuso
funcional. A mudança deve preservar integralmente o isolamento entre testes.

Se o prefixo divergir cedo, documentar o motivo e encerrar sem mudança.

**Task 6 — Asserção de raciocínio desligado**

Adicionar verificação que falhe de forma explícita quando o raciocínio não
estiver desligado no caminho efetivo dos testes. A mensagem de falha deve
apontar para o repasse de `chat_template_kwargs`, não para o conteúdo da
resposta.

Esta task não é condicional.

### Fase 3 — Consolidação

**Task 7 — Atualizar o ADR-0002**

Acrescentar AD-22 a AD-26 com os resultados reais, incluindo as medições
que levaram a não aplicar alguma mudança. Registrar as medições de base desta
rodada na seção de contexto, para que a próxima pessoa não precise remedi-las.

**Task 8 — Remover o arquivo de planejamento**

Somente após confirmar que o ADR-0002 contém as cinco decisões e as medições.

## Orquestração

Conforme o protocolo do `smart-planner`, a execução e a revisão ocorrem em
instâncias independentes, criadas pela capacidade nativa de subagentes da
plataforma atual (Copilot CLI).

| Papel | Modelo | Origem da escolha |
|---|---|---|
| Executor | GPT-5.6 Terra | Reutilizado de `plan/smart-planner-orquestracao.md` |
| Revisor | GPT-5.6 Terra | Reutilizado de `plan/smart-planner-orquestracao.md` |

O revisor recebe o plano, o ADR e o resultado observável da execução, mas nunca
a sessão do executor. Achados retornam ao executor em uma instância nova; a
instância revisora anterior jamais é reutilizada.

O término técnico só ocorre com aprovação explícita do revisor, sem achados
pendentes. A aprovação do plano, isoladamente, nunca encerra a tarefa.

## Risks and Mitigations

| Risco | Mitigação |
|---|---|
| Prefixo do prompt diverge cedo e o reuso é impossível | D22 é condicional; encerra sem mudança e documenta |
| `-t` não traz ganho e vira configuração inútil | Task 4 só aplica com medição; resultado negativo é registrado |
| Valor de `-t` fixo quebra portabilidade | D23 exige derivação em runtime, nunca constante |
| Reuso de cache enfraquece o isolamento entre testes | Isolamento é requisito; Task 5 falha se houver conflito |
| Instrumentação da Task 1 vaza para produção | Captura restrita à fase de medição, revertida ao final |
| Ganho é pequeno e o teto é o kernel ternário | Resultado é legítimo; registrar no ADR encerra a questão |
| Suíte degrada em silêncio se o repasse do parâmetro parar | Task 6 transforma isso em falha explícita |
| Medições feitas só nesta máquina não generalizam | ADR registra CPU e backend junto dos números |
| Verbosidade de log da Task 1B vaza para produção | Ajuste temporário, revertido ao fim da Fase 1 |
| Slot único vira gargalo se a suíte paralelizar no futuro | ADR registra que a premissa é execução sequencial |

## Open Questions

Nenhuma no momento.
