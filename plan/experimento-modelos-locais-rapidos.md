# Implementation Plan: Experimento de modelos locais rápidos

## Overview

Avaliar Qwen3-0.6B como possível substituto do Bonsai nos testes
comportamentais do OpenCode, preservando execução local, gratuita e sem
telemetria. Needle 2 foi avaliado e rejeitado antes da implementação.

## Architecture Decisions

- **D1 — Triagem inicial:** Needle 2 e Qwen3-0.6B foram avaliados contra os
  requisitos de execução local, gratuita, sem telemetria, endpoint OpenAI e
  tool calling; D6 reduziu o experimento ao Qwen.
- **D2 — Gate de substituição:** substituir o Bonsai somente se um candidato
  aprovar 100% da suíte `-m opencode`, não usar rede nem telemetria durante os
  testes e reduzir a duração total de forma mensurável.
- **D3 — Ganho mínimo:** exigir redução de ao menos 30% na duração total,
  comparada a uma execução-base recente do Bonsai no mesmo ambiente.
- **D4 — Fallback:** manter o Bonsai durante o experimento e mudar o padrão
  somente após a aprovação integral de um candidato nos gates definidos.
- **D5 — Escopo:** executar os comparativos e documentar a decisão; não
  substituir automaticamente o Bonsai neste plano.
- **D6 — Needle 2 rejeitado:** apesar da licença Apache-2.0 e da execução
  offline após provisionamento, sua API oficial é Python, não HTTP
  OpenAI-compatible, e seu contrato não oferece resposta textual livre. Não
  criar ponte local nem incluí-lo na comparação do OpenCode.
- **D7 — Modelos de execução:** o executor usará `gpt-5.6-luna`; a revisão
  independente usará `claude-sonnet-5`.

## Task List

### Phase 1: Pré-condições bloqueantes

## Task 1: Validar licença, offline e integridade do Qwen

**Description:** Antes de alterar o harness, fixar a origem, versão e artefato
GGUF do Qwen3-0.6B, conferindo a licença Apache-2.0 do modelo e do runtime
usado. Definir o provisionamento local e comprovar que, depois dele, o servidor
não exige rede, telemetria, chave de API ou cloud handoff.

**Acceptance criteria:**
- [ ] A documentação registra origem, versão, licença e identificador do GGUF.
- [ ] O Qwen e o runtime têm licença permissiva aceita e distribuição gratuita.
- [ ] O provisionamento e a inferência posterior não permitem egress.

**Verification:**
- [ ] Revisão manual confirma as licenças nas fontes oficiais fixadas.
- [ ] Teste de privacidade prova rede Docker interna e ausência de cloud handoff.

**Dependencies:** None

**Files likely touched:**
- `docs/experimentos/modelos-locais.md`
- `tests/integration/test_privacy_enforcement.py`
- `README.md`

**Estimated scope:** Small: 3 files

**Local commit checkpoint:** Registro de pré-condições e testes de privacidade.

## Task 2: Extrair o contrato de servidor local para experimento

**Description:** Isolar no harness de integração o contrato mínimo de um
servidor de modelo local: ciclo de vida, `/v1/models`, chat completions, tool
calling, configuração temporária do OpenCode e coleta de duração. O Bonsai
permanece o caminho padrão e a execução experimental não pode alterar sua
configuração permanente.

**Acceptance criteria:**
- [ ] Cada execução seleciona explicitamente Bonsai ou Qwen3-0.6B.
- [ ] O teste confirma disponibilidade, tool calling e ausência de acesso externo.
- [ ] O resultado contém candidato, versão fixada, duração total e status.

**Verification:**
- [ ] Testes unitários do controlador e da configuração temporária passam.
- [ ] O teste de privacidade confirma rede Docker interna e endpoint local.

**Dependencies:** Task 1

**Files likely touched:**
- `tests/integration/model/bonsai_server.py`
- `tests/integration/conftest.py`
- `tests/integration/docker/test_local_provider.py`
- `tests/integration/model/test_bonsai_server.py`

**Estimated scope:** Medium: 4 files

**Local commit checkpoint:** Arquivos da abstração e seus testes unitários.

### Checkpoint: Pré-condições

- [ ] Licença e modo offline foram aprovados antes de provisionar o Qwen.
- [ ] Bonsai permanece disponível como fallback.

### Phase 2: Compatibilização do Qwen

## Task 3: Integrar Qwen3-0.6B ao servidor compatível

**Description:** Provisionar uma variante GGUF fixada de Qwen3-0.6B no
`llama-server` já usado pelo harness. Configurar o template de chat, o modo sem
thinking e tool calling necessários para produzir respostas compatíveis com o
provider `@ai-sdk/openai-compatible`.

**Acceptance criteria:**
- [ ] O servidor Qwen responde localmente a `/v1/models` e chat completions.
- [ ] A chamada de ferramenta retornada é aceita pelo OpenCode.
- [ ] Nenhum download ou chamada externa ocorre depois do provisionamento.

**Verification:**
- [ ] Testes unitários validam artefato fixado, comando do servidor e modelo
  exposto.
- [ ] Smoke test no container chama o endpoint Qwen pelo gateway interno.

**Dependencies:** Task 2

**Files likely touched:**
- `tests/integration/model/bonsai_server.py`
- `tests/integration/model/test_bonsai_server.py`
- `tests/integration/config/opencode.test.json`
- `tests/integration/docker/test_local_provider.py`

**Estimated scope:** Medium: 4 files

**Local commit checkpoint:** Provisionamento Qwen e testes de compatibilidade.

### Checkpoint: Compatibilização do Qwen

- [ ] Bonsai permanece disponível como fallback.
- [ ] Qwen é selecionável sem modificar a configuração padrão.
- [ ] Os endpoints e tool calls passam nos testes unitários e de smoke.

### Phase 3: Comparação comportamental

## Task 4: Executar a suíte comportamental por modelo

**Description:** Executar a baseline recente do Bonsai e, isoladamente, a suíte
`pytest -m opencode` para Qwen. Registrar falhas com o teste, a saída
relevante e o candidato responsável; não mascarar falhas nem repetir por um
período arbitrário.

**Acceptance criteria:**
- [ ] Há uma baseline Bonsai executada no mesmo ambiente antes da comparação.
- [ ] O Qwen executa a suíte completa em configuração e processo
  isolados.
- [ ] A evidência inclui duração total, contagem de testes e falhas.

**Verification:**
- [ ] `pytest -m opencode` é executado para Bonsai e Qwen.
- [ ] Os testes de privacidade continuam aprovados em cada execução.

**Dependencies:** Task 3

**Files likely touched:**
- `tests/integration/conftest.py`
- `tests/integration/test_privacy_enforcement.py`
- `docs/experimentos/modelos-locais.md`

**Estimated scope:** Small: 3 files

**Local commit checkpoint:** Harness comparativo, se houver alteração necessária.

### Checkpoint: Comparação comportamental

- [ ] Todos os resultados têm baseline comparável.
- [ ] Licença, isolamento e egress foram aprovados na pré-condição.
- [ ] Falhas são registradas sem alterar o fallback Bonsai.

### Phase 4: Decisão documentada

## Task 5: Publicar a decisão do experimento

**Description:** Consolidar as medições e aplicar D2 e D3: um candidato só é
recomendado se aprovar 100% da suíte, não fizer egress/telemetria e reduzir ao
menos 30% da duração. Caso nenhum passe, documentar a rejeição e manter Bonsai.

**Acceptance criteria:**
- [ ] A tabela final compara Bonsai e Qwen por duração e aprovação.
- [ ] A decisão cita explicitamente cada gate e sua evidência.
- [ ] O provider padrão continua Bonsai, independentemente do resultado.

**Verification:**
- [ ] Revisão do relatório reproduz os cálculos do ganho percentual.
- [ ] Diff da configuração padrão confirma que não houve substituição automática.

**Dependencies:** Task 4

**Files likely touched:**
- `docs/experimentos/modelos-locais.md`
- `plan/experimento-modelos-locais-rapidos.md`

**Estimated scope:** Small: 2 files

**Local commit checkpoint:** Relatório e decisão documentada.

### Checkpoint: Complete

- [ ] Todos os gates de D2 e D3 foram avaliados.
- [ ] O Bonsai foi preservado como fallback e padrão.
- [ ] A decisão está documentada e pronta para revisão humana.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Modelo pequeno falha em instruções do OpenCode | High | Exigir 100% da suíte comportamental, sem flexibilizar assertions. |
| Ganho afetado por cache ou hardware | Medium | Medir a baseline e candidatos no mesmo ambiente, registrando versões. |
| Dependência com licença não permissiva | High | Validar licença de pesos e runtime antes de aprovar o candidato. |
| Egress ou cloud handoff acidental | High | Manter rede Docker interna e testes explícitos de privacidade. |

## Open Questions

- Nenhuma. A troca definitiva do provider padrão fica fora deste experimento.
