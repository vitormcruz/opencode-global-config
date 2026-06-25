## Harness por Agente

| Agente | Comando | Descrição | Detalhes |
|--------|---------|-----------|----------|
| eng-software | `harness/eng-software.sh` | Testes, análise estática | [Ver detalhes](#agente-eng-software) |
| dba | `harness/dba.sh` | Validação de schema | [Ver detalhes](#agente-dba) |
| sec | `harness/sec.sh` | OWASP checks, secrets | [Ver detalhes](#agente-sec) |
| qa | `harness/qa.sh` | Cobertura, aceitação | [Ver detalhes](#agente-qa) |
| front | `harness/front.sh` | Linting, a11y | [Ver detalhes](#agente-front) |
| rev | — | SEM HARNESS | [Ver detalhes](#agente-rev) |
| val-harness | — | SEM HARNESS | [Ver detalhes](#agente-val-harness) |
| curador-produto | — | SEM HARNESS | [Ver detalhes](#agente-curador-produto) |

### Detalhes por Agente

#### Agente: eng-software

**Arquivo:** `harness/eng-software.sh`
**Descrição:** Testes, análise estática, cobertura
**O que deve conter:**
- Ferramentas de teste específicas do projeto
- Analisadores estáticos (lint, typecheck)
- Validação de cobertura mínima
- Critérios de harness: [a definir com humano]

#### Agente: dba

**Arquivo:** `harness/dba.sh`
**Descrição:** Validação de schema, migrações
**O que deve conter:**
- Validação de schema contra modelo DBML
- Teste de migrações (up/down)
- Checks de performance de queries
- Critérios de harness: [a definir com humano]

#### Agente: sec

**Arquivo:** `harness/sec.sh`
**Descrição:** OWASP checks, secrets scanning
**O que deve conter:**
- Escaneamento de secrets
- OWASP dependency check
- SAST (análise estática de segurança)
- Critérios de harness: [a definir com humano]

#### Agente: qa

**Arquivo:** `harness/qa.sh`
**Descrição:** Cobertura de testes, aceitação
**O que deve conter:**
- Validação de critérios de aceite
- Verificação de cobertura de testes
- Testes exploratórios automatizados
- Critérios de harness: [a definir com humano]

#### Agente: front

**Arquivo:** `harness/front.sh`
**Descrição:** Linting, acessibilidade
**O que deve conter:**
- Lint de CSS/HTML/JS
- Validação de acessibilidade (a11y)
- Lighthouse checks
- Critérios de harness: [a definir com humano]

#### Agente: rev

**Status:** `SEM HARNESS A PEDIDO DO HUMANO`
**Justificativa:** Revisor não executa harness, apenas revisa

#### Agente: val-harness

**Status:** `SEM HARNESS A PEDIDO DO HUMANO`
**Justificativa:** Validador de harness não precisa de harness próprio

#### Agente: curador-produto

**Status:** `SEM HARNESS A PEDIDO DO HUMANO`
**Justificativa:** Curador não executa harness, apenas orquestra
