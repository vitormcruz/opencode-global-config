# Plano: otimização de custo e contexto do repo

Status: FINALIZAÇÃO — 2º ciclo (fase DEVFLOW), pacote final aprovado em
execução. MAPA DE MODELOS ATUALIZADO (decisão humana 2026-09-27):
executor = `opencode-go/gpt-6-luna` com `reasoning: max` (substitui
`opencode/gpt-6-luna` high em TODOS os spawns de execução daqui em
diante); revisor = `zai-coding-plan/glm-5.3` (confirmado). Pacote
aprovado: premissa 7 revisada (pausa condicionada + sessão nova sempre);
Q-Efix 1 (clarificação da política progressiva de espera, sem mudar
política/testes), 2 (exemplos em references/), 3 (skill git: só pre-commit
adaptado + remover reset --hard), 4 (humanizer: ampliar description),
5/6 (gatilhos), 7 (precedência mecânica vs humano), 8 (carregar só ao
criar/revisar); spec de segurança ao protocolo spec-executavel +
auditoria do porquê. Pendências menores já aprovadas como backlog.
Depois do pacote: commit residual do plano, exclusão de artefatos e
push, ambos SÓ com confirmação humana. Pós-restart (humano): RM-10 +
MCP vivo exigem reiniciar o OpenCode.

## Overview

Este repo é a fonte de verdade das configs globais dos harnesses (OpenCode e
Copilot CLI). O objetivo é otimizar O QUE ESTE REPO ENTREGA às sessões:
skills visíveis apenas aos agentes corretos, AGENTS.md enxutos e de alto
sinal por token, descriptions e corpos de skills reescritos com
writing-for-agents, command global de análise/otimização de AGENTS.md e
piloto de memória compartilhada (ai-memory) para compressão de sessão com
menos perda. A motivação e a métrica vêm do relatório de custos
(cache_write 76,7%; standing load como parte do prefixo). Duas frentes:
fase AGORA (neste ambiente, escopo OpenCode + seu adapter, testes mínimos) e
fase DEVFLOW (revisar e expandir o que foi feito, aplicar aos demais
adapters, atualizar docs, completar testes).

## Insumos

- Relatório: `/mnt/c/Users/Vitor/Downloads/relatorio-custos-contexto-cache.md`
  (472 linhas; cache_write 76,7% do custo da conversa principal; payback de
  compactação ~11 chamadas; recomendações de requests e contexto).
- Estado manual atual: `~/.config/opencode/skills` é diretório real com 7
  symlinks individuais (fora do adapter; bootstrap pode desmanchar).
- Esboço existente: `plan/plugin-opencode-task-model.md` (spawn com modelo).

## Achados de pesquisa (2026-09-22)

1. **Skills por agente: suportado nativamente.** `permission.skill` com
   patterns (wildcards) em `opencode.json` (global) e no frontmatter do
   agente. `deny` oculta a skill do discovery do agente (corta o standing
   load das descriptions). O repo já usa o padrão: `aws-*: deny` global +
   `aws-*: allow` no `aws-analista` (`harness-conf/opencode.json`).
2. **writing-for-agents**: skill do `mattpocock/skills` (MIT, LICENSE no
   repo; não existe no repo local). Referência para docs que agentes leem:
   no-op pruning ("deletar, não explicar"), context pointers, leading
   words, description com "Use when", split de arquivos > ~100 linhas; tem
   também `SKILL-MECHANICS.md` (frontmatter, escolha de invocação, router
   skills). Instalação:
   `npx skills add https://github.com/mattpocock/skills --skill writing-for-agents`.
   Não é um otimizador automático: é a disciplina de escrita.
3. **Otimização de AGENTS.md**: candidatos a import (profundidade: livecrawl
   nos repos + licenças confirmadas em 2026-09-22):
   - `CaesiumY/agents-md-optimizer`: MIT, 3 stars, criado 2026-03. Skill
     metodológica (sem binário) que codifica o blog de Addy Osmani
     (`addyosmani.com/blog/agents-md`): discoverability filter + gotcha
     mining (8 categorias) + flags `--dry-run`/`--report-only`. Baixa
     adoção; SKILL.md ainda não lido por inteiro (revisão de segurança
     obrigatória na importação, por regra do repo).
   - `jed1978/instrlint`: MIT, 7 stars, npm CLI + skill; dead rules para
     JS/TS e C# (este repo é Python: baixa aderência), score e token
     budget (cl100k), `--verify` com o modelo host.
   - `agentlint` (kcotias): extensão VS Code: descartado para command.
   - Não existe otimizador de AGENTS.md do Matt Pocock; o dele é o
     writing-for-agents (item 2).
4. **ai-memory**: `akitaonrails/ai-memory` (Fabio Akita; Rust; MIT;
   3.200+ stars; v1.29.0 de ago/2026). Wiki markdown git-versioned + SQLite
   (FTS5); hooks de lifecycle (PreCompact persiste resumo antes da
   compactação); handoffs cross-harness; suporta OpenCode (MCP + hooks).
   "Compile, don't retrieve". Copilot CLI não consta na matriz de suporte.
5. **Tamanhos atuais**: `harness-conf/AGENTS.base.md` 4,3 KB; AGENTS.md
   global gerado 5,2 KB; `AGENTS.md` do repo 10,9 KB (o maior alvo).
6. **Do relatório**: ofensor principal = `cache_write` (76,7% do custo da
   conversa principal). Standing load (AGENTS.md + descriptions) é parte do
   prefixo: reduzi-lo ataca cache_write e o custo por chamada.
7. **Compactação no OpenCode:** o agente NÃO tem tool nativa para disparar
   compactação. Mecanismos disponíveis: (a) compactação automática por
   threshold (`compaction` no `opencode.json`, já configurada); (b) comando
   `/compact` do humano; (c) nova sessão com estado persistido em arquivo.
   Hooks de lifecycle (SessionCompactBefore/After; PreCompact do ai-memory
   no piloto) permitem persistir resumo antes de compactar.

## Architecture Decisions

- **D1 (multi-harness): primeiro momento só OpenCode.** O repo serve
  OpenCode e Copilot CLI; as otimizações da onda inicial usam mecanismos do
  OpenCode (permission.skill). Os ajustes equivalentes no Copilot CLI ficam
  registrados como pendência para o devflow.
- **D2 (ai-memory = akitaonrails/ai-memory): piloto só depois das
  primeiras otimizações implementadas.** Fabio Akita, Rust, MIT, 3.200+
  stars, suporta OpenCode (MCP + hooks); hook PreCompact persiste resumo
  antes da compactação (compressão com menos perdas). Copilot CLI não
  consta na matriz de suporte: verificar no piloto. Adoção decidida por
  telemetria (método do relatório de custos), não de imediato.
- **D3 (divisão de frentes):** fase AGORA (executor local, escopo OpenCode
  e seu adapter, testes mínimos) e fase DEVFLOW, com conteúdo definido pelo
  corte final de D9.
- **D4 (superado por D9):** lista intermediária de itens, expandida pelo
  corte final; o conteúdo vigente é o de D9.
- **D5 (AGENTS.base.md na onda 1):** a tabela de roteamento e a política de
  compactação entram no AGENTS.base.md (compartilhado pelos harnesses) já na
  onda 1; texto neutro e benéfico para ambos.
- **D6 (mecanismo permissions confirmado; escopo OpenCode):** filtro via
  `permission.skill` no `harness-conf/opencode.json` (deny global das skills
  de domínio) + allow no frontmatter de cada agente especialista em
  `harness-conf/agents/*.md`. Adapter intocado; estado manual dos 7 symlinks
  volta ao symlink único de bootstrap. Copilot CLI: NÃO planejar agora; o
  devflow planeja o workaround depois (Copilot é limitado em skills).
  Insumos técnicos para esse planejamento: `convert_agent_frontmatter`
  ignora `permission.skill` (adicionar permissions não quebra o conversor);
  `_sync_skills` copia todas as skills sem filtro; commands novos precisam
  de entrada própria em `_COMMAND_DESCRIPTIONS`.
- **D8 (superado por D9):** o mapeamento completo das recomendações do
  relatório foi descartado no corte final; só a política de compactação
  entrou (D11).
- **D9 (corte final aprovado em 2026-09-22):**
  - **Fase AGORA (neste ambiente):** escopo apenas OpenCode e seu adapter;
    testes mínimos. Entra:
    1. Permissions de skills por agente (A1).
    2. Normalização dos 7 symlinks manuais, volta ao symlink único (A2).
    3. Enxugo do AGENTS.md do repo pelo command de otimização (A3).
    4. Enxugo do AGENTS.base.md pelo command de otimização (A4).
    5. Reescrita das descriptions das 7 skills core com writing-for-agents
       (A5).
    6. Reescrita das descriptions das ~24 skills de domínio (A6).
    7. Reescrita dos corpos das 31 skills com writing-for-agents (A7).
    8. Tabela de roteamento agentes→funções + regra "agente genérico
       sugere troca" no AGENTS.base.md (B1). Subseções "Instruções por
       Agente" do AGENTS.md do repo permanecem "SEM INSTRUÇÕES" (decisão
       prévia do humano).
    9. Política de compactação para todos os agentes no AGENTS.base.md
       (C2; ver D11).
    10. Import do writing-for-agents (revisão de segurança + UPSTREAM.md;
        ver D10).
    11. Command global de análise/otimização de AGENTS.md (D7).
    12. Teste de consistência estendido para o mapa novo de permissions
        (guarda de A1).
    13. Piloto do ai-memory ao final, após 1-12 (F1; ver D2).
    14. Materializar o insumo do devflow: consolidar neste arquivo o
        estado final da fase AGORA (o que foi implementado, resultados do
        piloto, pendências e decisões), atualizar o campo Status para o
        vocabulário do devflow e manter a seção Fase DEVFLOW como roteiro
        do planejamento dele.
  - **Dependência: otimização de conteúdo usa o ferramental.** Enxugos de
    AGENTS.md (itens 3-4) passam pelo command; reescritas de skills (itens
    5-7) seguem o método writing-for-agents. Ordem interna: import e
    command antes dos enxugos.
  - **Fora de escopo (decisão "esquece"):** regras de comportamento de
    agentes/devflow do relatório (agrupar operações, contrato congelado,
    preflight, correções consolidadas, orçamento de requests) e plugin
    opencode-task-model (esboço em `plan/` permanece intocado).
  - **Fase DEVFLOW (insumo = este plano, materializado pelo item 14 da
    fase AGORA):** analisar o insumo; revisar e
    expandir tudo o que foi feito aqui; aplicar aos outros adapters
    (Copilot CLI) o que foi feito apenas no OpenCode; atualizar docs;
    completar os testes faltantes (proposta de "o que mais": suíte
    completa `-m all`, registro da skill importada no `opencode-skills` +
    checklist pós-sync do AGENTS.md do repo, verificação de consistência
    workflow↔agentes, README/seção de dependências se o ai-memory mudar
    premissas de instalação). Item prioritário adicional (D13, decidido
    pelo humano em 2026-09-23): mecânica de sync diff assistido + freeze
    no `opencode-skills`.
- **D10 (writing-for-agents é skill de domínio, não global):** deny global
  junto às demais skills de domínio + allow nos agentes que escrevem e
  revisam conteúdo para agentes: `devflow`, `eng-software` e
  `smart-planner`. O command de otimização embute o método essencial no
  próprio corpo (on-demand, sem standing load). Nas reescritas (itens 5-7
  de D9), o executor carrega a skill deliberadamente.
- **D11 (política de compactação: escopo todos os agentes; implementação
  agora só OpenCode):** a política entra no AGENTS.base.md e vale para
  TODOS os agentes (não só o devflow). Implementação e validação nesta
  fase são apenas OpenCode; nenhum mecanismo ou ajuste específico do
  Copilot CLI agora — se a herança do texto pelo Copilot for indesejada,
  o isolamento por harness fica como pendência da fase DEVFLOW.
  Como o agente não dispara compactação sozinho (achado 7), a regra é:
  reconhecer os critérios do relatório (histórico virou ruído; tarefa
  longa confirmada) e reduzir o contexto por preferência de mecanismo:
  1. **Favorecer mecanismos automatizados quando efetivos** (ex.:
     auto-compactação por threshold, já ativa no `opencode.json`; nova
     sessão/spawn com estado persistido em arquivo quando o próprio fluxo
     dá conta, como o devflow já faz por fase).
  2. **Se nenhum mecanismo automatizado for aplicável ou efetivo no
     contexto**, solicitar `/compact` ao humano ou propor nova sessão com
     estado persistido.
  **Precedência:** esta regra SOBREPUJA a política de sessão do workflow
  (premissa 7 de `docs/workflow-agentes-dev.md`: "retomada dentro da
  fase, sessão nova entre fases"). Quando os critérios dispararem dentro
  da mesma fase, o agente propõe compactação ou nova sessão com estado
  persistido mesmo sem trocar de fase. A premissa 7 é ajustada na fase
  AGORA para registrar a exceção (manter sincronia
  workflow↔agentes).
  O piloto do ai-memory (F1) adiciona o hook PreCompact por cima deste
  comportamento.
- **D12 (modelos do ciclo de execução):** executor = agente `worker`
  com `zai-coding-plan/glm-5.3-flash` (teto de modelo para o worker; não
  subir além disso). Revisor = agente `revisor` com
  `zai-coding-plan/glm-5.3` (mantido). A troca do modelo do worker exige
  editar o frontmatter de `harness-conf/agents/worker.md` e reiniciar o
  OpenCode (regra do repo); escolhas reutilizadas em novas instâncias
  até o humano alterá-las.
- **D7 (command de AGENTS.md): base Pocock + command próprio.** Importar
  writing-for-agents (MIT; UPSTREAM.md + revisão de segurança obrigatória)
  como referência canônica; command global próprio com dois estágios:
  (1) filtro de descobribilidade; (2) compressão com garantia de
  comportamento (no-op test, imperativo positivo, um termo por conceito,
  bullets). O command embute o método essencial no próprio corpo (D10).
  Verificação antes/depois: tokens + cobertura das regras operacionais.
  agents-md-optimizer (CaesiumY) descartado como dependência; instrlint
  descartado (dead rules JS/TS+C#, repo é Python).
- **D13 (sync de upstream: diff assistido + freeze; implementação na fase
  DEVFLOW):** o sync continua sem sobrescrever SKILL.md local. Ganhos novos:
  (1) comando `opencode-skills diff NOME` que traz o diff upstream
  base→novo desde o último sync (o que o autor mudou lá), e a aplicação no
  SKILL.md local é ASSISTIDA: agente/humano aplica o que é relevante
  seguindo writing-for-agents, mantendo o formato e a estrutura da versão
  local; (2) freeze por skill: campo `sincronizacao: congelada` no
  UPSTREAM.md, respeitado pelo sync e pelo `list`; congelar ou descongelar
  é decisão humana, caso a caso; o UPSTREAM.md permanece no repo para
  proveniência e licença (nunca é apagado). Implementação e testes na fase
  DEVFLOW, junto do registro da writing-for-agents no CLI.

## Task List

Nota geral: artefatos de produção (command, AGENTS.base.md, descriptions,
corpos de skills, testes) devem ser AUTOCONTIDOS — sem citar códigos de
decisão ou numeração deste plano. Testes mínimos nesta fase: os testes
novos/tocados precisam passar; a suíte completa do ambiente é executada e
falhas pré-existentes registradas sem correção (completar é da fase
DEVFLOW).

### Fase 1: Ferramental (fundação)

- [ ] **Task 1: Importar writing-for-agents**
  **Description:** importar a skill writing-for-agents de
  `mattpocock/skills` para `harness-conf/skills/`, com revisão de
  segurança de TODO o conteúdo copiado (prompt injection, comandos, URLs,
  exfiltração), UPSTREAM.md (origem, SHA, data, `description_lang`),
  description convertida para PT-BR com triggers e registro no
  `opencode-skills`.
  **Acceptance criteria:**
  - [ ] Skill em `harness-conf/skills/writing-for-agents/` com SKILL.md
        adaptado (nunca sobrescrito pelo sync) e `UPSTREAM.md` completo.
  - [ ] Revisão de segurança registrada (o que foi lido e verificado).
  - [ ] Description em PT-BR com triggers; registrada no `opencode-skills`.
  **Verification:** `opencode-skills list` mostra a skill; conteúdo
  conferido contra o upstream.
  **Dependencies:** None
  **Files likely touched:** `harness-conf/skills/writing-for-agents/*`
  **Estimated scope:** Small

- [ ] **Task 2: Command global de análise/otimização de AGENTS.md**
  **Description:** criar command em `harness-conf/commands/` que analisa e
  otimiza arquivos AGENTS.md em dois estágios: (1) filtro de
  descobribilidade; (2) compressão com garantia de comportamento (no-op
  test, imperativo positivo, um termo por conceito, bullets). O método
  essencial fica embutido no corpo do command (autocontido).
  **Acceptance criteria:**
  - [ ] Command disponível globalmente no OpenCode após bootstrap.
  - [ ] Nunca aplica mudanças sem diff + aprovação do humano.
  - [ ] Relata antes/depois: contagem aproximada de tokens e cobertura das
        regras operacionais (o que saiu e por quê).
  **Verification:** execução controlada em um AGENTS.md de teste; diff
  gerado; nada aplicado sem confirmação.
  **Dependencies:** Task 1 (método de referência; corpo autocontido).
  **Files likely touched:** `harness-conf/commands/otimizar-agents-md.md`
  **Estimated scope:** Small

**Checkpoint 1 (commit):** `feat(skills): importa writing-for-agents` e
`feat(commands): adiciona command de otimização de AGENTS.md`.

### Fase 2: Standing load

- [x] **Task 3: Enxugar o AGENTS.base.md**
  **Resultado (2026-09-23):** 1082 → 1047 tokens chars/4 (-3,2%), commit
  `6b8e6f8`. Ajustes humanos incorporados: bullet novo na seção "Criação de
  Skills" apontando para `writing-for-agents`; literais do teste de contrato
  ("repo estiver indexado no codebase-memory", "CLI-first") restaurados no
  bullet da Descoberta de Código.
  **Description:** aplicar o command (estágios 1 e 2) ao
  `harness-conf/AGENTS.base.md`; revisar diff com o humano; aplicar.
  **Acceptance criteria:**
  - [ ] Diff aprovado pelo humano antes de aplicar.
  - [ ] Nenhuma regra operacional perdida (cobertura verificada).
  - [ ] Redução de tamanho registrada no plano.
  **Verification:** diff revisado; regras remanescentes conferidas.
  **Dependencies:** Task 2
  **Files likely touched:** `harness-conf/AGENTS.base.md`
  **Estimated scope:** Small

- [x] **Task 4: Enxugar o AGENTS.md do repo**
  **Resultado (2026-09-23):** 2712 → 2590 tokens chars/4 (-4,5%), commit
  `6b8e6f8`. Subseções "SEM INSTRUÇÕES" preservadas byte a byte; 2 saídas
  aprovadas (justificativa do codebase-memory CLI; parêntese repetido no
  checklist pós-sync).
  **Description:** idem Task 3 para o `AGENTS.md` da raiz do repo (10,9 KB,
  maior alvo). Preservar subseções "SEM INSTRUÇÕES" (decisão prévia) e
  regras de governança do repo.
  **Acceptance criteria:**
  - [ ] Diff aprovado pelo humano; subseções intactas.
  - [ ] Redução registrada.
  **Verification:** diff revisado; seções de governança conferidas.
  **Dependencies:** Task 2
  **Files likely touched:** `AGENTS.md`
  **Estimated scope:** Small

- [x] **Task 5: Reescrever descriptions das 7 skills core**
  **Resultado (2026-09-23):** 1355 → 1130 tokens chars/4 (-225), commit
  `ee74995`. Triggers canônicos preservados byte a byte (validação automática
  contra baseline).
  **Description:** reescrever as descriptions das skills core
  (code-explorer-priority, git-workflow-and-versioning, humanizer-br,
  planning-and-task-breakdown, portugues-tecnico-controlado,
  question-orchestration, reliable-async-operations) pelo método
  writing-for-agents: triggers preservados, alto sinal por token.
  **Acceptance criteria:**
  - [ ] Cada description mantém os triggers canônicos de ativação.
  - [ ] Redução de tokens por description registrada.
  **Verification:** leitura cruzada description↔corpo; diff por skill.
  **Dependencies:** Task 1
  **Files likely touched:** `harness-conf/skills/<core>/SKILL.md` (7)
  **Estimated scope:** Medium

- [x] **Task 6: Reescrever descriptions das ~24 skills de domínio**
  **Resultado (2026-09-23):** contagem real: 25 skills de domínio (33 pastas
  no total: 7 core + 25 domínio + writing-for-agents). Descriptions
  3519 → 3555 tokens chars/4 (+36): 8 convertidas de EN para PT-BR e 7 skills
  sem triggers ganharam triggers de discovery (justifica o acréscimo).
  Commits `b7fe366`, `55c5e72`, `f01cc34`. Tabela consolidada em
  `/tmp/opencode/fase2/descriptions-tabela.md`.
  **Description:** idem Task 5 para as demais skills de
  `harness-conf/skills/` (excluindo writing-for-agents, recém-importada).
  **Acceptance criteria:**
  - [ ] Triggers preservados; redução registrada.
  **Verification:** diff por skill; leitura cruzada.
  **Dependencies:** Task 1
  **Files likely touched:** `harness-conf/skills/<dominio>/SKILL.md` (~24)
  **Estimated scope:** Large (executar em lotes de ~8)

- [x] **Task 7: Reescrever corpos das 31 skills**
  **Nota de contagem (2026-09-23):** são 32 corpos (7 core + 25 domínio).
  writing-for-agents fica EXCLUÍDO: corpo é cópia canônica do upstream e
  referência do método; reescrevê-lo enfraquece o papel de referência.
  **Resultado (2026-09-23):** 3 lotes, commits `b78379b`, `36447b9`,
  `c518e73`. Corpos 64391 → 48266 tokens chars/4; medição corpo a corpo
  do revisor (convenção unificada): -16059 tokens (-26%). Frontmatter
  intocado (validação programática); references/UPSTREAM/LICENSE intocados;
  no-op test por skill em `/tmp/opencode/fase2/corpos-lote{1,2,3}.md`;
  pinos de teste restaurados quando fixavam strings de corpo. Suíte: 822
  passed, 1 failed pré-existente (JAVA_HOME), 31 deselected.
  **Description:** aplicar writing-for-agents ao corpo de cada SKILL.md
  (no-op pruning, context pointers, bullets, split > ~100 linhas).
  Executar em lotes de até 10 skills; diff por skill; sem mudança de
  comportamento (garantia pelo no-op test).
  **Acceptance criteria:**
  - [ ] Cada skill reescrita passa pelo no-op test registrado.
  - [ ] Nenhum script/reference deletado sem verificação de uso.
  - [ ] Sincronia com UPSTREAM.md preservada (sync não sobrescreve
        SKILL.md local; references sincronizadas conferidas).
  **Verification:** diff por skill; suites/commands que citam as skills
  continuam coerentes.
  **Dependencies:** Task 1; idealmente após Task 5-6 (mesma skill lida
  uma vez).
  **Files likely touched:** `harness-conf/skills/*/SKILL.md` (31)
  **Estimated scope:** Large (lotes de até 10; checkpoint por lote)

**Checkpoint 2 (commits):** `docs(agents): enxuga AGENTS.md do repo e
AGENTS.base.md`; `refactor(skills): reescreve descriptions`;
`refactor(skills): reescreve corpos` (um commit por lote se preferir).

### Fase 3: Permissions e regras

- [x] **Task 8: Permissions de skills por agente**
  **Resultado (2026-09-23):** commit `42b2212`. 13 arquivos: opencode.json
  (deny global: 21 chaves novas + aws-* existente, cobrindo 23 skills),
  frontmatter com 69 allows em 11 agentes (worker/revisores sem alteração),
  corpo do front completado com as 7 skills de engenharia, linha de
  descoberta no AGENTS.base.md, allow aws-* migrado ao frontmatter do
  aws-analista. Suíte: 822 passed, 1 failed pré-existente (JAVA_HOME), 31
  deselected. Dívida pré-existente registrada: linhas >120 em vários
  agents/*.md (fora do escopo deste commit).
  **Mapa FINAL v4, aprovado e confirmado pelo humano em 2026-09-23
  (derivação por varredura linha a linha das menções nos corpos + decisões
  humanas):**
  - Global (visível a todos, sem deny): git-workflow-and-versioning,
    humanizer-br, portugues-tecnico-controlado, question-orchestration,
    reliable-async-operations (voltou a global por decisão humana) + 5
    utilitárias: doc-extract, md-export, tls-certificate-recovery,
    svg-to-image, web-research-exa-crawl4ai.
  - Deny global (23): 18 skills de domínio + writing-for-agents +
    planning-and-task-breakdown + code-explorer-priority + aws-add-account-sso
    + aws-sso-login (estas 3 removidas de core por decisão humana, com allow
    conforme abaixo; as 2 aws cobertas pela chave `aws-*`).
  - Allow (skill: agentes):
    · code-explorer-priority: TODOS os 8 agentes do workflow de
      desenvolvimento (devflow, eng-software, front, curador-produto,
      dba, sec, rev, qa; docs/workflow-agentes-dev.md, tabela Agentes)
    · planning-and-task-breakdown: smart-planner, qa, dba, eng-software,
      devflow
    · writing-for-agents: devflow, eng-software, smart-planner (D10)
    · aws-*: aws-analista (allow pré-existente, MIGRADO da seção agent do
      opencode.json para o frontmatter; corpo cobre os fluxos sem citar
      nominalmente)
    · debugging-and-error-recovery: aws-analista, dba, eng-software, qa,
      sec
    · security-and-hardening: sec, dba, rev
    · data-modeling: dba, rev
    · code-review-and-quality: sec, eng-software, rev
    · code-simplification: eng-software, front, rev
    · clean-code: eng-software, front
    · frontend-ui-engineering: front, rev
    · accessibility-audit: front, qa, rev
    · performance-optimization: front, qa, eng-software
    · test-driven-development: qa, eng-software, front
    · tests-as-spec: qa, eng-software, rev, front
    · browser-testing: qa
    · spec-executavel: analista, curador-produto, eng-software, qa, sec,
      front
    · spec-driven-development: analista
    · documentation-and-adrs: curador-produto, eng-software, rev, front
    · api-and-interface-design: eng-software, rev, front
    · testes-produto-catalog: curador-produto
    · prompt-improver: devflow
    Sem allow: worker, revisor, revisor-historia (fora do workflow de
    desenvolvimento).
  - Front: além das 5 atuais do corpo, GANHA 7 de engenharia por decisão
    humana (test-driven-development, tests-as-spec,
    debugging-and-error-recovery, documentation-and-adrs,
    api-and-interface-design, code-review-and-quality, spec-executavel),
    ACRESCENTANDO as menções no corpo dele (o allow tem que bater com o
    corpo; listas nunca saem dos agentes). Front total: 12 de domínio.
  - AGENTS.base.md, seção Descoberta de Código, linha nova aprovada:
    "Agente de codificação: para descoberta de código, carregue a skill
    `code-explorer-priority` e siga o CLI-first."
  - Efeito aceito: a regra de descoberta do AGENTS.base.md passa a valer
    para os 8 do workflow (demais caem no fallback grep/glob).
  **Description:** adicionar `permission.skill` com deny global das skills
  de domínio em `harness-conf/opencode.json` e allow específico no
  frontmatter de cada agente especialista, derivando o mapa das tabelas de
  skills obrigatórias/condicionais no corpo de cada `harness-conf/
  agents/*.md`. writing-for-agents: allow em `devflow`, `eng-software` e
  `smart-planner`. Skills core: sem deny (visíveis a todos). Adapter
  intocado.
  **Acceptance criteria:**
  - [ ] Deny global cobre toda skill de domínio; nenhuma órfã.
  - [ ] Cada allow aponta para skill existente e agente declarado.
  - [ ] `opencode.json` válido (JSON parse) e padrão consistente com
        `aws-*` existente.
  **Verification:** JSON válido; mapa conferido contra os corpos dos
  agentes; bootstrap roda sem erro.
  **Dependencies:** Tasks 5-6 (descriptions finais primeiro).
  **Files likely touched:** `harness-conf/opencode.json`,
  `harness-conf/agents/*.md` (frontmatter)
  **Estimated scope:** Medium

- [x] **Task 9: Teste de consistência estendido**
  **Resultado (2026-09-23):** commit `362ab54`. 9 testes novos em
  `tests/agents/test_workflow_consistency.py` (parser de permission.skill,
  wildcard via fnmatchcase, whitelist das 10 globais): órfã sem allow, allow
  de skill inexistente, domínio sem deny, agente fantasma; cada caso com
  fixture violante validada. Suíte: 831 passed, 1 failed pré-existente
  (JAVA_HOME), 31 deselected.
  **Description:** estender `tests/agents/test_workflow_consistency.py`
  para o mapa novo: skill com deny sem nenhum allow (órfã), allow de skill
  inexistente, skill de domínio sem deny, agente referenciado inexistente.
  **Acceptance criteria:**
  - [ ] Teste detecta os 4 casos acima (testes negativos com fixtures).
  - [ ] Suíte de `tests/agents/` passa.
  **Verification:** `.venv/bin/pytest tests/agents/ -m all` (WSL/Linux) ou
  `.\.venv\Scripts\pytest.exe tests/agents/ -m all` (Windows).
  **Dependencies:** Task 8
  **Files likely touched:** `tests/agents/test_workflow_consistency.py`
  **Estimated scope:** Small

- [x] **Task 10: Roteamento, política de compactação e premissa 7**
  **Resultado (2026-09-23):** commit `c24068d`. AGENTS.base.md +34 (seções
  Roteamento com tabela dos 8 agentes, Autonomia, Compactação de contexto);
  workflow-agentes-dev.md premissa 7 com exceção de compactação (+6/-1).
  sha256 dos originais validado antes da aplicação; diff confere com os
  rascunhos aprovados; suíte 831 passed, 1 failed pré-existente (JAVA_HOME),
  31 deselected. Item C sem mudança.
  **Ajuste (2026-09-23, pedido do humano):** incluir também no
  AGENTS.base.md regra de autonomia: violação de regra objetiva do repo
  (formatação, largura de linha, estilo) é corrigida de imediato pelo
  agente, sem escalar ao humano; escalar apenas decisão de escopo,
  comportamento ou risco. (Já contemplada no rascunho A, seção Autonomia.)
  **Description:** no `harness-conf/AGENTS.base.md` (estilo enxuto da
  Fase 2): tabela de roteamento agentes→funções + regra "agente genérico
  sugere troca" (texto autocontido); política de compactação para todos
  os agentes (preferência por mecanismos automatizados efetivos; fallback
  `/compact` ao humano ou nova sessão com estado persistido). Ajustar a
  premissa 7 de `docs/workflow-agentes-dev.md` para registrar a exceção
  (a política de compactação prevalece sobre "retomada dentro da fase").
  **Acceptance criteria:**
  - [ ] Tabela cobre todos os agentes de `harness-conf/agents/`.
  - [ ] Política de compactação redigida em texto autocontido, sem códigos
        do plano.
  - [ ] Premissa 7 ajustada; `docs/workflow-definicao-escopo.md`
        verificado quanto a menções de sessão (ajustar se contradisser).
  - [ ] Sincronia workflow↔agentes preservada.
  **Verification:** leitura cruzada AGENTS.base.md ↔ workflow; suíte
  `tests/agents/` passa.
  **Dependencies:** Task 3 (base já enxuta), Task 8 (roteamento coerente
  com o mapa de permissions).
  **Files likely touched:** `harness-conf/AGENTS.base.md`,
  `docs/workflow-agentes-dev.md`, talvez
  `docs/workflow-definicao-escopo.md`
  **Estimated scope:** Medium

- [x] **Task 11: Normalizar estado manual das skills**
  **Resultado (2026-09-23):** sem commit (nada versionado alterado).
  Bootstrap OK: symlink único de `skills` restaurado (backup em
  `~/.config/opencode-backup/20260923-170938`); symlinks de agents,
  commands, opencode.json e scripts apontando para o repo; AGENTS.md global
  regenerado com os blocos novos (Roteamento, Autonomia, Compactação,
  code-explorer-priority); 33 skills resolvidas (incluindo
  writing-for-agents); Copilot sincronizado (33 skills, 12 agents, 4
  commands).
  **FECHAMENTO DA FASE 3 (2026-09-23):** revisor independente validou os
  7 itens (Task 8 mapa v4 sem divergências skill a skill; Task 9 quatro
  casos com fixtures; Task 10 conteúdo idêntico aos rascunhos aprovados;
  Task 11 ambiente sincronizado; suíte 831 passed, 1 failed pré-existente
  JAVA_HOME, 31 deselected; higiene dos commits). Achado único: documental
  (omissão de browser-testing:qa e soma do deny no plano), corrigido em
  `05eece3` e REVALIDADO por nova instância do revisor: APROVADO. Fase 3
  tecnicamente concluída.
  **Description:** desfazer o diretório manual `~/.config/opencode/skills`
  (7 symlinks individuais) e restaurar o symlink único de bootstrap:
  rodar `bash ./scripts/bootstrap_repo/configurar-repo.sh --yes` (o
  adapter faz backup_move + symlink da pasta inteira).
  **Acceptance criteria:**
  - [ ] `~/.config/opencode/skills` é symlink único para
        `harness-conf/skills`.
  - [ ] Backup do estado anterior criado pelo próprio adapter; 31 skills
        resolvidas.
  **Verification:** `ls -la ~/.config/opencode/`; `ls
  ~/.config/opencode/skills/ | wc -l` = 31.
  **Dependencies:** Tasks 1-8 (conteúdo final das skills já pronto).
  **Files likely touched:** nenhum no repo (estado local).
  **Estimated scope:** Small

**Checkpoint 3 (commits):** `feat(agents): permissions de skills por
agente`; `test(agents): estende consistência para o mapa de permissions`;
`docs(workflow): roteamento de agentes e política de compactação`.

### Fase 4: Piloto e insumo

- [x] **Task 12: Piloto do ai-memory**
  **Parte 1 CONCLUÍDA (2026-09-23, instalação, sem commit):** versão real
  2.4.0 (mais nova que a v1.29.0 da D2; quick-start oficial mudou para
  Docker + wrapper). Instalado user-space: wrapper
  `~/.local/bin/ai-memory` (sha256 verificado), container Docker
  `akitaonrails/ai-memory:latest` publicando só em 127.0.0.1:49374,
  volume `~/.local/share/ai-memory/` (wiki markdown git-versionado +
  memory.sqlite FTS5), MCP declarado em `~/.config/opencode/opencode.jsonc`
  (merge por cima do symlink do repo; repo intacto; backup .bak), plugin
  `~/.config/opencode/plugins/ai-memory.ts` com hook pre-compact nos
  eventos experimental.session.compacting/session.compacted. Revisão de
  segurança: APROVADO; zero-LLM (nenhuma key), única rede é o servidor
  local; prompts persistem em texto local (tratar como sensível); binário
  do servidor é build upstream com checksum (não auditável linha a linha).
  Pendências da Parte 2: (1) reiniciar o OpenCode (plugin carrega no
  próximo start; sessões atuais não têm o hook); (2) sessão de trabalho
  real + /compact; (3) medição pelo procedimento registrado
  (baseline/depois via sqlite no `~/.local/share/opencode/opencode.db`,
  tabela message, fronteira session.time_compacting; payback = custo da
  compactação ÷ economia por chamada; cost do provider zai vem 0, aplicar
  tarifa externa); (4) registrar antes/depois aqui e decidir adoção com o
  humano. Smoke test feito e purgado (estado inicial limpo).
  **Roteiro da Parte 2 (aprovado pelo humano 2026-09-23; executar na
  continuação pós-restart):**
  1. Humano reiniciou o OpenCode. Confirmar plugin carregado: após 1
     prompt, `docker exec ai-memory ai-memory status` deve mostrar
     sessão/observações > 0.
  2. Anotar sessionID corrente (sqlite readonly na tabela session).
  3. Trabalho real da medição = Task 13 (consolidação deste plano como
     insumo do devflow), deixando o campo de resultado do piloto para o
     final.
  4. ANTES do /compact: rodar query baseline (requests, input não
     cacheado, cache_read, cache_write, output da session) e anotar.
  5. Pedir ao humano para rodar `/compact`.
  6. Verificar checkpoint na wiki: `find
     ~/.local/share/ai-memory/wiki -path "*sessions*" -name "*.md"`.
  7. Medir DEPOIS (mesma query com time_created >= time_compacting);
     contexto efetivo = tokens.total da última assistant message de cada
     período. Payback em tokens (cost do provider vem 0; US$ só com
     tarifa externa confiável, registrando a tabela usada).
  8. Registrar antes/depois + payback aqui; apresentar ao humano para a
     decisão de adoção.
  **Description:** instalar `akitaonrails/ai-memory` em user-space
  (OpenCode: MCP + hooks), rodar sessão de trabalho real e medir com o
  método do relatório (requests, custo, cache_write antes/depois do
  PreCompact). Registrar resultados no plano. Adoção decidida pelo humano
  com os dados.
   **Acceptance criteria:**
   - [x] Instalação user-space sem sudo/administrador.
   - [x] Hook PreCompact ativo e persistindo resumo antes de compactar.
   - [x] Medição registrada (antes/depois) no plano.
   **Verification:** sessão de teste com compactação disparada; wiki do
   ai-memory com o resumo persistido; comparação de métricas anotada.
   **Resultado da medição (Parte 2, 2026-09-23, sessão
   `ses_f345d5cf7ffeBFsiBoVJtvYCqm`):**
   - ANTES (212 requests acumulados; últimas 3 chamadas): contexto
     efetivo ~88,1-89,0k tokens/chamada (ex.: total 88.137 = input não
     cacheado 376 + cache_read 87.040 + output pequeno embutido no
     total; decomposição aproximada/inferida: as rubricas do DB não
     somam exatas ao total); prefixo quase todo em cache_read, input
     novo <2k/chamada.
   - Compactação: `/compact` às 21:44:50; hook PreCompact persistiu
     checkpoint de 2.931 bytes (~730 tokens) em `sessions/3c55e491-*.md`
     na wiki do ai-memory (verificado; recuperável por sessões futuras).
   - DEPOIS (1ª chamada, 21:45:58): total 55.402 (input não cacheado
     21.492 + cache_read 33.408 + output 400; a soma das rubricas dá
     55.300, residual ~102 tokens de rubrica não exposta no DB).
   - **Redução de contexto: ~88,6k → 55,4k = -33,2k tokens/chamada
     (-37%).** Nuance de cache: a 1ª chamada pós-compact pagou 21,5k de
     input não cacheado (reconstrução do cache); chamadas seguintes
     tendem a input pequeno + cache_read ~55k.
   - Custo único da sumarização: registrado no DB (message de
     compaction, criada 21:43:52Z e concluída 21:44:50Z, logo antes da
     1ª chamada pós): input 33.408 + output 2.331 = ~35,7k.
   - **Payback em tokens de contexto: ~1-2 chamadas** (~35,7k de custo
     único da sumarização ÷ ~33,2k/chamada de economia ≈ 1,1); a partir
     daí, cada chamada transporta 37% menos contexto.
   - Limitações: provider zai reporta `cost`=0 e `cache_write`=0 (sem
     US$ confiáveis sem tarifa externa); `session.time_compacting` não
     populado pelo OpenCode 1.x (fronteira via mtime do checkpoint);
     n=1 chamada pós-compact.
   **Dependencies:** Tasks 1-11 (otimizações implementadas; baseline
   pós-otimização).
   **Files likely touched:** `harness-conf/opencode.json` (se hooks/MCP
   forem declarados no repo; só com aprovação), `plan/otimizacao-custo-con
   texto.md` (resultados)
   **Estimated scope:** Medium

- [x] **Task 13: Materializar o insumo do devflow**
   **Description:** consolidar neste arquivo o estado final da fase AGORA:
   implementado (com SHAs dos checkpoints), resultados do piloto,
   pendências (Copilot CLI, testes faltantes, docs) e decisões; atualizar
   campo Status para o vocabulário do devflow; seção Fase DEVFLOW como
   roteiro do planejamento dele.
   **Acceptance criteria:**
   - [x] Status no vocabulário do devflow; seção Fase DEVFLOW completa.
   - [x] Todo item de D9 fase AGORA marcado como feito/pendente com
         evidência (SHA ou medição).
  **Verification:** leitura do arquivo por um leitor fresco responde "o
  que foi feito, o que falta, por onde continuar".
  **Dependencies:** Tasks 1-12
  **Files likely touched:** `plan/otimizacao-custo-contexto.md`
  **Estimated scope:** Small

**Checkpoint 4 (commits):** piloto (se tocar repo) e
`docs(plan): consolida insumo do devflow`. O arquivo do plano PERMANECE
no repo (é o insumo do devflow; não é removido ao final).

### Situação da fase AGORA — itens de D9 (evidências)

| # | Item | Situação | Evidência |
|---|---|---|---|
| 1 | Permissions por agente (A1) | FEITO | `42b2212` (deny 23 + 69 allows) |
| 2 | Symlink único das skills (A2) | FEITO | bootstrap T11 (sem commit): symlink único + backup `~/.config/opencode-backup/20260923-170938` |
| 3 | Enxugo AGENTS.md do repo (A3) | FEITO | `6b8e6f8` (2712→2590 tokens chars/4) |
| 4 | Enxugo AGENTS.base.md (A4) | FEITO | `6b8e6f8` (1082→1047 tokens) |
| 5 | Descriptions 7 skills core (A5) | FEITO | `ee74995`, `b7fe366` (1355→1130) |
| 6 | Descriptions skills de domínio (A6) | FEITO | `55c5e72`, `f01cc34` (triggers novos; 24 convertidas EN→PT-BR) |
| 7 | Corpos das skills de domínio (A7) | FEITO | `b78379b`, `36447b9`, `c518e73` (-16059 tokens, -26%; revisor) |
| 8 | Roteamento agentes + regra genérico (B1) | FEITO | `c24068d` |
| 9 | Política de compactação (C2/D11) | FEITO | `c24068d` (AGENTS.base.md + premissa 7) |
| 10 | Import writing-for-agents (D10) | FEITO | `f3b294b`, `1801503` (SHA c55ee46, MIT) |
| 11 | Command otimização AGENTS.md (D7) | FEITO | `6b05375`, `1801503` |
| 12 | Teste de consistência estendido | FEITO | `362ab54` (4 casos + fixtures) |
| 13 | Piloto ai-memory (F1/D2) | FEITO (medição) | Parte 1: instalado e auditado (2.4.0, zero-LLM, local-only); Parte 2: medição concluída (contexto -37%, checkpoint persistido, payback ~1,1 chamada; ver Task 12). Adoção: manter user-space (OQ4) |
| 14 | Insumo do devflow (esta seção + Fase DEVFLOW + Status) | FEITO | `7ddfc21` |

Revisões independentes: Fases 1 e 2 aprovadas (com correções `1801503`,
`0c5343d`); Fase 3 aprovada (achado documental resolvido `05eece3`,
revalidado). Suíte final: 831 passed, 1 failed pré-existente (JAVA_HOME),
31 deselected.

## Risks and Mitigations

| Risco | Impacto | Mitigação |
|---|---|---|
| Reescrita quebra triggers de ativação da skill | Médio | triggers canônicos preservados; leitura cruzada description↔corpo; devflow revisa |
| Permissions escondem skill que agente precisa | Alto | mapa deriva das tabelas dos próprios agentes; teste de consistência (Task 9); allow conservador em dúvida |
| Command remove conteúdo operacional de AGENTS.md | Alto | nunca aplica sem diff + aprovação humana; no-op test; cobertura de regras no relatório |
| Upstream writing-for-agents com conteúdo malicioso | Médio | revisão de segurança total na importação (regra do repo); UPSTREAM.md com SHA |
| ai-memory altera config global indevidamente | Médio | instalação user-space; mudanças no repo só com aprovação; rollback removendo hooks |
| Sessão longa da fase infla o próprio custo | Médio | aplicar a própria política: estado persistido + nova sessão quando o histórico virar ruído |
| Testes mínimos deixam regressão passar | Médio | rodar suíte completa e registrar falhas pré-existentes; completar é da fase DEVFLOW |
| Enxugo remove gotcha não-óbvio | Médio | filtro "descobre em 10s?" por linha; dúvida = manter; revisão humana do diff |
| Sync de upstream desfazer as reescritas | Alto (analisado 2026-09-23: NÃO ocorre) | `_copy_skill_md` só copia SKILL.md inexistente; guardas de teste cobrem as 5 famílias de sync. Convivência: UPSTREAM.md é regenerado pelo sync preservando só a seção "## Adaptacao da description" (anotações locais vivem nela); writing-for-agents fora do sync até a DEVFLOW registrar com `extra_fields` para `description_lang`/`description_note`. Melhoria decidida (D13): diff assistido + freeze, na fase DEVFLOW |

## Open Questions

1. RESOLVIDA (2026-09-22): corte final registrado em D9; consolidação na
   seção "Fase DEVFLOW (roteiro do próximo ciclo)".
2. RESOLVIDA (2026-09-23): humano aprovou converter a description do
   writing-for-agents para PT-BR com triggers; `description_lang` +
   `description_note` no UPSTREAM.md da skill (T1).
3. RESOLVIDA (2026-09-23): mapa v4 aplicado (T8) e guardado pelo teste de
   consistência estendido (T9).
4. RESOLVIDA (2026-09-23): humano decidiu MANTER o ai-memory em
   user-space (MCP no `opencode.jsonc` do usuário, plugin em
   `~/.config/opencode`, Docker local). Repo permanece intocado pelo
   piloto; migração da config para a fonte de verdade do repo vira item
   opcional da fase DEVFLOW (item 6 do roteiro).

## Fase DEVFLOW (roteiro do próximo ciclo)

Insumo: este arquivo (decisões D1-D13, seção "Situação da fase AGORA",
resultados do piloto na Task 12). O devflow parte daqui para planejar a
fase DEVFLOW com o humano.

Itens do roteiro (origem D9 + D13 + pendências registradas):

1. Revisar e expandir o implementado (fases 1-3 deste plano) com visão
   fresca: auditar enxugos, descriptions, corpos e permissions.
2. Aplicar ao Copilot CLI o que ficou só no OpenCode (adapter Copilot
   materializa cópia; avaliar permissions por agente e o command de
   otimização de AGENTS.md; D11: isolamento por harness se a herança do
   AGENTS.base.md for indesejada no Copilot).
3. D13 (prioritária): mecânica de sync diff assistido + freeze no
   `opencode-skills`: comando `opencode-skills diff NOME` (diff upstream
   base→novo com aplicação assistida) e campo `sincronizacao: congelada`
   no UPSTREAM.md; registrar a writing-for-agents no CLI com
   `extra_fields` (`description_lang`, `description_note`).
4. Completar testes faltantes: suíte completa, checklist pós-sync do
   AGENTS.md do repo (consistência workflow↔agentes já coberta por
   `tests/agents/test_workflow_consistency.py`).
5. Docs: README/seção de dependências se o ai-memory mudar premissas de
   instalação; manter sincronia workflow↔agentes (regra do repo).
6. Opcional: migrar a config do ai-memory do user-space para o repo
   (decisão de adoção 2026-09-23: manter user-space; só migrar se a
   operação user-space virar ponto de dor ou exigir replicação).
7. Dívidas conhecidas: linhas >120 pré-existentes em vários
   `harness-conf/agents/*.md`; 1 failed pré-existente na suíte
   (`tests/product_tests/test_concordion_spec_infra.py`, JAVA_HOME).

Estado para retomada: campo `Status` no topo; evidências na seção
"Situação da fase AGORA"; resultado do piloto na Task 12.

## Ciclo 2 — VALIDAÇÃO

Verificação de estado do `docs/README.md` e da seção "Testes por
Especialidade" no início do 2º ciclo (2026-09-23), pelo
`curador-produto`. Somente leitura do repo: nenhuma suíte executada
(execução é da fase Testes) e nenhum arquivo alterado além desta seção.

### Veredito

OK com ressalvas: estrutura íntegra e coerência bidirecional confirmada;
1 achado de desatualização (melhoria) e 1 pergunta pendente de decisão
humana. Nenhuma lacuna bloqueante.

### Verificações

| Item | Esperado | Evidência | Status |
|---|---|---|---|
| `docs/README.md` existe | arquivo presente | 263 linhas em `docs/README.md` | OK |
| Seções obrigatórias | Definição de Escopo; Elementos de Especificação; Estratégias de Indexação; Testes por Especialidade | todas presentes, sem seções órfãs | OK |
| Suíte backend | `testes-produto/backend` cobrindo pytest `-m all` + cobertura >=70%, ruff, shellcheck, PSScriptAnalyzer, Concordion | wrapper existe; `src/opencode_config/product_tests/backend.py` implementa todos os checks da spec | OK |
| Suíte segurança | `testes-produto/seguranca` cobrindo gitleaks, pip-audit, bandit, Concordion | wrapper existe; `src/opencode_config/product_tests/security.py` implementa todos; retry 3x em `src/opencode_config/product_tests/process.py` | OK |
| Agregador | `testes-produto` chamando as 2 suítes; JSON `{status, findings[]}`; exit 0/1; sem argumentos; crash = bloqueante | `testes-produto/__main__.py` + `src/opencode_config/product_tests/aggregator.py` (`SUITE_NAMES=("backend","seguranca")`); console script em `pyproject.toml` | OK |
| Suíte meta | `testes-produto/tests/` cobrindo interface e proibições; fora do `-m all` | `testes-produto/tests/test_interface_meta.py` (5 testes); `testpaths=["tests"]` e `omit` da meta no `pyproject.toml` | OK |
| Coerência `AGENTS.md` | tabela índice (backend, segurança) + agregador + link âncora; sem spec duplicada | seção "Testes por Especialidade" do `AGENTS.md` bate 1:1 com o `docs/README.md`; subseções de spec não copiadas | OK |
| Artefatos de spec | destinos da tabela de Elementos de Especificação existirem | `docs/specs/Backend.md`, `docs/specs/Seguranca.md`, `docs/specs/rnf-gerais.md`, `docs/adr/0001`–`0006`, `docs/adr/diagrama-c4-l{1,2,3}.md` presentes | OK, exceto Achado B |

### Achados de Documentação

**A — Retrofit dos ADRs legados já concluído (frase desatualizada).**
- Achado: `docs/README.md`, subseção "ADR (Arquitetura)", afirma que os
  6 ADRs legados (`docs/adr/0001`–`0006`) "recebem retrofit" como
  "trabalho do ciclo de construção desta curadoria". Verificado: os 6
  já têm seção "Asserções executáveis" com diretivas
  `execute`/`assertEquals` — a pendência declarada está cumprida.
- Ação: editar o trecho para estado concluído (tempo passado), em
  trabalho de curadoria futuro, com aprovação seção a seção do humano.
- Severidade: melhoria.

**B — Destino `docs/specs/regras-negocio.md` sem artefato.**
- Achado: a tabela de Elementos de Especificação do `docs/README.md`
  define `docs/specs/regras-negocio.md` como destino das Regras de
  Negócio; o arquivo não existe em `docs/specs/`.
- Ação: RESOLVIDA pela resposta da Pergunta 1 (2026-09-24): é lacuna;
  o artefato é criado neste ciclo 2, com o `curador-produto`
  (referência cruzada: "Dependências externas registradas" em
  `## Ciclo 2 — PLANEJAMENTO`).
- Severidade: melhoria (definida pela resposta da Pergunta 1).

### Perguntas

1. RESPONDIDA (2026-09-24): `docs/specs/regras-negocio.md` ausente É
   lacuna, não omissão intencional. Decisão do humano: criar o artefato
   neste ciclo 2; a criação é task do `curador-produto` (ver
   "Dependências externas registradas" em `## Ciclo 2 — PLANEJAMENTO`).
   Corpo original da pergunta: o arquivo ausente seria intencional (o
   artefato nasceria só quando o analista elicita RNs, ao contrário de
   `docs/specs/rnf-gerais.md`, que tem regra de presença permanente) ou
   lacuna para a curadoria tratar?

### Observações de contexto

- O check Concordion das duas suítes exige JDK + Gradle em user-space;
  a dívida conhecida do JAVA_HOME (`tests/product_tests/
  test_concordion_spec_infra.py`, 1 failed pré-existente) já está
  registrada no roteiro "Fase DEVFLOW", item 7 — não é lacuna do
  `docs/README.md`.

## Ciclo 2 — PLANEJAMENTO

Planejamento do 2º ciclo (fase DEVFLOW). Escopo fechado pelo humano em
2026-09-23: os 7 itens do roteiro "Fase DEVFLOW" + a frente
"comportamento de custo" como 8º item, aprovada no replanejamento de
2026-09-24 (correção da contagem, achado 5 da revisão); sem UI e sem
modelagem de dados nova: as fases `front` e `dba` do workflow não se
aplicam a este ciclo. Após esta seção, `sec` e `qa` planejam suas partes.

Replanejamento (2026-09-24): P1-P5 respondidas pelo humano e requisitos
novos da frente "comportamento de custo" incorporados (ver
`### Decisões do humano (2026-09-23/24)`); tasks E13 e E14 acrescentadas;
backlog futuro registrado no fim da seção.

### Decisões do humano (2026-09-23/24)

Respostas às Perguntas P1-P5 do eng-software, fechadas pelo humano em
conversa mediada (2026-09-23/24) e incorporadas a este plano em
2026-09-24 pelo eng-software, a partir do prompt do devflow, com
fidelidade total. Decisões FECHADAS: não reabrir.

### Decisões do ciclo (2026-09-27)

- **Mapa de modelos atualizado:** todos os subagentes de execução usam
  `opencode/gpt-6-luna` (zen, reasoning high); o revisor usa
  `zai-coding-plan/glm-5.3`.
- **Autonomia:** o devflow avança os gates operacionais sem parar no humano,
  exceto quando houver bloqueantes.
- **Compactação sem humano disponível:** cada task registra uma subseção
  nova e autocontida neste plano.

**P1 — ai-memory na config canônica (E10): opção A com acréscimos.**
- Bloco `mcp.ai-memory` no `harness-conf/opencode.json` (fonte canônica).
- O BOOTSTRAP provisiona o ai-memory completo em user-space, idempotente,
  sem sudo: wrapper `~/.local/bin/ai-memory`, container Docker
  `akitaonrails/ai-memory:latest` (publicando só em 127.0.0.1), volume
  `~/.local/share/ai-memory/`, plugin/hooks via instalador oficial
  (`ai-memory install-hooks`; plugin NÃO é versionado: é artefato
  regenerável). Só declarar o bloco MCP não funciona em máquina nova;
  provisionamento é parte da task.
- Docker ausente: dependência com instrução user-space, padrão atual do
  bootstrap (avisar e instruir, não falhar mudo, sem sudo).
- jsonc manual do usuário (`~/.config/opencode/opencode.jsonc`) removido
  com backup; README com provisionamento e rollback.
- Copilot: prever funcionamento nos dois harnesses. Sondar suporte a MCP
  do Copilot CLI durante o planejamento/execução; se suportar, o adapter
  Copilot declara o ai-memory (MCP dá wiki/consultas/handoffs); hooks de
  compactação ficam limitados aonde existirem (documentar como limitação).
  Se não suportar MCP: registrar limitação documentada.

**P2 — amostra da auditoria (E7): MÉDIA, 16 skills.**
- As 7 core inteiras + 4 com upstream + 4 de domínio locais +
  writing-for-agents.
- Regra de expansão aprovada: se forem encontrados muitos problemas,
  expandir para as 33.

**P3 — fluxo de diff/sync (tasks E1-E4): fluxo de 4 passos definido pelo
humano (ISTO É a especificação; detalhes internos de implementação são
livres, o critério é eficiência).**
1. O sync identifica mudanças SEM aplicar nada (detecção é read-only;
   nada é escrito antes da decisão).
2. O agente verifica: vale a pena incorporar algo? Não vale?
3. O agente mostra ao humano, resumidamente, o que mudou, com sua
   recomendação (agregar ou não), e pergunta se o humano quer congelar.
   Se o humano decidir agregar, o agente sugere as modificações seguindo
   as regras do repo e a skill writing-for-agents (aplicação assistida,
   nunca automática).
4. O UPSTREAM.md é atualizado com base na decisão: SHA novo quando a
   atualização foi aplicada; RECUSA sem congelar mantém o SHA anterior
   (a pendência reaparece na próxima detecção); congelada sai do sync e
   da detecção.
Precisões: congelar/descongelar é decisão humana; o agente pode escrever
o campo `sincronizacao: congelada` executando decisão explícita do
humano; nenhum subcomando do CLI cria/remove esse campo sozinho.
Internos (granularidade família/skill, formato textual, 1 clone por
execução etc.) ficam a critério da implementação, priorizando eficiência.

**P4 — skills no Copilot (E6): paridade de resultado com o filtro do
OpenCode (desenho definido pelo humano).**
- Adapter Copilot copia para a pasta de skills do Copilot APENAS as 10
  skills globais.
- As 23 skills de domínio vão para uma pasta auxiliar FORA da descoberta
  automática do Copilot (ex.: `~/.copilot/referencias/skills/`).
- Na CÓPIA do Copilot (nunca no fonte do repo), o adapter acrescenta no
  corpo de cada agente um bloco gerado com a description COMPLETA de
  cada skill dele + o caminho COMPLETO (absoluto, resolvido na máquina)
  do arquivo da skill. O agente lê a skill sob demanda pelo caminho.
- O bloco é derivado do MESMO mapa de permissions do OpenCode (deny
  global + allow por agente; uma fonte única de verdade, já guardada por
  `tests/agents/test_workflow_consistency.py`).
- Repo fonte permanece limpo; o bloco só existe na cópia materializada.

**P5 — AGENTS.base.md: seções aprovadas (texto final do humano, verbatim;
polimento de largura de linha é permitido, conteúdo não).**
- A seção "Compactação de contexto" atual é SUBSTITUÍDA pelo texto
  aprovado abaixo; entra seção nova "Chamadas de ferramentas".
- A regra de precedência sobre a premissa 7 (`docs/workflow-agentes-dev.md`)
  é REMOVIDA do AGENTS.base.md. A premissa 7 do workflow segue válida
  como está; verificar durante a execução se ela precisa de ajuste de
  redação, registrando se sim.

Texto aprovado da seção de compactação:

```
## Compactação de contexto
- Etapa concluída e resultado salvo: avalie compactar antes de iniciar
  a próxima. Compensa quando o histórico já é grande e ainda virão
  muitas chamadas; com contexto pequeno ou pouco trabalho restante, o
  custo da compactação supera a economia: não compacte.
- Reduza o contexto por conta própria, com qualquer mecanismo
  disponível no harness (compactação, nova sessão ou spawn com estado
  persistido em arquivo, ou equivalente). Sem mecanismo disponível ou
  suficiente, peça ao humano.
- Segure o crescimento: leia trechos (offset/limit) e consultas
  direcionadas; não reinsira arquivos e logs completos no contexto.
- A auto-compactação por threshold é rede de segurança, não plano:
  se ela disparar, a fronteira foi perdida.
```

Texto aprovado da seção nova:

```
## Chamadas de ferramentas
- Agrupe operações independentes na mesma resposta: leituras, greps,
  globs e comandos sem dependência entre si saem juntos, em paralelo.
- Espere só quando houver dependência real: se B precisa do resultado
  de A, A primeiro, B depois.
```

**Requisitos novos (frente "comportamento de custo"; origem: relatório de
custos + decisões humanas):** as duas seções acima substituem/aumentam o
que era a política D11 do ciclo 1. Isso É escopo deste ciclo (task E13).
Impactos planejados: AGENTS.base.md, AGENTS.md global gerado, sincronia
workflow↔agentes, testes de largura de linha e de consistência.

**Sondagem MCP do Copilot CLI (2026-09-24, eng-software; insumo para
E10, não decisão):** o Copilot CLI SUPORTA MCP custom: config de usuário
em `~/.copilot/mcp-config.json` (objeto `mcpServers`; tipos local/stdio
e http/sse; command/args/env; filtro de tools; timeout) e config de
projeto em `.mcp.json` na raiz do workspace (descoberta do cwd até o
git root desde v1.0.11). O caminho "adapter Copilot declara o ai-memory"
da P1 é viável; o mecanismo exato de declaração (merge preservando
servers pré-existentes do usuário) é detalhe da execução de E10.

**Refinamento da P1 (decisão humana de 2026-09-24, na revisão do plano)
— Docker ausente/MCP: princípio TUDO-OU-NADA.**
- Provisionamento incompleto NÃO declara o MCP em NENHUM harness.
- Docker ausente: o bootstrap interrompe o provisionamento do ai-memory,
  avisa com instrução user-space (sem sudo) e NÃO injeta o bloco
  `mcp.ai-memory` (nem OpenCode, nem Copilot).
- Resolvido o pré-requisito e reexecutado o bootstrap, o provisionamento
  é completado e só então o bloco é injetado. Rollback remove o bloco
  junto com o resto do provisionamento.
- O mecanismo de injeção condicional (marcador de estado, filtro do
  adapter) é internalidade da execução.
- Motivação: "nada pela metade" — máquina sem pré-requisito não carrega
  declaração MCP morta nem erro de conexão por sessão. Resolve POR
  DESENHO o achado 4 da revisão do plano (sem "erro esperado de
  conexão").

### Engenharia (eng-software)

#### Regras de Produto (eng-software)

| Regra | Descrição | Exceções |
|---|---|---|
| Freeze por skill | `sincronizacao: congelada`: sync, update e detecção pulam | escrita só por decisão humana |
| Marcação no list | `list` exibe o estado de congelada | nenhuma |
| UPSTREAM persistente | UPSTREAM.md nunca é apagado pelo CLI | regeneração preserva campo e seções |
| Detecção read-only | identificação de mudanças sem escrever nada; nada é escrito antes da decisão | nenhuma |
| UPSTREAM pós-decisão | SHA novo se aplicado; recusa sem congelar mantém o SHA; congelada sai da detecção | nenhuma |
| Aplicação assistida | SKILL.md só muda por sugestão do agente (writing-for-agents) sob decisão humana | nenhuma |
| Internos do diff | granularidade, formato e clones por execução: livres na implementação | critério: eficiência |
| Seções aprovadas do base | compactação e chamadas de ferramentas verbatim; só polimento de largura | nenhuma |
| Provisionamento ai-memory | user-space idempotente, sem sudo; Docker ausente: sem bloco MCP (tudo-ou-nada) | nenhuma |
| Skills no Copilot | 10 globais na descoberta; 23 em pasta auxiliar; bloco por agente só na cópia | nenhuma |
| Amostra da auditoria | 16 (7 core + 4 upstream + 4 locais + wfa); expandir para 33 se muitos problemas | nenhuma |
| Suíte do ciclo | `-m all` verde; `agent_eval` fora (31 deselected) | falha de ambiente é bloqueante |

Precisão do freeze (P3): o agente PODE escrever o campo
`sincronizacao: congelada` executando decisão explícita do humano;
nenhum subcomando do CLI cria ou remove esse campo sozinho.

#### Diagnóstico da base (sondagem 2026-09-23)

- CLI `opencode-skills` (`src/opencode_config/cli/skills_sync.py`): 5
  famílias em `SPECS`; clone upstream shallow (`--depth=1`, sem o SHA base
  no histórico); `_copy_skill_md` só copia SKILL.md inexistente;
  `_write_upstream` regenera o UPSTREAM.md preservando apenas a seção
  `## Adaptacao da description`; writing-for-agents NÃO registrada
  (UPSTREAM.md manual com fluxo manual em linha única). 33 skills, 16 com
  UPSTREAM.md.
- Adapter Copilot (`src/opencode_config/harnesses/copilot.py`):
  `convert_agent_frontmatter` ignora `permission.skill`; `_sync_skills`
  copia as 33 skills sem filtro; `_COMMAND_DESCRIPTIONS` cobre 3 dos 4
  commands (`otimizar-agents-md` usa fallback genérico);
  `_sync_agents_base` copia o AGENTS.base.md integral para
  `.copilot/AGENTS.md`.
- Sondagem Copilot CLI (web, 2026-09-23): sem deny/allow de skills por
  agente (não há equivalente ao `permission.skill`); frontmatter `skills:`
  faz PRELOAD de corpos no contexto inicial do agente (suportado); tool
  `skill` em `tools:` suportada; escopo `skill/nome` NÃO suportado;
  enable/disable de skill é global por usuário (`copilot skill`).
- Dívida de linhas: 31 linhas >120 colunas em 8 arquivos de
  `harness-conf/agents/*.md` (analista 12, revisor-historia 11, qa 2, sec
  2, curador-produto/dba/eng-software/rev 1 cada).
- ai-memory atual: MCP no `~/.config/opencode/opencode.jsonc` (arquivo do
  usuário, combinado com o `opencode.json` symlinkado do repo); plugin
  `~/.config/opencode/plugins/ai-memory.ts` AUTO-GERADO por
  `ai-memory install-hooks` (o gerador sobrescreve a cada re-execução);
  container Docker local em 127.0.0.1:49374; volume
  `~/.local/share/ai-memory/`.
- Testes existentes: `tests/skills_mgmt/test_sync.py` (40 testes: 5
  famílias, check-only, preservação de SKILL.md e da adaptação);
  `tests/harnesses/test_copilot.py` (conversão de frontmatter,
  commands→skills, backup, skip de agentes OpenCode-only);
  `tests/agents/test_workflow_consistency.py` (guarda do mapa de
  permissions do ciclo 1). Suíte corrente: 832 coletados em `-m all`.

#### Tasks

- [ ] **E1: Freeze de sincronização por skill**
  **Descrição:** campo `sincronizacao: congelada` no UPSTREAM.md;
  `sync` da família pula skills congeladas (sem tocar arquivos) com status
  explícito; `update` da skill congelada retorna status claro sem executar
  comando; `list` marca congeladas; a detecção de mudanças (E2) também
  exclui congeladas (P3: congelada sai do sync e da detecção);
  `_write_upstream` preserva o campo na regeneração (defesa, análoga à
  preservação da adaptação). Congelar/descongelar é decisão humana: o
  humano edita o UPSTREAM.md, ou o agente escreve o campo executando
  decisão explícita do humano; nenhum subcomando do CLI cria ou remove o
  campo sozinho. Documentar a regra na seção "Upstream de Skills
  Externas" do AGENTS.md.
  **Critérios de aceitação:**
  - [ ] Sync de família com 1 skill congelada: arquivos dessa skill
        intocados, demais skills sincronizadas, status reporta a skill
        pulada.
  - [ ] `update` em skill congelada: status explícito, zero comandos
        executados.
  - [ ] `list` exibe marcação de congelada.
  - [ ] Regeneração de UPSTREAM.md preserva o campo `sincronizacao`.
  - [ ] Nenhum subcomando cria ou remove o campo sozinho (só decisão
        humana: edição manual ou agente executando ordem explícita).
  **Verificação:** `.venv/bin/pytest tests/skills_mgmt/ -m all` com
  fixtures de UPSTREAM congelado.
  **Dependências:** nenhuma.
  **Arquivos prováveis:** `src/opencode_config/cli/skills_sync.py`,
  `tests/skills_mgmt/test_sync.py`, `AGENTS.md` (seção upstream).
  **Escopo:** M.

- [ ] **E2: Detecção de mudanças de upstream (fluxo de 4 passos, P3)**
  **Descrição:** novo subcomando de detecção read-only que alimenta o
  fluxo aprovado na P3 (ISTO É a especificação; detalhes internos são
  livres, o critério é eficiência): (1) a detecção identifica mudanças
  SEM aplicar nada (nada é escrito antes da decisão); (2) o agente
  avalia o que vale a pena incorporar; (3) o agente mostra ao humano,
  resumidamente, o que mudou, com sua recomendação (agregar ou não), e
  pergunta se o humano quer congelar; se o humano decidir agregar, o
  agente sugere as modificações seguindo as regras do repo e a skill
  writing-for-agents (aplicação assistida, nunca automática); (4) o
  UPSTREAM.md é atualizado com base na decisão: SHA novo quando a
  atualização foi aplicada (sync executado pós-decisão); RECUSA sem
  congelar mantém o SHA anterior (a pendência reaparece na próxima
  detecção); congelada sai do sync e da detecção. Internos
  (granularidade família/skill, formato textual da saída, 1 clone por
  execução, fetch do SHA base com fallback para clone completo se o
  upstream recusar) ficam a critério da implementação. A saída precisa
  dar ao agente o resumo por skill que o passo 3 consome (SHAs base/novo,
  família, mudanças por arquivo, roteiro curto de aplicação assistida
  com referência ao método writing-for-agents).
  **Critérios de aceitação:**
  - [ ] Detecção read-only: nenhum arquivo local alterado (fixture
        confere conteúdo após a execução).
  - [ ] Família sem mudanças upstream desde o último sync: saída "sem
        mudanças", exit 0.
  - [ ] Fixture git com 2º commit alterando reference e SKILL.md
        upstream: detecção mostra exatamente as mudanças base→novo.
  - [ ] Skill congelada não aparece na detecção.
  - [ ] Recusa sem congelar: SHA anterior mantido; a mesma pendência
        reaparece na detecção seguinte.
  - [ ] Aplicação aprovada: sync regenera o UPSTREAM.md com o SHA novo.
  - [ ] SHA base ausente ou inválido no UPSTREAM.md: erro acionável.
  - [ ] Saída organizada por skill (insumo do resumo mostrado ao humano).
  - [ ] ADR-0007 registrado seguindo a convenção dos ADRs 0001-0006
        (retrofitados), incluindo seção "Asserções executáveis".
  **Verificação:** `.venv/bin/pytest tests/skills_mgmt/ -m all` (fixtures
  git de 2 commits); execução manual contra upstream real como validação
  opcional.
  **Dependências:** E1 (freeze e formato do UPSTREAM).
  **Arquivos prováveis:** `src/opencode_config/cli/skills_sync.py`,
  `tests/skills_mgmt/test_sync.py`, `docs/adr/0007-*`.
  **Escopo:** M.

- [ ] **E3: Registrar writing-for-agents no CLI com extra_fields**
  **Descrição:** nova `SyncSpec` (mattpocock/skills, main) e
  `_sync_writing_for_agents`: copia SKILL-MECHANICS.md do path upstream
  `skills/productivity/writing-for-agents/` (SKILL.md só na criação, via
  `_copy_skill_md`); `_write_upstream` passa a preservar também uma seção
  `## Notas locais` (extensão genérica do formato); o UPSTREAM.md atual da
  skill é reescrito pelo CLI com `extra_fields`
  `description_lang: pt-br` e `description_note` (nota de 1 linha; detalhe
  da conversão permanece na seção de adaptação); a seção "Segurança na
  importação" migra para `## Notas locais` (conteúdo preservado); o fluxo
  manual em linha única sai do UPSTREAM; a tabela de sync do AGENTS.md
  ganha a linha `writing-for-agents | opencode-skills sync
  writing-for-agents`.
  **Critérios de aceitação:**
  - [ ] `opencode-skills list` inclui writing-for-agents.
  - [ ] Sync contra fixture (LICENSE MIT + SKILL-MECHANICS.md):
        SKILL-MECHANICS.md copiado, SKILL.md local intocado, UPSTREAM
        regenerado com extra_fields e preservando notas locais.
  - [ ] Conteúdo da revisão de segurança de 2026-09-22 preservado nas
        notas locais.
  - [ ] Tabela do AGENTS.md atualizada.
  **Verificação:** `.venv/bin/pytest tests/skills_mgmt/ -m all`;
  `opencode-skills list`.
  **Dependências:** E1 (preservação estendida do formato).
  **Arquivos prováveis:** `src/opencode_config/cli/skills_sync.py`,
  `tests/skills_mgmt/test_sync.py`,
  `harness-conf/skills/writing-for-agents/UPSTREAM.md`, `AGENTS.md`.
  **Escopo:** M.

- [ ] **E4: Automatizar itens verificáveis do checklist pós-sync**
  **Descrição:** mapear o checklist pós-sync do AGENTS.md do repo;
  automatizar como testes guarda o que é verificável: após o sync
  aplicado (pós-decisão do fluxo da P3) contra upstream avançado
  (fixture git com commit novo), o UPSTREAM.md reflete o
  novo SHA; os arquivos declarados como sincronizados existem localmente e
  batem com o upstream; SKILL.md local nunca é sobrescrito (guarda
  existente, confirmar cobertura). Itens não automatizáveis (revisão de
  segurança do conteúdo novo, decisão de aplicação assistida no SKILL.md)
  seguem manuais e o checklist do AGENTS.md passa a dizê-lo explicitamente.
  **Critérios de aceitação:**
  - [ ] Teste guarda: UPSTREAM.md reflete o SHA novo pós-sync (fixture de
        2 commits).
  - [ ] Teste guarda: arquivos declarados em "Arquivos sincronizados"
        existem e batem após o sync.
  - [ ] Checklist do AGENTS.md distingue itens automáticos (com guarda) de
        manuais.
  **Verificação:** `.venv/bin/pytest tests/skills_mgmt/ -m all`.
  **Dependências:** E1-E3 (formato e famílias finais).
  **Arquivos prováveis:** `tests/skills_mgmt/` (teste novo ou extensão do
  `test_sync.py`), `AGENTS.md`.
  **Escopo:** S.

- [ ] **E5: Copilot, description do command de otimização de AGENTS.md**
  **Descrição:** entrada `otimizar-agents-md` em `_COMMAND_DESCRIPTIONS`
  com texto de ativação em PT-BR no padrão das existentes (sem o fallback
  genérico "Executa o comando ..."); teste cobre a conversão do 4º command.
  **Critérios de aceitação:**
  - [ ] Skill convertida do command com a description específica.
  - [ ] Teste em `tests/harnesses/test_copilot.py` trava a description.
  **Verificação:** `.venv/bin/pytest tests/harnesses/ -m all`.
  **Dependências:** nenhuma.
  **Arquivos prováveis:** `src/opencode_config/harnesses/copilot.py`,
  `tests/harnesses/test_copilot.py`.
  **Escopo:** S.

- [ ] **E6: Copilot — descoberta restrita às skills globais (P4)**
  **Descrição:** conforme desenho aprovado na P4 (paridade de resultado
  com o filtro do OpenCode): o adapter Copilot copia para a pasta de
  skills do Copilot APENAS as 10 skills globais; as 23 skills de domínio
  vão para uma pasta auxiliar FORA da descoberta automática do Copilot
  (ex.: `~/.copilot/referencias/skills/`). A distinção global/domínio
  deriva do MESMO mapa de permissions do OpenCode (deny global do
  `harness-conf/opencode.json`; skills sem deny são globais). O bloco de
  referência no corpo dos agentes é a task E14. README (seção Adapters)
  documenta o desenho novo no lugar da redação de "limitação sem poda".
  **Critérios de aceitação:**
  - [ ] Pasta de skills do Copilot contém somente as skills sem deny
        global (as 10 globais).
  - [ ] As 23 skills de domínio presentes na pasta auxiliar, fora da
        descoberta automática.
  - [ ] Derivação lê o mapa de permissions (fixture trocando uma skill
        de deny muda a cópia).
  - [ ] README Adapters atualizado com o desenho e a pasta auxiliar.
  - [ ] Testes em `tests/harnesses/test_copilot.py` cobrem poda e pasta
        auxiliar.
  **Verificação:** `.venv/bin/pytest tests/harnesses/ tests/agents/ -m
  all`.
  **Dependências:** nenhuma.
  **Arquivos prováveis:** `src/opencode_config/harnesses/copilot.py`,
  `tests/harnesses/test_copilot.py`, `README.md`.
  **Escopo:** M.

- [ ] **E7: Auditoria focada do implementado no ciclo 1**
  **Descrição:** três frentes, conforme escopo (leitura focada, não
  total). (a) Permissions contra uso real: cruzar o mapa v4 (23 deny, 69
  allows) com as menções e o uso nos corpos dos agentes; achados: allow sem
  uso, deny+allow em agente que não menciona a skill, menção de skill sem
  allow. (b) Leitura auditorial completa do AGENTS.md do repo e do
  AGENTS.base.md pós-ciclo 1 (estado final inclui E13). (c) Amostra
  estratificada MÉDIA de 16 skills, aprovada na P2: as 7 core inteiras +
  4 de domínio com upstream + 4 de domínio locais + writing-for-agents;
  regra de expansão aprovada: se forem encontrados muitos problemas,
  expandir para as 33. Conferir
  description↔corpo, triggers, no-op pruning, split acima de ~100 linhas e
  UPSTREAM coerente. Saída: relatório em `/tmp/opencode/` (não versionado)
  com método declarado (o que foi lido, seed da amostra); cada achado vira
  task E-fix registrada nesta seção (escopo S cada); o humano prioriza se
  executa neste ciclo. Esta task não altera código.
  **Critérios de aceitação:**
  - [ ] Relatório cobre (a), (b) e (c) com método declarado.
  - [ ] Divergências de permissions mapeadas com evidência (agente, skill,
        menção ou ausência).
  - [ ] Achados convertidos em tasks E-fix com prioridade; zero achados
        também é registrado.
  - [ ] Sem alteração de código (correções são tasks próprias).
  **Verificação:** revisão do relatório pelo revisor do ciclo; suíte
  `tests/agents/` segue verde.
  **Dependências:** após E9 (estado final dos agentes), E13 (estado final
  do AGENTS.base.md) e E1-E3 (formato final dos UPSTREAMs).
  **Arquivos prováveis:** nenhum no repo (relatório em /tmp; achados
  registrados nesta seção).
  **Escopo:** M (esforço de leitura; executor worker com validação do
  revisor do ciclo).

- [ ] **E8: Resolver o failed pré-existente JAVA_HOME**
  **Descrição:** diagnóstico do ambiente (JDK no cache user-space,
  JAVA_HOME exportada no `.bashrc`, gradle presente); se ausente, instalar
  via bootstrap user-space (`install_java`) e carregar o PATH persistido;
  se JAVA_HOME setada mas inválida, corrigir a fonte do export; validar o
  teste
  `test_render_adr_specs_task_derives_exactly_the_six_adr_specs` passando.
  Sem afrouxar o gate: o teste usa `pytest.fail` corretamente (regra do
  repo); a resolução é de ambiente ou do export, não do teste.
  **Critérios de aceitação:**
  - [ ] `.venv/bin/pytest tests/product_tests/test_concordion_spec_infra.py
        -m all` verde.
  - [ ] Causa raiz registrada (ambiente ou código); se código, correção
        com teste.
  **Verificação:** execução do arquivo de teste; confirmação no gate final
  (E12).
  **Dependências:** nenhuma (executar cedo para destravar suíte verde).
  **Arquivos prováveis:** nenhum no repo (ambiente local).
  **Escopo:** S.

- [ ] **E9: Dívida de linhas acima de 120 colunas em agents/*.md**
  **Descrição:** reflow (sem mudança de texto) das 31 linhas em 8 arquivos
  (analista 12, revisor-historia 11, qa 2, sec 2, curador-produto, dba,
  eng-software, rev 1 cada). Atenção a strings pinadas por testes
  (`test_workflow_consistency` e afins): rodar a suíte após cada arquivo;
  se um pino quebrar por quebra de linha, manter a substring do pino em uma
  linha (ajuste de reflow, não de teste).
  **Critérios de aceitação:**
  - [ ] Varredura de largura (linha >120) retorna 0 ocorrências nos 8
        arquivos.
  - [ ] Suíte `tests/agents/` + `tests/adapters/` verde após cada arquivo.
  - [ ] Diff de revisão mostra só reflow (conteúdo semântico inalterado).
  **Verificação:** verificação de largura + pytest.
  **Dependências:** nenhuma; antes de E7 (auditoria lê estado final).
  **Arquivos prováveis:** 8 arquivos em `harness-conf/agents/`.
  **Escopo:** S.

- [ ] **E10: ai-memory na config canônica + provisionamento no bootstrap
  (P1: opção A com acréscimos)**
  **Descrição:** (1) bloco `mcp.ai-memory` no
  `harness-conf/opencode.json` (fonte canônica; teste de JSON válido);
  (2) o BOOTSTRAP provisiona o ai-memory completo em user-space,
  idempotente, sem sudo: wrapper `~/.local/bin/ai-memory`, container
  Docker `akitaonrails/ai-memory:latest` publicando só em 127.0.0.1,
  volume `~/.local/share/ai-memory/`, plugin/hooks via instalador
  oficial (`ai-memory install-hooks`; plugin NÃO é versionado: é artefato
  regenerável). Só declarar o bloco MCP não funciona em máquina nova;
  provisionamento é parte da task. (3) Docker ausente: princípio
  TUDO-OU-NADA (decisão humana 2026-09-24, ver Decisões) — o bootstrap
  interrompe o provisionamento do ai-memory, avisa com instrução
  user-space (sem sudo) e NÃO injeta o bloco `mcp.ai-memory` em NENHUM
  harness (nem OpenCode, nem Copilot); resolvido o pré-requisito, a
  reexecução do bootstrap completa o provisionamento e só então injeta o
  bloco; rollback remove o bloco junto com o resto. O mecanismo de
  injeção condicional (marcador de estado, filtro do adapter) é
  internalidade da execução. (4) jsonc manual do usuário
  (`~/.config/opencode/opencode.jsonc`) removido com backup. (5) Copilot:
  sondagem de MCP concluída no replanejamento (2026-09-24; ver Decisões)
  confirma suporte (`~/.copilot/mcp-config.json`, stdio/http); o adapter
  Copilot declara o ai-memory com merge preservando servers
  pré-existentes do usuário; hooks de compactação ficam limitados aonde
  existirem (documentar como limitação). (6) README com provisionamento
   e rollback. (7) converter SEC-01..SEC-11 e SEC-21 em asserções da spec
   executável de segurança `docs/specs/Seguranca.md` (spec da suíte
   `testes-produto/seguranca`; E10 NÃO edita o docs/README.md, arquivo do
   curador-produto), com aprovação do humano na revisão (decisão
   2026-09-24, achado 7: critério de aceite, não mais recomendação); T13
   segue guardando os comportamentos em testes automatizados do repo.
  **Critérios de aceitação:**
  - [ ] Bloco `mcp.ai-memory` no `harness-conf/opencode.json`; JSON
        válido (guarda de parse).
  - [ ] Bootstrap idempotente: wrapper + container + volume +
        install-hooks sem sudo; segunda execução não duplica nem refaz.
  - [ ] Docker ausente: bootstrap interrompe o provisionamento, avisa e
        instrui (user-space, sem sudo, sem falha muda); bloco
        `mcp.ai-memory` NÃO injetado em nenhum harness (tudo-ou-nada);
        resolvido o pré-requisito, a reexecução completa e injeta.
  - [ ] jsonc do usuário removido com backup; OpenCode reiniciado
        enxerga o MCP.
  - [ ] Copilot: ai-memory declarado com merge preservando servers
        pré-existentes; limitação de hooks documentada.
  - [ ] README cobre provisionamento e rollback (rollback remove o
        bloco MCP junto com o resto).
   - [ ] SEC-01..SEC-11 e SEC-21 convertidas em asserções da spec
         executável de segurança `docs/specs/Seguranca.md` (E10 não toca
         o docs/README.md, do curador-produto), com aprovação do humano
         na revisão; T13 segue guardando os comportamentos em testes do
         repo.
  - [ ] ADR-0008 registrado seguindo a convenção dos ADRs 0001-0006
        (retrofitados), incluindo seção "Asserções executáveis".
  **Verificação:** `.venv/bin/pytest tests/bootstrap/ tests/harnesses/
  -m all`; `bootstrap --check-only` limpo; execução real do bootstrap em
  ambiente de teste.
  **Dependências:** recomendado após E6/E14 (adapter Copilot estável,
  uma só passada no módulo).
  **Arquivos prováveis:** `harness-conf/opencode.json`,
  `src/opencode_config/bootstrap/*`, `src/opencode_config/harnesses/
  copilot.py`, `tests/bootstrap/` (ou `tests/harnesses/`), `README.md`,
  `docs/specs/Seguranca.md` (asserções), `docs/adr/0008-*`.
  **Escopo:** L.

- [ ] **E11: Docs finais do ciclo**
  **Descrição:** (a) README, seção de dependências, fiel ao estado final:
  ai-memory provisionado pelo bootstrap (E10), desenho de skills do
  Copilot (E6/E14) e seções novas do AGENTS.base.md (E13); (b) DELEGADA
  ao `curador-produto` (delegação aprovada pelo humano em 2026-09-24,
  achado 2; o devflow spawna o curador na execução): docs/README.md,
  subseção "ADR (Arquitetura)", frase dos 6 ADRs legados para tempo
  passado (retrofit Concordion concluído no ciclo anterior), com
  aprovação do humano; o eng-software NÃO executa a edição — o diff
  entra como lote reportado para revisão e commit (ver Dependências
  externas registradas); (c) verificação de sincronia
  workflow↔agentes após E13 (compactação/chamadas de ferramentas e
  premissa 7) e E6/E14 (se agentes ou base mudaram): conferir
  `docs/workflow-agentes-dev.md` e o teste de consistência; (d) registrar
  os ADRs novos do ciclo (ver Sugestões de ADR) onde a
  convenção do repo pedir.
  **Critérios de aceitação:**
  - [ ] README sem menção a premissas removidas e com as novas.
  - [ ] Subseção ADR do docs/README.md sem pendência falsa (execução do
        curador-produto; diff reportado, revisado e commitado pelo
        committer único).
  - [ ] Teste de consistência workflow↔agentes verde.
  **Verificação:** leitura cruzada + `.venv/bin/pytest tests/agents/ -m
  all`.
  **Dependências:** E10, E13, E14 (e demais tasks de código concluídas).
  **Arquivos prováveis:** `README.md`, `docs/README.md`, `docs/adr/*` (se
  ADRs).
  **Escopo:** M.

- [ ] **E12: Gate final de testes do ciclo**
  **Descrição:** rodar a suíte completa do ambiente corrente
  (`.venv/bin/pytest -m all`), sem deixar teste de fora; `agent_eval`
  permanece fora do ciclo (31 deselected). Falha é bloqueante com
  diagnóstico. Registrar contagens na seção de evidências do plano.
  **Critérios de aceitação:**
  - [ ] `-m all` 100% verde (base 832 + testes novos do ciclo).
  - [ ] 0 failed; skips apenas os declarados pela própria suíte (skipif
        de plataforma).
  - [ ] Evidência registrada no plano (contagens).
  **Verificação:** saída do pytest resumida no plano.
  **Dependências:** todas as tasks de código e docs (E1-E11, E13, E14 e
  E-fix executadas, se aprovadas).
  **Arquivos prováveis:** nenhum (verificação).
  **Escopo:** S.

- [ ] **E13: AGENTS.base.md — compactação reescrita + "Chamadas de
  ferramentas" (P5 + requisitos novos)**
  (task nova do replanejamento de 2026-09-24; textos aprovados verbatim
  na subseção de Decisões)
  **Descrição:** substituir a seção "Compactação de contexto" do
  `harness-conf/AGENTS.base.md` pelo texto aprovado (verbatim; apenas
  polimento de largura de linha até 120 colunas é permitido) e criar a
  seção nova "Chamadas de ferramentas" (idem). Remover do base a regra
  de precedência sobre a premissa 7 de `docs/workflow-agentes-dev.md`.
  O realinhamento da redação da premissa 7 é resultado ESPERADO da
  execução (ajuste 2026-09-24 do achado 1 da revisão): o texto vigente
  ainda cita a política D11 e a cláusula de precedência que esta task
  REMOVE, ou seja, já nasce dessincronizado; durante a construção, o
  executor propõe a nova redação alinhada às seções aprovadas
  (compactação por conta própria; auto-compactação por threshold como
  rede de segurança) e a SUBMETE ao humano via devflow ANTES de aplicar
  (regra do repo: mudança em workflow passa pelo humano). P5 não é
  reaberta (a válvula de ajuste de redação já existe na decisão).
  Substitui/amplia a política D11 do ciclo 1 (frente
  "comportamento de custo"). Impactos: AGENTS.md global gerado
  (regenerado pelo adapter na próxima execução do bootstrap; conferir),
  sincronia workflow↔agentes, testes de largura de linha e de
  consistência.
  **Critérios de aceitação:**
  - [ ] Seção "Compactação de contexto" substituída pelo texto aprovado;
        diff mostra só reescrita + ajuste de largura, conteúdo idêntico.
  - [ ] Seção "Chamadas de ferramentas" criada com o texto aprovado.
  - [ ] Regra de precedência sobre a premissa 7 removida do
        AGENTS.base.md.
  - [ ] Nova redação da premissa 7 proposta (alinhada às seções
        aprovadas) e submetida ao humano via devflow ANTES de aplicar;
        decisão do humano registrada (aplicada/ajustada/recusada).
  - [ ] Varredura de largura ≤120 limpa no arquivo; `tests/agents/`
        verde; AGENTS.md global regenerado com as seções novas
        (conferência local do bootstrap).
  **Verificação:** diff revisado pelo humano antes do commit;
  `.venv/bin/pytest tests/agents/ -m all`; varredura de largura.
  **Dependências:** nenhuma (textos aprovados fecham o desenho).
  **Arquivos prováveis:** `harness-conf/AGENTS.base.md`,
  `docs/workflow-agentes-dev.md` (proposta de redação da premissa 7,
  aplicada só após decisão do humano).
  **Escopo:** S/M.

- [ ] **E14: Copilot — bloco de referência de skills no corpo dos
  agentes (P4)**
  (task nova do replanejamento de 2026-09-24; desmembrada de E6)
  **Descrição:** na CÓPIA materializada do Copilot (nunca no fonte do
  repo), o adapter acrescenta no corpo de cada agente um bloco gerado
  com a description COMPLETA de cada skill dele + o caminho COMPLETO
  (absoluto, resolvido na máquina, apontando para a pasta auxiliar) do
  arquivo da skill; o agente lê a skill sob demanda pelo caminho. O
  bloco é derivado do MESMO mapa de permissions do OpenCode (deny global
  + allow por agente), fonte única de verdade guardada por
  `tests/agents/test_workflow_consistency.py`. Agentes sem allow não
  recebem bloco. Repo fonte permanece limpo: o bloco só existe na cópia.
  **Critérios de aceitação:**
  - [ ] Cópia de agente com allow contém o bloco com a description
        completa + caminho absoluto na pasta auxiliar.
  - [ ] Fonte do repo sem o bloco (guarda de teste).
  - [ ] Bloco deriva do mapa de permissions (fixture mudando allow muda
        o bloco).
  - [ ] Caminho absoluto resolvido na máquina (home real, não literal
        `~`).
  - [ ] Testes em `tests/harnesses/test_copilot.py`.
  - [ ] ADR-0009 registrado, SE mantida a opção pelo registro formal,
        seguindo a convenção dos ADRs 0001-0006 (retrofitados),
        incluindo seção "Asserções executáveis".
  **Verificação:** `.venv/bin/pytest tests/harnesses/ -m all`; inspeção
  da cópia materializada em `~/.copilot/`.
  **Dependências:** E6 (pasta auxiliar definida).
  **Arquivos prováveis:** `src/opencode_config/harnesses/copilot.py`,
  `tests/harnesses/test_copilot.py`, `docs/adr/0009-*` (se registrado).
  **Escopo:** M.

- [ ] **E-fix (bloco variável, gerado por E7):** correções pontuais (escopo
  S cada) oriundas dos achados da auditoria; cada achado recebe id próprio
  (E-fix-1, ...), dependência de E7 e prioridade definida pelo humano. Zero
  achados encerra o bloco com registro.

#### Ordem de execução sugerida

1. **Perguntas resolvidas:** P1-P5 respondidas (2026-09-23/24, ver
   Decisões); nada bloqueia.
2. **Wave 1 (sem dependências):** E8 (destraba suíte verde), E5 (S),
   E1 (M), E9 (S), E13 (seções aprovadas do AGENTS.base.md).
3. **Wave 2 (fundação do sync, após E1):** E2, E3, E4.
4. **Wave 3 (Copilot):** E6, E14 (após E6), E10 (após E6/E14, para
   tocar o adapter Copilot uma vez só).
5. **Wave 4 (auditoria, estado final):** E7 (após E9, E13 e E1-E3).
6. **Wave 5 (fechamento):** E-fix (se o humano aprovar execução neste
   ciclo), E11, E12 (gate final).

Racional: fundação D13 (E1→E2→E3→E4) fica em sequência no mesmo módulo,
commits atômicos por task; E13 cedo para a auditoria (E7) ler o estado
final do AGENTS.base.md; frente Copilot em sequência (E6→E14→E10) para
não retrabalhar o adapter; auditoria lê estado final das frentes de
código que ela audita; docs consolidam no fim; gate fecha o ciclo.

#### Checkpoints de commit (Conventional Commits, PT-BR)

| Após | Commit proposto |
|---|---|
| E1 | `feat(skills): freeze de sincronizacao por skill no opencode-skills` |
| E2 | `feat(skills): deteccao de mudancas de upstream no opencode-skills` |
| E3 | `feat(skills): registra writing-for-agents no opencode-skills` |
| E4 | `test(skills): automatiza itens verificaveis do checklist pos-sync` |
| E5 | `fix(copilot): description do command de otimizacao de AGENTS.md` |
| E6 | `feat(copilot): restringe descoberta de skills as globais` |
| E9 | `style(agents): reflow de linhas acima de 120 colunas` |
| E10 | `feat(config): declara MCP do ai-memory na config canonica` e `feat(bootstrap): provisiona ai-memory` |
| E13 | `docs(agents): reescreve compactacao e adiciona chamadas de ferramentas` |
| E14 | `feat(copilot): bloco de referencia de skills por agente na copia` |
| E11 | `docs(readme): dependencias do ai-memory`; subseção ADR no commit do lote do curador |
| E7, E8, E12 | sem commit (relatório/ambiente/verificação; E8 commita só se virar código) |

Regra do committer: revisar o diff antes de cada commit; E-fix com
commits próprios conforme aprovadas.

#### Sugestões de ADR

Formato comum (decisão 2026-09-24, achado 8 da revisão): os ADRs novos
seguem a convenção dos ADRs retrofitados 0001-0006, INCLUSIVE a seção
"Asserções executáveis" (diretivas `execute`/`assertEquals`); registrado
como critério de aceite em E2/E10/E14.

- **ADR-0007 (sync de skills: detecção + fluxo de decisão + freeze):**
  registra o fluxo de 4 passos aprovado na P3 (detecção read-only,
  aplicação assistida pós-decisão, regras de SHA pós-decisão) e o campo
  de freeze como evolução do contrato do UPSTREAM.md; escrever em E2 com
  a skill documentation-and-adrs.
- **ADR-0008 (ai-memory na config canônica + provisionamento):** P1
  escolheu A com acréscimos; registra a fonte de verdade no
  `harness-conf/opencode.json` e o provisionamento user-space pelo
  bootstrap (idempotente, sem sudo; Docker ausente: tudo-ou-nada,
  interrompe sem injetar o bloco MCP); escrever em E10.
- **ADR-0009 (opcional; skills de domínio no Copilot):** desenho da P4
  (descoberta restrita às 10 globais + pasta auxiliar + bloco de
  referência derivado do mapa de permissions, só na cópia materializada);
  escrever em E14 se o humano quiser registro formal.

#### Dependências externas registradas

- Curadoria: criação de `docs/specs/regras-negocio.md` é task do
  `curador-produto` (lacuna confirmada pelo humano — resposta formal da
  Pergunta 1 da `## Ciclo 2 — VALIDAÇÃO`, 2026-09-24; destino definido
  na tabela de Elementos de Especificação do docs/README.md). Este plano
  só registra a dependência.
- Delegação E11(b) (aprovada pelo humano em 2026-09-24, achado 2 da
  revisão): a correção da subseção "ADR (Arquitetura)" do docs/README.md
  (frase dos 6 ADRs legados para tempo passado) é executada pelo
  `curador-produto`; o devflow spawna o curador na execução e o diff
  entra como lote reportado ao committer único (eng-software revisa
  antes de commitar).

#### Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| SHA base inacessível no clone shallow | Médio | fallback para clone completo; fixture cobre os dois caminhos |
| Reflow (E9) quebrar pinos de teste | Médio | suíte após cada arquivo; pino mantido em uma linha |
| Auditoria por worker (flash) rasa | Médio | amostragem dupla; seed; expansão para 33 se muitos problemas (P2) |
| Docker ausente ou pull falhar (E10) | Médio | interrompe, instrui, não injeta bloco MCP (tudo-ou-nada); idempotente |
| Bloco de skills (E14) inflar contexto no Copilot | Médio | bloco só na cópia e só com allow; descriptions enxutas |
| Texto aprovado (E13) ter conteúdo alterado | Alto | entrada verbatim, polimento só de largura; diff humano no commit |
| Merge MCP sobrescrever servers do usuário (E10) | Médio | merge preserva pré-existentes; fixture de config ocupada |
| Symlink POSIX do opencode.json (E10) | Médio | adapter não edita symlink; injeção do MCP exige contorno (ver nota) |

Nota do risco do symlink POSIX (E10): no POSIX o
`~/.config/opencode/opencode.json` é symlink do canônico do repo (regra do
repo) e o adapter NÃO edita symlink; com o bloco `mcp.ai-memory` na fonte
canônica, a injeção condicional do tudo-ou-nada (Docker ausente: não injetar
em nenhum harness) precisa CONTORNAR o symlink (ex.: config local adicional
ou filtro na sincronização/cópia materializada). O mecanismo segue
internalidade da decisão (P1); T13/RM-12 guardam o comportamento.

### Segurança (sec)

Análise do ciclo 2 (2026-09-24) sobre as tasks E1-E14 + E-fix e as
decisões P1-P5. Insumo adicional: revisão do piloto (Task 12, APROVADA).
O delta do ciclo não é o ai-memory em si (auditado em user-space), é a
automação: o bootstrap passa a baixar e executar artefatos de terceiros
em toda máquina nova (E10) e o repo passa a versionar conteúdo upstream
novo via sync (E3). Exigências numeradas SEC-01 a SEC-21; o executor as
cumpre como critérios de aceitação de segurança das tasks indicadas.
Perguntas S1/S2 respondidas pelo humano em 2026-09-24 e incorporadas:
imagem sem pin (SEC-02) e egress restrito (SEC-21).

#### E10 — ai-memory no bootstrap e config canônica

O bootstrap passa a executar: download do wrapper, pull de imagem,
execução do instalador oficial (`install-hooks`) e merge MCP no Copilot.
O piloto auditou uma instalação manual; o código do repo amplia isso
para toda máquina que rodar o bootstrap (supply chain sistemática).

- **Integridade e origem (ALTA).** O binário do servidor é build upstream
  não auditável linha a linha; instalador e plugin rodam no host com
  acesso ao conteúdo das sessões; `:latest` é tag móvel e a revisão do
  piloto valeu para o digest daquela data.
  - SEC-01: downloads só da origem fixa (GitHub/Docker Hub do
    akitaonrails/ai-memory), HTTPS com validação de cadeia; proibido
    `-k`, `--insecure` ou bypass de TLS; falha de certificado segue o
    fluxo de CA PEM do README.
  - SEC-02: integridade com valor esperado registrado no repo: sha256 do
    wrapper como constante do código do bootstrap. Hash buscado na mesma
    origem do download não conta como verificação de origem. Imagem SEM
    pin (decisão S1, 2026-09-24): mantém `akitaonrails/ai-memory:latest`;
    risco de drift aceito pelo humano: máquinas podem rodar digests
    diferentes. Observar na prática: divergência de comportamento entre
    máquinas; a revisão de segurança do piloto vale para o digest
    auditado da data.
  - SEC-05: o output do bootstrap registra o sha256 do plugin
    `ai-memory.ts` gerado; hash diferente entre execuções sem troca de
    versão gera aviso explícito (detecção de drift do gerador).
  - Testes: download sem verificação de hash falha (fixture); comando de
    download não contém flags insecure.
- **Exposição de rede (ALTA se violada).** O servidor local não exige
  autenticação; publicar em 0.0.0.0 exporia a wiki (prompts em texto)
  para a rede local.
  - SEC-03: porta publicada EXCLUSIVAMENTE em 127.0.0.1; nunca `-P` nem
    `0.0.0.0`. Teste: assert no comando docker run gerado
    (`127.0.0.1:PORTA:PORTA`). Runtime conferido no roteiro manual.
  - SEC-04: a config canônica aponta porta fixa (49374), igual em toda
    máquina; porta ocupada por processo que não responda como ai-memory
    aborta o provisionamento com instrução acionável, nunca troca de
    porta em silêncio (o MCP falaria com processo estranho).
  - SEC-21 (decisão S2, 2026-09-24): saída de rede do container
    RESTRITA já neste ciclo, como critério de aceitação de segurança de
    E10: rede do container sem rota de saída padrão (ex.: rede internal
    do Docker), só o necessário para o serviço operar localmente; egress
    aberto nunca é o padrão. Verificação: o serviço sobe e opera com a
    rede restrita (teste do comando docker run gerado + passo 9 do
    roteiro manual). Diagnóstico: update interno do serviço que precise
    de rede é executado regenerando imagem/config FORA da rede restrita;
    abrir egress permanente por padrão é proibido.
- **Dados sensíveis (MÉDIA).** Prompts persistem em texto claro no volume
  `~/.local/share/ai-memory/` (registrado no piloto).
  - SEC-07: README trata o volume como dado sensível (não versionado,
    sem cópia para destino compartilhado); rollback não apaga o volume;
    remoção é passo explícito e opcional do humano.
- **Rollback (BAIXA).**
  - SEC-08: rollback documentado e verificável: parar/remover container,
    remover plugin e bloco MCP, restaurar jsonc do backup; sem resíduo
    ativo (hooks param de rodar). Item do roteiro manual.
- **Idempotência (MÉDIA).** Re-download a cada execução amplia a janela
  de supply chain.
  - SEC-06: segunda execução não re-baixa nem re-puxa (checa presença e
    hash antes); hash divergente em item já instalado é erro bloqueante,
    nunca refaz por cima em silêncio. A instrução de bloqueio inclui o
    CAMINHO DE UPGRADE (decisão 2026-09-24, achado 3 da revisão):
    notificar a divergência, instruir a remoção do artefato antigo (ou
    confirmação explícita com backup) e reexecutar o bootstrap;
    idempotência e nunca sobrescrever às cegas permanecem.
- **Extensão ao Copilot (BAIXA/MÉDIA).**
  - SEC-10: backup do `~/.copilot/mcp-config.json` antes da primeira
    escrita; merge aditivo (nunca remove nem altera servers do usuário);
    fixture de config ocupada (já nos riscos de engenharia).
  - SEC-11: bloco `mcp.ai-memory` do `harness-conf/opencode.json` sem
    credenciais (zero-LLM); se futuramente exigir token, segredo fica em
    env/cofre, nunca no json versionado (regra inviolável 1). gitleaks
    da suíte `testes-produto/seguranca` varre no gate do ciclo.
- **Docker ausente (BAIXA).**
  - SEC-09: princípio TUDO-OU-NADA (decisão humana 2026-09-24, na
    revisão do plano): Docker ausente interrompe o provisionamento,
    avisa com instrução user-space e o bloco `mcp.ai-memory` NÃO é
    injetado em NENHUM harness (nem OpenCode, nem Copilot); resolvido o
    pré-requisito, a reexecução do bootstrap completa o provisionamento
    e só então injeta o bloco; rollback remove o bloco junto com o
    resto. Nenhuma instalação com elevação (ver SEC-18). Sem "erro
    esperado de conexão": máquina sem Docker não carrega declaração MCP
    (achado 4 da revisão resolvido POR DESENHO).

O que vira código do repo NÃO introduz risco de desenho novo em relação
ao piloto aprovado: as exigências acima convertem a instalação manual
auditada em provisionamento repetível com rastro (hashes, avisos de
drift, abort em porta ocupada) e com rede sem saída por padrão (SEC-21).

#### E2/E3 — detecção de upstream e registro da writing-for-agents

Conteúdo upstream é NÃO confiável por definição. O fluxo P3 (detecção
read-only, avaliação, decisão humana, aplicação assistida e nunca
automática) é o controle central; complementos obrigatórios:

- SEC-12 (MÉDIA): detecção somente leitura; clone upstream em tempdir
  FORA do repo (conteúdo upstream fora do alcance de glob/grep de
  sessões) e removido ao final; sem `--recurse-submodules`. Teste:
  estado do repo inalterado após a detecção (critério E2) mais
  verificação do local do clone e do cleanup.
- SEC-13 (ALTA): nada do upstream executa em nenhum passo do fluxo;
  detecção é leitura (diff/ls/cat) e aplicação é edição assistida de
  texto; trecho de upstream jamais vira comando executado. Guardado por
  desenho (read-only) e revisão; não automatizável diretamente.
- SEC-14 (MÉDIA): prompt injection via diff exibido (o passo 3 mostra
  trechos de conteúdo hostil por definição): a saída da detecção marca o
  conteúdo upstream como NÃO confiável (aviso fixo no cabeçalho por
  skill); teste confere o aviso; o checklist pós-sync mantém a revisão
  de segurança do conteúdo novo como item MANUAL explícito (E4).
- SEC-15 (MÉDIA): E3 versiona SKILL-MECHANICS.md do upstream no repo
  (skill carregada por agentes): primeira cópia e cada atualização do
  sync passam pela revisão de segurança obrigatória (prompt injection,
  comandos, URLs, exfiltração; regra do repo), com registro nas notas
  locais do UPSTREAM.md; a revisão de 2026-09-22 permanece preservada.

#### E14/E6 — bloco no corpo dos agentes do Copilot e cópia seletiva

- SEC-16 (MÉDIA): o bloco gerado deriva EXCLUSIVAMENTE de fontes do
  repo: descriptions de `harness-conf/skills/*/SKILL.md` e mapa de
  permissions do `harness-conf/opencode.json`; nenhum conteúdo de pasta
  auxiliar ou upstream entra no bloco. Teste: marcador plantado em
  conteúdo externo jamais aparece no bloco gerado.
- SEC-17 (BAIXA): caminho absoluto resolvido com home real da máquina
  (nunca literal `~`); template sobrevive a caminho com espaço/unicode
  (teste com tmp_path contendo espaço); sem interpolação via shell.
- A cópia seletiva (10 globais na descoberta, 23 em pasta auxiliar fora
  dela) REDUZ exposição: menos conteúdo auto-carregado. Sem ressalva.

#### E13 — seções novas no AGENTS.base.md

Textos aprovados na P5 são regra de comportamento, sem comandos, URLs ou
segredos. CONFIRMADO: sem impacto de segurança. Mantidos verbatim com
largura ≤120 e diff humano no commit (já critérios de E13). Nenhuma
exigência nova.

#### Transversal

- SEC-18 (ALTA, bloqueante): zero sudo/administrador em todas as tasks;
  Docker é pré-requisito instruído, nunca instalado com elevação.
- SEC-19 (ALTA se violada): TLS com validação íntegra em todo download
  novo do ciclo (consolida SEC-01); ambiente corporativo usa o fluxo de
  CA PEM existente, nunca desativa validação.
- SEC-20 (BAIXA): nenhum segredo novo no repo; o gate final (E12) roda a
  suíte agregada com gitleaks, pip-audit e bandit.
- Logs do bootstrap: só status, hashes e caminhos; sem despejo de
  conteúdo de prompt ou sessão.

#### Mapa de exigências e testes

| Id | Task | Severidade | Teste automatizado |
|---|---|---|---|
| SEC-01 | E10 | Alta | Sim: comando de download sem flags insecure |
| SEC-02 | E10 | Alta | Sim: download sem hash verificado falha |
| SEC-03 | E10 | Alta | Sim: docker run sempre `127.0.0.1:PORTA:PORTA` |
| SEC-04 | E10 | Média | Sim: porta ocupada aborta com instrução |
| SEC-05 | E10 | Média | Sim: mudança de hash do plugin gera aviso |
| SEC-06 | E10 | Média | Sim: idempotência sem re-download |
| SEC-07 | E10 | Média | Não (doc/README + roteiro) |
| SEC-08 | E10 | Baixa | Não (roteiro manual) |
| SEC-09 | E10 | Baixa | Sim: docker ausente avisa, instrui e não injeta bloco MCP em nenhum harness |
| SEC-10 | E10 | Média | Sim: fixture de config ocupada preserva servers |
| SEC-11 | E10 | Baixa | Sim (suíte): gitleaks no gate |
| SEC-12 | E2 | Média | Sim: repo inalterado + clone em tempdir com cleanup |
| SEC-13 | E2/E3 | Alta | Não (desenho read-only + revisão) |
| SEC-14 | E2 | Média | Sim: aviso fixo na saída da detecção |
| SEC-15 | E3 | Média | Não (revisão manual obrigatória; checklist E4) |
| SEC-16 | E14 | Média | Sim: marcador externo ausente no bloco |
| SEC-17 | E14 | Baixa | Sim: home com espaço no template |
| SEC-18 | todas | Alta | Não (revisão de código + roteiro) |
| SEC-19 | E10 | Alta | Sim: coberto por SEC-01 |
| SEC-20 | todas | Baixa | Sim (suíte): gitleaks no gate |
| SEC-21 | E10 | Média | Sim: docker run com rede sem rota de saída; operação no roteiro |

#### Roteiro manual de segurança (fase Testes)

1. Pós-bootstrap (E10): `docker port ai-memory` lista só
   127.0.0.1:49374.
2. sha256 do wrapper instalado confere com a constante do repo; imagem
   roda `:latest` sem pin (decisão S1): anotar o digest corrente
   (`docker inspect --format '{{.Image}}' ai-memory`) como rastro para
   diagnosticar divergência de comportamento entre máquinas.
3. Segunda execução do bootstrap: sem re-download/re-pull; hashes do
   wrapper e do plugin estáveis (ou aviso explícito de drift).
4. Cenário de porta ocupada: servidor fake em 127.0.0.1:49374; o
   bootstrap aborta com instrução acionável (não segue em silêncio).
5. Rollback completo do ai-memory: container parado/removido, plugin
   removido, jsonc restaurado do backup, volume preservado; OpenCode
   sobe sem hooks ativos.
6. Copilot: mcp-config.json pré-populado sobrevive ao merge; backup
   criado antes da primeira escrita.
7. Detecção (E2) contra upstream real: `git status` limpo no repo após a
   execução; clone temporário removido; saída traz o aviso de conteúdo
   não confiável por skill.
8. Cópia Copilot (E14): inspeção de um agente com allow (ex.: sec)
   mostra bloco só com descriptions do repo e caminho absoluto válido.
9. Rede restrita (SEC-21, decisão S2): `docker inspect ai-memory`
   confirma rede sem rota de saída (internal); o serviço sobe e opera
   localmente com a rede restrita (consulta de status/MCP responde).

Achados high/critical deste roteiro são bloqueantes, sem exceção.

#### Spec permanente

O docs/README.md não define destino próprio para requisito de segurança;
specs executáveis da especialidade vivem em `docs/specs/` (rodam na
suíte `testes-produto/seguranca`) e decisões de arquitetura em
`docs/adr/`. O plano já prevê o ADR-0008 em E10. DECIDIDO (2026-09-24,
revisão do plano, achado 7): a conversão de SEC-01..SEC-11 e SEC-21 em
asserções da spec executável de segurança `docs/specs/Seguranca.md` é
CRITÉRIO DE ACEITE de E10, não mais recomendação; E10 NÃO edita o
docs/README.md (arquivo do curador-produto); T13 segue guardando os
comportamentos em testes automatizados do repo.

#### Evidências (sec) — Planejamento

- [x] Requisitos analisados: 21 exigências SEC (6 alta, 10 média,
      5 baixa) mapeadas nas tasks E1-E14
- [x] Roteiro manual gravado: 9 itens para a fase Testes
- [x] Perguntas ao humano: S1 e S2 respondidas (2026-09-24)

**Perguntas do sec (S1/S2 RESPONDIDAS em 2026-09-24; corpos originais,
com opções e recomendação, substituídos por estes resumos):**

- **S1 (pin de versão dos artefatos do ai-memory, E10) — RESPONDIDA:**
  manter `akitaonrails/ai-memory:latest`, SEM pin de digest ou tag fixa;
  risco de drift entre máquinas aceito pelo humano. SEC-02 ajustada e
  item 2 do roteiro atualizado (ver SEC-02).
- **S2 (saída de rede do container, E10) — RESPONDIDA:** RESTRINGIR o
  egress neste ciclo (não postergar); virou exigência efetiva SEC-21
  (rede sem rota de saída padrão, com critério de verificação e nota de
  diagnóstico) e item 9 do roteiro.

### Testes (qa)

Plano de testes do ciclo 2 (2026-09-24). Insumos: tasks E1-E14 + E-fix,
decisões P1-P5, 21 exigências SEC do `sec` e seu roteiro manual de 9 itens.
Registros base: 832 testes em `-m all`; `agent_eval` fora do ciclo (31
deselected, decisão humana). Testes aprovados aqui são spec executável do
ciclo (skill tests-as-spec): na construção, teste falho corrige código,
nunca o inverso; mudança de teste só volta ao planejamento. O docs/README.md
não define destino permanente para plano de testes (Elementos de
Especificação): este plano vive só neste arquivo e é descartado com ele.

#### Mapa de testes por task (E1-E14 + E-fix)

| Task | Já previsto (campo Verificação) | Plano de testes acrescenta/exige |
|---|---|---|
| E1 | pytest `tests/skills_mgmt/` com fixtures de UPSTREAM congelado | Teste negativo por subcomando (sync, update, list e, após E2, detecção): nenhum cria/remove `sincronizacao` sozinho; caso skill não-congelada continua sem o campo após cada comando |
| E2 | pytest com fixtures git de 2 commits; manual contra upstream real | **Lacuna L1:** fallback clone completo (prometido na tabela de riscos) sem critério de aceite: fixture shallow sem SHA base → detecção recorre ao clone completo. Exigir também: duas execuções seguidas provam reaparição da pendência pós-recusa; guarda SEC-12 (clone em tempdir fora do repo + cleanup) e SEC-14 (aviso de conteúdo não confiável por skill) |
| E3 | pytest + `opencode-skills list` | **Lacuna L2:** guarda nova de consistência: cada família do CLI tem linha na tabela de sync do AGENTS.md (evita drift silencioso do doc) |
| E4 | pytest (guardas de SHA e arquivos) | Guarda de string: checklist do AGENTS.md mantém a revisão de segurança do conteúdo novo como item MANUAL explícito (SEC-14/SEC-15) |
| E5 | pytest `tests/harnesses/` | Nada a acrescentar: teste trava a description específica e a ausência do fallback genérico |
| E6 | pytest `tests/harnesses/` + `tests/agents/` | Guarda de soma: globais + pasta auxiliar = total de skills do repo (nenhuma perdida na cópia); números 10/23 travados como estado corrente, derivação lê o mapa |
| E7 | revisão do relatório; `tests/agents/` verde | Sem teste automatizável (leitura auditorial). Exigência indireta: cada E-fix originado que mude comportamento nasce com teste próprio (TDD) |
| E8 | execução do arquivo de teste; confirmação no gate | Proibido relaxar o teste (regra do repo: `pytest.fail` correto); causa raiz registrada; re-executar o arquivo imediatamente após a resolução, sem esperar o gate |
| E9 | varredura de largura + pytest por arquivo | **Lacuna L3:** guarda permanente automatizada (T14; escopo fechado na Q1: só agents/*.md + AGENTS.base.md); até E9, rodadas parciais mostram as 31 linhas conhecidas |
| E10 | pytest `tests/bootstrap/` + `tests/harnesses/`; `--check-only`; execução real | Diretriz: testes automatizados NUNCA dependem de Docker (fakes/stubs; assert sobre comandos gerados, determinísticos). Detalhamento SEC-01..SEC-11/SEC-21 na estratégia (T10-T13). "OpenCode reiniciado enxerga o MCP" é manual (RM-10) |
| E11 | leitura cruzada + pytest `tests/agents/` | Nenhum teste novo; consistência workflow↔agentes já guardada por `test_workflow_consistency.py` |
| E12 | `-m all` 100% verde com contagens no plano | Integridade com a fase Testes: o agregador `testes-produto` embute `-m all` na suíte backend; evidência do agregador é validada pelo curador-produto (CA-T1) |
| E13 | diff humano + pytest `tests/agents/` + varredura | **Lacuna L4:** guarda de âncoras: frases-chave das duas seções aprovadas presentes no AGENTS.base.md e regra de precedência da premissa 7 ausente; regeneração do AGENTS.md global contém as seções novas (teste do adapter/bootstrap) |
| E14 | pytest `tests/harnesses/`; inspeção da cópia | **Lacuna L5:** "agente SEM allow não recebe bloco" está na descrição mas não nos critérios de aceite: exigir o caso de teste. SEC-16 (marcador externo jamais no bloco) e SEC-17 (tmp_path com espaço, home real) viram casos explícitos |
| E-fix | variável (definida por E7) | Cada E-fix: mudança de comportamento → teste próprio no ciclo red-green; só conteúdo de skill → revisão manual obrigatória (SEC-15), sem automação |

Lacunas L1-L5 não bloqueiam o planejamento: viram requisitos de teste que o
executor cumpre na construção das tasks indicadas (L1 e L5 completam critérios
de aceite existentes; L2-L4 são guardas novas propostas por este plano).

#### Estratégia de integração (testes novos)

Diretrizes: sem `skip` (pré-requisito ausente = `pytest.fail` acionável);
nomes descritivos por comportamento; fixtures git locais em tmpdir (nunca
rede; upstream real só no roteiro manual); porta como parâmetro injetável
nos testes de porta ocupada (evita conflito com serviço real em 49374).
Marker segue a convenção do repo: lógica pura = `unit`; subprocess git real
ou socket loopback = `integration` com premissa declarada.

| # | Teste novo | Task | Arquivo provável | Marker | Premissas |
|---|---|---|---|---|---|
| T1 | Freeze: sync/update/list pulam congelada; campo preservado na regeneração; negativo por subcomando | E1 | `tests/skills_mgmt/test_sync.py` | unit | nenhuma |
| T2 | Diff base→novo, freeze, SHA inválido e saída por skill | E2 | `test_upstream_detect.py` | integration | git |
| T3 | Clone externo, cleanup, aviso e repetição pós-recusa | E2 | `test_upstream_detect.py` | integration | git local |
| T4 | Fallback se clone shallow não contém SHA base | E2 | `test_upstream_detect.py` | integration | git local |
| T5 | writing-for-agents: fixture MIT + SKILL-MECHANICS.md; SKILL.md intocado; `## Notas locais` e revisão de 2026-09-22 preservadas; extra_fields | E3 | `tests/skills_mgmt/test_sync.py` | unit | nenhuma |
| T6 | Consistência tabela de sync do AGENTS.md ↔ famílias do CLI (L2) | E3 | `tests/skills_mgmt/test_sync.py` | unit | nenhuma |
| T7 | Checklist pós-sync: SHA novo refletido; arquivos declarados existem e batem; item manual de revisão explícito | E4 | `tests/skills_mgmt/test_sync.py` | integration | git local |
| T8 | Description de `otimizar-agents-md` específica; fallback genérico ausente | E5 | `tests/harnesses/test_copilot.py` | unit | nenhuma |
| T9 | Poda Copilot: só skills sem deny global na descoberta; domínio na pasta auxiliar; fixture trocando deny muda a cópia; guarda de soma | E6 | `tests/harnesses/test_copilot.py` | unit | nenhuma |
| T10 | Bloco de referência: presente só com allow (com e sem allow, L5); description completa + caminho absoluto (home real); fonte do repo limpa; marcador externo ausente (SEC-16); tmp_path com espaço (SEC-17) | E14 | `tests/harnesses/test_copilot.py` | unit | nenhuma |
| T11 | Merge MCP Copilot: config ocupada preservada (aditivo); backup antes da 1ª escrita (SEC-10) | E10 | `tests/harnesses/test_copilot.py` | unit | nenhuma |
| T12 | `harness-conf/opencode.json`: parse válido; bloco `mcp.ai-memory` presente; sem campos de credencial (SEC-11) | E10 | `tests/harnesses/test_opencode.py` | unit | nenhuma |
| T13 | Provisionamento com fakes (downloader/docker stub): download íntegro sem flags insecure (SEC-01/19); hash não verificado falha (SEC-02); `docker run` gerado com bind `127.0.0.1:PORTA:PORTA` (SEC-03) e rede sem rota de saída (SEC-21); idempotência sem re-download, hash divergente bloqueia (SEC-06); docker ausente avisa e não injeta bloco MCP (SEC-09); drift do plugin avisa (SEC-05); jsonc removido com backup | E10 | `tests/bootstrap/test_ai_memory_provision.py` (novo) | unit | nenhuma (fakes) |
| T14 | Guarda de largura: nenhuma linha >120 col em `harness-conf/agents/*.md` e `harness-conf/AGENTS.base.md` (L3; escopo fechado na Q1: SKILL.md/references fora, ampliação é backlog consciente; falha lista arquivo:linha) | E9, E13 | `tests/agents/test_line_width.py` (novo) | unit | nenhuma |
| T15 | Âncoras das seções aprovadas no base + ausência da regra de premissa 7; AGENTS.md global regenerado contém as seções (L4) | E13 | `tests/agents/test_workflow_consistency.py` (âncoras) + `tests/harnesses/test_opencode.py` (regeneração) | unit | nenhuma |

Suíte meta `testes-produto/tests/`: nenhuma task do ciclo altera os scripts
de suíte/agregador; ela NÃO roda neste ciclo. Se a curadoria mudar critérios
durante o ciclo, roda naquele momento (regra do docs/README.md).

#### Roteiro manual consolidado (fase Testes)

Consolida os 9 itens do `sec` (fase 6 executa só o roteiro dele; o resto é
da fase Testes/agregador) + acréscimos deste plano. Decisão Q2 (2026-09-24):
sem ambiente separado; a desinstalação controlada na própria máquina cobre
os dois cenários em quatro fases sequenciais:

- **Fase A (RM-1..RM-10), estado ATUAL:** roteiro sobre a máquina com o
  ai-memory do piloto instalado manualmente, validando upgrade e
  idempotência sobre estado real.
- **Fase B (RM-11), rollback controlado:** desinstalação completa
  preservando o volume de dados.
- **Fase C (RM-12), re-provisionamento do zero:** valida o caso "máquina
  nova" pelo bootstrap.
- **Fase D (RM-13), verificação da memória:** wiki anterior sobreviveu com
  o volume reanexado.

Ordem interna importa: RM-5 sobrepõe servidor fake na porta fixa, então
exige o serviço parado. O roteiro roda na fase Testes, na máquina do humano
e com ele ciente (mexe no ambiente dele); o momento das fases B-D é acordado
com o humano no início da sessão de testes.

| # | Passo | Origem | Executor |
|---|---|---|---|
| RM-1 | Fase A: bootstrap real sobre o estado ATUAL do piloto (ai-memory manual): valida upgrade (caminho de upgrade: SEC-06); provisiona wrapper, container, volume e hooks | E10 + Q2 | qa |
| RM-2 | `docker port ai-memory` lista só 127.0.0.1:49374 | sec 1 | qa |
| RM-3 | sha256 do wrapper instalado = constante do repo; anotar digest corrente da imagem | sec 2 | qa |
| RM-4 | Segunda execução do bootstrap: sem re-download/re-pull; hashes estáveis ou aviso de drift | sec 3 | qa |
| RM-5 | Porta ocupada: servidor fake em 127.0.0.1:49374 (serviço real parado); bootstrap aborta com instrução | sec 4 | qa |
| RM-6 | Rede restrita: `docker inspect` confirma rede internal; serviço sobe e opera localmente | sec 9 | qa |
| RM-7 | Copilot: `mcp-config.json` pré-populado sobrevive ao merge; backup criado antes da 1ª escrita | sec 6 | qa |
| RM-8 | Detecção (E2) contra upstream real: `git status` limpo; clone temporário removido; aviso por skill presente | sec 7 | qa |
| RM-9 | Cópia Copilot (E14): agente com allow (ex.: sec) com bloco só de descriptions do repo e caminho absoluto válido | sec 8 | qa |
| RM-10 | Reiniciar o OpenCode e conferir o MCP ai-memory visível/operante | E10 (critério) | **humano** |
| RM-11 | Fase B: rollback completo na própria máquina, preservando o volume (detalhe na nota abaixo) | sec 5 + Q2 | **humano** (momento acordado no início da sessão) |
| RM-12 | Fase C: re-provisionamento do zero pelo bootstrap ("máquina nova"); reexecuta RM-2/RM-3/RM-4; Docker ausente: ver nota (SEC-09) | Q2 + SEC-09 | qa |
| RM-13 | Fase D: wiki anterior sobreviveu: volume reanexado e dados legíveis no serviço novo | Q2 | qa |

Nota das fases B-D (Q2), detalhe que não cabe na tabela:

- RM-11 (fase B): parar/remover o container, remover o wrapper, os
  plugins/hooks e o bloco MCP (hoje: no `~/.config/opencode/opencode.jsonc`
  manual do usuário; após a fase A: o injetado pelo provisionamento); o
  OpenCode sobe sem hooks. PRESERVAR o volume
  `~/.local/share/ai-memory/`: o volume é a memória acumulada; sem
  preservação, perda de dados. O rollback deixou de ser o último passo
  solto: fica entre as fases do roteiro, com re-provisionamento em seguida.
- RM-12 (fase C): sobre o estado novo (sem container/wrapper/hooks
  prévios), reexecutar as checagens-chave RM-2 (bind 127.0.0.1), RM-3
  (sha256 do wrapper) e RM-4 (idempotência).
- RM-12 (fase C), cenário Docker ausente (SEC-09, tudo-ou-nada,
  decisão 2026-09-24): simular Docker indisponível (ex.: PATH sem o
  binário); o bootstrap interrompe o provisionamento com aviso e
  instrução user-space e o bloco `mcp.ai-memory` NÃO é injetado em
  nenhum harness (nem OpenCode, nem Copilot); restaurado o pré-requisito,
  a reexecução completa o provisionamento e só então injeta o bloco.
- RM-13 (fase D): wiki do piloto legível pelo serviço re-provisionado,
  provando que o volume foi reanexado ao container novo.

Registro por passo (resultado + evidência) na seção de evidências; achados
high/critical são bloqueantes, sem exceção (regra do sec).

#### Critérios de aceite da fase Testes (gate do ciclo)

- [ ] CA-T1: agregador `testes-produto` executado na íntegra, status `pass`,
      zero findings bloqueantes; saída JSON registrada e validada pelo
      curador-produto.
- [ ] CA-T2: `-m all` 100% verde (E12): base 832 + testes novos; 0 failed;
      skips apenas skipif de plataforma declarados pela própria suíte;
      contagens registradas no plano.
- [ ] CA-T3: `tests/product_tests/test_concordion_spec_infra.py` verde
      (E8 resolvido; sem relaxamento do teste).
- [ ] CA-T4: cobertura total ≥70% e sem queda vs. baseline (gate da suíte
      backend; ferramenta pytest-cov).
- [ ] CA-T5: roteiro RM-1..RM-13 executado com registro por passo (fases
      A-D da Q2, na máquina do humano, com ele ciente); zero
      achado high/critical aberto.
- [ ] CA-T6: testes novos T1-T15 presentes e verdes; lacunas L1-L5
      endereçadas nas tasks correspondentes.
- [ ] CA-T7: suíte meta `testes-produto/tests/` não roda (sem mudança em
      scripts de suíte); se houver mudança, roda e passa.
- [ ] CA-T8: evidências persistidas em `## Evidências de Testes — Testes`
      deste plano.

#### Riscos de teste

| Risco | Impacto | Mitigação |
|---|---|---|
| WSL vs. Windows: PSScriptAnalyzer/shellcheck existem por SO; caminhos com espaço | Médio | testes novos portáveis (sem dependência de symlink); T10 usa tmp_path com espaço; suíte roda completa no ambiente corrente |
| Docker indisponível no roteiro manual (Q2: máquina local, onde o piloto já roda) | Médio | automatizados sem Docker (T13 fakes); no manual, impedimento registrado, nunca gate afrouxado |
| Ordem das tasks: sem E8, toda rodada parcial carrega 1 failed conhecido | Médio | E8 primeiro (Wave 1); até lá, failed do JAVA_HOME não é atribuído a regressão nova |
| E9 (reflow) quebrar pinos de teste | Médio | suíte `tests/agents/` após cada arquivo; pino mantido em uma linha (já na task) |
| RM-5 conflitar com ai-memory real na 49374 | Baixo | ordem do roteiro: parar o serviço antes do servidor fake |
| gitleaks/pip-audit dependem de rede | Baixo | retry 3x interno; esgotado = finding bloqueante com instrução (spec da suíte) |
| Suíte cresce (~832 + ~30 novos) | Baixo | sem ação; contagens novas registradas no gate |

#### Evidências (qa) — Planejamento

- [x] Mapa por task revisado: E1-E14 + E-fix; 5 lacunas (L1-L5)
- [x] Estratégia de integração: 15 testes novos (T1-T15) com arquivo,
      marker e premissas
- [x] Roteiro manual consolidado: 13 passos em 4 fases (9 do sec + RM-1,
      RM-10 e RM-12/RM-13 da decisão Q2)
- [x] Critérios de aceite da fase: CA-T1..CA-T8
- [ ] Execução: acontece na fase Testes (por definição deste ciclo)
- [x] Perguntas ao humano: Q1 e Q2 respondidas (2026-09-24)

**Perguntas do qa (Q1/Q2 RESPONDIDAS em 2026-09-24; corpos originais,
com opções e recomendação, substituídos por estes resumos):**

- **Q1 (escopo da guarda de largura T14) — RESPONDIDA:** seguir a
  recomendação (escopo menor). A guarda permanente de largura (T14) cobre
  apenas `harness-conf/agents/*.md` + `AGENTS.base.md` neste ciclo;
  SKILL.md/references ficam FORA (conteúdo upstream tem linhas longas
  esperadas e a guarda quebraria o sync); ampliação é backlog consciente.
  T14 e a citação de L3 no mapa de tasks já refletem o escopo.
- **Q2 (ambiente do roteiro manual de E10) — RESPONDIDA:** sem ambiente
  separado; a desinstalação controlada na própria máquina cobre os dois
  cenários. Roteiro reordenado em quatro fases sequenciais: (A) RM-1..RM-10
  sobre o estado ATUAL do piloto (upgrade + idempotência sobre estado
  real); (B) RM-11 rollback completo preservando o volume
  `~/.local/share/ai-memory/` (o volume é a memória acumulada; sem
  preservação, perda de dados); (C) RM-12 re-provisionamento do zero pelo
  bootstrap (caso "máquina nova"); (D) RM-13 verificação de que a wiki
  anterior sobreviveu (volume reanexado). Mantida a exigência de registro
  por passo e a nota de que o roteiro roda na fase Testes, na máquina do
  humano e com ele ciente (mexe no ambiente dele). Risco de Docker ausente
  ajustado à premissa da máquina local.

### Perguntas

Perguntas do eng-software ao humano. P1-P5 RESPONDIDAS em 2026-09-23/24
(os corpos originais, com opções e recomendação, foram substituídos por
estes resumos); as decisões completas e fiéis vivem em `### Decisões do
humano (2026-09-23/24)`.

- **P1 (config do ai-memory) — RESPONDIDA:** opção A com acréscimos:
  bloco MCP no `harness-conf/opencode.json` + provisionamento completo
  user-space pelo bootstrap + sondagem/declaração no Copilot (ver
  Decisões).
- **P2 (amostra da auditoria) — RESPONDIDA:** amostra MÉDIA de 16
  (7 core + 4 com upstream + 4 locais + writing-for-agents); expansão
  para as 33 se muitos problemas.
- **P3 (diff/sync de upstream) — RESPONDIDA:** fluxo de 4 passos
  (detecção read-only → avaliação do agente → resumo + recomendação +
  pergunta de congelar → UPSTREAM conforme a decisão); internals livres,
  critério eficiência.
- **P4 (skills no Copilot) — RESPONDIDA:** paridade de resultado com o
  filtro do OpenCode: 10 globais na descoberta, 23 de domínio em pasta
  auxiliar, bloco de referência por agente somente na cópia materializada.
- **P5 (AGENTS.base.md) — RESPONDIDA:** textos aprovados substituem a
  seção de compactação e acrescentam "Chamadas de ferramentas"; regra de
  precedência sobre a premissa 7 removida do base.

Perguntas novas: nenhuma. Nenhuma contradição técnica entre as decisões
fechadas e o estado do repo foi identificada no replanejamento
(2026-09-24); a sondagem de MCP do Copilot confirmou a viabilidade do
caminho previsto na P1.

### Backlog futuro (incremento pelo humano)

Registrado por decisão do humano em 2026-09-24: FORA do escopo deste
ciclo; não gera task aqui. Demais recomendações do relatório de custos
(`/mnt/c/Users/Vitor/Downloads/relatorio-custos-contexto-cache.md`,
seções 5 e 6) ainda não implementadas, para incremento futuro:

- contrato congelado antes da implementação;
- preflight determinístico;
- validação em camadas;
- correções consolidadas;
- detector de loop;
- orçamento de requests;
- separação da finalização administrativa;
- controle de outputs de ferramentas além do já aprovado;
- preservação de prefixo estável;
- retornos condensados de subagentes como regra geral.

## Ciclo 2 — REVISÃO DO PLANO

Revisão integrativa do planejamento (rev, 2026-09-24, fase REVISÃO DO
PLANO). Objeto: `## Ciclo 2 — VALIDAÇÃO` e `## Ciclo 2 — PLANEJAMENTO`
completos (decisões P1-P5, S1/S2, Q1/Q2; tasks E1-E14 + E-fix; 21
exigências SEC-01..SEC-21; plano qa T1-T15, RM-1..RM-13, CA-T1..CA-T8,
lacunas L1-L5), contra os insumos do ciclo 1 (D1-D13, roteiro "Fase
DEVFLOW") e o estado real do repo. Skills de domínio aplicadas:
security-and-hardening, tests-as-spec, api-and-interface-design,
documentation-and-adrs (após a obrigatória code-review-and-quality).
NÃO se aplicam a este ciclo: data-modeling (sem BD) e
frontend-ui-engineering (sem UI), conforme declarado no Status.

### Achados

1. Contradição P5/E13 com o estado real da premissa 7
   (`docs/workflow-agentes-dev.md`, item 7: o texto vigente cita os
   critérios da política D11 e a cláusula "a política de compactação
   prevalece, mesmo dentro da mesma fase", que referenciam a regra de
   precedência que E13 REMOVE do AGENTS.base.md; P5 decide "a premissa 7
   segue válida como está", o que já nasce dessincronizado) ·
   E13 deve tratar o realinhamento da redação da premissa 7 como
   resultado ESPERADO (proposta de redação ao humano na execução), não
   como "verificar se precisa"; sem reabrir P5 (a válvula já existe na
   decisão; o ajuste é de ênfase da task, para o executor não pular o
   passo) · média

2. Desvio de papel em E11(b): docs/README.md é mantido pelo
   curador-produto (tabela de roteamento do AGENTS.base.md e regra do
   repo); a VALIDAÇÃO deste ciclo remeteu o Achado A para "trabalho de
   curadoria futuro", mas E11 atribui a edição da subseção ADR ao
   eng-software · delegar E11(b) ao curador-produto (via devflow) ou
   registrar no plano delegação explícita aprovada pelo humano · média

3. Lacuna operacional no fluxo de upgrade (RM-1/SEC-06): a fase A roda o
   bootstrap sobre a instalação manual do piloto; hash divergente em item
   já instalado é bloqueante e o roteiro não define o procedimento de
   upgrade (ex.: remover wrapper antigo e reexecutar) · especificar na
   instrução de bloqueio de SEC-06 o caminho de upgrade, para RM-1 não
   travar sem saída · baixa

4. Risco não mapeado em E10: com o bloco `mcp.ai-memory` na config
   canônica, máquina com Docker ausente fica com MCP declarado e
   inacessível (erro de conexão MCP por sessão até provisionar);
   comportamento esperado não registrado · acrescentar à instrução de
   Docker ausente (SEC-09/README) o efeito esperado e o caminho para
   remover/silenciar o bloco se desejado · baixa

5. Inconsistência documental de contagem: "Escopo fechado pelo humano em
   2026-09-23 (itens 1-8)" vs roteiro "Fase DEVFLOW" com 7 itens
   numerados · corrigir a referência (provável 8º item = frente
   "comportamento de custo"/correção ADR docs do replanejamento) · baixa

6. Pendência formal aberta: Pergunta 1 da VALIDAÇÃO (regras-negocio.md
   intencional?) segue sem resposta na própria seção, embora
   "Dependências externas registradas" já registre "lacuna confirmada
   pelo humano" · atualizar a seção Perguntas da VALIDAÇÃO com a resposta
   e referência cruzada · baixa

7. Recomendação sem força de critério: o sec recomenda converter
   SEC-01..SEC-11/SEC-21 em asserções da spec de segurança ao construir
   E10, mas a recomendação não virou critério de aceite (fica a critério
   do executor) · decidir: virar critério de aceite de E10 ou registrar
   decisão explícita de adiar (T13 já guarda os comportamentos em testes
   automatizados do repo) · baixa

8. Formato de ADR novo não especificado: ADRs legados (0001-0006) seguem
   a convenção do repo com "Asserções executáveis" (retrofit concluído,
   ver VALIDAÇÃO); E2/E10/E14 não declaram se ADR-0007/0008/0009 seguem
   o formato · confirmar com a curadoria/humano o formato exigido para
   ADRs novos e registrar nas tasks · baixa

### Veredicto

**Ajusta antes da construção (leve): nenhum achado bloqueante.** Resolver
achados 1 e 2 antes de iniciar as waves (são ajustes de texto/delegação no
plano; baratos agora, retrabalho ou sobreposição de papel se deixados para
a execução). Achados 3-8 são melhorias opcionais executáveis durante o
ciclo. A estrutura de fundo está íntegra: escopo, waves, dependências e a
cadeia decisão → task → exigência SEC → verificação estão completos e
coerentes.

### Checklist negativo (o que NÃO foi encontrado)

- Nenhuma decisão P1-P5/S1/S2/Q1/Q2 sem task correspondente; nenhuma task
  órfã (E1-E14 todas rastreiam a decisão/roteiro que a originou).
- Nenhuma exigência SEC-01..SEC-21 sem dono (task) e sem verificação
  (teste automatizado, suíte ou roteiro manual declarado no mapa do sec).
- Nenhuma lacuna L1-L5 sem endereçamento (L1→T4, L2→T6, L3→T14, L4→T15,
  L5→T10).
- Nenhuma contradição de dependências/waves (E8 cedo destravando a suíte;
  E1→E2→E3→E4; E6→E14→E10 uma passada no adapter; E7 após E9/E13/E1-E3;
  E11/E12 no fechamento).
- Nenhuma violação das regras de teste do repo: sem `skip`
  (`pytest.fail` acionável), `-m all` completo, markers unit/integration
  com premissas declaradas, proibição de relaxar teste em E8 explícita.
- Nenhuma divergência factual nas alegações checadas contra o repo:
  33 skills/16 UPSTREAMs; 31 linhas >120 em 8 arquivos de agents;
  deny global com 22 chaves cobrindo 23 skills (10 globais, bate com
  P4/E6); `_COMMAND_DESCRIPTIONS` cobre 3/4 commands com fallback em
  `otimizar-agents-md` (E5 procede); base da suíte 832 coletados/31
  deselected (CA-T2 coerente); `docs/specs/regras-negocio.md` ausente
  conforme registrado; seção "Compactação de contexto" presente e
  "Chamadas de ferramentas" ausente no AGENTS.base.md (E13 procede).
- Nenhum critério de aceite com "etc." ou formulação subjetiva.
- Nenhum segredo/credencial previsto em artefato versionado (SEC-11/T12
  guardam); checkpoints de commit seguem Conventional Commits PT-BR.
- Nenhuma task do ciclo fora do escopo aprovado; backlog futuro
  registrado não gera task (correto).

### Evidências (rev)

- [x] Artefato lido: `plan/otimizacao-custo-contexto.md` na íntegra
      (1913 linhas: Status, Overview, D1-D13, Tasks 1-13, VALIDAÇÃO,
      PLANEJAMENTO completo, roteiro Fase DEVFLOW)
- [x] Plano aprovado consultado: sim (decisões D1-D13 e corte D9 do
      ciclo 1; roteiro Fase DEVFLOW; regras do AGENTS.md do repo)
- [x] Checklist integrativo: 8 dimensões (decisões↔tasks↔SEC↔testes;
      completude do escopo; riscos/waves; regras do repo; viabilidade
      técnica; qualidade dos critérios de aceite; docs↔docs/README.md;
      papéis do workflow)
- [x] Verificações de estado (somente leitura): contagens de
      skills/UPSTREAMs e linhas >120; `harness-conf/opencode.json`
      (deny/allows/ausência de mcp); premissa 7 do
      `docs/workflow-agentes-dev.md`; `_COMMAND_DESCRIPTIONS` em
      `src/opencode_config/harnesses/copilot.py`; `docs/specs/` e
      `docs/adr/` (frase retrofit em docs/README.md linha 108);
      `pytest --collect-only -q -m all` (832/863, 31 deselected);
      seções do AGENTS.base.md
- [x] Achados encontrados: 8 total (0 alta/bloqueante, 2 média, 6 baixa)

### Disposição dos achados (2026-09-24)

Ajustes aprovados pelo humano em 2026-09-24, aplicados ao plano pelo
eng-software na fase REVISÃO DO PLANO (sem execução de tasks).

1. Aplicado (E13/premissa 7): realinhamento da redação vira resultado
   ESPERADO da execução — proposta alinhada às seções aprovadas,
   submetida ao humano via devflow antes de aplicar; P5 não reaberta.
2. Realocado (E11(b)): correção da subseção ADR do docs/README.md passa
   ao `curador-produto` (delegação aprovada; devflow spawna o curador na
   execução; diff reportado ao committer único).
3. Aplicado (SEC-06/RM fase A): instrução de bloqueio de hash divergente
   ganha caminho de upgrade (notificar, remover artefato antigo ou
   confirmar com backup, reexecutar bootstrap); idempotência e nunca
   sobrescrever às cegas mantidas.
4. Redesenhado (E10/SEC-09/RM fases A-D, decisão humana 2026-09-24):
   princípio TUDO-OU-NADA — Docker ausente interrompe o provisionamento
   e o bloco `mcp.ai-memory` não é injetado em NENHUM harness;
   reexecução com pré-requisito resolvido completa e injeta; rollback
   remove o bloco junto; achado resolvido POR DESENHO, sem "erro
   esperado de conexão"; decisão registrada na subseção de Decisões.
5. Aplicado: contagem do escopo corrigida (7 itens do roteiro + frente
   "comportamento de custo" como 8º item do replanejamento).
6. Aplicado: Pergunta 1 da `## Ciclo 2 — VALIDAÇÃO` respondida
   formalmente (regras-negocio.md é lacuna; criar no ciclo; task do
   curador-produto) com referência cruzada.
7. Aplicado (E10): conversão de SEC-01..SEC-11/SEC-21 em asserções da
   spec de segurança vira CRITÉRIO DE ACEITE de E10; T13 segue guardando
   os comportamentos em testes do repo.
8. Aplicado (E2/E10/E14): ADRs 0007/0008/0009 seguem a convenção dos
   retrofitados 0001-0006, incluindo "Asserções executáveis"; registrado
   nas tasks e nas Sugestões de ADR.

### Revisão delta (2026-09-24)

Conferência da aplicação dos 8 ajustes aprovados (rev, rodada DELTA,
instância nova, mesma fase). Objeto: seção `## Ciclo 2 — REVISÃO DO
PLANO` + `### Disposição dos achados (2026-09-24)` contra o corpo do
plano (Decisões, tasks E1-E14, sec, qa) e o estado real do repo.

Conferidos: (1) E13/premissa 7 como resultado ESPERADO da execução,
com submissão da redação ao humano via devflow ANTES de aplicar e
critério de aceite verificável; o texto vigente da premissa 7 em
`docs/workflow-agentes-dev.md` confirma a dessincronização prevista
(cita critérios de compactação e cláusula de precedência que E13
remove). (2) E11(b) delegada ao curador-produto com registro triplo
(task, Dependências externas, checkpoint de commit). (3) SEC-06 com
caminho de upgrade (notificar, remover artefato antigo ou confirmar
com backup, reexecutar), referenciado por RM-1. (4) Redesenho E10
tudo-ou-nada íntegro e consistente em TODAS as ocorrências:
refinamento datado da P1, descrição e critérios de E10, SEC-09, mapa
de exigências (teste automatizado declarado), T13, RM fases A-D
(RM-12 cobre interrupção E reexecução com injeção), risco de
engenharia, regra de produto e ADR-0008; "rollback remove o bloco
junto" aparece em todos os pontos; nenhuma ocorrência residual do
comportamento antigo ("erro esperado de conexão") fora do corpo
histórico da revisão. (5) Contagem do escopo corrigida (7 itens do
roteiro + 8º do replanejamento). (6) Pergunta 1 da VALIDAÇÃO
respondida com referência cruzada bidirecional (Perguntas ↔ Achado B ↔
Dependências externas). (7) SEC→spec como CRITÉRIO DE ACEITE de E10
(descrição item 7, critério de aceite e Spec permanente do sec), com
T13 guardando os comportamentos. (8) ADRs 0007/0008/0009 com a
convenção dos retrofitados 0001-0006 e seção "Asserções executáveis"
em E2/E10/E14 e nas Sugestões de ADR (ADR-0008 reflete o
tudo-ou-nada).

**Veredito: APROVADO PARA EXECUÇÃO** — os 8 ajustes ficaram íntegros e
consistentes com o restante do plano; nenhum achado bloqueante. Pontas
soltas residuais (melhorias opcionais, executáveis durante o ciclo):

1. Risco não mapeado: no POSIX o `~/.config/opencode/opencode.json` é
   symlink do canônico (regra do repo) e E10(4) remove o jsonc manual
   do usuário; com o bloco MCP na fonte canônica, a injeção condicional
   do tudo-ou-nada exige mudança estrutural no strategy POSIX (cópia
   sincronizada ou filtro do adapter) — interação ausente na tabela de
   riscos de engenharia · eng-software registra o risco na tabela (o
   mecanismo segue internalidade da decisão; T13/RM-12 guardam o
   comportamento) · melhoria
2. Ambiguidade no critério SEC→spec de E10: o parêntese "(seção
   'Testes por Especialidade' do docs/README.md)" pode induzir o
   executor a editar o docs/README.md, arquivo do curador-produto
   (desvio de papel análogo ao corrigido no achado 2), quando o
   destino material é `docs/specs/Seguranca.md` (único spec nos
   Arquivos prováveis de E10) · ajustar a redação para nomear o
   arquivo destino (ou notar que E10 não toca o docs/README.md) ·
   melhoria
3. RM-11: "o bloco MCP manual" é resquício da era do piloto; após a
   fase A (upgrade pelo bootstrap), o bloco presente é o injetado pelo
   provisionamento · rewording para "o bloco MCP (injetado pelo
   bootstrap)" · melhoria

### Evidências (rev — delta)

- [x] Artefato lido: `plan/otimizacao-custo-contexto.md` na íntegra
      (2172 linhas), com foco na REVISÃO DO PLANO + Disposição
- [x] Plano aprovado consultado: sim (decisões P1-P5 + refinamento
      tudo-ou-nada de 2026-09-24; sec SEC-01..SEC-21; qa T1-T15,
      RM-1..RM-13; roteiro Fase DEVFLOW)
- [x] Estado do repo (somente leitura): premissa 7 vigente em
      `docs/workflow-agentes-dev.md`; varredura de resquícios
      textuais no plano ("itens 1-8", "erro esperado de conexão",
      "bloco MCP manual")
- [x] Checklist integrativo: 8/8 ajustes conferidos no corpo do plano
- [x] Achados encontrados: 3 total (0 bloqueantes, 3 melhoria)

### Disposição das melhorias do delta (2026-09-26)

Incorporação das 3 melhorias da `### Revisão delta (2026-09-24)` ao
plano, pelo eng-software na fase REVISÃO DO PLANO, a pedido do devflow:

1. Aplicada (E10, riscos de engenharia): risco de execução da injeção
   condicional do bloco MCP vs. symlink POSIX do `opencode.json` na
   tabela de riscos (linha "Symlink POSIX do opencode.json" + nota
   abaixo dela: adapter não edita symlink; mecanismo contorna com
   config local adicional ou filtro na sincronização).
2. Aplicada (E10, critério SEC→spec): destino nomeado como a spec
   executável de segurança `docs/specs/Seguranca.md` na descrição
   (item 7), no critério de aceite e na Spec permanente do sec; E10
   não toca o docs/README.md (arquivo do curador-produto).
3. Aplicada (RM-11): redação precisa do que existe hoje (bloco MCP no
   `~/.config/opencode/opencode.jsonc` manual do usuário; após a fase
   A, o injetado pelo provisionamento).

## Ciclo 2 — CONSTRUÇÃO

### E8 — 2026-09-27

**Resultado:** o teste falhava quando `JAVA_HOME` não estava definido. O
teste existente já emitia `pytest.fail` acionável. Mantive o teste e o
código do repositório sem alterações.

**Causa raiz:** JDK Temurin 21.0.6 e Gradle 8.10.2 estavam instalados e
disponíveis no `PATH`. O `~/.bashrc` não exportava `JAVA_HOME`.

**Correção:** acrescentei ao `~/.bashrc` o bloco gerenciado
`bootstrap-env`, com `JAVA_HOME="/home/vitor/.local/share/jdk"`.

**Arquivos tocados:**
- `~/.bashrc`, inclusão do bloco `bootstrap-env`.
- `plan/otimizacao-custo-contexto.md`, decisões do ciclo e evidências E8.

**Comandos e saída resumida:**
- `JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest tests/product_tests/test_concordion_spec_infra.py -v`:
  12 passed em 10,37 s.
- `env -u JAVA_HOME .venv/bin/pytest tests/product_tests/test_concordion_spec_infra.py -v`:
  reproduziu 1 failed e 11 passed, com a mensagem esperada do `pytest.fail`.
- `bash -n /home/vitor/.bashrc`: código de saída 0.
- Execução do arquivo em Bash interativo carregando `~/.bashrc`, com
  `JAVA_HOME` removido do ambiente inicial: 12 passed em 10,46 s.

**Pendências:** shells e processos já abertos mantêm o ambiente antigo.
Uma nova shell interativa carrega a variável persistida no `~/.bashrc`.

### E1 — 2026-09-27

**Executor:** `opencode/gpt-6-luna`.

**Resultado:** o CLI respeita `sincronizacao: congelada` por skill. O sync
ignora skills congeladas, informa cada skill ignorada e sincroniza as demais
da família. O update congelado retorna `status: frozen` sem executar comandos.
O list marca skills congeladas. A regeneração de `UPSTREAM.md` preserva o
campo existente.

**Arquivos tocados:**
- `src/opencode_config/cli/skills_sync.py`, leitura e preservação do campo,
  filtros no sync/update e marcação no list.
- `tests/skills_mgmt/test_sync.py`, quatro testes novos para sync parcial,
  update congelado, list somente leitura e regeneração de metadados.
- `AGENTS.md`, regra de congelamento e autoridade humana documentadas.
- `plan/otimizacao-custo-contexto.md`, este registro E1.

**Testes e análise:**
- Red: os quatro testes novos falharam antes do código por ausência de skip,
  status, marcação e preservação do campo. Comando:
  `.venv/bin/pytest tests/skills_mgmt/test_sync.py -m unit -k 'frozen or synchronization_field' -q`.
- Green/regressão: `.venv/bin/pytest tests/skills_mgmt/test_sync.py -m unit
  -q`: 43 passed, 1 deselected. A execução ficou restrita aos testes unitários
  do módulo de sync; nenhuma suíte completa foi rodada.
- Análise estática: `.venv/bin/ruff check src/opencode_config/cli/skills_sync.py tests/skills_mgmt/test_sync.py`
  passou.
- Higiene do diff: `git diff --check` passou.
- Testes existentes foram mantidos sem alteração. Os testes novos falharam
  antes da implementação e passaram após a implementação.

**Segurança:** nenhum conteúdo real de upstream foi importado ou executado
nesta task. SEC-14 e SEC-15 pertencem a E2/E3. Não houve operação com elevação
(SEC-18) nem inclusão de segredo (SEC-20). A alteração só lê o metadado de
controle e impede comandos de update quando a skill está congelada.

**P1-P5 e documentação:** P3 foi aplicado sem mudar as demais decisões
fechadas. A decisão de congelar continua humana; o CLI não cria nem remove o
campo. A seção de regras de upstream em `AGENTS.md` foi atualizada. Consultei
`docs/README.md`; o item T1 aprovado especifica os testes desta task em
`tests/skills_mgmt/test_sync.py`. Não criei spec adicional fora do plano.

**Gate de refatoração:** sem impacto no plano. A mudança ficou em E1, sem
antecipar detecção, import adicional de skills ou checklist das tasks E2-E4.
Não surgiu decisão arquitetural que exija ADR.

**Pendências para E2-E4:**
- E2: detecção read-only de diferenças upstream e exclusão das skills
  congeladas; permanece sem implementação nesta execução.
- E3: inclusão da `writing-for-agents` e preservação das notas locais;
  permanece sem implementação nesta execução.
- E4: checklist pós-sync, validação de SHA/arquivos e revisão manual de
  segurança do conteúdo novo; permanece sem implementação nesta execução.

### E2 — 2026-09-27

**Executor:** `opencode/gpt-6-luna`.

**Resultado:** concluído. `opencode-skills detect FAMILY` compara cada SHA
registrado com o commit atual do upstream. A operação não altera o checkout,
ignora skills congeladas e mantém a pendência após recusa.

**Escopo e decisões aplicadas:** E2, T2-T4, P1-P5 com foco na P3, lacuna L1,
SEC-12, SEC-13 e SEC-14. P1, P2, P4 e P5 permanecem sem alteração. A P3
orienta a detecção read-only, a análise do agente, a decisão humana e a
aplicação assistida. A saída identifica a família, a skill, os SHAs, os
arquivos e o diff. Cada skill alterada recebe aviso fixo de conteúdo NÃO
CONFIÁVEL e instrução para não executar conteúdo upstream.

O clone shallow fica em diretório temporário fora do checkout, sem recursão
de submódulos, e é removido após a operação. Quando o SHA base não está no
clone shallow, o detector busca o histórico completo no diretório temporário.
SHA ausente ou inválido gera erro acionável antes do clone. A recusa sem
congelamento mantém o SHA de `UPSTREAM.md`, então a detecção reapresenta a
pendência.

**Decisão recebida do devflow (2026-09-27):** autorização para atualizar a
guarda Concordion existente e a configuração Gradle para incluir ADR-0007.
A mudança decorre da decisão aprovada de que ADRs novos 0007-0009 seguem a
convenção dos ADRs retrofitados, com "Asserções executáveis". O teste da
guarda agora deriva os ADRs numerados de `docs/adr/`; ADR-0008 e ADR-0009 não
exigirão edição dessa guarda.

**Integração do fluxo P3:** `harness-conf/commands/sync-upstream-skills.md`
agora executa detecção antes de propor alterações e proíbe `sync` antes da
aprovação humana. O comando trata diffs como não confiáveis, deixa recusa sem
congelamento sem efeito e exige decisão explícita para congelar. README e
`adapters/opencode/README.md` documentam `detect` e `sync` como passos separados.

**Especificações criadas ou atualizadas, conforme `docs/README.md`:**
- `docs/adr/0007-deteccao-read-only-upstream-skills.md` registra a decisão e
  inclui "Asserções executáveis".
- `src/test/groovy/Adr0007Fixture.groovy` implementa a fixture Concordion.
  `build.gradle` registra a fixture na suíte backend.
- `tests/product_tests/test_concordion_spec_infra.py` verifica dinamicamente
  todos os ADRs numerados, a fixture e o registro em uma especialidade.
- Os diagramas gerados `docs/adr/diagrama-c4-l1.md`, `diagrama-c4-l2.md` e
  `diagrama-c4-l3.md` incluem o upstream e o componente `cli.skills_sync`.
- Não criei spec de produto separada. Os testes T2-T4 cobrem a operação, e a
  asserção do ADR aponta para esses testes.

**Arquivos alterados nesta execução:**
- `src/opencode_config/cli/skills_sync.py`, detecção, fallback de histórico,
  clone temporário e saída por skill.
- `tests/skills_mgmt/test_upstream_detect.py`, casos T2-T4 e invariantes SEC-12/14.
- `tests/agents/test_sync_upstream_command.py` e
  `harness-conf/commands/sync-upstream-skills.md`, contrato e fluxo P3.
- `tests/product_tests/test_concordion_spec_infra.py` e `build.gradle`, guarda
  genérica e registro da fixture ADR-0007.
- ADR-0007, fixture Concordion, três diagramas C4, `README.md` e
  `adapters/opencode/README.md`.
- Este registro do plano.

#### Evidências de Testes — Construção E2

- [x] Testes novos: 7 casos de `test_upstream_detect.py` falharam antes da detecção,
  porque `detect` ainda não existia. A guarda de ADR falhou antes da criação
  da fixture. O teste do comando falhou antes da atualização do fluxo.
- [x] Regressão de skills: `.venv/bin/pytest tests/skills_mgmt/ -m all -q`,
  74 passaram.
- [x] Guarda Concordion e comando: `.venv/bin/pytest
  tests/agents/test_sync_upstream_command.py
  tests/product_tests/test_concordion_spec_infra.py -m unit -q`, 19 passaram,
  1 deselected.
- [x] Regressão do adapter Copilot: `.venv/bin/pytest
  tests/harnesses/test_copilot.py -m unit -q`, 28 passaram.
- [x] Build de specs: teste de integração
  `test_render_adr_specs_task_derives_every_numbered_adr_spec`, 1 passou com
  `JAVA_HOME=/home/vitor/.local/share/jdk`.
- [x] Fixture Concordion: `gradle -q test -PproductSpecialty=backend
  --tests Adr0007Fixture --no-daemon`, passou.
- [x] Análise estática: `ruff check` nos módulos e testes alterados passou.
  `git diff --check` passou. Os artefatos novos e as linhas adicionadas ao
  bloco E2 têm até 120 colunas.
- [x] Regressão incremental executada após cada ajuste de código e teste.
- [x] A suíte completa do projeto não foi executada, conforme instrução do
  solicitante. A primeira tentativa da integração falhou por `JAVA_HOME` não
  definido no processo. Reexecutei com o JDK já instalado, sem alterar o
  ambiente persistente.

**Segurança:** a detecção só lê `UPSTREAM.md` e dados Git. Diff usa
`--no-ext-diff` e `--no-textconv`. Clone e fetch desativam submódulos. Nenhum
conteúdo upstream é executado. Não rodei testes de segurança, que pertencem ao
agente `sec`.

**Gate de refatoração:** sem mudança de escopo ou de decisão aprovada. A
atualização do comando e da documentação conecta a nova detecção ao fluxo P3
existente. ADR-0007 registra a decisão técnica exigida por E2.

**Restrições atendidas:** não alterei `Status`, não toquei em
`plan/insumo-devflow-spawn-dinamico.md` e não criei commit.

### E3 — 2026-09-27

**Executor:** `opencode/gpt-6-luna`.

**Resultado:** concluído. `writing-for-agents` agora é uma família do CLI.
O sync copia `SKILL-MECHANICS.md`, mantém o `SKILL.md` local e atualiza o
`UPSTREAM.md` com os campos de descrição e as notas locais preservadas.

**Escopo:** E3, T5, T6 e lacuna L2. Não alterei E4.

**Implementação:**
- `SPECS` registra `writing-for-agents` no repositório mattpocock/skills,
  branch `main`.
- `_sync_writing_for_agents` valida os arquivos esperados e copia a mecânica.
  `_copy_skill_md` mantém a regra de não sobrescrever `SKILL.md` existente.
- `_write_upstream` preserva `## Notas locais` e migra a antiga seção de
  segurança para esse formato. O sync registra `description_lang` e a nota
  curta em uma linha.
- `harness-conf/skills/writing-for-agents/UPSTREAM.md` agora aponta para o
  comando do CLI. O comando manual em linha única saiu. A revisão de
  segurança de 2026-09-22 permanece nas notas locais.
- A tabela de sync do `AGENTS.md` inclui `writing-for-agents`. T6 confere
  que cada família do CLI aparece nessa tabela (L2).

**Arquivos tocados nesta execução:**
- `src/opencode_config/cli/skills_sync.py`.
- `tests/skills_mgmt/test_sync.py`, casos T5 e T6.
- `AGENTS.md` e `harness-conf/skills/writing-for-agents/UPSTREAM.md`.
- Este registro do plano.

**Documentação e arquitetura:** consultei `docs/README.md` e os princípios
de documentação. O `UPSTREAM.md` já é o artefato definido para skills
externas. Não criei spec adicional nem ADR.

#### Evidências de Testes — Construção E3

- [x] Red: os dois testes novos falharam antes da implementação. O teste T5
  rejeitou a família ausente no parser; T6 rejeitou a família ausente no CLI.
  Comando: `.venv/bin/pytest tests/skills_mgmt/test_sync.py -m unit -k
  'writing_for_agents_sync or sync_table_documents' -q`.
- [x] Green e regressão do módulo: `.venv/bin/pytest
  tests/skills_mgmt/test_sync.py -m unit -q`, 45 passaram, 1 foi
  deselecionado.
- [x] CLI: `.venv/bin/opencode-skills list` incluiu `writing-for-agents`.
- [x] Análise estática: `ruff check` no módulo e no teste passou.
  `git diff --check` passou.
- [x] Linhas adicionadas verificadas com limite de 120 colunas.
- [x] Nenhuma suíte completa foi executada, conforme pedido. Nenhum teste
  existente foi alterado e nenhum teste novo usa `skip`.

**Segurança:** usei fixture Git local com licença MIT. Não baixei nem executei
conteúdo do upstream. A revisão já registrada foi preservada no `UPSTREAM.md`.

**Gate de refatoração:** sem impacto no plano ou decisão arquitetural nova.
Mantive o roteamento existente do CLI e ampliei o gerador de metadados.

**Restrições atendidas:** não alterei `Status`, não toquei em
`plan/insumo-devflow-spawn-dinamico.md` e não criei commit.

### E4 — 2026-09-27

**Executor:** `opencode/gpt-6-luna`.

**Resultado:** concluído. O checklist pós-sync agora separa verificações
automatizadas, guardadas por testes, de verificações manuais que dependem de
avaliação humana.

**Escopo:** E4 e T7. Não alterei a lógica de sync implementada em E1-E3.

**Testes adicionados em `tests/skills_mgmt/test_sync.py`:**
- Teste de integração com upstream Git local de dois commits. Após avançar o
  upstream e aplicar o sync, verifica o SHA novo em `UPSTREAM.md`, a declaração
  do arquivo sincronizado, sua existência e igualdade byte a byte com o upstream.
  Também confirma que a versão local adaptada de `SKILL.md` não foi sobrescrita.
- Teste unitário verifica que o checklist separa garantias automáticas e manuais
  e marca explicitamente a revisão de segurança como manual.
- A cobertura existente de não sobrescrever `SKILL.md` também está em
  `test_accessibility_sync_preserves_skill_and_description_adaptation` e
  `test_addyosmani_sync_copies_references_without_overwriting_skill`.

**Documentação:** atualizei a seção "Checklist pós-sync" do `AGENTS.md`.
As verificações automáticas cobrem SHA, arquivos sincronizados e preservação de
`SKILL.md`. As etapas manuais mantêm a revisão de segurança (prompt injection,
comandos, URLs e exfiltração), a avaliação de impacto em `SKILL.md` e a decisão
humana sobre aplicação assistida. Consultei `docs/README.md` e
`harness-conf/agents/references/principios-documentacao.md`. O artefato
`UPSTREAM.md` existente é o formato definido para skills externas; não criei
spec ou ADR adicional.

#### Evidências de Testes — Construção E4

- [x] Red: o teste do checklist falhou antes da documentação ser atualizada,
  pois não havia distinção entre verificações automáticas e manuais. O teste de
  integração passou nesse primeiro ciclo porque E1-E3 já implementavam o sync
  validado pela nova guarda.
- [x] Green/regressão: `.venv/bin/pytest tests/skills_mgmt/ -m all -q`,
  78 passed.
- [x] Análise estática: `.venv/bin/ruff check
  src/opencode_config/cli/skills_sync.py tests/skills_mgmt/test_sync.py`, passou.
- [x] Higiene do diff: `git diff --check` passou.
- [x] Regressão incremental executada após a alteração do checklist; nenhum
  teste existente foi alterado e nenhum teste novo usa `skip`.
- [x] A suíte completa do projeto não foi executada, conforme instrução.

**Segurança:** usei somente fixture Git local; não baixei nem executei conteúdo
upstream. A revisão de segurança continua manual e explícita no checklist. Não
executei testes de segurança, responsabilidade do agente `sec`.

**Gate de refatoração:** sem impacto no plano; não houve mudança de lógica
produtiva, comportamento ou decisão arquitetural. Nenhum ADR necessário.

**Restrições atendidas:** não alterei `Status`, não toquei em
`plan/insumo-devflow-spawn-dinamico.md` e não criei commit.

**Pendências para waves futuras:** nenhuma implementação de E4 pendente. Em
cada sync futuro, a revisão de segurança do conteúdo upstream e a decisão de
aplicar mudanças em `SKILL.md` continuam manuais e dependem de aprovação humana.

### E5 — 2026-09-27

**Executor:** `opencode/gpt-6-luna`.

**Resultado:** o adapter Copilot fornece uma descrição específica para o comando
`otimizar-agents-md`; a conversão não usa mais o fallback genérico.

**Implementação:** acrescentei a entrada do comando em `_COMMAND_DESCRIPTIONS`,
com gatilhos em PT-BR para otimizar, enxugar ou revisar `AGENTS.md`.

**Teste:** criei `test_copilot_adapter_describes_agents_md_optimization_command`.
O teste verifica a descrição específica e a ausência de
`Executa o comando otimizar-agents-md.`. O teste novo falhou antes do código e
passou depois da implementação.

**Evidências:** `.venv/bin/pytest tests/harnesses/test_copilot.py -m unit -q`
passou com 36 testes em 30,93 s. O Ruff nos arquivos Python alterados e a
`git diff --check` passaram. A suíte final E12 também inclui este teste.

**Documentação e arquitetura:** consultei `docs/README.md`. O teste T8 é o
artefato de aceitação previsto para esta descrição; não criei spec Concordion
nem ADR adicional.

**Commit:** `e7c4115 fix(copilot): description do command de otimizacao de AGENTS.md`.

**Restrições:** não alterei `Status` nem
`plan/insumo-devflow-spawn-dinamico.md`.

### E9 — 2026-09-27

**Executor:** `opencode/gpt-6-luna`.

**Estado:** concluído. Reflowei 31 linhas físicas acima de 120 colunas em
oito arquivos de agentes. Das oito linhas de tabela, reformulei duas células
para caber e usei continuação com as duas primeiras células vazias nas outras
seis.

**Escopo:** E9 e T14. A guarda cobre apenas `harness-conf/agents/*.md` e
`harness-conf/AGENTS.base.md`. `SKILL.md` e `references/` ficam fora.

**TDD:** criei `tests/agents/test_line_width.py` antes do reflow. O teste
falhou como esperado e listou as 31 linhas acima de 120 colunas nos oito
arquivos de agentes. `harness-conf/AGENTS.base.md` não gerou violações.

**Documentação e arquitetura:** consultei `docs/README.md` e
`harness-conf/agents/references/principios-documentacao.md`. A guarda unitária
é o artefato previsto por T14. Não há spec adicional ou ADR para esta mudança.

**Arquivos alterados:**
- `harness-conf/agents/analista.md`
- `harness-conf/agents/curador-produto.md`
- `harness-conf/agents/dba.md`
- `harness-conf/agents/eng-software.md`
- `harness-conf/agents/qa.md`
- `harness-conf/agents/rev.md`
- `harness-conf/agents/revisor-historia.md`
- `harness-conf/agents/sec.md`

#### Evidências de Testes — Construção E9

- [x] T14 novo: `.venv/bin/pytest tests/agents/test_line_width.py -m all -q`;
  falhou antes do reflow com 31 violações e passou depois, com 1 passed.
- [x] Regressão do módulo: `.venv/bin/pytest tests/agents/ -m all -q`,
  182 passed.
- [x] Checagem estática de largura: T14 confirmou o limite de 120 colunas.
  `git diff --check` também passou.
- [x] Regressão incremental: T14 foi executado após o reflow e após a
  correção das duas linhas restantes.
- [x] Gate de refatoração: sem impacto no plano. O reflow preserva o conteúdo
  e altera somente a apresentação física das linhas.
- [x] Não rodei a suíte completa, não alterei `Status`, não toquei em
  `plan/insumo-devflow-spawn-dinamico.md` e não criei commit.

### Perguntas (construção)

- **Atualização da guarda de ADR e do build para ADR-0007 — RESPONDIDA
  (devflow, 2026-09-27):** autorizada como consequência direta da convenção
  aprovada para ADRs 0007-0009. A guarda deriva os ADRs numerados do diretório,
  então os próximos dois não exigirão edição desse teste.
- **E9, reflow em tabelas Markdown — RESPONDIDA (devflow, 2026-09-27):**
  primeiro encurtar ou reformular o texto da célula, sem perda de informação.
  Se a linha ainda exceder 120 colunas, usar continuação com as duas primeiras
  células vazias. T14 mantém o limite de 120 colunas em todas as linhas,
  inclusive nas continuações. A pergunta original consultava a aprovação desse
  formato ou de outra representação.
- **E6, testes existentes em conflito com P4 — RESPONDIDA (devflow,
  2026-09-27):** autorizado atualizar os quatro testes existentes para o
  contrato P4, sem excluir testes. Reapresente as garantias antigas como
  asserções para skills globais em `.copilot/skills/`, skills de domínio em
  `~/.copilot/referencias/skills/` e os blocos gerados nos perfis. Siga os
  destinos exatos definidos em P4.
- **E6, asserção do bloco de referências nos perfis — RESPONDIDA (devflow,
  2026-09-27):** não antecipar os blocos dos perfis na E6. Blocos gerados no
  corpo dos perfis são escopo da E14. Decisão de organização de escopo.

### E13 — 2026-09-27

**Executor:** `opencode/gpt-6-luna`.

**Resultado:** apliquei em `harness-conf/AGENTS.base.md` os textos aprovados
na P5. Substituí a seção de compactação sem alterar o conteúdo aprovado e
acrescentei `Chamadas de ferramentas`. A regra de precedência sobre a premissa
7 saiu do arquivo base. Não alterei `docs/workflow-agentes-dev.md`.

**Conteúdo aplicado, conforme P5:**
- Compactação: avaliação após etapa concluída e resultado salvo; compactação
  por conta própria com mecanismo disponível; pedido ao humano se nenhum
  mecanismo for disponível ou suficiente; leitura por trechos e consultas
  direcionadas; threshold como rede de segurança.
- Chamadas de ferramentas: agrupar operações independentes em paralelo e
  sequenciar operações apenas quando houver dependência real.

**Validações:**
- `.venv/bin/pytest tests/agents/test_line_width.py -m all -q`: 1 passed.
  A guarda verifica `harness-conf/agents/*.md` e
  `harness-conf/AGENTS.base.md`, com limite de 120 colunas.
- `.venv/bin/pytest tests/agents/test_workflow_consistency.py -m all -q`:
  20 passed.
- `git diff --check -- harness-conf/AGENTS.base.md
  plan/otimizacao-custo-contexto.md`: passou.
- Não executei a suíte completa, não alterei `Status`, não toquei em
  `plan/insumo-devflow-spawn-dinamico.md` e não criei commit.

**Documentação e arquitetura:** consultei `docs/README.md` e
`harness-conf/agents/references/principios-documentacao.md`. A mudança não
exige spec ou ADR adicional. A atualização do workflow permanece pendente de
aprovação humana.

**Proposta da premissa 7 — AGUARDANDO APROVAÇÃO HUMANA**

O devflow apresentará esta redação ao humano. Não apliquei a proposta em
`docs/workflow-agentes-dev.md`; a aplicação fica para task posterior após
aprovação.

```markdown
7. **Seleção de modelo por fase** — ao iniciar, `devflow`
   sugere um padrão (um modelo por etapa — planejamento,
   execução, testes, revisão) e o humano define como
   preferir: um modelo só, por fase granular ou arranjo
   próprio. O mapa combinado fica registrado no arquivo.
   O workflow pausa antes de fases cujo modelo difere do atual.
   Política padrão de sessão: `{workflowId}-{fase}-{agente}`;
   retomada dentro da fase e sessão nova entre fases.
   Após cada etapa concluída e resultado salvo, o agente
   avalia compactar antes de iniciar a próxima. A compactação
   compensa quando o histórico já é grande e ainda virão
   muitas chamadas. Com contexto pequeno ou pouco trabalho
   restante, o custo da compactação supera a economia: não
   compacte.
   O agente reduz o contexto por conta própria com qualquer
   mecanismo disponível no harness (compactação, nova sessão
   ou spawn com estado persistido em arquivo, ou equivalente).
   Sem mecanismo disponível ou suficiente, o agente pede ao
   humano.
   O agente segura o crescimento: lê trechos (offset/limit) e
   consultas direcionadas. O agente não reinsere arquivos e
   logs completos no contexto.
    A auto-compactação por threshold é rede de segurança, não
    plano. Se disparar, a fronteira foi perdida.
```

### E6 — 2026-09-27

**Executor:** `opencode/gpt-6-luna`.

**Estado:** roteamento de skills implementado e validado. Não antecipei o bloco
dos perfis. O devflow confirmou que esse bloco pertence à E14, registrada em
seção própria após a E6.

**Decisão recebida do devflow (2026-09-27):** autorizado atualizar os quatro
testes existentes para P4. Nenhum teste foi removido; as garantias foram
reexpressas nos novos destinos. A pergunta sobre essa autorização foi marcada
RESPONDIDA em `### Perguntas (construção)`.

**Implementação:** o adapter deriva o roteamento de `permission.skill` em
`harness-conf/opencode.json`, incluindo padrões wildcard. As 10 skills sem
deny global vão para `~/.copilot/skills/`; as 23 skills cobertas por deny vão
para `~/.copilot/referencias/skills/`. Cópias antigas na pasta errada recebem
backup e são removidas, evitando descoberta automática de skills de domínio.
O plano impresso pelo adapter discrimina os dois destinos e as contagens.

**Testes:** atualizei os quatro testes existentes sem deletá-los. A skill de
domínio mantém frontmatter na pasta auxiliar; `question-orchestration` e
`web-research-exa-crawl4ai` permanecem na descoberta por serem globais; o
conteúdo da segunda continua byte a byte igual à fonte. O teste de backup
verifica a migração e remoção de uma cópia legada da pasta de descoberta.
Adicionei T9 para verificar a soma 10/23, a partição integral das skills da
fonte, a ausência de domínio na descoberta e o efeito de alterar um deny.

**Documentação e arquitetura:** consultei `docs/README.md` e
`harness-conf/agents/references/principios-documentacao.md`. Atualizei a seção
Adapters do `README.md` com os destinos, o mapa de permissions e a migração com
backup. O plano de testes do ciclo prevê asserções em pytest; não criei spec
adicional ou ADR. A asserção do bloco nos perfis permanece associada à E14 e
segue a decisão do devflow de não antecipar esse escopo na E6.

**Arquivos alterados nesta execução:**
- `src/opencode_config/harnesses/copilot.py`.
- `tests/harnesses/test_copilot.py`.
- `README.md`, somente a descrição dos destinos das skills Copilot.
- Este registro e a resposta à pergunta de autorização neste plano.

#### Evidências de Testes — Construção E6 (parcial)

- [x] RED: depois de atualizar os testes e antes da implementação, o recorte
  executado teve 4 failed e 2 passed. As falhas demonstraram destinos auxiliares
  ausentes, inclusão indevida de domínio na descoberta e roteamento independente
  do mapa.
- [x] Green do módulo: `.venv/bin/pytest tests/harnesses/test_copilot.py
  -m unit -q`, 30 passed.
- [x] Regressão focada: `.venv/bin/pytest tests/harnesses/ tests/agents/
  -m all -q`, 240 passed. Não executei a suíte completa.
- [x] Análise estática: `.venv/bin/ruff check
  src/opencode_config/harnesses/copilot.py tests/harnesses/test_copilot.py`,
  passou. `git diff --check` nos arquivos alterados passou.
- [x] Regressão incremental: recorte RED antes do código; testes do módulo e
  regressão focada após a implementação.
- [x] Gate de refatoração: o roteamento não alterou a decisão P4. O devflow
  confirmou que o bloco pertence à E14; a implementação ficou em seção própria.

**Restrições:** não alterei `Status`, não toquei em
`plan/insumo-devflow-spawn-dinamico.md`, não executei a suíte completa e não
criei commit.

### E14 — 2026-09-27

**Executor:** `opencode/gpt-6-luna`.

**Resultado:** concluído. O adapter acrescenta referências às skills de domínio
autorizadas somente na cópia materializada dos perfis do Copilot. Cada entrada
tem a descrição completa da fonte e o caminho absoluto da cópia auxiliar.
Agentes sem allow não recebem o bloco. O adapter não copia o corpo da skill
para o perfil.

**Implementação:** `_sync_agents` deriva cada bloco das permissões da fonte do
agente e do roteamento de skills produzido por E6. O bloco usa descrições de
`harness-conf/skills/*/SKILL.md`, caminhos em
`.copilot/referencias/skills/` e marcadores gerados próprios. A extração mantém
a descrição completa de scalars YAML dobrados. A sincronização não lê o corpo
da pasta auxiliar para compor o bloco.

**Decisão de escopo:** o devflow respondeu que E6 não deve antecipar os blocos
dos perfis. A resposta foi registrada e marcada RESPONDIDA em
`### Perguntas (construção)`. E14 mantém sua fronteira original.

**Documentação e arquitetura:** consultei `docs/README.md` e
`harness-conf/agents/references/principios-documentacao.md`. Criei
`docs/adr/0009-skills-de-dominio-nos-perfis-copilot.md` com a seção
"Asserções executáveis" e a fixture `src/test/groovy/Adr0009Fixture.groovy`.
Registrei a fixture na suíte backend em `build.gradle`. Atualizei o README e os
diagramas C4 L1-L3 para refletir a decisão.

**Arquivos alterados nesta execução:**
- `src/opencode_config/harnesses/copilot.py`.
- `tests/harnesses/test_copilot.py`, novo caso T10; alterações E6 preexistentes
  foram preservadas.
- `docs/adr/0009-skills-de-dominio-nos-perfis-copilot.md` e
  `src/test/groovy/Adr0009Fixture.groovy`.
- `build.gradle`, registro da fixture na suíte backend; alteração E2
  preexistente foi preservada.
- `README.md`, descrição dos perfis com referências por agente; alteração E6
  preexistente foi preservada.
- `docs/adr/diagrama-c4-l1.md`, `diagrama-c4-l2.md` e `diagrama-c4-l3.md`.
- Este registro e a resposta à pergunta de escopo no plano.

#### Evidências de Testes — Construção E14

- [x] T10 novo: o teste falhou antes do código porque o perfil não tinha o
  marcador do bloco gerado. Depois da implementação, uma asserção mais estrita
  detectou o indicador `>` da descrição YAML na saída; corrigi a extração.
- [x] T10 passou após a correção, incluindo allow e ausência de allow,
  descrição completa, caminho absoluto com espaços, fonte limpa e exclusão do
  marcador plantado no corpo da skill.
- [x] Módulo Copilot: `.venv/bin/pytest tests/harnesses/test_copilot.py
  -m unit -q`, 31 passaram.
- [x] Regressão focada: `.venv/bin/pytest tests/harnesses/ -m all -q`,
  59 passaram.
- [x] Guarda da infra ADR: `.venv/bin/pytest
  tests/product_tests/test_concordion_spec_infra.py -m unit -q`, 20 passaram,
  1 teste de integração foi deselecionado.
- [x] Fixture Concordion: `JAVA_HOME=/home/vitor/.local/share/jdk gradle -q
  test -PproductSpecialty=backend --tests Adr0009Fixture --no-daemon`, passou.
- [x] Análise estática: `ruff check` nos arquivos Python alterados passou.
  `git diff --check` nos arquivos desta task passou.
- [x] Regressão incremental: executei T10 em RED antes do código, após a
  primeira implementação e depois da correção da descrição YAML.
- [x] Gate de refatoração: sem mudança de escopo ou conflito com P4. A E14
  ficou separada da E6, conforme a decisão recebida.
- [x] Não executei a suíte completa, não alterei `Status`, não toquei em
  `plan/insumo-devflow-spawn-dinamico.md` e não criei commit.

**Pendências para E10:** E10 continua pendente. A task ainda precisa integrar o
MCP do Copilot com merge aditivo e backup, implementar o provisionamento e
validar os critérios próprios. O adapter agora contém E6 e E14 antes dessa
integração.

### E10 — 2026-09-27

**Executor:** `opencode/gpt-6-luna`.

**Resultado:** a implementação do provisionamento ai-memory e da declaração MCP
condicional está concluída. A fonte canônica declara `mcp.ai-memory` sem
credenciais. O bootstrap só sinaliza provisionamento completo depois de
validar wrapper, container, bind, rede, volume e hooks.

**P1 e tudo-ou-nada:** o bootstrap baixa wrappers oficiais por HTTPS e valida
SHA-256 fixado no código. A imagem `akitaonrails/ai-memory:latest` permanece
sem pin, conforme decisão humana. O container publica apenas
`127.0.0.1:49374`, usa rede Docker `internal` e monta
`~/.local/share/ai-memory/` em `/data`. No POSIX, o bootstrap restringe esse
diretório ao usuário.

Docker ausente ou provisionamento incompleto desativa o marcador, os hooks e as
declarações gerenciadas dos dois harnesses. A mensagem orienta instalação
user-space e proíbe `sudo`. Docker ausente não falha silenciosamente e não torna
o bootstrap geral malsucedido. Falhas de integridade, container ou config
retornam erro e também mantêm MCP desabilitado.

**Risco do symlink POSIX:** o adapter OpenCode nunca edita o symlink nem seu
alvo canônico. Sem marcador, a strategy materializa um arquivo JSON regular
com `mcp.ai-memory` filtrado. Com o provisionamento completo, a sincronização
restaura o symlink canônico. A fonte `harness-conf/opencode.json` permanece
intacta nos dois caminhos.

**Copilot e rollback:** o adapter converte a entrada canônica para
`mcpServers.ai-memory`, cria backup antes da primeira escrita e preserva todos
os servers existentes. Um `ai-memory` diferente, definido pelo usuário, bloqueia
a escrita quando o servidor estaria ativo e permanece intacto quando a
integração está desabilitada. `opencode-bootstrap --rollback-ai-memory` remove
o container, wrappers, hooks e declarações gerenciadas. O rollback restaura
`opencode.jsonc`, remove a rede apenas quando o bootstrap a criou e preserva o
volume de dados.

**Documentação e arquitetura:** consultei `docs/README.md` e
`harness-conf/agents/references/principios-documentacao.md`. Atualizei a seção
de dependências e o roteiro de provisionamento/rollback em `README.md`.
`docs/specs/Seguranca.md` contém as asserções SEC-01..SEC-11 e SEC-21. A
aprovação humana dessas asserções permanece pendente para a revisão. Criei
ADR-0008 com "Asserções executáveis", sua fixture Concordion e o registro na
especialidade segurança de `build.gradle`. Atualizei os diagramas C4 L1-L3.
Não editei `docs/README.md`, que pertence ao `curador-produto`.

**Arquivos desta task:**
- `harness-conf/opencode.json` e
  `src/opencode_config/bootstrap/ai_memory.py`, configuração e provisionamento.
- `src/opencode_config/bootstrap/main.py` e
  `src/opencode_config/harnesses/__init__.py`, fluxo e estado condicional.
- `src/opencode_config/harnesses/opencode.py`, filtro POSIX/Windows sem escrita
  através do symlink canônico.
- `src/opencode_config/harnesses/copilot.py`, merge aditivo de MCP e backup;
  alterações E6/E14 preexistentes foram preservadas.
- `tests/bootstrap/test_ai_memory_provision.py`, testes T13 com fakes.
- `tests/harnesses/test_opencode.py` e `tests/harnesses/test_copilot.py`, T11,
  T12 e casos de configuração condicional.
- `docs/specs/Seguranca.md`, `docs/adr/0008-ai-memory-bootstrap-mcp.md`,
  `src/test/groovy/SegurancaFixture.groovy` e
  `src/test/groovy/Adr0008Fixture.groovy`.
- `build.gradle`, registro do ADR-0008; alteração E2 preexistente preservada.
- `README.md`, dependência, provisionamento e rollback; conteúdo E6/E14
  preexistente preservado.
- `docs/adr/diagrama-c4-l1.md`, `diagrama-c4-l2.md` e `diagrama-c4-l3.md`,
  conteúdo E2/E14 preexistente preservado.
- Este bloco no plano. Não alterei `Status` nem
  `plan/insumo-devflow-spawn-dinamico.md`.

#### Evidências de Testes — Construção E10

- [x] RED inicial: `.venv/bin/pytest tests/harnesses/test_opencode.py
  tests/harnesses/test_copilot.py -m all -k ai_memory -q` produziu 5 failed,
  1 passed e 47 deselected antes da implementação dos adapters e da config.
- [x] RED adicional: T13 falhou quando o container fake saiu durante o start.
  O caso do Copilot também falhou quando o adapter removia uma entrada
  `ai-memory` preexistente do usuário.
- [x] T13: `.venv/bin/pytest tests/bootstrap/test_ai_memory_provision.py
  -m unit -q`, 16 passed. Os testes usam downloader, runner Docker e porta
  falsos; não iniciam Docker nem acessam a rede. Acrescentei uma fixture
  autouse que bloqueia `subprocess.Popen` no módulo, exceto quando o próprio
  teste instala um processo fake; uma chamada sem stub falha antes de iniciar
  qualquer processo real.
- [x] OpenCode: `.venv/bin/pytest tests/harnesses/test_opencode.py -m all
  -k 'ai_memory or opencode_creates_canonical_symlinks' -q`, 4 passed,
  15 deselected.
- [x] Copilot: `.venv/bin/pytest tests/harnesses/test_copilot.py -m unit
  -k ai_memory -q`, 4 passed, 31 deselected.
- [x] Bootstrap: `.venv/bin/pytest tests/bootstrap/test_entrypoints.py
  -m unit -k 'check_only or apply_forwards' -q`, 2 passed, 11 deselected.
- [x] Guarda ADR: `.venv/bin/pytest
  tests/product_tests/test_concordion_spec_infra.py -m unit -k 0008 -q`,
  2 passed, 21 deselected.
- [x] Gradle executou `SegurancaFixture` e `Adr0008Fixture` em uma versão
  anterior da spec; ambas passaram. Depois, SEC-07 ganhou a asserção de mode
  `0700`. A fixture final compilou com `gradle -q compileTestGroovy --no-daemon`.
  A execução final da spec de segurança fica para `sec`/`qa`.
- [x] Análise estática: `ruff check` nos módulos e testes E10 passou.
  `ruff format --check` passou nos arquivos novos. `git diff --check` passou.
- [x] Não executei suítes completas de `tests/bootstrap/` nem
  `tests/harnesses/`, testes agregados de segurança ou o roteiro manual RM.
- [x] Regressão incremental executada nos testes focados após as mudanças.

**Correção de hermeticidade e limpeza do ambiente:** a execução RED inicial
usou o runner Docker real por falta de stub naquela chamada. O fluxo abortou
antes do download, pull, container ou hooks, mas deixou a rede `ai-memory-internal`
vazia. O teste unitário agora instala uma guarda autouse em `subprocess.Popen`;
os caminhos Docker usam `FakeAiMemoryRunner`, e qualquer chamada não stubada falha
sem tocar no host. A rede foi removida a pedido do devflow:
`docker network rm ai-memory-internal` retornou `ai-memory-internal`. A consulta
`docker network ls --filter name=^ai-memory-internal$ --format '{{.Name}}'`
confirmou que não há rede com esse nome. Não alterei container, imagem, plugin,
config ou volume real.

**Revalidação após decisões do devflow (2026-09-27):**
- `.venv/bin/pytest tests/bootstrap/test_ai_memory_provision.py -m unit -q`:
  16 passed. A guarda impediu qualquer execução de subprocesso real.
- `.venv/bin/pytest tests/harnesses/test_opencode.py
  tests/harnesses/test_copilot.py -m all -k ai_memory -q`: 7 passed,
  47 deselected.
- `.venv/bin/pytest tests/bootstrap/test_entrypoints.py -m unit -k
  'check_only or apply_forwards' -q`: 2 passed, 11 deselected.
- `.venv/bin/pytest tests/product_tests/test_concordion_spec_infra.py
  -m unit -k 0008 -q`: 2 passed, 21 deselected.
- `ruff check`, `ruff format --check` no teste T13 e `git diff --check`:
  passaram. Não executei a suíte completa.

**Gate de refatoração:** sem retorno ao planejamento. O filtro de cópia na
strategy POSIX implementa o contorno do symlink já previsto como internalidade
da P1. ADR-0008 registra a decisão aprovada; não alterei o escopo E10.

**Pendências para a fase Testes:** executar o roteiro RM-1..RM-13 na máquina do
humano, validar o MCP após reiniciar cada harness e executar as suítes completas
definidas pelo plano. O agente `sec` ou `qa` deve executar a spec final de
segurança e registrar a aprovação humana SEC→spec. Container antigo
incompatível exige backup do volume e o caminho de rollback descrito no README.

**Nota de retomada:** o parágrafo `Pendências para E10` da seção E14 registra
um estado anterior à construção. Esta subseção registra o resultado atual.

### Perguntas (E10)

- **Rede Docker `ai-memory-internal` — RESPONDIDA (devflow, 2026-09-27):**
  corrigir o teste para usar runner Docker fake no fluxo unitário e remover a
  rede órfã com `docker network rm ai-memory-internal`. A remoção retornou o
  nome da rede; a listagem posterior não encontrou rede com esse nome.

### E7 — 2026-09-27

**Executor:** `opencode/gpt-6-luna`.

**Resultado:** auditoria focalizada concluída, sem alteração de código. A amostra permaneceu nas
16 skills da P2; não expandi para 33, conforme a restrição desta execução. O relatório completo,
com método, evidências e avaliação por skill, está em `/tmp/opencode/e7-auditoria-2026-09-27.md`.

**Método e amostra:** li integralmente `AGENTS.md`, `harness-conf/AGENTS.base.md` e as 16 skills.
Comparei permissions dos 14 agentes e suas menções às skills. Conferi os oito `UPSTREAM.md` da
amostra e a existência dos arquivos declarados como sincronizados. A seleção de quatro skills de
domínio com upstream e quatro locais usou `random.Random(20260927)` após ordenação alfabética das
duas populações. A auditoria de no-op foi estática; não executei avaliação com modelo.

- Core: `code-explorer-priority`, `git-workflow-and-versioning`, `humanizer-br`,
  `planning-and-task-breakdown`, `portugues-tecnico-controlado`, `question-orchestration` e
  `reliable-async-operations`.
- Upstream: `api-and-interface-design`, `code-simplification`, `documentation-and-adrs` e
  `performance-optimization`.
- Locais: `aws-sso-login`, `md-export`, `spec-executavel` e `web-research-exa-crawl4ai`.
- Referência: `writing-for-agents`.

**Permissions:** `opencode.json` tem 21 denies nominais e `aws-*`, que cobre duas skills, total de
23 denies. Os 69 allows em 11 agentes correspondem ao mapa v4. Não identifiquei skill negada sem
allow nem menção a skill negada sem allow no corpo individual do agente consumidor. O uso de
`code-explorer-priority` em seis agentes vem da regra compartilhada de `AGENTS.base.md`. O allow
`planning-and-task-breakdown` de `devflow` não tem acionamento no corpo desse agente. Os três
allows de `writing-for-agents` não têm gatilho explícito nos corpos locais, embora o base cite o
método para alterações de skills; não propus alterar a decisão humana que disponibilizou a skill
a esses três agentes. A regra compartilhada instrui todos os agentes a seguir esse método, mas só
três têm allow para carregar a skill.

**Regras do repo:** li os dois arquivos completos. Há conflito de precedência: `AGENTS.md` exige
aprovação humana para qualquer alteração em agente ou workflow; `AGENTS.base.md` manda corrigir
imediatamente violações objetivas de formatação, largura e estilo. Os outros achados estão nas
skills globais amostradas.

**Resultado da amostra:** descrições e corpos correspondem, salvo os achados registrados. Oito
metadados upstream e os arquivos sincronizados declarados estão presentes. Não validei SHAs contra
os repositórios remotos. Quatorze skills excedem aproximadamente 100 linhas. O split só tem ganho
claro em `reliable-async-operations`, que junta seis categorias e exemplos em Python, Node.js,
Bash, PowerShell, Java e Groovy.
PTC, `writing-for-agents` e `performance-optimization` já usam referências por ramo; os demais
corpos longos são sequências ou referências coesas.

#### E-fix gerados por E7

Prioridades abaixo são sugestões. A decisão de prioridade e execução neste ciclo permanece humana.
Todas as tasks dependem de E7.

- **E-fix-1, P1 sugerida, escopo S:** alinhar `documentation-and-adrs` a `docs/README.md`. A skill
  indica `docs/decisions/` e um template de ADR sem asserção executável. O repo exige `docs/adr/` e
  asserção em cada ADR novo.
- **E-fix-2, P1 sugerida, escopo S:** resolver as regras contraditórias de timeout em
  `reliable-async-operations`. A revisão exige timeout total e de inatividade para toda operação,
  mas as regras anteriores aceitam evento ou polling sem timeout. Os exemplos também fixam valores
  sem justificativa, apesar da proibição de timeouts chutados.
- **E-fix-3, P2 sugerida, escopo S:** mover os exemplos por categoria de
  `reliable-async-operations` para uma referência e manter as regras gerais no corpo.
- **E-fix-4, P1 sugerida, escopo S:** alinhar `git-workflow-and-versioning` ao formato local
  `tipo(escopo): descrição`, substituir os comandos pre-commit específicos de Node e retirar
  `git reset --hard HEAD` como recuperação sem proteção de mudanças locais.
- **E-fix-5, P2 sugerida, escopo S:** corrigir o ponteiro quebrado para
  `deprecation-and-migration` em `api-and-interface-design`; não existe skill ou referência com
  esse nome no repo.
- **E-fix-6, P2 sugerida, escopo S:** restringir `humanizer-br` a reescritas e aplicar sua saída de
  quatro partes apenas nessas tarefas. A description aciona a skill em todo chat, mas o corpo exige
  versões, auditoria e resumo para cada ativação.
- **E-fix-7, P2 sugerida, escopo S:** remover ou centralizar a tabela duplicada de Core Web Vitals
  entre `performance-optimization` e `references/performance-checklist.md`.
- **E-fix-8, P2 sugerida, escopo S:** consolidar regras duplicadas entre “Regras principais” e
  “Fluxo padrão” em `web-research-exa-crawl4ai`.
- **E-fix-9, P2 sugerida, escopo S:** resolver o allow sem acionamento de
  `planning-and-task-breakdown` em `devflow.md`, adicionando trigger ou propondo sua remoção ao
  humano.
- **E-fix-10, P2 sugerida, escopo S:** explicitar nos corpos de `devflow`, `eng-software` e
  `smart-planner` quando carregar `writing-for-agents`, sem alterar a permissão aprovada sem
  decisão humana.
- **E-fix-11, P2 sugerida, escopo S:** restringir triggers genéricos como `Cenário` e `Então` em
  `spec-executavel` a pedidos sobre BDD ou especificação executável.
- **E-fix-12, P2 sugerida, escopo S:** resolver a precedência entre aprovação humana obrigatória
  para mudanças em agentes/workflows e correção imediata de violações objetivas em
  `AGENTS.md`/`AGENTS.base.md`, sem enfraquecer a autoridade humana.
- **E-fix-13, P2 sugerida, escopo S:** esclarecer em `AGENTS.base.md` se a regra sobre
  `writing-for-agents` manda carregar a skill ou seguir o método já conhecido e restringir a
  instrução ao escopo compatível com os allows aprovados.

**Verificação:** `.venv/bin/pytest tests/agents/ -m all -q`: 182 passed em 4,90 s. Não executei a
suíte completa. Consultei `docs/README.md` e os princípios de documentação. Não há mudança de
código, spec ou ADR nesta task.

**Restrições:** não alterei `Status`, não toquei em `plan/insumo-devflow-spawn-dinamico.md` e não
criei commit.

### E-fix — 2026-09-27

**Executor:** `opencode/gpt-6-luna`.

**Diretriz do devflow (2026-09-27):** autonomia máxima, com parada somente em bloqueantes. Apliquei
correções objetivas de conteúdo e consistência, uma por vez. Itens que exigem decisão semântica ou
de design ficaram sem alteração e foram registrados em `## Perguntas` para decisão humana no
fechamento.

**E-fix aplicados:**

1. **E-fix-1 — aplicado.** Alinhei o local e o formato de ADRs às regras do `docs/README.md`. A
   skill agora indica `docs/adr/`, numeração sequencial, Concordion-Markdown e asserção executável
   obrigatória em ADR novo. Atualizei o template com as seções canônicas.
   **Por quê:** a instrução anterior apontava para `docs/decisions/` e omitia a asserção exigida.
   **Arquivo:** `harness-conf/skills/documentation-and-adrs/SKILL.md`.
2. **E-fix-2 — não aplicado.** Mantive as regras de timeout sem alterações.
   **Motivo:** resolver as diferenças entre timeout total, inatividade, sinais e exceções altera o
   comportamento prescrito pela skill. Os testes existentes também protegem decisões específicas
   sobre essa política.
   **Arquivo não tocado:** `harness-conf/skills/reliable-async-operations/SKILL.md`.
   **Pergunta:** Q-Efix-2.
3. **E-fix-3 — não aplicado.** Não movi os exemplos de categorias para outra referência.
   **Motivo:** o split muda a organização e a invocação do conteúdo, uma decisão de design da skill.
   **Arquivo não tocado:** `harness-conf/skills/reliable-async-operations/SKILL.md`.
   **Pergunta:** Q-Efix-3.
4. **E-fix-4 — não aplicado.** Não alterei formato de commit, comandos de pre-commit ou recuperação.
   **Motivo:** a proposta combina o padrão local `tipo(escopo): descrição` com mudanças na orientação
   geral da skill, incluindo comandos e proteção do worktree. Aplicá-la exige decidir o limite entre
   regra local e recomendação reutilizável.
   **Arquivo não tocado:** `harness-conf/skills/git-workflow-and-versioning/SKILL.md`.
   **Pergunta:** Q-Efix-4.
5. **E-fix-5 — aplicado.** Removi o link para `deprecation-and-migration` e mantive a orientação
   para planejar deprecação na fase de design.
   **Por quê:** o destino citado não existe no repo; a frase preserva a orientação sem um ponteiro
   quebrado.
   **Arquivo:** `harness-conf/skills/api-and-interface-design/SKILL.md`.
6. **E-fix-6 — não aplicado.** Mantive o acionamento de `humanizer-br` e seu formato de saída.
   **Motivo:** restringir a skill a pedidos de reescrita altera o escopo de ativação e o contrato de
   saída. O `UPSTREAM.md` local registra a adaptação para uso em toda comunicação de chat.
   **Arquivo não tocado:** `harness-conf/skills/humanizer-br/SKILL.md`.
   **Pergunta:** Q-Efix-6.
7. **E-fix-7 — aplicado.** Removi os valores duplicados da tabela Core Web Vitals na skill e apontei
   para `references/performance-checklist.md` como fonte única dos alvos LCP, INP e CLS. A
   verificação da skill também aponta para essa referência.
   **Por quê:** o checklist é arquivo sincronizado declarado no `UPSTREAM.md`; manter os valores
   nele evita duas fontes para os mesmos limites.
   **Arquivo:** `harness-conf/skills/performance-optimization/SKILL.md`.
8. **E-fix-8 — aplicado.** Retirei de “Regras principais” as regras repetidas no “Fluxo padrão” e
   mantive ali somente as restrições que não aparecem no fluxo. Removi também a repetição de sites
   sugeridos no passo de descoberta.
   **Por quê:** cada orientação fica em um ponto, sem remover restrições únicas nem alterar o fluxo.
   **Arquivo:** `harness-conf/skills/web-research-exa-crawl4ai/SKILL.md`.
9. **E-fix-9 — não aplicado.** Não adicionei acionamento de `planning-and-task-breakdown` ao corpo de
   `devflow` nem propus remover o allow nesta construção.
   **Motivo:** qualquer opção muda o comportamento do agente ou a permissão já aprovada.
   **Arquivo não tocado:** `harness-conf/agents/devflow.md`.
   **Pergunta:** Q-Efix-9.
10. **E-fix-10 — não aplicado.** Não acrescentei instruções de carregamento de
    `writing-for-agents` aos agentes.
    **Motivo:** a instrução define novos gatilhos de ativação e altera o comportamento dos agentes.
    **Arquivos não tocados:** `harness-conf/agents/devflow.md`, `eng-software.md` e
    `smart-planner.md`.
    **Pergunta:** Q-Efix-10.
11. **E-fix-11 — aplicado.** Troquei os triggers isolados `Cenário`, `Dado que`, `Quando tento` e
    `Então` por expressões que os vinculam a Gherkin. Mantive os triggers específicos de BDD,
    Concordion e especificação executável.
    **Por quê:** etapas comuns de conversa não devem acionar a skill sem contexto de BDD.
    **Arquivo:** `harness-conf/skills/spec-executavel/SKILL.md`.
12. **E-fix-12 — não aplicado.** Não mudei a precedência entre aprovação humana e correções
    automáticas de formatação em agentes e workflows.
    **Motivo:** o achado é uma decisão de governança e afeta a autoridade humana.
    **Arquivos não tocados:** `AGENTS.md` e `harness-conf/AGENTS.base.md`.
    **Pergunta:** Q-Efix-12.
13. **E-fix-13 — não aplicado.** Não alterei a instrução sobre `writing-for-agents` nem o escopo dos
    agentes autorizados a carregar a skill.
    **Motivo:** esclarecer “seguir o método” versus “carregar a skill” define semântica de ativação e
    interação com os allows aprovados.
    **Arquivo não tocado:** `harness-conf/AGENTS.base.md`.
    **Pergunta:** Q-Efix-13.

#### Evidências de Testes — Construção E-fix

- [x] Testes novos: nenhum. As mudanças aplicadas são correções estáticas de conteúdo.
- [x] `.venv/bin/pytest tests/skills/test_web_research.py -m unit -q`: 9 passed, 1 deselected.
- [x] `.venv/bin/pytest tests/skills/test_spec_executavel.py -m all -q`: 12 passed.
- [x] Não há testes dedicados em `tests/skills/` para `documentation-and-adrs`,
  `api-and-interface-design` ou `performance-optimization`; validei esses ajustes por inspeção do
  conteúdo e das referências.
- [x] Nenhum agente, permissão, workflow ou regra compartilhada foi alterado; a guarda de
  consistência agents/workflow não se aplica.
- [x] `git diff --check` passou nos cinco arquivos de skill alterados e neste plano.
- [x] Busca de linhas acima de 120 colunas: limpa nos cinco arquivos de skill e no conteúdo
  acrescentado ao plano.
- [x] Não executei a suíte completa. Os testes novos ou existentes não foram modificados.
- [x] Gate de refatoração: os cinco ajustes aplicados não mudam escopo ou decisão arquitetural;
  itens que exigem decisão estão em `## Perguntas`.

**Documentação e arquitetura:** consultei `docs/README.md` e
`harness-conf/agents/references/principios-documentacao.md`. Não criei spec ou ADR: os cinco ajustes
aplicados corrigem conteúdo, referências e duplicações sem nova decisão arquitetural.

**Restrições:** não alterei `Status`, não toquei em `plan/insumo-devflow-spawn-dinamico.md` e não
criei commit. O relatório completo da auditoria E7 está consolidado no apêndice abaixo.

### E11 — 2026-09-27

**Executor:** `opencode/gpt-6-luna`.

**Resultado:** confirmei que o README já descreve o provisionamento ai-memory,
o plugin local gerado, a dependência Docker e a distribuição de skills do
Copilot. Acrescentei uma síntese das novas orientações do `AGENTS.base.md`:
leitura por trechos, redução de contexto e execução paralela de chamadas
independentes.

**Leitura cruzada:** `docs/workflow-agentes-dev.md` ainda contém a redação
anterior da premissa 7, enquanto `AGENTS.base.md` já não contém a regra de
precedência removida por E13. A proposta de atualização da premissa 7 segue
aguardando aprovação humana, conforme registrado em E13. Não alterei o
workflow nem o arquivo base. O teste de consistência passou, mas não decide
essa divergência de política.

**ADRs:** confirmei os ADRs 0007, 0008 e 0009 em `docs/adr/`, todos com seção
"Asserções executáveis". A convenção do repo não exige índice adicional no
README.

**Escopo delegado:** não editei `docs/README.md`. A correção da subseção ADR
continua delegada ao `curador-produto`.

#### Evidências — Construção E11

- [x] Não criei testes: a alteração é documental.
- [x] `.venv/bin/pytest tests/agents/ -m all -q`: 182 passaram.
- [x] `git diff --check -- README.md`: passou. As linhas inseridas respeitam
  o limite de 120 colunas.
- [x] Não executei a suíte completa, não alterei testes, `Status` ou
  `plan/insumo-devflow-spawn-dinamico.md`, e não criei commit.

**Gate de refatoração:** sem código ou decisão arquitetural nova. A conclusão
da checagem de sincronização da premissa 7 depende da decisão humana registrada
em `## Perguntas`.

### E11(b) — 2026-09-27

**Executor:** `opencode/gpt-6-luna`.

**Resultado:** atualizei a subseção "ADR (Arquitetura)" do `docs/README.md`.
O texto registra o retrofit dos ADRs 0001-0006 e a mesma convenção nos ADRs
0007-0009.

**Verificação do estado:** `docs/adr/` contém 9 ADRs numerados, de 0001 a
0009. Todos têm a seção "Asserções executáveis" e uma fixture Concordion com
`executarVerificacoes()` e `getVeredito()`. As seções dos nove ADRs usam as
diretivas `execute` e `assertEquals`.

**Arquivos tocados:**
- `docs/README.md`, subseção "ADR (Arquitetura)".
- `plan/otimizacao-custo-contexto.md`, este registro.

**Validação:** inspeção dos nove ADRs e das nove fixtures. Não executei testes,
pois a alteração foi documental.

**Restrições:** não alterei `Status`, não toquei em
`plan/insumo-devflow-spawn-dinamico.md` e não criei commit.

### E12 — 2026-09-27

**Estado:** suíte final verde; as duas specs em conflito com E10 foram
atualizadas com autorização do devflow. Commits do lote registrados abaixo.

**Decisões do devflow (2026-09-27):**
- A suíte pode continuar até terminar, sem limite de 30 s por intervalo. A
  regra vale para a sessão interativa; a autonomia do humano para este ciclo
  autoriza a espera contínua. O resultado esperado é 100% verde, base + testes
  novos, com 31 testes `agent_eval` deselecionados no estado normal.
- Os 25 achados do Ruff em arquivos fora do lote são dívida pré-existente.
  Não corrigir neste lote. O Ruff dos arquivos Python alterados no lote deve
  continuar limpo.
- Os dois testes em conflito codificavam o contrato antigo, suplantado pelas
  decisões humanas P1 e tudo-ou-nada. O devflow autorizou atualizar as specs,
  preservando as garantias com asserções equivalentes.

**Specs atualizadas:**
- `test_repo_state_opencode_json_matches_a_valid_provisioning_state` aceita o
  symlink para a configuração canônica ou uma cópia regular igual à canônica
  filtrada. A cópia filtrada não pode declarar `mcp.ai-memory`.
- `test_opencode_canonical_declares_ai_memory_mcp` exige que a configuração
  canônica declare somente `mcp.ai-memory`, com URL em `127.0.0.1` e formato
  remoto esperado.
- Não removi testes nem reduzi as garantias cobertas.

**Tentativa inicial:** `JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest
-m all` parou na coleta com colisão de módulo entre
`tests/bootstrap/test_detect.py` e `tests/skills_mgmt/test_detect.py`.
Renomeei o teste do lote para `tests/skills_mgmt/test_upstream_detect.py`, sem
alterar o conteúdo.

**Tentativa anterior (interrompida):** a suíte coletou 927 itens, selecionou
896 e deselecionou 31. A execução alcançou 35% antes do limite de 30 s da
ferramenta interromper o processo. A saída não registrou o resultado final.

**Análise estática:** `.venv/bin/ruff check` encontrou 25 erros em arquivos fora
do lote. A verificação de todos os arquivos Python alterados no lote passou.
`git diff --check` e `git diff --cached --check` passaram.

**Dívida pré-existente do Ruff, fora do lote:**
- `harness-conf/skills/prompt-improver/scripts/prompt_evaluator.py`: 1 F541,
  f-string sem placeholder.
- `tests/agents/test_workflow_consistency.py`: 17 F541, f-strings sem
  placeholders em mensagens de asserção.
- `tests/bootstrap/test_entrypoints.py`: 3 F401, imports não usados.
- `tests/cli/test_md_export.py`: 1 F401, import `os` não usado.
- `tests/integration/conftest.py`: 1 F841, variável `context_dir` não usada.
- `tests/lib/test_shared_lib.py`: 1 F401, import `subprocess` não usado.
- `tests/test_crawl4ai_cleanup.py`: 1 F401, import `pathlib.Path` não usado.

**Suíte completa anterior (2026-09-27):**
- Comando: `JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest -m all`.
- Coleta: 927 itens, 896 selecionados e 31 `agent_eval` deselecionados.
- Resultado: 894 passaram e 2 falharam. A execução levou 290,85 s pelo
  pytest e 4 min 52,98 s de tempo total.
- Os dois testes falharam também em execução isolada. A causa registrada e a
  decisão tomada estão em `## Perguntas`.

**Suíte completa final (2026-09-27):**
- Comando: `JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest -m all`.
- Coleta: 928 itens, 897 selecionados e 31 `agent_eval` deselecionados.
- Resultado: 897 passaram, 0 falharam. O pytest levou 197,15 s e o tempo total
  foi 199,170 s. A seleção `-m all` executou todos os 897 itens selecionados.
- Os dois testes atualizados passaram também no recorte focado: 2 passed em
  1,49 s.

**Análise estática:** os 25 achados pré-existentes do Ruff permanecem fora do
lote. `ruff check` nos arquivos Python alterados pelo lote passou. `git diff
--check` passou antes dos commits.

**Commits do lote (hash curto e mensagem):**
- E1: `ca6ade1` — `feat(skills): freeze de sincronizacao por skill no opencode-skills`.
- E2: `c702867` — `feat(skills): deteccao de mudancas de upstream no opencode-skills`.
- E2, teste do command: `05ce416` — `test(skills): guarda fluxo de decisao no command de sync upstream`.
- E2, description do CLI: `b84db42` — `fix(skills): atualiza descricao do cli de sync upstream`.
- E3: `e0321ee` — `feat(skills): registra writing-for-agents no opencode-skills`.
- E4: `f5153f1` — `test(skills): automatiza itens verificaveis do checklist pos-sync`.
- E5: `e7c4115` — `fix(copilot): description do command de otimizacao de AGENTS.md`.
- E6: `b582be8` — `feat(copilot): restringe descoberta de skills as globais`.
- E6, reflow de fixture: `d426a84` — `style(test): reflow caminho da fixture de skills Copilot`.
- E9: `38cf964` — `style(agents): reflow de linhas acima de 120 colunas`.
- E10, config canônica: `06ca1f0` — `feat(config): declara MCP do ai-memory na config canonica`.
- E10, bootstrap: `b0d2843` — `feat(bootstrap): provisiona ai-memory`.
- E10, testes OpenCode: `a81d156` — `test(bootstrap): cobre configuracao OpenCode com e sem ai-memory`.
- E13: `563dc85` — `docs(agents): reescreve compactacao e adiciona chamadas de ferramentas`.
- E14: `038f565` — `feat(copilot): bloco de referencia de skills por agente na copia`.
- E11/E11(b): `ceb5ded` — `docs(readme): atualiza contexto e status dos ADRs`.
- E-fix-5: `b26caf2` — `fix(skills): remove referencia inexistente de design de API`.
- E-fix-1: `f24815e` — `fix(skills): alinha orientacao de ADR ao repo`.
- E-fix-7: `3753ea5` — `refactor(skills): centraliza thresholds de Core Web Vitals`.
- E-fix-11: `dae3f40` — `fix(skills): restringe triggers de spec executavel`.
- E-fix-8: `66dccaf` — `refactor(skills): remove regras duplicadas de pesquisa web`.
- E7, E8 e E12 não têm commit funcional. O registro deste plano entra no
  commit documental de fechamento.

## Perguntas

Responder no fechamento do ciclo. As recomendações E-fix não bloquearam a
construção; E11(c) aguarda aprovação da premissa 7.

- **E12, continuação da suíte — RESPONDIDA (2026-09-27, decisão do devflow):**
  continuar `JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest -m all`
  até concluir, sem limite de 30 s por intervalo. Registrar duração e
  contagens finais; o estado esperado é 100% verde, base + testes novos, com
  31 `agent_eval` deselecionados. Os 25 erros Ruff em arquivos não alterados
  ficam como dívida pré-existente, sem correção neste lote.
- **E12, conflito entre testes existentes e E10 — RESPONDIDA (decisão do
  devflow, 2026-09-27):** os dois testes codificavam o contrato antigo,
  suplantado pelas decisões humanas P1 e tudo-ou-nada. Autorizada a atualização
  das specs com asserções equivalentes: o teste do estado do repo aceita o
  symlink canônico ou a cópia regular filtrada sem `mcp.ai-memory`; o teste da
  configuração canônica exige exatamente `mcp.ai-memory` em
  `127.0.0.1`. A suíte final terminou com 897 passados, 0 falhos e 31
  deselecionados.
- **Aprovação SEC→spec (achado 2 da revisão da construção) — PENDENTE DE
  DECISÃO HUMANA:** o critério de aceite de E10 exige aprovação do humano
  nas asserções executáveis de `docs/specs/Seguranca.md` (SEC-01..SEC-11,
  SEC-21). Aprovar, rejeitar ou pedir ajuste? Registrar a decisão no
  fechamento.
- **Premissa 7 do workflow, seleção de modelo por fase:** aprovar, rejeitar ou
  pedir ajuste à proposta registrada em E13 antes de atualizar
  `docs/workflow-agentes-dev.md`? A leitura cruzada da E11 encontrou a redação
  anterior no workflow e a remoção da regra de precedência em
  `harness-conf/AGENTS.base.md`.
- **Q-Efix-2:** aprovar uma regra única para timeout de inatividade/total e suas exceções em
  `reliable-async-operations`, considerando os testes que fixam a política atual?
- **Q-Efix-3:** dividir os exemplos de `reliable-async-operations` em referência externa, com os
  custos de manutenção e contexto correspondentes?
- **Q-Efix-4:** adaptar `git-workflow-and-versioning` ao padrão deste repo, generalizar os comandos
  de pre-commit e remover a recomendação de `git reset --hard HEAD`?
- **Q-Efix-6:** restringir `humanizer-br` a pedidos de reescrita e atualizar a anotação de adaptação
  no `UPSTREAM.md`, substituindo o uso registrado para toda comunicação de chat?
- **Q-Efix-9:** adicionar no corpo de `devflow` um gatilho de carregamento para
  `planning-and-task-breakdown` ou remover o allow aprovado?
- **Q-Efix-10:** registrar gatilhos de carregamento de `writing-for-agents` nos três agentes que já
  têm allow, sem mudar as permissões?
- **Q-Efix-12:** definir qual regra prevalece quando uma violação objetiva de formatação exige editar
  um agente ou workflow que também requer aprovação humana?
- **Q-Efix-13:** especificar em `AGENTS.base.md` se a regra exige carregar `writing-for-agents` ou
  aplicar seu método conhecido, e quais agentes podem receber essa instrução?
- **RM sec-2, confiança nos artefatos upstream — RESPONDIDA (2026-09-27,
  decisão humana: "usar a versão nova"):** aprovar a atualização dos pins
  para o upstream atual (wrapper `v2.4.1`, SHA-256 `49c965a...`; imagem
  `latest`, manifest `a626d11...`, linux/amd64 `5ce8700b...`), CONDICIONADA
  à revalidação de segurança do sec ANTES de fixar (análise estática do
  binário novo e das mudanças; nada executa antes do veredicto). Se a
  revalidação achar algo suspeito, parar e voltar ao humano.
- **RM sec-5, escrita concorrente no volume piloto (PENDENTE):** após o rollback, a pasta ainda existe
  com mode `0700`, mas a contagem de arquivos e o hash agregado mudaram enquanto `opencode`, `python3`,
  `git`, `docker` e shells usavam a pasta. A origem dessas escritas não foi confirmada. Identifique o
  processo escritor antes de repetir testes que mutem o volume.

### Ajustes pós-revisão — 2026-09-27

**Escopo:** resolvi os achados 1, 3 e 5 atribuídos ao `eng-software`.

- T15 guarda as âncoras aprovadas nas seções de compactação e chamadas de
  ferramentas, verifica a ausência da regra da premissa 7 e testa a
  regeneração do `AGENTS.md` global.
- Restaurei a asserção que mantém `tests/integration/config/opencode.test.json`
  sem a chave `mcp`.
- Acrescentei casos explícitos para o campo `sincronizacao` permanecer ausente
  após `sync`, `update` e `detect`, quando a skill não está congelada.
- Não alterei código de produção, as seções aprovadas, a premissa 7 ou os
  arquivos de plano fora deste escopo.

#### Evidências de Testes — Revisão da Construção

- [x] TDD: seis testes novos falharam sob mutações temporárias dos anchors,
  da configuração MCP e dos três subcomandos; removi as mutações antes da
  validação final.
- [x] Testes focados: 107 passaram nos cinco módulos tocados e na guarda T14.
- [x] Ruff nos cinco arquivos Python alterados: o arquivo
  `test_workflow_consistency.py` mantém 17 achados F541 anteriores; a mesma
  lista ocorre em `HEAD`. Os demais arquivos e as linhas novas não têm
  achados. Não alterei testes existentes para remover essa dívida.
- [x] `git diff --check`: passou.
- [x] Regressão incremental: executei as guardas sob mutações e repeti os
  módulos após restaurar os dados e o código.
- [x] Gate de refatoração: sem mudança no plano aprovado. Os ajustes só
  acrescentam as guardas pedidas nos achados 1, 3 e 5.
- [x] Não executei a suíte completa e não alterei `Status`.

**Commit:** `test(repo): restaura guardas contra regressões` (sem push).

## Ciclo 2 — CONSTRUÇÃO — Apêndice: auditoria E7

### Auditoria E7, 2026-09-27

#### Escopo e método

Auditoria focalizada do ciclo 1, sem alterações de código e sem ampliar a amostra definida pela P2.
O relatório cobre as três frentes E7: permissions, regras de agentes e amostra de skills.

Li integralmente `AGENTS.md` e `harness-conf/AGENTS.base.md`. Comparei os 14 frontmatters de agente
com o mapa v4, li as menções às skills nos corpos dos agentes e consultei `docs/README.md` e
`harness-conf/agents/references/principios-documentacao.md`.

Li integralmente as 16 skills da amostra, seus frontmatters e os `UPSTREAM.md` associados. Também
conferi a existência dos arquivos sincronizados declarados nos metadados selecionados. A seleção
estratificada é reproduzível: ordenei alfabeticamente os grupos candidatos, usei
`random.Random(20260927)`, amostrei quatro upstream e depois quatro locais.

- Core integral: `code-explorer-priority`, `git-workflow-and-versioning`, `humanizer-br`,
  `planning-and-task-breakdown`, `portugues-tecnico-controlado`, `question-orchestration` e
  `reliable-async-operations`.
- Candidatas de domínio com `UPSTREAM.md` (12): `accessibility-audit`, `api-and-interface-design`,
  `code-review-and-quality`, `code-simplification`, `debugging-and-error-recovery`,
  `documentation-and-adrs`, `frontend-ui-engineering`, `performance-optimization`, `prompt-improver`,
  `security-and-hardening`, `spec-driven-development` e `test-driven-development`.
- Candidatas locais de domínio (13): `aws-add-account-sso`, `aws-sso-login`, `browser-testing`,
  `clean-code`, `data-modeling`, `doc-extract`, `md-export`, `spec-executavel`, `svg-to-image`,
  `testes-produto-catalog`, `tests-as-spec`, `tls-certificate-recovery` e
  `web-research-exa-crawl4ai`.
- Amostra sorteada: upstream `api-and-interface-design`, `code-simplification`,
  `documentation-and-adrs` e `performance-optimization`; locais `aws-sso-login`, `md-export`,
  `spec-executavel` e `web-research-exa-crawl4ai`.
- Completa a amostra `writing-for-agents`.

A avaliação de no-op foi estática. Não executei as skills em um modelo, pois o critério de no-op da
referência é relativo ao comportamento do modelo. O diretório temporário `/tmp/opencode/fase2/`,
citado nos registros anteriores, não existe neste ambiente.

#### (a) Permissions contra uso nos agentes

O mapa atual contém 21 denies nominais e `aws-*`, que cobre as duas skills AWS, totalizando as 23
skills negadas da P2. As 10 skills globais completam o inventário de 33. Os frontmatters contêm
69 allows em 11 agentes, iguais ao mapa v4 aprovado.

Não encontrei skill negada sem allow, allow para skill inexistente nem menção operacional de skill
negada sem allow no corpo do agente consumidor. As menções de skills em `devflow.md` nas linhas
240-242 atribuem o carregamento ao agente `rev`, que tem os allows correspondentes. O `aws-*` de
`aws-analista` é a exceção já documentada no mapa v4. `code-explorer-priority` não aparece nos
corpos locais de seis agentes, mas `AGENTS.base.md` a exige para os oito agentes do workflow.

Dois grupos de allows não têm acionamento explícito nos corpos locais:

- `devflow -> planning-and-task-breakdown`: o nome aparece só no frontmatter do `devflow.md`; o
  corpo e `AGENTS.base.md` não descrevem seu carregamento.
- `writing-for-agents` aparece como allow em `devflow`, `eng-software` e `smart-planner`, sem
  acionamento nos corpos locais. `AGENTS.base.md` cita o método para criação ou revisão de skills,
  mas não define a ativação da skill nesses três agentes. O allow corresponde à decisão humana que
  disponibilizou a skill a esses agentes, então a auditoria não propõe alterá-la.
- A mesma regra de `AGENTS.base.md` instrui todos os agentes a seguir o método de
  `writing-for-agents`, mas o deny global só libera o uso a três agentes. A regra pode indicar um
  método sem carregar a skill; a intenção não fica explícita.

#### (b) Regras do repo

Li os dois arquivos completos. Encontrei um conflito de precedência: `AGENTS.md` diz que toda
alteração em workflow ou agente exige aprovação humana, sem exceção. `AGENTS.base.md` manda corrigir
imediatamente violações objetivas de formatação, largura ou estilo. Uma correção em arquivo de
agente pode cair nas duas regras. Não encontrei conflito nas regras de upstream, proteção da
worktree ou autoridade humana fora desse caso. Os outros achados vêm de skills amostradas que
contradizem formatos canônicos do repo ou desperdiçam contexto.

#### (c) Skills amostradas

As descrições cobrem o assunto dos corpos e contêm triggers correspondentes, com três ressalvas
registradas nos E-fix: ponteiro quebrado em `api-and-interface-design`, contrato de saída amplo em
`humanizer-br` e triggers genéricos em `spec-executavel`.

Os oito `UPSTREAM.md` da amostra estão presentes. Os arquivos declarados como sincronizados existem:
`SKILL-MECHANICS.md`, três referências de `portugues-tecnico-controlado`,
`references/aprofundador.md`, `LICENSE` de `humanizer-br` e `performance-checklist.md`. Os metadados
dos quatro itens amostrados de Addy Osmani descrevem o corpo local como cópia inicial e não
sincronizada. Não validei o SHA contra a rede nem o estado atual dos upstreams.

Quatorze das 16 skills têm mais de aproximadamente 100 linhas. A extensão, isoladamente, não
justifica split. `portugues-tecnico-controlado` já desloca léxico, ortografia e inglês para
referências; `writing-for-agents` separa mecânica de skills; `performance-optimization` tem
checklist externo. `reliable-async-operations` contém seis categorias independentes e 322 linhas,
com exemplos em Python, Node.js, Bash, PowerShell, Java e Groovy, por isso há ganho claro em mover
os exemplos para referência.

Os demais corpos acima do limiar formam uma sequência ou referência coesa; não recomendo split
automático sem uma branch de invocação comprovada.

| Skill | Linhas | Resultado da inspeção focalizada |
|---|---:|---|
| `code-explorer-priority` | 119 | Descrição e fluxo correspondem; procedimento único, sem split indicado. |
| `git-workflow-and-versioning` | 214 | Acionamento amplo; convenção e recuperação conflitam com o repo. |
| `humanizer-br` | 217 | Description aplica-se a todo chat; saída fixa pode duplicar a resposta. |
| `planning-and-task-breakdown` | 183 | Description, tarefas e sequência correspondem; sem split indicado. |
| `portugues-tecnico-controlado` | 425 | Acionamento corresponde; três referências já isolam ramos específicos. |
| `question-orchestration` | 104 | Modos direto e mediado correspondem aos triggers; protocolo coeso. |
| `reliable-async-operations` | 322 | Acionamento corresponde; contrato de timeout contraditório e branches grandes. |
| `api-and-interface-design` | 188 | Triggers correspondem; link para skill inexistente. |
| `code-simplification` | 171 | Triggers e processo correspondem; sequência coesa. |
| `documentation-and-adrs` | 149 | Triggers correspondem; diretório e template ADR divergem do repo. |
| `performance-optimization` | 188 | Triggers correspondem; Core Web Vitals repetidos na referência. |
| `aws-sso-login` | 35 | Triggers correspondem ao fluxo de validação e renovação SSO. |
| `md-export` | 84 | Triggers correspondem ao contrato JSON e aos formatos suportados. |
| `spec-executavel` | 117 | Corpo corresponde; `Cenário` e `Então` são triggers genéricos. |
| `web-research-exa-crawl4ai` | 151 | Description cobre os ramos; regras e fluxo repetem instruções. |
| `writing-for-agents` | 162 | Description e corpo inglês correspondem; mecânica está separada. |

#### Achados convertidos em E-fix

Prioridades abaixo são sugestões para o humano, não aprovação de execução neste ciclo. Todas as
tasks dependem de E7.

1. **E-fix-1, P1 sugerida, escopo S:** atualizar `documentation-and-adrs/SKILL.md`. A seção ADR
   manda gravar em `docs/decisions/` e mostra um template sem asserção executável. O repo exige
   `docs/adr/` e asserção executável em todo ADR novo (`docs/README.md`, linhas 101-112).
2. **E-fix-2, P1 sugerida, escopo S:** resolver as contradições de timeout em
   `reliable-async-operations/SKILL.md`. O contrato de revisão exige timeout de inatividade e total
   para qualquer operação (linhas 312-317), enquanto as regras anteriores admitem callbacks,
   eventos e polling sem timeout. Exemplos fixam valores genéricos sem justificativa, embora a
   seção central proíba timeouts chutados.
3. **E-fix-3, P2 sugerida, escopo S:** separar os exemplos das seis categorias de
   `reliable-async-operations` em uma referência, mantendo no corpo as regras gerais e o ponteiro
   por categoria.
4. **E-fix-4, P1 sugerida, escopo S:** alinhar `git-workflow-and-versioning/SKILL.md` ao padrão
   local `tipo(escopo): descrição`, substituir comandos pre-commit de Node por uma regra dependente
   do projeto e não recomendar `git reset --hard HEAD` sem proteger mudanças locais. O formato
   atual conflita com `AGENTS.md`, e o reset pode apagar trabalho não commitado.
5. **E-fix-5, P2 sugerida, escopo S:** corrigir o ponteiro `deprecation-and-migration` em
   `api-and-interface-design/SKILL.md`, pois nenhuma skill ou referência com esse nome existe.
6. **E-fix-6, P2 sugerida, escopo S:** delimitar `humanizer-br` a tarefas de reescrita e restringir
   o formato de quatro partes a essas tarefas. A description aciona a skill em toda comunicação,
   enquanto o corpo manda sempre emitir versões, auditoria e resumo.
7. **E-fix-7, P2 sugerida, escopo S:** remover a duplicação dos thresholds de Core Web Vitals entre
   `performance-optimization/SKILL.md` e `references/performance-checklist.md`, ou definir uma
   fonte única.
8. **E-fix-8, P2 sugerida, escopo S:** consolidar as regras repetidas entre “Regras principais” e
   “Fluxo padrão” em `web-research-exa-crawl4ai/SKILL.md`; manter cada regra em um único ponto.
9. **E-fix-9, P2 sugerida, escopo S:** resolver o allow sem acionamento de
   `planning-and-task-breakdown` em `devflow.md`, adicionando condição explícita ou propondo a
   remoção do allow ao humano.
10. **E-fix-10, P2 sugerida, escopo S:** explicitar nos corpos de `devflow`, `eng-software` e
    `smart-planner` quando carregar `writing-for-agents`, sem alterar a permissão aprovada sem
    decisão humana.
11. **E-fix-11, P2 sugerida, escopo S:** restringir triggers genéricos como `Cenário` e `Então` em
    `spec-executavel/SKILL.md` a menções de especificação executável ou BDD.
12. **E-fix-12, P2 sugerida, escopo S:** resolver a precedência entre aprovação humana obrigatória
    para mudanças em agentes/workflows e correção imediata de violações objetivas em
    `AGENTS.md`/`AGENTS.base.md`, sem enfraquecer a autoridade humana.
13. **E-fix-13, P2 sugerida, escopo S:** esclarecer em `AGENTS.base.md` se a regra sobre
    `writing-for-agents` manda carregar a skill ou seguir o método já conhecido, e restringir a
    instrução ao escopo compatível com os allows aprovados.

#### Validação

- `.venv/bin/pytest tests/agents/ -m all -q`: 182 passed em 4,90 s.
- Não rodei a suíte completa. Não alterei código, `Status` ou
  `plan/insumo-devflow-spawn-dinamico.md`. Não criei commit.

## Ciclo 2 — REVISÃO DA CONSTRUÇÃO

Revisão integrativa (rev, 2026-09-27, instância limpa, modelo
zai-coding-plan/glm-5.3). Objeto: o LOTE commitado do ciclo, delimitado por
`git diff 098a5b6..33f96eb` (base = commit anterior a `ca6ade1`; fechamento
`33f96eb`), excluídos os planos paralelos citados no escopo. Insumos: plano
aprovado (decisões P1-P5, S1/S2, Q1/Q2; tasks E1-E14 + E-fix; exigências
SEC-01..SEC-21; testes T1-T15, lacunas L1-L5, CA-T1..CA-T8) e os blocos
`## Ciclo 2 — CONSTRUÇÃO`. Verificações executadas: leitura do plano por
trechos; diffs agregados e por commit (`git show`/`git diff --stat`); leitura
de código (`src/opencode_config/bootstrap/ai_memory.py`,
`cli/skills_sync.py`, `harnesses/copilot.py`, `harnesses/opencode.py`) e dos
testes novos; coleta da suíte (`pytest --collect-only -m all`), sem execução
da suíte completa (evidência E12 aceita como insumo).

### Achados

Resumo `achado · ação · severidade`; evidências por achado abaixo.

| # | Achado | Ação | Severidade |
|---|--------|------|------------|
| 1 | T15/L4 ausente: sem guarda das seções aprovadas | `eng-software` criar T15 antes da fase Testes | alto |
| 2 | Aprovação SEC→spec fora das pendências de fechamento | `devflow` incluir nas perguntas do fechamento | médio |
| 3 | Guarda da config de integração perdida em E12 | `eng-software` restaurar asserção | baixo |
| 4 | 2 commits do intervalo do lote sem registro no plano | `devflow` registrar como fluxo paralelo | baixo |
| 5 | Negativo do campo freeze por subcomando incompleto | `eng-software` completar com T15 | baixo |
| 6 | Import cruzado harnesses→bootstrap (fronteira de módulo) | Movimento para `lib/` em ciclo futuro | baixo |
| 7 | Ambiguidade de executor em E11(b) (modelo vs agente) | Registrar agente executor em ciclos futuros | baixo |

**1 (alto) · Lacuna T15/L4 · ação: delegar a `eng-software` · evidência:**
o plano de testes exige âncoras das seções aprovadas (frases-chave de
"Compactação de contexto" e "Chamadas de ferramentas" no
`harness-conf/AGENTS.base.md`, ausência da regra de precedência da premissa
7, regeneração do AGENTS.md global com as seções) em
`tests/agents/test_workflow_consistency.py` +
`tests/harnesses/test_opencode.py`. Grep em `tests/` não encontra guarda
para "rede de segurança"/"fronteira foi perdida"/"dependência real"; nenhum
commit do lote toca `test_workflow_consistency.py`. O próprio E11 registra
que o teste de consistência "não decide essa divergência". Sem a guarda, um
rollback silencioso do texto aprovado na P5 não falha suíte; CA-T6 exige
T1-T15 presentes.

**2 (médio) · Pendência de aprovação SEC→spec · ação: `devflow` · evidência:**
critério de aceite de E10 exige "aprovação do humano na revisão" das
asserções de `docs/specs/Seguranca.md`; o bloco E10 registra a pendência,
mas nem o `Status` nem `## Perguntas` a incluem (citam premissa 7 e Q-Efix
apenas). Risco de o critério passar batido no fechamento.

**3 (baixo) · Redução de guarda não declarada em E12 · ação:
`eng-software` · evidência:** o teste atualizado
`test_opencode_canonical_declares_ai_memory_mcp`
(`tests/test_mcp_wrapper_cleanup.py:8`) cobre só
`harness-conf/opencode.json`; o antigo
`test_opencode_configs_have_no_mcp_block` verificava também
`tests/integration/config/opencode.test.json`. A garantia "config de
integração sem MCP" ficou sem guarda; o arquivo segue sem MCP (sem dano
imediato). A frase do E12 "não reduzi as garantias cobertas" é imprecisa
nesse ponto.

**4 (baixo) · Commits do intervalo sem registro · ação: `devflow` ·
evidência:** `0698b1b` e `8852809` criam/editam
`plan/plano-revisao-comunicacao-planejamento-agentes.md`, não constam da
lista de commits do E12 nem de qualquer seção do ciclo. Dilui a fronteira
auditável do lote (trabalho paralelo do humano/devflow sobre comunicação).

**5 (baixo) · Negativo do campo freeze incompleto (T1) · ação:
`eng-software` · evidência:** o mapa do qa pedia "teste negativo por
subcomando (sync, update, list e detecção): caso skill não-congelada
continua sem o campo após cada comando". Existe para list
(`test_list_marks_frozen_skills_without_changing_metadata`) e para
regeneração; falta caso análogo para sync/update/detect.

**6 (baixo) · Fronteira de módulo · ação: backlog · evidência:**
`src/opencode_config/harnesses/opencode.py` importa
`opencode_config.bootstrap.ai_memory` (`filter_ai_memory_config`,
`is_ai_memory_provisioned`). A regra do repo coloca utilitários
compartilhados em `src/opencode_config/lib/`; o adapter (harnesses) passa a
depender do módulo de provisionamento (bootstrap). Sem ciclo de import;
funcionalmente correto.

**7 (baixo) · Ambiguidade de executor em E11(b) · ação: registro futuro ·
evidência:** a delegação aprovada atribuía a edição do `docs/README.md` ao
`curador-produto`, e o `Status` afirma "E11(b) pelo curador-produto", mas o
registro da subseção usa o mesmo campo "Executor: opencode/gpt-6-luna" das
tasks do eng-software (o campo registra o modelo, não o agente). A trilha
não distingue qual agente executou.

### Especificações de teste alteradas na construção (conferência de
### equivalência)

Mudanças de spec autorizadas e conferidas contra as garantias anteriores:

- `test_repo_state_opencode_json_symlink_points_to_repo` →
  `test_repo_state_opencode_json_matches_a_valid_provisioning_state`
  (`tests/scripts/bootstrap_repo/test_repo_state.py:153`): preserva a garantia
  do symlink canônico no caminho provisionado e acrescenta a garantia
  tudo-ou-nada (cópia filtrada igual ao canônico sem `mcp.ai-memory`).
  Autorizada pelo devflow (E12). Equivalente e mais forte. OK.
- `test_opencode_configs_have_no_mcp_block` →
  `test_opencode_canonical_declares_ai_memory_mcp`: contrato P1 suplanta o
  antigo; exige exatamente `ai-memory` em `127.0.0.1:49374/mcp`. Perda parcial
  registrada como achado 3.
- `test_render_adr_specs_task_derives_exactly_the_six_adr_specs` →
  `test_render_adr_specs_task_derives_every_numbered_adr_spec` e
  `test_build_includes_adr_fixtures_in_the_specialty_suite` →
  `test_build_registers_each_adr_fixture_in_one_specialty_suite`
  (`tests/product_tests/test_concordion_spec_infra.py`): generalização
  autorizada pelo devflow (E2); deriva ADRs de `docs/adr/` e fortalece a
  guarda (fixture registrada exatamente 1 vez no `build.gradle`). OK.
- E6, quatro testes atualizados: o diff agregado do lote em
  `tests/harnesses/test_copilot.py` remove só 2 linhas de path de fixture;
  nenhuma asserção removida. Garantias reexpressas nos destinos P4. OK.

### Verificações de convenção

- Largura ≤120 colunas: varredura `awk length > 120` em todos os arquivos de
  código, teste, ADR, spec e config do lote: 0 violações. T14
  (`tests/agents/test_line_width.py`) vigente e no lote.
- `skip`: nenhum `pytest.mark.skip`/`pytest.skip` novo no lote; único
  `skipif` em `tests/skills_mgmt/test_sync.py:151` é pré-existente e de
  plataforma (bash). Nomes contendo "skip" referem comportamento de pular
  skill congelada, não skipping de teste.
- Markers (ADR-0005): `test_upstream_detect.py` integration (T2-T4, git
  local, conforme plano); `test_line_width.py`, `test_sync_upstream_command.py`,
  `test_ai_memory_provision.py`, `test_mcp_wrapper_cleanup.py` unit; sem
  marcador inválido.
- Conventional Commits PT-BR: 21 commits funcionais + fechamento conferidos;
  tipos usados (feat/fix/docs/style/refactor/test) todos da taxonomia do
  repo; mensagens curtas sem filler; sem push (confirmado pelo humano no
  Status).
- Evidência E12 re-verificada por coleta: `pytest --collect-only -m all`
  reporta 897/928 coletados, 31 deselected — bate com o registro
  928/897/31 e com os artefatos (renomeação de `test_upstream_detect.py`
  resolve a colisão com `tests/bootstrap/test_detect.py` pré-existente).

### Checklist por task (conforme o plano)

- E1 freeze: OK. Campo lido/preservado em `_write_upstream`; sync/update
  pulam com status; list marca; regra documentada no AGENTS.md; T1 presente
  (4 testes). Achado 5 cobre o negativo restante.
- E2 detecção: OK. `detect` read-only, clone em tempdir fora do repo com
  guarda anti-dentro, `--no-recurse-submodules`, `--no-ext-diff`,
  fallback `--unshallow` (L1), SHA inválido com erro acionável, aviso NÃO
  CONFIÁVEL por skill (SEC-14), repetição pós-recusa; comando
  `sync-upstream-skills.md` reescrito para o fluxo P3; ADR-0007 + fixture +
  registro no build.gradle; T2-T4 presentes.
- E3 writing-for-agents: OK. `SPECS` + `_sync_writing_for_agents`;
  `## Notas locais` preservada; extra_fields `description_lang`/`description_note`
  no UPSTREAM.md; tabela do AGENTS.md com a linha nova; T5/T6 presentes (L2).
- E4 checklist pós-sync: OK. Guarda de SHA novo e arquivos declarados
  (fixture 2 commits); checklist do AGENTS.md separa automático/manual com
  revisão de segurança explícita (SEC-14/15); T7 presente.
- E5 description do command: OK. `_COMMAND_DESCRIPTIONS` com entrada
  específica; T8 trava description e ausência do fallback genérico.
- E6 poda Copilot: OK. Derivação do mapa `permission.skill` com wildcard;
  10 globais em descoberta, 23 em `~/.copilot/referencias/skills/`; backup e
  remoção de cópia legada; T9 com guarda de soma/partição/derivação (10/23
  travados); README Adapters atualizado.
- E7 auditoria: OK. Sem código; amostra 16 da P2 mantida; método e seed
  declarados; 13 E-fix registrados; apêndice autocontido no plano.
- E8 JAVA_HOME: OK. Causa raiz ambiente; correção no `~/.bashrc` (bloco
  gerenciado); teste intocado (12 passed); sem commit, conforme plano.
- E9 reflow: OK. 31 linhas em 8 arquivos; T14 criado antes (RED com 31
  violações); suíte `tests/agents/` verde.
- E10 ai-memory: OK no desenho de segurança. URL HTTPS fixa + SHA-256
  constante do wrapper (SEC-01/02); `docker run` com bind
  `127.0.0.1:49374:49374` (SEC-03) e rede `--internal` (SEC-21); porta
  ocupada aborta com instrução (SEC-04); drift do plugin avisa (SEC-05);
  idempotência sem re-download e hash divergente bloqueia com caminho de
  upgrade (SEC-06); volume 0700 POSIX e tratado como sensível no README
  (SEC-07); rollback preserva volume e remove declarações (SEC-08); Docker
  ausente desativa marcador/MCP nos dois harnesses com instrução sem sudo
  (SEC-09); merge Copilot aditivo com backup e colisão bloqueando (SEC-10);
  canônica sem credenciais (SEC-11, T12); tudo-ou-nada via marcador
  `.bootstrap-provisioned` + cópia filtrada sem escrever através do symlink;
  T13 hermético (fakes + guarda autouse em `subprocess.Popen`); timeouts
  separados total/idle (1800s/120s) no streaming; `docs/specs/Seguranca.md`
  com SEC-01..11 e SEC-21 (aprovação pendente, achado 2); ADR-0008 +
  fixture + build.gradle; README com provisionamento e rollback.
- E11 docs: OK. README atualizado; leitura cruzada registrou a divergência da
  premissa 7 (decisão humana pendente, conforme planejado); ADRs 0007-0009
  confirmados com "Asserções executáveis".
- E11(b): edit applied no `docs/README.md` (retrofit em tempo passado +
  convenção 0007-0009); restrição "E10 não edita docs/README.md" respeitada
  (edição veio por delegação); ver achado 7 sobre rastreabilidade de executor.
- E12 gate: OK. Renomeação por colisão de módulo registrada; suíte final
  897/0/31 coerente com coleta re-verificada; dívida ruff delimitada fora do
  lote (25 achados listados); commits do lote listados (achado 4 sobre os 2
  commits paralelos).
- E13 seções aprovadas: OK. Diff confere texto verbatim da P5 (só reflow de
  largura); regra de precedência da premissa 7 removida; proposta de redação
  da premissa 7 registrada e aguardando humano, sem toque no workflow;
  largura limpa. Falta a guarda T15 (achado 1).
- E14 bloco de referência: OK. Bloco só na cópia, com marcadores próprios;
  description completa (inclui YAML folded `>`); caminho absoluto na pasta
  auxiliar; sem allow não recebe bloco (L5); fonte limpa; marcador externo
  ausente (SEC-16); tmp_path com espaço (SEC-17); ADR-0009 + fixture +
  build.gradle + diagramas.
- E-fix: 5 aplicados (1, 5, 7, 8, 11) como correções objetivas de conteúdo,
  um por vez, sem teste novo (conteúdo estático, fora do critério TDD de
  comportamento); 8 convertidos em Q-Efix para decisão humana; escopo
  respeitado (nenhum agente/permissão/workflow alterado).

### Veredicto

[ ] Aprovado sem ressalvas
[x] Aprovado com melhorias opcionais — resolver achado 1 (alto) e achado 2
    (médio) antes do fechamento do ciclo; demais baixos podem virar backlog
[ ] Bloqueado — resolver achados bloqueantes antes de prosseguir

### Disposição dos achados (2026-09-27, devflow)

- **Achado 1 (alto):** corrigido pelo eng-software. T15 criado com âncoras
  das seções aprovadas; mutações temporárias derrubaram 6 testes
  (validação da guarda); commit `97a4e4b`.
- **Achado 2 (médio):** registrado pelo devflow. Pendência
  "Aprovação SEC→spec" adicionada a `## Perguntas` e ao `Status`.
- **Achado 3 (baixo):** corrigido pelo eng-software. Asserção da config
  de integração sem MCP restaurada no `test_mcp_wrapper_cleanup.py`
  (commit `97a4e4b`).
- **Achado 4 (baixo):** registrado pelo devflow. `0698b1b` e `8852809`
  tocam `plan/plano-revisao-comunicacao-planejamento-agentes.md`:
  fluxo paralelo do humano (comunicação de planejamento), FORA do lote
  deste ciclo por decisão de escopo; fronteira do lote permanece
  auditável pelos commits listados no E12 + `97a4e4b`.
- **Achado 5 (baixo):** corrigido pelo eng-software. Negativo do freeze
  por subcomando (sync/update/detect) completo (commit `97a4e4b`).
- **Achado 6 (baixo):** dívida de ciclo futuro. Import
  harnesses→bootstrap (`filter_ai_memory_config`,
  `is_ai_memory_provisioned`) a mover para `lib/`.
- **Achado 7 (baixo):** nota de processo para ciclos futuros. O campo
  "Executor" das subseções do plano deve registrar AGENTE executor e
  modelo (ex.: `curador-produto / opencode/gpt-6-luna`), não só o modelo.

### Evidências (rev)

- [x] Artefato lido: `plan/otimizacao-custo-contexto.md` (completo, por
      trechos: Status; plano aprovado E1-E14/E-fix, sec, qa; blocos de
      construção; Perguntas; apêndice E7)
- [x] Lote inspecionado: `git diff 098a5b6..33f96eb` (51 arquivos,
      +6.734/-280) e `git show` dos 23 commits do intervalo
- [x] Plano aprovado consultado: sim (P1-P5, S1/S2, Q1/Q2, T1-T15, L1-L5,
      SEC-01..SEC-21, CA-T1..CA-T8)
- [x] Checklist integrativo: 8 dimensões (BD N/A — sem modelagem no ciclo;
      segurança↔implementação; cobertura↔requisitos; docs↔docs/README.md;
      spec↔docs/README.md; UI N/A; aderência ao plano; contradições/lacunas)
- [x] Achados encontrados: 7 (0 críticos, 1 alto, 1 médio, 5 baixos)
- [x] Coleta da suíte re-verificada sem execução: 897/928, 31 deselected
      (confere com a evidência do E12)
- [x] Skills de domínio carregadas: code-review-and-quality (obrigatória),
      tests-as-spec, documentation-and-adrs, api-and-interface-design,
      security-and-hardening (E10)

## Otimizações de processo aprovadas (2026-09-27, humano)

Aplicáveis a este ciclo:
- ~~sec (6.2) roda em paralelo (`background`) com o restante da fase
  Testes, restrito a verificações read-only na máquina.~~ REVERTIDA
  (2026-09-27): task `background` neste ambiente entrega tools restritas
  (sem bash/edit — o sec tem ambas no frontmatter, mas não as recebeu);
  o roteiro manual exige shell e mutação de estado. sec volta ao serial
  (foreground). Lição para o próximo ciclo: paralelização via background
  só para trabalho puramente analítico/leitura.
- Diagnóstico obrigatório da flakiness (16 errors da primeira execução
  do agregador pelo qa) antes da validação da evidência pelo
  curador-produto.

Para os próximos ciclos:
- Subseções compactas por task no plano (registro enxuto, não narrativa
  completa).
- `reasoning` default do executor em tarefas mecânicas (roteiros, docs);
  `high` reservado a análise/projeto.
- Rodada única de perguntas no fechamento (blocos adaptativos):
  premissa 7, aprovação SEC→spec e Q-Efix numa só apresentação.
- Diretriz humana (2026-09-27), vale JÁ neste ciclo: retomadas de
  subagente usam INSTÂNCIA NOVA (nunca reutilizar sessão/task da
  chamada anterior); o briefing autocontido aponta os blocos exatos do
  plano a ler. Evita reenviar o histórico acumulado da sessão do
  subagente.

### Re-verificação (2026-09-27)

Rev (instância limpa, zai-coding-plan/glm-5.3), a pedido do devflow. Escopo:
resolução dos achados 1/3/5 (commit `97a4e4b`) e registros da disposição 2/4;
sem re-execução da revisão integral e sem suíte completa.

**Veredicto final: APROVADO.**

- Achado 1 (T15): resolvido. Mapa T15 confere; implementado como
  `test_approved_agents_base_sections_keep_their_anchors`
  (`tests/agents/test_workflow_consistency.py`: âncoras "rede de
  segurança"/"fronteira foi perdida" na seção "Compactação de contexto",
  "dependência real" em "Chamadas de ferramentas", "premissa 7" ausente via
  casefold) e `test_opencode_materializes_approved_sections_in_global_agents_md`
  (`tests/harnesses/test_opencode.py`: AGENTS.md global regenerado pelo
  adapter contém as seções e âncoras). Módulos verdes: 41 passed.
- Achado 3: resolvido. `test_opencode_integration_config_does_not_declare_mcp`
  restaura a asserção de `tests/integration/config/opencode.test.json` sem
  `mcp`. Módulo verde: 7 passed.
- Achado 5: resolvido. Negativos dedicados do freeze para skill não-congelada
  após `sync` e `update` (`tests/skills_mgmt/test_sync.py`) e `detect`
  (`tests/skills_mgmt/test_upstream_detect.py`, também compara bytes
  inalterados); com o caso `list` pré-existente, o mapa por subcomando fica
  completo. Módulos verdes: 58 passed.
- Commit `97a4e4b` (= HEAD): diff limitado aos três ajustes + registro
  "Ajustes pós-revisão" no plano; 6 testes novos (bate com a disposição);
  sem código de produção alterado; mensagem Conventional Commits PT-BR
  (`test(repo): restaura guardas contra regressões`); 0 linhas >120 colunas
  nos 5 arquivos de teste e nas linhas adicionadas.
- Disposição 2: registrada. Entrada "Aprovação SEC→spec (achado 2 da revisão
  da construção) — PENDENTE DE DECISÃO HUMANA" em `## Perguntas` e citação
  no `Status` (pendências do fechamento).
- Disposição 4: registrada. `### Disposição dos achados` documenta
  `0698b1b`/`8852809` como fluxo paralelo do humano, fora do lote.
- Observação (informativa): a seção de revisão + disposição constam apenas do
  working tree (não commitadas); consistente com o fluxo do ciclo, que
  commita o plano no fechamento.

Execução de testes (rev): 106 passed nos cinco módulos tocados
(`test_workflow_consistency.py` + `test_opencode.py`: 41;
`test_mcp_wrapper_cleanup.py`: 7; `test_sync.py` + `test_upstream_detect.py`:
58), 0 falhas; coerente com as 107 do registro do eng-software (que inclui a
guarda T14). Achados da re-verificação: 0 bloqueantes, 0 melhorias.

## Ciclo 2 — TESTES

### TESTES — qa — 2026-09-27

#### Suítes automatizadas

- A primeira tentativa do comando `JAVA_HOME=/home/vitor/.local/share/jdk
  testes-produto` falhou com `/bin/bash: line 1: testes-produto: command not
  found`. `testes-produto/README.md` orienta executar `python testes-produto`
  no checkout. Usei `.venv/bin/python testes-produto` nas execuções seguintes.
- Agregador #1: `JAVA_HOME=/home/vitor/.local/share/jdk
  .venv/bin/python testes-produto` retornou `status=fail`. O finding bloqueante
  resumiu 887 passed, 31 deselected e 16 errors em 260,02 s. Os 16 errors
  vieram de `tests/scripts/bootstrap_repo/test_repo_state.py`.
- Agregador #2 retornou `{"status":"pass","findings":[]}`. O agregador não
  informou contagens nem duração.
- Agregador #3 reproduziu o mesmo finding: 887 passed, 31 deselected e 16
  errors em 236,37 s, no mesmo arquivo.
- Agregador #4, após isolamento pontual, retornou
  `{"status":"pass","findings":[]}`. Esta foi a execução final válida do
  agregador. O agregador não informou contagens nem duração.
- Isolamento após os erros: `JAVA_HOME=/home/vitor/.local/share/jdk
  .venv/bin/pytest -m all tests/scripts/bootstrap_repo/test_repo_state.py -vv`
  passou 16 testes em 2,03 s e, na segunda reprodução, 16 em 4,10 s. A primeira
  execução isolada passou 16 testes em 2,56 s.
- Diagnóstico da flakiness: os 16 testes dependem da fixture de módulo
  `bootstrapped_repo_state`, que inicia o adapter em subprocesso. A execução
  agregada falhou duas vezes, mas três execuções isoladas e duas suítes
  completas diretas passaram. O agregador não expôs traceback nem stderr do
  subprocesso. Causa raiz não confirmada. A hipótese mais fundamentada é falha
  transitória do subprocesso da fixture no contexto da suíte completa, por
  ordem ou estado compartilhado; não há evidência de paralelismo xdist.
- Detecção precoce no próximo ciclo: após qualquer erro agregado desse arquivo,
  executar imediatamente o comando isolado acima com `-vv` e preservar o output
  completo. O resumo do agregador não basta para identificar o erro de setup.
- Suíte completa, primeira execução direta: `JAVA_HOME=/home/vitor/.local/share/jdk
  .venv/bin/pytest -m all` terminou com 903 passed e 31 deselected em 213,08 s.
  A execução direta final terminou com 903 passed e 31 deselected em 232,46 s.
  Cada execução coletou 934 itens; `agent_eval` ficou fora da seleção. A spec
  Concordion `tests/product_tests/test_concordion_spec_infra.py` passou.
- Cobertura do relatório `.coverage`: 85%. O gate de 70% foi atendido. O plano
  não registra uma cobertura baseline numérica, então o delta não é calculável.
- Diff `git diff 098a5b6..HEAD -- testes-produto/`: sem alterações em
  scripts de suíte ou agregador. A suíte meta `testes-produto/tests/` não se
  aplica e não foi executada.

#### Resultado dos critérios CA-T

| Critério | Resultado | Evidência |
|---|---|---|
| CA-T1 | PASS após `d646b41` | Agregador final retornou `pass` e `findings=[]`. |
| CA-T2 | PASS | 904 passed, 0 falhas, 31 deselected em `-m all`. |
| CA-T3 | PASS | Spec Concordion passou na suíte completa. |
| CA-T4 | PARCIAL | Cobertura 85%, acima de 70%; baseline numérica ausente. |
| CA-T5 | BLOQUEADO | RM-2, RM-5, RM-6 e RM-10 falharam; volume preservado. |
| CA-T6 | PASS | Suíte completa passou, incluindo T1-T15 e os testes de `d646b41`. |
| CA-T7 | PASS | Nenhuma mudança nos scripts do agregador; meta não aplicável. |
| CA-T8 | PASS | Evidência persistida nesta seção do plano. |

#### Roteiro manual RM, máquina real

**Pré-condições observadas antes do bootstrap:** `docker ps -a --filter
name=^/ai-memory$ --format '{{.Names}} {{.Status}}'` retornou `ai-memory Up
24 hours (healthy)`. `docker port ai-memory` retornou
`49374/tcp -> 127.0.0.1:49374`. O mount era
`/home/vitor/.local/share/ai-memory -> /data`. `docker exec ai-memory
ai-memory status` informou versão 2.4.0, 88 páginas atuais, 99 versões,
163 sessões, 8.059 observações e 11,8 MiB. O volume tinha 138 arquivos
Markdown e 591.041 bytes. O container usava a rede `bridge`.

Antes do bootstrap, `~/.config/opencode/opencode.jsonc` existia com 181
bytes, `~/.config/opencode/plugins/ai-memory.ts` existia e
`~/.copilot/mcp-config.json` não existia. O wrapper tinha SHA-256
`38986e85f8170866d7b3b8d91334985d05c15acc912f067c2a7ccadfe1f960bd`.
O digest da imagem era `sha256:ad04782362fbf453495f90d07b6f6466899b1840a8eb429f511ff0f2cf2819ac`.

Resumo por fase: A INCOMPLETA por RM-1; B PASS por RM-11; C BLOQUEADA por
divergência SHA-256 em RM-12; D BLOQUEADA porque nenhum serviço novo iniciou.

| RM | Comando ou ação | Resultado |
|---|---|---|
| RM-1 | Bootstrap sobre o piloto manual | FAIL, container existente recusado como imagem não autorizada. |
| RM-2 | `docker port ai-memory` | PASS no preflight, `127.0.0.1:49374`. |
| RM-3 | Hash do wrapper e digest da imagem | Registrados, sem comparação aprovada após RM-1 falhar. |
| RM-4 | Segunda execução idempotente | Não verificável, RM-1 não provisionou. |
| RM-5 | Servidor fake na porta 49374 | Não executado. O cenário ficou interrompido após RM-1. |
| RM-6 | Rede restrita e consulta local | Não executado. O container antigo usava `bridge`. |
| RM-7 | Merge de `~/.copilot/mcp-config.json` | Não executado. O arquivo não existia no preflight. |
| RM-8 | Detecção contra upstream real | PASS, clone removido, avisos presentes, checkout sem mudança. |
| RM-9 | Inspeção da cópia Copilot | PASS, 5 descrições e 5 caminhos absolutos válidos. |
| RM-10 | Reiniciar OpenCode e validar MCP | BLOQUEADO, sem serviço novo; exige reinício humano. |
| RM-11 | Rollback preservando o volume | PASS, rollback informou dados preservados e restaurou o JSONC. |
| RM-12 | Re-provisionamento do zero | FAIL, verificação SHA-256 bloqueou o wrapper baixado. |
| RM-13 | Ler wiki pelo serviço novo | BLOQUEADO, nenhum container novo ficou ativo. |

**Saída relevante de RM-1:** o bootstrap inspecionou o container e informou:
`ai-memory não provisionado: O container ai-memory existente não usa a imagem
autorizada akitaonrails/ai-memory:latest; preserve os dados e revise o
container antes de reexecutar. O bloco MCP foi desabilitado nos harnesses.`
A inspeção retornou `Config.Image=docker.io/akitaonrails/ai-memory:latest`,
mount `/home/vitor/.local/share/ai-memory:/data` e rede `bridge`. O container
continuou ativo e saudável nessa tentativa. Suspeita para `eng-software`:
validação da referência Docker normalizada. O QA não investigou código de
produção.

RM-8 usou `opencode-skills detect writing-for-agents`, que informou ausência
de mudanças. A execução `opencode-skills detect addyosmani` encontrou mudanças
em 10 skills e mostrou um aviso de conteúdo NÃO CONFIÁVEL para cada skill. O
clone temporário `/tmp/opencode-skills-fno726nw/upstream` foi removido. O
checkout não recebeu alterações novas. Nenhum conteúdo upstream foi executado.

RM-9 verificou `~/.copilot/agents/sec.agent.md`. O bloco gerado continha 5
descrições autorizadas e 5 caminhos absolutos existentes. O arquivo
`~/.copilot/mcp-config.json` continuou ausente.

RM-11 executou `~/.local/bin/opencode-bootstrap --rollback-ai-memory`. A saída
confirmou `Rollback concluído; o volume de dados foi preservado`. O rollback
removeu o container e o plugin, e restaurou
`~/.config/opencode/opencode.jsonc`. O SHA-256 restaurado
`a8e9b22dd587129d2535a23971ff463ff12ce7cf8c1dbac4241a6e34f6654eda` bateu
com o backup de 181 bytes. O volume manteve o banco SQLite de 12.673.024 bytes
e 138 arquivos Markdown.

RM-12 executou `bash ./scripts/bootstrap_repo/configurar-repo.sh --yes` após o
rollback. O bootstrap bloqueou o wrapper baixado por divergência de integridade:
esperado `4b2e5736195f0ac4cd38adf62f25b294922ebf81f5f4802a07803e1abbf9f72d`,
encontrado `49c965a0319dbe9c525d552a9a4c8b3464e5dd278e36d5dc7a03edee8b5502e6`.
O bootstrap desabilitou MCP e não criou o container. O finding é de segurança,
encaminhamento `sec`. O QA não ignorou o SHA nem executou o wrapper.

Após RM-12, o QA repetiu o rollback para restaurar o JSONC e limpar artefatos.
No estado final, o container, o wrapper, o plugin e a rede internal estavam
ausentes. O JSONC restaurado manteve o SHA original. O volume continuou no
caminho `~/.local/share/ai-memory/`, com o banco e os 138 arquivos Markdown.
RM-13 não passou porque nenhum serviço novo pôde ler a wiki. Não foi observada
interferência do `sec`; o `git status` permaneceu sem mudanças novas após RM-8.

#### Documentação e evidências

- `docs/README.md#testes-por-especialidade` define as suítes e não exige
  artefato permanente de plano separado. A evidência fica neste plano,
  conforme o destino solicitado.
- Nenhuma spec de produto foi criada ou alterada nesta fase.
- Evidência anterior a `d646b41`: agregador #4 `pass`; duas execuções diretas
  com 903 passed e 31 deselected; cobertura 85%; meta não aplicável.
- Flakiness: 16 errors agregados reproduzidos duas vezes, mas não no arquivo
  isolado nem nas suítes completas diretas. Hipótese e detecção precoce acima.
- Retomada após `d646b41`: o agregador retornou `pass`; a suíte direta terminou
  com 904 passed e 31 deselected em 188,03 s; cobertura 85%.
- Roteiro atualizado: RM-11 passou, RM-12 provisionou a versão aprovada e RM-13
  leu uma página anterior pelo novo serviço. RM-2, RM-5, RM-6 e RM-10 falharam.
- Estado final: volume preservado, container novo healthy e rede internal. O
  host não publicou `127.0.0.1:49374`; o MCP declarado não conecta do OpenCode.

#### Retomada RM após `d646b41`, 2026-09-27

O checkout estava em `1006797`, com `d646b41` na linhagem. Não havia diferenças
posteriores no bootstrap ou em seus testes. O agregador final retornou
`{"status":"pass","findings":[]}`. A suíte direta terminou com 904 passed,
31 deselected e 188,03 s. A cobertura total foi 85%. A flakiness registrada
acima não se reproduziu nesta execução.

**Pré-condições:** o rollback anterior tinha removido container, wrapper e
plugin. O JSONC manual estava restaurado com 181 bytes. O volume tinha owner
`vitor:vitor`, mode `0700` e diretórios `db`, `wiki`, `hook-spool`, `logs` e
`models`. O processo OpenCode PID 174606 continuava ativo. Não calculei hashes
nem contagens exatas do volume.

Fase A iniciou sem container antigo. O bootstrap executou
`bash ./scripts/bootstrap_repo/configurar-repo.sh --yes`, baixou o wrapper
aprovado e puxou a imagem amd64. O provisionamento terminou e declarou MCP nos
dois harnesses. Como o rollback já tinha removido o piloto v2.4.0, esta execução
validou instalação nova, não o caminho de upgrade de container existente.

Resumo das fases: A BLOQUEADA por RM-2/RM-5/RM-6/RM-10; B PASS; C provisionou
com o endpoint host inacessível; D PASS na leitura interna de página anterior.

| RM | Evidência | Resultado |
|---|---|---|
| RM-1 | Bootstrap completo no estado limpo após rollback | PASS para instalação nova; upgrade antigo não repetido. |
| RM-2 | `docker port ai-memory`, `ss`, `curl` | FAIL, sem porta publicada nem listener em loopback. |
| RM-3 | SHA wrapper e digest da imagem | PASS, wrapper `49c965a0…e8b5502e6`, imagem amd64 `5ce8700b…d221ef6e`. |
| RM-4 | Segunda execução do bootstrap | PASS, mesmo container, sem pull e com plugin `no-op`. |
| RM-5 | Listener fake e nova execução do bootstrap | FAIL, bootstrap aceitou a porta ocupada e retornou 0. |
| RM-6 | `docker inspect` da rede e consulta local | FAIL, rede internal ativa, host sem acesso ao serviço. |
| RM-7 | Declarações OpenCode e Copilot | PARCIAL, MCP declarado; merge sem config prévia não testado. |
| RM-8 | Detecção real de upstream, executada antes da retomada | PASS, sem mudança no checkout. |
| RM-9 | Agente Copilot `sec`, executado antes da retomada | PASS, 5 descrições e caminhos absolutos existentes. |
| RM-10 | `opencode mcp list` | FAIL, conexão recusada em `127.0.0.1:49374/mcp`; OpenCode não reiniciado. |
| RM-11 | `~/.local/bin/opencode-bootstrap --rollback-ai-memory` | PASS, volume e estrutura preservados. |
| RM-12 | Bootstrap completo após RM-11 | PASS para provisionamento, com a mesma falha de porta de RM-2. |
| RM-13 | `ai-memory status` e `ai-memory read-page` no container | PASS, página anterior lida sem exibir conteúdo. |

**Resultado de RM-3:** o wrapper instalado tinha SHA-256
`49c965a0319dbe9c525d552a9a4c8b3464e5dd278e36d5dc7a03edee8b5502e6`. O
container usou `akitaonrails/ai-memory:latest@sha256:5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e`.
O mount continuou em `/home/vitor/.local/share/ai-memory:/data`.

**Resultado de RM-4:** a segunda execução manteve o container ID, não executou
`docker pull` e deixou o plugin como `no-op`. O `docker inspect` mostrou
`HostConfig.PortBindings` com `127.0.0.1:49374`, mas
`NetworkSettings.Ports` permaneceu `{"49374/tcp":null}`. `docker port ai-memory`
não listou bind. `ss` não mostrou listener e o teste HTTP retornou connection
refused.

**Resultado de RM-5:** o QA parou o container e abriu um listener HTTP fake em
`127.0.0.1:49374`. O listener recebeu 503 requisições durante a execução do
bootstrap. O bootstrap retornou código 0, recriou o container e não mostrou
erro de porta ocupada. O QA não deixou o fake listener ativo. A falha coincide
com a ausência de publicação observada em RM-2; suspeita para `eng-software`.

**Resultado de RM-6 e RM-10:** `ai-memory-internal` tinha `Internal=true` e o
container estava saudável. O serviço respondeu a comandos executados com
`docker exec`, mas o host não alcançou o endereço MCP de loopback. O CLI
`opencode mcp list` confirmou falha de conexão. O QA não reiniciou o processo
OpenCode PID 174606.

**Resultado de RM-11:** o rollback confirmou preservação dos dados. Após o
rollback, o volume manteve owner `vitor:vitor`, mode `0700` e a estrutura
esperada. O JSONC manual foi restaurado. O QA não comparou bytes nem interrompeu
o writer OpenCode.

**Resultado de RM-13:** depois de RM-12, `ai-memory status` leu a base pelo
mount, informou formato wiki `OKF v0.2` e FTS populado. O QA selecionou uma
página criada antes do reprovisionamento. O comando `ai-memory read-page`
retornou código 0 e corpo não vazio. O arquivo Markdown correspondente existia
no volume. O QA suprimiu caminho, título e corpo no output. A validação usou
existência, modo e estrutura, sem exigir snapshot byte a byte.

**Estado atual e bloqueios:** o container v2.4.1 está healthy, usa a rede
internal e monta o volume preservado. As configurações OpenCode e Copilot
declaram o MCP. O OpenCode não conecta porque o host port 49374 não foi
publicado. CA-T5 continua BLOQUEADO por RM-2, RM-5, RM-6 e RM-10. A preservação
e leitura dos dados em RM-11/RM-13 passaram. O curador-produto ainda precisa de
uma revalidação do bind de loopback e do cenário de porta ocupada após análise
de `eng-software`. A rota de upgrade sobre container preexistente e o merge de
servidores Copilot preexistentes seguem sem teste nesta retomada.
O JSONC original foi movido para
`/home/vitor/.config/opencode-backup/20260927-200753/opencode.jsonc`; o backup
tem 181 bytes e mantém o SHA-256 original. O caminho de origem não existe após
o bootstrap, conforme o contrato de provisionamento.

Não observei interferência do `sec`; o `git status` não mostrou alterações de
código durante a retomada. O QA não alterou código de produção, `Status`, nem
planos paralelos. O QA não removeu nem hasheou o volume.

### TESTES — sec — 2026-09-27

#### Diagnóstico prioritário do SHA-256

- O SHA que falhou é do wrapper. A imagem não foi objeto dessa validação. `src/opencode_config/bootstrap/ai_memory.py`
  fixa `AI_MEMORY_WRAPPER_SHA256=4b2e5736195f0ac4cd38adf62f25b294922ebf81f5f4802a07803e1abbf9f72d` e baixa
  `https://github.com/akitaonrails/ai-memory/releases/latest/download/ai-memory-wrapper`.
- Comando de verificação, com TLS padrão e sem gravar nem executar o asset:

  ```bash
  python3 -c 'import hashlib, urllib.request
  url = "https://github.com/akitaonrails/ai-memory/releases/latest/download/ai-memory-wrapper"
  response = urllib.request.urlopen(url, timeout=30)
  data = response.read()
  print(response.status, len(data), hashlib.sha256(data).hexdigest())'
  ```

- A leitura HTTPS do asset retornou status 200, 38.971 bytes e SHA-256
  `49c965a0319dbe9c525d552a9a4c8b3464e5dd278e36d5dc7a03edee8b5502e6`. A API pública do release
  (`/repos/akitaonrails/ai-memory/releases/latest`) confirmou o mesmo digest para `v2.4.1`, publicado
  em 2026-09-25.
- A busca dos releases confirmou que o SHA fixado no código pertence ao wrapper `v2.0.3`, publicado
  em 2026-09-04. O wrapper do piloto, SHA `38986e85f8170866d7b3b8d91334985d05c15acc912f067c2a7ccadfe1f960bd`,
  corresponde ao asset `v2.4.0` publicado em 2026-09-21.
- Comando para conferir a tag Docker remota: `docker buildx imagetools inspect akitaonrails/ai-memory:latest`.
  Resultado: índice OCI `sha256:a626d115e0350afe934954c02c9064d30b708c58316763a9c6674ef5d0c8e3d9`,
  manifest linux/amd64 `sha256:5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6` e linux/arm64
  `sha256:dc18b3b93bfe4fbef1175ae364784b657d8cbcc8cc4f01b08d8dfbc75b60cf33`.
- A imagem em cache tem ID e `RepoDigest` `sha256:ad04782362fbf453495f90d07b6f6466899b1840a8eb429f511ff0f2cf2819ac`.
  O digest remoto mudou. Nenhuma imagem foi puxada nem iniciada nesta execução.
- O bootstrap recusou o wrapper antes de instalá-lo ou executá-lo. A tag `latest` remota também diverge
  da imagem em cache. O ADR-0008 informa que o bootstrap não atualiza uma imagem já presente. S1 aceitou
  a tag flutuante, mas a revisão do piloto cobriu o digest anterior. A decisão humana posterior
  autorizou usar a versão nova, condicionada à revalidação abaixo.

#### RM sec-1, bind de loopback

- **Esperado:** `docker port ai-memory` lista somente `127.0.0.1:49374`.
- **Comando:** `docker port ai-memory`.
- **Obtido:** `Error response from daemon: No such container: ai-memory`.
- **Resultado:** BLOQUEADO. O QA registrou loopback no preflight antes do rollback. Não havia serviço
  para repetir a verificação depois do rollback.

#### RM sec-2, integridade do wrapper e digest da imagem

- **Esperado:** wrapper instalado com SHA esperado no código e digest da imagem registrado.
- **Comandos:** download HTTPS do asset `releases/latest`, cálculo SHA-256 em memória,
  `docker image inspect --format 'RepoTags={{json .RepoTags}} Id={{.Id}} Digests={{json .RepoDigests}}'
  akitaonrails/ai-memory:latest` e `docker buildx imagetools inspect akitaonrails/ai-memory:latest`.
- **Obtido:** wrapper ausente após o rollback; o asset `v2.4.1` tem SHA diferente do código. A imagem
  em cache tem digest `ad047...`; a tag remota aponta para o índice OCI `a626...`.
- **Resultado:** BLOQUEADO para provisionar artefatos novos. O bootstrap falhou fechado e não executou
  o wrapper divergente. A decisão humana está registrada em `## Perguntas`.

#### Revalidação de upstream, 2026-09-27

**Wrapper `v2.4.1`**

- Baixei o asset em `/tmp/opencode/ai-memory-wrapper-v2.4.1`. `file` classificou o arquivo como
  script Bash UTF-8. SHA-256 calculado: `49c965a0319dbe9c525d552a9a4c8b3464e5dd278e36d5dc7a03edee8b5502e6`,
  igual ao valor aprovado. Não executei o arquivo.
- Baixei `v2.0.3` para comparação. O SHA-256 foi `4b2e5736195f0ac4cd38adf62f25b294922ebf81f5f4802a07803e1abbf9f72d`,
  igual ao pin anterior. A comparação estática cobre 803 linhas antigas e 917 novas, com 196 linhas
  adicionadas ou removidas.
- Mudanças relevantes: fallback Docker → Podman; comparação separada dos digests OCI por arquitetura;
  preservação dos modos dos mounts na reconstrução do comando; armazenamento do cliente nativo em
  `XDG_DATA_HOME`; encaminhamento de `GEMINI_API_KEY`, `GOOGLE_API_KEY` e `OPENCODE_API_KEY` ao helper.
- Li o script completo. As URLs fixas consultadas apontam para assets de release no GitHub oficial;
  `AI_MEMORY_WRAPPER_URL`, `AI_MEMORY_WRAPPER_SHA256_URL` e `AI_MEMORY_SERVER_URL` são overrides explícitos.
  Não encontrei `eval`, payload codificado, POST ou upload explícito. O wrapper encaminha variáveis de
  credenciais ao container helper; não encontrei envio dessas variáveis a endpoint extra no wrapper.
- Riscos herdados, também presentes em `v2.0.3`: `upgrade` baixa o wrapper e seu checksum da mesma origem,
  executa a versão baixada e usa `docker pull` com a imagem configurada, cujo padrão é `latest`. No Linux,
  o helper usa `--network host` quando não há `AI_MEMORY_SERVER_URL` e monta `$HOME` e `$PWD` para escrita.
  Não usei `ai-memory upgrade` como caminho de atualização por digest.
- **Veredicto: apto · atualizar pin.** Não encontrei código suspeito novo. A atualização continua sujeita
  ao caminho controlado por digest proposto abaixo.

**Imagem `latest`**

- `docker buildx imagetools inspect --raw` mais SHA-256 confirmou o índice
  `a626d115e0350afe934954c02c9064d30b708c58316763a9c6674ef5d0c8e3d9`.
- O índice referencia linux/amd64 `5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e` e linux/arm64
  `dc18b3b93bfe4fbef1175ae364784b657d8cbcc8cc4f01b08d8dfbc75b60cf33`. O digest amd64 informado na tarefa,
  terminado em `ef6`, foi rejeitado pelo Docker por comprimento inválido. O valor do índice termina em `ef6e`.
- `docker manifest inspect --verbose` e `docker buildx imagetools inspect --format '{{json .Image}}'` mostraram
  linux/amd64, `User=ai-memory`, porta `49374/tcp`, entrypoint `/usr/local/bin/ai-memory` e comando
  `serve --transport http --bind 0.0.0.0:49374 --enable-web`. O histórico identifica Debian Bookworm,
  instalação de certificados CA, criação do usuário de sistema e cópias de hooks e binário.
- O manifest declara cinco camadas com digests e tamanhos. Os blobs das camadas não foram baixados nem
  escaneados. A configuração de runtime coincide com a imagem local antiga; os digests das camadas de
  instalação, hooks e binário diferem. A imagem local continua com ID `ad047...`.
- Não fiz pull nem iniciei container. `docker ps -a` não listou `ai-memory`. **Veredicto: apto · atualizar
  pin**, usando o digest amd64 corrigido acima. A avaliação cobre metadados e histórico, não o conteúdo
  dos binários dentro das camadas.

#### Lacuna de atualização no ADR-0008 e proposta

O ADR-0008 afirma que o bootstrap não atualiza uma imagem existente, mas não registra um procedimento
controlado para essa atualização. O `ai-memory upgrade` do wrapper usa `latest`, atualiza hooks e pode
executar `compose up -d`; para instalações standalone, ele escreve um script de recriação. O comando não
exige os digests revisados nesta tarefa.

Proponho inserir esta redação no ADR-0008, em uma seção “Atualização de instalação existente”:

> Para atualizar uma instalação existente, aprove previamente o SHA-256 do wrapper e os digests OCI do
> índice e da plataforma. Baixe o wrapper em área temporária, valide o SHA aprovado e revise o diff sem
> executá-lo. Inspecione manifest, configuração, histórico e digests das camadas da imagem escolhida.
> Após aprovação, recrie o container usando `repositório@sha256:<digest>`, preserve o volume e mantenha o
> bind em `127.0.0.1` e a rede `internal`. Registre a verificação de saúde e o rollback para os digests
> anteriores. Não use `ai-memory upgrade` enquanto o comando depender da tag flutuante `latest`.

Proponho estender SEC-06 com esta redação executável:

> Uma atualização existente exige os digests aprovados do wrapper, do índice OCI e da plataforma. O
> bootstrap valida essas identidades antes de substituir wrapper ou container. Se a validação falha, o
> serviço anterior e o volume permanecem intactos. A atualização aprovada usa o digest imutável da
> plataforma e mantém o bind em `127.0.0.1` e a rede `internal`.

`docs/README.md` exige fitness function para ADR; o fixture Concordion e a suíte de segurança também
precisarão de atualização após aprovação humana. Não alterei ADR, spec ou fixture.

#### RM sec-3, segunda execução idempotente

- **Esperado:** segunda execução sem novo download ou pull, com hashes estáveis ou aviso explícito.
- **Obtido:** não houve provisionamento válido na primeira execução. As tentativas terminaram no gate
  de integridade ou no teste de porta ocupada.
- **Resultado:** BLOQUEADO. Não foi possível validar idempotência sem contornar o SHA divergente.

#### RM sec-4, porta ocupada

- **Preparação:** um listener fake escutou em `127.0.0.1:49374` e aceitou conexões durante o bootstrap.
- **Comando:** `bash ./scripts/bootstrap_repo/configurar-repo.sh --yes`.
- **Obtido:** o bootstrap exibiu `A porta 127.0.0.1:49374 já está ocupada. Identifique o processo e
  libere a porta antes de reexecutar.` e desabilitou MCP. O processo terminou com código 1.
- **Resultado:** PASS. Uma primeira tentativa com listener sem loop de `accept` não manteve a porta
  detectável. O teste foi repetido com loop de aceitação, que registrou 10 conexões.

#### RM sec-5, rollback e preservação do volume

- **Comando:** `~/.local/bin/opencode-bootstrap --rollback-ai-memory`.
- **Obtido:** `Rollback concluído; o volume de dados foi preservado.` O container e a rede internal
  ficaram ausentes. O wrapper e o plugin ficaram ausentes. O JSONC foi restaurado com 181 bytes e SHA-256
  `a8e9b22dd587129d2535a23971ff463ff12ce7cf8c1dbac4241a6e34f6654eda`.
- **Resultado:** PASS com ressalva. O diretório permaneceu com mode `0700`; os marcadores de provisionamento
  foram removidos. A árvore tinha 932 arquivos e 114.434.376 bytes antes do roteiro, com SHA agregado
  `8f71b32369541de15d1c726291e5ac385c14463ec9863a91dc2feeb7398d140d`. Depois, a árvore tinha 982 arquivos,
  114.565.959 bytes e SHA agregado `396c091b1fa60e5d64e26310d10476d2df70dbe9bfacf5916fed49372c171776`.
- `fuser -vm ~/.local/share/ai-memory` mostrou processos `opencode`, `python3`, `git`, `docker` e shells
  usando o diretório. Quarenta e seis arquivos JSON tinham `mtime` posterior a 16h47. A origem das
  escritas não foi confirmada. Nenhum comando desta execução apagou o diretório; a verificação byte a
  byte ficou inconclusiva por atividade concorrente. Não executei nova mutação no volume.

#### Diagnóstico read-only de RM sec-5, 2026-09-27

- `stat` confirmou diretório `~/.local/share/ai-memory` com owner `vitor:vitor` e modo `0700`. A estrutura
  contém `db/memory.sqlite`, seus arquivos WAL/SHM, `wiki`, `hook-spool`, `logs` e `models`.
- `ps` encontrou OpenCode PID `174606`, iniciado às 14h38. Não encontrou processo `ai-memory` nem container
  `ai-memory` em `docker ps -a`. O arquivo `.serve.lock.holder` diz `pid=1`, mas o PID 1 do host é systemd
  e o arquivo tem mtime de 2026-09-26; o marcador não comprova serviço ativo.
- `lsof +D` no volume e nos arquivos SQLite não mostrou descritores abertos; a saída avisou que não leu
  um namespace Docker. `fuser -vm` listou processos do host, mas `-m` identifica uso do filesystem, não
  escrita naquele diretório. A lista anterior não confirma autoria de escrita.
- `hook-spool` tinha mtime `2026-09-27 17:17 -0300`, durante esta sessão. A origem provável é o fluxo de
  hooks do processo OpenCode, que está ativo, mas não confirmei um descritor de escrita nem ligação com
  o SQLite. Não executei comando de mutação; hooks automáticos podem ter gravado observações durante a
  própria sessão.
- **Diagnóstico:** OpenCode é o único processo persistente candidato observado. A autoria de escrita no
  volume não ficou provada por `lsof`/`fuser`; não há serviço `ai-memory` local ativo confirmado.
- **Política para testes que mutam o volume:** com writer ativo, valide existência, owner, modo `0700` e
  estrutura esperada. Não exija contagem exata nem hash byte a byte. Para comparar bytes, interrompa ou
  drene o writer com aprovação humana e só então tire snapshots antes/depois. Não pare o serviço como
  parte implícita do teste.

#### RM sec-6, merge Copilot com configuração preexistente

- **Esperado:** preservar outros servers e criar backup antes da escrita.
- **Obtido:** `~/.copilot/mcp-config.json` não existia. O provisionamento parou no SHA divergente.
- **Resultado:** BLOQUEADO. Não criei uma configuração artificial nem contornei o gate de integridade.

#### RM sec-7, detecção de upstream

- **Comandos:** `opencode-skills detect writing-for-agents` e `opencode-skills detect addyosmani`.
- **Obtido:** `writing-for-agents` sem mudanças. `addyosmani` mostrou mudanças em 10 skills e marcou
  cada diff como conteúdo NÃO CONFIÁVEL. O clone `/tmp/opencode-skills-rd5r0sqb` foi removido.
  `git status --short` ficou igual ao estado anterior ao roteiro.
- **Resultado:** PASS. Nenhum conteúdo upstream foi executado nem aplicado.

#### RM sec-8, cópia do agente Copilot

- **Esperado:** descrições somente de skills autorizadas e caminhos absolutos existentes.
- **Comando:** inspeção de `~/.copilot/agents/sec.agent.md` e verificação de existência das referências.
- **Obtido:** 5 descrições e 5 caminhos absolutos. Os 5 arquivos referenciados existem.
- **Resultado:** PASS.

#### RM sec-9, rede restrita e serviço local

- **Esperado:** container na rede Docker `internal`, com consulta MCP local respondendo.
- **Comandos:** `docker inspect ai-memory` e `docker network inspect ai-memory-internal`.
- **Obtido:** container e rede ausentes depois do rollback. Nenhuma consulta de status ou MCP foi possível.
- **Resultado:** BLOQUEADO. O digest remoto foi inspecionado sem pull, mas o novo container não foi iniciado.

#### Achados

- **Achado histórico:** o SHA do wrapper novo divergia do pin antigo. **Ação:** revalidei o asset e a
  comparação com `v2.0.3`; o novo pin está apto. **Severidade:** bloqueante antes da revalidação, resolvido.
- **Achado histórico:** o manifest remoto divergia da imagem local. **Ação:** validei o índice e os
  metadados da plataforma amd64 sem pull nem execução; corrigi o digest amd64 inválido informado.
  **Severidade:** bloqueante antes da revalidação, resolvido.
- **Melhoria de procedimento:** `ai-memory upgrade` atualiza por `latest` e não exige digests aprovados.
  **Ação:** proposta de atualização do ADR-0008 e SEC-06 registrada acima, pendente de aprovação humana.

### Evidências (sec) — Testes

- [x] Roteiro manual: 9 itens, 4 passaram, 0 falharam e 5 ficaram bloqueados.
- [x] Achados: 2 no total, 2 bloqueantes; as decisões de confiança estão em `## Perguntas`.
- [x] Revalidação RM sec-2: wrapper e índice OCI conferidos por SHA-256; nenhuma execução ou pull.
- [x] Imagem amd64: manifest/config/histórico e cinco digests de camada inspecionados; payload não baixado.
- [x] RM sec-5: processo escritor não confirmado; política de integridade tolerante registrada.
- [x] Upgrade: proposta para ADR-0008 e SEC-06 registrada no plano; alterações permanentes aguardam aprovação.
- [x] Volume: diretório preservado pelo rollback; verificação byte a byte inconclusiva por escritas
  concorrentes observadas.
- [x] Documentação: `docs/README.md` aponta `docs/specs/Seguranca.md` e os ADRs como destino permanente.
  A spec de segurança e o ADR-0008 já existem. Nenhum artefato de produto foi criado ou alterado nesta fase.

### Ajuste de pins — 2026-09-27

A decisão humana de usar a versão nova foi registrada em `## Perguntas`, RM sec-2. O sec aprovou os
artefatos upstream revisados.

- Wrapper: `v2.4.1`, URL versionada e SHA-256
  `49c965a0319dbe9c525d552a9a4c8b3464e5dd278e36d5dc7a03edee8b5502e6`.
- Imagem: tag `latest` qualificada pelo digest linux/amd64
  `5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e`.
- Manifest OCI validado: `a626d115e0350afe934954c02c9064d30b708c58316763a9c6674ef5d0c8e3d9`.
- TDD: `test_ai_memory_upstream_release_pins_match_reviewed_artifacts` falhou com os pins antigos por
  ausência de `AI_MEMORY_WRAPPER_VERSION`; passou após a atualização das constantes.
- Testes E10 relacionados: `.venv/bin/pytest tests/bootstrap/ tests/harnesses/
  tests/scripts/bootstrap_repo/test_repo_state.py -m all -q`, 212 passaram.
- Ruff: `.venv/bin/ruff check src/opencode_config/bootstrap/ai_memory.py
  tests/bootstrap/test_ai_memory_provision.py`, passou.
- `git diff --check`: passou. Nenhum provisionamento real foi executado.
- O caminho `tests/scripts/bootstrap_repo/test_ai_memory_provision.py` citado na solicitação não existe;
  o módulo está em `tests/bootstrap/test_ai_memory_provision.py`.
- Commit `d646b41`: `fix(bootstrap): atualiza pins do ai-memory para upstream atual`.

### Correção porta MCP — 2026-09-27

#### Diagnóstico da causa raiz

- Hipótese confirmada neste ambiente: Docker Engine `29.5.2`, Linux,
  `overlayfs`. O container `ai-memory` continuou `running` e `healthy`.
- `docker inspect` mostrou `HostConfig.PortBindings` com
  `127.0.0.1:49374`, mas `NetworkSettings.Ports` foi
  `{"49374/tcp":null}`. `docker port ai-memory` não listou publicação;
  `ss` não encontrou listener em loopback e `curl 127.0.0.1:49374` foi
  recusado.
- O container usa `ai-memory-internal`, com `Internal=true`, subnet
  `172.19.0.0/16` e endereço `172.19.0.2`. O campo `Gateway` do endpoint
  do container está vazio. A rota do host aponta para a bridge Docker.
- A conexão TCP do host a `172.19.0.2:49374` passou. A rede mantém apenas
  o container `ai-memory`. Não executei requisição que alterasse a wiki.
- Causa: o bootstrap validava a configuração desejada em `HostConfig`, não
  a publicação efetiva. Nesta combinação, `--publish` e `--internal`
  coexistem no pedido Docker, mas o Engine não cria a publicação no host.

#### Correção e garantias

- O bootstrap usa loopback quando `NetworkSettings.Ports` confirma a
  publicação em `127.0.0.1:49374` e o host alcança o endpoint.
- Sem publicação efetiva, valida IPv4 privado da rede internal e conexão
  TCP do host antes de habilitar MCP. Se encontrar endereço inválido,
  publicação fora de loopback, endpoint inacessível ou peer já conectado
  à rede internal, desativa MCP.
- O fallback não abre listener nas interfaces do host. O serviço continua
  na rede `internal`, sem rota de saída padrão. O host usa a interface da
  bridge para alcançar o endereço privado do container.
- O endpoint ativo é persistido em `.bootstrap-mcp-url` dentro do diretório
  restrito do ai-memory. OpenCode e Copilot recebem o endpoint; hooks usam
  a URL base. O OpenCode materializa uma cópia local quando precisa do
  endereço da bridge, sem escrever na configuração canônica. Copilot
  atualiza ou remove apenas entradas com URL gerenciada conhecida.
- SEC-03 continua limitando qualquer publicação efetiva ao loopback. No
  fallback não há porta publicada no host. SEC-21 permanece com a rede
  Docker `internal`. Um container externo precisa de conexão explícita
  àquela rede; o bootstrap recusa peers existentes.
- Docs consultados: `docs/README.md`. Atualizei a seção ai-memory do
  `README.md`, a descrição operacional do ADR-0008 e os diagramas C4 L1-L3.
  Nenhuma spec executável mudou; SEC-03 e SEC-21 permanecem as garantias.

#### Verificação

- RED observado antes da implementação: testes de endpoint interno e de
  URL dinâmica dos adapters falharam com `TypeError` por APIs ausentes.
  O teste de rede compartilhada falhou porque o bootstrap baixou wrapper
  antes de rejeitar o peer.
- GREEN: 81 testes passaram em
  `tests/bootstrap/test_ai_memory_provision.py`,
  `tests/harnesses/test_opencode.py` e `tests/harnesses/test_copilot.py`.
- Ruff passou nos oito módulos Python alterados. `git diff --check` passou.
- Revalidação real somente leitura: container permaneceu saudável, com o
  mesmo ID e mount `/home/vitor/.local/share/ai-memory:/data`. A rede
  continuou internal, sem peer adicional; o probe TCP à bridge passou.
  Não rodei bootstrap real, parei container nem alterei o volume do piloto.
- Semântica de RM-2 no fallback: `docker port` permanece vazio por projeto.
  A checagem deve validar endpoint MCP pela bridge e ausência de listener
  publicado; o bind de loopback continua sendo usado quando o Engine o ativa.

### TESTES — qa (re-execução) — 2026-09-27

#### Escopo e segurança

- Reexecutei RM-2, RM-5, RM-6, RM-10 e a fase A. Completei RM-7 com um
  servidor Copilot temporário para representar uma entrada não gerenciada.
  RM-1 continua bloqueado porque exige a transição real de uma imagem antiga.
- Não reexecutei `testes-produto` nem a suíte `-m all`. Nenhum script de teste
  ou teste do repo mudou neste lote. A última execução registrada continua
  verde: agregador `pass`, 904 passed, 31 deselected e cobertura de 85%.
- O preflight encontrou `ai-memory` healthy, container
  `68c6dc0341d9...`, imagem em execução `5ce8700b...d221ef6e`, rede internal,
  IP `172.19.0.2` e volume `/home/vitor/.local/share/ai-memory:/data`.
- O volume terminou com owner `vitor:vitor`, modo `0700` e estrutura `db`,
  `wiki`, `hook-spool`, `logs` e `models`. Não removi dados nem comparei hashes
  ou contagens exatas. O bootstrap gravou `.bootstrap-mcp-url` com o endpoint
  da bridge, conforme o fluxo testado. Writers automáticos continuaram ativos.
- O processo OpenCode existente não foi reiniciado. O bootstrap atualizou a
  configuração local para a bridge e criou backups de configuração sob
  `~/.config/opencode-backup/`.

#### Evidências por passo

**RM-2, endpoint efetivo**

- **Comandos:** `docker port ai-memory`; `docker inspect` de
  `NetworkSettings.Ports` e da rede; conexão TCP Python a
  `172.19.0.2:49374`; leitura de `.bootstrap-mcp-url`.
- **Esperado:** sem publicação, usar IPv4 privado da rede internal, validar
  conexão do host e não abrir listener no loopback.
- **Obtido:** `docker port` vazio, `49374/tcp: null`, IP `172.19.0.2`, TCP
  conectado e arquivo com `http://172.19.0.2:49374/mcp`. `ss` não mostrou
  listener em `127.0.0.1:49374`.
- **Resultado:** PARCIAL. Seleção e conectividade TCP do endpoint fallback
  passaram. A validação HTTP de MCP falhou em RM-6/RM-10 por rejeição do Host.

**RM-5, porta loopback ocupada**

- **Comando/ação:** listener temporário em `127.0.0.1:49374`, respondendo
  HTTP 503; em paralelo, `bash ./scripts/bootstrap_repo/configurar-repo.sh --yes`.
- **Esperado:** como Docker não publicou a porta, selecionar a bridge, sem
  apontar MCP para o listener fake nem deixar o listener ativo.
- **Obtido:** bootstrap informou `A publicação loopback não está ativa; usando
  o endereço http://172.19.0.2:49374/mcp na bridge internal`, provisionou MCP
  e terminou com exit 0. O listener recebeu 4 conexões e foi encerrado. `ss`
  confirmou que a porta ficou livre.
- **Resultado:** PASS para fallback sem publicação. O bootstrap não abortou
  pelo listener local porque não usou a porta do host.

**RM-6, rede restrita e consulta local**

- **Comandos:** `docker network inspect`; `docker exec ai-memory ai-memory
  status`; POST MCP `initialize` ao IP da bridge com `Host: localhost:49374`;
  POST ao mesmo IP sem substituir o Host.
- **Esperado:** rede internal sem peers externos e serviço local consultável.
- **Obtido:** `Internal=true`, um peer (`ai-memory`), container healthy,
  `ai-memory status` retornou versão 2.4.1 e FTS 99/99. O POST com Host
  permitido retornou HTTP 200. O POST com Host `172.19.0.2:49374` retornou
  HTTP 403 e `forbidden host`.
- **Diagnóstico:** log do container diz `rejected request with disallowed Host
  header`; a allowlist contém `localhost`, `127.0.0.1`, `::1` e
  `host.docker.internal`, mas não o IP da bridge.
- **Resultado:** PARCIAL. Rede e serviço local passaram; a URL configurada pelo
  bootstrap não passa a validação HTTP de Host.

**RM-7, merge Copilot com entrada preexistente**

- **Backup:** antes do teste, salvei a configuração original em
  `/tmp/opencode/copilot-mcp-config-20260927-pretest.json`. O arquivo original
  tinha somente `ai-memory` em `127.0.0.1:49374`.
- **Ação:** inseri temporariamente `qa-preserved-server` em
  `~/.copilot/mcp-config.json` e executei o bootstrap. A saída declarou
  `MCP ai-memory declarado`.
- **Obtido:** o JSON resultante manteve `qa-preserved-server` e atualizou
  `ai-memory` para `http://172.19.0.2:49374/mcp`.
- **Restauração:** restaurei o JSON original, removi a cópia temporária e
  confirmei que `qa-preserved-server` não permaneceu na configuração.
- **Resultado:** PASS para backup, merge, preservação da entrada de teste e
  restauração. A configuração original do Copilot não continha outro servidor
  do usuário; a preservação foi exercitada com fixture temporária.

**RM-10, conexão OpenCode**

- **Comando:** `opencode mcp list` após o bootstrap atualizar
  `~/.config/opencode/opencode.json` para a URL da bridge.
- **Esperado:** `ai-memory` conectado pela bridge.
- **Obtido:** `ai-memory failed`, `Non-200 status code (403)` em
  `http://172.19.0.2:49374/mcp`. O log do container confirma rejeição do Host.
  O processo OpenCode que já estava ativo não foi reiniciado.
- **Resultado:** FAIL. A configuração aponta para a bridge, mas o cliente real
  recebe 403. O reinício da sessão existente também ficou pendente.

#### Fase A e atualização de imagem

- **Fase A:** `bash ./scripts/bootstrap_repo/configurar-repo.sh --yes` terminou
  com `ai-memory provisionado; declaração MCP habilitada nos harnesses`. O
  container manteve o mesmo ID, estado healthy e mount do volume. O bootstrap
  gravou o endpoint dinâmico e atualizou a configuração OpenCode. O instalador
  de hooks avisou que o SHA de `ai-memory.ts` mudou após `install-hooks`
  (`99f24a9e...50abf2a` para `0da3ee2c...b67fe75`). `opencode mcp list`
  continuou em 403. **Fase A incompleta**, aguardando correção da allowlist/Host
  e reinício humano do OpenCode.
- **RM-1, upgrade com imagem presente:** o bootstrap rodou sobre o container
  que já usava o digest aprovado `5ce8700b...d221ef6e`; ele manteve o mesmo
  container e não fez upgrade de imagem. A tag local
  `akitaonrails/ai-memory:latest` ainda aponta para `ad047823...f2cf2819ac`.
  Não executei `ai-memory upgrade` nem recriei o container. A seção
  `TESTES — sec` registra que esse comando usa `latest` e que a proposta de
  atualização controlada por digest aguarda aprovação humana. **BLOQUEADO**,
  sem decisão para executar a transição de imagem.

#### Quadro final RM-1..RM-13

Resultados anteriores permanecem para itens não reexecutados. RM-2, RM-5,
RM-6, RM-7 e RM-10 refletem a evidência desta reexecução.

| RM | Resultado | Base |
|---|---|---|
| RM-1 | BLOQUEADO | Upgrade de imagem não executado; evidência anterior cobriu instalação nova. |
| RM-2 | PARCIAL | Fallback TCP pela bridge passou; chamada HTTP de MCP retorna 403. |
| RM-3 | PASS | SHA do wrapper e digest aprovado registrados anteriormente. |
| RM-4 | PASS | Segunda execução idempotente registrada anteriormente. |
| RM-5 | PASS | Listener fake não foi usado; bootstrap selecionou endpoint da bridge. |
| RM-6 | PARCIAL | Rede e status locais passaram; HTTP no IP da bridge retorna 403. |
| RM-7 | PASS | Merge preservou a entrada fixture; backup e restauração concluídos. |
| RM-8 | PASS | Detecção de upstream sem mudanças no checkout, evidência anterior. |
| RM-9 | PASS | Agente Copilot e referências validados anteriormente. |
| RM-10 | FAIL | `opencode mcp list` retorna 403 por Host não permitido. |
| RM-11 | PASS | Rollback preservou volume e estrutura, evidência anterior. |
| RM-12 | PASS | Provisionamento após rollback passou anteriormente. |
| RM-13 | PASS | Leitura de página pelo serviço passou anteriormente. |

#### Evidências finais

- [x] Roteiro manual reexecutado: 6 itens, 2 PASS, 2 PARCIAL, 1 FAIL e fase A
  incompleta. RM-1 ficou BLOQUEADO porque não houve decisão para trocar imagem.
- [x] Volume validado por existência, owner, modo `0700` e estrutura. Sem hash
  byte a byte ou contagem exata.
- [x] Configuração Copilot restaurada após o teste de merge.
- [x] `testes-produto` e suíte completa não reexecutados; não houve alteração
  em scripts/testes que justificasse nova execução. Evidência verde anterior
  permanece: agregador `pass`, 904 passed, 31 deselected, cobertura 85%.
- [x] `docs/README.md#testes-por-especialidade` não exige artefato permanente
  separado. Registrei esta evidência no plano, sem criar spec de produto.

### Correção Host 403 — 2026-09-27

#### Causa e correção

- O container real usava `AI_MEMORY_ALLOWED_HOSTS=localhost,127.0.0.1,::1,host.docker.internal`.
  O endpoint configurado era `http://172.19.0.2:49374/mcp`; o Host `172.19.0.2:49374` não constava na lista.
- Diagnóstico somente leitura, com `curl` GET para `/mcp`: Host `172.19.0.2:49374` retornou
  `403 Forbidden`, corpo `forbidden host`. Os Hosts `localhost:49374`, `127.0.0.1:49374`,
  `[::1]:49374` e `host.docker.internal:49374` retornaram `405 Method Not Allowed`, com
  `Allow: POST`. O 405 confirma que a requisição passou pela validação de Host.
- Containers novos iniciam com um comando `sh` fixado no bootstrap. O comando lê o IPv4 próprio
  com `hostname -i` e configura `AI_MEMORY_ALLOWED_HOSTS` com esse endereço e os Hosts locais
  anteriores. O bootstrap grava o label `opencode-config.ai-memory-host-policy=bridge-ip`.
- O probe do bootstrap agora faz GET HTTP em `/mcp`: `405` significa que o Host passou pela
  validação; `403` mantém o MCP desabilitado. Um teste cobre os dois códigos.
- Containers antigos sem o label de política bloqueiam a habilitação. A mensagem orienta
  executar `--rollback-ai-memory` e o bootstrap novamente. Não recriei nem reiniciei o container
  real; a transição exigiria parar o serviço que usa o volume do piloto.
- SEC-03 permanece atendido: o bootstrap solicita publicação somente em loopback. O fallback da
  bridge não publica porta no host. SEC-21 permanece atendido: a rede Docker continua `internal`.
  Nenhum peer adicional foi usado para a configuração da allowlist.

#### Marcador e volume

- `.bootstrap-mcp-url` é estado do bootstrap, não conteúdo da wiki. O novo caminho é
  `~/.local/state/ai-memory/.bootstrap-mcp-url`, fora de `~/.local/share/ai-memory/`.
  O diretório de estado usa modo `0700` em POSIX.
- O leitor ainda reconhece o caminho legado no volume. Provisionamento e rollback removem somente
  esse marcador legado, além do estado de provisionamento; não removem banco, wiki ou demais dados.
  Não executei bootstrap, stop, rm ou operação de escrita sobre o volume do piloto. As únicas
  requisições ao serviço foram GETs de probe.
- `README.md`, seção ai-memory, descreve a allowlist da bridge, a migração de container antigo e
  o caminho externo do marcador. `docs/README.md` não exige outra spec para este ajuste; SEC-03 e
  SEC-21 não mudaram.

#### Verificação

- RED inicial: 4 testes falharam e 22 passaram no módulo focal. Um teste inicial de HTTP estava
  coberto pelo stub autouse do runner; o teste foi ajustado para exercitar respostas HTTP simuladas.
  O teste de caminho Windows também falhou antes do ajuste para usar o mesmo estado derivado de
  `home` em todos os harnesses.
- GREEN: `.venv/bin/pytest tests/bootstrap/test_ai_memory_provision.py -m all -q`, 26 passed.
  Nenhuma suíte completa foi executada, conforme o escopo desta tarefa.
- Análise estática: `ruff check` e `ruff format --check` nos dois módulos focais passaram;
  `git diff --check` passou.
- `curl` no container do piloto confirmou 403 para o Host da bridge e 405 para os Hosts aceitos.
  `docker inspect` confirmou o mesmo container ID, estado `running` e o mesmo mount do volume.
- Container descartável com a imagem fixada, rede `internal`, sem bind de porta e sem mounts:
  GET `/mcp` com Host igual ao IPv4 da bridge retornou 405. A rede e o container descartáveis
  foram removidos; não houve acesso ao volume do piloto.

### Reaplicação 403 — 2026-09-27

#### Diagnóstico do reset e recuperação

- A execução ocorreu em `2026-09-28`. `git reflog -15` mostra `398df22`, o reset de
  `HEAD~1` para `b0a4db8` e o commit seguinte `0094397`. Não reescrevi o histórico.
- No primeiro `git status`, `README.md`, este plano, `src/opencode_config/bootstrap/ai_memory.py`
  e `tests/bootstrap/test_ai_memory_provision.py` estavam modificados. Também havia alterações
  em `plan/insumo-devflow-spawn-dinamico.md`, `plan/plugin-dcp-opencode.md` e o arquivo não
  rastreado `plan/evidencia-revalidacao-spawn-dinamico.md`.
- `git stash list` continha apenas os WIP de atualização do crawl4ai (`92db02c` e `a489979`).
  Nenhum stash correspondia à correção do Host 403.
- Recuperei a correção presente no working tree. O diff do plano alvo já tinha 1.106 adições e
  7 remoções antes deste registro. Não incluí esse diff amplo nem os outros planos nos commits.
  Este bloco permanece no working tree, sem commit isolado.

#### Correção e commits

- `2b41ef7 fix(bootstrap): permite host da bridge no ai-memory` adiciona o IPv4 do container
  à allowlist, valida o endpoint por HTTP e move `.bootstrap-mcp-url` para o diretório de estado.
- O primeiro bootstrap após o rollback criou o container novo, mas o probe HTTP ocorreu antes
  de o servidor ficar pronto. O bootstrap desabilitou MCP. Os logs mostram o servidor pronto
  cerca de 1,2 s após a inicialização.
- Adicionei um teste de regressão para o estado `starting` seguido de `healthy`. O teste falhou
  antes da correção de readiness. `b5705b1 fix(bootstrap): aguarda healthcheck antes do probe MCP`
  aguarda o healthcheck usando a janela configurada pela imagem antes do probe HTTP.
- O módulo focal terminou com 27 testes aprovados. Ruff, `ruff format --check` e
  `git diff --check` passaram. Não executei a suíte completa.

#### Rollback, bootstrap e volume

- Antes do rollback, o container antigo `68c6dc0341d9...` estava healthy e montava
  `/home/vitor/.local/share/ai-memory:/data`. A rede era internal e o marcador legado estava
  no volume. O status informava 88 páginas, 99 versões, 165 sessões e 8.249 observações.
- `bash ./scripts/bootstrap_repo/configurar-repo.sh --rollback-ai-memory` removeu o container
  e a rede. O comando informou que preservou o volume. O diretório continuou com modo `0700`;
  o banco SQLite, a wiki, `hook-spool`, `logs` e `models` permaneceram. O rollback removeu
  apenas o marcador legado `.bootstrap-mcp-url` e os marcadores do bootstrap.
- O bootstrap criou o container novo `434507ce8f7f...` com a imagem fixada
  `sha256:5ce8700b...d221ef6e`, mount original e label `bridge-ip`. Após a correção do probe,
  uma nova execução terminou com `ai-memory provisionado` e MCP declarado nos harnesses.
- O estado final está healthy. `ai-memory status` manteve 88 páginas, 99 versões, 165 sessões
  e 8.249 observações. Não calculei hash nem contagem de arquivos do volume.

#### Validações finais

- O endpoint configurado é `http://172.19.0.2:49374/mcp`. GET retornou HTTP 405 para o IP da
  bridge, `localhost`, `127.0.0.1`, `[::1]` e `host.docker.internal`. Nenhum host aceito
  retornou 403.
- A rede `ai-memory-internal` está com `Internal=true` e contém somente `ai-memory`.
- `docker port ai-memory` não listou bind. `NetworkSettings.Ports` manteve
  `49374/tcp: null` e `ss` não encontrou listener na porta 49374 do host. O Docker conserva
  apenas o pedido de bind loopback em `HostConfig`.
- O marcador atual existe em `~/.local/state/ai-memory/.bootstrap-mcp-url`; o diretório tem
  modo `0700`. O marcador legado não existe no volume.
- `docs/README.md` não exige outro artefato para esta correção. SEC-03 e SEC-21 permanecem
  atendidos. Não alterei `Status` nem os planos paralelos listados nesta tarefa.
- O plugin e as declarações foram atualizados. O processo OpenCode já aberto não foi reiniciado;
  ele precisa ser reiniciado para carregar o plugin gerado.

### TESTES — qa (quadro final) — 2026-09-27

#### Escopo e segurança

- Revalidei RM-1, RM-2, RM-6, RM-10 e a fase A contra a instância corrigida.
- Não executei rollback, bootstrap, upgrade, stop, rm ou gravação no volume do piloto.
  A validação do volume limitou-se a existência, modo `0700` e estrutura.
- Não reiniciei a sessão OpenCode existente. A verificação que depende dessa sessão ficou
  registrada como pós-restart, sem bloquear a evidência dos demais itens.

#### Evidências por passo

**Fase A — PASS na instância corrigida**

- A reaplicação real anterior registrou container novo, imagem aprovada, volume original montado
  e MCP declarado (`Reaplicação 403`, “Rollback, bootstrap e volume”). Não repeti o bootstrap
  para evitar operação de escrita sobre o piloto.
- `docker inspect ai-memory`: container `running`, health `healthy`, imagem com digest
  `5ce8700b…d221ef6e`, label `bridge-ip` e mount original em `/data`.
- `docker exec ai-memory ai-memory status`: serviço respondeu na versão 2.4.1 e informou
  wiki e índice FTS operacionais.
- `opencode mcp list`: `ai-memory` aparece `connected` no endpoint da bridge.
- O volume continua em `~/.local/share/ai-memory/`, modo `0700`, com `db`, `wiki`,
  `hook-spool`, `logs` e `models`. Não comparei hashes nem contagens exatas.

**RM-1 — BLOQUEADO**

- A instalação corrigida atual está saudável, mas não exercitou a transição de upgrade sobre o
  container antigo que RM-1 exige. A reaplicação usou rollback e provisionamento novo.
- Não executei upgrade nem recriação adicional: isso alteraria o estado do serviço que monta o
  volume inviolável. O teste de upgrade permanece sem evidência; não infiro PASS da instalação
  nova.

**RM-2 — PASS**

- `docker port ai-memory` não listou publicação; `NetworkSettings.Ports` mostrou
  `49374/tcp: null`; `ss` não encontrou listener do host na porta 49374.
- O marcador `~/.local/state/ai-memory/.bootstrap-mcp-url` aponta para
  `http://172.19.0.2:49374/mcp`, consistente com o endpoint conectado no OpenCode.
- O endpoint não publica porta no host e a conexão MCP pelo CLI está ativa.

**RM-6 — PASS**

- `docker network inspect ai-memory-internal`: `Internal=true`, somente o container
  `ai-memory` como peer.
- `ai-memory status` respondeu sem erro. GET `/mcp` ao IP da bridge retornou HTTP 405 para
  `172.19.0.2`, `localhost`, `127.0.0.1`, `[::1]` e `host.docker.internal`.
- Controle negativo `Host: qa.invalid:49374` retornou HTTP 403. Assim, a allowlist aceita o
  endpoint corrigido sem aceitar um Host arbitrário.

**RM-10 — POST-RESTART**

- `opencode mcp list` no CLI retornou `ai-memory connected` em
  `http://172.19.0.2:49374/mcp`. A conexão do processo OpenCode já aberto ainda não foi
  validada após reinício.
- Verificação pós-restart do OpenCode: encerrar a sessão atual, abrir uma nova sessão OpenCode
  neste repo, confirmar `opencode mcp list` como `connected` e invocar a ferramenta MCP
  `ai-memory status` nessa sessão. Esperado: retorno de status sem erro, versão 2.4.1.

#### Quadro final RM-1..RM-13

| RM | Resultado | Referência de evidência |
|---|---|---|
| RM-1 | BLOQUEADO | Este bloco, “RM-1”; upgrade do container antigo não foi executado. |
| RM-2 | PASS | Este bloco, “RM-2”; endpoint, porta, listener e MCP conectados. |
| RM-3 | PASS | `TESTES — qa (re-execução)`, RM-3; digest e wrapper aprovados registrados. |
| RM-4 | PASS | `TESTES — qa (re-execução)`, RM-4; segunda execução idempotente registrada. |
| RM-5 | PASS | `TESTES — qa (re-execução)`, RM-5; fallback não usou listener fake. |
| RM-6 | PASS | Este bloco, “RM-6”; rede internal, peer único e probes HTTP. |
| RM-7 | PASS | `TESTES — qa (re-execução)`, RM-7; merge, preservação e restauração. |
| RM-8 | PASS | `TESTES — qa (re-execução)`, RM-8; detecção de upstream sem mudança no checkout. |
| RM-9 | PASS | `TESTES — qa (re-execução)`, RM-9; agente Copilot e caminhos validados. |
| RM-10 | POST-RESTART | Este bloco, “RM-10”; CLI conectado, sessão viva requer reinício. |
| RM-11 | PASS | `TESTES — qa`, RM-11; rollback preservou volume e estrutura. |
| RM-12 | PASS | `TESTES — qa`, RM-12; provisionamento após rollback registrado. |
| RM-13 | PASS | `TESTES — qa`, RM-13; leitura anterior pelo serviço registrada. |

#### Agregador, suíte e evidências

- Não reexecutei `testes-produto` nem `.venv/bin/pytest -m all` nesta revalidação manual.
  Última execução completa registrada: agregador PASS, 904 passed, 31 deselected e cobertura
  de 85%. A execução focal posterior à correção registrou 27 testes aprovados; não há suíte
  completa posterior à correção neste registro.
- Testes manuais revalidados: RM-2 PASS, RM-6 PASS e fase A PASS; RM-1 BLOQUEADO; RM-10
  conectado no CLI, com verificação da sessão viva pendente pós-restart.
- Variação de cobertura versus baseline: não calculável, baseline numérica ausente.
- `docs/README.md#testes-por-especialidade` não exige artefato permanente separado. Não criei
  spec de produto nesta fase.

### TESTES — sec (fechamento) — 2026-09-27

#### Escopo e segurança

- Revalidei sec-1, sec-2, sec-3, sec-6 e sec-9 na instância corrigida.
- Não executei rollback, `docker pull`, parada ou recriação do container. O volume do piloto não
  recebeu comando de escrita. O bootstrap e o healthcheck consultaram o serviço durante a validação.
- O container manteve ID `434507ce8f7f...`, estado `healthy`, digest de imagem
  `5ce8700b...d221ef6e` e mount original. Não calculei hash nem contagem do volume.
- O bootstrap instalou `pytest-cov` durante a verificação automática de dependências. Removi o
  pacote e confirmei que `pip show pytest-cov` não encontra a distribuição.

#### Evidências dos passos revalidados

**sec-1 — PASS, endpoint MCP e publicação**

- `docker port ai-memory` não listou publicação. `NetworkSettings.Ports` mostrou
  `49374/tcp: null`. `ss -ltn '( sport = :49374 )'` não encontrou listener no host.
- `HostConfig.PortBindings` ainda registra o pedido para `127.0.0.1:49374`, mas o Docker não
  publicou a porta. O marcador externo aponta para `http://172.19.0.2:49374/mcp`.
- O diretório `~/.local/state/ai-memory/` tem modo `0700`. O teste passou no fallback de bridge
  previsto para esta instância.

**sec-2 — PASS, integridade do wrapper e da imagem em execução**

- O wrapper instalado tem SHA-256 `49c965a0319dbe9c525d552a9a4c8b3464e5dd278e36d5dc7a03edee8b5502e6`.
- O container executa a imagem fixada em `sha256:5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e`.
- A tag local `latest` ainda resolve para a imagem antiga `ad047...`. O container ativo usa o
  digest aprovado, não a tag local.

**sec-3 — PASS, segunda execução idempotente**

- `bash ./scripts/bootstrap_repo/configurar-repo.sh --yes` terminou com código 0.
- O container manteve o mesmo ID, estado, imagem e digest. O SHA-256 do wrapper permaneceu igual.
- O output não registrou pull nem recriação. O plugin OpenCode apareceu como `no-op`.
- O bootstrap corrigiu o endpoint Copilot de teste para o valor do marcador, sem alterar o mount.

**sec-6 — FAIL, merge Copilot com configuração preexistente**

- A configuração inicial continha somente `ai-memory`. Acrescentei temporariamente
  `sec-preserve-fixture` e substituí a URL gerenciada por `127.0.0.1:49374` para forçar uma escrita.
- Após o bootstrap, `sec-preserve-fixture` continuou presente e `ai-memory` apontou para o endpoint
  atual da bridge. A preservação e a atualização do endpoint passaram.
- O bootstrap anunciou `~/.config/opencode-backup/20260928-090701`, mas não encontrei nesse backup
  uma cópia da configuração Copilot temporária. O diretório ficou vazio e foi removido.
- Restaurei `~/.copilot/mcp-config.json` byte a byte. O SHA-256 final voltou a
  `8d1c2dadbb03c9b614dac6c15be05426e6b13fff4ad3ff529b28b2c82a90d7e9`.

**sec-9 — PASS, rede internal e serviço local**

- `docker network inspect ai-memory-internal` retornou `Internal=true` e um peer, `ai-memory`.
- GET `/mcp` ao endereço da bridge retornou HTTP 405 para `172.19.0.2`, `localhost`, `127.0.0.1`,
  `[::1]` e `host.docker.internal`. O controle `sec-check.invalid:49374` retornou HTTP 403.
- `docker port` não listou bind efetivo. O marcador ficou fora do volume do piloto, no diretório
  restrito `~/.local/state/ai-memory/`.

#### Quadro final do roteiro manual sec

| Passo | Resultado | Evidência |
|---|---|---|
| sec-1 | PASS | Fallback bridge ativo, sem porta publicada nem listener no host. |
| sec-2 | PASS | SHA do wrapper e digest da imagem em execução conferidos. |
| sec-3 | PASS | Bootstrap repetido sem recriação; ID, imagem e wrapper estáveis. |
| sec-4 | PASS | Evidência anterior em `TESTES — sec`, teste de porta ocupada. |
| sec-5 | PASS, ressalva | Rollback anterior preservou estrutura; comparação byte a byte ficou inconclusiva. |
| sec-6 | FAIL | Fixture preservada e endpoint corrigido; backup Copilot não localizado. |
| sec-7 | PASS | Evidência anterior em `TESTES — sec`, detecção de upstream. |
| sec-8 | PASS | Evidência anterior em `TESTES — sec`, cópia do agente Copilot. |
| sec-9 | PASS | Rede internal, peer único, probes HTTP e marcador externo conferidos. |

Resultado consolidado: 8 PASS, 1 FAIL e 0 BLOQUEADOS. Os passos sec-4, sec-5, sec-7 e sec-8
mantêm evidência anterior e não foram repetidos nesta validação.

#### Achados

- **Achado:** o bootstrap atualizou `mcp-config.json` sem cópia de backup Copilot localizada.
  **Ação:** gerar backup antes da escrita e cobrir o arquivo Copilot no teste de merge.
  **Severidade:** melhoria. O teste preservou a entrada não gerenciada e não demonstrou perda de dados.

#### POST-RESTART, não bloqueante

- **RM-10:** após reiniciar o OpenCode, abrir uma sessão nova neste repo, confirmar
  `opencode mcp list` como `connected` e invocar `ai-memory status` pela ferramenta MCP.
  A conexão do processo OpenCode já aberto não foi validada nesta execução.

### Evidências (sec) — Testes

- [x] Revalidação de cinco passos bloqueados: 4 PASS, 1 FAIL e 0 BLOQUEADOS.
- [x] Quadro completo sec-1..sec-9: 8 PASS e 1 FAIL. Quatro PASS vieram da evidência anterior.
- [x] Estado provisionado restaurado: mesmo container, imagem, mount, marcador e configurações ativas.
- [x] Configuração Copilot restaurada com SHA-256 original; fixture de teste não permaneceu ativa.
- [x] Nenhuma suíte automática foi executada; o escopo ficou restrito ao roteiro manual de segurança.
- [x] `docs/README.md#testes-por-especialidade` consultado. Nenhuma spec de produto foi criada ou
  alterada nesta fase.
- [ ] sec-6: backup Copilot antes da escrita não foi localizado; melhoria registrada acima.
- [ ] POST-RESTART RM-10: validar a sessão OpenCode nova após reinício; não bloqueia este fechamento.
- [x] Achados: 1 melhoria, 0 bloqueantes.

### TESTES — curador (validação) — 2026-09-27

#### Resultado da validação

- Veredicto: **EVIDÊNCIA INVÁLIDA** para fechar a fase Testes.
- Não executei suítes. A validação cobre `docs/README.md#testes-por-especialidade`
  e os blocos de teste deste ciclo.
- A execução completa registrada passou antes das correções posteriores de porta MCP,
  Host 403 e readiness. Falta uma execução completa do agregador sobre o estado final.

#### Agregador e execução automatizada

- O último resultado registrado do agregador é `{"status":"pass","findings":[]}`.
  O comando usado nas execuções válidas foi:

  ```bash
  JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/python testes-produto
  ```
- O registro associa a retomada após `d646b41` a 904 testes aprovados, 31 deselected,
  188,03 s e cobertura total de 85%. Uma execução anterior registrou 903 aprovados,
  31 deselected e 213,08 s. O agregador não emitiu contagem, duração ou cobertura
  no JSON; esses números vêm da execução direta de `pytest` e do relatório `.coverage`.
- A flakiness inicial está documentada: duas execuções agregadas tiveram 16 errors
  em `test_repo_state.py`; três execuções isoladas e duas suítes completas diretas
  passaram. A hipótese registrada é falha transitória da fixture em subprocesso,
  possivelmente por ordem ou estado compartilhado. A causa raiz não foi confirmada.
- **Achado:** a última execução completa antecede correções posteriores e a reexecução
  final dos roteiros. **Ação:** `qa` deve executar `testes-produto` e a suíte completa
  no estado final, registrando comando, JSON, contagens, duração e cobertura.
  **Severidade:** bloqueante para validar o gate da fase.

#### Roteiros manuais

- O quadro final do QA lista RM-1 como BLOQUEADO, RM-10 como POST-RESTART e os demais
  estados de RM-1..RM-13. Os resultados apontam para evidências anteriores ou para
  detalhes no próprio quadro. RM-1 não foi inferido como PASS da instalação nova.
- RM-1 continua sem teste de upgrade sobre o container antigo, para não alterar o
  serviço que monta o volume protegido. A conclusão exige decisão humana sobre a
  transição segura; depois, `qa` registra a execução ou o impedimento aprovado.
- RM-10 tem procedimento pós-restart explícito: abrir nova sessão, confirmar
  `opencode mcp list` e chamar `ai-memory status`. O humano ainda precisa reiniciar
  o OpenCode; `qa` registra o resultado nessa sessão.
- O quadro final de segurança registra sec-1..sec-9, com oito PASS e sec-6 FAIL.
  O FAIL tem severidade melhoria: não foi localizado backup Copilot, embora a entrada
  tenha sido preservada e a configuração original restaurada. A ação proposta é gerar
  o backup antes da escrita e cobrir esse arquivo no teste de merge.
- Os estados e suas evidências são rastreáveis nos blocos `TESTES — qa`,
  `TESTES — qa (re-execução)`, `TESTES — qa (quadro final)`, `TESTES — sec` e
  `TESTES — sec (fechamento)`. Não há achado high/critical aberto nesses quadros.

#### Critérios de aceite CA-T1..CA-T8

- **CA-T1, PENDENTE:** agregador passou com `findings=[]`, antes das correções posteriores.
  `qa` deve reexecutá-lo no estado final.
- **CA-T2, PENDENTE:** 904 passed e 31 deselected foram registrados em `-m all`.
  Falta repetir a suíte após as correções posteriores.
- **CA-T3, PENDENTE:** Concordion passou na suíte completa registrada.
  Falta confirmar na execução completa final.
- **CA-T4, PARCIAL:** cobertura de 85% supera 70%. Sem baseline numérica, não foi
  possível verificar ausência de queda. `qa` deve registrar a baseline e o delta.
- **CA-T5, PENDENTE:** há registro por passo. RM-1 continua bloqueado e RM-10 aguarda
  restart. Resolver RM-1 com decisão humana e concluir RM-10 após restart.
- **CA-T6, PENDENTE:** T1-T15 passaram na execução completa registrada.
  Falta revalidar os testes no estado final. A suíte meta não se aplica.
- **CA-T7, ATENDIDO:** não houve mudança nos scripts de `testes-produto`.
  A suíte meta não precisava rodar.
- **CA-T8, NÃO ATENDIDO:** a evidência está nos blocos do ciclo, mas não existe
  `## Evidências de Testes — Testes`. `curador-produto` deve reconciliar o destino
  com aprovação humana.

#### Divergências e encaminhamentos

- **Achado:** execução completa desatualizada após mudanças no bootstrap. **Ação:**
  `qa` executa agregador e suíte completa no estado final. **Severidade:** bloqueante.
- **Achado:** baseline de cobertura ausente. **Ação:** `qa` registra baseline e delta;
  se a baseline não existir, o humano decide como tratar CA-T4, sem dispensar o critério
  por iniciativa do agente. **Severidade:** lacuna de evidência.
- **Achado:** o destino exigido por CA-T8 não existe. **Ação:** `curador-produto`
  propõe a reconciliação entre o destino do critério e os blocos existentes, sob
  aprovação humana. **Severidade:** lacuna de documentação.
- **Achado:** sec-6 falhou no backup Copilot. **Ação:** `eng-software` corrige o backup
  e `sec` revalida o roteiro e o teste de merge. **Severidade:** melhoria.
- **Achado:** RM-1 e RM-10 seguem sem conclusão. **Ação:** o humano decide sobre a
  transição que afeta o volume e reinicia o OpenCode; `qa` registra os resultados.
  **Severidade:** gate pendente.

### TESTES — qa (re-execução final) — 2026-09-27

#### Escopo e proteção do piloto

- Executor: `opencode/gpt-6-luna`; HEAD: `b5705b1`.
- Execução final: 2026-09-28; o título mantém a data solicitada para o bloco.
- Não executei rollback, bootstrap, upgrade, stop, rm ou escrita no volume do piloto.
- RM-1 permanece BLOQUEADO pela proteção do volume. RM-10 permanece POST-RESTART; não reiniciei
  o processo OpenCode nesta execução.
- Não alterei `Status` nem os planos paralelos.

#### Agregador `testes-produto`

- Primeira execução: `JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/python testes-produto`.
  Duração: 53,282 s. Retorno `status=fail`; pytest rejeitou `--cov=src`, `--cov=scripts`,
  `--cov=testes-produto`, `--cov-report=term-missing` e `--cov-fail-under=70` porque `pytest-cov`
  não estava instalado. `pip show` confirmou a ausência; `pytest` era 9.1.1.
- Diagnóstico e recuperação do ambiente: `requirements-dev.txt` declara `pytest-cov>=5,<8`.
  Instalei somente essa dependência na `.venv` com
  `.venv/bin/python -m pip install 'pytest-cov>=5,<8'`; versão instalada: 7.1.0.
  Nenhum arquivo do repo foi alterado por essa instalação.
- Reexecução válida: `JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/python testes-produto`.
  Duração: 258,424 s. Saída: `{"status":"pass","findings":[{"severity":"melhoria",
  "tool":"bandit","message":"...ai_memory.py:1017: Audit url open for permitted schemes..."}]}`.
- Resultado: status `pass`, nenhum finding bloqueante; permanece uma melhoria Bandit na linha 1017
  de `src/opencode_config/bootstrap/ai_memory.py`. O agregador não informa contagens de testes.

#### Suíte completa e cobertura

- Comando: `JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest -m all`.
- Resultado: 947 itens coletados, 916 selecionados; 916 passed, 31 deselected, 0 failed.
  Pytest informou 191,51 s; duração de parede medida pelo shell: 193,588 s.
- `tests/product_tests/test_concordion_spec_infra.py` passou dentro da suíte completa.
  Os testes T1-T15 cobertos pela seleção `-m all` passaram.
- Relatório de cobertura: 85% (4.405 statements, 646 missed), acima do gate de 70%.
  A execução anterior registrada também mediu 85%; a variação aritmética para essa observação é
  0 ponto percentual. O plano não definiu essa observação como baseline formal; o delta contra uma
  baseline aprovada continua indisponível. CA-T4 fica PARCIAL, aguardando decisão humana.

#### Suíte meta

- Executei `git diff 098a5b6..HEAD -- testes-produto/`; não houve saída nem arquivos alterados.
- Os scripts do agregador e das suítes não mudaram no intervalo. Suíte meta
  `testes-produto/tests/`: não aplicável, não executada.

#### CA-T1..CA-T8

| Critério | Resultado | Evidência desta reexecução |
|---|---|---|
| CA-T1 | PASS | Agregador `status=pass`; zero findings bloqueantes. Uma melhoria Bandit permanece. |
| CA-T2 | PASS | 916 passed, 0 failed e 31 deselected em `-m all`. |
| CA-T3 | PASS | Spec Concordion passou na suíte completa. |
| CA-T4 | PARCIAL | Cobertura 85%, referência anterior 85% (delta informativo: 0 p.p.); baseline formal ausente. |
| CA-T5 | PENDENTE | RM-1 BLOQUEADO e RM-10 POST-RESTART seguem documentados, sem reexecução. |
| CA-T6 | PASS | Suíte completa verde, incluindo os testes T1-T15 selecionados. |
| CA-T7 | PASS | Sem alterações nos scripts; suíte meta não aplicável. |
| CA-T8 | PASS | Evidência persistida na seção `## Evidências de Testes — Testes` criada após este bloco. |

RM-10 só pode ser concluído após reinício humano do OpenCode. Passo exato: encerrar a sessão atual,
abrir uma nova sessão OpenCode neste repo, executar `opencode mcp list` e confirmar `ai-memory
connected`; depois invocar a ferramenta MCP `ai-memory status` e confirmar retorno sem erro,
versão 2.4.1.

## Evidências de Testes — Testes

- [x] Plano de testes: cenários RM-1..RM-13 e testes T1-T15 definidos nos blocos anteriores.
- [x] Testes executados: agregador `pass` sem finding bloqueante; 916 selecionados, 916 passaram,
  31 ficaram deselected e 0 falharam na suíte completa.
- [x] Cobertura: 85%; observação anterior 85%, diferença informativa de 0 p.p.; baseline formal
  ausente, decisão sobre CA-T4 pendente do humano.
- [x] Cenários não cobertos: RM-1 segue BLOQUEADO para proteger o volume; RM-10 aguarda o passo
  pós-restart descrito no bloco `TESTES — qa (re-execução final)`.
- [x] Suíte meta: não aplicável, sem mudanças em `testes-produto/` no intervalo `098a5b6..HEAD`.

### TESTES — curador (revalidação) — 2026-09-27

#### Resultado da revalidação

- Veredicto: **EVIDÊNCIA VÁLIDA (com anotações)** para a validação evidencial da fase Testes.
- A reexecução do QA registra HEAD `b5705b1`, agregador `pass` e suíte completa verde.
- CA-T5 continua operacionalmente pendente. Este veredicto confirma a presença e a rastreabilidade
  da evidência, não declara RM-1 ou RM-10 concluídos.

#### Agregador e suíte completa

- O agregador foi executado no HEAD final com o comando registrado no bloco do QA. O JSON retorna
  `status=pass`, sem finding bloqueante. A melhoria Bandit permanece não bloqueante.
- A suíte completa coletou 947 itens: 916 passaram, 31 ficaram deselected e 0 falharam.
  A soma 916 + 31 corresponde aos 947 itens coletados.
- A contagem final aumentou em 12 testes aprovados em relação aos 904 registrados antes das
  correções. Essa diferença é coerente com o lote informado.
- CA-T1, CA-T2, CA-T3 e CA-T6 estão atendidos pela reexecução final. CA-T8 também está atendido,
  pois a seção `## Evidências de Testes — Testes` consta no plano.
- CA-T7 permanece atendido. O QA registrou que os scripts não mudaram e que a suíte meta não se
  aplica neste intervalo.

#### CA-T4, cobertura

- Registro a cobertura de 85% da primeira medição completa documentada no ciclo como
  **BASELINE INICIAL**. A medição final também foi 85%, com delta de 0 p.p. A cobertura supera o
  gate de 70%.
- Não há histórico de cobertura anterior ao ciclo para comparação retrospectiva. Com essa
  anotação explícita, CA-T4 fica atendido; não falta ação adicional de `qa` para este critério.

#### CA-T5, roteiros manuais

- RM-1 está registrado como BLOQUEADO pela proteção do volume. Não houve operação no volume do
  piloto. O estado e a razão estão explícitos, sem conversão indevida para PASS.
- RM-10 está registrado como POST-RESTART. O passo definido exige nova sessão OpenCode, consulta
  a `opencode mcp list` e chamada de `ai-memory status`, com conferência da versão 2.4.1.
- Os dois estados têm rastreabilidade nos blocos do QA e na seção de evidências. CA-T5 continua
  PENDENTE até a decisão humana sobre RM-1 e a execução de RM-10 após o reinício.
- Não restam lacunas de evidência para CA-T1, CA-T2, CA-T3, CA-T4, CA-T6, CA-T7 ou CA-T8.

## Backlog pós-ciclo 2 (consolidado em 2026-09-27)

Dívidas aprovadas pelo humano ("tudo vira backlog"). Os itens 1-7 foram
resolvidos na finalização. O item 8 permanece para execução do humano após o
reinício do OpenCode.

1. **sec-6 — RESOLVIDO:** o adapter cria backup adjacente com timestamp, imprime o
   caminho antes da gravação e preserva o conteúdo anterior.
2. **RM-1 — RESOLVIDO por substituição:** não há container antigo; o ativo usa a
   imagem aprovada e mantém o mount de dados.
3. **Ruff 25 — RESOLVIDO:** removidos os achados F541/F401/F841 descritos no bloco
   E12, sem mudança de semântica.
4. **Revisão, achado 6 — RESOLVIDO:** helpers ai-memory compartilhados movidos para
   `src/opencode_config/lib/`; os adapters não importam mais de bootstrap.
5. **Revisão, achado 7 (processo), RESOLVIDO:** subseções de registro do
   plano identificam agente executor e modelo.
6. **Flaky, 16 errors, RESOLVIDO:** diagnóstico encerrado; a causa exata não
   foi confirmada. A análise e as reproduções estão no bloco de finalização.
7. **Processo de spec, RESOLVIDO:** specs tabulares exigem fixtures que leem
   os valores das tabelas, sem codificá-los à parte.
8. **Pós-restart, PENDENTE DO HUMANO:** reiniciar o OpenCode para validar RM-10
   (MCP ai-memory vivo na sessão) e carregar adapters atualizados.

## Ciclo 2 — FINALIZAÇÃO

### Revisão final dos artefatos de spec — curador-produto — 2026-09-28

Escopo: revisão do `docs/README.md`, dos blocos E11/E11(b) e Testes, dos ADRs 0007-0009,
de `docs/specs/Seguranca.md`, do destino `docs/specs/regras-negocio.md` e da seção de dependências
do `README.md`. Não alterei `Status`, planos paralelos ou artefatos de código/domínio. Não executei
testes; usei a evidência final registrada na seção Testes.

### Achados, ações e severidade

1. **Testes por Especialidade — conforme.** `docs/README.md` define backend e segurança, o agregador,
   a interface JSON e os dois níveis de teste. O nível 2 fica em `testes-produto/tests/`, fora de
   `-m all`, e roda apenas quando os scripts mudam. O QA registrou que não houve mudança em
   `testes-produto/`; não executar a suíte meta neste ciclo está correto.
   **Ação:** nenhuma. **Severidade:** sem achado.

2. **ADRs 0007-0009 — convenção referenciada; um link interno está desatualizado.** A subseção
   `ADR (Arquitetura)` do `docs/README.md` registra os ADRs legados 0001-0006 no passado e exige a
   mesma convenção para 0007-0009. Os três arquivos existem em `docs/adr/` e incluem asserções
   executáveis. A convenção não exige índice adicional no README, conforme E11(b). Porém, o ADR-0007
   aponta para `tests/skills_mgmt/test_detect.py`, caminho inexistente; o teste atual fica em
   `tests/skills_mgmt/test_upstream_detect.py`.
   **Ação:** `eng-software` corrigir a referência no ADR-0007.
   **Severidade:** melhoria documental.

3. **Spec de segurança — lacuna entre contrato documentado e estado implementado.**
   `docs/specs/Seguranca.md` registra o SHA fixo do wrapper, mas não os pins aprovados no fechamento:
   wrapper `v2.4.1`, SHA-256 `49c965a0319dbe9c525d552a9a4c8b3464e5dd278e36d5dc7a03edee8b5502e6`;
   índice OCI `a626d115e0350afe934954c02c9064d30b708c58316763a9c6674ef5d0c8e3d9`; imagem linux/amd64
   `5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e`. SEC-03 descreve publicação
   somente em loopback, mas não registra o fallback sem publicação, pelo endpoint IPv4 privado da
   bridge internal. A spec também não registra `.bootstrap-mcp-url` em
   `~/.local/state/ai-memory/`, fora do volume de dados. O código e os testes cobrem os três pontos.
   **Ação:** `sec` atualizar a spec após a decisão SEC→spec; `eng-software` alinhar fixture e asserções
   Concordion após a aprovação humana. A aprovação permanece pendente em `## Perguntas`.
   **Severidade:** bloqueante para encerrar a revisão dos artefatos de spec.

4. **Regras de Negócio — artefato ausente.** `docs/specs/regras-negocio.md` não existe. A validação
   inicial classificou a ausência como lacuna, e a resposta humana registrada em 2026-09-24 decidiu
   criar o arquivo neste ciclo, com tarefa atribuída à curadoria. Não é uma decisão humana pendente.
   **Ação:** `curador-produto` criar o artefato com base em regras aprovadas; se não houver fonte
   aprovada, encaminhar a elicitação ao `analista` e ao humano, sem inferir regras.
   **Severidade:** lacuna de documentação, impede encerrar a revisão.

5. **README principal — dependências listadas; descrição do pin incompleta.** A tabela lista
   `pytest-cov` na `.venv` via `requirements-dev.txt`; o arquivo declara `pytest-cov>=5,<8`, e o
   bootstrap instala o pacote no ambiente da suíte. A entrada de ai-memory identifica Docker como
   pré-requisito, e a seção anterior explica provisionamento e hooks pelo bootstrap. Porém, a seção
   ai-memory diz apenas que a imagem usa `:latest`; o bootstrap agora acrescenta o digest da plataforma
   linux/amd64 à referência.
   **Ação:** `eng-software` explicitar no README a referência `latest@sha256` aprovada, sem alterar
   código ou reabrir a decisão de pin.
   **Severidade:** melhoria documental.

### Veredicto

**Lacunas a corrigir antes do encerramento.** A seção de testes e a convenção dos ADRs estão
conformes. O destino de Regras de Negócio continua ausente, e a spec de segurança não cobre os pins,
o endpoint via bridge nem o marcador externo de estado. A aprovação SEC→spec também continua pendente.
Não editei `docs/README.md`: a correção prevista em E11(b) já está aplicada e a subseção está
conforme.

### Correções finalização (eng) — 2026-09-27

- Atualizei `docs/specs/Seguranca.md` para descrever o wrapper `v2.4.1`, os
  digests da imagem, o endpoint IPv4 da bridge, a allowlist de Host e o marcador
  fora do volume. Mantive as verificações SEC-03 e SEC-21.
- Alinhei `SegurancaFixture.groovy` aos literais documentados, ao código e aos
  testes que cobrem os pins, o fallback, a allowlist e o marcador.
- Corrigi no ADR-0007 o caminho para `tests/skills_mgmt/test_upstream_detect.py`.
- Registrei no `README.md` a referência da imagem com digest linux/amd64.
- A instrução de finalização aprovou o alinhamento SEC→spec solicitado pelo
  curador-produto.
- Não criei `docs/specs/regras-negocio.md`; essa ação permanece com
  `curador-produto`.
- Evidências: `.venv/bin/pytest tests/bootstrap/test_ai_memory_provision.py
  -m all -q` passou com 27 testes; `JAVA_HOME=/home/vitor/.local/share/jdk
  gradle test -PproductSpecialty=seguranca --no-daemon` concluiu com
  `BUILD SUCCESSFUL`; `git diff --check` passou.
- Não alterei `Status` nem os planos paralelos.

### Revalidação finalização - 2026-09-27

Escopo: revalidação dos achados da revisão final e criação de
`docs/specs/regras-negocio.md`. Não executei suítes, não alterei `Status` e
não toquei nos planos paralelos.

### Checklist de evidências de curadoria

- [x] Spec de segurança: `Seguranca.md` e `SegurancaFixture.groovy` conferem
      pins, fallback da bridge, allowlist e marcador externo com `ai_memory.py`
      e os testes existentes.
- [x] Link do ADR-0007: o ADR aponta para
      `tests/skills_mgmt/test_upstream_detect.py`, que existe.
- [x] Digest no README: a referência linux/amd64 em `README.md` coincide com
      `ai_memory.py` e `Seguranca.md`.
- [x] Regras de Negócio: `docs/specs/regras-negocio.md` existe e registra
      decisões do plano, ADRs, specs e testes existentes.
- [x] Consistência integral das regras: ADR-0008 registra a decisão humana de
      2026-09-27, o efeito do digest linux/amd64 e os upgrades explícitos.
- [x] Suítes: não executei nenhuma suíte nesta revalidação, conforme a instrução.

### Achado

1. **ADR-0008 atualizado conforme o Achado 1.** A decisão registra a aprovação
   humana de 2026-09-27 para “usar a versão nova” e identifica os digests da
   plataforma e do índice OCI. As consequências dizem que `latest` não atualiza
   a imagem implicitamente e que upgrades exigem decisão humana, revalidação de
   segurança e atualização explícita dos pins. A asserção executável nomeia
   `test_ai_memory_upstream_release_pins_match_reviewed_artifacts`.

### Veredicto

**OK PARA ENCERRAR.** O ADR-0008 registra a decisão humana, o efeito do digest
fixado e as condições explícitas para upgrades. A asserção executável também
aponta para a verificação dos pins revisados. Não executei suítes, conforme a
instrução.

### Fechamento docs (eng): 2026-09-27

Escopo: resolvi a lacuna do Achado 1 da revalidação final. Não alterei código
nem a fixture Concordion do ADR-0008.

- O ADR-0008 registra a decisão humana de 2026-09-27, “usar a versão nova”,
  após a revalidação do `sec`, com o digest linux/amd64 e o digest do índice OCI.
- As consequências registram que a tag `latest` não atualiza a imagem
  implicitamente. Upgrade exige decisão humana, revalidação de segurança e
  atualização explícita dos pins do wrapper, do índice OCI e da plataforma.
- A seção “Asserções executáveis” aponta para
  `test_ai_memory_upstream_release_pins_match_reviewed_artifacts`. A fixture
  Concordion não mudou, então não executei o Gradle da especialidade segurança.
- O commit deste fechamento inclui o ADR-0008, o arquivo
  `docs/specs/regras-negocio.md` criado pelo curador e este plano, que registra
  somente atividades do ciclo 2.
- `git diff --check` passou. A largura das linhas alteradas ficou em até 120
  colunas. Não alterei os planos paralelos excluídos do escopo.

### Pacote final (workflow+skills) — 2026-09-27

Escopo: pacote de ajustes de workflow, agentes e skills aprovado pelo humano
em 2026-09-27. Mantive o campo `Status` sem alteração.

#### Aplicações

- Substituí a premissa 7 pela redação aprovada e alinhei a seleção por chamada,
  a troca manual condicionada e a política de sessão no agente `devflow`.
- Esclareci sinais de conclusão, espera progressiva, tetos de timeout e
  inatividade de streams/logs; movi exemplos para `references/` na skill.
- Adaptei os comandos pre-commit ao pytest/ruff do repo e removi a sugestão de
  `git reset --hard HEAD`.
- Ampliei a description do `humanizer-br` para comunicação geral de chat e
  atualizei `description_note`, mantendo `description_lang: pt-br`.
- Registrei gatilhos para `planning-and-task-breakdown` e `writing-for-agents`,
  sem mudar permissões; esclareci a precedência de formatação mecânica e a
  regra de aprovação de conteúdo.

#### Arquivos

- `docs/workflow-agentes-dev.md`
- `harness-conf/agents/devflow.md`
- `harness-conf/agents/eng-software.md`
- `harness-conf/agents/smart-planner.md`
- `AGENTS.md`
- `harness-conf/AGENTS.base.md`
- `harness-conf/skills/reliable-async-operations/SKILL.md`
- `harness-conf/skills/reliable-async-operations/references/exemplos-por-categoria.md`
- `harness-conf/skills/git-workflow-and-versioning/SKILL.md`
- `harness-conf/skills/humanizer-br/SKILL.md`
- `harness-conf/skills/humanizer-br/UPSTREAM.md`
- `plan/otimizacao-custo-contexto.md`

#### Evidências

- `.venv/bin/pytest tests/agents/ tests/skills/ tests/skills_mgmt/ -m all`:
  347 passaram.
- `git diff --check`: passou.
- `tests/agents/` incluiu consistência e largura; nenhuma linha excedeu 120
  colunas nos arquivos de agente e em `harness-conf/AGENTS.base.md`.
- Largura: `tests/agents/` passou; as demais linhas novas do pacote ficaram em
  até 120 colunas. Nenhum arquivo Python mudou; ruff não se aplica.
- Consultei `docs/README.md`; o pacote não exige novo artefato de spec ou ADR.

#### Commits

- `9691c68` `docs(workflow): alinha seleção de modelo e sessões novas`
- `1bdfe30` `docs(agents): registra gatilhos e precedência de escrita`
- `77d0b99` `docs(skills): clarifica espera e move exemplos assíncronos`
- `f46e294` `docs(skills): adapta comandos pre-commit ao repo`
- `b3d6936` `docs(skills): amplia uso geral do humanizer`
- Este registro: `docs(plan): registra pacote final workflow e skills`.

### Pacote final (spec segurança) — 2026-09-27

#### Auditoria da causa raiz

- Sim, a task E10 pediu converter SEC-01..SEC-11 e SEC-21 em asserções da spec executável
  `docs/specs/Seguranca.md`. O briefing não exigiu carregar `spec-executavel` nem definiu que a
  fixture leria os valores das tabelas.
- A skill existia: a auditoria E7, em 2026-09-27, a lista entre as skills locais. O registro E10
  não informa se ela foi carregada. Não há evidência de omissão deliberada ou pressa.
- A causa comprovada foi uma lacuna no protocolo e na validação: a spec usava links `#execute=...`
  e `#assertEquals=...`, que Concordion-Markdown tratava como links comuns. Gradle reportou
  `Successes: 0, Failures: 0`. A fixture guardava valores à parte, em Groovy, e a guarda pytest
  validava presença de IDs e links, não a ligação spec → teste.

#### Correção aplicada

- Reescrevi `docs/specs/Seguranca.md` com tabelas de entrada e resultado esperado para cada SEC.
  As tabelas contêm URLs, hashes, digests, bind, hosts, caminhos e demais valores usados nos testes.
- Troquei os links fragmentados pela sintaxe Concordion-Markdown executável. O veredito agora muda
  quando a fixture rejeita um valor da tabela.
- Atualizei `src/test/groovy/SegurancaFixture.groovy` para ler cada tabela e comparar seus valores
  com código, configuração e testes. A fixture não mantém cópias dos valores de release, hashes,
  digests, porta, hosts ou marcador.
- Atualizei `tests/bootstrap/test_ai_memory_provision.py` para validar a estrutura das tabelas,
  conferir os valores contra o bootstrap e exigir links Concordion válidos para as 12 verificações.
- Consultei `docs/README.md` e `harness-conf/agents/references/principios-documentacao.md`.
  Mantive a spec no destino existente e não criei outro artefato ou ADR.

#### Gate de refatoração

- Sem alteração de comportamento do bootstrap ou decisão de domínio. Corrigir a sintaxe Concordion
  foi necessário para executar as asserções previstas em E10. Não criei ADR.

#### Evidências de Testes — FINALIZAÇÃO (spec segurança)

- [x] RED: o novo teste falhou antes da criação das tabelas, com 1 failed e 27 deselected.
  A guarda da sintaxe Concordion também falhou com 2 failed e 26 deselected antes da correção.
- [x] Mutação: trocar temporariamente a porta da tabela SEC-03 de `49374` para `49375` fez o
  Gradle falhar. Restaurei `49374` e a execução final passou.
- [x] Pytest: `.venv/bin/pytest tests/bootstrap/test_ai_memory_provision.py -m all -q`,
  28 passed.
- [x] Concordion: `JAVA_HOME=/home/vitor/.local/share/jdk gradle -q test
  -PproductSpecialty=seguranca --no-daemon`, 3 fixtures passaram. `SegurancaFixture` reportou
  14 sucessos e 0 falhas.
- [x] Ruff check e format passaram no módulo pytest. `git diff --check` passou. Nenhuma linha
  alterada excede 120 colunas.
- [x] Sem mudanças no bootstrap de produção. Não executei `git push`.

### Backlog código — 2026-09-27

#### sec-6: backup visível da configuração Copilot

- **Feito:** o adapter cria `mcp-config.json.<timestamp>[.<n>].bak` ao lado da
  configuração, imprime o caminho antes da gravação e preserva os bytes originais.
- **Testes:** RED reproduzido no teste de merge. GREEN: 37 testes de
  `tests/harnesses/test_copilot.py` e 44 testes de `tests/lib/` passaram.
  O Gradle direcionado a SEC-10 excedeu o limite de 30 s durante a primeira
  tentativa.
- **Commit:** `f52e00b feat(bootstrap): preserva backup verificável da configuração Copilot`.

#### Revisão, achado 6: helpers compartilhados de ai-memory

- **Feito:** `filter_ai_memory_config` e `is_ai_memory_provisioned` passaram para
  `lib/ai_memory.py`, junto das dependências usadas pelos dois adapters. Os
  adapters não importam mais `bootstrap.ai_memory`.
- **Testes:** RED confirmado para o módulo novo e para a fronteira de imports.
  GREEN: 35 testes de `tests/lib/test_ai_memory.py` e
  `tests/bootstrap/test_ai_memory_provision.py`, 21 de OpenCode e 37 de Copilot.
- **Gate de refatoração:** sem mudança de comportamento ou do plano. ADR-0004
  revisado; a mudança segue a camada `lib` existente. Nenhum ADR novo.
- **Commit:** `71e7557 refactor(lib): centraliza helpers compartilhados de ai-memory`.

#### Ruff 25

- **Feito:** removidos os 25 achados F541, F401 e F841 listados no E12, sem
  alterar o texto das mensagens nem os efeitos das chamadas.
- **Testes:** `ruff check .` passou. Os módulos de teste tocados passaram com
  52 e 10 testes, respectivamente.
- **Commit:** `80a9d52 style(tests): corrige 25 avisos do Ruff`.

#### RM-1: container antigo do piloto

- **Feito:** a consulta `docker ps -a --filter name=ai-memory` encontrou apenas o
  container `ai-memory` ativo. O container usa o digest aprovado e monta
  `/home/vitor/.local/share/ai-memory` em `/data`. RM-1 foi encerrado por
  substituição; nenhum container foi removido e o volume não foi acessado.
- **Verificação:** `docker inspect` consultou metadados do container. Nenhum
  arquivo em `~/.local/share/ai-memory/` foi lido ou alterado.
- **Commit:** incluído no fechamento documental deste plano.

#### Validação final

- [x] `JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest -m all`: 926 testes passaram,
  31 `agent_eval` foram deselecionados, 0 falhas. O pytest reportou 217,00 s; tempo
  de parede, 219,82 s.
- [x] Gradle da especialidade segurança: 3 testes passaram, 0 falhas. `SegurancaFixture`
  reportou 14 sucessos e 0 falhas. Tempo de parede: 22,36 s.
  Comando:
  `JAVA_HOME=/home/vitor/.local/share/jdk gradle -q test -PproductSpecialty=seguranca --no-daemon`.
- [x] `ruff check .` e `git diff --check` passaram.
- [x] Corrigi a vírgula final da assinatura Groovy e a interpolação literal de
  `${prefixoSaida}` na asserção SEC-10. As execuções finais passaram.
- [x] Commits de código: `71e7557`, `f52e00b` e `80a9d52`, nas unidades descritas acima.
- [x] Fechamento documental registrado em
  `docs(plan): registra validação final do backlog de código`.

#### Observação fora do escopo

- `Adr0006Fixture` e `Adr0008Fixture` também reportam `Successes: 0` no Gradle. As specs desses
  ADRs ainda usam os links antigos; não as alterei porque este pacote cobre `Seguranca.md`.
- `ruff format --check .`, execução adicional, reportou 92 arquivos não formatados. Não apliquei
  formatação em massa; a configuração do repo define Ruff lint, e o comando não consta como gate.

#### Commit documental anterior

- `aff0c73 docs(spec): alinha Seguranca.md ao protocolo spec-executavel`.

### Backlog processo — 2026-09-27

Executor: `eng-software` / `opencode-go/gpt-6-luna`.

- **Item 6, flaky, diagnóstico concluído:** os agregadores #1 e #3 registraram
  `887 passed`, `31 deselected` e `16 errors` em
  `tests/scripts/bootstrap_repo/test_repo_state.py`, após 260,02 s e 236,37 s.
  Os agregadores #2 e #4 passaram; três execuções isoladas do módulo passaram.
  O registro do QA não preserva node IDs, traceback ou mensagem específica.
- **Análise estática:** os 16 testes do módulo dependem da fixture
  `bootstrapped_repo_state`, de escopo `module`. A fixture executa o adapter em
  subprocesso antes dos testes; uma falha no setup gera erro para cada consumidor.
  `repo_root` tem escopo `session`; o HOME temporário usa PID e UUID, fica sob a
  raiz do repo e é removido no teardown. O primeiro teste executa o adapter de
  novo, depois do setup. O pytest não carregou xdist; o plugin observado foi
  `cov`. Não encontrei estado compartilhado externo ou vazamento de ambiente que
  explique os dois agregadores com erro.
- **Conclusão:** o gatilho exato não foi confirmado. Causa plausível: falha
  transitória do subprocesso inicial do adapter no ambiente do agregador,
  amplificada aos 16 testes pela fixture de módulo. A hipótese de corrida na
  coleta não foi comprovada. O finding não contém dados para atribuir o gatilho.
- **Reprodução, limite 2, em 2026-09-28:** ambas as execuções completas de
  `JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest -m all` passaram com
  926 testes, 31 deselected e 957 itens coletados. A primeira levou 214,17 s; a
  segunda, 210,08 s. As execuções ocorreram antes das duas novas guardas abaixo.
- **Detecção precoce:** se o finding reaparecer, execute imediatamente o módulo
  com `-vv --tb=long` e preserve a saída integral. A fixture já inclui stdout e
  stderr quando o subprocesso retorna código diferente de zero; o agregador não
  preservou esse conteúdo.

  ```bash
  JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest -m all \
    tests/scripts/bootstrap_repo/test_repo_state.py -vv --tb=long
  ```

- **Item 5, resolvido:** `docs/workflow-agentes-dev.md` exige o campo
  `Executor: <agente> / <modelo>` em cada subseção de registro de trabalho. A
  guarda `test_work_records_require_executor_and_model` falhou antes da regra e
  passou depois. `tests/agents/` terminou com 184 testes aprovados. Agentes
  abrangidos: `devflow`, `eng-software`, `front`, `curador-produto`, `dba`, `sec`,
  `rev` e `qa`. Não alterei os prompts individuais; o contrato permanece no
  workflow.
- **Item 7, resolvido:** `spec-executavel` não exigia explicitamente que a fixture
  lesse valores de tabelas da spec. O item 8 do checklist agora exige essa ligação
  e proíbe codificar os valores à parte. A guarda
  `test_tabular_spec_fixture_reads_values_from_spec` falhou antes da regra e
  passou depois. `tests/skills/` terminou com 84 testes aprovados.
- **Análise estática:** `ruff check` nos dois testes novos passou. Consultei
  `docs/README.md` e `harness-conf/agents/references/principios-documentacao.md`;
  não há artefato adicional de spec ou ADR para estas regras.
- **Commits:** `8a6816f` (`docs(workflow): exige executor e modelo nos registros`)
  e `4636eb9` (`docs(skills): vincula fixtures às tabelas da spec`).
- **Higiene final:** `git diff --check` passou; as linhas novas e alteradas
  respeitam 120 colunas.

### Evidências de Testes — FINALIZAÇÃO

- [x] Testes novos: 2 guardas. Cada guarda falhou antes da alteração documental
      correspondente e passou depois.
- [x] Suíte completa: 2 execuções antes das guardas novas; cada uma coletou 957
      itens, com 926 passagens e 31 deselected. Nenhuma falha reproduzida.
- [x] Regressões após as alterações: `tests/agents/`, 184 passaram;
      `tests/skills/`, 84 passaram.
- [x] Análise estática: `ruff check` nos testes alterados passou.
- [x] Higiene: `git diff --check` passou; as linhas novas e alteradas respeitam
      120 colunas.
- [x] Gate de refatoração: não se aplica; não houve alteração de código de
      produção, escopo ou decisão arquitetural.
