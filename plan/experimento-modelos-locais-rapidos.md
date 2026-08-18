# Implementation Plan: Experimento de modelos locais rápidos

## Overview

Avaliar Needle 2 e Qwen3-0.6B como possíveis substitutos do Bonsai nos testes
comportamentais do OpenCode, preservando execução local, gratuita e sem
telemetria.

## Architecture Decisions

- **D1 — Candidatos:** comparar Needle 2 e Qwen3-0.6B contra o Bonsai. Ambos
  precisam operar localmente, gratuitamente e sem telemetria; a aprovação
  depende de compatibilidade com o endpoint OpenAI e com tool calling.
- **D2 — Gate de substituição:** substituir o Bonsai somente se um candidato
  aprovar 100% da suíte `-m opencode`, não usar rede nem telemetria durante os
  testes e reduzir a duração total de forma mensurável.
- **D3 — Ganho mínimo:** exigir redução de ao menos 30% na duração total,
  comparada a uma execução-base recente do Bonsai no mesmo ambiente.
- **D4 — Fallback:** manter o Bonsai durante o experimento e mudar o padrão
  somente após a aprovação integral de um candidato nos gates definidos.
- **D5 — Escopo:** executar os comparativos e documentar a decisão; não
  substituir automaticamente o Bonsai neste plano.

## Task List

### Phase 1: Contrato e candidatos

## Task 1: Extrair o contrato de servidor local para experimento

**Description:** Isolar no harness de integração o contrato mínimo de um
servidor de modelo local: ciclo de vida, `/v1/models`, chat completions, tool
calling, configuração temporária do OpenCode e coleta de duração. O Bonsai
permanece o caminho padrão e a execução experimental não pode alterar sua
configuração permanente.

**Acceptance criteria:**
- [ ] Cada execução seleciona explicitamente Bonsai, Qwen3-0.6B ou Needle 2.
- [ ] O teste confirma disponibilidade, tool calling e ausência de acesso externo.
- [ ] O resultado contém candidato, versão fixada, duração total e status.

**Verification:**
- [ ] Testes unitários do controlador e da configuração temporária passam.
- [ ] O teste de privacidade confirma rede Docker interna e endpoint local.

**Dependencies:** None

**Files likely touched:**
- `tests/integration/model/bonsai_server.py`
- `tests/integration/conftest.py`
- `tests/integration/docker/test_local_provider.py`
- `tests/integration/model/test_bonsai_server.py`

**Estimated scope:** Medium: 4 files

**Local commit checkpoint:** Arquivos da abstração e seus testes unitários.

## Task 2: Integrar Qwen3-0.6B ao servidor compatível

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

**Dependencies:** Task 1

**Files likely touched:**
- `tests/integration/model/bonsai_server.py`
- `tests/integration/model/test_bonsai_server.py`
- `tests/integration/config/opencode.test.json`
- `tests/integration/docker/test_local_provider.py`

**Estimated scope:** Medium: 4 files

**Local commit checkpoint:** Provisionamento Qwen e testes de compatibilidade.

## Task 3: Criar ponte OpenAI compatível para Needle 2

**Description:** Avaliar e, se necessário, implementar uma ponte local mínima
entre as requisições OpenAI-compatible do OpenCode e a API Python do Needle 2.
A ponte deve converter as definições JSON de ferramentas e devolver tool calls
na forma esperada pelo OpenCode; ela não pode habilitar cloud handoff,
telemetria ou fallback remoto.

**Acceptance criteria:**
- [ ] O processo Needle responde a `/v1/models` e à operação de chat usada pelo
  OpenCode.
- [ ] Ferramentas e argumentos são preservados na conversão de ida e volta.
- [ ] A ponte falha explicitamente se a compatibilidade não for possível.

**Verification:**
- [ ] Testes unitários cobrem conversão de mensagens, schemas e tool calls.
- [ ] Smoke test prova uma chamada de ferramenta pelo endpoint local.

**Dependencies:** Task 1

**Files likely touched:**
- `tests/integration/model/needle_server.py`
- `tests/integration/model/test_needle_server.py`
- `tests/integration/conftest.py`
- `tests/integration/docker/test_local_provider.py`

**Estimated scope:** Medium: 4 files

**Local commit checkpoint:** Ponte Needle e testes de contrato.

### Checkpoint: Contrato e candidatos

- [ ] Bonsai permanece disponível como fallback.
- [ ] Qwen e Needle são selecionáveis sem modificar a configuração padrão.
- [ ] Os endpoints e tool calls passam nos testes unitários e de smoke.

### Phase 2: Comparação comportamental

## Task 4: Executar a suíte comportamental por candidato

**Description:** Executar a baseline recente do Bonsai e, isoladamente, a suíte
`pytest -m opencode` para Qwen e Needle. Registrar falhas com o teste, a saída
relevante e o candidato responsável; não mascarar falhas nem repetir por um
período arbitrário.

**Acceptance criteria:**
- [ ] Há uma baseline Bonsai executada no mesmo ambiente antes da comparação.
- [ ] Cada candidato executa a suíte completa em configuração e processo
  isolados.
- [ ] A evidência inclui duração total, contagem de testes e falhas.

**Verification:**
- [ ] `pytest -m opencode` é executado para Bonsai, Qwen e Needle.
- [ ] Os testes de privacidade continuam aprovados em cada execução.

**Dependencies:** Tasks 2 and 3

**Files likely touched:**
- `tests/integration/conftest.py`
- `tests/integration/test_privacy_enforcement.py`
- `docs/experimentos/modelos-locais.md`

**Estimated scope:** Small: 3 files

**Local commit checkpoint:** Harness comparativo, se houver alteração necessária.

## Task 5: Validar licenças, offline e integridade do resultado

**Description:** Confirmar nos artefatos usados que Qwen3-0.6B e Needle 2, seus
pesos e runtimes empregados são gratuitos e Apache-2.0 (ou outra licença
permissiva explicitamente aceita), com versões e hashes/identificadores
registrados. Verificar que as execuções após provisionamento não fazem egress.

**Acceptance criteria:**
- [ ] A documentação lista origem, versão e licença de cada artefato.
- [ ] Não há cloud handoff, chave de API ou telemetria ativa.
- [ ] Qualquer licença ou egress não conforme reprova o candidato.

**Verification:**
- [ ] Teste de privacidade de rede passa para cada candidato.
- [ ] Revisão manual confere as licenças nas fontes oficiais fixadas.

**Dependencies:** Tasks 2 and 3

**Files likely touched:**
- `docs/experimentos/modelos-locais.md`
- `tests/integration/test_privacy_enforcement.py`
- `README.md`

**Estimated scope:** Small: 3 files

### Checkpoint: Comparação comportamental

- [ ] Todos os resultados têm baseline comparável.
- [ ] Licença, isolamento e egress foram verificados.
- [ ] Falhas são registradas sem alterar o fallback Bonsai.

### Phase 3: Decisão documentada

## Task 6: Publicar a decisão do experimento

**Description:** Consolidar as medições e aplicar D2 e D3: um candidato só é
recomendado se aprovar 100% da suíte, não fizer egress/telemetria e reduzir ao
menos 30% da duração. Caso nenhum passe, documentar a rejeição e manter Bonsai.

**Acceptance criteria:**
- [ ] A tabela final compara Bonsai, Qwen e Needle por duração e aprovação.
- [ ] A decisão cita explicitamente cada gate e sua evidência.
- [ ] O provider padrão continua Bonsai, independentemente do resultado.

**Verification:**
- [ ] Revisão do relatório reproduz os cálculos do ganho percentual.
- [ ] Diff da configuração padrão confirma que não houve substituição automática.

**Dependencies:** Tasks 4 and 5

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
| Needle não expõe HTTP OpenAI-compatible | High | Implementar e testar ponte local; rejeitar se tool calls não forem fiéis. |
| Modelo pequeno falha em instruções do OpenCode | High | Exigir 100% da suíte comportamental, sem flexibilizar assertions. |
| Ganho afetado por cache ou hardware | Medium | Medir a baseline e candidatos no mesmo ambiente, registrando versões. |
| Dependência com licença não permissiva | High | Validar licença de pesos e runtime antes de aprovar o candidato. |
| Egress ou cloud handoff acidental | High | Manter rede Docker interna e testes explícitos de privacidade. |

## Open Questions

- Nenhuma. A troca definitiva do provider padrão fica fora deste experimento.
