# Plano: Melhorias em Agentes, Curadoria e Estrutura de Harness

Status: EXECUÇÃO CONCLUÍDA — REVISÃO FINAL APROVADA

## Fechamento

### Fase 5 — correções pós-revisão (aprovadas pelo humano, em definição)

- **D12 (skills autocontidas)**: skill não referencia paths ou títulos
  de artefatos internos do harness; pode mencionar convenções do
  ecossistema (AGENTS.md do projeto-alvo, docs/README.md criado pelo
  workflow) e as próprias `references/`.
- **5.1**: `reliable-async-operations` — remover as 2 referências ao
  AGENTS.md global (nome de seção renomeado na base); reescrever os
  trechos de forma autocontida.
- **5.2**: templates `default-artifacts/` — renomear com sufixo
  `-template` (`git mv`: doc-readme-template.md,
  testes-por-especialidade-template.md,
  instrucoes-por-agente-template.md); comentário `<!-- TEMPLATE: ... -->`
  no topo de cada um especificando o papel; corpo do
  `curador-produto.md` explica o papel de cada template (não só os
  paths); varredura grep por TODAS as referências aos nomes antigos
  (curador, adapter copilot, scaffold, testes, comandos, agentes) e
  ajuste.
- **5.3**: `AGENTS.md` raiz — remover o bullet residual com a ordem das
  ferramentas do codebase-memory e a dica de `Section` (fica só a
  prioridade do CLI + gatilho da skill `code-explorer-priority`);
  verificar testes associados.
- **5.4**: `reliable-async-operations` — ponte explícita entre a
  proibição ("PROIBIDO timeouts genéricos/conveniência") e o requisito
  do contrato ("toda chamada de rede precisa de timeout explícito"):
  1-2 frases explicando que a proibição mira o número chute como
  desencargo, e o timeout exigido é rede de segurança ancorada a sinal
  de vida (inatividade) com valor justificado.
- **5.5**: `harness-conf/commands/index-codebase.md` — reescrever as
  Etapas 1-2 como fluxo único, sem bifurcação por cliente (OpenCode/
  Copilot); diferenças pontuais de ambiente viram nota curta (padrão da
  linha "sem prefixo wsl"); manter a Etapa 3 já corrigida.
- **5.6**: fixture do servidor Qwen (`tests/integration/model/`) —
  health-check antes do lote `opencode` (chamada simples ao servidor);
  servidor doente → reiniciar ou falhar de imediato com mensagem
  acionável (`python3 tests/integration/model/local_model_server.py
  --up`); sem skip (pytest.fail com instrução).
- Execução: todas as 6 aprovadas individualmente pelo humano; executor
  + revisor independente ao final.
- (demais correções em aprovação individual com o humano)


- **Fase 5 CONCLUÍDA** (commits `55706aa`, `0c15d7b`, `e210a6d`,
  `7362e08`, `ee5b722`, `81bef96`). Suíte completa verde (686 passed,
  2 deselected copilot, WSL, integração OpenCode incluída; `/health`
  do llama-server validado empiricamente). Grep sem referências ativas
  aos nomes antigos dos templates. 5.2: `git mv` com rename 100%,
  comentários `<!-- TEMPLATE: -->`, curador explicando papéis, testes
  do curador/scaffold/adapter copilot atualizados. 5.6: TDD com
  servidor doente simulado; `ensure_healthy` (uma tentativa de restart
  + `pytest.fail` acionável) na fixture session-scoped.
- Fases 1-4 executadas; cada fase revisada por instância independente
  (todas APROVADAS); revisão final global APROVADA sem divergências.
- Suíte completa: 675 passed, 2 deselected (copilot/Windows).
- Bootstrap re-executado com sucesso no WSL.
- Pendências do humano: suíte Copilot no Windows; reindexar
  codebase-memory; `git push` somente com confirmação explícita.
- Notas pós-plano (melhorias não-bloqueantes, fora do escopo,
  coletadas pelos revisores):
  1. Fixture do servidor Qwen validar saúde antes do lote (ambiente).
  2. `reliable-async-operations` cita seção do AGENTS global com título
     antigo ("Espera de tarefas" vs "Espera por tarefas").
  3. Frase amarrando a tensão "PROIBIDO timeouts" vs "toda chamada de
     rede precisa de timeout" na própria skill.
  4. `index-codebase.md` Etapas 1-2 ainda bifurcam por cliente.
  5. Bullet residual com ordem das ferramentas no AGENTS.md raiz.
  6. Cabeçalho de 1 linha em `testes-por-especialidade.md` explicando
     seu papel de tabela-índice.

## Overview

Ajustes no repo opencode-global-config a partir de 6 anotações do humano:
contextualização do plano na conversa, especificação executável na curadoria,
skill de spec executável extraída do analista, AGENTS.md global para harnesses,
distinção repo vs artefatos copiados, e flexibilidade de modelos no devflow.
A curadoria do AGENTS.base.md foi conduzida no planejamento (decisões D9-D11 +
Anexo A aprovado); o executor materializa copiando.

## Architecture Decisions

- **D1 (plano único)**: as 6 anotações serão tratadas em um único plano,
  com fases independentes e checkpoints por fase. Corte natural se preciso
  isolar: [1,2,3,6] agentes/workflow vs [4,5] estrutura/adapters.
- **D2 (fusão no README, anotação 2)**: o spec `docs/testes-produto.md`
  do projeto-alvo será fundido no `docs/README.md` como seção "Testes por
  Especialidade". O `AGENTS.md` do projeto-alvo mantém só a tabela índice
  + link (âncora para a seção). O template `default-artifacts/testes-produto.md`
  é absorvido pelo `doc-readme.md`.
- **D3 (dois níveis de teste, anotação 2)**: distinção obrigatória e
  explícita para o agente: (1) **testes da aplicação** — rodam via
  suítes/orquestrador `testes-produto` na fase Testes, sempre que se
  desenvolve funcionalidade; (2) **testes dos scripts de teste** — os
  scripts de suíte/orquestrador são código, têm testes próprios que cobrem
  o que o doc especifica (o doc é a especificação executável deles) e rodam
  SOMENTE quando os scripts mudam (ex: curadoria alterando
  ferramentas/critérios por orientação do humano); nunca no ciclo normal.
  A distinção deve ficar clara nos agentes, nos templates default-artifacts
  e no doc gerado no projeto-alvo.
- **D4 (AGENTS.md base, anotação 4)**: criar `harness-conf/AGENTS.base.md`
  com as regras universais do humano. Entrega: OpenCode via symlink
  `~/.config/opencode/AGENTS.md`; Copilot via cópia para
  `~/.copilot/AGENTS.md`. Extinção do
  `.github/copilot-specific.instructions.md`. `AGENTS.md` raiz fica só com
  regras específicas do repo + aponta para a base. Conteúdo final definido
  pela curadoria (D10/D11) e materializado do **Anexo A**.
- **D5 (reestruturação harness-conf/, anotações 4 e 5)**: mover para
  `harness-conf/` (via `git mv`): `agents/`, `skills/`, `commands/`,
  `opencode.json` + novo `AGENTS.base.md`. Ficam na raiz (infra do repo):
  `AGENTS.md` (repo), `scripts/`, `src/`, `tests/`, `docs/`, `adapters/`,
  `plan/`, `README.md`. Sentido do termo **harness** a partir daqui:
  plataforma de agentes (OpenCode, Copilot CLI) — NÃO o antigo "harness"
  de testes (hoje `testes-produto`). **Requisito de commit:** o commit da
  reestruturação DEVE ter body detalhado explicando a mudança de conceito
  (harness antigo = agregador de testes renomeado para testes-produto;
  harness novo = plataforma de agentes) para desambiguar o log para
  agentes que consultarem o histórico.
- **D6 (contextualizar com o plano, anotação 1)**: nova cláusula na skill
  `question-orchestration` (fonte única): quando existir artefato de
  planejamento/estado persistido, toda interação com o humano carrega o
  contexto relevante do plano (fase, decisões que afetam a pergunta,
  escopo). **Motivação central**: o plano é artefato do AGENTE — o humano
  não está necessariamente olhando-o; a informação do plano precisa vir
  até o humano na conversa, nunca ser presumida como conhecida.
  Smart-planner, devflow e analista herdam pela skill, sem
  duplicação em cada agente.
- **D7 (devflow flexível em modelos, anotação 6)**: substituir o menu
  rígido de seleção de modelo por sugestão de padrão (ex: um modelo por
  etapa — planejamento, execução, testes, revisão) + aviso explícito de
  que o humano define como preferir (um modelo só, por fase granular,
  arranjo próprio). Devflow registra o mapa combinado no plano e continua
  pausando antes de fases com modelo diferente do atual.
- **D8 (skill spec-executavel, anotação 3)**: skill nova
  `harness-conf/skills/spec-executavel` (após D5), agnóstica de
  ferramenta (Concordion citado apenas como exemplo). Gherkin =
  recomendação forte default com cláusula de exceção (agente avalia
  adequação por caso; formato melhor → propõe e discute com o humano;
  ex.: tabela para permissionamento). Arquivos MD favorecidos, exceções
  possíveis. Conteúdo: itens 1-10 da lista aprovada, com o item 8
  (valores concretos/aspas) elevado a **princípio central** — a spec é
  ótima quando o humano mexe no texto e o teste quebra; linkar ao máximo
  os valores das regras ao código de teste. Rastreabilidade por link à
  origem (referenciar requisito/regra, ex.: threat model → RNF), sem
  ensinar criação de RF/RNF (isso fica no analista; estrutura de
  elementos vive no docs/README.md do projeto-alvo). Sem regra de
  cobertura mínima. Item 11 (rejeição/limite só por regra de negócio)
  permanece só no corpo do analista. Referência obrigatória em
  eng-software, sec e qa; analista referencia e **fecha para Gherkin**
  (desvie só pela cláusula de exceção, com o humano); curador-produto
  referencia como orientação na entrevista.
- **D9 (skills de escrita, anotação 4 — nova)**: importar DUAS skills
  upstream em `harness-conf/skills/`, ambas com revisão obrigatória de
  segurança (prompt injection, comandos, URLs, exfiltração) + UPSTREAM.md
  com SHA/commit + **registro no sync automático** do `opencode-skills`
  (estender pacote + testes):
  - `portugues-tecnico-controlado` (kayquer; MIT a confirmar na revisão):
    precisão/baixa ambiguidade para texto técnico.
  - `humanizer-br` (carlosafjr-dev; MIT confirmado): naturalidade
    anti-IA (~150 padrões PT-BR + aprofundador). Fallback se a revisão
    reprovar: `phardoom/humanizador` (MIT).
  Seção do AGENTS.base.md "Comunicação": Língua + Perfil do Humano
  (aprovado: analista de sistemas, jargão de software livre, calibrar
  registro pela distância do domínio, inglês aceitável) + Concisão +
  **Tom natural**: `humanizer-br` carregada no início da sessão e
  aplicada a TODA comunicação (chat incluso — objetivo declarado do
  humano: comunicação não maçante); `portugues-tecnico-controlado`
  carregada para texto técnico (specs, docs, explicações densas).
- **D10 (modelo de camadas, curadoria da base)**: o AGENTS.base.md é
  GLOBAL e também vige neste repo; o `AGENTS.md` raiz não duplica
  conteúdo da base — mantém apenas o específico do repo. Princípio da
  curadoria: na base fica **somente o estritamente necessário**;
  detalhe mora em skills, com gatilho de carregamento. Fechados:
  seção "Comunicação" completa; "Commits" mínima; "Ação" sai INTEIRA da
  base (agentes livres para agir ao responder); regras de timeout de
  CÓDIGO saem da base (proibição sintetizada migra para
  `reliable-async-operations`); na base fica, em versão mínima (~3
  linhas), apenas a espera do AGENTE por tarefas. Redação final
  aprovada com as skills de escrita aplicadas = **Anexo A**.
- **D11 (descoberta de código é do repo, não da base)**: a regra
  codebase-memory e a referência à skill `code-explorer-priority` ficam
  no `AGENTS.md` raiz (cada repo decide usar codebase-memory). A skill
  `code-explorer-priority` absorve os detalhes operacionais do CLI
  (comandos JSON, ordem das ferramentas, busca em docs) e ganha
  description condicionada: só ativar quando o AGENTS.md do repo indicar
  codebase-memory. A tabela "Acesso por cliente" sai (comando idêntico
  nos dois harnesses). "Criação de Skills" entra na base (2 bullets).
  Comunicação do bootstrap fica no raiz; seção SmartPlanner sai do raiz
  (restrição vive no corpo do agente). Linha `crwl` sai da base (a skill
  `web-research-exa-crawl4ai` cobre). Linha "sem prefixo wsl" vai como
  1 linha na seção de descoberta do `AGENTS.md` raiz.

## Execução — configuração aprovada

### Progresso
- **Fase 1 CONCLUÍDA** (commits `b580f55`, `30b5958`, `3dc552c`,
  `47292b4`, `516a9ad`, `742895e`). Revisor independente: **APROVADO**
  (suíte 632 passed; base = Anexo A; auditoria de segurança das skills
  refeita pelo revisor com confiança zero — limpa; codebase-memory-mcp
  resolvido por concatenação, symlink rejeitado com evidência).
- Achados não-bloqueantes do revisor (decisão humana pendente):
  1. `harness-conf/commands/index-codebase.md` ainda referencia o
     copilot-specific extinto (sugerido vincular à Task 13).
  2. Comunicação do bootstrap (docling/TLS) ficou só no README;
     revisor sugere 1-2 linhas na seção Bootstrap do AGENTS.md raiz.
- Nota operacional: a tool `task` não está disponível para o subagente
  executor (encadeamento executor→worker não suportado nesta
  plataforma). **Modalidade A aprovada**: o orquestrador spawna workers
  (luna) diretamente, em paralelo ao executor, para lotes mecânicos
  identificados; executor solo quando não houver lote mecânico claro.

- **Fase 2 CONCLUÍDA** (commits `91abdbe`, `4ef59fa`,
  `7841b79`, `3d5959a`, `3d50728`). Suíte completa verde
  (639 passed, WSL, integração OpenCode incluída); grep
  `docs/testes-produto.md` sem referências ativas (só
  plano, asserções negativas e a proibição no curador).
  Nota da execução: a skill `testes-produto-catalog` e o
  teste `tests/skills/test_testes_produto_catalog.py`
  também foram atualizados (referências ativas ao arquivo
  extinto, exigidas pela verificação final da fase).
- **Fase 3 CONCLUÍDA** (commits `5b8320f`, `be50655`, `24202e4`,
  `578a440`). Suíte completa verde (670 passed, 2 deselected copilot,
  WSL, integração OpenCode incluída). Skills criadas/migradas:
  `spec-executavel` (autocontida, description rica em triggers);
  `reliable-async-operations` absorveu a proibição de timeouts (3
  bullets + triggers na description); `code-explorer-priority` absorveu
  os comandos JSON posicionais, a ordem das ferramentas, a busca via
  `Section`/Cypher e o fallback estrito, com description condicionada ao
  AGENTS.md. Adendo da Task 13 aplicado: Etapa 3 do
  `harness-conf/commands/index-codebase.md` sem o copilot-specific
  extinto. Testes novos/atualizados:
  `tests/skills/test_spec_executavel.py`,
  `tests/skills/test_reliable_async_operations.py`,
  `tests/agents/test_spec_executavel_adoption.py` e
  `tests/skills/test_code_explorer.py`.
- **Fase 4 CONCLUÍDA** (commits `f279d69`, `9f74e61`). Suíte completa
  verde (675 passed, 2 deselected copilot, WSL, integração OpenCode
  incluída). Bootstrap re-executado com sucesso no WSL. Pendências para
  o humano: suíte Copilot no Windows e reindexação do codebase-memory.
- **Executor**: subagente genérico (`general`), modelo da sessão (GLM).
  Instruído a delegar ao `worker` os lotes grandes/mecânicos via `task`.
- **Worker**: agente `worker`, modelo `opencode-go/gpt-5.6-luna`
  (trocado no frontmatter com autorização humana; edição de 1 linha,
  sem commit — será incluída em commit da execução). Mecanismo:
  `model:` no frontmatter de `agents/worker.md` contorna a limitação
  da tool `task` (não aceita modelo no spawn); trocar + reiniciar o
  OpenCode quando precisar.
- **Revisor**: agente `revisor`, modelo da sessão (GLM), instância nova
  e independente por revisão.
- **Documentação do mecanismo**: incluída na Task 5 (uma linha no
  `AGENTS.md` raiz).

## Task List

### Phase 1: Reestruturação, skills de escrita e base (D4, D5, D9, D10, D11)

- [x] **Task 1: Mover artefatos copiáveis para `harness-conf/`**
  - **Description**: criar `harness-conf/` e mover com `git mv`:
    `agents/`, `skills/`, `commands/`, `opencode.json`. Atualizar
    referências de path em `src/` (bootstrap, symlinks, adapter,
    scaffold) e `tests/`. NUNCA simular move como delete+create.
  - **Acceptance criteria**:
    - `harness-conf/{agents,skills,commands,opencode.json}` existem e o
      histórico git preserva renames (`git log --follow` funciona).
    - Zero path antigo em `src/`+`tests/` (exceto `harness-conf/`).
    - Suíte verde: `.venv/bin/pytest -m "unit or tools or opencode"`.
  - **Verification**: `git log --follow harness-conf/agents/devflow.md`;
    grep de paths antigos; suíte pytest.
  - **Dependencies**: None
  - **Files likely touched**: `harness-conf/**` (move),
    `src/opencode_config/**`, `tests/**`, `scripts/bootstrap_repo/**`
  - **Estimated scope**: Large (mecânico)
  - **Commit**: `refactor: mover artefatos copiáveis para harness-conf/`
    com body conceitual obrigatório (D5).

- [x] **Task 2: Adapter Copilot — origens em `harness-conf/`**
  - **Description**: `src/opencode_config/adapters/copilot.py` lê de
    `harness-conf/`. Atualizar testes do adapter.
  - **Acceptance criteria**: adapter aponta para `harness-conf/`;
    `tests/adapters/` verdes.
  - **Verification**: `.venv/bin/pytest tests/adapters -m "unit or tools"`.
  - **Dependencies**: Task 1
  - **Files likely touched**: `src/opencode_config/adapters/copilot.py`,
    `tests/adapters/**`
  - **Estimated scope**: Small

- [x] **Task 3: Importar skills de escrita com revisão de segurança**
  - **Description**: importar para `harness-conf/skills/`:
    `portugues-tecnico-controlado` (kayquer) e `humanizer-br`
    (carlosafjr-dev; MIT confirmado). **Revisão de segurança obrigatória
    antes de consolidar**: ler TODO conteúdo copiado procurando prompt
    injection, comandos, URLs e exfiltração. Reprovou humanizer-br →
    fallback `phardoom/humanizador` (MIT). Reprovou PTC → bloquear e
    reportar (sem fallback). Para cada skill: `UPSTREAM.md` (URL+branch,
    SHA+data, data do sync, arquivos sincronizados, SKILL.md NÃO
    sincronizado, instruções de sync, licença, description_lang/note),
    description enriquecida com triggers, registro no sync do
    `opencode-skills` (estender pacote Python + testes).
  - **Acceptance criteria**:
    - Skills instaladas em `harness-conf/skills/<nome>/` com UPSTREAM.md
      completo.
    - `opencode-skills list`/`sync` cobrem as duas; revisão de segurança
      documentada no resumo.
    - Suíte verde.
  - **Verification**: `.venv/bin/pytest -m "unit or tools"`;
    `opencode-skills list`.
  - **Dependencies**: Task 1
  - **Files likely touched**:
    `harness-conf/skills/portugues-tecnico-controlado/`,
    `harness-conf/skills/humanizer-br/`, `src/opencode_config/**`,
    `tests/skills_mgmt/**`
  - **Estimated scope**: Medium

- [x] **Task 4: `harness-conf/AGENTS.base.md` do Anexo A + extinção copilot-specific**
  - **Description**: criar `harness-conf/AGENTS.base.md` **copiando
    literalmente o Anexo A** deste plano (autocontido, sem citar o
    plano). Extinção: `git rm .github/copilot-specific.instructions.md`.
    Adapter copia a base → `~/.copilot/AGENTS.md` (se o Copilot exigir
    outro path global, reportar bloqueio em vez de improvisar).
    Bootstrap cria symlink `~/.config/opencode/AGENTS.md` → base.
    **Investigação obrigatória antes do symlink**:
    `~/.config/opencode/AGENTS.md` é gerenciado pelo codebase-memory-mcp;
    definir convivência (base absorve marcadores, bootstrap concatena,
    ou outro caminho). Sem decisão segura, bloquear — não substituir o
    arquivo gerado.
  - **Resultado da investigação (execução)**: o codebase-memory-mcp
    injeta/remove apenas o bloco entre marcadores e preserva o resto do
    arquivo, mas escreve ATRAVÉS de symlinks (mutaria a base versionada;
    comprovado em HOME isolado). Convivência adotada: **concatenação** —
    o adapter OpenCode gera `~/.config/opencode/AGENTS.md` como arquivo
    regular (base + blocos marcados de terceiros preservados, com
    backup); sem symlink para AGENTS.md.
  - **Acceptance criteria**:
    - Base idêntica ao Anexo A; copilot-specific removido.
    - Testes do adapter/bootstrap verdes; symlink sem conflito com o
      codebase-memory-mcp.
  - **Verification**: diff base↔Anexo A vazio; suíte pytest.
  - **Dependencies**: Task 3 (a base referencia as skills)
  - **Files likely touched**: `harness-conf/AGENTS.base.md` (novo),
    `.github/copilot-specific.instructions.md` (rm),
    `src/opencode_config/**`, `tests/**`
  - **Estimated scope**: Medium

- [x] **Task 5: `AGENTS.md` raiz reescrito + mapa no README**
  - **Description**: raiz remove as regras que foram para a base e fica
    com: descoberta de código SINTETIZADA (codebase-memory antes de
    grep/glob, recovery `list_projects`, referência à skill
    `code-explorer-priority`, linha "no Windows, execute os CLIs sem
    prefixo `wsl`"; SEM tabela por cliente); atalho "configure este
    repo"; links simbólicos com paths `harness-conf/`; bootstrap +
    comunicação do bootstrap (docling/TLS) nesta seção; upstream de
    skills (com as duas novas no sync); sincronização
    workflow↔agentes; regras de testes; dependências do README;
    sincronização dos adaptadores. **Remover** a seção SmartPlanner
    (restrição vive no corpo do agente). `README.md`: seção de
    estrutura `harness-conf/` vs infra do repo. Paths textuais em
    `docs/workflow-*.md` atualizados. Incluir linha documentando o
    mecanismo do worker: modelo definido no frontmatter de
    `agents/worker.md` (contorna a limitação da tool `task`); trocar
    e reiniciar quando precisar.
  - **Acceptance criteria**:
    - Raiz sem duplicar a base; descoberta sintetizada sem tabela
      cliente; SmartPlanner removido.
    - README com mapa de estrutura; sem path antigo em docs.
  - **Verification**: grep de duplicações/paths antigos em `AGENTS.md`,
    `README.md`, `docs/*.md`.
  - **Dependencies**: Task 4
  - **Files likely touched**: `AGENTS.md`, `README.md`, `docs/*.md`
  - **Estimated scope**: Medium

### Checkpoint: Phase 1
- [x] Suíte completa verde (WSL): `.venv/bin/pytest -m "unit or tools or opencode"`
- [x] Skills de escrita importadas com revisão de segurança documentada
  (APROVADAS; detalhes nos UPSTREAM.md de cada skill)
- [x] Base entregue nos dois harnesses sem conflito com codebase-memory-mcp
  (convivência por concatenação — ver nota na Task 4)
- [x] Bootstrap re-executado com sucesso (home real: links harness-conf +
  AGENTS.md = base + bloco do mcp preservado)
- [x] Review com humano antes de prosseguir

### Phase 2: Curadoria unificada no docs/README.md (D2, D3)

- [x] **Task 6: Fundir templates default-artifacts**
  - **Description**: `doc-readme.md` absorve `testes-produto.md` como
    seção "Testes por Especialidade" (suítes, orquestrador, interface
    JSON, proibições). O template declara os dois níveis de teste (D3) e
    o papel do doc como meta-informação que vira spec executável dos
    scripts (testes deles rodam SOMENTE quando os scripts mudam).
    `git rm` do `testes-produto.md`.
  - **Acceptance criteria**: seção completa no `doc-readme.md`; dois
    níveis explícitos; arquivo removido com `git rm`.
  - **Verification**: leitura; grep sem referências ao removido.
  - **Dependencies**: Task 1
  - **Files likely touched**:
    `harness-conf/agents/default-artifacts/doc-readme.md`,
    `harness-conf/agents/default-artifacts/testes-produto.md` (rm)
  - **Estimated scope**: Small

- [x] **Task 7: Curador e mensagens de curadoria**
  - **Description**: `curador-produto.md`: entrevista sem spec separado
    (docs/README.md com a seção; `AGENTS.md` do projeto-alvo com tabela +
    link âncora); orienta o humano sobre spec executável dos scripts e
    os dois níveis de teste (D3). `mensagens-curadoria.md` atualizada
    (um artefato só).
  - **Acceptance criteria**: nenhum fluxo gravando
    `docs/testes-produto.md`; orientação presente; mensagens coerentes.
  - **Verification**: `.venv/bin/pytest tests/agents/test_curador_produto.py`.
  - **Dependencies**: Task 6
  - **Files likely touched**:
    `harness-conf/agents/curador-produto.md`,
    `harness-conf/agents/references/mensagens-curadoria.md`,
    `tests/agents/test_curador_produto.py`
  - **Estimated scope**: Medium

- [x] **Task 8: Scaffold unificado**
  - **Description**: `scaffold_mapa.py`: `DOC_TEMPLATE` ganha a seção
    "Testes por Especialidade"; `TESTES_PRODUTO_TEMPLATE` (tabela do
    AGENTS.md) linka âncora `docs/README.md#testes-por-especialidade`
    (não mais arquivo próprio). Atualizar
    `tests/scaffold/test_mapa_produto.py`.
  - **Acceptance criteria**: scaffold gera doc com a seção; tabela
    aponta âncora; `tests/scaffold/` verdes.
  - **Verification**: `.venv/bin/pytest tests/scaffold -m "unit or tools"`.
  - **Dependencies**: Task 6
  - **Files likely touched**: `src/opencode_config/cli/scaffold_mapa.py`,
    `tests/scaffold/test_mapa_produto.py`
  - **Estimated scope**: Medium

- [x] **Task 9: Referências nos agentes e workflows**
  - **Description**: trocar leituras de `docs/testes-produto.md` pela
    seção no `docs/README.md` em `devflow.md`, `eng-software.md`,
    `qa.md`, `sec.md`, `dba.md`, `rev.md`, `front.md` e
    `docs/workflow-*.md`. Dois níveis (D3) explícitos em `devflow.md`,
    `qa.md`, `eng-software.md`, `curador-produto.md`. Verificar
    `harness-conf/agents/references/interface-testes-produto.md`.
  - **Acceptance criteria**: zero referências ao arquivo extinto; dois
    níveis descritos nos agentes-chave; `tests/agents/` verdes.
  - **Verification**: grep `testes-produto.md` (sem falso positivo);
    `.venv/bin/pytest tests/agents -m "unit or tools"`.
  - **Dependencies**: Task 6
  - **Files likely touched**: `harness-conf/agents/*.md`,
    `docs/workflow-*.md`, `tests/agents/**`
  - **Estimated scope**: Medium

### Checkpoint: Phase 2
- [x] Suíte agents+scaffold+adapters verde
- [x] Curadoria coerente end-to-end (templates, curador, scaffold, agentes)
- [x] Review com humano antes de prosseguir

- [x] **Task 9b (adicionada no checkpoint da Fase 1, aprovada)**: na seção
  Bootstrap do `AGENTS.md` raiz, adicionar 1-2 linhas apontando os fluxos
  docling/TLS detalhados no `README.md`.
  - **Acceptance criteria**: seção Bootstrap referencia os fluxos; sem
    duplicar o conteúdo do README.
  - **Verification**: leitura do trecho.
  - **Dependencies**: Task 9
  - **Files likely touched**: `AGENTS.md`
  - **Estimated scope**: XS

### Phase 3: Skills — spec-executavel e migrações (D8, D10, D11)

- [x] **Task 10: Criar a skill `spec-executavel`**
  - **Description**: criar `harness-conf/skills/spec-executavel/SKILL.md`,
    autocontido (sem citar plano/decisões). Conteúdo canônico:
    1. Estrutura canônica do cenário: `Cenário` + `Dado que` + `E` +
       exatamente 1 `Quando tento` + `Então` (+ `E`)
    2. `Então` sempre verificável — estado/registro/mensagem/regra
       aplicada; nunca frase vaga
    3. Linguagem de negócio — sem UI/implementação (tela, botão,
       endpoint, classe)
    4. Desambiguação real — explicitar identificador/entidade quando há
       risco de dupla interpretação
    5. Repetição útil vs redundância — repetir no `Então` só o que
       valida estado/persistência
    6. Consistência contextual — steps formam um todo coeso
    7. Concisão — só o indispensável por passo
    8. **Princípio central** — a spec é ótima quando o humano mexe no
       texto e o teste quebra; linkar ao máximo os valores definidos
       nas regras ao código de teste (valores concretos e aspas duplas
       apenas para literais que mudam o veredito)
    9. Persona/perfil — só quando o foco é permissão/acesso
    10. `Esquema do Cenário` + `Exemplos` para variações da mesma regra
    Gherkin = recomendação forte com cláusula de exceção (avaliar
    adequação por caso; formato melhor → propõe ao humano e discute;
    ex.: tabela para permissionamento); MD favorecido; rastreabilidade
    por link à origem; agnóstica de ferramenta (Concordion só como
    exemplo). FORA da skill (permanece no analista): rejeição/erro e
    casos limite só por regra de negócio/legal; INVEST;
    escrita/classificação de RF/RNF. Description rica em triggers.
  - **Acceptance criteria**: SKILL.md completo e autocontido; teste de
    consistência/boilerplate verde.
  - **Verification**: `.venv/bin/pytest tests/skills* -m "unit or tools"`.
  - **Dependencies**: Task 1
  - **Files likely touched**:
    `harness-conf/skills/spec-executavel/SKILL.md`
  - **Estimated scope**: Medium

- [x] **Task 11: Referenciar a skill nos agentes**
  - **Description**: `analista.md`: seção 3B e "Padrão de qualidade"
    referenciam a skill + **fechamento para Gherkin** (desvio só pela
    cláusula de exceção, com o humano); INVEST, RF/RNF e item 11
    permanecem no corpo. `eng-software.md`, `sec.md`, `qa.md`: skill
    obrigatória na capacidade de criar specs executáveis.
    `curador-produto.md`: orientação na entrevista. Atualizar testes de
    consistência.
  - **Acceptance criteria**: agentes referenciam a skill existente;
    analista mantém regras próprias; `tests/agents/` verdes.
  - **Verification**: `.venv/bin/pytest tests/agents -m "unit or tools"`.
  - **Dependencies**: Task 10
  - **Files likely touched**: `harness-conf/agents/analista.md`,
    `harness-conf/agents/eng-software.md`, `harness-conf/agents/sec.md`,
    `harness-conf/agents/qa.md`,
    `harness-conf/agents/curador-produto.md`, `tests/agents/**`
  - **Estimated scope**: Medium

- [x] **Task 12: `reliable-async-operations` absorve a proibição de timeouts**
  - **Description**: incluir na skill os 3 bullets sintetizados da
    proibição: (1) PROIBIDO definir/ajustar timeouts genéricos ou por
    conveniência; timeout não mascara travamento, não impõe desempenho
    e não vira critério de falha; (2) exceções: recurso contínuo com
    inatividade já comprovada, ou confirmação explícita prévia do humano
    com justificativa do recurso e do valor; (3) não troque timeout
    proibido por valor alto: remova ou consulte o humano; timeout
    existente fora das exceções: informe, não altere silenciosamente.
    Ajustar description para cobrir o gatilho.
  - **Acceptance criteria**: skill contém a proibição; base não a
    duplica; testes correspondentes verdes.
  - **Verification**: leitura da skill; `.venv/bin/pytest -m "unit or tools"`.
  - **Dependencies**: Task 4
  - **Files likely touched**:
    `harness-conf/skills/reliable-async-operations/SKILL.md`, `tests/**`
  - **Estimated scope**: Small

- [x] **Task 13: `code-explorer-priority` absorve detalhes do CLI**
  - **Description**: mover para a skill o conteúdo operacional do
    extinto copilot-specific: comandos com JSON posicional único
    (`list_projects`, `index_repository`, `search_graph`, `trace_path`,
    `get_code_snippet`, `query_graph`, `search_code`,
    `get_architecture`), ordem search_graph→trace_path→
    get_code_snippet→query_graph→get_architecture, busca em docs via
    nós `Section` (Cypher), fallback estrito grep/glob. Description da
    skill `code-explorer-priority` condicionada: ativar apenas
    quando o AGENTS.md do repo indicar codebase-memory.
    **Adendo (aprovado no checkpoint da Fase 1)**: reescrever a Etapa 3
    de `harness-conf/commands/index-codebase.md` para remover a
    referência ao extinto `.github/copilot-specific.instructions.md`.
  - **Acceptance criteria**: skill contém os detalhes; description
    condicionada; base/raiz sem duplicar; testes verdes.
  - **Verification**: leitura; `.venv/bin/pytest -m "unit or tools"`.
  - **Dependencies**: Task 4
  - **Files likely touched**:
    `harness-conf/skills/code-explorer-priority/SKILL.md`, `tests/**`
  - **Estimated scope**: Medium

### Checkpoint: Phase 3
- [x] Skills criadas/importadas/migradas; consistência verde
- [x] Review com humano antes de prosseguir

### Phase 4: Protocolo conversacional e devflow (D6, D7)

- [x] **Task 14: Cláusula de contextualização na question-orchestration**
  - **Description**: cláusula na skill: quando existir artefato de
    planejamento/estado persistido, toda interação com o humano carrega
    o contexto relevante (fase, decisões que afetam a pergunta,
    escopo). Motivação explícita: o plano é artefato do agente; o
    humano não o está lendo; nunca presumir conhecimento do plano.
    Atualizar `tests/agents/test_question_orchestration_adoption.py`.
  - **Acceptance criteria**: cláusula presente na skill (fonte única);
    testes verdes.
  - **Verification**:
    `.venv/bin/pytest tests/agents/test_question_orchestration_adoption.py`.
  - **Dependencies**: Task 1
  - **Files likely touched**:
    `harness-conf/skills/question-orchestration/SKILL.md`,
    `tests/agents/test_question_orchestration_adoption.py`
  - **Estimated scope**: Small

- [x] **Task 15: Devflow flexível na seleção de modelo**
  - **Description**: reescrever "Seleção de modelo por fase" do
    `devflow.md`: devflow **sugere** padrão (um modelo por etapa —
    planejamento, execução, testes, revisão) e avisa que o humano define
    como preferir (um modelo só, por fase granular, arranjo próprio);
    registra o mapa combinado no plano; pausa antes de fases com modelo
    diferente do atual mantida. Atualizar premissa 7 do
    `workflow-agentes-dev.md` e `tests/agents/test_devflow.py`.
  - **Acceptance criteria**: sem menu rígido numerado; sugestão +
    liberdade explícitas; mapa no plano; pausa mantida; testes verdes.
  - **Verification**: `.venv/bin/pytest tests/agents/test_devflow.py`.
  - **Dependencies**: Task 1
  - **Files likely touched**: `harness-conf/agents/devflow.md`,
    `docs/workflow-agentes-dev.md`, `tests/agents/test_devflow.py`
  - **Estimated scope**: Small

### Checkpoint: Complete
- [x] Suíte completa verde (WSL): `.venv/bin/pytest -m "unit or tools or opencode"`
  (675 passed, 2 deselected copilot)
- [ ] Suíte Copilot executada no Windows pelo humano
- [x] Bootstrap re-executado com sucesso (WSL: links + AGENTS.md gerados);
  reindexação do codebase-memory fica como pendência para o humano
- [x] Pronto para revisão final

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Reestruturação quebra symlinks/instalações existentes | High | Re-executar bootstrap pós-merge; instruir no commit |
| Termo "harness" confundir agentes (histórico) | Med | Body conceitual no commit da Task 1; base define o termo |
| `~/.config/opencode/AGENTS.md` gerenciado pelo codebase-memory-mcp conflitar com o symlink | High | Investigação obrigatória na Task 4; sem decisão segura, bloquear |
| Skills upstream com prompt injection | High | Revisão de segurança obrigatória na Task 3; fallback definido; SHA no UPSTREAM.md |
| Índice codebase-memory desatualizado após o move | Med | Reindexar (checkpoint final); testes não dependem do índice |
| Adapter Copilot só validável no Windows | Med | Testes copilot no ambiente alvo (humano executa); pytest.fail sem skip |
| Base referenciar skills ainda não importadas | Med | Task 3 (importação) é dependência da Task 4 (base) |
| doc-readme.md maior após fusão | Low | Leitura por seção (agents leem seções específicas) |
| Skill nova não ser ativada corretamente | Med | Description rica em triggers; teste de consistência |

## Open Questions

- Nenhuma. Curadoria da base concluída (Anexo A aprovado). Ações
  pós-implementação (Checkpoint Complete): re-executar bootstrap nos
  dois ambientes e reindexar codebase-memory.

## Anexo A — Conteúdo final do `harness-conf/AGENTS.base.md`

> Executor: copiar literalmente (sem os marcadores de citação), sem citar
> o plano.

```markdown
# Regras Globais

## Comunicação

### Língua
- Escreva em PT-BR (ASCII aceitável). Use acentuação em todo texto em
  PT-BR.

### Perfil do Humano
- O humano é analista de sistemas com foco em desenvolvimento de
  software. Use terminologia técnica e jargão da área sem cerimônia
  (código, arquitetura, testes, git, LLMs). Não explique conceitos
  básicos desses domínios.
- Ajuste o registro pela distância do domínio: em áreas adjacentes
  (infra, dados, segurança aplicada), mantenha o jargão com breve
  contexto. Em áreas afastadas (negócio, jurídico, outras engenharias),
  use linguagem menos técnica e defina termos específicos no primeiro
  uso.
- O humano lê inglês fluentemente: cite termos, mensagens de erro e
  trechos em inglês sem traduzir. A conversa permanece em PT-BR.

### Concisão
- Responda curto por padrão. Detalhe apenas quando o humano pedir ou
  quando houver risco de ambiguidade ou erro.
- Prefira bullets a parágrafos longos.
- Passou de 20-30 linhas? Resuma e pergunte se o humano quer se
  aprofundar em algum ponto.
- Texto explicativo: no máximo 30 linhas, salvo importância evidente ou
  pedido explícito do humano.
- Pode passar desse limite com bullets, desde que o total de palavras
  fique equivalente ao de 20-30 linhas corridas.

### Tom natural
- Carregue a skill `humanizer-br` no início da sessão e siga as regras
  dela em toda comunicação, inclusive nas respostas de chat.
- Carregue a skill `portugues-tecnico-controlado` ao produzir texto
  técnico (specs, docs, explicações densas).

## Geração de arquivos MD
- Limite cada linha a 120 colunas. Use word-wrap para garantir.

## Exibição de texto para copiar
- Coloque em um único bloco de código qualquer texto que o humano deva
  copiar e colar.

## Espera por tarefas
- Espere por um sinal de conclusão (evento, callback, polling de
  condição) em vez de estimar um tempo total.
- Aumente a espera em incrementos de 30 segundos. Antes de esperar mais
  de 30 segundos, peça confirmação ao humano.
- Para código que depende de uma espera, carregue a skill
  `reliable-async-operations`.

## Commits
- Siga Conventional Commits. Ao versionar, carregue a skill
  `git-workflow-and-versioning`.
- Execute `git push` apenas com confirmação explícita do humano, nunca
  de forma automática.
- Para mover ou renomear arquivo versionado, use sempre `git mv`, nunca
  delete seguido de create. Se precisar mover e editar, faça o `git mv`
  primeiro e edite depois. Sem exceção.

## Criação de Skills
- Escreva todas as instruções de ativação na description da skill.
  Ativação descrita apenas no corpo não funciona.
- Não descreva no corpo formas de ativação que não constem na
  description.
```
