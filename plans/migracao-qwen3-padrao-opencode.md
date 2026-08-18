# Implementation Plan: Migracao do Qwen3-0.6B como padrao OpenCode

## Overview

Promover Qwen3-0.6B Q8_0 como modelo e provider padrao da integracao OpenCode
no WSL/Linux. Bonsai 27B Q1_0 permanece um fallback manual por
`--local-model bonsai`; nao havera selecao automatica, fallback silencioso,
alteracao para Copilot nem trabalho sobre Needle 2. O runtime continua local:
o host serve llama.cpp ao container pela rede Docker interna, sem telemetria,
handoff em cloud ou egress em tempo de execucao. Apos o provisionamento
verificado em cache, a execucao permanece offline.

## Architecture Decisions

- **D1 - Qwen como contrato padrao:** `qwen3-0.6b` sera o valor padrao unico
  do servidor, da opcao pytest e da configuracao estatica de integracao. O
  provider sera `qwen-local/qwen3-0.6b`.
- **D2 - Bonsai somente opt-in:** manter ambos os artefatos fixados e usar o
  contrato ja existente `--local-model bonsai`; nao introduzir fallback
  automatico quando o Qwen estiver indisponivel.
- **D3 - Isolamento preservado:** manter o endpoint
  `host.docker.internal:8080/v1`, a rede `opencode-test-net --internal`, o
  proxy localhost e a configuracao efetiva com exatamente um provider local.
- **D4 - Provisionamento delimitado:** o bootstrap continua sem baixar pesos.
  O harness provisiona sob demanda binario Prism e pesos Qwen no cache do
  usuario, valida o SHA-256 do Qwen e reutiliza somente artefatos ja em cache
  para execucao offline.
- **D5 - Timeouts imutaveis:** os valores existentes permanecem como protecao
  de falha; a migracao nao adiciona, remove nem ajusta timeouts.
- **D6 - Registro arquitetural:** criar um ADR que substitua, apenas para esta
  integracao, as decisoes de modelo unico/Bonsai padrao do ADR-0002, sem
  reescrever o historico daquela decisao.

## Task List

### Phase 1: Contrato padrao e provisionamento

## Task 1: Inverter o modelo padrao em todas as entradas OpenCode

**Description:** Alterar o contrato canonico para Qwen e alinhar o seletor
pytest, o contexto gerado e o JSON-base de integracao. Preservar a selecao
explicita de Bonsai e a geracao por spec para que nenhum provider externo seja
declarado.

**Acceptance criteria:**
- [ ] `pytest -m opencode` usa `qwen-local/qwen3-0.6b` sem argumento extra.
- [ ] `pytest -m opencode --local-model bonsai` usa exclusivamente
  `bonsai-local/bonsai-27b`.
- [ ] O JSON estatico e os contextos gerados fixam um unico provider local e os
  agentes `plan` e `build` usam o modelo selecionado.

**Verification:**
- [ ] Executar os testes unitarios do seletor, contexto e provider local.
- [ ] Inspecionar a configuracao gerada para os caminhos padrao e Bonsai.

**Dependencies:** None.

**Files likely touched:**
- `tests/conftest.py`
- `tests/integration/model/bonsai_server.py`
- `tests/integration/integration_context.py`
- `tests/integration/config/opencode.test.json`

**Estimated scope:** M (4 files).

**Local commit checkpoint:** `feat(integracao): define qwen como modelo padrao`
apos os testes unitarios desta unidade logica.

## Task 2: Cobrir o contrato Qwen padrao e o fallback Bonsai

**Description:** Atualizar testes unitarios e nomenclaturas de assercoes para
que o padrao Qwen seja explicito, Bonsai seja validado somente por opt-in e o
servidor continue recusando reutilizar com seguranca um endpoint de modelo
divergente. Manter checksum Qwen, cache e argumentos existentes do
llama-server.

**Acceptance criteria:**
- [ ] Os testes verificam o artefato, provider e identidade padrao Qwen.
- [ ] Um teste prova a selecao explicita do Bonsai sem alterar o padrao.
- [ ] Nenhum teste ou producao adiciona ou modifica timeout existente.

**Verification:**
- [ ] Executar testes unitarios em `tests/conftest.py`,
  `tests/integration/model/`, `tests/integration/test_integration_context.py`
  e `tests/integration/docker/test_local_provider.py`.

**Dependencies:** Task 1.

**Files likely touched:**
- `tests/integration/model/test_bonsai_server.py`
- `tests/integration/test_integration_context.py`
- `tests/integration/docker/test_local_provider.py`
- `tests/integration/test_prompts.py`
- `tests/integration/test_behavioral_helper.py`

**Estimated scope:** M (5 files).

**Local commit checkpoint:** `test(integracao): cobre qwen padrao e bonsai opt-in`
apos a suite unitaria alvo.

### Checkpoint: Contrato e provisionamento

- [ ] No WSL/Linux, os testes unitarios alvo passam com `.venv/bin/pytest`.
- [ ] O padrao, o fallback e a integridade do Qwen estao cobertos sem
  provisionamento pelo bootstrap.

### Phase 2: Privacidade e documentacao operacional

## Task 3: Manter enforcement de privacidade independente do modelo

**Description:** Tornar as mensagens e os testes de privacidade neutros quanto
ao modelo, mantendo a assercao do provider selecionado, endpoint localhost,
rede interna e bloqueio de egress para Qwen padrao e Bonsai opt-in.

**Acceptance criteria:**
- [ ] A suite padrao executa os quatro controles de privacidade contra Qwen.
- [ ] A execucao explicita com Bonsai mantem os mesmos controles.
- [ ] A configuracao efetiva nao contem provider remoto, telemetria, proxy
  externo ou handoff em cloud.

**Verification:**
- [ ] Executar `.venv/bin/pytest -m opencode` no WSL/Linux com Docker.
- [ ] Executar `.venv/bin/pytest -m opencode --local-model bonsai` no mesmo
  ambiente.

**Dependencies:** Tasks 1-2.

**Files likely touched:**
- `tests/integration/test_privacy_enforcement.py`
- `tests/integration/conftest.py`
- `tests/integration/test_prompts.py`

**Estimated scope:** S (3 files).

**Local commit checkpoint:** `test(privacidade): valida qwen local padrao`
apos as duas execucoes OpenCode.

## Task 4: Documentar operacao, decisao e rollback

**Description:** Atualizar o README para apresentar Qwen como padrao, explicar
o provisionamento sob demanda e o comando Bonsai opt-in. Registrar em novo ADR
a substituicao de decisao e atualizar o experimento com o resultado final,
mantendo Needle 2 explicitamente fora de escopo.

**Acceptance criteria:**
- [ ] A documentacao mostra o comando padrao e o comando explicito para Bonsai.
- [ ] Documenta cache local, checksum Qwen, execucao offline apos
  provisionamento, ausencia de telemetria e prerequisito Docker no WSL/Linux.
- [ ] O ADR contem motivacao, escopo, decisoes substituidas, consequencias e
  rollback manual para Bonsai; nao altera o ADR-0002 historico.

**Verification:**
- [ ] Conferir que todos os comandos documentados usam
  `.venv/bin/pytest -m opencode` no WSL/Linux.
- [ ] Conferir que nao ha instrucao de cloud, telemetria, Needle 2 ou alteracao
  de timeout.

**Dependencies:** Tasks 1-3.

**Files likely touched:**
- `README.md`
- `docs/experimentos/modelos-locais.md`
- `docs/adr/0003-qwen3-padrao-integracao-opencode.md`

**Estimated scope:** S (3 files).

**Local commit checkpoint:** `docs(integracao): documenta qwen padrao`
apos revisao cruzada entre documentacao e codigo.

### Checkpoint: Complete

- [ ] No WSL/Linux com Docker, `.venv/bin/pytest -m opencode` passa com Qwen
  padrao.
- [ ] No mesmo ambiente, `.venv/bin/pytest -m opencode --local-model bonsai`
  passa como fallback opt-in.
- [ ] Os testes de privacidade permanecem quatro de quatro em cada selecao.
- [ ] O cache permite repetir as execucoes sem download; nao ha egress em
  runtime, telemetria ou handoff em cloud.
- [ ] Nao ha alteracao de timeout nem escopo relacionado a Needle 2.
- [ ] A implementacao esta pronta para revisao independente.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Referencia Bonsai permanecer como padrao | Medio | Cobrir seletor, JSON-base, contextos e fixtures no mesmo checkpoint. |
| Regressao de isolamento ao inverter provider | Alto | Executar enforcement de config, endpoint e rede para Qwen e Bonsai. |
| Cache ausente exigir rede | Medio | Separar provisionamento explicito da execucao e documentar a repeticao offline. |
| Endpoint antigo Qwen/Bonsai ocupar a porta | Medio | Preservar a reconciliacao segura por identidade existente; nao matar processo externo. |
| Rollback urgente | Baixo | Usar `--local-model bonsai`; o contrato e os pesos Bonsai continuam suportados. |
| Alterar acidentalmente a politica de timeout | Medio | Tratar constantes e argumentos atuais como invariantes e revisar o diff. |

## Open Questions

- Nenhuma para a implementacao: o seletor `--local-model bonsai` existente e o
  mecanismo de fallback aprovado.
