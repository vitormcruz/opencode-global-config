## Harness por Agente

| Agente | Comando de Execução | Descrição |
|--------|--------------------|-----------|
| eng-software | `harness/eng-software.sh` | Testes backend |
| dba | `harness/dba.sh` | Validação de schema e modelo de dados |
| sec | `harness/sec.sh` | Segurança — secrets, dependências, OWASP |
| qa | `harness/qa.sh` | Cobertura de testes e acessibilidade |
| front | `harness/front.sh` | Testes, lint, build e acessibilidade do frontend |
| rev | `harness/rev.sh` | Revisão de documentação e consistência cross-artefato |
| analista | (sem harness) | SEM HARNESS |
| val-harness | (sem harness) | SEM HARNESS |
| curador-produto | (sem harness) | SEM HARNESS |

> Scripts shell. Interface: saída JSON `{ status, findings[], prompt }`, exit 0 = pass, exit 1 = fail.

> **PROIBIDO/NAO PODE:** bypassar, comentar, remover ou condicionar qualquer verificação do harness. Ferramenta ausente NAO justifica remoção — o correto é reportar severidade `melhoria` com instrução de instalação. Todo finding `bloqueante` DEVE ser resolvido antes de avançar no workflow. O harness é inegociável.

### eng-software

**Arquivo:** `harness/eng-software.sh`
**Descrição:** Testes backend
**O que deve conter:**
- Comandos de teste específicos do projeto (unitários + integração)
- Critérios de harness: [a definir com humano]

### dba

**Arquivo:** `harness/dba.sh`
**Descrição:** Validação de schema e modelo de dados
**O que deve conter:**
- Validação de existência de documentos de especificação
- Validação de sintaxe de modelo de dados (DBML ou equivalente)
- Prompt instrucional: verificar se o modelo reflete o schema atual e se alterações passaram pela aprovação do dba
- Critérios de harness: [a definir com humano]

### sec

**Arquivo:** `harness/sec.sh`
**Descrição:** Segurança — secrets, dependências, OWASP
**O que deve conter:**
- Secrets scan no repositório
- Auditoria de dependências
- Verificação de vulnerabilidades conhecidas
- Prompt instrucional: revisar OWASP Top 10 aplicável ao projeto
- Critérios de harness: [a definir com humano]

### qa

**Arquivo:** `harness/qa.sh`
**Descrição:** Cobertura de testes e acessibilidade
**O que deve conter:**
- Relatório de cobertura de testes
- Verificação de acessibilidade
- Prompt instrucional: revisar cobertura dos critérios de aceitação e resultado dos testes manuais
- Critérios de harness: [a definir com humano]

### front

**Arquivo:** `harness/front.sh`
**Descrição:** Testes, lint, build e acessibilidade do frontend
**O que deve conter:**
- Testes frontend
- Lint
- Build
- Verificação de acessibilidade
- Prompt instrucional: verificar aderência à identidade visual aprovada
- Critérios de harness: [a definir com humano]

### rev

**Arquivo:** `harness/rev.sh`
**Descrição:** Revisão de documentação e consistência cross-artefato
**O que deve conter:**
- Validação de sintaxe de documentação (markdownlint ou equivalente)
- Prompt instrucional: verificar consistência entre artefatos (BD, código, segurança, testes, docs) e aderência ao plano aprovado
- Critérios de harness: [a definir com humano]

### analista

**Status:** `SEM HARNESS`

### val-harness

**Status:** `SEM HARNESS`

### curador-produto

**Status:** `SEM HARNESS`
