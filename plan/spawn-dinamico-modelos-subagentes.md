# Plano: spawn dinâmico de subagentes com modelo por chamada (OpenCode)

Status: PLANO COMPLETO (aguardando aprovação do humano)

Base: esboço anterior em `plan/plugin-opencode-task-model.md` (não executado).

## Overview

Permitir que orquestradores do OpenCode spawnem subagentes com modelo
escolhido **por chamada**, sem agente pré-criado por modelo (padrão
atual do `worker`). Solução: adotar o plugin npm `opencode-task-model`
(pin exato), que sobrescreve a tool `task` nativa adicionando `model`,
`reasoning`, `background` e `worktree` por chamada. O plano inclui
revisão de segurança obrigatória do upstream, aplicação no repo
(config + docs + guarda de comportamento), teste automatizado de
integração que valida o spawn dinâmico com dois modelos reais
distintos, runbook de validação funcional com evidências, e produção de
insumo autocontido para o devflow revisar e promover a aderência ao
repo depois (o devflow não pode atuar agora por causa dessa própria
restrição).

## Architecture Decisions

- **D1 — Base da solução: plugin upstream pinado.** Adotar
  `opencode-task-model` (npm, versão pinada exata) via
  `harness-conf/opencode.json`, precedido de revisão de segurança
  obrigatória do código upstream (SHA + diff do tarball npm), com status
  PROVISÓRIO até o OpenCode suportar `model` nativamente na `task`.
  Descartadas: plugin próprio (vocação de fork) e aguardar nativo
  (bloqueia o objetivo).
- **D2 — Validação: automatizada + runbook.** Teste pytest (marker
  `integration`) validando instalação e resolução dinâmica de model no
  spawn, mais runbook de validação funcional com dois modelos reais
  distintos e evidência registrada no insumo. Requisito central: spawnar
  subagentes com modelos diferentes, sem agente pré-criado por modelo.
- **D3 — Worker mantém fallback.** `harness-conf/agents/worker.md`
  continua com `model:` no frontmatter como fallback canônico; o plugin
  não altera a precedência nativa sem argumento explícito. Migração dos
  orquestradores para model por chamada fica para ciclo posterior.
- **D4 — Insumo para o devflow: revisão + aderência ao repo.** O
  documento final pede que o devflow revise o que foi implementado e
  promova a aderência ao repo (consistência com regras, workflows e
  testes de consistência existentes). Sem sugestões novas de adoção ou
  funcionalidade.
- **D5 — Teste automatizado usa dois modelos reais.** O teste de
  integração consome providers reais (custo desprezível em modelos
  flash; premissa: credenciais no ambiente). Não restringir ao Qwen
  local do `agent_eval`.
- **D6 — Modelos da validação: zai flash + zai.** `zai-coding-plan/
  glm-5.3-flash` e `zai-coding-plan/glm-5.3` (provider já configurado),
  para o teste automatizado e para o runbook.
- **D7 — Validação pelo caminho real de uso.** O teste automatizado
  exercita o fluxo que os agentes usam: um agente primário headless
  (`opencode run`) chama a tool `task` (com o plugin) passando `model`
  explícito. Proibido chamar API de provider diretamente ou criar
  sessão child por fora da tool `task`. Verificação do modelo efetivo
  pelo storage local de sessões do OpenCode (`modelID` da child).
- **D8 — Commit final remove plano e esboço; insumo do devflow
  permanece.** No commit final do fluxo, `git rm` remove este plano E o
  esboço `plan/plugin-opencode-task-model.md`. O
  `plan/insumo-devflow-spawn-dinamico.md` é artefato de produção e
  permanece no repo até o devflow consumir.

## Task List

### Phase 0 — Barreira de segurança (obrigatória, antes de qualquer
aplicação)

- [ ] **Task 1: Revisão de segurança do upstream**
  **Description:** clonar o upstream em `/tmp/opencode`, confirmar a
  versão vigente (`npm view opencode-task-model version`) e fixar o SHA
  do commit da release correspondente ao pin. Ler TODO o código que
  roda no processo do OpenCode (`src/`, entrypoints, scripts de
  build/publish) procurando: prompt injection, comandos shell
  inesperados, URLs externas, escrita fora do escopo, exfiltração.
  Conferir o diff entre o SHA revisado e o tarball publicado
  (`npm pack opencode-task-model@<versao>`). Confirmar também os
  identificadores vigentes de rastreio do suporte nativo (issue
  anomalyco/opencode#6651 confirmada; PR de `model` na task em review,
  número a confirmar). Go/no-go: findings bloqueantes abortam e voltam
  ao planejador/humano.
  **Acceptance criteria:**
  - [ ] SHA do commit upstream da versão pinada registrado.
  - [ ] Todo código executável lido; findings classificados
        (bloqueante / risco / limpo).
  - [ ] Diff SHA ↔ tarball npm conferido e registrado.
  - [ ] `harness-conf/plugins/opencode-task-model/UPSTREAM.md` criado
        com origem, SHA, data, findings e instruções de sync (padrão de
        skills, adaptado para plugin).
  - [ ] Números de rastreio confirmados e corrigidos se divergentes do
        esboço.
  **Verification:** UPSTREAM.md completo; decisão go/no-go registrada
  nele.
  **Dependencies:** None.
  **Files likely touched:** `harness-conf/plugins/opencode-task-model/
  UPSTREAM.md` (novo).
  **Estimated scope:** S.

### Checkpoint: Phase 0
- [ ] Commit: `docs(plugin): registra revisao de seguranca do
      opencode-task-model`
- [ ] Revisão de segurança aprovada (go) antes de prosseguir.

### Phase 1 — Aplicação no repo

- [ ] **Task 2: Plugin no config + docs + guarda de comportamento**
  **Description:** editar `harness-conf/opencode.json` (array `plugin`
  com pin exato `opencode-task-model@<X.Y.Z>`); adicionar seção
  "Plugins" no `README.md` (após "Variáveis de ambiente") documentando
  o plugin, status PROVISÓRIO, rastreio e comando de atualização do
  pin; adicionar a guarda no `harness-conf/AGENTS.base.md` (texto do
  esboço: omitir `model`/`reasoning` por padrão, usar apenas quando o
  briefing pedir; `background: true` só com escopo aprovado e
  preferindo `worktree: true`; prompts delegados não resolvem
  `@arquivo`, incluir conteúdo no texto). Sem mudanças em `src/` nem
  `adapters/`.
  **Acceptance criteria:**
  - [ ] `harness-conf/opencode.json` válido com pin exato.
  - [ ] README com seção Plugins (status PROVISÓRIO + rastreio).
  - [ ] Guarda presente no `AGENTS.base.md`.
  - [ ] Nenhum arquivo de `src/`, `adapters/` ou `tests/` alterado.
  **Verification:** `python -m json.tool harness-conf/opencode.json`;
  rodar o bootstrap do repo e confirmar propagação para o ambiente.
  **Dependencies:** Task 1 (go).
  **Files likely touched:** `harness-conf/opencode.json`, `README.md`,
  `harness-conf/AGENTS.base.md`.
  **Estimated scope:** S.

- [ ] **Task 3: Testes unitários de pin e paridade**
  **Description:** criar `tests/test_opencode_plugins.py` (marker
  `unit`): (1) todo entry de `plugin` no config tem pin exato semver;
  (2) o plugin provisório aparece no README com "PROVISÓRIO" (par
  config↔README como lembrete de remoção).
  **Acceptance criteria:**
  - [ ] Teste de pin rejeita `@latest`, range ou ausência de versão.
  - [ ] Teste de paridade quebra se o plugin sumir do config ou do
        README isoladamente.
  - [ ] Suíte completa do ambiente corrente verde (`-m all`).
  **Verification:** `.venv/bin/pytest -m all` (WSL/Linux) ou
  `.\.venv\Scripts\pytest.exe -m all` (Windows).
  **Dependencies:** Task 2.
  **Files likely touched:** `tests/test_opencode_plugins.py` (novo).
  **Estimated scope:** S.

### Checkpoint: Phase 1
- [ ] Suíte `-m all` verde.
- [ ] Commit: `feat(harness): adiciona plugin provisorio
      opencode-task-model`
- [ ] OpenCode reiniciado com plugin carregado (tool `task` expondo os
      args novos), precedência nativa preservada sem `model`.

### Phase 2 — Validação automatizada do spawn dinâmico

- [ ] **Task 4: Validação automatizada via caminho real de uso**
  **Description:** teste pytest (marker `integration`) que executa o
  OpenCode headless (`opencode run`) com o plugin carregado em contexto
  próprio — o `tests/integration/integration_context.py` padrão zera
  `config["plugin"]`, então o teste precisa de contexto que preserve o
  plugin. O prompt instrui um agente primário a spawnar subagente
  built-in SEM `model` no frontmatter (ex.: `general`) usando a tool
  `task` com `model` explícito `zai-coding-plan/glm-5.3-flash` e, em
  seguida, `zai-coding-plan/glm-5.3`. O consumo do provider acontece
  dentro do OpenCode; o teste NUNCA chama API de provider diretamente
  nem cria sessão child por fora da tool `task`. Verificar o modelo
  efetivo de cada child lendo o storage local de sessões do OpenCode
  (`modelID`). Caso negativo: sem `model`, precedência nativa (model do
  agente, senão herdado do pai). Sem `skip`: `pytest.fail` com
  mensagem acionável se faltar pré-requisito (plugin, providers
  configurados).
  **Acceptance criteria:**
  - [ ] Dois spawns reais via tool `task` (com plugin) com models
        distintos, na mesma execução.
  - [ ] Modelo efetivo de cada child verificado via storage de
        sessões do OpenCode.
  - [ ] Caso negativo (sem `model`) preserva precedência nativa.
  - [ ] Contexto de teste não zera o plugin.
  - [ ] Nenhuma chamada direta a API de provider; nenhum spawn fora
        da tool `task`.
  - [ ] Suíte `-m all` do ambiente corrente verde.
  **Verification:** `.venv/bin/pytest -m integration` (e `-m all`
  completo) verde; custo mínimo (spawns flash).
  **Dependencies:** Tasks 2-3.
  **Files likely touched:** `tests/integration/` (teste novo + ajuste
  de contexto/fixture).
  **Estimated scope:** M.

### Checkpoint: Phase 2
- [ ] Commit: `test(integration): valida spawn dinamico com modelos
      distintos via task`
- [ ] Evidência do teste anotada para o insumo (modelos efetivos,
  IDs de sessão).

### Phase 3 — Validação funcional (runbook) e insumo para o devflow

- [ ] **Task 5: Runbook de validação funcional executado**
  **Description:** runbook reproduzível (vive como seção do insumo)
  executando o cenário real: numa sessão OpenCode reiniciada com o
  plugin, o orquestrador spawna o MESMO subagente built-in duas vezes,
  uma com `zai-coding-plan/glm-5.3-flash` e outra com
  `zai-coding-plan/glm-5.3`, sem nenhum agente pré-criado por modelo;
  verificar o modelo efetivo de cada child (API ou resposta do child)
  e registrar evidências (comandos, IDs, excertos).
  **Acceptance criteria:**
  - [ ] Runbook com passos reproduzíveis e forma de verificação do
        modelo efetivo.
  - [ ] Executado com sucesso: dois modelos distintos confirmados no
        mesmo tipo de subagente.
  - [ ] Evidências registradas no insumo.
  **Verification:** evidências no insumo; inspeção.
  **Dependencies:** Task 4.
  **Files likely touched:** `plan/insumo-devflow-spawn-dinamico.md`
  (novo, seção do runbook).
  **Estimated scope:** S.

- [ ] **Task 6: Insumo autocontido para o devflow**
  **Description:** escrever `plan/insumo-devflow-spawn-dinamico.md`,
  AUTOCONTIDO (sem IDs de decisão, números de task ou vocabulário
  interno deste plano), contendo: motivação (restrição do OpenCode que
  impediu usar o devflow neste ciclo); o que foi implementado (arquivos
  e comportamento novo da `task`); como foi validado (teste
  automatizado + runbook + evidências); rastreio do suporte nativo e
  procedimento de remoção; pedido ao devflow: REVISAR o que foi feito e
  promover a ADERÊNCIA ao repo (rodar suíte completa, conferir
  `tests/agents/test_workflow_consistency.py`, validar `UPSTREAM.md`
  e a seção Plugins do README, checar a guarda do `AGENTS.base.md`).
  Sem sugestões novas de adoção ou funcionalidade.
  **Acceptance criteria:**
  - [ ] Documento autocontido e autoexplicativo.
  - [ ] Evidências de validação incluídas.
  - [ ] Checklist de revisão/aderência explícito para o devflow.
  - [ ] Nenhuma referência a identificadores internos deste plano.
  **Verification:** leitura humana; checagem de ausência de
  identificadores do plano.
  **Dependencies:** Tasks 4-5.
  **Files likely touched:** `plan/insumo-devflow-spawn-dinamico.md`.
  **Estimated scope:** S.

### Checkpoint: Phase 3 (final)
- [ ] Commit: `docs(plan): valida spawn dinamico e registra insumo
      para devflow`
- [ ] Revisão independente (executor/revisor do fluxo) aprovada.
- [ ] Commit final do fluxo remove ESTE plano e o esboço
      `plan/plugin-opencode-task-model.md` (`git rm`); o
      `plan/insumo-devflow-spawn-dinamico.md` permanece no repo até o
      devflow consumir.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Plugin sobrescreve a `task` built-in para todos os agentes | Superfície de risco global | Fase 0 obrigatória (revisão + SHA + diff npm); pin exato; status PROVISÓRIO; deny rules do config como kill switch |
| Mantenedor único, adoção baixa | Abandono upstream | Pin + PROVISÓRIO + procedimento de remoção documentado (README/insumo) |
| Teste executa spawns reais dentro do OpenCode | Consome cota do provider; exige providers configurados no ambiente | Spawns em modelos flash (custo desprezível); premissa declarada; `pytest.fail` com mensagem acionável (sem `skip`) |
| Números de PR/issue de rastreio divergentes entre esboço e pesquisa | Documentação imprecisa | Task 1 confirma os identificadores vigentes antes de escrever README |
| `background: true` libera `bash`/`write`/`edit` no child | Escopo não intencional | Guarda no `AGENTS.base.md`; usar apenas com escopo aprovado e `worktree: true` |
| Spawn refeito via client API não resolve `@arquivo` em prompts delegados | Comportamento surpreendente | Guarda no `AGENTS.base.md`: incluir conteúdo no texto |
| Versão pinada desatualizada vs npm | Review de versão errada | Task 1 confere `npm view opencode-task-model version` e pina a release revisada |

## Open Questions

- Nenhuma aberta. Acompanhamento do suporte nativo upstream
  (issue #6651 + PR em review) é procedimento contínuo registrado no
  README e no insumo, com remoção do plugin quando nativo.

## Execução (registro do orquestrador)

- Plano completo apresentado e commitado (b2ac417); revisto após
  mediação: D7 (validação só pelo caminho real de uso, sem API por
  fora) e D8 (commit final remove plano + esboço; insumo do devflow
  permanece).
- Executor acordado: subagente `worker` (`zai-coding-plan/
  glm-5.3-flash`), enquanto o plugin não está instalado.
- Revisor acordado: instância `general` no modelo atual da sessão
  (`zai-coding-plan/glm-5.3`).
- Execução NÃO autorizada ainda; aguardando palavra do humano.
