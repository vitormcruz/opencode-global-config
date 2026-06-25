# Documentação do Produto

## Definição de Escopo

O analista deve elicitar:
- Requisitos funcionais e não funcionais
- Critérios de aceitação por exemplos
- Organizados por histórias de usuário
- Critérios devem referenciar requisitos funcionais
- Nenhum requisito pode ficar sem critério
- **Skill recomendada:** `grill-me` (entrevista estruturada com humano)

## Elementos de Especificação

| Elemento | Formato/Ferramenta | Agente Responsável | Destino |
|----------|-------------------|-------------------|---------|
| Critérios de Aceite + Requisitos | Concordion | eng-software | docs/specs/ |
| Regras de Produto | Tabela | eng-software | nenhum |
| Modelo de Dados | DBML | dba | docs/modelo.dbml |
| Threat Model | Markdown | sec | docs/threat-model.md |
| Plano de Testes | Markdown | qa | nenhum |
| Identidade Visual | Protótipo HTML/SVG | front | plan/ui/ |
| ADR (Arquitetura) | Markdown | eng-software | docs/adr/ |

### Regras Gerais

- Documentação complementa o código, não o repete
- Doc derivável do código não se armazena — gere sob demanda
- Doc desatualizada é pior que ausência de doc
- Preferir formatos versionáveis (Markdown, Mermaid, DBML)

##### Critérios de Aceite + Requisitos

Os critérios de aceite devem estar organizados por Funcionalidade
levando-se em conta a coesão. Cada funcionalidade deve ter um arquivo
Concordion separado. Cenários devem ser expressos em linguagem natural
e executáveis.

##### Regras de Produto

Regras de negócio devem ser documentadas em tabela com: ID da regra,
descrição, origem (requisito), e agente responsável pela verificação.

##### Modelo de Dados

Schema de banco deve ser versionado em DBML. DBA verifica consistência
entre modelo e schema real via diff. Convenções de nomenclatura SQL
seguem padrão do projeto (lowercase_com_snake_case, nomes no singular
para tabelas e colunas).

##### Threat Model

Modelo de ameaças segue STRIDE. Cadastro e pagamento são áreas de
elevada atenção. OWASP Top 10 deve ser verificado.

##### Plano de Testes

Plano define: estratégia de testes, ambientes, tipos de teste (unit,
integração, aceitação), critérios de entrada/saída, e
responsabilidades por agente.

##### Identidade Visual

Protótipos devem ser validados pelo humano antes de implementação.
Design system baseado em shadcn/ui (preset new-york) com Tailwind
CSS 4.

##### ADR (Arquitetura)

ADR registra decisões arquiteturais significativas. Formato: contexto,
decisão, consequências, status
(proposed/accepted/deprecated/superseded).

## Estratégias de Indexação de Código

- codebase-memory
