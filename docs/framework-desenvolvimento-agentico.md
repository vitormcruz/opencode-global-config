# Framework de Desenvolvimento Agêntico

## Objetivo

Criar uma organização em torno de especificações de negócio, testes e regras de validação que sirvam de memória do 
produto, contexto e harness para que agentes consigam evoluir no desenvolvimento do produto de maneira controlada, com 
insumo para que os humanos possam entender o sistema e orientar os agentes.

![Fluxo de Produto](./svgImage/FwcAgenticoBase.svg)
📍 **Navegar pelo diagrama:** [Governança de Produto](#governanca) · [Ideação](#ideacao)  · [Desenvolvimento](#desenvolvimento)

## Governança de Produto

A Governança de Produto é a dimensão responsável por estabelecer, organizar e manter a memória viva do sistema. Seu papel é definir a estrutura das especificações de negócio, os contratos técnicos, as suítes de validação e as instruções operacionais que servem de contexto e *harness* para todo o ciclo de vida do software.

O **`curador-produto`** é o único agente responsável por conduzir entrevistas estruturadas com o humano para criar ou modificar as Diretrizes e Regras de Produto. Ele também revisa e valida se as diretrizes foram seguidas em um fluxo de desenvolvimento.

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

- [Agentes](#agentes)
- [Commits](#commits)
- [Contratos do Workflow](#contratos-do-workflow)
- [Premissas](#premissas)
- [Schema do arquivo de planejamento](#schema-do-arquivo-de-planejamento)
- [Testes por Especialidade](#testes-por-especialidade)
- [Fluxo de Desenvolvimento](#fluxo-de-desenvolvimento)
- [Trabalho de curadoria](#trabalho-de-curadoria)
- [Notas de Implementação](#notas-de-implementação)


### Agentes

A tabela a seguir identifica os agentes, as fases em que participam no workflow de desenvilvimento e a responsabilidade de cada um por 
fase.

| Agente            | Planejamento                 | Construção                   | Validação                                          | 
|-------------------|------------------------------|------------------------------|----------------------------------------------------|
| `devflow`         | Roteia fases e mantém Status | Roteia fases e mantém Status | Roteia fases                                       | 
| `curador-produto` | —                            | —                            | Valida docs/README.md, testes-produto e evidências | 
| `eng-software`    | Planeja o código             | TDD e ajustes integrativos   | —                                                  | 
| `front`           | Prototipa telas              | Implementa UI                | Revisa identidade visual                           | 
| `dba`             | Modela dados                 | Atualiza modelo e scripts    | Revisa artefatos de BD                             | 
| `sec`             | Analisa segurança            | Gera configurações           | Revisa segurança e testa                           | 
| `rev`             | —                            | —                            | Revisão solo com skills de domínio                 | 
| `qa`              | Planeja testes               | —                            | Revisa cobertura e executa testes                  | 

A disposição dos agentes no processo de desenvolvimento foi otimizado para:

- **separação de contexto** por especialidade;
- **redução de consumo de tokens** via delegação focada;
- **qualidade** através de gates de revisão obrigatórios;
- **governança** com o humano no loop em pontos-chave;
- **higiene de contexto** — cada fase roda em instância
  nova, usando o arquivo de planejamento como handoff.

#### Commits

O `eng-software` é o **único committer** do workflow.
Especialistas (`dba`, `sec`, `qa`, `front`, `rev`,
`curador-produto`) são subagentes: editam arquivos e
reportam `[arquivos alterados + resumo]` ao
solicitante. O `eng-software` revisa o diff do especialista
antes de commitar.

O `eng-software` carrega e segue a skill
`git-workflow-and-versioning`: commits atômicos por unidade
lógica, higiene pré-commit, mensagens Conventional Commit.
Nunca inclui alterações alheias não reportadas. Nunca
executa `git push` sem confirmação explícita do humano.


### Contratos do Workflow

O workflow se apoia em seis contratos. Cada contrato tem
uma seção própria e deve permanecer verificável.

#### 1. Diretrizes e Regras de Produto

As [Diretrizes e Regras de Produto](# Diretrizes-e-Regras-de-Produto) são insumos para o 
workflow. O devflow deve avaliar se elas existem e sugerir a sua criação quando não. O 
processo pode continuar sem diretrizes, o agente perde a âncora para o desenvolvimento 
e o devflow deve alertar isso, mas se tudo estiver definido, os agentes do workflow vão 
amarrar toda a implementação às diretrizes.

#### 2. Novo escopo

Antes da criação do Arquivo de Planejamento, o `devflow`
confirma se o [novo escopo](#) está definido. Se o humano quiser fazer
uma elicitação especializada, pode recomendar o `analista`, seguindo o fluxo da [Ideação](#ideação).
Se o humano preferir continuar, o `devflow` ajuda a definir o
escopo por perguntas mediadas. O plano só nasce depois dessa
definição.

#### 3. Arquivo de Planejamento

Fonte de verdade temporária durante o workflow. Criado pelo
`devflow` depois da definição do escopo, é entrada e saída de
cada agente. Ciclo de vida:
commitado durante o trabalho como ponto de salvamento e
consultável para auditoria; excluído no encerramento com
autorização humana. A aprovação do humano é do plano
apresentado na conversa, não do arquivo físico. Ver schema
na seção "Schema do arquivo de planejamento".

## Premissas

### Orquestração

1. **`devflow` como roteador stateless**:
   - Lê o arquivo, identifica a fase pelo `Status`, spawna o
     agente adequado e recebe resumo curto.
   - **Nunca executa** tarefas de domínio.
   - Ao final da fase Testes, spawna `curador-produto` para
     validar a evidência do agregador.
   - Se houver falhas, re-spawna o agente ou consulta o humano.
2. **Contrato de retorno** — todo agente persiste resultado
   no arquivo e retorna resumo curto (≤ 5 linhas). Ultima
   linha: `Skills: skill1, skill2` ou `Skills: nenhuma`.
3. **Instância nova a cada fase** — obrigatório em voltas
   (gate de refatoração, re-revisões) e recomendado para
   todas as transições.
4. **Mediação de perguntas** — agentes com dúvidas formulam
   perguntas, salvam progresso parcial e retornam ao
   `devflow`, que media (skill `question-orchestration`,
   fonte única). Controles: Checklist estrutural,
   Continuidade da mediação, Prompt-improver para handoff
   — ver `harness-conf/agents/devflow.md` para detalhes.
5. **Falha de agente** — registra impedimento e retorna.
   `devflow` consulta humano: corrigir e retentar, ajustar
   escopo, ou pular com registro.
6. **Agentes são agnósticos do workflow** — prompts descrevem
   capacidades, nunca fases. Apenas `devflow` conhece o
   workflow.
7. **Seleção de modelo por fase**:
   - Ao iniciar, `devflow` sugere um padrão, com um modelo
     por etapa de planejamento, execução, testes e revisão.
     O humano define se prefere um modelo só, modelos por
     fase granular ou outro arranjo. O mapa combinado fica
     registrado no arquivo.
   - Se o harness suportar seleção de modelo por chamada
     (plugin de task), o mapa é aplicado diretamente em cada
     spawn, sem pausa.
   - Sem esse suporte, o workflow pausa antes de fases cujo
     modelo difere do atual para troca manual.
   - A sessão é sempre nova. O workflow nunca retoma sessão
     anterior, nem na mesma fase.
   - O estado vive no arquivo de planejamento e na memória de
     longo prazo. Cada spawn recebe briefing autocontido, com
     ponteiros para os blocos relevantes.
   - No OpenCode com o plugin DCP, a tool `compress` é o
     mecanismo preferido de compactação, acionada pelo próprio
     agente. `/compact` é fallback.
   - A auto-compactação por threshold é rede de segurança, não
     plano. Se disparar, a fronteira foi perdida. O agente lê
     trechos (offset/limit), faz consultas direcionadas e não
     reinsere arquivos e logs completos no contexto.

### Governança

8. **Humano aprova o plano** antes da construção. A
   aprovação é do plano apresentado na conversa (abstraído,
   por partes), não do arquivo físico.
9. **Humano controla re-revisões** — sem loops automáticos.
10. **Pós-planejamento, tudo se baseia no plano aprovado.**
11. **Planeje perguntando, execute com autonomia** — no
    planejamento, valide decisões não-triviais com o humano.
    Na construção, execute com autonomia. Exceção: gate de
    refatoração (premissa 31).
12. **Granularidade sensível ao contexto** — arquivo grande =
    escopo grande. `devflow` alerta e sugere divisão.
12.1. **Identidade visual como contrato** — desvios visuais
     requerem nova aprovação do humano.

### Revisão

13. **Revisão solo do `rev` com skills de domínio**:
    - Carrega skills aplicáveis (security-and-hardening,
      data-modeling, frontend-ui-engineering, tests-as-spec,
      api-and-interface-design, documentation-and-adrs).
    - Revisa com checklist.
    - **Não corrige**. Reporta achados no formato
      `achado · ação · severidade`.
    - `devflow` repassa o achado ao especialista responsável.
14. **Instâncias novas com contexto limpo** — obrigatório,
    sem exceção. Elimina viés de confirmação.
15. **Base de revisão** — plano aprovado e insumos originais
    do humano. Formato não prescrito.
16. **Formato do resumo:** achado · ação · severidade
    (bloqueante ou melhoria).
27. **`qa` não analisa código** — foca em execução de testes.
28. **Roteiro manual de segurança é do `sec`**. A suíte
    automática entra no agregador executado pelo `qa`.

### Arquivo de planejamento

17. **Fonte de verdade temporária** — commitado durante o
    trabalho como ponto de salvamento e consultável para
    auditoria; excluído no encerramento com autorização
    humana. `curador-produto` exclui plano e artefatos
    auxiliares.
17.1. **Seção de evidências** —
     `## Evidências de Testes — Testes`. `curador-produto`
     lê a evidência do agregador no fim da fase Testes.
18. **Campo `Status` obrigatório** no topo. O agente que
    conclui uma fase atualiza o status antes de retornar.
19. **Regras de escrita:**
    - Na construção, apenas marca etapas concluídas.
    - Na revisão, resumos são persistidos.
    - Modificações no plano só na Revisão do Plano ou no gate
      de refatoração.
    - O histórico de mudanças é registrado.
20. **Contexto via arquivo** — não via histórico da conversa.
20.1. **Rastreabilidade do executor**: cada subseção de registro de trabalho
     informa `Executor: <agente> / <modelo>`. O campo registra o agente e o
     modelo usados.

##### Schema do arquivo de planejamento

Seções obrigatórias na ordem:

```markdown
Status: <FASE> [— detalhe opcional]

##### Regras de Produto

| Campo | Tam. máx | Tipo/Formato | Máscara | Limite | Obs |
|-------|----------|-------------|---------|--------|-----|

##### Evidências de Testes — <fase>

(evidências de cada agente que atuou na fase)

##### Perguntas

(perguntas pendentes de decisão humana)
```

- **Status**: `VALIDAÇÃO`, `PLANEJAMENTO`, `REVISÃO DO PLANO`,
  `CONSTRUÇÃO`, `GATE-REFATORAÇÃO — volta ao planejamento`,
  `REVISÃO DA CONSTRUÇÃO`, `TESTES`, `FINALIZAÇÃO`.
- **Regras de Produto**: tabela de restrições de domínio.
- **Evidências de Testes — Testes**: evidência do
  agregador `testes-produto`.
- **Perguntas**: pendências de decisão humana.

### [docs/README.md](README.md)

21. **O workflow exige um docs/README.md** — criação e
    manutenção pelo `curador-produto`. A fase de VALIDAÇÃO detecta
    ausência ou problema. O `devflow` aciona e medeia o curador,
    sem editar ou validar o conteúdo.
21.1. **Regras de Produto — preenchimento incremental** —
     `eng-software` inicializa no planejamento. Campos sem
     definição: `(a definir)`. Agentes consultam, perguntam
     se ausente, registram antes de prosseguir.
21.2. **Especificação evolutiva** — pode mudar durante o
     planejamento. Mudanças de "o quê" alteram spec;
     mudanças de "como" não. `curador-produto` verifica
     consistência.
21.3. **Documentação de spec por domínio** — docs/README.md
     define artefatos, formato e destino por agente/fase.
25. **`curador-produto` valida aderência ao docs/README.md** —
    não cria escopo nem requisitos. Na finalização, verifica
    existência de artefatos obrigatórios. Guarda do humano:
    após correção, pergunta se resubmete ou segue.

### Construção

29. **Construção em três etapas (TDD):** testes primeiro →
    código → análise de refatoração. Testes são
    especificação executável (ver skill `tests-as-spec`).
30. **Autonomia na construção** — sem consultar o humano,
    seguindo o plano aprovado.
31. **Gate de refatoração** — acomodar código novo ao
    existente pode mudar o plano. `eng-software` consulta
    humano: nada muda, ajuste mínimo (propõe e registra),
    ou mudança significativa (volta ao planejamento).

### Testes por Especialidade

32. **Índices no [`AGENTS.md`](../AGENTS.md)** — criação pelo
    `curador-produto`. O `AGENTS.md` mantém o link geral para o
    `docs/README.md`, a tabela de Testes por Especialidade com link
    âncora e as Instruções por Agente. A spec fica na seção "Testes por
    Especialidade" do `<pasta-docs>/README.md`; o conteúdo detalhado
    não é copiado para o `AGENTS.md`.
    Suítes não rodam na Construção nem na Revisão.
33. **Fase Testes** — `qa` executa só `testes-produto` e
    manuais do plano. `sec` executa só o roteiro manual.
34. **Evidência** — JSON `{ status, findings[] }` do
    agregador, persistida na fase Testes.
35. **Validação pelo `curador-produto`** — no fim da fase
    Testes, confere se o agregador rodou e se a evidência está
    presente e completa. Registra OK/FALHA/LACUNA e encaminha o
    achado ao `devflow`. O `devflow` encaminha a correção ao agente
    responsável ou consulta o humano quando a decisão depender dele.
36. **Falha de suíte** — backend → `eng-software`; dados →
    `dba`; segurança automática → `sec`; frontend →
    `front`. Depois `eng-software` normaliza e commita.
    Então "re-executar?".

## Fluxo de Desenvolvimento

1. **Inicialização & Escopo**
   - `devflow` alinha/confirma o escopo com o Humano (sugere `analista` se for elicitação aberta).
   - `devflow` cria o Arquivo de Planejamento com `Status: VALIDAÇÃO`.

2. **Validação (Gate de Curadoria)**
   - `devflow` pede ao `curador-produto`: verificar integridade de `docs/README.md` e `AGENTS.md`.
   - Se houver lacuna, `devflow` pergunta ao Humano se trata agora ou registra para seguir.
   - `devflow` atualiza status para `PLANEJAMENTO`.

3. **Planejamento**
   - `devflow` despacha tarefas pontuais de domínio para cada especialista:
     - `eng-software`: arquitetura, plano de código e inicialização das Regras de Produto.
     - `front`: prototipação de telas (se houver UI).
     - `dba`: modelagem de dados.
     - `sec`: requisitos e análise de segurança.
     - `qa`: estratégia e planejamento de testes.
   - Cada especialista apenas cumpre sua tarefa, registra no plano e devolve resumo (≤ 5 linhas).
   - `devflow` atualiza status para `REVISÃO DO PLANO`.

4. **Revisão do Plano**
   - `devflow` pede ao `rev`: auditar o plano com checklists de domínio.
   - Se houver apontamentos, `devflow` aciona o especialista responsável para ajustar e pede revalidação ao `rev`.
   - `devflow` apresenta o plano consolidado ao Humano para aprovação explícita.
   - `devflow` atualiza status para `CONSTRUÇÃO`.

5. **Construção**
   - `devflow` aciona a execução conforme o plano aprovado:
     - `dba`: scripts de banco e migrações.
     - `front`: implementação de interface (se houver).
     - `eng-software`: TDD (testes → código), integração do lote e commits.
   - *Gate de refatoração*: se o código exigir mudança no plano, `eng-software` alerta o `devflow`, que consulta o Humano antes de prosseguir.
   - `devflow` atualiza status para `REVISÃO DA CONSTRUÇÃO`.

6. **Revisão da Construção**
   - `devflow` pede ao `rev`: auditar a implementação contra o plano aprovado.
   - Se houver correções, `devflow` direciona ao especialista adequado, `eng-software` normaliza/commita e `devflow` consulta o Humano sobre re-revisão.
   - `devflow` atualiza status para `TESTES`.

7. **Testes**
   - `devflow` pede ao `qa`: rodar `testes-produto` + testes manuais e registrar evidência JSON.
   - `devflow` pede ao `sec`: executar roteiro manual de segurança.
   - `devflow` pede ao `curador-produto`: validar presença e completude da evidência do agregador.
   - Em caso de falha em suítes, `devflow` aciona o especialista da área (backend/dados/segurança/front) para corrigir e `eng-software` para commitar.
   - `devflow` atualiza status para `FINALIZAÇÃO`.

Na fase **Testes**, o `qa` executa o agregador `testes-produto` e
registra no arquivo de planejamento a evidência no formato definido.
Ao final da fase, o `curador-produto` verifica se essa evidência está
presente e completa. Se houver falha ou lacuna, o `curador-produto`
registra o achado e o `devflow` encaminha a correção ao agente
responsável ou consulta o humano quando a decisão depender dele.

8. **Finalização**
   - `devflow` pede ao `curador-produto`: auditar existência dos artefatos de especificação mapeados no `docs/README.md`.
   - Havendo lacuna, `devflow` aciona `eng-software` para criar e `curador-produto` para revalidar.
   - `devflow` pede confirmação ao Humano e aciona `curador-produto` para excluir o plano temporário.

## Trabalho de curadoria

O trabalho de curadoria (criação e manutenção do
`docs/README.md` e dos índices do `AGENTS.md`) ocorre dentro da fase
de VALIDAÇÃO quando o curador detecta uma lacuna e o humano decide
tratar o problema naquele ciclo.

### Gate de curadoria na VALIDAÇÃO

1. `devflow` aciona `curador-produto`.
2. `curador-produto` verifica `docs/README.md` e os índices do
   `AGENTS.md`, e retorna um relatório.
3. Se houver lacuna, `devflow` pergunta **"Tratar a curadoria agora?"**
   - **Sim**: `devflow` aciona e medeia o trabalho do curador.
     Depois, aciona o curador novamente para revalidar.
   - **Não**: `devflow` registra a lacuna em `## Perguntas` e segue.
4. Se tudo estiver OK, segue para PLANEJAMENTO.

### Planejamento da curadoria (item a item)

`devflow` aciona `curador-produto` e medeia a interação com o humano.
O curador percorre cada seção usando os blocos adaptativos da
`question-orchestration`:

- **docs/README.md** — Definição de Escopo, Elementos de
  Especificação, Estratégias de Indexação de Código e Testes por
  Especialidade. `Regras de Documentação` é uma subseção de
  Elementos de Especificação. Cada seção requer aprovação explícita.
- **AGENTS.md** — link geral para o mapa, índice de Testes por
  Especialidade e Instruções por Agente. Cada entrada requer aprovação
  explícita.

### Construção da curadoria

1. `curador-produto` escreve o `docs/README.md` aprovado.
2. `curador-produto` spawna `eng-software` com briefing para
   implementar scripts de testes-produto com TDD.
3. `curador-produto` registra tabela no `AGENTS.md`.

### Validação da curadoria

1. `eng-software` roda os scripts de testes-produto
   implementados.
2. `curador-produto` verifica o verde — validação objetiva
   (resolve "não valida o que editou").
3. Verde → curadoria concluída. `devflow` volta ao gate de curadoria.

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
