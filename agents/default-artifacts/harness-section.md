## Harness por Agente

| Agente | Comando de Execução | Descrição |
|--------|--------------------|-----------|
| eng-software | `harness/eng-software` | Testes backend |
| dba | `harness/dba` | Validação de schema e modelo de dados |
| sec | `harness/sec` | Segurança — secrets, dependências, OWASP |
| qa | `harness/qa` | Cobertura de testes e acessibilidade |
| front | `harness/front` | Testes, lint, build e acessibilidade do frontend |
| rev | (sem harness) | SEM HARNESS A PEDIDO DO HUMANO |
| analista | (sem harness) | SEM HARNESS A PEDIDO DO HUMANO |
| curador-produto | (sem harness) | SEM HARNESS A PEDIDO DO HUMANO |

> Ferramentas do projeto. Interface: saída JSON `{ status, findings[], prompt }`;
> exit 0 = pass, exit 1 = fail.
> Critérios, orçamento e ferramentas saem da entrevista do
> editor. O estado de fingerprint/cache fica em
> `harness/target/` e não é versionado. A página de métricas
> gerada pelo coletor aprovado fica em
> `docs/harness-report/harness-report.md`.

## Agregador de Harness

| Comando | Destino |
|---------|---------|
| `harness/agregar` | `docs/harness-report/harness-report.md` |

> O comando é executado sem argumentos e pode ser substituído
> pelo comando aprovado pelo humano durante a entrevista.

> O índice `docs/harness-report/harness-report.md` é o único MD
> na raiz de `docs/harness-report/`. Cópias ficam em
> `docs/harness-report/<ferramenta>/`. Regeneração substitui a
> subpasta. Origem ausente → o MD declara ausente. Links só para
> a cópia; nunca para `target/` nem path de build. O MD resume
> dados estruturados da ferramenta e não inventa métrica.

> **PROIBIDO/NAO PODE:** bypassar, comentar, remover ou condicionar
> qualquer verificação do harness. Ferramenta ausente NAO justifica remoção —
> o correto é reportar severidade `melhoria` com instrução de instalação.
> Todo finding `bloqueante` DEVE ser resolvido antes de avançar no workflow.
> O harness é inegociável.

### eng-software

**Arquivo:** `harness/eng-software`
**Descrição:** Testes backend
**O que deve conter:**
- Comandos de teste específicos do projeto (unitários + integração)
- Critérios, orçamento e ferramentas: definidos na entrevista do editor

### dba

**Arquivo:** `harness/dba`
**Descrição:** Validação de schema e modelo de dados
**O que deve conter:**
- Validação de existência de documentos de especificação
- Validação de sintaxe de modelo de dados (DBML ou equivalente)
- Prompt instrucional: verificar se o modelo reflete o schema atual e se alterações passaram pela aprovação do dba
- Critérios, orçamento e ferramentas: definidos na entrevista do editor

### sec

**Arquivo:** `harness/sec`
**Descrição:** Segurança — secrets, dependências, OWASP
**O que deve conter:**
- Secrets scan no repositório
- Auditoria de dependências
- Verificação de vulnerabilidades conhecidas
- Prompt instrucional: revisar OWASP Top 10 aplicável ao projeto
- Critérios, orçamento e ferramentas: definidos na entrevista do editor

### qa

**Arquivo:** `harness/qa`
**Descrição:** Cobertura de testes e acessibilidade
**O que deve conter:**
- Relatório de cobertura de testes
- Verificação de acessibilidade
- Prompt instrucional: revisar cobertura dos critérios de aceitação e resultado dos testes manuais
- Critérios, orçamento e ferramentas: definidos na entrevista do editor

### front

**Arquivo:** `harness/front`
**Descrição:** Testes, lint, build e acessibilidade do frontend
**O que deve conter:**
- Testes frontend
- Lint
- Build
- Verificação de acessibilidade
- Prompt instrucional: verificar aderência à identidade visual aprovada
- Critérios, orçamento e ferramentas: definidos na entrevista do editor

### analista

**Status:** `SEM HARNESS A PEDIDO DO HUMANO`

### curador-produto

**Status:** `SEM HARNESS A PEDIDO DO HUMANO`
