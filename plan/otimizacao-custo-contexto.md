# Plano: otimização de custo e contexto do repo

Status: CONSTRUÇÃO — 2º ciclo (fase DEVFLOW). Plano aprovado pelo humano
(2026-09-24, condicionado à revisão delta; veredito APROVADO em
2026-09-26) com 3 melhorias do delta incorporadas. Executar waves em
ordem (E8 primeiro; E1→E2→E3→E4; E9/E13; E6→E14→E10; E7; E11/E12 no
fechamento; bloco E-fix + curadoria E11(b) pelo curador-produto).
Executor: worker glm-5.3-flash; revisor glm-5.3 (D12). Gate de
refatoração: volta a REVISÃO DO PLANO. Sem UI e sem modelagem de dados.

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
| T2 | Detecção read-only com fixture git de 2 commits: mudanças exatas base→novo, congelada ausente, SHA inválido com erro acionável, saída por skill | E2 | `tests/skills_mgmt/test_detect.py` (novo) | integration | git local |
| T3 | Detecção: clone em tempdir fora do repo + cleanup; aviso de conteúdo não confiável por skill; pendência reaparece na 2ª execução pós-recusa | E2 | `tests/skills_mgmt/test_detect.py` | integration | git local |
| T4 | Fallback clone completo quando shallow sem SHA base (L1) | E2 | `tests/skills_mgmt/test_detect.py` | integration | git local |
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
