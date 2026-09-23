# Plano: otimização de custo e contexto do repo

Status: APROVADO (plano aprovado pelo humano; execução pela fase AGORA
inicia após reinício do OpenCode, necessário para o novo modelo do worker
valer; executor = worker zai-coding-plan/glm-5.3-flash, revisor =
zai-coding-plan/glm-5.3, ver D12)

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

- [ ] **Task 8: Permissions de skills por agente**
  **Mapa FINAL aprovado em 2026-09-23 (pendente de aplicação; derivação por
  varredura linha a linha das menções nos corpos, não só tabelas):**
  - Core (visível a todos, sem deny): git-workflow-and-versioning,
    humanizer-br, portugues-tecnico-controlado, question-orchestration.
  - Utilitárias globais (sem deny): doc-extract, md-export,
    tls-certificate-recovery, svg-to-image, web-research-exa-crawl4ai.
  - Deny global (24): as demais skills de domínio + writing-for-agents
    + planning-and-task-breakdown + code-explorer-priority +
    reliable-async-operations (estas 3 removidas de core por decisão
    humana, com allow conforme menções nos corpos).
  - Allow (skill: agentes): planning-and-task-breakdown: smart-planner,
    qa, dba, eng-software · code-explorer-priority: eng-software, front
    · reliable-async-operations: eng-software, front, dba, qa, sec, rev
    · writing-for-agents: devflow, eng-software, smart-planner (D10)
    · aws-*: aws-analista (allow pré-existente, migrado ao frontmatter)
    · debugging-and-error-recovery: aws-analista, dba, eng-software, qa,
    sec · security-and-hardening: sec, dba, rev · data-modeling: dba,
    rev · code-review-and-quality: sec, eng-software, rev ·
    code-simplification: eng-software, front, rev · clean-code:
    eng-software, front · frontend-ui-engineering: front, rev ·
    accessibility-audit: front, qa, rev · performance-optimization:
    front, qa, eng-software · test-driven-development: qa, eng-software
    · tests-as-spec: qa, eng-software, rev · spec-executavel: analista,
    curador-produto, eng-software, qa, sec, front ·
    spec-driven-development: analista · documentation-and-adrs:
    curador-produto, eng-software, rev, front · api-and-interface-design:
    eng-software, rev, front · testes-produto-catalog: curador-produto
    · prompt-improver: devflow. Sem allow: worker, revisor,
    revisor-historia.
  - Front: além das 5 atuais do corpo, GANHA 7 de engenharia por decisão
    humana (test-driven-development, tests-as-spec,
    debugging-and-error-recovery, documentation-and-adrs,
    api-and-interface-design, code-review-and-quality, spec-executavel),
    ACRESCENTANDO as menções no corpo dele (o allow tem que bater com o
    corpo; listas nunca saem dos agentes).
  - Efeitos aceitos: "Descoberta de Código" do AGENTS.base só funciona
    para eng-software/front (demais caem no fallback grep/glob);
    "Espera por tarefas" (reliable-async) vale para os 6 com allow.
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

- [ ] **Task 9: Teste de consistência estendido**
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

- [ ] **Task 10: Roteamento, política de compactação e premissa 7**
  **Ajuste (2026-09-23, pedido do humano):** incluir também no
  AGENTS.base.md regra de autonomia: violação de regra objetiva do repo
  (formatação, largura de linha, estilo) é corrigida de imediato pelo
  agente, sem escalar ao humano; escalar apenas decisão de escopo,
  comportamento ou risco.
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

- [ ] **Task 11: Normalizar estado manual das skills**
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

- [ ] **Task 12: Piloto do ai-memory**
  **Description:** instalar `akitaonrails/ai-memory` em user-space
  (OpenCode: MCP + hooks), rodar sessão de trabalho real e medir com o
  método do relatório (requests, custo, cache_write antes/depois do
  PreCompact). Registrar resultados no plano. Adoção decidida pelo humano
  com os dados.
  **Acceptance criteria:**
  - [ ] Instalação user-space sem sudo/administrador.
  - [ ] Hook PreCompact ativo e persistindo resumo antes de compactar.
  - [ ] Medição registrada (antes/depois) no plano.
  **Verification:** sessão de teste com compactação disparada; wiki do
  ai-memory com o resumo persistido; comparação de métricas anotada.
  **Dependencies:** Tasks 1-11 (otimizações implementadas; baseline
  pós-otimização).
  **Files likely touched:** `harness-conf/opencode.json` (se hooks/MCP
  forem declarados no repo; só com aprovação), `plan/otimizacao-custo-con
  texto.md` (resultados)
  **Estimated scope:** Medium

- [ ] **Task 13: Materializar o insumo do devflow**
  **Description:** consolidar neste arquivo o estado final da fase AGORA:
  implementado (com SHAs dos checkpoints), resultados do piloto,
  pendências (Copilot CLI, testes faltantes, docs) e decisões; atualizar o
  campo Status para o vocabulário do devflow; seção Fase DEVFLOW como
  roteiro do planejamento dele.
  **Acceptance criteria:**
  - [ ] Status no vocabulário do devflow; seção Fase DEVFLOW completa.
  - [ ] Todo item de D9 fase AGORA marcado como feito/pendente com
        evidência (SHA ou medição).
  **Verification:** leitura do arquivo por um leitor fresco responde "o
  que foi feito, o que falta, por onde continuar".
  **Dependencies:** Tasks 1-12
  **Files likely touched:** `plan/otimizacao-custo-contexto.md`
  **Estimated scope:** Small

**Checkpoint 4 (commits):** piloto (se tocar repo) e
`docs(plan): consolida insumo do devflow`. O arquivo do plano PERMANECE
no repo (é o insumo do devflow; não é removido ao final).

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

1. Conteúdo da fase DEVFLOW ("o que mais?"): proposta registrada em D9
   (suíte completa, registro no opencode-skills + checklist pós-sync,
   consistência workflow↔agentes, README). A validar na aprovação do plano.
2. Língua da description do writing-for-agents importado: regra do repo
   manda perguntar ao humano. Default proposto: converter para PT-BR e
   enriquecer com triggers, registrando `description_lang` no UPSTREAM.md.
3. Mapeamento fino skills de domínio ↔ agentes especialistas (para o
   `permission.skill` de A1): a definir na execução a partir das tabelas de
   skills obrigatórias/condicionais já presentes no corpo de cada
   `agents/*.md`; validado pelo teste de consistência estendido (D3).
