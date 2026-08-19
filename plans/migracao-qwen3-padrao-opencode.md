# Implementation Plan: Migracao do Qwen3-0.6B como padrao OpenCode

## Overview

Promover Qwen3-0.6B Q8_0 como o unico modelo e provider da integracao OpenCode
no WSL/Linux e remover completamente o Bonsai do harness. Nao havera selecao
alternativa, fallback silencioso, alteracao para Copilot nem trabalho sobre
Needle 2. O runtime continua local:
o host serve llama.cpp ao container pela rede Docker interna, sem telemetria,
handoff em cloud ou egress em tempo de execucao. Apos o provisionamento
verificado em cache, a execucao permanece offline.

## Architecture Decisions

- **D1 - Qwen como contrato padrao:** `qwen3-0.6b` sera o valor padrao unico
  do servidor, da opcao pytest e da configuracao estatica de integracao. O
  provider sera `qwen-local/qwen3-0.6b`.
- **D2 - Bonsai descontinuado:** remover a spec, seletor, configuracoes, testes,
  documentacao e nomenclatura do Bonsai. Falha de provisionamento ou de
  inferencia do Qwen e explicita; nao existe fallback em runtime.
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
  integracao, as decisoes Bonsai do ADR-0002, sem reescrever o historico
  daquela decisao. O rollback e `git revert` do conjunto de migracao, nao uma
  opcao suportada do harness.
- **D7 - Runtime OpenMP user-space:** o bootstrap WSL/Linux provisionara a
  `libgomp.so.1` em cache do usuario com origem, versao e checksum fixados. O
  harness usara essa runtime para iniciar o Prism sem `sudo`, `apt` ou
  `LD_LIBRARY_PATH`; a execucao sera offline apos o provisionamento.
- **D8 - Falha orientada para acao:** se o teste nao encontrar uma runtime
  valida, deve falhar antes de subir o Prism, informar a dependencia ausente e
  orientar a executar o bootstrap. Instalacao manual so e necessaria quando o
  bootstrap reportar falha acionavel de download, integridade ou plataforma.

## Task List

### Phase 0: Runtime nativa do Prism

## Task 0: Provisionar runtime OpenMP no bootstrap

**Description:** Estender o bootstrap para WSL/Linux a fim de provisionar uma
runtime OpenMP autocontida no cache do usuario. Fixar a origem, versao,
checksum, arquitetura e termos de redistribuicao da `libgomp.so.1`, sem
alteracao global do sistema.

**Acceptance criteria:**
- [x] O bootstrap identifica a ausencia da runtime, baixa somente o artefato
  fixado para o cache do usuario e valida sua integridade.
- [x] O bootstrap nao usa `sudo`, `apt`, instalacao global ou modificacao de
  bibliotecas do sistema.
- [x] A documentacao inclui origem, licenca GPLv3 com GCC Runtime Library
  Exception, avisos de redistribuicao e o limite de plataforma WSL/Linux.

**Verification:**
- [x] Executar testes unitarios do registro, download, checksum e erro de
  runtime ausente com stubs, sem acesso externo.
- [x] Em WSL/Linux, executar o bootstrap e confirmar que o Prism inicia sem
  dependencia de `libgomp1` instalada globalmente.
- [x] Repetir `.venv/bin/pytest -m opencode` com cache provisionado e sem novo
  download.

**Dependencies:** None.

**Files likely touched:**
- `src/opencode_config/bootstrap/`
- `tests/bootstrap/`
- `README.md`

**Estimated scope:** M (3-5 files).

**Local commit checkpoint:** `feat(bootstrap): provisiona runtime openmp local`
apos testes unitarios e validacao WSL/Linux.

## Task 0.1: Integrar runtime OpenMP ao servidor local

**Description:** Fazer o harness localizar e validar a runtime provisionada
antes de iniciar Prism. A inicializacao deve usar a copia cacheada sem
`LD_LIBRARY_PATH`; se estiver ausente, invalida ou incompativel, a falha deve
informar a dependencia e o comando de bootstrap a executar.

**Acceptance criteria:**
- [x] O servidor nao inicia Prism sem runtime OpenMP valida.
- [x] A mensagem de erro informa o caminho esperado e como provisionar.
- [x] A inicializacao usa a runtime cacheada sem mutar bibliotecas do sistema,
  variaveis globais ou timeouts.

**Verification:**
- [x] Executar testes unitarios do caminho com runtime valida, ausente e
  checksum invalido.
- [x] Em WSL/Linux, confirmar que Prism inicia usando apenas o cache
  provisionado.

**Dependencies:** Task 0.

**Files likely touched:**
- `tests/integration/model/local_model_server.py`
- `tests/integration/model/test_local_model_server.py`
- `tests/integration/conftest.py`

**Estimated scope:** S (3 files).

**Local commit checkpoint:** `fix(integracao): carrega runtime openmp local`
apos os testes unitarios e o smoke WSL/Linux.

### Checkpoint: Runtime nativa

- [x] A runtime e obtida somente pelo bootstrap WSL/Linux e funciona do cache.
- [x] A ausencia dela falha com instrucao clara, sem tentar inferencia.
- [x] A conformidade de licenca e redistribuicao foi revisada antes de baixar
  qualquer artefato.

### Phase 1: Contrato padrao e provisionamento

## Task 1: Inverter o modelo padrao em todas as entradas OpenCode

**Description:** Converter o contrato canonico em Qwen-only e alinhar o
servidor, contexto gerado e JSON-base de integracao. Remover o seletor
`--local-model`, a spec Bonsai e todas as ramificacoes de modelo; renomear os
modulos versionados que ainda citam Bonsai com `git mv`.

**Acceptance criteria:**
- [x] `pytest -m opencode` usa `qwen-local/qwen3-0.6b` sem argumento extra.
- [x] O JSON estatico e os contextos gerados fixam um unico provider local e os
  agentes `plan` e `build` usam Qwen.
- [x] Nao resta no harness contrato, provider, seletor ou artefato Bonsai.

**Verification:**
- [x] Executar os testes unitarios do seletor, contexto e provider local.
- [x] Inspecionar a configuracao gerada e confirmar que declara somente Qwen.

**Dependencies:** Task 0.1.

**Files likely touched:**
- `tests/conftest.py`
- `tests/integration/model/bonsai_server.py` -> `local_model_server.py`
- `tests/integration/integration_context.py`
- `tests/integration/config/opencode.test.json`

**Estimated scope:** M (4 files).

**Local commit checkpoint:** `feat(integracao): define qwen como modelo padrao`
apos os testes unitarios desta unidade logica.

## Task 2: Cobrir o contrato Qwen padrao e o fallback Bonsai

**Description:** Atualizar testes unitarios e nomenclaturas de assercoes para
o contrato Qwen-only. O servidor continua recusando reutilizar com seguranca
um endpoint divergente e mantem checksum Qwen, cache e argumentos existentes
do llama-server.

**Acceptance criteria:**
- [x] Os testes verificam o artefato, provider e identidade padrao Qwen.
- [x] Os testes rejeitam a antiga selecao `--local-model` e nao referenciam
  Bonsai.
- [x] Nenhum teste ou producao adiciona ou modifica timeout existente.

**Verification:**
- [x] Executar testes unitarios em `tests/conftest.py`,
  `tests/integration/model/`, `tests/integration/test_integration_context.py`
  e `tests/integration/docker/test_local_provider.py`.

**Dependencies:** Tasks 0.1-1.

**Files likely touched:**
- `tests/integration/model/test_bonsai_server.py` -> `test_local_model_server.py`
- `tests/integration/test_integration_context.py`
- `tests/integration/docker/test_local_provider.py`
- `tests/integration/test_prompts.py`
- `tests/integration/test_behavioral_helper.py`

**Estimated scope:** M (5 files).

**Local commit checkpoint:** `test(integracao): cobre contrato exclusivo qwen`
apos a suite unitaria alvo.

### Checkpoint: Contrato e provisionamento

- [x] No WSL/Linux, os testes unitarios alvo passam com `.venv/bin/pytest`.
- [x] O padrao e a integridade do Qwen estao cobertos sem
  provisionamento pelo bootstrap.

### Phase 2: Privacidade e documentacao operacional

## Task 3: Manter enforcement de privacidade independente do modelo

**Description:** Tornar as mensagens e os testes de privacidade neutros quanto
ao modelo, mantendo a assercao do unico provider Qwen, endpoint localhost,
rede interna e bloqueio de egress.

**Acceptance criteria:**
- [x] A suite padrao executa os quatro controles de privacidade contra Qwen.
- [x] A configuracao efetiva nao contem provider remoto, telemetria, proxy
  externo ou handoff em cloud.

**Verification:**
- [x] Executar `.venv/bin/pytest -m opencode` no WSL/Linux com Docker.

**Dependencies:** Tasks 0.1-2.

**Files likely touched:**
- `tests/integration/test_privacy_enforcement.py`
- `tests/integration/conftest.py`
- `tests/integration/test_prompts.py`

**Estimated scope:** S (3 files).

**Local commit checkpoint:** `test(privacidade): valida qwen local padrao`
apos a execucao OpenCode.

## Task 4: Documentar operacao, decisao e rollback

**Description:** Atualizar o README para apresentar o contrato Qwen-only e o
provisionamento sob demanda. Registrar em novo ADR a substituicao de decisao e
atualizar o experimento com o resultado final, mantendo Needle 2 explicitamente
fora de escopo.

**Acceptance criteria:**
- [x] A documentacao mostra somente o comando padrao Qwen.
- [x] Documenta cache local, checksum Qwen, execucao offline apos
  provisionamento, ausencia de telemetria e prerequisito Docker no WSL/Linux.
- [x] O ADR contem motivacao, escopo, decisoes substituidas, consequencias e
  rollback por reversao Git; nao altera o ADR-0002 historico.

**Verification:**
- [x] Conferir que todos os comandos documentados usam
  `.venv/bin/pytest -m opencode` no WSL/Linux.
- [x] Conferir que nao ha instrucao de cloud, telemetria, Needle 2 ou alteracao
  de timeout.

**Dependencies:** Tasks 0.1-3.

**Files likely touched:**
- `README.md`
- `docs/experimentos/modelos-locais.md`
- `docs/adr/0003-qwen3-padrao-integracao-opencode.md`

**Estimated scope:** S (3 files).

**Local commit checkpoint:** `docs(integracao): documenta qwen padrao`
apos revisao cruzada entre documentacao e codigo.

### Checkpoint: Complete

- [x] No WSL/Linux com Docker, `.venv/bin/pytest -m opencode` passa com Qwen
  padrao.
- [x] O bootstrap WSL/Linux provisiona a runtime OpenMP cacheada necessaria
  sem instalacao manual em uma maquina compativel.
- [x] Os quatro testes de privacidade passam com Qwen.
- [x] O cache permite repetir as execucoes sem download; nao ha egress em
  runtime, telemetria ou handoff em cloud.
- [x] Nao ha alteracao de timeout nem escopo relacionado a Needle 2.
- [x] A implementacao esta pronta para revisao independente.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Referencia Bonsai permanecer ativa | Medio | Buscar seletor, specs, docs e modulos antigos apos a remocao. |
| Regressao de isolamento ao inverter provider | Alto | Executar enforcement de config, endpoint e rede para Qwen. |
| Cache ausente exigir rede | Medio | Separar provisionamento explicito da execucao e documentar a repeticao offline. |
| Runtime OpenMP nao carregar do cache | Alto | Validar integridade e carregamento antes de iniciar Prism; falhar com instrucao de bootstrap. |
| Redistribuicao inadequada da libgomp | Alto | Fixar origem e versao, registrar GPLv3 + Runtime Exception e incluir avisos exigidos. |
| Endpoint antigo Qwen/Bonsai ocupar a porta | Medio | Preservar a reconciliacao segura por identidade existente; nao matar processo externo. |
| Rollback urgente | Baixo | Reverter o commit da migracao; Bonsai nao permanece como caminho operacional. |
| Alterar acidentalmente a politica de timeout | Medio | Tratar constantes e argumentos atuais como invariantes e revisar o diff. |

## Open Questions

- Nenhuma para a implementacao.

## Execution Roles

- **Executor:** `gpt-5.6-luna`.
- **Revisor independente:** `gpt-5.6-terra`.

## Execution Harness

- **Gate obrigatório:** no WSL/Linux com Docker, executar
  `.venv/bin/pytest -m opencode`.
- **Evidência requerida:** resultado da suíte, incluindo os quatro controles de
  privacidade, com runtime provisionada pelo bootstrap e sem alteracao de
  timeout.
