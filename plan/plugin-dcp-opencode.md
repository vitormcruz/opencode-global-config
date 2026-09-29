# Plano: incorporação do plugin DCP (Dynamic Context Pruning) ao OpenCode

Status: CONSTRUÇÃO: Fase 3 em andamento, Tasks 6 e 7 concluídas, commitadas
e verificadas (suíte verde). Pendentes: Tasks 8 e 9, revisão da construção
(rev) e materialização no user-space (Fase 4). Próxima: Task 8.

Workflow aberto em 2026-09-27. Escopo original: até a aprovação do plano.
EXTENDIDO em 2026-09-28 pelo humano (item 13 de `## Perguntas`): após a
verificação final do rev (APROVADO COM RESSALVAS, achados 12 e 13
textuais), o ciclo segue direto para a CONSTRUÇÃO e fases seguintes.
Autonomia vigente: gates operacionais fluem; parar só em bloqueante (push
e exclusões sempre exigem humano).

Histórico de controle (2026-09-27): "esperar para tudo" vigorou até a
decisão de estender o ciclo.

## Insumo do humano (2026-09-27)

### Contexto

Este projeto usa OpenCode como ferramenta de desenvolvimento assistido.
Sessões longas enchem a janela de contexto. O `/compact` nativo é comando de
usuário e apresentou falhas recentes (anomalyco/opencode#17557: o contexto
aumentava em vez de diminuir). A decisão foi adotar o plugin DCP, que expõe
a compactação como ferramenta chamável pelo próprio agente. Este prompt é
autocontido; nenhuma conversa anterior é necessária.

### O que é o DCP

- Pacote npm: `@tarquinen/opencode-dcp`
- Repo: https://github.com/Opencode-DCP/opencode-dynamic-context-pruning
- Registra a tool `compress` no contexto do modelo: o agente decide quando
  comprimir, escolhe os ranges (IDs `mNNNN`/`bN`) e escreve os sumários. O
  histórico original nunca é modificado; o plugin substitui conteúdo por
  placeholders antes de enviar requisições ao LLM.
- Nudges: lembretes injetados no prompt quando o contexto passa de
  `maxContextLimit`, empurrando o agente a chamar `compress`.
- Instalação: `opencode plugin @tarquinen/opencode-dcp@latest --global` ou
  `"plugin": ["@tarquinen/opencode-dcp"]` no `opencode.json`.
- Config principal: `compress.permission` (allow|ask|deny), `compress.mode`
  (range|message), `maxContextLimit`, `minContextLimit`, `nudgeFrequency`,
  `iterationNudgeThreshold`, `protectedFilePatterns`, `protectedTools`,
  `protectUserMessages`, `manualMode`, `strategies` (deduplication,
  purgeErrors), `experimental.allowSubAgents`.
- Comandos: `/dcp` (painel TUI), `/dcp-compress [focus]`.
- Licença: AGPL-3.0-or-later.

### Ressalva de escopo (importante para o plano)

Não existe alternativa equivalente no GitHub Copilot: a compactação é
host-level, o agente não tem tool para dispará-la (o hook `preCompact` é
apenas notificação). O MCP `compaction-mcp` até gera resumos, mas não evicta
mensagens da janela do host; recuperar tokens exige re-seed em chat novo.
Conclusão: o ganho desta implementação vale apenas onde o fluxo roda
OpenCode. Partes do workflow que rodarem no Copilot continuam sem compactação
acionável pelo agente. O plano deve mapear quais fluxos rodam em qual
ferramenta.

### O que planejar (entregável: plano em fases, sem implementar)

1. Inventário: versão do OpenCode em uso, plugins e MCP servers já
   configurados, uso de subagents (suporte do DCP a subagents é experimental
   via `experimental.allowSubAgents`; validar se os subagents do projeto
   funcionam com ele ativo).
2. Escopo de ativação: global vs por projeto; modo (`range` vs `message`) e
   thresholds iniciais coerentes com o tamanho de contexto dos modelos
   usados no projeto.
3. Riscos: interação com hooks/plugins que também transformam prompt
   (transformações concorrentes), AGPL-3.0 (relevante só se o projeto
   distribuir código derivado), permission gate (`allow` vs `ask`) diante
   das regras de permissão existentes.
4. Validação: critérios objetivos para aceitar o plugin (tokens de contexto
   caem após `compress`, prompt cache não degradado, subagents sem regressão)
   e rollback (remover do config e reiniciar).
5. Rollout: fases com pontos de verificação e critério de decisão explícito
   por fase.

## Contexto adicional levantado pelo devflow (2026-09-27)

- Política de compactação vigente (decisão D11 do plano
  `otimizacao-custo-contexto.md`, commit `c24068d`): o `AGENTS.base.md`
  orienta todos os agentes a preferir mecanismos automatizados (auto
  compactação por threshold, nova sessão com estado persistido) e, sem
  alternativa, pedir `/compact` ao humano. A tool `compress` do DCP muda
  essa premissa: prever atualização do texto do `AGENTS.base.md` e da
  premissa 7 de `docs/workflow-agentes-dev.md` (exceção de compactação).
- Plugin ai-memory ativo em user-space
  (`~/.config/opencode/plugins/ai-memory.ts`) com hooks em
  `experimental.session.compacting`/`session.compacted`; MCP ai-memory com
  provisionamento no bootstrap (decisão P1 do ciclo vizinho). O risco de
  "transformações concorrentes" citado no insumo INCLUI esse plugin.
- Baseline de compactação (Task 12 do ciclo vizinho, 2026-09-23): `/compact`
  reduziu o contexto de ~88,6k para ~55,4k tokens/chamada (-37%); payback
  ~1,1 chamada; provider zai reporta `cost`=0 (medição em tokens; US$ só
  com tarifa externa). Método de medição: sqlite em
  `~/.local/share/opencode/opencode.db`, tabela `message`.
- Mapa de modelos decidido em 2026-09-27 no ciclo vizinho (registro
  HISTÓRICO; suplantado pelo mapa definitivo de 2026-09-28, seção
  `## Mapa de modelos deste workflow`, item 13 de `## Perguntas`):
  executores = `opencode/gpt-6-luna` (reasoning high); revisor =
  `zai-coding-plan/glm-5.3`. No mapa vigente o provider é sempre zai
  (execução `zai-coding-plan/glm-5.3-flash`) e o luna está
  descontinuado neste ciclo.
- Config canônica do OpenCode: `harness-conf/opencode.json` (symlink global
  no Linux/WSL; cópia sincronizada no Windows). Regra do repo: toda mudança
  em workflow ou agentes passa pelo humano; consistência guardada por
  `tests/agents/test_workflow_consistency.py`.
- Regra do repo para skills/plugins importados: revisão de segurança
  obrigatória na importação (ler TODO o conteúdo copiado procurando prompt
  injection, comandos, URLs e exfiltração) e registro de proveniência.

## Mapa de modelos deste workflow

Mapa definitivo (humano, 2026-09-28; provider sempre zai):

- Execução (CONSTRUÇÃO/TESTES e correções por executores):
  `zai-coding-plan/glm-5.3-flash`.
- Revisão (REVISÃO DO PLANO e REVISÃO DA CONSTRUÇÃO):
  `zai-coding-plan/glm-5.3`.
- VALIDAÇÃO já ocorreu com `opencode-go/gpt-6-luna` max (2026-09-27);
  provider luna descontinuado neste ciclo ("sempre zai").
- Autonomia (humano, 2026-09-28): verificação do rev passando (ou achados
  simples resolvidos sem nova revisão) segue direto para a CONSTRUÇÃO, sem
  pausa de aprovação do plano. Gates operacionais fluem; parar só em
  bloqueante (push e exclusões sempre exigem humano).

## Perguntas

1. RESOLVIDA (2026-09-27): provider `opencode-go` existe; ref registrado no
   mapa de modelos: `opencode-go/gpt-6-luna` com reasoning `max` (o "max" é
   effort, não parte do nome, conforme o humano). Remissão (2026-09-28):
   registro HISTÓRICO; o mapa definitivo (seção `## Mapa de modelos deste
   workflow`; item 13 de `## Perguntas`) descontinuou o provider luna
   neste ciclo ("sempre zai").
2. REGISTRADA (2026-09-27, decisão do humano no gate: "não tratar agora"):
   lacunas de curadoria ADIADAS, não bloqueiam este ciclo plan-only.
   (a) `docs/specs/regras-negocio.md` ausente (destino obrigatório na tabela
   de Elementos de Especificação; criação atribuída nominalmente ao ciclo
   vizinho `otimizacao-custo-contexto.md` desde 2026-09-24 e ainda não
   executada); (b) suíte de segurança: após retry de rede 3x, pip-audit sem
   finding bloqueante garantido para exit code não zero e sem instrução de
   rede acionável nos caminhos de erro;    (c) melhoria de redação do retrofit
   dos ADRs em `docs/README.md:108`. Encaminhamento fica com o humano.
3. RESOLVIDA (2026-09-27, humano): global via repo (opção a). Plugin
   declarado em `harness-conf/opencode.json`; adapter estendido para
   sincronizar `harness-conf/dcp.jsonc` até `~/.config/opencode/dcp.jsonc`
   (novo destino no contrato `HarnessAdapter`, com testes).
4. RESOLVIDA (2026-09-27, humano; EMENDADA na revisão do plano): modo
   `range` (default do upstream), SEM `protectedTools`. Emenda do humano:
   compressão existe para economizar tokens; estado é papel do ai-memory
   (captura automática de prompts como observações de ciclo de vida); o
   que o agente perder, reconsulta. Sem rede de proteção.
5. RESOLVIDA (2026-09-27, humano): `compress.permission = "allow"`
   (automático) desde o spike; auditoria de sumário pós-fato pelo sqlite
   (caminho QA-ACC-5 com `allow`). Divergência eng (allow) vs sec (ask
   inicial) resolvida pelo lado da engenharia; `deny` segue como rollback
   instantâneo.
6. RESOLVIDA (2026-09-27, humano): defaults no piloto (`maxContextLimit`
   100000 / `minContextLimit` 50000); limites de PRODUÇÃO por modelo
   (`modelMaxLimits`/`modelMinLimits`) calibrados no gate C4 com os dados
   medidos, antes do rollout geral (decisão de intenção registrada).
7. RESOLVIDA (2026-09-27, humano): spec com versão fixa
   (`@tarquinen/opencode-dcp@X.Y.Z`, sem autoUpdate), com acréscimo do
   humano: criar rotina de verificação e atualização de versões defasadas
   (incorporar ao plano; bump continua sendo nova importação com checklist
   SEC reexecutado).
8. RESOLVIDA (2026-09-27, humano, CONTRA as recomendações de eng/sec/qa):
   `experimental.allowSubAgents = true` já no piloto. Risco experimental
   aceito pelo humano; o plano deve prever método de validação por sessão
   filha (`session.parent_id`) e ciclo dedicado (ajustes no QA-ACC-3).
9. RESOLVIDA (2026-09-27, humano; REVERTIDA na revisão do plano):
   `compress.protectUserMessages = false` (default do upstream). Princípio
   do humano: comportamento o mais próximo possível do padrão; o modelo
   pode trabalhar sobre resumo das falas antigas; recuperação sempre por
   reconsulta ao ai-memory.
10. RESOLVIDA (2026-09-27, humano): sessão longa natural no piloto (opção
    a do qa); sem thresholds reduzidos como instrumento.
11. RESOLVIDA (2026-09-27, humano): literais do QA-ACC-1 endossados: ≥ 20%
    de queda por evento, média ≥ 37%, payback ≤ 3 steps.
12. REGISTRADA (2026-09-27, humano, na revisão do plano): princípio de
    simplicidade — comportamento o mais próximo possível do padrão do
    DCP; sem mecanismos de proteção ou integrações inventadas. Efeitos:
    `protectedTools` e `protectedFilePatterns` removidos;
    `protectUserMessages = false` (reverte P9); Task 4 passa a OBSERVAR,
    de forma passiva, se o hook do ai-memory dispara sobre uma compressão
    do DCP (verificação pedida pelo humano), sem construir cola nova; o
    hook segue necessário apenas para o `/compact` nativo (destrutivo),
    onde nada muda. `experimental.allowSubAgents = true` (P8) permanece:
    decisão funcional explícita, não mecanismo de proteção.
13. REGISTRADA (2026-09-28, humano): mapa de modelos definitivo — execução
    `zai-coding-plan/glm-5.3-flash`; revisão `zai-coding-plan/glm-5.3`;
    provider sempre zai. Autonomia concedida: após a verificação do rev
    (passando, ou com achados simples resolvidos sem nova revisão), o
    workflow segue direto para a CONSTRUÇÃO, sem pausa de aprovação do
    plano; gates operacionais fluem; parar só em bloqueante (push e
    exclusões sempre exigem humano).

## VALIDAÇÃO

**Veredito: LACUNAS**

Inspeção estática do checkout em 2026-09-27. Nenhuma suíte foi executada,
conforme solicitado.

| Item | Esperado | Evidência | Status |
|---|---|---|---|
| `docs/README.md` | Quatro seções, sem H2 órfão. | H2 nas linhas 9, 43, 144 e 152. | OK |
| backend | pytest, lint, cobertura ≥70% e Concordion. | Wrapper e módulo cobrem os checks declarados. | OK |
| segurança | Checks e retry 3x, com falha acionável. | Pós-retry não garante finding de rede acionável. | LACUNA |
| agregador | Chama as duas suítes e falha se uma falhar. | Lista backend e segurança e agrega os resultados. | OK |
| índice no `AGENTS.md` | Tabela e link iguais, sem spec duplicada. | Linhas 185-197: nomes, agregador e âncora. | OK |
| destinos | Todo Destino não `nenhum` existe. | Falta `docs/specs/regras-negocio.md`; os demais existem. | LACUNA |
| Achado A | Reavaliar frase do retrofit. | Frase persiste; ADRs 0001-0006 têm seção e fixtures. | RESSALVA |

### Evidências detalhadas

- `src/opencode_config/product_tests/backend.py:64-98` executa pytest
  `-m all` e exige cobertura de 70%.
  As linhas 101-198 executam ruff, shellcheck e PSScriptAnalyzer.
  As linhas 271-279 executam Concordion para backend.
- `src/opencode_config/product_tests/security.py:121-276` executa os quatro
  checks da spec.
  `src/opencode_config/product_tests/process.py:141-174` limita o retry a três
  tentativas.
- `src/opencode_config/product_tests/security.py:185-198` não valida o exit
  code de pip-audit após retry.
  `src/opencode_config/product_tests/concordion.py:166-197` não acrescenta
  instrução de rede explícita após o retry esgotado.
- `src/opencode_config/product_tests/aggregator.py:20, 33-101` chama as duas
  suítes e agrega status e findings.
  `testes-produto/__main__.py:14-18` delega para o agregador.
- `docs/specs/` contém `Backend.md`, `Seguranca.md` e `rnf-gerais.md`.
  `docs/adr/` contém ADRs 0001-0009 e diagramas C4 L1, L2 e L3.
- `README.md` existe. Foram encontrados 16 arquivos `UPSTREAM.md` em pastas
  de skills. O destino `nenhum` de Regras de Produto foi ignorado.
- O Achado A não se repete como lacuna factual: `docs/README.md:108-110`
  descreve os ADRs legados como retrofitados; os ADRs 0001-0006 têm a seção
  "Asserções executáveis", fixtures correspondentes e mapeamento em
  `build.gradle:47-61`. A ressalva é de redação histórica.

### Achados

- **Achado:** `docs/specs/regras-negocio.md` não existe, embora conste como
  destino obrigatório em `Elementos de Especificação`.
  **Ação:** solicitar ao agente `eng-software` a criação do artefato conforme
  a spec. Esta inspeção não alterou o arquivo.
  **Severidade:** bloqueante.
- **Achado:** após o retry de rede, pip-audit pode não gerar finding bloqueante
  para exit code não zero; os caminhos de erro também não garantem instrução
  de rede acionável.
  **Ação:** tratar exit não zero como falha e emitir finding bloqueante com
  instrução de rede após a terceira tentativa. Manter o retry e os checks.
  **Severidade:** bloqueante.
- **Achado:** `docs/README.md:108` ainda descreve o retrofit dos ADRs em termos
  históricos, embora a convenção já esteja vigente.
  **Ação:** considerar uma formulação de estado atual para os ADRs 0001-0009.
  **Severidade:** melhoria.

**Perguntas abertas:** nenhuma decisão humana pendente nesta inspeção.

## PLANEJAMENTO

### Engenharia (eng-software)

Planejamento da incorporação do plugin DCP (`@tarquinen/opencode-dcp`),
elaborado em 2026-09-27. Escopo deste ciclo: plano até a aprovação na fase
REVISÃO DO PLANO. Nenhuma fase de execução inicia sem confirmação humana
(decisão "esperar para tudo", 2026-09-27).

Revisão de encerramento (2026-09-27): decisões humanas das Perguntas 3 a
11 (mediação do devflow; textos completos na seção `## Perguntas`)
incorporadas ao corpo desta subseção. Os `(a definir)` das Regras de
Produto foram preenchidos com os valores decididos.

Complemento da revisão (2026-09-27): Task 13 criada para a rotina de
verificação de defasagem da versão pinada (Pergunta 7); Task 5 e
Checkpoint C2 marcados como satisfeitos em nível de plano; cabeçalho da
Fase 3, Task 10, Task 11, Task 12, rollback e tabela de riscos ajustados
ao estado decidido.

Revisão do plano (2026-09-27, achados 2, 3, 5, 6 e 7 do rev; Pergunta
12): Task 4 ganha o cenário do SEC-06 (evento nativo + `compress` na
mesma sessão; gate C1) e a observação passiva do hook do ai-memory;
Task 1 e C0 ganham a janela dos modelos do mapa e o gatilho do
`compaction.auto` nativo, com referência ao instrumento do SEC-05;
Task 12 materializa os limites calibrados no `dcp.jsonc`; Task 13
declarada procedimento manual; reflow na tabela da VALIDAÇÃO;
proteções removidas das Regras de Produto (Pergunta 12).

Re-verificação aplicada (2026-09-28, achados 8 e 9 do rev): premissa 4
resolvida pelo retorno do plugin local ai-memory (SEC-12 agora requisito
bloqueante ATIVO); Task 1 sem o agente `worker` (removido do repo em
2026-09-28, commit `e38bbc1`), com spawns via tool `task` do
`opencode-task-model@1.3.1` sobre os agentes especialistas do workflow e
mapa real de spawn por agente; executor do mapa atualizado para
`zai-coding-plan/glm-5.3-flash` (decisão do humano, 2026-09-28); linha
de risco do `allowSubAgents` reescrita para regressão em spawns da tool
`task`.

O plano cobre os pontos 1, 2 e 5 do insumo (inventário, escopo de ativação
e rollout com checkpoints). Os pontos 3 e 4 ficam como ganchos para os
agentes sec e qa, ao fim desta subseção.

#### Premissas verificadas (2026-09-27)

Confirmação dos fatos do devflow mais achados próprios:

1. OpenCode 1.18.32 (`opencode --version`), binário em `~/.opencode/bin`.
2. Plugins declarados no config canônico: `@slkiser/opencode-quota` e
   `opencode-task-model@1.3.1`. O OpenCode resolve as specs pelo cache
   `~/.cache/opencode/packages/`; os `node_modules` user-space têm só o
   SDK `@opencode-ai/plugin`. Nenhum pacote DCP em cache hoje.
3. MCP ativo: ai-memory, remote `127.0.0.1:49374`, declarado em
   `harness-conf/opencode.json`.
4. Plugin local ai-memory PRESENTE: discrepância RESOLVIDA pela
   realidade nova (2026-09-28). O `~/.config/opencode/plugins/ai-memory.ts`
   RETORNOU ao user-space (retorno confirmado pelo sec em 2026-09-28,
   com backup de 2026-09-27), com os hooks
   `experimental.session.compacting` e `session.compacted` ativos
   novamente. Ele entra na lista de transformações concorrentes
   (GANCHO-SEC) e o SEC-12 é agora requisito bloqueante ATIVO desde a
   Fase 1 (verificação explícita pré-piloto), deixando de ser
   condicional.
5. Materialização do config: o adapter grava `harness-conf/opencode.json`
   em `~/.config/opencode/opencode.json`, com cópia filtrada sem o bloco
   `mcp` quando o ai-memory não está provisionado
   (`src/opencode_config/harnesses/opencode.py`). Estado atual do
   user-space: arquivo regular sem o bloco `mcp`.
6. Semântica do DCP validada no README upstream (leitura de 2026-09-27;
   versões v3.1.9 a v3.2.4-beta0 coerentes entre si):
   - o plugin lê config própria `dcp.jsonc`, na ordem global
     (`~/.config/opencode/dcp.jsonc`), depois custom
     (`$OPENCODE_CONFIG_DIR`), depois projeto (`.opencode/`); cada nível
     sobrepõe o anterior; o OpenCode reinicia após mudança;
   - defaults: `compress.permission = "allow"`, `compress.mode =
     "range"`, `maxContextLimit = 100000`, `minContextLimit = 50000`,
     `nudgeFrequency = 5`, `iterationNudgeThreshold = 15`,
     `protectUserMessages = false`, `strategies.deduplication` e
     `strategies.purgeErrors` ligados, `manualMode.enabled = false`,
     `experimental.allowSubAgents = false`, `autoUpdate = true` (specs
     com versão fixa não entram no autoUpdate);
   - `compress.permission = "deny"` não registra a tool;
   - `modelMaxLimits` e `modelMinLimits` aceitam limite por
     `providerID/modelID`, em tokens absolutos ou percentual da janela;
   - o upstream recomenda reduzir os thresholds para modelos de janela
     menor.
7. Tensão de arquitetura: o `dcp.jsonc` global vive em user-space, fora
   da fonte de verdade do repo. RESOLVIDA (Pergunta 3, 2026-09-27):
   global via repo; o adapter estende o contrato `HarnessAdapter` para
   sincronizar `harness-conf/dcp.jsonc` até
   `~/.config/opencode/dcp.jsonc` (Tasks 6 e 7).

#### Regras de Produto

Valores decididos pelo humano em 2026-09-27 (Perguntas 3 a 11; emendas
da Pergunta 12 aplicadas na revisão do plano). Nenhum campo
`(a definir)` remanesce.

| Regra | Estado |
|---|---|
| `compress.permission` | `allow` já no spike (Pergunta 5); auditoria pós-fato no sqlite (QA-ACC-5); `deny` = rollback |
| `compress.mode` | `range` (Pergunta 4) |
| `compress.maxContextLimit` | `100000` no piloto; limites de produção por modelo calibrados no gate C4 (Pergunta 6) |
| `compress.minContextLimit` | `50000` no piloto; limites de produção por modelo calibrados no gate C4 (Pergunta 6) |
| `compress.protectUserMessages` | `false` (default; Pergunta 9 revertida pela 12; SEC-08 superado) |
| `compress.protectedTools` | REMOVIDO (Pergunta 12; histórico da Pergunta 4: `memory_query`, `memory_read_page`) |
| `compress.protectedFilePatterns` | REMOVIDO (Pergunta 12; histórico: `plan/**` do SEC-07, superado) |
| `experimental.allowSubAgents` | `true` já no piloto (Pergunta 8; decisão humana CONTRA recomendação; risco aceito) |
| versão do pacote | versão fixa, sem autoUpdate; defasagem manual (Task 13); bump com checklist SEC (Pergunta 7) |
| histórico persistido | o DCP não altera o histórico salvo; placeholders só no envio ao LLM (design upstream) |

#### Fase 0: Inventário e linha de base (ponto 1 do insumo)

Objetivo: fechar o inventário técnico e a base de comparação de tokens.

Task 1: concluir o inventário.
- Descrição: registrar versão do OpenCode, compatibilidade declarada do
  DCP com ela, plugins e resolução por cache, MCP servers, subagents em
  uso (spawns via tool `task` do plugin `opencode-task-model@1.3.1`
  com os agentes especialistas do workflow; o agente `worker` foi
  removido do repo em 2026-09-28, commit `e38bbc1`; registrar o mapa
  real de spawn por agente), transformações concorrentes (hooks do
  ai-memory, ativos no plugin local retornado) e em qual harness cada
  fluxo do workflow roda (OpenCode vs Copilot CLI, ressalva de escopo
  do insumo). Inclui a janela de contexto dos modelos do mapa
  (`zai-coding-plan/glm-5.3-flash` execução;
  `zai-coding-plan/glm-5.3` planejamento/revisão) e o gatilho efetivo
  da `compaction.auto` nativa para cada modelo (função da
  janela e do `reserved`); esses números são a base do instrumento do
  SEC-05 (verificado por construção no C3 e medido no C4) e da
  calibração de `modelMaxLimits`/`modelMinLimits` no C4 (Pergunta 6).
- Critérios de aceitação:
  - [x] inventário cobre versão, plugins, MCP, subagents e hooks;
  - [x] janela de contexto e gatilho do `compaction.auto` nativo
    registrados para todo modelo do mapa;
  - [x] estado do `plugins/ai-memory.ts` registrado (retorno de
    2026-09-28 confirmado; SEC-12 ativo);
  - [x] lista de transformações concorrentes e mapa de fluxos por
    harness entregues (entrada do GANCHO-SEC).
- Verificação: inspeção estática; resultado registrado nesta seção.
- Dependências: nenhuma.
- Arquivos: nenhum alterado.
- Escopo: S.

Task 2: replicar a linha de base de medição.
- Descrição: aplicar o método da Task 12 do ciclo vizinho (sqlite em
  `~/.local/share/opencode/opencode.db`, tabela `message`) numa sessão
  típica, registrando tokens por chamada antes e depois de `/compact`.
- Critérios de aceitação:
  - [x] números de tokens e payback registrados nesta seção;
  - [x] método replicável (comandos salvos).
- Verificação: consulta sqlite documentada.
- Dependências: nenhuma.
- Arquivos: nenhum alterado.
- Escopo: S.

Checkpoint C0 (gate de dados):
- Decisão: avançar à Fase 1 se o inventário estiver completo e sem
  incompatibilidade impeditiva conhecida — incluindo a janela de
  contexto dos modelos do mapa e o gatilho efetivo da
  `compaction.auto` nativa, insumos do instrumento do SEC-05 (por
  construção no C3, medido no C4) e da calibração de
  `modelMaxLimits`/`modelMinLimits` no C4; ajustar se houver lacuna;
  abortar o caminho global se a versão do OpenCode em uso for
  incompatível com o DCP sem workaround.

#### Fase 1: Spike em sandbox

Objetivo: validar o comportamento do DCP em ambiente isolado, sem tocar
na fonte de verdade do repo.

Task 3: instalar e revisar o pacote em ambiente de teste.
- Descrição: projeto de teste fora do repo, com ativação por nível
  projeto (`.opencode/dcp.jsonc`) ou config local, sem `--global`; spec
  com versão fixa.
- Critérios de aceitação:
  - [x] revisão de segurança do conteúdo instalado feita segundo a regra
    do repo (ler todo o conteúdo: prompt injection, comandos, URLs,
    exfiltração), com checklist do GANCHO-SEC;
  - [x] versão testada registrada.
- Verificação: artefato de revisão arquivado para o sec
  (`/tmp/opencode/dcp-spike/sec-review.md`; resumo nos Resultados da
  Fase 1).
- Dependências: C0.
- Arquivos: fora do repo.
- Escopo: M.

Task 4: validar semântica da tool e dos comandos.
- Descrição: confirmar em sessão descartável o registro da tool
  `compress`, os comandos `/dcp` e `/dcp-compress`, o disparo de nudges
  acima do threshold e o efeito de `manualMode`. Na MESMA sessão,
  exercitar o cenário do SEC-06: um evento nativo determinístico
  (`/compact` manual, mesmo caminho da compactação nativa) e um
  `compress` do DCP, registrando a ordem observada, o comportamento dos
  ranges `mNNNN`/`bN` após o evento nativo e a integridade do histórico
  no sqlite. Observação passiva (Pergunta 12, pedido do humano):
  registrar se o hook do ai-memory dispara (ou não) sobre a compressão
  do DCP, sem construir integração.
- Critérios de aceitação:
  - [x] evidência de cada item da descrição registrada;
  - [x] cenário do SEC-06 executado com ordem observada e integridade
    do contexto registradas (gate: C1); se o cenário não puder ser
    exercitado na sandbox, impeditivo registrado e verificação movida
    para o C4;
  - [x] observação passiva do hook do ai-memory registrada (disparou ou
    não sobre o `compress` do DCP), sem erro de sessão atribuável.
- Verificação: relato na subseção de resultados.
- Dependências: Task 3.
- Arquivos: fora do repo.
- Escopo: M.

Checkpoint C1 (gate técnico):
- Decisão: go se a tool opera, o cenário do SEC-06 (Task 4) tiver
  evidência registrada (ou impeditivo com verificação movida ao C4) e a
  revisão de segurança não levantar bloqueio; no-go devolve ao humano
  com as evidências.

#### Fase 2: Decisões de configuração (mediação humana)

Task 5: fechar as Perguntas 3 a 11 com o humano (mediação do devflow).
- Descrição: a engenharia fornece subsídio (resultados do spike,
  trade-offs registrados nas perguntas, dados da linha de base).
- Estado (2026-09-27): satisfeita em nível de plano; o humano antecipou
  as decisões no encerramento do planejamento. As Perguntas 3 a 11
  estão RESOLVIDAS na seção `## Perguntas` e incorporadas às Regras de
  Produto e às tasks desta fase em diante.
- Critérios de aceitação:
  - [x] todas as perguntas respondidas e registradas na seção
    `## Perguntas`.
- Dependências: nenhuma (decisões antecipadas pelo humano).
- Escopo: S.

Checkpoint C2 (gate de entrada da implementação):
- Decisão: a Fase 3 não inicia sem as respostas.
- Estado (2026-09-27): satisfeito em nível de plano; Perguntas 3 a 11
  RESOLVIDAS. A execução da Fase 3 segue condicionada à confirmação
  humana ("esperar para tudo").

#### Fase 3: Implementação no repo (TDD)

Tasks redigidas para a Pergunta 3 = opção (a), decidida pelo humano
(2026-09-27): global via repo. As Tasks 6 e 7 sincronizam o destino novo
no adapter; as Tasks 8 e 9 independem do destino.

Task 6: testes do novo destino de sync (TDD, testes primeiro).
- Descrição: suíte em `tests/harnesses/` cobrindo a sincronização de
  `harness-conf/dcp.jsonc` para o user-space no POSIX (materialização
  da strategy) e no Windows (cópia sincronizada), incluindo backup.
- Critérios de aceitação:
  - [x] testes novos escritos antes do código, falhando primeiro
    (evidência: ordem dos commits; executada por instância anterior e
    verificada em 2026-09-29);
  - [x] suíte `-m all` verde no ambiente corrente.
- Verificação: `.venv/bin/pytest -m all` (WSL/Linux) ou
  `.\.venv\Scripts\pytest.exe -m all` (Windows).
- Dependências: C2.
- Arquivos prováveis: `tests/harnesses/test_opencode_*.py`.
- Escopo: M.

Task 7: incorporar plugin e config canônica.
- Descrição: acrescentar a spec version-locked em
  `harness-conf/opencode.json` (array `plugin`), criar
  `harness-conf/dcp.jsonc` com as decisões da Fase 2 e estender o
  contrato `HarnessAdapter` com o destino novo.
- Critérios de aceitação:
  - [x] bootstrap materializa opencode.json e dcp.jsonc conforme a
    strategy do SO (coberto por testes nas duas strategies);
  - [x] `tests/lib/` atualizado se utilitários compartilhados mudarem
    (n/a: nenhum utilitário alterado);
  - [x] `tests/agents/test_workflow_consistency.py` sem achado novo
    (dentro do lote verde de 2026-09-29).
- Dependências: Task 6.
- Arquivos prováveis: `harness-conf/opencode.json`,
  `harness-conf/dcp.jsonc` (novo),
  `src/opencode_config/harnesses/opencode.py`, `tests/harnesses/`,
  `tests/lib/`.
- Escopo: M.

Task 8: atualizar a política de compactação.
- Descrição: reescrever a política D11 do `harness-conf/AGENTS.base.md`
  e a premissa 7 de `docs/workflow-agentes-dev.md`. No OpenCode, a tool
  `compress` passa a mecanismo automatizado preferido; `/compact` vira
  fallback; a auto-compaction nativa permanece rede de segurança. No
  Copilot CLI nada muda (compactação host-level; recuperação por re-seed
  em chat novo), conforme a ressalva de escopo do insumo.
- Critérios de aceitação:
  - [ ] textos coerentes entre si e com o comportamento configurado;
  - [ ] passagem pelo humano (regra do repo para workflow e agentes).
- Dependências: Task 7.
- Arquivos prováveis: `harness-conf/AGENTS.base.md`,
  `docs/workflow-agentes-dev.md`.
- Escopo: S.

Task 9: documentação e ADR.
- Descrição: sugerir o ADR-0010 registrando a decisão (DCP como
  mecanismo preferido de compactação no OpenCode; extensão do contrato
  do adapter), com asserção executável conforme a convenção do repo;
  atualizar a seção de dependências do `README.md` e checar o
  `docs/README.md` por artefatos de spec deste domínio.
- Critérios de aceitação:
  - [ ] ADR com contexto, alternativas e asserção executável;
  - [ ] README com o que muda para o humano (nudges, tool compress);
  - [ ] registro do artefato criado e sua localização nesta seção.
- Dependências: Task 8.
- Arquivos prováveis: `docs/adr/0010-*.md`, `README.md`,
  `docs/README.md`.
- Escopo: M.

Checkpoint C3 (gate de qualidade):
- Decisão: avançar ao piloto só com suíte verde, diff revisado e docs
  coerentes; qualquer falha devolve à construção.

#### Fase 4: Piloto controlado (canário)

Task 10: ativar e rodar um ciclo real.
- Descrição: aplicar o bootstrap na máquina do humano, confirmar a
  materialização (opencode.json, dcp.jsonc, cache do pacote) e rodar um
  ciclo de construção típico deste repo com o DCP ativo e
  `experimental.allowSubAgents = true` (Pergunta 8: decisão humana
  CONTRA a recomendação de eng/sec/qa; risco experimental aceito).
- Critérios de aceitação:
  - [ ] evidência de ativação (config materializada, tool visível);
  - [ ] sessão longa sem erro atribuível ao DCP;
  - [ ] fluxo multiagente exercitado (spawns via tool `task`), com
    sessões filhas validadas no QA-ACC-3.
- Dependências: C3.
- Escopo: S.

Task 11: medir e comparar.
- Descrição: medir tokens por chamada antes e depois de `compress` com o
  método sqlite da linha de base; comparar com o resultado do `/compact`
  (-37% na Task 12 do ciclo vizinho); observar frequência de nudges e
  coerência dos sumários.
- Critérios de aceitação: definidos pelo GANCHO-QA (QA-ACC-1 a 5;
  literais numéricos endossados na Pergunta 11). Destaques:
  - [ ] queda de contexto por evento e na média (QA-ACC-1);
  - [ ] prompt cache preservado, sem loop de nudge (QA-ACC-2 e 4);
  - [ ] fluxo multiagente sem regressão, sessões filhas validadas via
    `session.parent_id` (QA-ACC-3; Pergunta 8).
- Dependências: Task 10.
- Escopo: M.

Checkpoint C4 (gate de adoção):
- Decisão: adotar, ajustar thresholds ou reverter. Critério explícito:
  se os tokens não caírem ou houver instabilidade, rollback; não afinar
  às cegas.

#### Fase 5: Rollout geral e fechamento

Task 12: generalizar, documentar e fazer a retro.
- Descrição: aplicar os limites calibrados de produção por modelo
  (Pergunta 6, decididos no C4 com os dados medidos) em
  `harness-conf/dcp.jsonc` (`modelMaxLimits`/`modelMinLimits`), com
  commit e bootstrap (materialização no user-space); se a Pergunta 3
  for global, comunicar o que muda nos demais projetos (nudges, tool
  compress); consolidar a documentação; registrar lições para o ciclo
  vizinho de otimização de custo.
- Critérios de aceitação:
  - [ ] limites de produção por modelo aplicados no
    `harness-conf/dcp.jsonc`, com commit e bootstrap executado;
  - [ ] documentação final coerente (README, AGENTS.base.md, ADR);
  - [ ] itens pendentes em backlog (ex.: pin da spec do quota plugin,
    risco aceito pré-existente citado pelo sec).
- Dependências: C4.
- Arquivos prováveis: `harness-conf/dcp.jsonc`.
- Escopo: S.

Task 13: verificar defasagem da versão pinada (Pergunta 7).
- Descrição: rotina periódica comparando a versão pinada na spec de
  `harness-conf/opencode.json` com a versão corrente do registry npm e
  com a resolvida no cache `~/.cache/opencode/packages/@tarquinen/`;
  emitir relatório de defasagem para decisão humana sobre bump. Bump é
  nova importação: checklist SEC reexecutado (SEC-04 e item 9 do
  checklist do sec) antes de trocar a spec; sem autoUpdate. Natureza
  (achado 6 do rev): procedimento MANUAL documentado no plano, SEM
  script no repo, pelo princípio de simplicidade do humano (Pergunta
  12); se um script um dia se tornar imprescindível, a regra do repo
  (toda evolução funcional cria testes) exige a suíte correspondente
  na mesma mudança.
- Critérios de aceitação:
  - [ ] procedimento manual registrado (comandos salvos no plano) e
    primeira execução com resultado arquivado;
  - [ ] relatório com versão pinada, versão do registry, versão do
    cache e veredito (em dia ou defasada);
  - [ ] bump, se decidido pelo humano, com checklist SEC reexecutado e
    aprovado antes da troca da spec.
- Verificação: relatório registrado nesta seção; inspeção da spec no
  config canônico.
- Dependências: C4.
- Arquivos: nenhum alterado na verificação; bump altera
  `harness-conf/opencode.json` (nova importação).
- Escopo: S.

Checkpoint C5 (gate de fechamento):
- Decisão: encerrar com o humano; pendências viram backlog.

#### Rollback (a partir da Fase 3)

1. Remover a spec do array `plugin` em `harness-conf/opencode.json`.
2. Remover o `dcp.jsonc` gerenciado e o destino do adapter com seus
testes (Pergunta 3 = global via repo; simetria do QA-RB-3).
3. Rodar o bootstrap e reiniciar o OpenCode.
4. Limpeza opcional do cache `~/.cache/opencode/packages/`.

Não há dado a migrar: o histórico persistido nunca foi alterado
(placeholders só no envio ao LLM).

#### Riscos conhecidos e mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Hooks ai-memory + nudges DCP no mesmo pipeline | sessão instável, sumário duplicado | Task 4; GANCHO-SEC |
| `allowSubAgents` experimental | regressão em spawns da tool `task` | decisão humana: `true` no piloto (nota) |
| AGPL-3.0 | obrigação de distribuição se houver código derivado | análise no GANCHO-SEC |
| autoUpdate sem versão fixa | comportamento muda sem aviso | spec version-locked + rotina de defasagem (Task 13) |
| DCP + `compaction.auto` nativo juntos | interação perto do limite | nativa segue como rede de segurança (Task 8) |
| ganho restrito ao OpenCode | expectativa errada no Copilot | mapa de fluxos na Task 1; ressalva na Task 8 |

Nota de risco (Pergunta 8): o humano decidiu `allowSubAgents = true` já no
piloto, CONTRA a recomendação de eng/sec/qa. Risco experimental aceito; a
Pergunta 12 mantém a decisão (é funcional, não mecanismo de proteção). A
mitigação é a validação por sessão filha (`session.parent_id`) no critério
do qa (QA-ACC-3).

#### Ganchos para especialistas

GANCHO-SEC (ponto 3 do insumo): preenchido pelo sec na subseção
`### Segurança (sec)`, ao fim desta seção de planejamento.

GANCHO-QA (ponto 4 do insumo): preenchido pelo qa na subseção
`### Testes (qa)`, ao fim desta seção de planejamento.

Complexidade total estimada: L. A ordem de execução segue os checkpoints;
nenhuma task da Fase 3 ou seguinte roda antes de C2.

### Evidências (eng-software) — REVISÃO DO PLANO

- [x] Achado 2: Task 4 com o cenário do SEC-06 (evento nativo +
      `compress` na mesma sessão; ordem e integridade; gate C1) e com a
      observação passiva do hook do ai-memory (Pergunta 12)
- [x] Achado 3: Task 1 e C0 com a janela dos modelos do mapa e o gatilho
      do `compaction.auto` nativo; referência ao instrumento do SEC-05
      (por construção no C3, medido no C4) como base da calibração
- [x] Achado 5: Task 12 com aplicação dos limites calibrados por modelo
      no `harness-conf/dcp.jsonc`, com commit e bootstrap
- [x] Achado 6: Task 13 declarada procedimento manual documentado, sem
      script no repo (princípio da Pergunta 12)
- [x] Achado 7: reflow da linha da tabela em `## VALIDAÇÃO` para
      ≤ 120 colunas
- [x] Pergunta 12: `protectedTools` e `protectedFilePatterns` marcados
      como removidos; `protectUserMessages = false` (P9 revertida);
      `deny` como rollback mantido
- [ ] Correções de código aplicadas: nenhuma (ciclo plan-only)

### Resultados da Fase 0 (eng-software, 2026-09-28)

Execução das Tasks 1 e 2 da Fase 0 (CONSTRUÇÃO), com os retoques
textuais dos achados 12 e 13 da verificação final do rev aplicados
neste mesmo arquivo. Nenhum código do repo alterado; DCP não
instalado (fica para a Fase 1); nenhuma suíte executada. Leituras do
sqlite em modo SOMENTE LEITURA (`file:...?mode=ro`). Fontes de
evidência: `opencode --version`; config canônico
`harness-conf/opencode.json`; user-space `~/.config/opencode/`;
cache `~/.cache/opencode/` (`packages/` e `models.json`, fonte
models.dev); binário `~/.opencode/bin/opencode` (extração das
funções de `SessionCompaction` do 1.18.32); sqlite
`~/.local/share/opencode/opencode.db` (leitura); registry npm e
README upstream do DCP (consulta web de 2026-09-28);
`docs/workflow-agentes-dev.md`. Checagem do `docs/README.md`: nenhum
artefato de spec deste domínio é exigido na Fase 0 (ADR fica para a
Task 9; README dependências muda em fase futura).

#### Task 1: inventário (concluído)

- **OpenCode**: `1.18.32`; binário `~/.opencode/bin/opencode`
  (185 MB, build 2026-09-21). Evidência: `opencode --version`.
- **Compatibilidade do DCP com 1.18.32**: peer dependency
  `@opencode-ai/plugin >=1.4.3` (registry npm; latest `3.1.15`,
  publicado 2026-08-16); o README upstream não declara teto de
  versão do OpenCode; release notes citam compatibilidade com
  OpenCode 1.17.10 (TUI/OpenTUI 0.4.x). `1.18.32 >= 1.4.3`:
  compatível, sem workaround necessário. Notas de risco: (a) a issue
  upstream 507 registrou incompatibilidade de packaging (3.1.9 com
  imports ESM sem extensão × loader Node ESM do OpenCode 1.14.x,
  pós-refactor BunProc→arborist), corrigida no 3.1.10 via tsup,
  reforça o pin com versão fixa (SEC-04); (b) o README direciona
  quem começa agora para o sucessor "Sleev"; o DCP "remains
  available" para OpenCode, e a desaceleração do upstream é risco de
  manutenção, não incompatibilidade impeditiva.
- **Plugins declarados e resolução no cache**: `@slkiser/
  opencode-quota` (spec sem pin, comportamento `@latest`) resolve
  `3.10.1` no cache (`@slkiser/opencode-quota@latest`); 
  `opencode-task-model@1.3.1` (pinado) resolve no cache
  `opencode-task-model@1.3.1`. Nenhum pacote `@tarquinen/` no cache
  (DCP ausente, coerente com a Fase 0). `node_modules` user-space:
  SDKs `@opencode-ai/plugin` + `@opencode-ai/sdk` e dependências
  transitivas (effect, zod, msgpackr etc.); sem pacote DCP.
- **MCP servers**: `ai-memory`, remote `http://127.0.0.1:49374/mcp`,
  `enabled: true`; único bloco `mcp` do config canônico
  (`harness-conf/opencode.json:12-18`).
- **Subagents em uso**: spawns via tool `task` do
  `opencode-task-model@1.3.1` (injeção de `model`/`reasoning`).
  Agentes disponíveis em `harness-conf/agents/`: analista,
  aws-analista, curador-produto, dba, devflow, eng-software, front,
  qa, rev, revisor-historia, sec, smart-planner. SEM `worker`
  (removido em 2026-09-28, commit `e38bbc1`, junto com `revisor.md`).
  Mapa real de spawn: `devflow` spawna os especialistas por fase
  (premissa 1 do workflow); especialistas não spawnam agentes; o
  humano pode chamar qualquer agente diretamente; o modelo de cada
  spawn é aplicado pelo plugin de task (premissa 7): flash na
  execução, glm-5.3 na revisão. Sessões filhas confirmadas no sqlite
  (`parent_id` preenchido; sessões flash filhas com 50-82 steps no
  período recente).
- **Hooks do ai-memory**: plugin local PRESENTE
  (`~/.config/opencode/plugins/ai-memory.ts`, 34.372 bytes,
  2026-09-28 06:00; backup `ai-memory.ts.bak-1790555475` de
  2026-09-27 21:31). Eventos escutados: `session.compacted` (l. 607)
  e `experimental.session.compacting` (l. 650). Item confirmado na
  lista de transformações concorrentes (SEC-12 ativo desde a
  Fase 1).
- **Mapa de fluxos por harness**: o workflow de agentes suporta duas
  plataformas (`docs/workflow-agentes-dev.md`, "Interação
  agente-humano por plataforma"): OpenCode spawna via Subagentes
  (tool `task`); Copilot CLI via `task(agent_type=...)`; devflow
  media em ambas. O ciclo DCP corre no OpenCode (sessões zai no
  sqlite do OpenCode; config materializado em
  `~/.config/opencode/`). O Copilot CLI está materializado pelo
  bootstrap (`~/.copilot/` com AGENTS.md, agents, plugins), sem
  registro de fluxo deste workflow rodando nele no período. Ressalva
  de escopo do insumo: o ganho do DCP vale apenas onde o fluxo roda
  OpenCode; partes do workflow que rodarem no Copilot seguem sem
  compactação acionável pelo agente (preservada na Task 8).
- **Janela de contexto dos modelos do mapa** (cache
  `~/.cache/opencode/models.json`, fonte models.dev; confirmados em
  `opencode models`): `zai-coding-plan/glm-5.3-flash` (execução) e
  `zai-coding-plan/glm-5.3` (planejamento/revisão):
  `limit.context = 1.000.000`, `limit.output = 131.072`. Nem o
  provider nem o config declaram `limit.input` ou `outputTokenMax`.
- **Gatilho efetivo da `compaction.auto` nativa (1.18.32)**: extraído
  do binário (`SessionCompaction.isOverflow`): com `compaction.auto`
  ativo (nosso config), dispara quando
  `(tokens.total || input+output+cache.read+cache.write) >= vn(model)`,
  onde `vn(model) = limit.input ? max(0, limit.input - reserved) :
  max(0, limit.context - maxOutputTokens)` e `maxOutputTokens =
  min(limit.output, outputTokenMax||32000) || 32000` (constante
  `OUTPUT_TOKEN_MAX = 32000`; default do `reserved` sem config:
  `min(20000, maxOutputTokens)`). Para os DOIS modelos do mapa (sem
  `limit.input`; `outputTokenMax` não configurado): gatilho =
  1.000.000 - 32.000 = **968.000 tokens** de contexto total. O
  `reserved: 10000` do config NÃO participa do gatilho desses
  modelos (só afeta modelos com `limit.input` declarado). Sanidade:
  pico máximo observado no banco no período = 235.679 tokens, muito
  abaixo do gatilho, coerente com ZERO compactações automáticas
  registradas.
- **Leitura para o SEC-05 e a calibração (P6/C4)**: o default
  `maxContextLimit` (100.000) fica muito abaixo do gatilho nativo
  (968.000) para os dois modelos: pass por construção já com os
  defaults. Atenção para a calibração: as medianas das sessões flash
  filhas (spawns) já operam em ~86k-117k, acima ou próxima do
  default de 100k; os `modelMaxLimits`/`modelMinLimits` de produção
  devem considerar a faixa operacional medida (números na Task 2).

#### Task 2: linha de base (concluída)

- **Baseline do ciclo vizinho LOCALIZADA e REPRODUZIDA no banco
  atual**: sessão `sunny-eagle`
  (`ses_f345d5cf7ffeBFsiBoVJtvYCqm`; `zai-coding-plan/glm-5.3`,
  variante `max`; 240 steps; 2026-09-23). Cinco eventos de
  compactação nativa (queda ≥ 30% entre steps consecutivos): step 32
  (121.108→42.610, -64,8%), steps 90-91 (97.510→56.068→34.737),
  steps 167-168 (174.784→110.997→35.991) e step 213
  (88.776→33.536; patamar 55.509 no segundo step seguinte, após o
  re-warm do cache). O evento do step 213 (2026-09-23 03:04 UTC)
  reproduz a baseline citada no plano: 88.776 ≈ ~88,6k; patamar
  55.509 ≈ ~55,4k; -37,5% ≈ -37%. Payback medido: custo do evento
  (output+reasoning do step da compactação) = 4.913 tokens; ganho =
  33.267 até o patamar (55.240 até o vale) → payback 0,15 chamada
  (0,09 até o vale), mesma ordem de grandeza do ~1,1 citado (método
  `message` do ciclo vizinho).
- **Comparabilidade com o mapa novo**: os dois modelos do mapa têm a
  MESMA janela (1.000.000) e o MESMO gatilho nativo (968.000); a
  régua (contexto efetivo por chamada =
  input+cache.read+cache.write, usage do provider) é a mesma.
  Ressalva registrada: o `/compact` medido ocorreu no `glm-5.3`
  (hoje modelo de REVISÃO); NENHUMA sessão flash registra
  compactação nativa (`time_compacting` NULL em todas; nenhuma
  mensagem user `/compact` no banco desde 2026-09-18). A baseline
  herdade é comparável como régua, não como amostra do modelo de
  execução.
- **Baseline própria no modelo de execução (flash)**: sessões pai
  com ≥ 10 steps desde 2026-09-18: `crisp-otter`
  (`ses_f1ff26dabffetztAvrgo`; 53 steps): pico 80.977, mediana
  50.969, cache hit de regime (≥ 10 steps após warm-up de 3) =
  98,18%; `swift-falcon` (13 steps): pico 32.091, mediana 30.557,
  cache hit 62,91% (sessão curta, warm-up domina). Sessões filhas
  flash (spawns via tool `task`, ≥ 50 steps): picos 108k-171k,
  medianas 86k-117k (quiet-forest 170.662/109.331; misty-falcon
  141.771/116.850; quick-cabin 124.486/106.572; clever-lagoon
  131.716/102.120; quiet-falcon 108.498/86.145). Sessões pai
  glm-5.3 (revisão): picos 143k-236k. Baseline do QA-ACC-2: taxa de
  referência de regime = 98,18% (flash, sessão longa) / 94,63%
  (glm-5.3, sunny-eagle).
- **Leitura para o piloto**: com os defaults do DCP (100k/50k), o
  `compress` dispararia dentro da faixa operacional já observada no
  flash (medianas filhas ~86k-117k; pico pai 81k), bem antes do
  gatilho nativo (968k), coerente com o desenho do SEC-05 e com a
  necessidade de amostragem do C4 (P10: risco de não cruzar o
  threshold é baixo no regime de spawns).

Comando salvo (replicável; sqlite em modo somente leitura):

```python
import sqlite3, os, json
con = sqlite3.connect("file:" + os.path.expanduser(
    "~/.local/share/opencode/opencode.db") + "?mode=ro", uri=True)
cur = con.cursor()
# serie de contexto por chamada (steps step-finish) de uma sessao:
rows = cur.execute("""
SELECT p.time_created, p.data
FROM part p JOIN message m ON p.message_id = m.id
WHERE p.session_id = :sid
  AND m.data LIKE '%"role":"assistant"%'
  AND p.data LIKE '%step-finish%'
ORDER BY p.time_created""", {"sid": "ses_f345d5cf7ffeBFsiBoVJtvYCqm"})
serie = []
for t, d in rows:
    tk = json.loads(d)["tokens"]
    ctx = tk["input"] + tk["cache"]["read"] + tk["cache"]["write"]
    serie.append((t, ctx, tk))
# eventos de compactacao nativa: queda >= 30% entre steps consecutivos
# payback: custo(output+reasoning do step do evento) / ganho do evento
# cache hit de regime: sum(cache.read) / sum(input+read+write),
# sobre os steps >= 4 (warm-up de 3) e em janela >= 10 steps
```

Sessões de referência: `sunny-eagle`
`ses_f345d5cf7ffeBFsiBoVJtvYCqm` (eventos nativos, glm-5.3);
`crisp-otter` `ses_f1ff26dabffetztAvrgo` (pai flash típico).

#### Gate C0 (veredito)

Avaliado contra a condição pass/fall registrada na subseção
`### Testes (qa)`:

- Inventário da Task 1 sem campo "desconhecido": versão (1.18.32);
  plugins e resolução por cache (quota 3.10.1; task-model 1.3.1);
  MCP (ai-memory); subagents via tool `task` com mapa real de spawn
  por agente especialista e sem o `worker` removido; transformações
  concorrentes com o plugin ai-memory confirmado PRESENTE (SEC-12
  ativo); janela de contexto dos modelos do mapa (1.000.000 para
  ambos) e gatilho efetivo do nativo (968.000); mapa por harness.
  **Atendido.**
- Compatibilidade do DCP (README upstream) cobre o OpenCode em uso:
  peer `>=1.4.3` < 1.18.32, sem teto declarado; sem
  incompatibilidade impeditiva, sem workaround. **Atendido.**
- Números da Task 2 registrados com comandos salvos: **Atendido.**
- (fall): nenhum campo vazio; nenhuma incompatibilidade sem
  workaround. **Não configurado.**

**Veredito C0: PASS.** A Fase 1 (spike em sandbox) está liberada pelo
gate, nos termos da autonomia da Pergunta 13 (gates operacionais
fluem; push e exclusões seguem exigindo humano).

### Evidências (eng-software) — CONSTRUÇÃO (Fase 0)

- [x] Task 1: inventário completo, 10 campos com evidência, sem
      campo "desconhecido"
- [x] Task 2: baseline do ciclo vizinho localizada e reproduzida no
      banco atual; baseline própria no flash extraída; comando
      replicável salvo nesta subseção
- [x] Achado 12 do rev: desfecho da P8 anotado na nota do sec
      (texto histórico preservado)
- [x] Achado 13 do rev: remissões ao mapa definitivo acrescentadas
      no contexto do devflow e na Pergunta 1
- [x] Gate C0: PASS (condição pass/fall da subseção do qa)
- [x] sqlite em modo somente leitura; DCP não instalado; nenhuma
      suíte executada (inventário, não construção de código)
- [ ] Testes novos: 0 (nenhum código produto alterado na Fase 0)
- [ ] Análise estática: n/a (sem código alterado)
- [ ] Gate de refatoração: n/a (sem código; plano sem mudança)

### Resultados da Fase 1 (eng-software, 2026-09-28)

Execução das Tasks 3 e 4 (spike em sandbox) e avaliação do gate C1.
Nenhum código do repo alterado; nenhuma suíte executada (ferramenta de
terceiro, sem código produto). O `~/.config/opencode` real ficou SEM
nenhuma escrita; a única presença em user-space é o cache de pacotes
(`~/.cache/opencode/packages/@tarquinen/`), previsto no plano como local
de resolução.

Sandbox: `/tmp/opencode/dcp-spike/` (FORA do repo). Isolamento efetivo:
`XDG_CONFIG_HOME=/tmp/opencode/dcp-spike/xdg` (recoloca para dentro do
sandbox TANTO o config global do OpenCode QUANTO o layer global do DCP;
achado de isolamento: o plugin cria
`<$XDG_CONFIG_HOME>/opencode/dcp.jsonc` default quando ausente, pois o
layer global do DCP usa XDG e não `OPENCODE_CONFIG_DIR`),
`OPENCODE_CONFIG_DIR=/tmp/opencode/dcp-spike/xdg/opencode`; plugin local
ai-memory copiado byte a byte para `plugins/` do sandbox (para os hooks
existirem); data dir (`~/.local/share/opencode/`, auth e sqlite) intacto.
Ativação por nível projeto (`.opencode/dcp.jsonc`), nunca `--global`.
Headless: `opencode serve` (127.0.0.1:4987, `--print-logs --log-level
DEBUG`) dirigido pela API: `POST /session`, `POST /session/{id}/message`
(prompt síncrono com `model` explícito `zai-coding-plan/glm-5.3-flash`),
`POST /session/{id}/command` (`/dcp`, `/dcp-compress`) e
`POST /session/{id}/summarize` (compactação nativa).

#### Task 3: instalação e revisão (concluída)

- Instalação: spec fixa `@tarquinen/opencode-dcp@3.1.15` declarada no
  config do sandbox (array `plugin`); `autoUpdate: false` no
  `dcp.jsonc` do sandbox. Resolvida em
  `~/.cache/opencode/packages/@tarquinen/opencode-dcp@3.1.15/` (wrapper
  + `node_modules/@tarquinen/opencode-dcp`). Versão testada: 3.1.15.
- Checklist dos 9 itens do sec: EXECUTADO; artefato arquivado em
  `/tmp/opencode/dcp-spike/sec-review.md` (destino: leitura do sec).
  Resumo: (1) integridade do cache = registry (package-lock; diff byte
  a byte vs tarball npm); (2) SEM scripts pre/postinstall (só
  dev/build/test; `prepublishOnly` roda no publish do autor); 6
  dependências diretas legítimas, sem typosquat aparente; (3) ZERO
  `child_process`/`exec`/`spawn`/`eval`/`new Function`/`require` no
  bundle e nas fontes; ZERO `import(` dinâmico; escritas locais
  confinadas (config home, data home, logs); `process.env` lê só
  XDG_CONFIG_HOME, XDG_DATA_HOME, OPENCODE_CONFIG_DIR,
  OPENCODE_SERVER_PASSWORD/USERNAME (auth local do host); (4) egress:
  schema no raw.githubusercontent é STRING de editor, não fetchada; 1
  fetch real condicionado (`registry.npmjs.org/{pkg}/latest` em
  `update.ts`, envia só o nome do pacote), dispara no startup APENAS
  com `autoUpdate != false`; runtime medido com `autoUpdate: false` e 4
  compressões: ZERO conexões externas do processo; nenhuma telemetria;
  (5) sessão circula in-memory; persistência local só de estado
  operacional (IDs, tokens, tópicos, âncoras); sem conteúdo de mensagem
  gravado; (6) nudges são strings estáticas locais, com override só de
  arquivos locais; (7) sem caminho de self-update com spec fixa
  (`isAutoUpdatableSpec("3.1.15") = false`); com `autoUpdate: false` nem
  a verificação roda; (8) proveniência registrada no artefato e aqui;
  (9) bump = nova importação (checklist reexecutável; template no
  artefato).
- RESSALVA (não bloqueante sob a decisão vigente; condição
  OBRIGATÓRIA): o fetch de versão do item 4 existe no código e rodaria
  no startup com `autoUpdate` true, violando a barra SEC-02. A P7 já
  decidiu "sem autoUpdate". A Task 7 DEVE materializar
  `"autoUpdate": false` no `harness-conf/dcp.jsonc` canônico;
  recomenda-se teste na Task 6 que fixe essa propriedade. Com
  `autoUpdate` true, o item 4 do checklist vira bloqueante.

#### Task 4: semântica em sessão descartável (concluída)

As quatro evidências do C1, o cenário SEC-06 e a observação passiva,
todos na sandbox (sessões `ses_f15d216f8ffeBwLW4BIpuj8fXd` e
`ses_f159fc698ffe1goOKojQi6TSGv`):

- Tool `compress` registrada: o modelo a lista entre as tools; parts
  `compress` no sqlite; permissão avaliada no log do server
  (`evaluated permission=compress pattern=* action.permission=co...`,
  gate `allow` da P5, sem pausa de confirmação).
- Comandos operam headless via `POST /session/{id}/command`:
  `/dcp stats` entregou o painel como mensagem (barra de contexto,
  "-38K removed, +438 summary"); `/dcp-compress <foco>` executou
  compressão manual completa. RESSALVA: após o comando roubado pelo
  plugin (hook de chat.message), o endpoint `command` do HOST devolve
  `UnknownError` no server headless (fluxo de conclusão de comando do
  OpenCode sem TUI; o conteúdo foi entregue; não é erro do DCP).
- Nudge acima do threshold: instrumento = thresholds REDUZIDOS
  20k/10k no `dcp.jsonc` do sandbox (documentado; o piloto usa os
  defaults 100k/50k, P6/P10). Evidência: 1 `contextLimitAnchors` no
  state file do DCP e o agente chamou `compress` 2x espontaneamente
  após cruzar 20k. Quedas medidas na série step-finish
  (input+cache.read+cache.write): 34.450 para 22.798 (-33,8%) e
  35.423 para 10.313 (-70,9%).
- `manualMode.enabled = true` (2ª sessão, server reiniciado): contexto
  subiu 9.811 para 63.930 com ZERO chamadas de `compress`, zero nudges
  e sem state file (caminho automático suprimido); `/dcp-compress`
  manual funcionou (1 bloco, 55.483 tokens comprimidos). Auto desliga,
  manual segue operando.
- SEC-06 (mesma sessão): ordem observada = 3 `compress` do DCP (2 por
  nudge + 1 por comando) e depois o summarize NATIVO via API
  (23:27:10-23:27:34 UTC; mensagem assistant com `summary = true`
  criada) e, por fim, `compress` do DCP pós-nativo: executou SEM erro;
  os ranges `mNNNN` foram reenumerados no espaço pós-nativo (bloco 1
  reancorado em m0001..m0002, 444 tokens). Integridade: sqlite com 21
  mensagens, prompt original presente, state file coerente. Sem
  corrupção; o modo de falha 2 (referências órfãs) NÃO se
  materializou.
- Observação passiva do hook ai-memory (P12; ponto de partida do
  SEC-12): os hooks disparam SOMENTE no evento nativo. DB do ai-memory
  (`~/.local/share/ai-memory/db/memory.sqlite`): 2 registros
  `pre-compact` (23:27:10 e 23:27:34, exatamente a janela do summarize
  nativo) e NENHUM nos 4 `compress` do DCP (22:42:06, 22:42:32,
  23:26:42, 23:29:11). Confere com a análise estática: o bundle do DCP
  não emite eventos de compactação nativa. Sem duplo sumário no
  caminho DCP; sem erro de sessão atribuível.
- Limitações registradas: (a) `session.time_compacting` permaneceu NULL
  mesmo após o evento nativo headless; o instrumento do qa (SEC-05
  medido, QA-ACC) deve considerar o detector alternativo "mensagem
  assistant com `summary = true`" quando a sessão não for TUI
  (registrar no C4); (b) o painel TUI do `/dcp` (modal) não é
  exercitável headless; o que opera headless é o comando `/dcp` com
  subcomandos de texto.

Comandos salvos (replicáveis; mesma ordem do spike):

```bash
# sandbox (FORA do repo); server headless isolado por XDG:
cd /tmp/opencode/dcp-spike && XDG_CONFIG_HOME=$PWD/xdg \
  OPENCODE_CONFIG_DIR=$PWD/xdg/opencode \
  opencode serve --port 4987 --hostname 127.0.0.1 \
  --print-logs --log-level DEBUG
# sessao e prompt (model obrigatorio no body):
curl -s -X POST http://127.0.0.1:4987/session -d '{}' \
  -H 'content-type: application/json'
curl -s -X POST http://127.0.0.1:4987/session/$SID/message \
  -H 'content-type: application/json' \
  -d '{"model":{"providerID":"zai-coding-plan",
      "modelID":"glm-5.3-flash"},
      "parts":[{"type":"text","text":"..."}]}'
# comando /dcp-compress e compactacao NATIVA:
curl -s -X POST http://127.0.0.1:4987/session/$SID/command \
  -H 'content-type: application/json' \
  -d '{"command":"dcp-compress","arguments":"foco"}'
curl -s -X POST http://127.0.0.1:4987/session/$SID/summarize \
  -H 'content-type: application/json' \
  -d '{"providerID":"zai-coding-plan",
      "modelID":"glm-5.3-flash"}'
```

#### Gate C1 (veredito)

Avaliado contra a condição pass/fall registrada na subseção
`### Testes (qa)`:

- Quatro evidências da Task 4: tool registrada (**atendida**); `/dcp` e
  `/dcp-compress` operam (**atendida**, com a ressalva do endpoint
  `command` do host headless, não atribuível ao DCP); nudge acima do
  threshold (**atendida**: 1 âncora + 2 compress espontâneos); sessão
  sem erro atribuível ao DCP (**atendida**).
- Cenário SEC-06 com ordem observada e integridade registradas:
  **atendido** na sandbox (sem fallback ao C4).
- Checklist SEC de 9 itens: executado, ZERO bloqueantes sob a decisão
  P7 (spec fixa, sem autoUpdate); 1 ressalva com condição obrigatória
  para a Task 7 (`"autoUpdate": false` no `dcp.jsonc` canônico).
- (fall): nenhuma evidência ausente; nenhum bloqueio SEC.

**Veredito C1: PASS.** Fase 3 (implementação no repo) liberada nos
termos da autonomia da Pergunta 13, com a condição da ressalva do
item 4 do checklist a materializar na Task 7.

### Evidências (eng-software): CONSTRUÇÃO (Fase 1)

- [x] Task 3: instalação em sandbox com spec fixa e `autoUpdate: false`;
      checklist SEC de 9 itens executado e arquivado
      (`/tmp/opencode/dcp-spike/sec-review.md`); versão 3.1.15
- [x] Task 4: 4 evidências + SEC-06 (ordem e integridade) + observação
      passiva do hook (dispara só no nativo) + manualMode (auto off,
      manual on)
- [x] Gate C1: PASS (condição da ressalva: `autoUpdate` false na Task 7)
- [x] Isolamento: `~/.config/opencode` intocado; repo intocado (exceto
      este plano); instalação fora do repo; nenhuma exclusão
- [ ] Testes novos: 0 (spike de ferramenta de terceiro; sem código
      produto alterado)
- [ ] Análise estática: varredura do pacote (bundle + fontes) feita;
      lint do repo n/a (sem código alterado)
- [ ] Gate de refatoração: n/a (sem código; plano sem mudança de
      desenho)

### Resultados da Fase 3 (eng-software, 2026-09-29, Tasks 6 e 7)

Verificação, completamento e fechamento das Tasks 6 e 7. Os artefatos
foram implementados por instância anterior que não persistiu resultado
no plano; esta passagem verificou o trabalho, rodou a suíte e registrou
o estado. Worktree limpo ao fechar: a alteração alheia citada pelo
devflow (`plan/plano-revisao-comunicacao-planejamento-agentes.md`) não
está mais pendente no repositório (nada a isolar; nada commitado nesta
passagem além deste plano).

#### Commits verificados (Tasks 6 e 7)

- `7ccc3ae` `test(harnesses): cobre sincronizacao do dcp.jsonc`: suíte
  nova `tests/harnesses/test_opencode_dcp.py` (168 linhas, 5 testes).
- `dc55da7` `feat(harness): incorpora plugin dcp com config canonica`:
  `harness-conf/dcp.jsonc` (novo), spec `@tarquinen/opencode-dcp@3.1.15`
  no array `plugin` do `harness-conf/opencode.json`, destino novo nas
  duas strategies (`src/opencode_config/harnesses/opencode.py`) e
  fixtures de teste atualizadas (`tests/adapters/
  test_opencode_adapter.py`, `tests/harnesses/test_opencode.py`).
- Ordem TDD verificável pelo histórico: commit de testes precede o
  commit de código. A execução "falhando primeiro" não é reproduzível
  retroativamente; aceita pela ordem dos commits e pela cobertura
  registrada abaixo.

#### Conteúdo da suíte nova (Task 6)

`test_canonical_dcp_jsonc_pins_decided_configuration` fixa no artefato
canônico toda a decisão da Fase 2: `allow`, `range`, 100000/50000,
`protectUserMessages = false`, ausência de `protectedTools` e
`protectedFilePatterns` (Pergunta 12), `allowSubAgents = true` (P8) e
`autoUpdate = false` (condição obrigatória da ressalva SEC do C1).
`test_canonical_opencode_json_declares_pinned_dcp_plugin` fixa a spec
pinada (P7/SEC-04). Os três testes restantes cobrem a materialização:
symlink POSIX (`requires_symlink`), cópia sincronizada Windows com
backup e idempotência Windows.

#### Simetria do contrato (Task 7)

- Extensão feita nas tuplas de destinos das strategies do OpenCode
  (`_POSIX_DESTINATIONS` e `_WINDOWS_DESTINATIONS`), forma canônica de
  variação por SO; a interface `HarnessAdapter` em si não mudou.
- `src/opencode_config/lib/` sem alteração nos dois commits: sem
  duplicação de cópia sincronizada ou backup. Grep por "dcp" em `src/`
  e `adapters/` só acerta `harnesses/opencode.py`.
- Copilot sem o destino: `src/opencode_config/harnesses/copilot.py` e
  `adapters/copilot-cli/` não mencionam dcp; nenhum dos dois commits
  toca o harness Copilot. CONFIRMADO: `dcp.jsonc` é destino exclusivo
  do OpenCode, coerente com a ressalva de escopo do insumo.

#### Suíte completa e análise estática (verificação)

- `.venv/bin/pytest -m all` (WSL/Linux, 2026-09-29): **940 passed,
  31 deselected, 0 failed** em 222,41s. Nenhuma falha preexistente a
  registrar. `test_workflow_consistency.py` dentro do lote verde.
- `.venv/bin/ruff check src tests`: sem achados.

#### Estado parcial do C3 (checklist do plano)

- [x] suíte `-m all` exit 0 no ambiente corrente;
- [x] Task 7 com checklist concluído (ver Commits e Simetria acima);
- [ ] Tasks 8 (política de compactação) e 9 (ADR-0010 + README)
  pendentes, fora do escopo desta passagem;
- [ ] revisão da construção pelo rev pendente;
- [ ] materialização no user-space (bootstrap na máquina do humano)
  pendente, prevista para a Fase 4 (Task 10).

C3 segue ABERTO. Próximo passo: Task 8, depois Task 9, depois revisão
da construção.

#### Evidências (eng-software) — CONSTRUÇÃO (Fase 3, Tasks 6-7)

- [x] Testes novos: 5 em `tests/harnesses/test_opencode_dcp.py`; commit
  de teste precede o commit de feat (primeiro-fail aceito pela ordem do
  histórico; implementação da instância anterior, verificada nesta)
- [x] Testes totais: 940 passed, 31 deselected, 0 failed
  (`.venv/bin/pytest -m all`, WSL, 2026-09-29)
- [x] Análise estática: ruff sem achados
- [x] Regressão incremental: suíte completa executada na verificação;
  verde
- [x] Gate de refatoração: cenário "nada muda"; sem impacto no plano
  (extensão por tupla de destinos, padrão existente)
- [x] Worktree limpo; alteração alheia citada não mais pendente;
  nenhum commit novo de código nesta passagem

### Segurança (sec)

Análise de segurança do ponto 3 do insumo, registrada em 2026-09-27 na
fase PLANEJAMENTO. Método: inspeção estática do plano, da config canônica
(`harness-conf/opencode.json`), do user-space (`~/.config/opencode/`), do
cache de pacotes (`~/.cache/opencode/packages/`) e do código instalado do
plugin quota. Nenhuma suíte executada; nenhum arquivo além deste plano
foi alterado. Decisões permanecem com o humano (Perguntas 3 a 9).

Revisão do plano (2026-09-27, achados 1 a 3 do rev): SEC-07, SEC-08 e
SEC-09 reclassificados como SUPERADOS/REVERTIDOS por decisão humana
(Perguntas 5, 9 e 12; anotações nos próprios itens); SEC-05 ganha
instrumento de verificação; SEC-06 ganha gate (C1) e evidência; nota
sobre hook ai-memory × DCP nas transformações concorrentes. Textos
originais preservados como histórico com anotação de desfecho.

Re-verificação (2026-09-28, achados 9 e 11 do rev): SEC-12 reescrito de
condicional para requisito ATIVO (o plugin local ai-memory retornou ao
user-space, confirmado por inspeção: `ai-memory.ts` de 2026-09-28 com
backup de 2026-09-27); item "Hooks ai-memory" das transformações
concorrentes atualizado (conflito potencial volta a existir); rótulo
"risco 4 do insumo" da supply chain corrigido (o ponto 3 do insumo
lista três riscos; supply chain é extensão do sec). Conteúdo técnico
dos requisitos 1 a 11 inalterado.

#### Requisitos de segurança

- **SEC-01** (bloqueante). Revisão de importação do pacote DCP pelo
  checklist abaixo, antes de qualquer ativação (alimenta o gate C1).
  Risco: código de terceiros lê a sessão inteira antes de auditoria.
- **SEC-02** (bloqueante). Egress remoto zero no DCP: nenhum endpoint de
  rede além de recursos locais do OpenCode. Risco: exfiltração do
  conteúdo da sessão (prompts, saídas de tools, segredos em contexto).
- **SEC-03** (bloqueante). Pacote sem scripts de instalação
  (pre/postinstall), ou com scripts revisados linha a linha. Risco:
  execução arbitrária no host no momento do install.
- **SEC-04** (bloqueante). Spec com versão fixa e reexecução do checklist
  a cada bump (bump é nova importação; regra do repo). Risco:
  comportamento ou egress muda sem aviso.
- **SEC-05** (bloqueante para adoção). Thresholds do DCP posicionados
  para disparar antes do `compaction.auto` nativo (DCP primário; nativo
  como rede de segurança). Risco: duplo sumário concorrente.
  Instrumento de verificação (achado 3 do rev), em dois níveis:
  - Por construção, na Fase 3 (gate C3): comparar no config materializado
    os thresholds do DCP (`maxContextLimit`/`minContextLimit` e, após a
    calibração da Pergunta 6, `modelMaxLimits`/`modelMinLimits`) com o
    gatilho do nativo, função da janela do modelo e do `reserved`; os
    valores vêm do inventário da Task 1, que passa a incluir a janela
    dos modelos do mapa e o gatilho do nativo. Pass: threshold do DCP
    abaixo do gatilho nativo para todo modelo do mapa.
  - Medido, no piloto (Fase 4, gate C4): cruzar no sqlite o timestamp de
    cada `compress` com `session.time_compacting` (atribuição já
    definida no instrumento do qa). Pass: todo `compress` precede
    qualquer evento nativo na mesma sessão; evento nativo antes do DCP
    é violação.
- **SEC-06** (bloqueante para adoção; verificado no C1). Task 4 exercita
  um evento nativo e um `compress` na mesma sessão, registrando ordem
  observada e integridade do contexto. Risco: corrupção por ordem não
  coordenada. Gate declarado (achado 2 do rev): C1, na Fase 1, para
  falhar barato antes de qualquer implementação no repo; a engenharia
  incorpora o passo na Task 4. Evidência que satisfaz: sessão
  descartável com um evento nativo determinístico (`/compact` manual,
  mesmo caminho da compactação nativa) e um `compress` do DCP, com
  registro da ordem observada, do comportamento dos ranges `mNNNN`/`bN`
  após o evento nativo (modo de falha 2) e da integridade do histórico
  no sqlite. Se o cenário não puder ser exercido na sandbox, registrar
  o impeditivo e mover a verificação para o C4 (medição no piloto).
- **SEC-07** (SUPERADO; texto histórico). `protectedFilePatterns` cobrindo
  `plan/**`. Risco: sumarização de artefatos de estado do workflow.
  Desfecho (Pergunta 12, 2026-09-27): mecanismo removido por decisão
  humana (princípio de simplicidade; sem rede de proteção, comportamento
  padrão do DCP; recuperação por reconsulta ao ai-memory). Risco
  residual aceito pelo humano; o requisito deixa de existir.
- **SEC-08** (SUPERADO; texto histórico). `protectUserMessages = true`
  (Pergunta 9). Risco: sumário descarta instruções e decisões do humano
  silenciosamente. Desfecho (Pergunta 12, 2026-09-27): REVERTIDO para
  `false` (default do upstream) por decisão humana; o modelo pode
  trabalhar sobre resumo das falas antigas, com recuperação por
  reconsulta ao ai-memory. Risco residual aceito pelo humano; o
  requisito deixa de existir.
- **SEC-09** (SUPERADO; texto histórico). Permission gate `ask` no spike
  e no início do piloto (input para a Pergunta 5). Risco: compressões
  com sumário incoerente passam sem auditoria humana. Desfecho
  (Pergunta 5, 2026-09-27): `allow` desde o spike, decidido pelo humano;
  auditoria pós-fato pelo sqlite (caminho do QA-ACC-5), aplicável
  também ao spike; `deny` segue como rollback instantâneo. A
  recomendação `ask` permanece como discordância registrada, sem
  efeito executável.
- **SEC-10** (bloqueante se violado). Proibir vendoring ou derivação de
  código do DCP no repo sem decisão humana explícita. Risco: obrigação
  de distribuição copyleft (AGPL).
- **SEC-11** (bloqueante se violado). Nunca commitar conteúdo de
  `~/.cache/opencode/packages/` (tarball, mirror offline, dist). Risco:
  distribuição do programa AGPL pelo repo.
- **SEC-12** (bloqueante para adoção; ATIVO desde a Fase 1). O plugin
  local ai-memory RETORNOU ao user-space (achado 9 da re-verificação,
  2026-09-28) e a condição do condicional original está disparada.
  Antes do piloto (Fase 4), revalidar a interação dos hooks
  (`experimental.session.compacting`/`session.compacted`) com o DCP,
  usando a observação da Task 4 como ponto de partida e elevando-a a
  verificação explícita pré-piloto. O que verificar: (a) os hooks
  disparam ou não sobre um `compress` do DCP; (b) duplo sumário (hook
  e DCP atuando sobre a mesma compressão/sessão); (c) integridade da
  sessão (histórico íntegro no sqlite; sem erro atribuível). Risco:
  hooks reagindo a compressões do DCP.

#### Transformações concorrentes (risco 1 do insumo)

Inventário do pipeline verificado em 2026-09-27 (item "Hooks ai-memory"
atualizado em 2026-09-28 após mudança paralela no user-space, achado 9
da re-verificação):

- **Hooks ai-memory** (`experimental.session.compacting`/`compacted`):
  plugin local PRESENTE novamente
  (`~/.config/opencode/plugins/ai-memory.ts`; retorno de 2026-09-28,
  achado 9 da re-verificação; constava ausente na inspeção de
  2026-09-27, com o diretório vazio). Papel: disparam no ciclo de
  compactação NATIVO. Conflito com DCP: potencial novamente; o risco
  de duplo sumário volta a existir (SEC-12, requisito ativo).
- **ai-memory MCP** (`127.0.0.1:49374`): declarado na config canônica.
  Papel: servidor MCP externo; não transforma prompt. Conflito:
  nenhum conhecido.
- **`@slkiser/opencode-quota`**: instalado no cache. Papel: diagnóstico
  de uso/tokens (toast/TUI); faz fetch a APIs de provedores. Conflito:
  não altera conteúdo do prompt; leituras de token podem misturar
  valores pré e pós-placeholder.
- **`opencode-task-model@1.3.1`**: instalado no cache. Papel: intercepta
  a tool `task` (injeta model/reasoning). Conflito: só via subagents
  (Pergunta 8).
- **`compaction.auto` + `prune` nativos**: ativos (`auto: true`,
  `prune: true`, `reserved: 10000`). Papel: resume e poda perto do
  limite da janela, no caminho nativo. Conflito: gatilho independente
  com threshold próprio; ordem não coordenada.

Onde há ordem definida:
- Por design do OpenCode, os hooks de compactação pertencem ao caminho
  NATIVO (`/compact` e `compaction.auto`). A tool `compress` do DCP é uma
  transformação de request feita pelo plugin, fora desse ciclo, e o
  histórico persistido não é alterado (placeholders só no envio ao LLM).
- A resolução de plugins e a injeção da tool ocorrem no startup; nudges
  entram no prompt por requisição quando o limite é ultrapassado.

Onde a ordem é indefinida (validar na Task 4):
- se os hooks ai-memory disparam (ou não) sobre uma compressão do DCP;
- qual transformação prevalece quando DCP e `compaction.auto` atuam na
  mesma sessão entre limites próximos;
- comportamento dos ranges `mNNNN`/`bN` quando `prune` remove mensagens
  que eles referenciam.

Nota sobre hook ai-memory × DCP (Pergunta 12, pedido do humano): a Task 4
observa PASSIVAMENTE se o hook do ai-memory dispara sobre uma compressão
do DCP, apenas registrando o resultado; nenhuma integração nova é
construída. Fundamento: o hook segue necessário apenas para o `/compact`
nativo, que é destrutivo (reescreve o histórico); o DCP não destrói
histórico (placeholders só no envio ao LLM), logo não há resgate a fazer
no momento da compressão. Com o retorno do plugin local (2026-09-28),
a observação alimenta o SEC-12, agora requisito ATIVO com verificação
explícita pré-piloto.

Modos de falha mapeados:
1. Duplo sumário: nativo resume o histórico e o DCP comprime ranges do
   resultado; perda acumulada ou crescimento do contexto (classe do bug
   anomalyco/opencode#17557 citado no insumo).
2. Referências órfãs: `prune` remove mensagens apontadas por ranges do
   DCP; compress falha ou substitui o bloco errado.
3. Loop de nudge: compress rejeitado (range inválido) e o nudge insiste;
   o contexto cresce em vez de reduzir.
4. Divergência armazenado vs enviado: o sqlite guarda o histórico
   completo; a requisição sai com placeholders. Depuração e métricas
   precisam distinguir os dois (input para o GANCHO-QA: o método da Task 2
   só vê efeito do DCP se ler o usage reportado pelo provider, não o
   tamanho do histórico armazenado).

Mitigações: SEC-05 (thresholds; input para a Pergunta 6), SEC-06, SEC-12
(ativo); monitorar loop de nudge como critério de rollback no piloto
(GANCHO-QA).

#### Licença AGPL-3.0-or-later (risco 2 do insumo)

Fatos deste repo:
- O repo distribui config, scripts, skills e docs próprios; não tem
  LICENSE no topo e não contém código do DCP.
- A incorporação planejada declara apenas a string de spec
  (`@tarquinen/opencode-dcp@X.Y.Z`) em `harness-conf/opencode.json` e,
  se a Pergunta 3 optar por (a), um `dcp.jsonc` autoral. Quem baixa o
  pacote é o OpenCode, do registry npm, em cada máquina.

Quando a obrigação dispara:
- AGPL-3.0 obriga quem distribui (conveyance) o programa ou obra
  derivada (cópias, modificações) e quem o oferece como serviço de rede
  (seção 13). Uso local pelo humano e mera referência por nome de pacote
  não disparam copyleft.
- Entendimento corrente: arquivo de config autoral lido em runtime não é
  obra derivada do programa que o consome. Não é garantia jurídica; se a
  intenção mudar, a decisão sobe ao humano.

O plano deve PROIBIR (sem decisão humana explícita, registrada):
- copiar código do DCP (ou do cache resolvido) para dentro do repo;
- importar módulos do DCP a partir do código Python do adapter (o adapter
  escreve strings de config; nada além disso);
- redistribuir o pacote pelo repo (tarball, mirror offline, dist).

O plano pode PERMITIR:
- declarar a spec versionada no config canônico;
- manter `harness-conf/dcp.jsonc` autoral versionado;
- uso local do plugin em qualquer máquina que rode o bootstrap.

Se um dia houver distribuição de obra derivada, aplicar AGPL na íntegra
(avisos de copyright, fonte correspondente, seção 13 quando couber).
Fora desse cenário, não há obrigação concreta neste ciclo.

#### Permission gate (risco 3 do insumo; input para a Pergunta 5)

Mapa atual: dois eixos de permissão coexistem. O eixo global
(`permission.*` no `opencode.json`; hoje com `permission.skill` em deny
quase total) e o eixo por agente (frontmatter dos agents, ex.: `sec` com
`edit/bash allow` e `task deny`). O gate do DCP (`compress.permission`)
é um TERCEIRO eixo, interno do plugin: não é coberto pelo mapa existente
nem pelos testes de consistência do repo.

Propriedades relevantes da tool `compress`:
- substitui o conteúdo visto pelo modelo por sumários escritos pelo
  próprio agente; o histórico fica íntegro no banco;
- o sumário pode descartar ressalvas, achados e instruções; com `allow`,
  nenhuma auditoria humana vê a substituição;
- com `ask`, cada compressão pausa por confirmação; em sessão autônoma
  longa vira ponto de espera frequente (nudge a cada 5 iterações acima do
  limite, default upstream).

Input técnico (texto histórico; foi o input da mediação da Pergunta 5):
- Original: no spike (Fase 1) e no início do piloto (Fase 4), `ask`, para
  o humano auditar as primeiras compressões (coerência do sumário,
  cobertura de decisões e achados).
- Original: `allow` ficaria aceitável quando o piloto demonstrasse
  sumários coerentes, `protectUserMessages = true` (Pergunta 9) e
  `protectedFilePatterns` cobrindo `plan/**` (SEC-07).
- Desfecho (Perguntas 5, 9 e 12, 2026-09-27): `allow` desde o spike;
  `protectUserMessages = false`; `protectedFilePatterns` removido.
  Auditoria pós-fato pelo sqlite (caminho principal do QA-ACC-5).
- Vigente: toda troca de versão do pacote reavalia o gate (liga à
  Pergunta 7); `deny` (desregistro da tool) é rollback instantâneo, sem
  desinstalar.

#### Supply chain e revisão de importação (extensão do sec, sem item correspondente no insumo)

Barra de egress, com contraste: o quota plugin instalado faz 28 chamadas
`fetch` a APIs de provedores (nano-gpt, z.ai, deepseek, entre outras);
é a função dele, consultar saldo, e é o baseline aceito hoje. Para o DCP
a função não exige rede: a barra é ZERO endpoint remoto, e o conteúdo de
sessão nunca sai do processo (SEC-02).

Checklist obrigatório da Task 3 (artefato arquivado para o sec):
1. Localizar o pacote resolvido em `~/.cache/opencode/packages/
   @tarquinen/`; registrar versão exata e integridade disponível
   (package-lock do cache).
2. `package.json`: scripts pre/postinstall (presença é bloqueante sem
   justificativa revisável); dependências diretas: contagem, typosquat,
   estado de manutenção.
3. Varredura estática do dist e de todo código carregado:
   `child_process`/`exec`/`spawn`, `eval`/`new Function`, import
   dinâmico ofuscado, escrita de arquivos fora dos dirs do plugin,
   leitura de `process.env` (quais chaves e para quê).
4. Egress: enumerar todas as URLs e hosts (fetch, WebSocket, undici,
   http/https). Aceitável: nenhum remoto. Qualquer telemetria é
   bloqueante.
5. Conteúdo de sessão: confirmar por leitura que as mensagens circulam
   apenas in-memory; persistência restrita a estado operacional local;
   sem conteúdo em logs remotos ou em relatórios de erro.
6. Nudges: strings estáticas vindas do config local; nada de texto
   buscado remotamente (vetor de prompt injection).
7. autoUpdate: com spec fixa, verificar no código a ausência de caminho
   de self-update.
8. Proveniência: registro no plano (origem, versão, data, resultado da
   revisão), no padrão da regra do repo para importados.
9. Bump de versão é nova importação: reexecutar o checklist inteiro
   antes de atualizar a spec (input para a Pergunta 7).

Nota sobre a Pergunta 7: o plugin quota roda hoje com spec não fixada
(`@latest` no config; cache resolve 3.10.1). É risco aceito pré-existente
e não serve de precedente para o DCP; pin do quota pode virar backlog
à parte, fora do escopo deste ciclo.

Nota sobre a Pergunta 8 (texto HISTÓRICO; desfecho anotado em
2026-09-28): segurança concorda com `false` para
`experimental.allowSubAgents` no piloto. Subagents (worker com reasoning
max, tool `task`) geram sessões filhas; expor transformação experimental
a elas amplia a superfície sem ganho medido. `true` só após ciclo
dedicado, com o checklist reexecutado para a versão corrente.
Desfecho: a Pergunta 8 foi decidida `true` pelo humano (2026-09-27,
CONTRA as recomendações de eng/sec/qa; item 8 da seção
`## Perguntas`), e o agente `worker` foi removido do repo em
2026-09-28 (commit `e38bbc1`); os spawns correntes usam a tool `task`
sobre os agentes especialistas do workflow. Risco experimental aceito
pelo humano; a recomendação `false` permanece como discordância
registrada, sem efeito executável (mesmo padrão do SEC-09).

Superfície de dados (resumo): o plugin lê a sessão completa (prompts,
saídas de tools, eventuais segredos de contexto) e produz sumários que
seguem ao LLM do provider, como já segue o contexto original. O risco
acrescido não é o LLM ver o sumário; é egress a host de terceiro e
persistência fora do previsto. Daí a SEC-02 e o item 5 do checklist.

#### Roteiro manual de segurança (Fases 1 e 4, se autorizadas)

Spike (Fase 1, Tasks 3 e 4):
- [ ] checklist de importação executado e arquivado (9 itens acima);
- [ ] gate `allow` confirmado (Pergunta 5): compress executa sem pausa
      de confirmação; auditoria pós-fato pelo sqlite comparando cada
      bloco original com o sumário produzido (mesmo método do QA-ACC-5);
- [ ] sessão sem erro atribuível ao DCP.

Piloto (Fase 4):
- [ ] histórico completo preservado no sqlite após compress (método da
  Task 2);
- [ ] auditoria pós-fato dos sumários (método do QA-ACC-5), com atenção
  especial a instruções e decisões do humano (risco residual do SEC-08
  revertido; substitui o antigo item de conteúdo protegido `plan/**`,
  removido na Pergunta 12);
- [ ] sem loop de nudge (contagem de ocorrências registrada);
- [ ] nenhum egress remoto novo atribuável ao DCP (verificação a definir
  com o humano; ex.: inspeção de conexões do processo).

#### Verificação de artefatos de documentação

Checagem contra o `docs/README.md`: nenhum artefato de spec de segurança
exige criação nesta fase. A spec de testes de segurança existente cobre
código produto do repo; o DCP não é código produto. O ADR fica a cargo da
Task 9 (engenharia), com input de segurança disponível nas seções acima.

### Evidências (sec) — PLANEJAMENTO

- [x] Requisitos analisados: 12 (SEC-01 a SEC-12); 11 bloqueantes (7
      condicionais à adoção, à violação ou ao retorno do plugin local),
      1 melhoria
- [ ] Correções aplicadas: nenhuma (ciclo plan-only)
- [ ] Roteiro manual: 7 itens definidos para as Fases 1 e 4; execução
      depende de autorização do humano

### Evidências (sec) — REVISÃO DO PLANO

- [x] Achado 1 do rev tratado: desfecho da Pergunta 5 anotado no SEC-09,
      no "Input técnico" do Permission gate e no roteiro do spike
      (auditoria pós-fato pelo sqlite, caminho do QA-ACC-5)
- [x] Achados 2 e 3 do rev (coautoria): SEC-06 com gate C1 e evidência
      declarados; SEC-05 com instrumento por construção (C3) e medido
      (C4); passos na Task 4 e no inventário da Task 1 ficam com a
      engenharia
- [x] Reclassificações por decisão humana: SEC-07 e SEC-08 SUPERADOS
      (Pergunta 12), SEC-09 SUPERADO (Pergunta 5); textos preservados
      como histórico com anotação de desfecho
- [x] Nota hook ai-memory × DCP acrescentada (Pergunta 12): observação
      passiva na Task 4; hook necessário só para o `/compact` nativo
- [ ] Correções de código aplicadas: nenhuma (ciclo plan-only)

### Evidências (sec) — REVISÃO DO PLANO (2026-09-28)

- [x] Achado 9 do rev tratado: SEC-12 reescrito de condicional para
      requisito ATIVO (verificação explícita pré-piloto: disparo dos
      hooks sobre o `compress` do DCP, duplo sumário, integridade da
      sessão; ponto de partida = observação da Task 4); item "Hooks
      ai-memory" das transformações concorrentes atualizado (plugin
      presente novamente; conflito potencial); nota da Pergunta 12,
      linha de mitigações e cabeçalho da subseção alinhados
- [x] Achado 11 do rev tratado: rótulo "risco 4 do insumo" corrigido
      para "extensão do sec, sem item correspondente no insumo"
      (conferido: o ponto 3 do insumo lista três riscos e os rótulos
      "risco 1/2/3" apontam os subitens certos); conteúdo técnico
      inalterado
- [ ] Correções de código aplicadas: nenhuma (ciclo plan-only)

### Testes (qa)

Planejamento da validação do ponto 4 do insumo (critérios de aceite,
medição e rollback), registrado em 2026-09-27 na fase PLANEJAMENTO.
Nenhuma suíte foi executada. Foi feita inspeção estática read-only do
banco `~/.local/share/opencode/opencode.db` (schema e chaves de usage;
nenhum conteúdo de sessão copiado) para confirmar o instrumento de
medição. Execução depende de autorização humana nas Fases 1 e 4.

Revisão de encerramento (2026-09-27): decisões humanas das Perguntas 3
a 11 incorporadas. QA-ACC-3 reescrito para `allowSubAgents = true`
(Pergunta 8); QA-ACC-5 com auditoria pós-fato pelo sqlite como caminho
principal (Pergunta 5, gate `allow`); procedimento do piloto, critérios
de aborto e desfechos anotados nas perguntas. Mudança de spec registrada
aqui, conforme planejamento (tests-as-spec).

Correção da re-verificação (2026-09-28, achados 8 e 10 do rev): o agente
`worker` foi removido do repo (commit `e38bbc1`, 2026-09-28; executores
passam a ser os agentes especialistas diretamente, modelo
`zai-coding-plan/glm-5.3-flash`) e o plugin local ai-memory RETORNOU ao
user-space (SEC-12 agora bloqueante ATIVO). Emendas: QA-ACC-3 reescrito
para spawns de agentes especialistas via tool `task` (spec substituída:
"≥ 1 do agente `worker`" e "modelo do frontmatter" → modelo chamado na
task, verificável em `session.model` da filha); QA-ABT-4 reescrito
("sessão filha fora do modelo chamado" substitui "worker fora do modelo
do frontmatter"); passos 6 e 7 do procedimento do piloto sem `worker`;
enumeração do C0 alinhada ao inventário novo (sem `worker`; plugin
ai-memory como item confirmado presente; janela dos modelos e gatilho
do nativo, já acrescentados pelo eng). Mudança de spec registrada aqui
(tests-as-spec).

#### Instrumento de medição (confirmado por inspeção de 2026-09-27)

Fonte: sqlite `~/.local/share/opencode/opencode.db`. Estrutura verificada:

- `message.data` (role=assistant): objeto `tokens` no formato
  `{total, input, output, reasoning, cache: {read, write}}`, além de
  `cost`, `modelID`, `providerID`;
- `part` type=`step-finish`: mesmo objeto `tokens` por step (uma
  requisição ao provider por step); `part` type=`tool` registra cada
  chamada de tool (incluída uma futura `compress`, com timestamp);
- `session`: agregados `tokens_input/output/reasoning/cache_read/
  cache_write`, `cost`, `time_compacting` (ciclo NATIVO), `parent_id`
  (sessão filha de subagent) e `model`.

Definições operacionais:

- contexto efetivo por chamada = `input + cache.read + cache.write`
  (tamanho do prompt enviado ao provider; `total` soma isso com `output`
  e `reasoning`);
- taxa de acerto de cache = `cache.read / (input + cache.read +
  cache.write)`;
- série da sessão = parts `step-finish` ordenadas por `time_created`
  (granularidade por requisição, isola o primeiro step pós-compress);
  para comparar com a linha de base do ciclo vizinho, usar `message`
  (mesma fonte e agregado do método validado);
- provider zai reporta `cost`=0: critérios medidos em tokens, sem
  conversão monetária neste ciclo.

Ajuste obrigatório do método herdado (modo de falha 4 do sec): o DCP não
altera o histórico persistido; placeholders existem só na requisição. A
medição do efeito usa SEMPRE o usage reportado pelo provider, nunca o
comprimento do texto armazenado. O painel do plugin quota não é fonte de
verdade (leituras podem misturar valores pré e pós-placeholder).

`session.time_compacting` distingue compactação nativa (`/compact`,
`compaction.auto`) de compressão do DCP: cruzar as séries para atribuir
cada queda de contexto ao mecanismo certo.

#### Critérios de aceitação do piloto (Fase 4, Task 11)

Formato: lista de critérios com threshold sobre série de medição, e não
Gherkin, por serem condições numéricas sobre séries de dados; desvio à
convenção de specs executáveis proposto ao humano na revisão do plano.
Literais numéricos são valores de veredito (Pergunta 11). Origem: ponto
4 do insumo; referência de linha de base = `/compact` nativo, -37%
(~88,6k para ~55,4k tokens/chamada), payback ~1,1 chamada (Task 12 do
ciclo vizinho, 2026-09-23).

- **QA-ACC-1 — queda de contexto após `compress`** (fonte: série
  step-finish da sessão do piloto):
  - por evento: `(P0−P1)/P0 ≥ 20%`, sendo P0 o último step-finish
    antes da tool `compress` e P1 o primeiro depois;
  - média dos eventos ≥ 37% (paridade com `/compact` nativo);
  - payback ≤ 3 steps: menor k com `k·(P0−P1) ≥` custo do evento
    (`output + reasoning` dos steps entre o nudge e o fim do
    compress).
- **QA-ACC-2 — prompt cache não degradado** (fonte: `cache.read`/
  `cache.write` por step):
  - em regime estável (≥ 10 steps sem compress): taxa média de acerto
    ≥ 90% da taxa baseline da Task 2;
  - após cada compress: recuperação a ≥ 90% do baseline em ≤ 2 steps;
  - fall: abaixo disso por ≥ 3 steps consecutivos.
- **QA-ACC-3 — subagents sem regressão** com `allowSubAgents = true`
  (Pergunta 8; decisão humana CONTRA recomendação de eng/sec/qa, risco
  aceito; as sessões filhas da tool `task` AGORA são processadas pelo
  DCP; fonte: session/message das filhas, via `session.parent_id`):
  - ≥ 2 spawns via tool `task` de agentes especialistas do workflow
    (ex.: eng-software, qa) com DCP ativo e `allowSubAgents = true`:
    100% concluem sem erro atribuível ao DCP;
  - a sessão filha (`session.parent_id`) executa com o modelo
    efetivamente passado na chamada da task (verificável em
    `session.model` da sessão filha);
  - eventos de `compress` em sessões filhas são ESPERADOS e medidos
    com a régua do QA-ACC-1: `(P0−P1)/P0 ≥ 20%` por evento, na série
    step-finish da própria filha (substitui o antigo "0 tools
    `compress` em sessões filhas", que pressupunha `false`);
  - sem crash ou corrupção nas sessões filhas.
- **QA-ACC-4 — nudges sem loop** (fonte: log de eventos do piloto):
  - ≥ 1 nudge observado acima de `maxContextLimit` (contagem
    registrada);
  - loop = ≥ 3 nudges consecutivos sem compressão eficaz entre eles
    (eficaz = QA-ACC-1 pass no evento); 0 loops no piloto;
  - após compressão eficaz, nudges cessam até novo cruzamento do
    limite.
- **QA-ACC-5 — coerência do sumário** (manual, pós-fato; gate `allow`
  decidido na Pergunta 5, sem auditoria no momento da compressão;
  fonte: histórico sqlite):
  - 100% dos eventos revisados (se > 5 eventos, amostra de 3): o
    sumário preserva decisões, achados e restrições de escopo dos
    blocos substituídos; o histórico íntegro no sqlite permite
    comparar cada bloco original com o sumário produzido;
  - veredito binário por evento, registrado.

Observações:

- QA-ACC-2 depende dos campos `cache.read/write`, confirmados na
  inspeção de hoje; se uma versão futura do OpenCode os remover, o
  critério vira não-testável e é reportado antes de C4 (sem proxy).
- O mínimo de 20% do QA-ACC-1 segue válido como régua mínima por evento;
  as proteções cuja perda de potencial ele contemplava foram removidas
  (Pergunta 12: `protectUserMessages = false`, P9 revertida;
  `protectedFilePatterns` removido; SEC-07/08 superados).
- QA-ACC-3 depende de `session.parent_id` e da série step-finish por
  sessão filha, ambos confirmados na inspeção de hoje; a régua do
  QA-ACC-1 nas filhas mede o contexto efetivo (usage do provider),
  como define o instrumento.
- QA-ACC-5 (Pergunta 5 decidida: gate `allow` desde o spike): a
  auditoria é pós-fato pelo histórico do sqlite, caminho principal; a
  variante com `ask` (auditar no momento da compressão) não se aplica;
  `deny` segue como rollback instantâneo.

#### Procedimento do piloto (baseline, intervenção, pós)

Baseline (Fase 0, Task 2):

1. Sessão típica sem DCP, no modelo de execução do mapa; exportar do
   sqlite a série de usage por chamada (comandos salvos no plano).
2. Registrar: pico pré-`/compact`, queda percentual, payback e a taxa
   de acerto de cache em regime estável (≥ 10 steps após warm-up de 3);
   esta taxa é o baseline do QA-ACC-2.
3. Guardar session_id e snapshot das contagens de mensagens (base do
   QA-RB-4).

Intervenção (Fase 4, Tasks 10-11):

4. Ativar conforme C3; confirmar materialização (config, cache do
   pacote) e tool `compress` visível.
5. Rodar ciclo real de construção típico do repo, com
   `experimental.allowSubAgents = true` (Pergunta 8) e
   `compress.permission = "allow"` (Pergunta 5; auditoria pós-fato
   pelo sqlite, QA-ACC-5).
6. Registrar durante a sessão: timestamp de cada nudge, de cada
   compress (ranges, duração), de cada spawn via tool `task` (agente
   especialista chamado e modelo passado) e de erros, nas sessões pai
   e filhas.
7. Amostragem mínima para fechar C4: ≥ 1 sessão com ≥ 2 eventos de
   compressão (senão, Pergunta 10); ≥ 10 steps entre compressões para
   regime de cache; ≥ 2 spawns via tool `task` de agentes
   especialistas (ex.: eng-software, qa), com eventos de compress
   das filhas medidos pela régua do QA-ACC-3; 100% dos sumários
   revisados (≤ 5 eventos; senão amostra de 3).

Pós:

8. Extrair as séries do sqlite; calcular QA-ACC-1 a 5; comparar com o
   baseline; registrar os números no plano (Task 11).
9. Comparabilidade com a linha de base: mesma fonte (sqlite), mesmo
   agregado (`input + cache.read + cache.write`), mesma máquina e
   modelo do mapa. Limitação declarada: `/compact` reescreve o
   histórico, o DCP não; a comparação vale porque ambas as métricas
   medem contexto efetivo processado pelo provider.

#### Rollback operacional

Contenção (primeiro passo, sem desinstalar): `compress.permission =
"deny"` e reiniciar; a tool fica desregistrada. Verificar: `compress`
ausente na nova sessão.

Remoção completa (passos 1-4 da engenharia) com verificação da
restauração do estado anterior:

- QA-RB-1: nova sessão pós-restart sem tool `compress` e sem resposta
  de `/dcp` e `/dcp-compress`.
- QA-RB-2: `harness-conf/opencode.json` sem a spec no array `plugin`;
  user-space sem `dcp.jsonc` gerenciado após o bootstrap.
- QA-RB-3: destino do adapter e testes removidos e `pytest -m all`
  verde no ambiente corrente (Pergunta 3 decidida: global via repo;
  simetria da Task 6).
- QA-RB-4: sqlite: sessões do piloto com contagem de mensagens idêntica
  ao snapshot do passo 3 e conteúdo de amostra íntegro (o DCP não
  escreve no histórico; qualquer divergência é achado).
- QA-RB-5: nova sessão típica com contexto por chamada e taxa de cache
  nos patamares do baseline da Task 2 (sem resíduo de transformação).
- QA-RB-6: `~/.cache/opencode/packages/@tarquinen/` removido (limpeza
  opcional); presença residual sem efeito: sem spec, o plugin não é
  resolvido.

Critérios de aborto do piloto (disparam contenção e rollback):

| ID | Gatilho |
|---|---|
| QA-ABT-1 | QA-ACC-1 falha em todos os eventos (nenhuma queda ≥ 20%) |
| QA-ABT-2 | loop de nudge (definição do QA-ACC-4) |
| QA-ABT-3 | erro de sessão atribuível ao DCP (crash, corrupção, sessão inutilizável) |
| QA-ABT-4 | regressão multiagente: spawn falha, sessão filha fora do modelo chamado ou filha com crash/corrupção |
| QA-ABT-5 | degradação sustentada de cache (fall do QA-ACC-2) |
| QA-ABT-6 | qualquer bloqueante SEC violado (encaminhar ao sec) |

Regra de ajuste (espelha o C4): uma única rodada de reajuste de
thresholds com hipótese documentada, se a falha for isoladamente de
threshold; segunda rodada sem verde → rollback (não afinar às cegas).

#### Condições pass/fall dos checkpoints C0-C5

Objetivação proposta pelo qa; não substitui a redação da engenharia.

- **C0** (pass): inventário da Task 1 sem campo "desconhecido" (versão;
  plugins e resolução por cache; MCP; subagents via tool `task`, com o
  mapa real de spawn por agente especialista e sem o `worker` removido
  em 2026-09-28; transformações concorrentes, com o plugin ai-memory
  confirmado PRESENTE no user-space, SEC-12 ativo; janela de contexto
  dos modelos do mapa e gatilho efetivo da `compaction.auto` nativa;
  mapa por harness); range de compatibilidade do DCP (README upstream)
  cobre o OpenCode em uso, ou workaround documentado; números da Task 2
  registrados com comandos salvos. (fall): qualquer campo vazio;
  incompatibilidade sem workaround.
- **C1** (pass): quatro evidências da Task 4 (tool registrada; `/dcp` e
  `/dcp-compress` operam; ≥ 1 nudge acima do threshold; sessão sem erro
  atribuível); checklist SEC de 9 itens com zero bloqueante.
  (fall): qualquer evidência ausente; bloqueio SEC.
- **C2** (pass): zero perguntas com estado ABERTA (3 a 11) na seção
  `## Perguntas`. (fall): qualquer ABERTA.
- **C3** (pass): `pytest -m all` exit 0 no ambiente corrente; revisão
  da construção sem achado bloqueante; Tasks 7-9 com checklists
  concluídos; materialização no user-space confirmada (spec no
  opencode.json; dcp.jsonc no destino). (fall): qualquer item pendente.
- **C4** (pass): QA-ACC-1 a 5 verdes na amostragem mínima. (fall):
  QA-ABT-1 a 6; ou falha só de threshold (uma rodada de ajuste);
  segunda rodada sem verde → rollback.
- **C5** (pass): Task 12 com checklist concluído; evidências QA
  persistidas no plano; procedimento de rollback validado (executado ou
  verificado por inspeção); pendências em backlog (decisão final do
  humano). (fall): pendências sem registro.

C2 já era objetivo (formalizado acima); C5 permanece decisão humana, com
a parte verificável explícita.

#### Inputs de validação para as perguntas (histórico + desfechos)

Texto original preservado como input da mediação; desfechos das
decisões humanas de 2026-09-27 (seção `## Perguntas`) anotados.

- P4 (modo): DECIDIDO `range`, SEM `protectedTools` (item 12 da seção
  `## Perguntas` removeu as proteções; desfecho emendado). Original: a
  validação só cobre `range` (semântica de IDs
  `mNNNN`/`bN` verificável); `message` é experimental e sem baseline
  comparável; se escolhido, exige ciclo de validação próprio.
- P5 (gate): DECIDIDO `allow` desde o spike; a auditoria pós-fato
  pelo sqlite vira o caminho principal do QA-ACC-5. Original: com
  `ask`, a auditoria do QA-ACC-5 acontece no momento da compressão
  (evidência natural, custo menor); com `allow`, é pós-fato pelo
  sqlite.
- P6 (thresholds): DECIDIDO defaults no piloto (100k/50k), com
  limites de produção por modelo calibrados no C4. Original: além do
  SEC-05 (disparar antes do nativo), o C4 exige ≥ 2 compressões
  exercitadas; com defaults (100k/50k), a sessão típica (pico ~88,6k
  na linha de base) pode não cruzar 100k em um ciclo só; ver
  Pergunta 10.
- P8 (subagents): DECIDIDO `true` já no piloto, CONTRA a recomendação
  registrada abaixo; o método por sessão filha (`session.parent_id`)
  exigido pela decisão está definido no QA-ACC-3 e roda no próprio
  piloto; se o piloto apontar regressão multiagente, o ciclo dedicado
  previsto na decisão trata o ajuste antes do rollout. Original: com
  `false`, o QA-ACC-3 valida não-interferência e conclusão dos
  spawns; com `true`, seria preciso método por sessão filha
  (`session.parent_id`) e ciclo dedicado. Endosso quantitativo à
  recomendação `false` no piloto.
- P10 (sessão longa): DECIDIDO sessão longa natural no piloto (opção
  a do qa), sem thresholds reduzidos; o risco registrado em P6 (não
  cruzar 100k em um ciclo) é aceito: sem eventos suficientes, C4 não
  fecha e a decisão volta ao humano.

#### Verificação de artefatos de documentação

Checagem contra o `docs/README.md`: nenhum artefato de spec de testes
exige criação nesta fase. A validação do DCP é de ferramenta de
terceiro (não código produto); as suítes por especialidade (backend,
segurança) permanecem como estão. Se a Pergunta 3 = (a) gerar código de
adapter, os testes dele já estão planejados na Task 6 (engenharia).
Nada criado além deste plano.

### Evidências (qa) — PLANEJAMENTO

- [x] Plano de testes: 5 critérios QA-ACC, 6 critérios de aborto,
      6 verificações de rollback e condições pass/fall para C0-C5
- [ ] Testes executados: 0 (ciclo plan-only; execução depende de
      autorização humana nas Fases 1 e 4)
- [ ] Cobertura: não se aplica (ferramenta de terceiro, sem baseline
      de cobertura)
- [ ] Cenários não cobertos: modo `message` (Pergunta 4, decidido
      `range`); Copilot CLI (ressalva de escopo do insumo)

## REVISÃO DO PLANO

Revisão integrativa solo do rev em 2026-09-27 (instância limpa; primeiro
contato com o ciclo). Objeto: plano completo (insumo, contexto adicional,
mapa de modelos, Perguntas 1-11, VALIDAÇÃO, PLANEJAMENTO eng/sec/qa).
Método: leitura integral (1131 linhas), checklist multi-eixo com skills de
domínio (security-and-hardening, tests-as-spec, documentation-and-adrs,
api-and-interface-design) e sanity check factual leve contra
`harness-conf/opencode.json` (plugins, `compaction.auto/prune/reserved`,
MCP ai-memory, `permission.skill`: tudo confere com o citado no plano).
Nenhuma suíte executada; nenhum arquivo além desta seção foi alterado.

**Veredito: APROVADO COM RESSALVAS**

### Cobertura do checklist

- Aderência ao insumo: 5/5 pontos cobertos. Inventário (Task 1 + premissas
  verificadas); escopo de ativação (P3 global via repo; P4 modo `range` +
  `protectedTools`; P6 thresholds com calibração no C4); riscos (GANCHO-SEC:
  transformações concorrentes, AGPL, permission gate, supply chain);
  validação (GANCHO-QA: QA-ACC-1 a 5 com instrumento sqlite declarado e
  confirmado por inspeção); rollout (Fases 0-5 com C0-C5 e pass/fall
  objetivos na subseção do qa).
- Decisões humanas respeitadas: P5 (`allow` desde o spike), P7 (Task 13 +
  bump como nova importação), P8 (`allowSubAgents = true` contra
  recomendação, com nota de risco e método por sessão filha no QA-ACC-3) e
  P4 (`range` + `protectedTools`) estão incorporadas em Regras de Produto,
  tasks e critérios QA. Ressalva apenas na subseção do sec (achado 1).
- Regras do repo: testes previstos para toda evolução funcional (Task 6
  TDD; Task 7 com `tests/lib/` e `test_workflow_consistency.py`); mudança
  em workflow/agentes com passagem pelo humano (Task 8); sincronia
  workflow↔agentes endereçada (Task 8 toca `AGENTS.base.md` e
  `docs/workflow-agentes-dev.md`); revisão de segurança de importação e
  proveniência (SEC-01, checklist de 9 itens); AGPL-3.0-or-later tratado
  com regime PROIBIR/PERMITIR (SEC-10/SEC-11).
- Executabilidade: C0-C5 com critério pass/fall objetivo; QA-ACC-1 a 5
  mensuráveis (fonte sqlite, definições operacionais, literais endossados
  na P11); rollback completo (contenção via `deny` + 4 passos de remoção +
  QA-RB-1 a 6); sem dependência circular (Fases lineares com gates);
  todas as tasks têm critério de aceitação; sem estouro de escopo (ciclo
  plan-only respeitado; inspeções foram read-only).
- Mudança de spec registrada conforme tests-as-spec: QA-ACC-3 reescrito
  para `allowSubAgents = true` com registro do critério substituído.

### Achados

Formato: `achado · ação · severidade` (bloqueante / importante / melhoria),
com responsável pela correção e localização exata (linhas da versão
original do plano, anteriores a esta seção).

1. Contradição P5 ↔ subseção sec: a Pergunta 5 decidiu
   `compress.permission = "allow"` desde o spike, mas SEC-09 (gate `ask` no
   spike e no início do piloto), o "Input técnico (sem decisão)" do
   Permission gate e o roteiro manual de segurança da Fase 1 ("gate `ask`
   confirmado a cada compress") seguem recomendando `ask` sem anotação de
   desfecho. Eng e qa registraram revisão de encerramento; a subseção do
   sec não. Risco: executor do roteiro da Fase 1 configurar `ask` contra
   decisão humana.
   · Ação: anotar o desfecho da P5 na subseção sec; reclassificar SEC-09
   como superado pela decisão; marcar o "Input técnico" como texto
   histórico; corrigir o item do roteiro manual do spike para a auditoria
   pós-fato pelo sqlite (caminho do QA-ACC-5). Discordância registrada é
   legítima como histórico; roteiro executável não pode contradizer a
   decisão.
   · Severidade: importante · Resp.: sec · Localização: `### Segurança
   (sec)`, SEC-09 (linhas 629-631), "Input técnico" do Permission gate
   (linhas 749-752) e Roteiro manual do spike (linha 814).

2. SEC-06 (bloqueante para adoção) atribui à Task 4 o cenário "um evento
   nativo e um `compress` na mesma sessão", mas a Task 4 (eng) não prevê
   esse passo: critérios de aceitação cobrem tool, comandos, nudges e
   `manualMode` apenas. O requisito fica sem passo executável e com gate
   ambíguo (Task 4 é Fase 1; classificação diz "adoção", que soa como C4).
   · Ação: incluir na Task 4 o cenário nativo + `compress` na mesma sessão
   (ordem observada e integridade do contexto), em coautoria com o sec;
   definir em qual gate o SEC-06 é verificado (C1 ou C4).
   · Severidade: importante · Resp.: eng-software · Localização: SEC-06
   (linhas 621-623) vs Task 4 (linhas 377-388).

3. Janela de contexto dos modelos do mapa e gatilho do `compaction.auto`
   nativo não constam do inventário (Task 1) nem do pass do C0. Sem esses
   números, SEC-05 (bloqueante para adoção: DCP dispara antes do nativo)
   fica sem instrumento de verificação e a calibração de
   `modelMaxLimits`/`modelMinLimits` no C4 perde referência explícita. O
   insumo (ponto 2) pede thresholds coerentes com o tamanho de contexto
   dos modelos usados.
   · Ação: acrescentar à Task 1 (e ao pass do C0) a janela dos modelos e o
   threshold do nativo; sec indica o instrumento de verificação do SEC-05
   nos gates (por construção ou medido no piloto).
   · Severidade: importante · Resp.: eng-software · Localização: Task 1
   (linhas 322-338), C0 do eng (linhas 352-356), SEC-05 (linhas 618-620),
   premissa 6 (linhas 292-293).

4. `protectedTools` fechado em `memory_query` e `memory_read_page` (P4), mas
   o ai-memory expõe outras tools de leitura (`memory_recent`,
   `memory_briefing`, `memory_explore`, `memory_read_session_observations`)
   cujos resultados também são "leituras recuperadas da wiki" e podem virar
   sumário. Não é reversão da P4; é delimitação de escopo da lista.
   · Ação: esclarecer com o humano (via devflow) se a lista é fechada nas
   duas tools nomeadas ou se cobre todas as tools de leitura do ai-memory;
   registrar a resposta nas Regras de Produto.
   · Severidade: melhoria · Resp.: eng-software · Localização: Regras de
   Produto (linha 312), Pergunta 4 (linhas 136-141).

5. Aplicação dos limites de produção por modelo
   (`modelMaxLimits`/`modelMinLimits`), decidida na P6 para o gate C4
   "antes do rollout geral", não tem task: a Task 12 não materializa a
   edição do `dcp.jsonc` com os limites calibrados.
   · Ação: acrescentar à Task 12 (ou a task própria da Fase 5) o passo de
   aplicar os limites calibrados no `harness-conf/dcp.jsonc`, com commit e
   bootstrap.
   · Severidade: melhoria · Resp.: eng-software · Localização: Regras de
   Produto (linhas 309-310), Pergunta 6 (linhas 147-150), Task 12 (linhas
   522-531).

6. Task 13: natureza da "rotina periódica" de defasagem é ambígua (comando
   manual salvo no plano vs script do repo). Se virar script, a regra do
   repo (toda evolução funcional cria testes) exige suíte, não prevista.
   · Ação: declarar na Task 13 que a rotina é procedimento manual
   documentado ou, se script, incluir os testes automatizados
   correspondentes.
   · Severidade: melhoria · Resp.: eng-software · Localização: Task 13
   (linhas 533-552).

7. Formatação: linha 180 excede o limite do repo para arquivos md (125
   colunas; limite 120). Única ocorrência fora desta seção.
   · Ação: reflow da linha na próxima edição do plano.
   · Severidade: melhoria · Resp.: eng-software · Localização: seção
   `## VALIDAÇÃO`, tabela de itens, linha 180.

Fluxo: devflow repassa o achado 1 ao sec, os achados 2 e 3 ao eng-software
(com validação do sec) e os achados 4 a 7 ao eng-software. O rev não aplica
correções.

### Veredicto

**APROVADO COM RESSALVAS** (nenhum achado bloqueante). Os 3 achados
importantes são de coerência interna e instrumentação (achados 1 a 3) e
devem ser resolvidos antes da execução das Fases 1 e 4; as fases seguem
condicionadas à confirmação humana ("esperar para tudo"). As 4 melhorias
podem ser tratadas na próxima edição do plano.

### Evidências (rev) — REVISÃO DO PLANO

- [x] Artefato lido: `plan/plugin-dcp-opencode.md` (integral, 1131 linhas)
- [x] Insumos de referência consultados: seção de insumo do humano no
      próprio plano; `AGENTS.md` da raiz; `harness-conf/opencode.json`
      (sanity check factual: plugins, compaction, mcp, permission)
- [x] Checklist integrativo: 6 dimensões (aderência ao insumo, coerência
      interna, decisões humanas, regras do repo, executabilidade, riscos)
- [x] Achados encontrados: 7 (0 bloqueantes, 3 importantes, 4 melhorias)
- [x] Suítes executadas: nenhuma (fase de revisão de plano; read-only)

### Re-verificação (2026-09-28)

Segunda passagem do rev (instância limpa, sem contato anterior com o
ciclo). Objeto: plano integral (1437 linhas) após as correções da primeira
revisão. Método: verificação dos 7 achados, varredura de regressão das
emendas (P4, P9 e Pergunta 12), checklist rápido dos eixos da primeira
passagem e sanity check factual contra `harness-conf/opencode.json` e o
estado corrente do repo. Nenhuma suíte executada; nenhum arquivo além
desta subseção foi alterado. O relatório original acima está preservado.

#### Resolução dos achados da primeira revisão

| # | Achado original | Estado | Evidência (linhas) |
|---|---|---|---|
| 1 | Contradição P5 `allow` ↔ sec | RESOLVIDO | l. 745-752; l. 879-891; l. 948-951 |
| 2 | SEC-06 sem passo executável | RESOLVIDO | l. 415-429; l. 435-439; l. 720-731 |
| 3 | Janela/gatilho; instrumento SEC-05 | RESOLVIDO* | l. 351-360; l. 384-390; l. 704-719 |
| 4 | Delimitação de `protectedTools` | RESOLVIDO | l. 168-177; l. 333-335; l. 136-140; l. 159-163 |
| 5 | Task 12 sem materializar limites | RESOLVIDO | l. 569-584 |
| 6 | Natureza ambígua (Task 13) | RESOLVIDO | l. 593-598 |
| 7 | Linha >120 colunas na VALIDAÇÃO | RESOLVIDO | awk 2026-09-28: 0 linhas >120 no arquivo |

Notas de evidência:
- 1: SEC-09 SUPERADO com desfecho da P5; "Input técnico" marcado como
  histórico com desfecho P5/P9/P12; roteiro do spike com gate `allow` e
  auditoria pós-fato pelo sqlite (mesmo método do QA-ACC-5).
- 2: Task 4 exige o cenário SEC-06 (evento nativo + `compress` na mesma
  sessão) com gate C1 e fallback C4; C1 cita o SEC-06; SEC-06 declara
  gate e evidência que satisfaz.
- 3: Task 1 e o C0 do eng incluem a janela dos modelos do mapa e o
  gatilho do `compaction.auto` nativo; SEC-05 com instrumento por
  construção (C3) e medido (C4). Ressalva (*) da enumeração do C0 do qa
  no achado 10.
- 4: Pergunta 12 remove `protectedTools`/`protectedFilePatterns` e
  reverte a P9; Regras de Produto, a P4 emendada e a P9 revertida
  refletem a decisão.
- 5: Task 12 aplica `modelMaxLimits`/`modelMinLimits` calibrados no
  `harness-conf/dcp.jsonc`, com commit e bootstrap.
- 6: Task 13 declarada procedimento MANUAL documentado, sem script no
  repo; regra de testes citada caso um script um dia exista.

#### Varredura de regressão das correções

- As remoções da Pergunta 12 propagaram sem contradição nova: a observação
  do QA-ACC-1 registra a perda de proteção que o mínimo de 20% contemplava
  (l. 1108-1111); o roteiro do piloto do sec substitui o item de conteúdo
  protegido `plan/**` por atenção ao risco residual do SEC-08 revertido
  (l. 956-959); o permission gate registra o desfecho P5/P9/P12
  (l. 886-888); a subseção qa registra os desfechos de P4/P5
  (l. 1236-1245).
- Nenhum critério QA-ACC, requisito SEC ou task ficou dependendo de
  proteção removida; `deny` segue como rollback (l. 329, 889-891,
  1162-1164) e o QA-ACC-5 opera como auditoria pós-fato, coerente com
  `allow`.
- Eixos da primeira passagem: coerência interna OK (exceto achados novos
  8 e 9); decisões humanas 1 a 12 incorporadas; regras do repo
  respeitadas (Task 6 TDD; Task 8 com passagem pelo humano; Task 13 sem
  script); C0-C5, QA-ACC e rollback íntegros, com a ressalva do achado 8
  para QA-ACC-3 e QA-ABT-4; largura ≤ 120 colunas OK no arquivo inteiro.

#### Achados novos

8. Premissa quebrada por mudança paralela no repo: o agente `worker` foi
   excluído (commit `e38bbc1`, 2026-09-28, decisão humana registrada na
   mensagem; `harness-conf/agents/worker.md` removido; `opencode.json`
   sem o bloco do worker). O plano trata `worker` como agente spawnável:
   Task 1 (l. 347-348), nota da P8 do sec (l. 932-935), QA-ACC-3
   (l. 1078-1081, "≥ 1 do agente `worker`"; "worker executa com o modelo
   do frontmatter"), procedimento do piloto (l. 1141-1148) e QA-ABT-4
   (l. 1192, "worker fora do modelo do frontmatter"). Sem o agente,
   QA-ACC-3 e QA-ABT-4 ficam não-executáveis como escritos e a Task 1
   perde premissa (subagents em uso).
   · Ação: emendar na próxima edição: spawn genérico via tool `task` com
   subagentes do mapa corrente de agentes; qa reescreve QA-ACC-3, os
   passos 6 e 7 do procedimento do piloto e o QA-ABT-4; eng-software
   atualiza a Task 1; sec ajusta a nota da P8. Mudança paralela legítima
   (decisão humana no commit); nenhuma intenção assumida.
   · Severidade: importante · Resp.: eng-software, qa (sec: nota da P8) ·
   Localização: l. 347-348, 932-935, 1078-1081, 1141-1148, 1192.

9. Mudança inesperada no user-space: o plugin local ai-memory RETORNOU
   (`~/.config/opencode/plugins/ai-memory.ts`, datado de 2026-09-28, com
   backup de 2026-09-27). O plano registra o diretório como vazio na
   premissa 4 (l. 286-291) e no inventário de transformações concorrentes
   do sec (l. 767-770, "Conflito: nenhum hoje"). O SEC-12 (bloqueante
   para adoção, condicional ao retorno do plugin local, l. 759-761) tem a
   condição disparada: passa a requisito ativo para spike e piloto. O
   plano já prevê o caminho (Task 1 resolve a discrepância; nota hook
   ai-memory × DCP, l. 801-808); falta anotar o fato novo.
   · Ação: anotar o retorno na próxima edição (premissa 4 e inventário do
   sec), declarar o SEC-12 ativo desde a Fase 1 e dar prioridade à
   observação passiva da Task 4. Nenhuma intenção assumida.
   · Severidade: importante · Resp.: eng-software, sec · Localização:
   l. 286-291, 759-761, 767-770, 801-808.

10. Enumeração do C0 na subseção qa não acompanhou a emenda do achado 3:
    "(versão, plugins+cache, MCP, subagents, hooks, mapa por harness)"
    sem "janela dos modelos" e "gatilho do compaction.auto nativo"
    (l. 1204-1209). O C0 do eng (canônico, l. 384-390) está correto; o do
    qa é "objetivação proposta" (l. 1202) e pode ser lido como lista
    fechada.
    · Ação: alinhar a enumeração na próxima edição.
    · Severidade: melhoria · Resp.: qa · Localização: l. 1204-1209.

11. Rótulo "risco 4 do insumo" na seção de supply chain do sec: o ponto 3
    do insumo lista três riscos (transformações concorrentes, AGPL,
    permission gate); supply chain é extensão própria do sec, sem item
    correspondente no insumo (l. 893). Imprecisão pré-existente,
    cosmética.
    · Ação: reword na próxima edição (ex.: "extensão do sec" ou "risco
    adicional mapeado pelo sec").
    · Severidade: melhoria · Resp.: sec (edição via eng-software) ·
    Localização: l. 893.

Fluxo: devflow repassa o 8 ao eng-software/qa/sec, o 9 ao
eng-software/sec, o 10 ao qa; o 11 é cosmético. O rev não aplica
correções.

#### Veredicto da re-verificação

**APROVADO COM RESSALVAS.** Os 7 achados da primeira revisão estão
RESOLVIDOS (7/7), incluindo a propagação da Pergunta 12 sem contradição
nova. Os achados novos 8 e 9 (importantes) decorrem de mudanças paralelas
no repo e no user-space em 2026-09-28, posteriores à redação do plano, e
não invalidam o desenho: exigem emenda na próxima edição, antes da
execução das Fases 0, 1 e 4 (que seguem condicionadas à confirmação
humana, "esperar para tudo"). Achados 10 e 11 são melhorias.

#### Evidências (rev)

- [x] Artefato relido: `plan/plugin-dcp-opencode.md` (integral, 1437
      linhas)
- [x] Relatório original consultado: seção `## REVISÃO DO PLANO`
      (preservada; esta subseção foi acrescentada ao final)
- [x] Checklist integrativo: 6 eixos da primeira passagem + varredura de
      regressão das emendas P4/P9/Pergunta 12
- [x] Achados: 7 re-verificados (7 RESOLVIDOS); 4 novos (0 bloqueantes,
      2 importantes, 2 melhorias)
- [x] Sanity check: `harness-conf/opencode.json` confere com o plano
      (plugins quota e task-model@1.3.1; compaction auto/prune/reserved
      10000; MCP ai-memory 127.0.0.1:49374; permission.skill deny);
      `harness-conf/dcp.jsonc` ausente (coerente com ciclo plan-only);
      `~/.config/opencode/dcp.jsonc` ausente; mudanças paralelas do repo
      e do user-space registradas como achados 8 e 9
- [x] Suítes executadas: nenhuma (read-only)

### Verificação final (2026-09-28)

Terceira passagem do rev (instância limpa; primeiro contato com o estado
corrente do ciclo). Objeto: plano integral (1670 linhas) após as correções
dos achados 8 a 11 da re-verificação. Método: verificação dos 4 achados
com evidência de linha, varredura de regressão das correções (sem worker;
SEC-12 ativo; mapa de modelos definitivo) e sanity check factual leve
contra o repo e o user-space. Nenhuma suíte executada; nenhum arquivo
além desta subseção foi alterado. Os relatórios anteriores estão
preservados.

#### Resolução dos achados da re-verificação

| # | Achado | Estado | Evidência (linhas) |
|---|---|---|---|
| 8 | worker removido; plano o tratava como spawnável | PARCIAL | l. 366-372, 1153-1167; resíduo l. 980-984 |
| 9 | retorno do ai-memory; SEC-12 condicional | RESOLVIDO | l. 304-312, 385-386, 792-802, 810-816, 871-873 |
| 10 | C0 do qa sem janela/gatilho do nativo | RESOLVIDO | l. 1287-1296 |
| 11 | rótulo "risco 4 do insumo" na supply chain | RESOLVIDO | l. 941 |

Notas de evidência:

- 8: essência resolvida. Task 1 descreve spawns via tool `task` com os
  agentes especialistas e registra a remoção do worker (commit `e38bbc1`,
  l. 366-372); tabela de riscos reescrita (l. 656); QA-ACC-3 reescrito
  para spawns de especialistas com modelo da chamada verificado em
  `session.model` (l. 1153-1167); passos 6 e 7 do procedimento sem
  worker (l. 1222-1231); QA-ABT-4 reescrito (l. 1275); C0 do qa sem
  worker e com mapa real de spawn (l. 1287-1296); mudança de spec
  registrada pelo qa (l. 1076-1089). PARCIAL porque a ação prescrita
  incluía "sec ajusta a nota da P8" e isso não foi executado: a l. 981
  ainda cita "worker com reasoning max" como fato corrente, sem anotação
  de desfecho (achado 12).
- 9: premissa 4 reescrita (plugin PRESENTE; retorno de 2026-09-28 com
  backup de 2026-09-27); SEC-12 ATIVO desde a Fase 1, com verificação
  explícita pré-piloto (l. 792-802); transformações concorrentes com
  conflito potencial restabelecido (l. 810-816); critério da Task 1 e
  mitigações alinhados (l. 385-386, 871-873).
- 10: o C0 do qa agora enumera janela dos modelos, gatilho do
  `compaction.auto` nativo, plugin ai-memory confirmado presente,
  mapa por harness e inventário sem worker (l. 1287-1296).
- 11: cabeçalho da subseção reescrito para "extensão do sec, sem item
  correspondente no insumo" (l. 941).

#### Varredura de regressão

- worker: grep no plano retorna 14 ocorrências; 13 são notas de correção
  ou histórico da revisão; a única ocorrência "viva" é a l. 981 (achado
  12). Nenhum critério QA-ACC, requisito SEC, task, checkpoint ou
  procedimento depende do worker.
- Proteções removidas (Pergunta 12): nenhuma dependência residual; os
  trechos que citam `protectedTools`/`protectedFilePatterns`/
  `protectUserMessages` estão anotados como históricos com desfecho
  (l. 354-356, 927-939, 1004-1007, 1189-1192).
- SEC-12 ativo: coerente com a observação passiva da Task 4 (ponto de
  partida), com a nota hook × DCP (l. 847-855) e com o C0 do qa; sem
  contradição em nenhuma subseção.
- Mapa de modelos definitivo: tasks e critérios citam o mapa novo
  (l. 106-117, 279-287, 374-376) ou referências genéricas ao "modelo de
  execução do mapa" (l. 1206); nenhuma task ou critério depende do luna.
  Ressalva: referências históricas ao mapa luna sem remissão (achado 13).
- Largura: awk 2026-09-28: 0 linhas com mais de 120 colunas no arquivo.

#### Sanity check factual

- `harness-conf/agents/`: sem `worker.md` (confere). O commit `e38bbc1`
  (2026-09-28) existe e removeu `worker.md` e `revisor.md`; o plano não
  referencia o agente `revisor` (a única ocorrência de "revisor" é o
  papel no mapa histórico, l. 94), logo a segunda remoção não o afeta.
- `~/.config/opencode/plugins/ai-memory.ts`: PRESENTE (2026-09-28), com
  backup de 2026-09-27 (confere com a premissa 4 e o SEC-12).
- `harness-conf/opencode.json`: plugins quota (spec sem pin, como o sec
  registra em `@latest`) e `opencode-task-model@1.3.1`; `compaction`
  auto/prune/reserved 10000; MCP ai-memory `127.0.0.1:49374`;
  `permission.skill` deny quase total. Confere com as citações do plano.

#### Achados novos

12. Resíduo do achado 8: a nota da Pergunta 8 do sec (l. 980-984) ainda
    descreve "Subagents (worker com reasoning max, tool `task`)" como
    fato corrente e recomenda `false` sem anotação de desfecho; o agente
    foi removido e a P8 decidiu `true`. Nada executável depende da nota;
    é texto histórico sem marcação, mesma classe do achado 1 da primeira
    revisão.
    · Ação: anotar o desfecho (P8 decidida `true`; worker removido em
    `e38bbc1`) na próxima edição do plano.
    · Severidade: melhoria · Resp.: sec (edição via eng-software) ·
    Localização: l. 980-984.

13. Referências históricas ao mapa luna sem remissão ao mapa definitivo:
    o contexto do devflow (l. 93-95) e a Pergunta 1 (l. 121-123, "ref
    registrado no mapa de modelos") descrevem o mapa de 2026-09-27 como
    vigentes; o mapa definitivo (P13) os suplanta e até registra a
    descontinuação do luna, mas os trechos não apontam para ele.
    · Ação: acrescentar remissão ao mapa definitivo (l. 104-117 / P13)
    nas duas passagens, na próxima edição do plano.
    · Severidade: melhoria · Resp.: eng-software · Localização: l. 93-95,
    121-123.

Fluxo: devflow repassa o 12 ao sec (edição via eng-software) e o 13 ao
eng-software; ambos cabem na próxima edição do plano, sem nova revisão.
O rev não aplica correções.

#### Veredito final

**APROVADO COM RESSALVAS.** 3/4 achados da re-verificação RESOLVIDOS; o
achado 8 fica PARCIAL por resíduo documental sem impacto executável
(achado 12). Nenhum achado bloqueante ou importante: o plano está
internamente coerente, aderente ao insumo e às decisões humanas (P1 a
P13), com gates C0-C5 objetivos e rollback íntegro. Pela autonomia da
Pergunta 13, o workflow segue direto para a CONSTRUÇÃO; os achados 12 e
13 são correções simples de texto, aplicáveis pela eng-software na
próxima edição do plano, sem nova passagem do rev.

#### Evidências (rev) — verificação final

- [x] Artefato relido: `plan/plugin-dcp-opencode.md` (integral, 1670
      linhas)
- [x] Histórico de revisões consultado: seção `## REVISÃO DO PLANO`
      (primeira passagem e re-verificação preservadas)
- [x] Checklist integrativo: 4 achados re-verificados; varredura de
      regressão (worker, proteções P12, SEC-12, mapa de modelos) sobre
      os eixos da primeira passagem
- [x] Sanity check: `harness-conf/agents/` sem worker; commit `e38bbc1`
      confere; `~/.config/opencode/plugins/ai-memory.ts` presente com
      backup de 2026-09-27; `harness-conf/opencode.json` confere
- [x] Achados: 4 re-verificados (3 RESOLVIDOS, 1 PARCIAL); 2 novos
      (0 bloqueantes, 0 importantes, 2 melhorias)
- [x] Suítes executadas: nenhuma (fase de revisão de plano; read-only)
