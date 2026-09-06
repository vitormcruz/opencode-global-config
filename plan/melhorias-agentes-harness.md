# Plano: Melhorias em Agentes, Curadoria e Estrutura de Harness

Status: EM PLANEJAMENTO

## Overview

Ajustes no repo opencode-global-config a partir de 6 anotações do humano:
contextualização do plano na conversa, especificação executável na curadoria,
skill de spec executável extraída do analista, AGENTS.md global para harnesses,
distinção repo vs artefatos copiados, e flexibilidade de modelos no devflow.

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
  com as regras universais do humano (idioma/concisão, proibição de timeouts,
  espera determinística, Conventional Commits, codebase-memory, CLIs nativos,
  separação por ambiente, confirmação para ação, etc.). Entrega: OpenCode
  via symlink `~/.config/opencode/AGENTS.md`; Copilot via cópia para
  `~/.copilot/AGENTS.md`. Extinção do
  `.github/copilot-specific.instructions.md`, com conteúdo absorvido pela
  base. `AGENTS.md` raiz fica só com regras específicas do repo + aponta
  para a base.
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
  detalhe mora em skills, com gatilho de carregamento. Fechados até
  aqui: seção "Comunicação" completa; "Commits" mínima (Conventional
  Commits + carregar git-workflow-and-versioning ao versionar; push só
  com confirmação; git mv obrigatório); "Ação" perde o bullet de
  confirmação prévia para editar; regras de timeout de CÓDIGO saem da
  base (a proibição sintetizada migra para a skill
  reliable-async-operations — nova task). "Ação" sai INTEIRA da base
  (incluindo o bullet de perguntas-não-são-ordens — agentes livres para
  agir ao responder). Fica na base, em versão mínima (~3 linhas), apenas
  a espera do AGENTE por tarefas: preferir determinismo a tempo cego;
  escalonar +30s; acima de 30s confirmar com o humano; para código que
  espera, carregar reliable-async-operations.
- **D11 (descoberta de código é do repo, não da base)**: a regra
  codebase-memory e a referência à skill `code-explorer-priority` ficam
  no `AGENTS.md` raiz (cada repo decide usar codebase-memory). A skill
  `code-explorer-priority` absorve os detalhes operacionais do CLI
  (comandos JSON, ordem das ferramentas, busca em docs) e ganha
  description condicionada: só ativar quando o AGENTS.md do repo indicar
  codebase-memory. A tabela "Acesso por cliente" sai (comando idêntico
  nos dois harnesses). "Criação de Skills" entra na base (2 bullets).
  Comunicação do bootstrap fica no raiz; seção SmartPlanner sai do raiz
  (restrição vive no corpo do agente).

## Task List

### Phase 1: Reestruturação harness-conf/ e AGENTS.md base (D4, D5)

- [ ] **Task 1: Mover artefatos copiáveis para `harness-conf/`**
  - **Description**: criar `harness-conf/` e mover com `git mv`:
    `agents/`, `skills/`, `commands/`, `opencode.json`. Atualizar todas as
    referências de path em `src/` (bootstrap, symlinks, adapter, scaffold)
    e `tests/` — buscar por `agents/`, `skills/`, `commands/`,
    `opencode.json` e redirecionar para `harness-conf/...`. NUNCA
    simular move como delete+create: sempre `git mv`.
  - **Acceptance criteria**:
    - `harness-conf/{agents,skills,commands,opencode.json}` existem e o
      histórico git preserva renames (`git log --follow` funciona).
    - Nenhuma referência a `agents/`, `skills/`, `commands/` na raiz em
      `src/` e `tests/` (exceto `harness-conf/`).
    - Suíte verde: `.venv/bin/pytest -m "unit or tools or opencode"`.
  - **Verification**: `git log --follow harness-conf/agents/devflow.md`;
    grep de paths antigos em `src/`+`tests/`; suíte pytest.
  - **Dependencies**: None
  - **Files likely touched**: `harness-conf/**` (move),
    `src/opencode_config/**`, `tests/**`, `scripts/bootstrap_repo/**`
  - **Estimated scope**: Large (mecânico, sem mudança de comportamento)
  - **Commit**: `refactor: mover artefatos copiáveis para harness-conf/`
    com **body obrigatório** explicando: "harness" passa a significar
    plataforma de agentes (OpenCode, Copilot); o antigo harness de testes
    chama-se `testes-produto` (ver commits 771b31a/1c9ef66).

- [ ] **Task 2: Adapter Copilot — origens em `harness-conf/`**
  - **Description**: ajustar `src/opencode_config/adapters/copilot.py`
    para ler agentes/skills/comandos/default-artifacts de `harness-conf/`.
    Atualizar testes do adapter.
  - **Acceptance criteria**: adapter aponta para `harness-conf/`; testes
    `tests/adapters/` verdes.
  - **Verification**: `.venv/bin/pytest tests/adapters -m "unit or tools"`.
  - **Dependencies**: Task 1
  - **Files likely touched**: `src/opencode_config/adapters/copilot.py`,
    `tests/adapters/**`
  - **Estimated scope**: Small

- [ ] **Task 3: `harness-conf/AGENTS.base.md` + extinção do copilot-specific**
  - **Description**: criar `harness-conf/AGENTS.base.md` com as regras
    universais migradas do `AGENTS.md` raiz (idioma, concisão, word-wrap
    120 col, proibição de timeouts, espera determinística, texto
    copiável, confirmação para ação, Conventional Commits) + conteúdo do
    `.github/copilot-specific.instructions.md` (codebase-memory, CLIs
    nativos, separação por ambiente, comunicação de bootstrap). Extinção:
    `git rm .github/copilot-specific.instructions.md`. Adapter passa a
    copiar `AGENTS.base.md` → `~/.copilot/AGENTS.md`. Bootstrap cria
    symlink `~/.config/opencode/AGENTS.md` → `harness-conf/AGENTS.base.md`.
    `AGENTS.md` raiz fica somente com regras específicas do repo + link
    para a base. Arquivo autocontido — não citar plano/decisões. Se o
    Copilot exigir path diferente de `~/.copilot/AGENTS.md` para
    instruções globais, reportar bloqueio ao revisor em vez de
    improvisar.
    **Mapa de migração seção-por-seção** (migrar sem reescrever
    semântica; conteúdo final pode ser curado pelo humano — ver Open
    Questions):
    - Do `AGENTS.md` raiz → base: Idioma (PT-BR+acentuação); Concisão;
      Geração de arquivos MD (wrap 120); Proibição de timeouts genéricos;
      Espera de tarefas (determinismo, +30s); Texto copiável (bloco
      único); Ação (confirmação explícita); Commits (Conventional
      Commits, tipos, push com confirmação, git mv).
    - Do `copilot-specific.instructions.md` → base: Prioridade de
      descoberta codebase-memory (proibições, fluxo seguro, recovery);
      Busca em docs Markdown (query_graph/Section); CLIs nativos
      (codebase-memory, crwl); Separação por ambiente (WSL/Linux vs
      Windows); Comunicação do bootstrap (docling, TLS); Fallback
      estrito.
    - Ficam no `AGENTS.md` raiz: descoberta de código/doc (aponta para a
      base + tabela por cliente), atalho "configure este repo", links
      simbólicos (paths `harness-conf/`), bootstrap, upstream de skills,
      sincronização workflow↔agentes, regras de testes do repo,
      dependências do README, restrição SmartPlanner.
    **Investigação obrigatória**: `~/.config/opencode/AGENTS.md` já
    existe e é gerenciado pelo `codebase-memory-mcp` (bloco
    `codebase-memory-mcp:start`). Definir convivência antes do symlink:
    se a base absorve os marcadores da ferramenta, se o bootstrap
    concatena, ou se a ferramenta gerencia outro caminho. Sem decisão
    segura aqui, reportar bloqueio — não substituir o arquivo gerado.
  - **Acceptance criteria**:
    - Base contém as regras universais; `AGENTS.md` raiz sem duplicá-las.
    - `.github/copilot-specific.instructions.md` removido; testes do
      adapter que o referenciavam atualizados para `AGENTS.base.md`.
    - Testes de bootstrap cobrem o novo symlink.
  - **Verification**: suíte pytest; teste de adapter verde.
  - **Dependencies**: Task 1
  - **Files likely touched**: `harness-conf/AGENTS.base.md` (novo),
    `AGENTS.md`, `src/opencode_config/**`, `tests/**`
  - **Estimated scope**: Medium

- [ ] **Task 4: Mapa de estrutura no README e docs**
  - **Description**: `README.md` ganha seção de estrutura distinguindo
    `harness-conf/` (copiado para os harnesses) vs infra do repo
    (`scripts/`, `src/`, `tests/`, `docs/`, `adapters/`, `plan/`).
    Atualizar paths textuais em `docs/workflow-*.md` e no `AGENTS.md`
    raiz (seções "Sincronização de Adaptadores" e "Links Simbólicos").
  - **Acceptance criteria**: README descreve a divisão; nenhum path
    antigo solto em docs/AGENTS.md.
  - **Verification**: grep de `agents/`/`skills/` em `README.md`,
    `AGENTS.md`, `docs/*.md` sem falso positivo.
  - **Dependencies**: Task 1
  - **Files likely touched**: `README.md`, `AGENTS.md`, `docs/*.md`
  - **Estimated scope**: Small

### Checkpoint: Phase 1
- [ ] Suíte completa verde (WSL): `.venv/bin/pytest -m "unit or tools or opencode"`
- [ ] Bootstrap re-executado com sucesso (symlinks novos funcionam)
- [ ] Commits criados (Task 1 com body conceitual)
- [ ] Review com humano antes de prosseguir

### Phase 2: Curadoria unificada no docs/README.md (D2, D3)

- [ ] **Task 5: Fundir templates default-artifacts**
  - **Description**: `doc-readme.md` absorve o conteúdo de
    `testes-produto.md` como seção "Testes por Especialidade" (suítes,
    orquestrador, interface JSON, proibições). O template declara: o doc
    é meta-informação que ajuda o agente a criar os scripts; os scripts
    têm testes próprios cobrindo o que o doc especifica (spec executável
    dos scripts), executados SOMENTE quando os scripts mudam; testes da
    aplicação rodam nas fases de Testes do workflow. `git rm` do
    `testes-produto.md`.
  - **Acceptance criteria**: seção completa no `doc-readme.md`; distinção
    dois-níveis explícita; arquivo antigo removido com `git rm`.
  - **Verification**: leitura do template; grep sem referências ao
    arquivo removido.
  - **Dependencies**: Task 1 (paths)
  - **Files likely touched**:
    `harness-conf/agents/default-artifacts/doc-readme.md`,
    `harness-conf/agents/default-artifacts/testes-produto.md` (rm)
  - **Estimated scope**: Small

- [ ] **Task 6: Curador e mensagens de curadoria**
  - **Description**: `curador-produto.md`: entrevista sem spec separado —
    docs/README.md com a seção; `AGENTS.md` do projeto-alvo mantém tabela
    + link âncora; curador orienta o humano sobre spec executável dos
    scripts e os dois níveis de teste (D3). `mensagens-curadoria.md`
    atualizada (um artefato só).
  - **Acceptance criteria**: nenhum fluxo gravando `docs/testes-produto.md`;
    orientação de spec executável presente; mensagens coerentes.
  - **Verification**: `tests/agents/test_curador_produto.py` atualizado e
    verde.
  - **Dependencies**: Task 5
  - **Files likely touched**:
    `harness-conf/agents/curador-produto.md`,
    `harness-conf/agents/references/mensagens-curadoria.md`,
    `tests/agents/test_curador_produto.py`
  - **Estimated scope**: Medium

- [ ] **Task 7: Scaffold unificado**
  - **Description**: `scaffold_mapa.py`: `DOC_TEMPLATE` ganha a seção
    "Testes por Especialidade"; `TESTES_PRODUTO_TEMPLATE` (tabela do
    AGENTS.md) linka para âncora da seção no `docs/README.md` (não mais
    arquivo próprio). Atualizar `tests/scaffold/test_mapa_produto.py`.
  - **Acceptance criteria**: scaffold gera doc com a seção; tabela do
    AGENTS.md aponta para `docs/README.md#testes-por-especialidade`;
    testes verdes.
  - **Verification**: `.venv/bin/pytest tests/scaffold -m "unit or tools"`.
  - **Dependencies**: Task 5
  - **Files likely touched**: `src/opencode_config/cli/scaffold_mapa.py`,
    `tests/scaffold/test_mapa_produto.py`
  - **Estimated scope**: Medium

- [ ] **Task 8: Referências nos agentes e workflows**
  - **Description**: substituir leituras de `docs/testes-produto.md` por
    "seção Testes por Especialidade do docs/README.md" em:
    `devflow.md`, `eng-software.md`, `qa.md`, `sec.md`, `dba.md`,
    `rev.md`, `front.md` e em `docs/workflow-agentes-dev.md` +
    `workflow-definicao-escopo.md`. Explicitar os dois níveis de teste
    (D3) em `devflow.md`, `qa.md`, `eng-software.md` e
    `curador-produto.md`. Verificar coerência de
    `agents/references/interface-testes-produto.md`.
  - **Acceptance criteria**: zero referências ao arquivo extinto; dois
    níveis descritos nos agentes-chave; `tests/agents/` verde.
  - **Verification**: grep `testes-produto.md` (sem falso positivo);
    `.venv/bin/pytest tests/agents -m "unit or tools"`.
  - **Dependencies**: Task 5
  - **Files likely touched**: `harness-conf/agents/*.md`,
    `docs/workflow-*.md`, `tests/agents/**`
  - **Estimated scope**: Medium

### Checkpoint: Phase 2
- [ ] Suíte agents+scaffold+adapters verde
- [ ] Curadoria coerente end-to-end (templates, curador, scaffold, agentes)
- [ ] Review com humano antes de prosseguir

### Phase 3: Skill spec-executavel (D8)

- [ ] **Task 9: Criar a skill `spec-executavel`**
  - **Description**: criar
    `harness-conf/skills/spec-executavel/SKILL.md`, autocontido (sem
    citar plano/decisões): princípio central do item 8 (spec é ótima
    quando o humano mexe no texto e o teste quebra — linkar valores das
    regras ao código de teste); itens 1-10; Gherkin como recomendação
    forte com cláusula de exceção (avaliar adequação, propor alternativa
    ao humano; ex.: tabela para permissionamento); MD favorecido;
    rastreabilidade por link à origem; agnóstica de ferramenta
    (Concordion apenas como exemplo). Description da skill rica em
    triggers (regra de ativação do repo). Conteúdo dos itens (lista
    canônica, redigir em linguagem autocontida na skill):
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
       texto e o teste quebra; linkar ao máximo os valores definidos nas
       regras ao código de teste (valores concretos e aspas duplas
       apenas para literais que mudam o veredito)
    9. Persona/perfil — só quando o foco é permissão/acesso
    10. `Esquema do Cenário` + `Exemplos` para variações da mesma regra
    FORA da skill (permanece no analista): rejeição/erro e casos limite
    só por regra de negócio/legal; INVEST; escrita/classificação de
    RF/RNF.
  - **Acceptance criteria**: SKILL.md completo e autocontido; nome
    válido (mesmo padrão das existentes); registra no comando
    `opencode-skills list` se aplicável.
  - **Verification**: teste de boilerplate/consistência de skills verde.
  - **Dependencies**: Task 1
  - **Files likely touched**: `harness-conf/skills/spec-executavel/SKILL.md`
  - **Estimated scope**: Medium

- [ ] **Task 10: Referenciar a skill nos agentes**
  - **Description**: `analista.md`: seção 3B e "Padrão de qualidade"
    passam a referenciar a skill + **fechamento para Gherkin** (desvio só
    pela cláusula de exceção, com o humano); INVEST, RF/RNF e item 11
    permanecem no corpo. `eng-software.md`, `sec.md`, `qa.md`: skill
    obrigatória na capacidade de criar specs executáveis.
    `curador-produto.md`: referência de orientação na entrevista.
    Atualizar `tests/agents/test_workflow_consistency.py` e afins.
  - **Acceptance criteria**: todos os agentes referenciam a skill e ela
    existe; analista mantém regras próprias (RF/RNF, item 11); testes de
    consistência verdes.
  - **Verification**: `.venv/bin/pytest tests/agents -m "unit or tools"`.
  - **Dependencies**: Task 9
  - **Files likely touched**: `harness-conf/agents/analista.md`,
    `harness-conf/agents/eng-software.md`, `harness-conf/agents/sec.md`,
    `harness-conf/agents/qa.md`, `harness-conf/agents/curador-produto.md`,
    `tests/agents/**`
  - **Estimated scope**: Medium

### Checkpoint: Phase 3
- [ ] Skill criada e referenciada; consistência verde
- [ ] Review com humano antes de prosseguir

### Phase 4: Protocolo conversacional e devflow (D6, D7)

- [ ] **Task 11: Cláusula de contextualização na question-orchestration**
  - **Description**: adicionar à
    `harness-conf/skills/question-orchestration/SKILL.md` cláusula:
    quando existir artefato de planejamento/estado persistido, toda
    interação com o humano carrega o contexto relevante (fase, decisões
    que afetam a pergunta, escopo). Motivação explícita na cláusula:
    o plano é artefato do agente; o humano não o está lendo; nunca
    presumir conhecimento do plano. Atualizar
    `tests/agents/test_question_orchestration_adoption.py`.
  - **Acceptance criteria**: cláusula presente na skill (fonte única);
    testes de adoção verdes.
  - **Verification**: `.venv/bin/pytest tests/agents/test_question_orchestration_adoption.py`.
  - **Dependencies**: Task 1
  - **Files likely touched**:
    `harness-conf/skills/question-orchestration/SKILL.md`,
    `tests/agents/test_question_orchestration_adoption.py`
  - **Estimated scope**: Small

- [ ] **Task 12: Devflow flexível na seleção de modelo**
  - **Description**: reescrever a seção "Seleção de modelo por fase" de
    `devflow.md`: devflow **sugere** padrão (um modelo por etapa —
    planejamento, execução, testes, revisão) e avisa que o humano define
    como preferir (um modelo, por fase granular, arranjo próprio);
    registra o mapa combinado no plano; continua pausando antes de fases
    com modelo diferente do atual. Atualizar premissa 7 de
    `docs/workflow-agentes-dev.md` e `tests/agents/test_devflow.py`.
  - **Acceptance criteria**: sem menu rígido numerado; sugestão + liberdade
    explícitas; mapa registrado no plano; pausa mantida; testes verdes.
  - **Verification**: `.venv/bin/pytest tests/agents/test_devflow.py`.
  - **Dependencies**: Task 1
  - **Files likely touched**: `harness-conf/agents/devflow.md`,
    `docs/workflow-agentes-dev.md`, `tests/agents/test_devflow.py`
  - **Estimated scope**: Small

### Checkpoint: Complete
- [ ] Suíte completa verde (WSL): `.venv/bin/pytest -m "unit or tools or opencode"`
- [ ] Suíte Copilot executada no Windows pelo humano
- [ ] Bootstrap re-executado; codebase-memory reindexado
- [ ] Pronto para revisão final

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Reestruturação quebra symlinks/instalações existentes | High | Re-executar bootstrap pós-merge; instruir no commit |
| Termo "harness" confundir agentes (histórico) | Med | Body conceitual no commit da Task 1; AGENTS.base.md define o termo |
| Índice codebase-memory desatualizado após o move | Med | Reindexar (checkpoint final); testes não dependem do índice |
| Adapter Copilot só validável no Windows | Med | Testes copilot rodam no ambiente alvo (humano executa); pytest.fail sem skip |
| doc-readme.md maior após fusão | Low | Leitura por seção (agents leem seções específicas) |
| Skill nova não ser ativada corretamente | Med | Description rica em triggers; teste de consistência D11 |
| `~/.config/opencode/AGENTS.md` já gerenciado pelo codebase-memory-mcp conflitar com o symlink da base | High | Investigação obrigatória na Task 3; sem decisão segura, reportar bloqueio em vez de substituir arquivo gerado |

## Open Questions

- **Q1 (conteúdo do AGENTS.base.md)**: curadoria em andamento (opção "a"
  escolhida). Concluídas: seção "Comunicação" completa (Língua, Perfil
  do Humano, Concisão, Tom natural com skills no chat). Restam:
  autonomia/segurança, git, descoberta de código, seções cinzentas.
- **Q2 (humanizer-br)**: RESOLVIDA — importar `humanizer-br` (MIT
  confirmado) com revisão de segurança; fallback `phardoom/humanizador`.

