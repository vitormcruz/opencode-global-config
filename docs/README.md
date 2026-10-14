# Especificação do Produto

Este documento é a fonte de verdade do produto. Define o escopo do que será
construído, os artefatos que devem ser produzidos em cada ciclo de
desenvolvimento e as regras que governam como esses artefatos são criados e
mantidos. É lido por agentes e humanos antes de qualquer ciclo de
implementação.

## Definição de Escopo

O analista deve elicitar, para cada história de usuário:
- Regras de Negócio (comportamentos e restrições que o pacote de
  configuração deve impor)
- Requisitos funcionais e não funcionais
- Critérios de aceitação por exemplos
- Organizar tudo por histórias de usuário
- Critérios de aceitação devem referenciar:
    - Requisitos funcionais, que, por sua vez, referenciam regras de
      negócio, ou;
    - Requisitos não funcionais.
- Nenhum requisito pode ficar sem critério, e vice-versa
- Toda Regra de Negócio deve ter pelo menos um Requisito Funcional
  associado
- Nem todo Requisito Funcional precisa necessariamente ter uma Regra de
  Negócio associada
- Requisitos Não Funcionais associados a uma história ficam no arquivo
  da história e são validados por critérios de aceite daquela história
- Requisitos Não Funcionais gerais (transversais, sem história
  específica) são:
    - Consolidados em `docs/specs/rnf-gerais.md`
    - Derivados em Critérios de Aceitação no mesmo arquivo, com uma
      seção para cada RNF
- O humano pode iniciar o workflow imediatamente após elicitar uma
  história — nesse caso a história fica apenas no arquivo de planejamento
  do devflow e pode ser descartada após o ciclo.
- O humano pode também elicitar múltiplas histórias antecipadamente para
  iniciar os workflows posteriormente, uma por vez — nesse caso o
  analista salva cada história em `docs/backlog/` (um arquivo Markdown
  por história).

---

## Elementos de Especificação

| Elemento | Formato/Ferramenta | Agente Responsável | Destino |
|----------|-------------------|-------------------|---------|
| Regras de Negócio | Lista Numerada | eng-software | docs/specs/regras-negocio.md |
| Critérios de Aceite + Requisitos | Concordion-Markdown — spec executável (Concordion/Groovy) | eng-software | docs/specs/ |
| RNFs Gerais | Concordion-Markdown — spec executável (Concordion/Groovy) | eng-software | docs/specs/rnf-gerais.md |
| Regras de Produto | Tabela | eng-software | nenhum |
| ADR (Arquitetura) | Concordion-Markdown (asserção executável obrigatória) | eng-software | docs/adr/ |
| Arquitetura (Diagrama Gerado) | Mermaid — C4 L1/L2/L3 gerado dos ADRs | eng-software | docs/adr/diagrama-c4-l1.md, docs/adr/diagrama-c4-l2.md, docs/adr/diagrama-c4-l3.md |
| UPSTREAM.md (skills externas) | Markdown padronizado | eng-software | harness-conf/skills/<skill>/UPSTREAM.md |
| README — Dependências | Markdown (seção do README) | eng-software | README.md |
| Workflows de Agentes de IA | Markdown | eng-software | docs/workflow-*.md |

### Regras de Documentação

#### Regras Gerais
- Documentação complementa o código, não o repete
- Doc derivável do código não se armazena — gere sob demanda
- Doc desatualizada é pior que ausência de doc
- Preferir formatos versionáveis (Markdown)
- Preferir especificações executáveis a documentação passiva

##### Regras de Negócio
- Derivado das histórias de usuário
- Formato de lista numerada, cada uma com a regra descrita claramente
- Cada regra deve ter um identificador único (ex: RN-001) para ser
  referenciada pelos requisitos funcionais
- Nenhuma Regra de Negócio pode ficar sem Requisito Funcional associado

##### Critérios de Aceite + Requisitos
- Cada funcionalidade deve ter arquivo de spec separado
- Critérios de aceite organizados por funcionalidade com base em coesão
- Cada critério de aceite deve referenciar o requisito (funcional ou não
  funcional) ao qual pertence
- Requisitos funcionais devem referenciar a(s) regra(s) de negócio que
  os originam (ex: RN-001)
- Nenhum requisito funcional ou não funcional pode ficar sem critério
  de aceite
- Todo exemplo da spec referencia a origem (requisito/regra) que o
  motivou
- Specs executadas pelo Concordion (fixtures Groovy); o texto é a spec —
  editar o texto muda o veredito do teste (link texto↔teste)
- Especificação executável É UM TESTE: toda spec executável pertence
  à suíte da sua especialidade e roda dentro dela (ex.: spec de
  segurança roda na suíte `testes-produto/seguranca`)

##### RNFs Gerais
- Arquivo sempre presente em `docs/specs/rnf-gerais.md`; fica vazio se
  não houver RNFs transversais
- Cada RNF com identificador (ex: `RNF-G-001`)
- Critérios executáveis; estratégia de execução avaliada por RNF

##### Regras de Produto
- Formato tabular: Regra | Descrição | Exceções
- Escopo: decisões que guiam a implementação (comportamentos padrão,
  limites, validações que o pacote deve impor)
- Descartadas junto com o arquivo de planejamento ao fim do ciclo

##### ADR (Arquitetura)
- Um arquivo Concordion-Markdown por decisão relevante em `docs/adr/`,
  numeração sequencial (padrão já existente no repo)
- Estrutura: Contexto | Decisão | Consequências | Alternativas
  consideradas | Asserção executável
- A asserção executável (fitness function) é OBRIGATÓRIA em todo ADR
  novo: valida que a decisão está implementada
- Os ADRs legados (`docs/adr/0001`–`0006`) foram retrofitados com fixtures
  Concordion e a seção "Asserções executáveis"
- Os ADRs novos (`docs/adr/0007`–`0009`) seguem a mesma convenção
- ADRs nunca são deletados — apenas superseded (novo ADR referencia o
  anterior)

##### Arquitetura (Diagrama Gerado)
- Gerado pelo eng-software a partir dos ADRs + análise do código
  (codebase-memory)
- Segue o modelo C4, níveis 1, 2 e 3:
  - L1 (diagrama-c4-l1.md): sistema e seus atores/sistemas externos
  - L2 (diagrama-c4-l2.md): containers internos (scripts, pacote
    Python, harness-conf, destinos sincronizados)
  - L3 (diagrama-c4-l3.md): componentes internos dos containers
- Gate de julgamento do L3: o diagrama não cobre todo o código; o
  eng-software inclui apenas as partes mais importantes ou
  complexas; componentes iguais e padronizados, repetidos, não
  entram. O critério de seleção é do eng-software na geração
- Formato: bloco Mermaid (C4Context para L1, C4Container para L2,
  C4Component para L3)
- Regenerar sempre que um ADR for adicionado ou superseded
- Não editar manualmente — é artefato gerado

##### Workflows de Agentes de IA
- Os workflows documentam os papéis dos agentes, a sequência de trabalho,
  os handoffs, os gates e os contratos entre fases.
- São especificações documentais, não especificações executáveis. Não usam
  Concordion e não pertencem às suítes `testes-produto`.
- O `eng-software` mantém os workflows deste produto. Antes de criar ou
  revisar um workflow, carrega `writing-for-agents`.
- Toda alteração em `harness-conf/agents/` deve ser refletida nos workflows
  relacionados.
- Toda alteração em `docs/workflow-*.md` deve ser refletida nos agentes
  relacionados.
- A consistência entre agentes e workflows deve ser verificada pelos testes
  estruturais do repositório.

##### UPSTREAM.md (skills externas)
- Regra canônica na seção "Upstream de Skills Externas" do `AGENTS.md`;
  este documento referencia, não duplica
- Presente em toda skill baseada em repositório externo

##### README — Dependências
- Regra canônica na seção "README" do `AGENTS.md`; este documento
  referencia, não duplica
- Atualizada sempre que bootstrap, scripts, skills ou requisitos de
  instalação mudarem

---

## Testes por Especialidade

A especificação das suítes fica no arquivo independente
[Testes por Especialidade](testes-por-especialidade.md). Este README
apenas referencia o arquivo e não reproduz seus critérios, ferramentas
ou scripts.
