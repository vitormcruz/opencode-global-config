# Implementation Plan: Orquestração Simples do Smart-Planner

Status: FINALIZAÇÃO — revisão aprovada; commit local autorizado

## Overview

Evoluir o `smart-planner` de gerador de prompts de handoff para um orquestrador leve que
planeja, obtém aprovação humana, seleciona executor e revisor independentes e encerra
somente após uma revisão aprovada. O arquivo de planejamento continua como fonte de verdade
entre as instâncias.

## Architecture Decisions

### D1 — Workflow simples e canônico

Criar `docs/workflow-agentico-simples.md` como especificação independente e genérica do ciclo
planejar → executar → revisar. Ele não substitui nem replica o workflow especializado de
desenvolvimento; referências nos workflows existentes só serão adicionadas se necessárias para
evitar divergência.

### D2 — Seleção por capacidade da plataforma

O `smart-planner` detecta o mecanismo nativo de subagentes antes de executar. Quando
disponíveis, usa o agente comum de construção do OpenCode (por exemplo, `build`) e o mecanismo
padrão equivalente do Copilot CLI. A implementação não presume que os nomes ou argumentos sejam
universais.

### D3 — Modelos por papel, com fallback humano

Após a aprovação do plano, o humano escolhe um modelo para executor e outro para revisor. As
escolhas são registradas no plano e reutilizadas em retries. Sem suporte para iniciar a sessão
com o modelo escolhido, o `smart-planner` solicita a troca manual e aguarda confirmação antes do
spawn.

### D4 — Mediação e replanejamento centralizados

Bloqueios, ambiguidades, riscos e requisitos novos retornam ao `smart-planner`, que consulta o
humano, atualiza o plano e inicia uma nova instância a partir do estado correto. O executor não
inventa decisões fora do plano.

### D5 — Revisão independente como gate de término

Executor e revisor sempre usam instâncias separadas. O revisor relata achados; o executor aplica
os ajustes e uma nova instância revisa novamente. A tarefa só termina com aprovação explícita do
revisor, sem bloqueios nem decisões humanas pendentes.

### D6 — Sugestão de commit após revisão aprovada

Após a aprovação técnica do revisor, o `smart-planner` apresenta resumo, arquivos e uma mensagem
Conventional Commit sugerida. Ele aguarda confirmação explícita antes de criar o commit local,
inclui somente a unidade lógica aprovada e nunca executa `git push`. A recusa do commit não
desfaz a conclusão técnica da tarefa.

## Execution Configuration

- Modelo do executor: GPT-5.6 Terra.
- Modelo do revisor: GPT-5.6 Terra.
- Autorização de execução: confirmada pelo humano.
- Seleção nativa de agente e de modelo: confirmar durante a implementação.

## Execution Results

- Executor: concluído sem bloqueios.
- Arquivos alterados: `agents/smart-planner.md`, `docs/workflow-agentico-simples.md`,
  `tests/agents/test_smart_planner.py` e `tests/adapters/test_copilot_adapter.py`.
- Evidências relatadas: 39 contratos do smart-planner, contrato manual do adapter Copilot,
  `py_compile` e `git diff --check` passaram.
- Na primeira execução, o pytest direcionado esteve indisponível porque `.venv` era Linux,
  `pytest` não estava no PATH e a instalação no Artifactory expirou.
- Replanejamento: incluir a sugestão e a confirmação explícita de commit após revisão aprovada.
- Finalização implementada em `agents/smart-planner.md`,
  `docs/workflow-agentico-simples.md` e `tests/agents/test_smart_planner.py`.
- Evidências da finalização: pytest direcionado, `py_compile`, `git diff --check` e o limite de
  120 colunas passaram.

## Review Results

- Revisor: GPT-5.6 Terra, em instância independente.
- Resultado: APPROVED, sem achados de alta confiança.
- Avaliação da lacuna de pytest: evidência local pendente, mas não bloqueante para a correção,
  pois os contratos e a conversão do adapter foram verificados.
- Nova revisão independente será necessária após concluir a Task 4.
- Revisor da finalização: APPROVED, sem problemas significativos.
- Revalidação local do revisor: `py_compile`, `git diff --check` e limite de 120 colunas passaram;
  pytest não estava disponível nessa instância.

## Task List

### Phase 1: Contrato testável

## Task 1: Definir o contrato de orquestração

**Description:** Criar ou atualizar testes que descrevam o novo ciclo de execução, seleção de
modelos, replanejamento e aprovação do revisor.

**Acceptance criteria:**
- [ ] Os testes deixam de exigir que handoffs sejam o encerramento do fluxo.
- [ ] Os testes cobrem executor e revisor independentes, seleção de modelos e fallback manual.
- [ ] O contrato de término exige aprovação explícita do revisor.

**Verification:**
- [ ] Testes direcionados executam com sucesso após a implementação.

**Dependencies:** None.

**Files likely touched:**
- `tests/agents/test_smart_planner.py`
- `tests/adapters/test_copilot_adapter.py`

**Estimated scope:** Small: 1-2 files.

### Phase 2: Especificação e agente

## Task 2: Especificar o workflow agêntico simples

**Description:** Criar a especificação genérica do ciclo de orquestração, sem reproduzir fases,
especialidades ou agentes do workflow de desenvolvimento.

**Acceptance criteria:**
- [ ] O documento descreve papéis, estados, transições, seleção de plataforma e de modelos.
- [ ] O documento define bloqueio, replanejamento, correção e aprovação como transições claras.
- [ ] O documento preserva o plano como fonte de verdade.

**Verification:**
- [ ] A especificação atende aos testes de contrato adicionados.
- [ ] Não há duplicação desnecessária de `docs/workflow-agentes-dev.md`.

**Dependencies:** Task 1.

**Files likely touched:**
- `docs/workflow-agentico-simples.md`
- `docs/workflow-agentes-dev.md` (somente se uma referência for necessária)
- `docs/workflow-curadoria.md` (somente se uma referência for necessária)

**Estimated scope:** Small: 1-3 files.

## Task 3: Implementar a orquestração no smart-planner

**Description:** Substituir o encerramento por handoff pelo ciclo aprovado de spawn, mediação,
replanejamento e revisão, habilitando apenas a permissão mínima de subagente necessária.

**Acceptance criteria:**
- [ ] O agente pergunta se pode iniciar a execução somente após a aprovação do plano.
- [ ] O agente coleta e registra modelos separados para executor e revisor.
- [ ] O agente aguarda a troca manual de modelo quando não puder definir o modelo no spawn.
- [ ] O agente retoma executor ou revisor em instância nova após cada retorno ao planejamento.

**Verification:**
- [ ] Os testes de contrato do `smart-planner` passam.
- [ ] O adapter Copilot materializa a capacidade de subagente necessária.

**Dependencies:** Tasks 1 and 2.

**Files likely touched:**
- `agents/smart-planner.md`
- `tests/agents/test_smart_planner.py`
- `tests/adapters/test_copilot_adapter.py`

**Estimated scope:** Small: 1-3 files.

### Checkpoint: Orquestração

- [ ] O agente, o workflow e os testes descrevem o mesmo ciclo.
- [ ] Nenhum caminho encerra antes da aprovação do revisor.
- [ ] Seleção de plataforma e de modelo tem fallback explícito.

### Phase 3: Finalização

## Task 4: Formalizar a finalização por commit

**Description:** Fazer o agente e o workflow sugerirem um commit local depois da aprovação
técnica, sem criar esse commit antes da confirmação humana.

**Acceptance criteria:**
- [ ] O agente sugere resumo, arquivos e mensagem Conventional Commit após aprovação do revisor.
- [ ] O commit local exige confirmação explícita do humano e permanece limitado à unidade lógica.
- [ ] O workflow genérico descreve a mesma regra, inclusive a proibição de `git push` automático.

**Verification:**
- [ ] Testes de contrato confirmam a sugestão e o gate de confirmação.

**Dependencies:** Tasks 2 and 3.

**Files likely touched:**
- `agents/smart-planner.md`
- `docs/workflow-agentico-simples.md`
- `tests/agents/test_smart_planner.py`

**Estimated scope:** Small: 1-3 files.

### Phase 4: Validação

## Task 5: Validar contratos e adapters

**Description:** Executar os testes unitários direcionados e corrigir somente inconsistências
causadas pela nova orquestração.

**Acceptance criteria:**
- [ ] Os testes direcionados de agente e adapter passam no Windows.
- [ ] A mudança não altera comportamentos não relacionados de `devflow`.

**Verification:**
- [ ] `.\.venv\Scripts\pytest.exe tests\agents\test_smart_planner.py
      tests\adapters\test_copilot_adapter.py -m "unit or tools or copilot"` passa.

**Dependencies:** Tasks 1, 2, 3 and 4.

**Files likely touched:**
- `tests/agents/test_smart_planner.py`
- `tests/adapters/test_copilot_adapter.py`

**Estimated scope:** Small: 1-2 files.

### Checkpoint: Complete

- [ ] Todos os critérios de aceitação foram atendidos.
- [ ] O revisor independente aprovou a implementação.
- [ ] O plano e a especificação estão consistentes.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| APIs de subagente divergem entre plataformas | High | Detectar capacidade e usar fallback explícito por plataforma. |
| Modelo escolhido não pode ser definido no spawn | Medium | Solicitar troca manual e aguardar confirmação humana. |
| Revisor compartilhar contexto com executor | High | Exigir instância nova e briefing independente para toda revisão. |
| Workflow genérico duplicar o de desenvolvimento | Medium | Limitar o novo documento ao ciclo universal e usar referências mínimas. |

## Open Questions

- Criar o commit local autorizado para a unidade lógica de implementação.
