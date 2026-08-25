# Workflow de Agentes — Desenvolvimento (`dev`)

## Objetivo

Workflow multi-agente para desenvolvimento de funcionalidades,
otimizado para:
- **separação de contexto** por especialidade;
- **redução de consumo de tokens** via delegação focada;
- **qualidade** através de gates de revisão obrigatórios;
- **governança** com o humano no loop em pontos-chave;
- **higiene de contexto** — cada fase roda em instância
  nova, usando o arquivo de planejamento como handoff.

> **Nota:** este workflow começa em PLANEJAMENTO. A fase
> de VALIDAÇÃO (verificação de docs/README.md e Harness)
> e a ELICITAÇÃO de escopo foram transferidas para o
> **workflow de Definição de Escopo**
> (`docs/workflow-definicao-escopo.md`), que roda antes
> deste.

## Sequência de Workflows

O `devflow` sempre executa os workflows na seguinte
ordem:

```
devflow
  └── workflow-curadoria.md        ← Valida docs/README.md e Harness
        (curador-produto, curador-produto-editor)
  └── workflow-definicao-escopo.md ← Elicita requisitos
        (analista, revisor-historia)
  └── workflow-agentes-dev.md      ← Desenvolvimento (este arquivo)
        (começa em PLANEJAMENTO)
```

- [`workflow-curadoria.md`](workflow-curadoria.md) —
  garante que docs/README.md e Harness existem e estão
  válidos antes de qualquer elicitação ou desenvolvimento.
- [`workflow-definicao-escopo.md`](workflow-definicao-escopo.md) —
  elicita requisitos e critérios com o humano, produz o
  Arquivo de Planejamento.
- Este workflow (`workflow-agentes-dev.md`) — executa o
  ciclo completo de desenvolvimento a partir do
  Arquivo de Planejamento já preenchido.

## Agentes

| Sigla | Nome completo | Tipo | Fases onde atua |
|---|---|---|---|
| `devflow` | Orquestrador | Roteador | Todas; apenas roteia |
| `eng-software` | Engenheiro de Software | Executor | Planejamento e construção |
| `front` | Engenheiro Frontend | Executor | Planejamento, construção e revisões |
| `curador-produto` | Curador de Produto | Executor | Revisões e finalização |
| `dba` | Analista de BD | Executor | Planejamento, construção e revisões |
| `sec` | Analista Cyber | Executor | Planejamento, construção, revisões e testes |
| `rev` | Revisor Integrativo | Executor | Revisões do plano e da construção |
| `qa` | Testador | Executor | Planejamento, revisões e testes |
| `val-harness` | Validador de Harness | Executor | Construção e revisão da construção |

## Commits dos Agentes

Os agentes `eng-software`, `front`, `qa`, `rev`, `sec`,
`val-harness` e `dba` versionam suas próprias alterações.
Antes de commitar, devem carregar e seguir a skill
`git-workflow-and-versioning`.

O agente decide o ponto de commit conforme a skill: uma task
isolada ou um conjunto coerente de duas ou três tasks pode
formar uma unidade lógica. O plano não deve ser reorganizado
para forçar commits. Cada commit deve conter somente arquivos
sob responsabilidade do agente, passar pela higiene
pré-commit e usar uma mensagem Conventional Commit descritiva.

Essa autonomia de versionamento não altera a autoridade do
humano sobre escopo, requisitos, decisões de produto ou
aprovação do resultado. Agentes não executam `git push` sem
confirmação explícita do humano.

### Especialidades

| Agente | Planejamento | Construção | Validação |
|---|---|---|---|
| `devflow` | Roteia fases e mantém o Status | Roteia fases e mantém o Status | Roteia fases |
| `eng-software` | Planeja o código | TDD e ajustes integrativos | — |
| `curador-produto` | — | — | Valida docs/README.md e harness |
| `dba` | Modela dados | Atualiza modelo e scripts | Revisa artefatos de BD |
| `sec` | Analisa requisitos de segurança | Gera configurações | Revisa segurança e testa |
| `qa` | Planeja testes | — | Revisa cobertura e executa testes |
| `front` | Prototipa telas | Implementa UI | Revisa identidade visual |
| `rev` | — | — | Revisa consistência e aderência ao plano |
| `val-harness` | — | — | Valida evidências de harness |

> **Nota de sequenciamento (P26):** `sec` analisa
> requisitos de segurança com base no plano de
> implementação do `eng-software` — por isso é spawnado
> após o engenheiro no planejamento.

## Contratos do Workflow

O workflow se apoia em quatro contratos formais. Cada um
é um artefato do projeto — deve existir, ser mantido e
ser verificável.

### 1. docs/README.md

Arquivo que define como a documentação do produto se
organiza e como deve ser mantida. Contém 3 seções:
Definição de Escopo, Elementos de Especificação e
Estratégias de Indexação de Código. É o contrato de
documentação do projeto.
Definição e criação: ver `docs/workflow-curadoria.md`.
Premissa de consumo: 21.

### 2. Harness por Agente

Regras de contenção e direcionamento de cada agente —
ativadas como regras de prompt, ferramentas ou scripts.
O Harness deve estar listado no AGENTS.md do projeto.
Definição e criação: ver `docs/workflow-curadoria.md`.
Premissas de execução: 32–36.

### 3. Arquivo de Planejamento

Arquivo temporário que serve de fonte de verdade durante
o processamento do workflow. É gerado pelos agentes e é 
a entrada e saída de cada um deles — todo resultado é persistido 
nele, todo contexto é lido dele. Descartável ao fim do processo.
Premissas detalhadas: 17–20.

### 4. Verificação de Harness

Saída obrigatória dos agentes: lista de evidências de
execução do harness apontando para logs ou artefatos que
comprovem o cumprimento das regras. O `val-harness` é
responsável por validar essas evidências em lote ao
final das fases de **Construção** e **Revisão da
Construção** (quando houve modificações) — **esta é a
sua única função**.
O `devflow` recebe o relatório do `val-harness` e decide
a ação (re-spawnar agente ou consultar humano).
Premissas detalhadas: 32–36.

### 6. DevFlowNotes (Modo Debug)

Arquivo opcional de observação ativado pelo humano
(`modo debug on`). Registra notas contextuais quando o
humano escreve `**[texto]**` e acumula skills utilizadas
por agente/fase. Criado no root do projeto como
`DevFlowNotes-YYYY-MM-DD.md`. Descartável ao fim do
processo (junto com o arquivo de planejamento).
Definição detalhada: ver `agents/devflow.md`, seção
"Modo Debug".

### 5. Elementos de Especificação

O docs/README.md define para cada elemento de
especificação do software: (1) o que é,
(2) formato/ferramenta, (3) qual agente cria, (4) em
qual fase, (5) onde vive permanentemente.

O padrão de preenchimento — inicializar, enriquecer
incrementalmente, nunca re-perguntar o que já está
registrado, curador valida — aplica-se a **todos** os
elementos de spec mapeados, não apenas a um.

**Exemplo: Regras de Produto** — seção no arquivo de
planejamento que reúne restrições técnicas de domínio
por campo (tamanho máximo, tipo/formato, máscara de
exibição, limites numéricos, regras de validação). É o
contrato de dados do domínio. `eng-software` inicializa
a seção ao planejar; qualquer agente que precisar de uma
regra ausente consulta a seção, pergunta ao humano se
não estiver registrada e registra antes de prosseguir.
Regras já registradas nunca são reperguntadas.

Outros elementos de spec (requisitos, critérios de
aceitação, plano de testes, modelo de dados, threat
 model, etc.) seguem o mesmo padrão — o docs/README.md define o
que, quem, quando e onde para cada um.
Premissas detalhadas: 21.1–21.3.

## Premissas

### Orquestração

1. **`devflow` como roteador stateless** — lê o arquivo de
   planejamento, identifica a fase atual pelo campo
   `Status`, spawna o agente adequado e recebe de volta
   apenas um resumo curto. `devflow` **nunca executa** tarefas
   de domínio; sua função é **rotear** e
   **contextualizar** os agentes. Ao final das fases de
   **Construção** e **Revisão da Construção** (quando
   houve modificações), spawna `val-harness` para
   validação em lote das evidências de harness. Se o
   `val-harness` reportar falhas, `devflow` re-spawna o
   agente faltante ou consulta o humano (ver premissa 35).
2. **Contrato de retorno: resultado no arquivo, resumo
   curto** — todo agente spawnado por `devflow` persiste seu
   resultado no arquivo de planejamento e retorna apenas
   um resumo curto (≤ 5 linhas). A ultima linha do resumo
   lista as skills utilizadas: `Skills: skill1, skill2` ou
   `Skills: nenhuma`. Isso mantém o contexto do `devflow`
   leve ao longo de todo o workflow.
3. **Instância nova a cada fase** — quando uma fase
   termina, `devflow` spawna instância nova do agente para a
   próxima fase. Nenhum agente executor carrega contexto
   de fases anteriores. Isso é **obrigatório** quando há
   volta a fases anteriores (gate de refatoração,
   re-revisões) e **recomendado** para todas as
   transições.
4. **Quando têm dúvidas que dependem de decisão, agentes
   formulam perguntas, salvam progresso parcial e
   retornam.** O Devflow media a comunicação agente-humano
   em modo orquestrado (ver premissas 4.1 a 4.4).
   4.1. **Protocolo de mediação** — Devflow aplica a skill
        `question-orchestration` no modo mediado. Essa skill
        é a fonte única de organização e apresentação de
        perguntas; os agentes não precisam carregá-la.
   4.2. **Checklist estrutural** — Devflow avalia cada
        pergunta: decisão explícita, contexto, opções com
        trade-offs, recomendação justificada e pergunta
        autocontida. Itens ausentes retornam ao agente para
        reformulação. Máximo 2 rodadas; na 3ª, apresenta ao
        humano com a nota: "Agente não conseguiu detalhar
        mais."
   4.3. **Continuidade da mediação** — Devflow nunca encerra
        a mediação por conta própria. Continua enquanto o
        humano quiser prosseguir. Se o humano não entender
        após reformulações, oferece alternativas, mas só para
        quando ele decidir.
   4.4. **Prompt-improver para handoff** — Antes de spawnar
        um subagente, Devflow usa `prompt-improver`
        autonomamente no modo de briefing interno. O insumo
        original do humano continua como fonte de verdade; o
        briefing não inventa decisões nem resolve
        ambiguidades, que retornam pela mediação.
5. **Falha de agente** — se não consegue completar a
   tarefa (erro, incerteza, falta de informação), registra
   o impedimento no arquivo e retorna resumo ao `devflow`,
   que consulta o humano para decidir: corrigir e
   retentar, ajustar escopo, ou pular com registro.
6. **Agentes são agnósticos do workflow** — o prompt de
   cada agente descreve **capacidades** (o que sabe
   fazer), nunca fases ou sequência do workflow. Apenas
   o `devflow` conhece o workflow e decide quando chamar
   cada agente. Os demais agentes funcionam tanto
   sozinhos (chamados diretamente pelo humano) quanto
   orquestrados (spawnados pelo `devflow`), sem mudança
   no prompt.
7. **Seleção de modelo por fase** — ao iniciar o workflow,
   `devflow` pergunta ao humano (via tool `ask`/`question`)
   qual modelo usar. A pergunta oferece duas opções:
   - **Usar o modelo atual para todas as fases** — nenhuma
     parada adicional entre fases.
   - **Definir por fase** — o humano lista no formato
     `<nº>. <modelo>` (fases omitidas usam modelo atual):
      ```
      1-PLANEJAMENTO  2-REVISÃO DO PLANO
      3-CONSTRUÇÃO  4-REVISÃO DA CONSTRUÇÃO  5-TESTES
      6-FINALIZAÇÃO
      ```
   O mapa de modelos é registrado no arquivo de
   planejamento. Aplicação por plataforma:
    - **Copilot CLI**: `devflow` instrui o uso de `/model` ou define o modelo
      na criação da sessão via SDK.
   - **OpenCode**: `devflow` para antes de fases com modelo
     diferente do anterior e solicita ao humano que
      troque o modelo antes de prosseguir.

    Política de sessão: dentro da fase, a sessão é retomada; entre fases,
    uma sessão nova é criada. O identificador segue
    `{workflowId}-{fase}-{agente}`. O Copilot CLI usa
    `resumeSession(sessionId)` e `createSession(sessionId novo)`; o OpenCode
    preserva `task_id` dentro da fase e cria instância nova entre fases.

7.1. **Modo Debug** — o humano pode ativar o modo debug
     a qualquer momento (`modo debug on`). Quando ativo,
     o `devflow` cria o arquivo `DevFlowNotes-YYYY-MM-DD.md`
     no root do projeto e captura comentarios do humano no
     formato `**[texto]**`, registrando contexto e nota.
     Skills utilizadas por cada agente sao acumuladas no
     final do arquivo. O modo debug se aplica a **todo o
     workflow** (curadoria, definição de escopo e
     desenvolvimento). Ver `agents/devflow.md`, seção
     "Modo Debug".

### Governança

8. **Humano aprova o plano** antes da construção iniciar.
9. **Humano controla re-revisões** — após ajustes, o humano
   decide se resubmete para revisão ou segue adiante.
   Isso evita loops infinitos.
10. **Pós-planejamento, tudo se baseia no plano aprovado** —
    falhas de teste são tratadas como bugs.
11. **Planeje perguntando, execute com autonomia** — no
    planejamento, todo agente deve validar cada decisão
    não-trivial com o humano, formulando perguntas e
    retornando para mediação do Devflow (ver premissa 4).
    Decisões triviais (nome de variável, formatação,
    ordem de passos sem impacto funcional) não precisam
    de validação. Tudo o que for persistido no arquivo
    de planejamento deve ter passado pelo humano.
    Na construção, deve executar com máxima autonomia,
    sem intervenções desnecessárias. A **única exceção**
    é o gate de refatoração (ver premissa 31).
12. **Granularidade sensível ao contexto** —
    `eng-software` deve avaliar o tamanho do plano em
    relação à capacidade de revisão do humano e ao
    contexto do agente. Se o plano for grande demais,
    sugere dividir. Se for pequeno demais, sugere agregar
    funcionalidades. A decisão final é do humano.
    **Arquivo de planejamento grande = escopo grande
    demais** — o arquivo é efêmero e deve permanecer
    leve. Se o arquivo crescer a ponto de comprometer
    o contexto dos agentes, `devflow` deve alertar o humano
    e sugerir divisão do escopo.
12.1. **Identidade visual como contrato** — quando o
    plano inclui protótipos de tela aprovados pelo
    humano, a identidade visual (paleta de cores,
    tipografia, layout estrutural, hierarquia visual,
    espaçamentos) é tratada como contrato. Na construção,
    `front` pode evoluir o código dos componentes, mas
    desvios da identidade visual aprovada requerem nova
    aprovação explícita do humano. O `rev` inclui
    aderência visual no checklist integrativo.

### Revisão

13. **Revisão híbrida: especialistas + integrativa** —
    revisores especializados (`dba`, `sec`, `qa`) revisam
    e corrigem artefatos da sua área, devolvendo resumo
    estruturado. `rev` atua como revisor integrativo:
    verifica consistência entre as partes e aderência ao
    plano, mas **não corrige** — devolve relatório para
    `eng-software` aplicar diretamente (exceto correções
    complexas, delegadas ao especialista).
14. **Revisores são sempre instâncias novas com contexto
    limpo** — toda revisão é executada por uma instância
    nova do agente, sem histórico da conversa anterior.
    O agente que planejou ou construiu **nunca** revisa
    na mesma instância. Isso elimina viés de confirmação
    e garante avaliação independente. **Esta regra não tem
    exceção e se aplica tanto aos revisores especializados
    (`dba`, `sec`, `qa`) quanto ao revisor integrativo
    (`rev`).**
15. **Base de revisão** — revisores avaliam com base no
    plano aprovado e nos insumos originais do humano
    (requisitos, critérios de aceitação, regras de
    negócio). O formato dos insumos não é prescrito
    pelo workflow.
16. **Formato do resumo de revisão especializada:**
    - **Achado**: o que estava errado
    - **Ação**: o que foi corrigido
    - **Severidade**: bloqueante ou melhoria
27. **`qa` não analisa código** — foca em execução de
    testes.
28. **Testes de segurança são do `sec`**, não do `qa`.
    Isso inclui testes dinâmicos (DAST, pen testing
    automatizado) — são testes funcionais especializados
    em segurança, não testes de lógica de negócio.

### Arquivo de planejamento

17. **Arquivo como fonte de verdade temporária** — plano,
    revisões e status das etapas ficam persistidos.
    Permite retomada em caso de interrupção.
    **O arquivo é descartável**: ao fim do processo de
    implementação, `curador-produto` o exclui, junto com
    quaisquer artefatos auxiliares gerados durante o
    planejamento (ex.: protótipos de tela em `plan/ui/`).
17.1. **Seção de evidências de harness** — o arquivo deve
    conter uma seção `## Evidências de Harness — <fase>`
    onde cada agente persiste suas evidências ao final
    da execução. O `val-harness` lê apenas esta seção +
    AGENTS.md para realizar a validação em lote.
17.2. **Arquivo grande = escopo grande** — o arquivo de
    planejamento é efêmero e deve permanecer leve.
    Quando o arquivo crescer a ponto de comprometer o
    contexto dos agentes, o `devflow` deve alertar o humano
    e sugerir redução de escopo (conforme premissa 12).
18. **Campo `Status` obrigatório** — o arquivo deve conter
    um campo de status no topo (ex.:
    `Status: CONSTRUÇÃO — etapa 2/3`) que permite ao
    `devflow` identificar a fase atual sem interpretar o
    conteúdo. O agente que conclui uma fase atualiza o
    status antes de retornar ao `devflow`.
19. **Regras de escrita do arquivo:**
    - Na **construção**, `eng-software` apenas marca
      etapas como concluídas (checkbox). O conteúdo do
      plano não é alterado.
    - Na **revisão**, resumos dos revisores e relatório
      do `rev` são persistidos na seção dedicada. O plano
      original permanece intacto.
    - Modificações no plano só ocorrem na fase de
      **Revisão do Plano**, antes da aprovação do humano,
      **ou durante o gate de refatoração** na construção
      (ver premissa 31).
    - Quando o plano é alterado durante a construção,
      o histórico da mudança (motivo, o que mudou, decisão
      do humano) deve ser registrado no arquivo para que
      todos os agentes tenham conhecimento e a retomada
      seja possível.
20. **Contexto via arquivo** — agentes usam o arquivo de
    planejamento como fonte de contexto, não o histórico
    acumulado da conversa.

### docs/README.md

21. **O workflow exige um docs/README.md** — a definição,
    criação e manutenção do docs/README.md são
    responsabilidade do `curador-produto-editor` conforme
    descrito em `docs/workflow-curadoria.md`. O
    `curador-produto` detecta ausência do docs/README.md
    na fase de Validação (workflow de Definição de Escopo)
    e aciona `curador-produto-editor` para criá-lo. Se o
    docs/README.md não existir, o fluxo para até que seja
    criado.
21.1. **Regras de Produto — preenchimento incremental** —
    a seção `## Regras de Produto` é inicializada por
    `eng-software` na fase de Planejamento com o que já
    for identificável dos requisitos. Campos sem definição
    recebem `(a definir)`. Em todas as fases, cada agente
    que precisar de uma regra ausente: (1) consulta a
    seção, (2) se não encontrar, pergunta ao humano,
    (3) registra antes de prosseguir. Nenhum agente
    repergunta o que já está registrado.
    Formato canônico da seção:

    | Campo | Tam. máx | Tipo/Formato | Máscara        | Limite numérico | Observação      |
    |-------|----------|--------------|----------------|-----------------|-----------------|
    | nome  | 100      | texto        | —              | —               | —               |
    | valor | —        | decimal      | —              | 0–999.999,99    | 2 casas         |

21.2. **Especificação evolutiva no planejamento** — a
    especificação (requisitos, critérios de aceitação,
    regras de produto) é dada como entrada, mas pode
    mudar durante o **planejamento**. Qualquer agente
    cuja pergunta ao humano resulte em mudança de spec
    deve registrar a alteração no arquivo de
    planejamento, na seção do elemento de spec
    correspondente (conforme o docs/README.md).
    **Distinção**: mudanças de "como" (arquitetura,
    abordagem técnica) não alteram spec; mudanças de
    "o quê" (escopo, requisitos, critérios de aceitação)
    alteram. O `curador-produto`, ao revisar o plano,
    verifica se mudanças de spec foram registradas e se
    estão consistentes com o docs/README.md. Na **construção**,
    a premissa 10 se mantém — tudo se baseia no plano
    aprovado. Se algo inviabilizar um critério de
    aceitação, o gate de refatoração (premissa 31) já
    trata o retorno ao planejamento.
21.3. **Documentação de spec por domínio** — o docs/README.md
    define, por projeto, quais artefatos de
    especificação cada agente deve criar ou atualizar,
    em qual formato e onde vivem permanentemente.
    Exemplos não-prescritivos: critérios de aceitação
    como specs executáveis (eng-software cria no TDD),
    plano de testes em arquivo permanente (qa extrai ao
    final), modelo de dados em DBML (dba cria/atualiza),
     threat model em docs/ (sec, se o docs/README.md definir).
    Cada agente, ao concluir sua fase, consulta o
    docs/README.md para verificar obrigações de
    documentação de spec em seu domínio para essa fase.
    Se o docs/README.md não definir obrigações para um
    agente/fase, nada a fazer.
25. **`curador-produto` valida aderência ao docs/README.md,
    não requisitos** — verifica se artefatos produzidos
    estão em conformidade com o docs/README.md. Não cria
    escopo nem requisitos. Participa dos loops de revisão
    verificando se documentação planejada/produzida está
    conforme o docs/README.md. **Não altera** o
    docs/README.md nem harness diretamente — delega ao
    `curador-produto-editor`. Para artefatos de outros
    domínios (código, BD, segurança), devolve instruções
    de ajuste ao `devflow`. Faz revisão final de
    documentação e estrutura.
    **Finalização — verificação de spec e exclusão do
    plano:** ao finalizar, `curador-produto` lê o
    docs/README.md e lista todos os artefatos de spec
    obrigatórios.
    Para artefatos com Destino definido (caminho):
    verifica existência no local definitivo. Para
    artefatos com Destino `nenhum`: ignora (descartados
    com o plano). Reporta lacunas ao `devflow` com instrução
    de qual agente spawnar. Após `devflow` spawnar agentes e
    receber retorno, `curador-produto` revalida.
    **Guarda do humano**: após cada rodada de correção,
    `devflow` pergunta ao humano se deseja resubmeter para
    revalidação ou seguir adiante (similar à revisão,
    premissa 9). Isso evita loops infinitos. Só confirma
    conclusão (permitindo exclusão do plano e artefatos
    auxiliares temporários, ex.: protótipos de tela em
    `plan/ui/`) após verificar que toda documentação
    obrigatória existe **ou** após o humano decidir
    encerrar o loop.

### Construção

29. **Construção em três etapas (TDD):**
    1. **Testes primeiro** — `eng-software` implementa os
       testes automatizados que devem falhar.
    2. **Código** — implementa o código que faz os testes
       passarem.
    3. **Análise de refatoração** — avalia como acomodar o
       código novo ao existente.

    **Testes são especificação** — testes implementados
    conforme o plano são especificação executável do
    sistema. Na construção, se um teste falha, o código
    está errado — não o teste. Se testes se contradizem,
    o plano precisa ser revisado (gate P31). Alteração
    de testes existentes só ocorre no planejamento, como
    mudança de spec. Ver skill `tests-as-spec`.
30. **Na etapa de testes e código, `eng-software` executa
    com autonomia** — sem consultar o humano, seguindo o
    plano aprovado.
31. **Gate de refatoração** — a análise de refatoração é
    um ponto sensível. Acomodar código novo ao existente
    **pode mudar o plano**. Quando `eng-software`
    identifica essa possibilidade, **deve sempre consultar
    o humano**. Os cenários possíveis são:
    - Nada muda → segue normalmente.
    - Ajuste mínimo no plano → `eng-software` propõe,
      humano aprova, registra no arquivo e segue.
    - Mudança significativa → `eng-software` registra o
      estado no arquivo, atualiza o `Status` para
      `GATE-REFATORAÇÃO — volta ao planejamento` e
      retorna ao `devflow`. O `devflow` spawna nova instância
      para a fase de Revisão do Plano.
    Independente do cenário, a decisão e o motivo devem
    ser registrados no arquivo de planejamento para
    rastreabilidade e retomada.

### Harness por Agente

32. **Harness é definido no AGENTS.md** — a criação e
    manutenção do harness são responsabilidade do
    `curador-produto-editor` conforme descrito em
    `docs/workflow-curadoria.md`. Harness é **obrigatório
    na construção** para agentes com harness definido. Na
    **revisão da construção**, o harness só é obrigatório
    se o agente **modificou** algum artefato. Sem
    modificação, o agente não executa o script e registra
    `sem modificações — harness não executado` na seção
    de evidências. Agentes marcados
    `SEM HARNESS A PEDIDO DO HUMANO` não executam harness.
    **Harness não se aplica ao planejamento nem à revisão
    do plano.** Implementado como
    **script único por harness** — sem argumentos, sem
    parâmetro de fase, idempotente.
33. **Agente localiza seu harness antes de executar** —
    ao iniciar uma tarefa na construção ou revisão da
    construção, o agente localiza o Harness no AGENTS.md
    do projeto e verifica se há harness configurado para
    ele. Se a seção contiver `SEM HARNESS A PEDIDO DO
    HUMANO`, segue sem harness. Se a seção não existir ou
    estiver vazia, registra LACUNA e não prossegue até o
    humano definir a política. Se houver comando
    registrado: na construção, executa o script; na
    revisão da construção, executa somente se modificar
    algum artefato.
34. **Evidência de execução do harness** — todo agente
    que possui harness e o executou deve produzir, ao
    final da sua execução, a saída JSON do script como
    evidência. O JSON contém `status`, `findings` e
    `prompt`. A saída é persistida no arquivo de
    planejamento. Se `fail`: o agente lê `findings`, tenta
    resolver e roda o harness novamente. Se `pass`: lê
    `prompt` e executa se houver. Na revisão da
    construção, se não houve modificação, persiste
    `sem modificações — harness não executado` no lugar
    do JSON.
35. **Validação de harness pelo `val-harness`** — ao
    final das fases de **Construção** e **Revisão da
    Construção** (quando houve modificações), `devflow`
    spawna `val-harness`, que cruza a seção
    `## Evidências de Harness — <fase>` do arquivo de
    planejamento com o AGENTS.md do projeto.
    Para cada agente que atuou na fase:
    - Se harness definido e evidência presente → OK.
    - Se harness definido e evidência
      `sem modificações — harness não executado` → OK.
    - Se harness definido e evidência ausente/incompleta
      → FALHA (lista o que falta).
    - Se `SEM HARNESS A PEDIDO DO HUMANO` → OK.
    - Se seção ausente no AGENTS.md → LACUNA.
    Antes de cruzar as evidências, executa somente o comando
    agregador registrado na seção própria do AGENTS.md para
    atualizar `docs/harness-report.md`, sem executar harness
    por agente. Se o registro estiver ausente, reporta LACUNA.
    O `val-harness` **não spawna agentes** — apenas
    reporta. O `devflow` recebe o relatório e decide:
    re-spawnar o agente faltante ou consultar o humano.
36. **Instalação de harness durante execução** — quando um
    agente com `bash: allow` identificar dependência de
    harness faltante, pode executar o script de instalação
    de harness do projeto para avançar com segurança.

> **Resumo da sequência harness:**
> agente localiza comando de harness no AGENTS.md (P33) →
> na construção, executa sempre; na revisão da construção,
> só executa se modificou (P32) →
> se `fail`: resolve findings e re-executa →
> se `pass`: lê prompt e executa se houver →
> persiste saída JSON ou o registro de skip (P34)
> → `val-harness` executa somente o agregador registrado e
> valida em lote ao final da Construção
> e Revisão da Construção, se houve modificações (P35)
> → `devflow` decide ação sobre falhas.

## Fluxo — Diagrama de Sequência

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {
    'actorTextColor': '#000000',
    'signalTextColor': '#000000',
    'labelTextColor': '#000000',
    'noteBkgColor': '#ffffff',
    'noteTextColor': '#000000',
    'activationBorderColor': '#666666',
    'sequenceNumberColor': '#000000'
}}}%%
sequenceDiagram
    actor Humano
    participant devflow as devflow
    participant eng as eng-software
    participant front as front
    participant prod as curador-produto
    participant dba as dba
    participant sec as sec
    participant qa as qa
    participant rev as rev
    participant val as val-harness

    %% ── INÍCIO ──────────────────────────────
    Humano ->> devflow: Nova funcionalidade (requisitos)
    Note right of devflow: Workflow de Escopo<br/>workflow-definicao-escopo.md<br/>Validação + Elicitação
    devflow ->> devflow: Cria arquivo de planejamento<br/>Status: PLANEJAMENTO

    %% ── PLANEJAMENTO ──────────────────────────
    rect rgb(230, 245, 255)
    Note over Humano, rev: PLANEJAMENTO

    devflow ->> eng: Planejar implementação
    Note right of eng: Se tiver dúvidas, formula perguntas,<br/>salva progresso e retorna ao devflow

    eng -->> devflow: Perguntas de escopo (se tiver dúvidas)
    devflow ->> eng: Respostas do humano (mediação)

    eng ->> eng: Elabora plano de código

    eng -->> devflow: Plano persistido no arquivo (resumo curto)

    devflow ->> front: Prototipar telas (se houver UI)
    alt Sem componente visual
        front -->> devflow: Sem UI nesta funcionalidade (resumo curto)
    else Com componente visual
        front ->> front: Gera protótipos (HTML/SVG)
        front -->> devflow: Perguntas sobre aprovação visual
        devflow ->> front: Respostas do humano (mediação)
        front ->> front: Itera até aprovação
        front -->> devflow: Identidade visual aprovada (resumo curto)
    end

    devflow ->> dba: Analisar modelagem de dados
    dba -->> devflow: Modelo persistido no arquivo (resumo curto)

    devflow ->> sec: Analisar requisitos de segurança
    Note right of sec: Recebe plano via arquivo
    sec -->> devflow: Requisitos persistidos no arquivo (resumo curto)

    devflow ->> qa: Planejar testes
    Note right of qa: Recebe plano via arquivo
    qa -->> devflow: Plano de testes persistido (resumo curto)

    devflow ->> devflow: Atualiza Status: REVISÃO DO PLANO

    end

    %% ── REVISÃO DO PLANO ──────────────────────
    rect rgb(255, 245, 230)
    Note over Humano, rev: REVISÃO DO PLANO

    Note right of devflow: Instâncias limpas —<br/>revisam e corrigem

    devflow ->> dba: Revisar modelagem do plano
    dba ->> dba: Revisa, corrige e<br/>registra resumo no arquivo
    dba -->> devflow: Resumo (achado · ação · severidade)

    devflow ->> sec: Revisar segurança do plano
    sec ->> sec: Revisa, corrige e<br/>registra resumo no arquivo
    sec -->> devflow: Resumo (achado · ação · severidade)

    devflow ->> qa: Revisar testabilidade do plano
    qa ->> qa: Revisa, corrige e<br/>registra resumo no arquivo
    qa -->> devflow: Resumo (achado · ação · severidade)

    devflow ->> prod: Revisar documentação planejada (docs/README.md)
    prod ->> prod: Verifica aderência ao docs/README.md
    prod -->> devflow: Resumo (achado · ação · severidade)

    devflow ->> front: Revisar protótipos/planejamento de UI
    front ->> front: Revisa protótipos e<br/>registra resumo no arquivo
    front -->> devflow: Resumo (achado · ação · severidade)

    Note right of devflow: Revisão integrativa
    devflow ->> rev: Revisão integrativa do plano
    rev ->> rev: Verifica consistência entre partes<br/>e aderência ao plano
    rev -->> devflow: Relatório (achados integrativos)

    opt Ajustes necessários (rev + curador-produto)
        devflow ->> eng: Aplicar ajustes (integrativos + documentação)
        eng -->> devflow: Ajustes aplicados (resumo curto)
        opt Ajuste complexo demais para eng-software
            devflow ->> dba: Ajustar modelagem
            dba -->> devflow: Modelo ajustado (resumo curto)
        end
    end

    devflow ->> Humano: Plano revisado. Resubmeter?
    alt Humano: sim
        devflow ->> rev: Resubmete plano
        rev -->> devflow: Feedback
    else Humano: não, seguir
        Note right of devflow: Segue para aprovação
    end

    devflow ->> Humano: Apresenta plano para aprovação
    Humano -->> devflow: Aprovação / ajustes

    devflow ->> devflow: Atualiza Status: CONSTRUÇÃO

    end

    %% ── CONSTRUÇÃO ────────────────────────────
    rect rgb(230, 255, 230)
    Note over Humano, rev: CONSTRUÇÃO

    devflow ->> dba: Criar/atualizar modelo, scripts e migrações
    dba -->> devflow: Artefatos de BD persistidos (resumo curto)

    opt Funcionalidade envolve UI
        devflow ->> front: Implementar telas
        Note right of front: Usa protótipos aprovados<br/>como referência visual
        front -->> devflow: UI implementada (resumo curto)
    end

    devflow ->> eng: Implementar (TDD)
    Note right of eng: Etapa 1 — Testes primeiro<br/>Etapa 2 — Código

    Note right of eng: Etapa 3 — Gate de refatoração
    eng ->> eng: Analisa como acomodar<br/>código novo ao existente

    alt Refatoração não afeta o plano
        eng ->> eng: Aplica refatoração e segue
        eng -->> devflow: Construção concluída (resumo curto)
        devflow ->> devflow: Atualiza Status:<br/>REVISÃO DA CONSTRUÇÃO
    else Refatoração pode mudar o plano
        eng -->> devflow: Perguntas sobre ajustes ao plano
        alt Humano: ajuste mínimo
            eng ->> eng: Atualiza plano no arquivo<br/>(registra motivo e decisão)
            eng -->> devflow: Construção concluída (resumo curto)
            devflow ->> devflow: Atualiza Status:<br/>REVISÃO DA CONSTRUÇÃO
        else Humano: mudança significativa
            eng ->> eng: Registra pausa no arquivo
            eng -->> devflow: Gate disparado —<br/>volta ao planejamento
            devflow ->> devflow: Atualiza Status:<br/>REVISÃO DO PLANO
            Note right of devflow: Spawna nova instância<br/>de eng-software
        else Humano: nada muda
            eng ->> eng: Registra decisão e segue
            eng -->> devflow: Construção concluída (resumo curto)
            devflow ->> devflow: Atualiza Status:<br/>REVISÃO DA CONSTRUÇÃO
        end
    end

    devflow ->> val: Validar evidências da fase
    val -->> devflow: Relatório de harness (resumo curto)

    end

    %% ── REVISÃO DA CONSTRUÇÃO ─────────────────
    rect rgb(255, 245, 230)
    Note over Humano, rev: REVISÃO DA CONSTRUÇÃO

    Note right of devflow: Instâncias limpas —<br/>revisam e corrigem

    devflow ->> dba: Revisar artefatos de BD
    dba ->> dba: Revisa, corrige e<br/>registra resumo no arquivo
    dba -->> devflow: Resumo (achado · ação · severidade)

    devflow ->> sec: Revisar segurança da implementação
    sec ->> sec: Revisa, corrige e<br/>registra resumo no arquivo
    sec -->> devflow: Resumo (achado · ação · severidade)

    devflow ->> qa: Revisar cobertura de testes
    qa ->> qa: Revisa, corrige e<br/>registra resumo no arquivo
    qa -->> devflow: Resumo (achado · ação · severidade)

    devflow ->> prod: Revisar documentação produzida (docs/README.md)
    prod ->> prod: Verifica aderência ao docs/README.md
    prod -->> devflow: Resumo (achado · ação · severidade)

    devflow ->> front: Revisar aderência visual da implementação
    front ->> front: Compara implementação contra<br/>identidade visual aprovada
    front -->> devflow: Resumo (achado · ação · severidade)

    Note right of devflow: Revisão integrativa
    devflow ->> rev: Revisão integrativa da construção
    rev ->> rev: Verifica consistência entre partes<br/>e aderência ao plano
    rev -->> devflow: Relatório (achados integrativos)

    devflow ->> val: Validar evidências da fase
    val -->> devflow: Relatório de harness (resumo curto)

    opt Ajustes necessários (rev + curador-produto)
        devflow ->> eng: Aplicar ajustes (integrativos + documentação)
        eng -->> devflow: Ajustes aplicados (resumo curto)
        opt Ajuste complexo demais para eng-software
            devflow ->> dba: Ajustar artefatos de BD
            dba -->> devflow: Ajustes aplicados (resumo curto)
            devflow ->> sec: Ajustar segurança
            sec -->> devflow: Ajustes aplicados (resumo curto)
            devflow ->> front: Ajustar UI
            front -->> devflow: Ajustes aplicados (resumo curto)
        end
    end

    devflow ->> Humano: Revisão concluída. Resubmeter?
    alt Humano: sim
        devflow ->> rev: Resubmete construção
        rev -->> devflow: Feedback
    else Humano: não, seguir
        Note right of devflow: Segue para testes
    end

    devflow ->> devflow: Atualiza Status: TESTES

    end

    %% ── TESTES ────────────────────────────────
    rect rgb(245, 230, 255)
    Note over Humano, rev: TESTES

    devflow ->> qa: Executar testes automatizados + manuais
    qa -->> devflow: Resultado dos testes (resumo curto)

    opt Testes falharam
        devflow ->> eng: Corrigir com base no feedback
        eng -->> devflow: Correções aplicadas (resumo curto)
        devflow ->> Humano: Ajustes feitos. Re-executar testes?
        alt Humano: sim
            devflow ->> qa: Re-executar testes
            qa -->> devflow: Resultado (resumo curto)
        else Humano: não, seguir
            Note right of devflow: Segue para testes de segurança
        end
    end

    devflow ->> sec: Executar testes de segurança
    sec -->> devflow: Resultado (resumo curto)

    opt Testes de segurança falharam
        devflow ->> eng: Corrigir com base no feedback
        eng -->> devflow: Correções aplicadas (resumo curto)
        devflow ->> Humano: Ajustes feitos. Re-executar testes?
        alt Humano: sim
            devflow ->> sec: Re-executar testes de segurança
            sec -->> devflow: Resultado (resumo curto)
        else Humano: não, seguir
            Note right of devflow: Segue para finalização
        end
    end

    devflow ->> devflow: Atualiza Status: FINALIZAÇÃO

    end

    %% ── FINALIZAÇÃO ───────────────────────────
    rect rgb(255, 255, 230)
    Note over Humano, rev: FINALIZAÇÃO

    devflow ->> prod: Revisão final — verificar artefatos de spec (docs/README.md)
     prod ->> prod: Lê docs/README.md, verifica existência<br/>de cada artefato de spec
    prod ->> prod: Atualiza docs de produto (se lacunas)
    prod -->> devflow: Relatório: lacunas de spec<br/>por domínio (resumo curto)

    loop Revalidação (guarda do humano)
        opt Lacunas em outros domínios
            Note right of devflow: especialistas do curador<br/>eng, dba, sec, qa, front<br/>docs/README.md
            devflow ->> eng: Extrair/criar artefato de spec<br/>do domínio indicado
            eng -->> devflow: Artefatos criados (resumo curto)
        end
        devflow ->> prod: Revalidar completude
        prod -->> devflow: Relatório atualizado (resumo curto)
        alt Tudo OK
            Note right of devflow: Sai do loop
        else Ainda há lacunas
            devflow ->> Humano: Lacunas restantes. Resubmeter?
            alt Humano: sim
                Note right of devflow: Continua loop
            else Humano: não, seguir
                Note right of devflow: Sai do loop
            end
        end
    end

    devflow ->> Humano: Funcionalidade concluída. Excluir plano?
    Humano -->> devflow: Aprovação
    devflow ->> prod: Excluir plano e artefatos auxiliares
    prod -->> devflow: Plano excluído

    end
```

## Notas de Implementação

### Interação agente–humano por plataforma

| Plataforma | Como `devflow` spawna agentes | Comunicação com humano |
|---|---|---|
| **Copilot CLI** | `task(agent_type=...)` ou `/fleet` | Devflow media; subagentes retornam perguntas |
| **OpenCode** | Subagentes | Devflow media. Subagentes retornam perguntas; não precisam de tool `ask`. |

**Ambas as plataformas**: subagentes retornam perguntas ao invés de
consultar o humano diretamente. O `devflow` avalia, reformula se necessário
e apresenta ao humano. Subagentes não precisam de tool `ask` (OpenCode)
nem ser primários (Copilot CLI).

**Exceção**: agentes não mediados (ex: analista no workflow de definição
de escopo) conversam direto com o humano. O `devflow` instrui o humano
a trocar de agente quando necessário.
