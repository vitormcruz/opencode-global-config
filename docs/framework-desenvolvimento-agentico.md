# Framework de Desenvolvimento Agêntico

## Objetivo

Criar uma organização em torno de especificações de negócio, testes e regras de validação que sirvam de memória do
produto, contexto e harness para que agentes consigam evoluir no desenvolvimento do produto de maneira controlada, com
insumo para que os humanos possam entender o sistema e orientar os agentes.

![Fluxo de Produto](./svgImage/FwcAgenticoBase.svg)
📍 **Navegar pelo diagrama:** [Governança de Produto](#governanca) · [Ideação](#ideacao)  · [Desenvolvimento](#desenvolvimento)

## Governança de Produto

A Governança de Produto é a dimensão responsável por estabelecer, organizar e manter a memória viva do sistema. Seu papel é definir a estrutura das especificações de negócio, os contratos técnicos, as suítes de validação e as instruções operacionais que servem de contexto e *harness* para todo o ciclo de vida do software.

O **`curador-produto`** é o único agente responsável por conduzir entrevistas estruturadas com o humano para criar ou modificar as Diretrizes e Regras de Produto, mas ele pode ser intermediado por outros agentes. Ele também revisa e valida se as diretrizes foram seguidas em um fluxo de desenvolvimento.

As Diretrizes e Regras de Produto orientam o trabalho dos agentes e documentam as decisões de especificação para o humano.

### Diretrizes e Regras de Produto

As Diretrizes e Regras de Produto reúnem os documentos que orientam a organização, a especificação e a validação do produto.

![Estrutura das Diretrizes e Regras de Produto](./svgImage/DiretrizesRegrasProduto.svg)

O `AGENTS.md` mantém a seção central de diretrizes. Ela aponta para a **Especificação do Produto**, referencia o arquivo de **Testes por Especialidade** e contém, inline, as **Instruções por Agente**.

O `curador-produto` é responsável por criar, atualizar e validar esse conjunto. Os demais agentes consultam a seção de diretrizes do `AGENTS.md` e seguem as referências encontradas nela, sem depender de caminhos fixos em seus próprios prompts.

As Diretrizes e Regras de Produto são formadas pelos documentos abaixo.
Cada repositório mantém os links para as versões vigentes de suas
especificações. Os templates usados pelo `curador-produto` estão
referenciados aqui:

- **Especificação do Produto:** descreve o escopo, os elementos de
  especificação, as regras de documentação e os links para os documentos
  que detalham cada parte do produto. Ele registra como o projeto guarda
  requisitos, critérios de aceitação, casos de uso, histórias e diagramas,
  preferencialmente como **Especificações Executáveis**.
  [Consultar template](../harness-conf/agents/default-artifacts/doc-readme-template.md)

- **Testes por Especialidade:** define as suítes de validação do produto,
  os testes de cada especialidade, os critérios de execução, os limites e
  o formato dos resultados. Define os testes necessários para considerar
  uma alteração concluída.
  [Consultar template](../harness-conf/agents/default-artifacts/testes-por-especialidade-template.md)

- **Instruções por Agente:** registra as orientações específicas que cada
  agente deve seguir em um repositório. Fica dentro do `AGENTS.md`, junto
  da seção de Diretrizes e Regras de Produto, para servir de reforço aos agentes.
  [Consultar template](../harness-conf/agents/default-artifacts/instrucoes-por-agente-template.md)

## Ideação



## Desenvolvimento

![Ciclo de Desenvolvimento](./svgImage/FluxoDesenvolvimento.svg)

- [Contratos do Workflow](#contratos-do-workflow)
- [Etapas/Fases](#etapasfases)
  - [Planejamento](#planejamento)
  - [Construção](#construcao)
  - [Revisão](#revisao)
  - [Testes](#testes)
- [Fluxo de Etapas/Fases](#fluxo-de-etapasfases)
  - [Agentes e responsabilidades](#agentes-e-responsabilidades)
  - [Sequência e transições](#sequencia-e-transicoes)
  - [Commits e pontos de salvamento](#commits-e-pontos-de-salvamento)
- [Notas de Implementação](#notas-de-implementacao)


### Contratos do Workflow

O workflow se apoia em três contratos. Cada contrato tem
uma seção própria e deve permanecer verificável.

#### 1. Diretrizes e Regras de Produto

As [Diretrizes e Regras de Produto](#diretrizes-e-regras-de-produto)
são insumos para o workflow.
O `devflow` verifica se elas existem e sugere sua criação quando
estão ausentes. O processo pode continuar sem elas, mas o `devflow`
deve alertar que os agentes perderam essa âncora de desenvolvimento.
Quando existem, os agentes baseiam a implementação nas diretrizes.

#### 2. Novo escopo

Antes da criação do Arquivo de Planejamento, o `devflow`
confirma se o novo escopo está definido. Se o humano quiser fazer
uma elicitação especializada, pode recomendar o `analista`, seguindo o
fluxo da [Ideação](#ideacao).

Se o humano preferir continuar, o `devflow` ajuda a definir o
escopo por perguntas mediadas. O plano só nasce depois dessa
definição.

#### 3. Arquivo de Planejamento

Fonte de verdade temporária durante o workflow. Criado pelo
`devflow` depois da definição do escopo, é entrada e saída de
cada agente. É commitado durante o trabalho como ponto de
salvamento e consultado para retomada e auditoria. É excluído
no encerramento com autorização humana. A aprovação do humano
é do plano apresentado na conversa, não do arquivo físico.

##### Formato do arquivo

O arquivo de planejamento segue o template definido pela skill
`planning-and-task-breakdown`.

Para permitir a retomada do workflow, mantém:

- `Status` no topo, indicando a fase atual;
- `## Perguntas`, para decisões pendentes do humano;
- `## Evidências de Testes — <fase>`, para evidências produzidas;
- o executor e o modelo utilizados nos registros de trabalho;
- o histórico das alterações relevantes.

O agente que conclui uma fase atualiza o `Status` antes de
retornar. Na construção, o arquivo registra etapas concluídas.
Na revisão, registra os resumos dos agentes. Alterações no plano
ocorrem na Revisão do Plano ou no gate de refatoração.

O arquivo é o handoff entre instâncias. Os agentes consultam o
arquivo para recuperar o contexto do workflow, em vez de depender
do histórico da conversa.

### Etapas/Fases

As etapas descrevem o tipo de trabalho realizado, seu resultado e
os agentes que podem participar. A ordem, os gates e os retornos
ficam no [Fluxo de Etapas/Fases](#fluxo-de-etapasfases).

#### Planejamento

Define o escopo técnico, registra as decisões e produz o plano
de implementação, os critérios de teste e os insumos de domínio.
O resultado é um plano que pode ser revisado e apresentado ao
humano para aprovação.

#### Construção

Implementa o plano aprovado e integra as alterações entre as
especialidades. Usa TDD, com testes primeiro, código depois e
análise de refatoração ao final. Os testes são especificação
executável, conforme a skill `tests-as-spec`.

#### Revisão

Revisão não é uma etapa independente. Ocorre no fim do
Planejamento e da Construção, com instâncias novas do `rev`.
Avalia o plano ou a implementação contra os insumos aprovados.

O `rev` não corrige. Produz achados no formato
`achado · ação · severidade`, que são encaminhados ao especialista
responsável.

#### Testes

Verifica o comportamento implementado segundo o plano e as
especificações de Testes por Especialidade, incluindo a
implementação e os testes produzidos. Produz as evidências do
ciclo para registro no Arquivo de Planejamento.

### Fluxo das Etapas/Fases

#### Agentes e responsabilidades

A tabela a seguir identifica os agentes, as fases em que participam no workflow de desenvolvimento e a responsabilidade de cada um por
fase.

| Agente            | Planejamento             | Construção                | Revisão                      | Testes                 |
|-------------------|--------------------------|---------------------------|------------------------------|------------------------|
| `devflow`         | Roteia e mantém status   | Roteia e mantém status    | Roteia a revisão             | Roteia e mantém status |
| `curador-produto` | Valida diretrizes       | —                         | Valida aderência             | Valida evidências     |
| `eng-software`    | Planeja o código         | TDD e integração          | Corrige achados              | —                      |
| `front`           | Prototipa telas          | Implementa a UI           | Corrige achados visuais      | —                      |
| `dba`             | Modela dados             | Atualiza modelo e scripts | Corrige achados de dados     | —                      |
| `sec`             | Analisa requisitos       | Gera configurações        | Corrige achados de segurança | Executa roteiro manual |
| `rev`             | —                        | —                         | Faz revisão independente     | —                      |
| `qa`              | Planeja testes           | —                         | —                            | Executa as suítes      |

A disposição dos agentes no processo de desenvolvimento foi otimizada para:

- **separação de contexto** por especialidade;
- **redução de consumo de tokens** via delegação focada;
- **qualidade** através de gates de revisão obrigatórios;
- **governança** com o humano no loop em pontos-chave;
- **higiene de contexto** — cada fase roda em instância
  nova, usando o arquivo de planejamento como handoff.


#### Premissas


0. Commits e pontos de salvamento

  - O `eng-software` é o **único committer** do workflow.
  Especialistas (`dba`, `sec`, `qa`, `front`, `rev`,
  `curador-produto`) são subagentes: editam arquivos e
  reportam `[arquivos alterados + resumo]` ao
  solicitante. O `eng-software` revisa o diff do especialista
  antes de commitar.

  - O `eng-software` carrega e segue a skill
  `git-workflow-and-versioning`: commits atômicos por unidade
  lógica, higiene pré-commit, mensagens Conventional Commit.
  Nunca inclui alterações alheias não reportadas. Nunca
  executa `git push` sem confirmação explícita do humano.


1. **`devflow` como roteador stateless**:
   - Lê o arquivo, identifica a fase pelo `Status`, spawna o
     agente adequado e recebe resumo curto.
   - **Nunca executa** tarefas de domínio.
   - Ao final da fase Testes, spawna `curador-produto` para
     validar a evidência do agregador.
   - Se houver falhas, re-spawna o agente ou consulta o humano.
2. **Contrato de retorno**: todo agente persiste resultado
   no arquivo e retorna resumo curto, com no máximo cinco linhas.
   A última linha informa `Skills: skill1, skill2` ou
   `Skills: nenhuma`.
3. **Instância nova a cada fase**: é obrigatória nas voltas,
   como gate de refatoração e re-revisões, e recomendada para
   todas as transições.
4. **Mediação de perguntas**: agentes com dúvidas formulam
   perguntas, salvam o progresso parcial e retornam ao
   `devflow`, que faz a mediação pela skill
   `question-orchestration`. O `devflow` usa o Checklist estrutural,
   a Continuidade da mediação e o Prompt-improver para o handoff,
   conforme `harness-conf/agents/devflow.md`.
5. **Falha de agente**: registra o impedimento e retorna.
   O `devflow` consulta o humano sobre corrigir e retentar,
   ajustar o escopo ou pular com registro.
6. **Agentes são agnósticos do workflow**: seus prompts descrevem
   capacidades, nunca fases. Apenas o `devflow` conhece o workflow.
7. **Seleção de modelo por fase**:
   - Ao iniciar, o `devflow` sugere um modelo por etapa.
     O humano define se prefere um modelo único, modelos por
     fase ou outro arranjo. O mapa combinado fica registrado
     no arquivo.
   - Se o harness suportar seleção de modelo por chamada,
     o mapa é aplicado em cada spawn. Sem esse suporte, o
     workflow pausa antes de uma fase que exija outro modelo.
   - A sessão é sempre nova. O workflow nunca retoma sessão
     anterior, nem na mesma fase.
   - O estado vive no arquivo de planejamento e na memória de
     longo prazo. Cada spawn recebe briefing autocontido, com
     ponteiros para os blocos relevantes.
   - No OpenCode com o plugin DCP, a tool `compress` é o
     mecanismo preferido de compactação. `/compact` é fallback.
   - A auto-compactação por threshold é rede de segurança.
     Se disparar, o agente lê trechos por offset/limit, faz
     consultas direcionadas e não reinsere arquivos e logs
     completos no contexto.

#### Fluxo Detalhado

1. **Planejamento**
   - `devflow` confirma o escopo e cria o Arquivo de Planejamento.
   - O `curador-produto` verifica as Diretrizes e Regras de
     Produto e registra as lacunas encontradas.
   - Os especialistas elaboram o plano de implementação, os
     critérios de teste e os demais insumos de domínio.
   - Decisões não triviais são mediadas com o humano. Arquivos
     grandes podem exigir divisão de escopo. Desvios de identidade
     visual exigem nova aprovação.
   - O `devflow` atualiza o `Status` para a revisão do plano.

2. **Revisão do plano**
   - O `devflow` aciona uma nova instância do `rev`.
   - O `rev` revisa o plano com as skills de domínio aplicáveis,
     usando o plano e os insumos originais do humano.
   - O `devflow` encaminha os achados aos especialistas
     responsáveis e solicita nova revisão quando necessário.
   - O humano aprova o plano apresentado na conversa. A aprovação
     não é do arquivo físico.
   - O humano controla as re-revisões. Não há loops automáticos.
   - O `devflow` atualiza o `Status` para Construção.

3. **Construção**
   - O `devflow` aciona os especialistas conforme o plano aprovado.
   - O `eng-software` coordena TDD, integração e commits.
   - A construção segue o plano sem novas consultas ao humano,
     exceto quando o gate de refatoração for acionado.
   - Se a integração exigir mudança no plano, o `eng-software`
     consulta o humano. O plano pode ser mantido, receber um
     ajuste mínimo ou retornar ao Planejamento quando a mudança
     for significativa.
   - O `devflow` atualiza o `Status` para revisão da construção.

4. **Revisão da construção**
   - O `devflow` aciona uma nova instância do `rev` para verificar
     a implementação contra o plano e as especificações.
   - O `rev` não corrige. Os achados são encaminhados aos
     especialistas responsáveis.
   - Depois das correções, o humano decide se haverá nova revisão.
     Não há loops automáticos.
   - O `devflow` atualiza o `Status` para Testes.

5. **Testes**
   - O `qa` executa `testes-produto` e os testes previstos no plano.
     Não analisa código.
   - O `sec` executa o roteiro manual de segurança.
   - A evidência do agregador usa o formato JSON
     `{ status, findings[] }` e é registrada no arquivo de
     planejamento.
   - O `curador-produto` verifica a presença e a completude da
     evidência.
   - Falhas de suíte são encaminhadas pelo `devflow` ao agente
     responsável e retornam à Construção. Mudanças de escopo ou
     comportamento retornam ao Planejamento.
   - O `devflow` atualiza o `Status` para Encerramento.

6. **Encerramento**
   - O `devflow` confirma que os gates foram concluídos.
   - O humano autoriza a exclusão do Arquivo de Planejamento e
     dos artefatos auxiliares.


## Notas de Implementação

### Interação agente–humano por plataforma

| Plataforma | Como spawna | Comunicação |
|---|---|---|
| **Copilot CLI** | `task(agent_type=...)` | Devflow media |
| **OpenCode** | Subagentes | Devflow media |

Subagentes retornam perguntas; `devflow` avalia e apresenta
ao humano. Exceção: agentes não mediados (ex: analista)
conversam direto com o humano.

**Mediação ao spawnar:** `curador-produto`, quando
spawnado, faz perguntas ao humano via `devflow`
(mediação), não diretamente.
