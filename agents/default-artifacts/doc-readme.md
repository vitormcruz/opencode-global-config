# Mapa do Produto

Este documento é a fonte de verdade do produto. Define o escopo do que será construído, os artefatos que devem ser produzidos em cada ciclo de desenvolvimento e as regras que governam como esses artefatos são criados e mantidos. É lido por agentes e humanos antes de qualquer ciclo de implementação.

## Definição de Escopo

O analista deve elicitar:
- Regras de Negócio
- Requisitos funcionais e não funcionais
- Critérios de aceitação por exemplos
- Organizar tudo por histórias de usuário
- Critérios de aceitação devem referenciar:
    - Requisitos funcionais, que, por sua vez, referenciam regras de negócio, ou;
    - Requisitos não funcionais.
- Nenhum requisito pode ficar sem critério, e vice-versa
- Toda Regra de Negócio deve ter pelo menos um Requisito Funcional associado
- Nem todo Requisito Funcional precisa necessariamente ter uma Regra de Negócio associada
- Regras de controle de acesso são transversais e devem ser elicitadas como uma matriz separada (`RN-ACL`), não como itens sequenciais da lista de regras de negócio
- Requisitos Não Funcionais associados a uma funcionalidade ficam no arquivo da história e são validados por critérios de aceite daquela história
- Requisitos Não Funcionais gerais (transversais, sem história específica) são:
    - Consolidados em `docs/specs/rnf-gerais.md`
    - Derivados em Critérios de Aceitação no mesmo arquivo, com uma seção para cada RNF
- O humano pode iniciar o workflow imediatamente após elicitar uma história — nesse caso
  a história fica apenas no arquivo de planejamento do devflow e pode ser descartada após o ciclo.
- O humano pode também elicitar múltiplas histórias antecipadamente para iniciar os workflows
  posteriormente, uma por vez — nesse caso o analista salva cada história em `docs/backlog/`
  (um arquivo Markdown por história).

---

## Elementos de Especificação

| Elemento | Formato/Ferramenta | Agente Responsável | Destino |
|----------|-------------------|-------------------|---------|
| Regras de Negócio | Lista Numerada + Matriz ACL | eng-software | docs/specs/regras-negocio.md |
| Critérios de Aceite + Requisitos | Concordion | eng-software | docs/specs/ |
| RNFs Gerais | Concordion | eng-software | docs/specs/rnf-gerais.md |
| Regras de Produto | Tabela | eng-software | nenhum |
| Modelo de Dados | DBML | dba | docs/modelo.dbml |
| Threat Model | Concordion - Markdown | sec | docs/threat-model/ |
| Plano de Testes Manuais | Markdown | qa | nenhum |
| Identidade Visual | Protótipo HTML/SVG | front | plan/ui/ |
| ADR (Arquitetura) | Concordion - Markdown | eng-software | docs/adr/ |
| Arquitetura (Diagrama Gerado) | Mermaid | eng-software | docs/adr/diagrama-c4-l1.md, docs/adr/diagrama-c4-l2.md |

### Regras de Documentação

#### Regras Gerais
- Documentação complementa o código, não o repete
- Doc derivável do código não se armazena — gere sob demanda
- Doc desatualizada é pior que ausência de doc
- Preferir formatos versionáveis (Markdown, Mermaid, DBML)
- Preferir especificações executáveis a documentação passiva — Concordion-Markdown é o formato padrão para regras que podem ser validadas por código

##### Regras de Negócio
- Derivado das histórias de usuário
- Formato de lista numerada, cada uma com a regra descrita claramente
- Cada regra deve ter um identificador único (ex: RN-001) para ser referenciada pelos requisitos funcionais
- Nenhuma Regra de Negócio pode ficar sem Requisito Funcional associado
- Regras de controle de acesso (permissionamento) são separadas das regras sequenciais:
  - Agrupadas em `## Controle de Acesso por Perfil` com identificador único `RN-ACL`
  - Formato: matriz tabular Funcionalidade × Perfil, células ✅/❌
  - Uma única seção `RN-ACL` por arquivo — cobre todas as funcionalidades do módulo
  - Referenciada nos requisitos como `*(RN-ACL)*`, igual a qualquer outra RN

##### Critérios de Aceite + Requisitos
- Cada funcionalidade deve ter um arquivo Concordion separado
- Critérios de aceite devem estar organizados por funcionalidade com base em coesão
- Cada critério de aceite deve referenciar o requisito (funcional ou não funcional) ao qual pertence
- Requisitos funcionais devem referenciar a(s) regra(s) de negócio que os originam (ex: RN-001)
- Nenhum requisito funcional ou não funcional pode ficar sem critério de aceite

##### RNFs Gerais
- Arquivo sempre presente em `docs/specs/rnf-gerais.md`; fica vazio se não houver RNFs transversais
- Formato Concordion-Markdown; cada RNF com identificador (ex: `RNF-G-001`)
- Critérios executáveis implementados em Concordion; estratégia de execução avaliada por RNF

##### Regras de Produto
- Formato tabular: Regra | Descrição | Exceções
- Escopo: decisões de produto que guiam a implementação (comportamentos padrão, limites, validações que o sistema deve impor)
- Descartadas junto com o arquivo de planejamento ao fim do ciclo

##### Modelo de Dados
- Schema versionado em DBML e validado contra o BD real (diff)
- Alterações de schema passam por `dba` antes de `eng-software`

##### Threat Model
- Um arquivo Concordion-Markdown por fluxo sensível (ex: autenticação, autorização por role, logout)
- Estrutura por fluxo: Contexto | Ameaças STRIDE | Mitigações | Asserção executável
- Asserção executável valida que a mitigação está implementada (ex: endpoint protegido, CSRF habilitado)
- Atualizar a cada nova rota autenticada ou dado sensível

##### Plano de Testes Manuais
- Inclui: escopo, abordagem, critérios de entrada/saída, riscos
- Cobre obrigatoriamente:
  - Validação de todos os critérios de aceitação
  - Validação das regras de produto (comportamentos padrão, limites, validações)
  - Fluxos de autenticação e autorização por perfil
  - Testes exploratórios por área funcional
  - Monkey testing — interações aleatórias e imprevisíveis para detectar comportamentos inesperados

##### Identidade Visual
- Protótipo HTML/SVG aprovado pelo humano antes da implementação
- Paleta, tipografia e espaçamentos definidos no protótipo

##### ADR (Arquitetura)
- Um arquivo Concordion-Markdown por decisão arquitetural relevante
- Estrutura: Contexto | Decisão | Consequências | Alternativas consideradas | Asserção executável
- A asserção executável valida que a decisão está implementada (fitness function)
- ADRs nunca são deletados — apenas superseded (novo ADR referencia o anterior)

##### Arquitetura (Diagrama Gerado)
- Gerado pelo eng-software a partir dos ADRs + análise do código (codebase-memory)
- Segue o modelo C4, apenas níveis 1 e 2:
  - L1 (diagrama-c4-l1.md): sistema e seus atores/sistemas externos
  - L2 (diagrama-c4-l2.md): containers internos (backend, frontend, banco, IdP, observabilidade)
- Formato: bloco Mermaid (C4Context para L1, C4Container para L2)
- Regenerar sempre que um ADR for adicionado ou superseded
- Não editar manualmente — é artefato gerado

---

## Estratégias de Indexação de Código

| Ferramenta | Uso | Instalação |
|-----------|-----|-----------|
| codebase-memory | Grafo de conhecimento do código-fonte e docs (.md). Permite que agentes naveguem estrutura, rastreiem chamadas e consultem seções de documentação sem precisar ler arquivo por arquivo. | `npx -y @avelino/codebase-memory-mcp` (via MCP) |
