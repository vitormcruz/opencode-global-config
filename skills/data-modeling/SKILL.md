---
name: data-modeling
description: >
  Guia de modelagem de dados: schema, normalização, tipos, constraints,
  migrações seguras, indexação e zero-downtime. Use quando: projetar ou
  alterar schema de banco de dados, criar ou revisar migrations, modelar
  entidades e relacionamentos, definir constraints e índices, avaliar
  normalização/desnormalização, planejar migração com zero-downtime,
  revisar artefatos de BD (DBML, SQL, migration files). Triggers:
  "modelagem", "modelagem de dados", "data modeling", "schema", "schema
  de dados", "migration", "migração", "migrate", "normalização",
  "forma normal", "1NF", "2NF", "3NF", "BCNF", "índice", "index",
  "FK", "foreign key", "chave estrangeira", "constraint", "CHECK",
  "NOT NULL", "UNIQUE", "zero-downtime", "lock", "deadlock",
  "DDL", "ALTER TABLE", "CREATE TABLE", "DBML", "tipo de dado",
  "enum", "serial", "UUID", "bigserial", "particionamento",
  "sharding", "replicação", "rollback de migration",
  "reversível", "backward-compatible".
---

# Modelagem de Dados

Guia para projetar, evoluir e revisar schemas de banco de dados
relacional. Carregar **antes** de criar ou alterar artefatos de BD.

## Relação com outras skills

| Skill | Papel |
|---|---|
| `data-modeling` | Como modelar e evoluir o schema |
| `api-and-interface-design` | Contratos públicos que o schema sustenta |
| `security-and-hardening` | Dados sensíveis, criptografia, PII |
| `clean-code` | Nomes e organização do código de migration |
| `test-driven-development` | Testes de migration e integridade |

## Princípios

1. **Schema é contrato** — toda alteração de schema é uma mudança de
   contrato entre a aplicação e o banco. Trate com a mesma disciplina
   de uma API pública.
2. **Reversibilidade obrigatória** — toda migration deve ter rollback
   ou plano de reversão documentado. Migration irreversível exige
   aprovação explícita do humano.
3. **Backward-compatible primeiro** — alterações aditivas (nova coluna
   nullable, nova tabela) antes de breaking changes. Breaking changes
   em múltiplas etapas (expand → migrate → contract).
4. **Constraints são documentação executável** — NOT NULL, UNIQUE,
   CHECK e FK expressam regras de negócio no schema, não apenas na
   aplicação.
5. **Nomes estáveis** — colunas e tabelas são renomeadas com custo
   alto. Escolha nomes claros desde o início; evite abreviações
   obscuras.

## Modelagem Conceitual e Lógica

### Entidades e Relacionamentos

- Identifique entidades a partir dos substantivos do domínio.
- Relacionamentos: 1:1, 1:N, N:M. N:M sempre gera tabela associativa.
- Cardinalidade mínima e máxima explícitas (opcional vs obrigatório).
- Entidades fracas dependem de chave da entidade forte — use chave
  composta ou FK NOT NULL.

### Normalização

| Forma | Regra | Quando desnormalizar |
|-------|-------|---------------------|
| 1NF | Valores atômicos, sem grupos repetidos | — |
| 2NF | Sem dependência parcial de chave composta | Tabelas de cache materializado |
| 3NF | Sem dependência transitiva | Leitura intensiva sem JOIN aceitável |
| BCNF | Toda dependência funcional tem superchave como determinante | Raro desnormalizar |

Desnormalização é decisão consciente: documente o motivo, a
consulta beneficiada e o custo de escrita adicional.

### Chaves

- **PK**: prefira UUID ou bigserial. Evite PK natural mutável.
- **FK**: sempre NOT NULL quando o relacionamento é obrigatório.
  Use ON DELETE apropriado (CASCADE, SET NULL, RESTRICT).
- **Chave natural**: adicione UNIQUE constraint quando existir
  (ex: email, CPF). Não use como PK se for mutável.

## Tipos e Constraints

### Escolha de tipos

| Categoria | Prefira | Evite |
|-----------|---------|-------|
| Texto curto | `VARCHAR(n)` com limite real | `TEXT` sem limite |
| Texto longo | `TEXT` | `VARCHAR(MAX)` sem necessidade |
| Inteiro | `INTEGER` ou `BIGINT` conforme escala | `SMALLINT` sem necessidade |
| Decimal | `NUMERIC(p,s)` para dinheiro | `FLOAT`/`DOUBLE` para valores monetários |
| Booleano | `BOOLEAN` | `CHAR(1)` ou `INT` |
| Data/hora | `TIMESTAMPTZ` (com fuso) | `TIMESTAMP` sem fuso |
| Enum | Tabela de referência com FK | `ENUM` nativo (rígido para alterar) |
| JSON | `JSONB` (PostgreSQL) para dados semi-estruturados | `JSON` sem índice |
| Identificador | `UUID` ou `BIGSERIAL` | `INT` com autoincremento em sistemas distribuídos |

### Constraints essenciais

- **NOT NULL** em toda coluna que não aceita ausência. Prefira
  NOT NULL + DEFAULT a nullable.
- **CHECK** para regras de domínio simples (ex: `quantidade >= 0`,
  `status IN ('ativo','inativo')`).
- **UNIQUE** para invariantes de unicidade do negócio.
- **FK** para integridade referencial. Sem FK órfã.

## Migrações Seguras

### Padrão Expand-Migrate-Contract

Para alterações breaking (renomear coluna, mudar tipo, remover coluna):

1. **Expand** — adicione a nova coluna/tabela (backward-compatible).
2. **Migrate** — copie dados, dual-write na aplicação.
3. **Contract** — remova a coluna antiga após validação.

Cada etapa é uma migration separada, deployável independentemente.

### Regras de migration

- **Uma alteração por migration** — não misture DDL de tabelas
  diferentes sem motivo.
- **Idempotente quando possível** — `IF NOT EXISTS`, `IF EXISTS`.
- **Rollback testado** — execute o rollback em ambiente de teste
  antes de aplicar em produção.
- **Sem dados em produção sem backup** — migration que altera dados
  exige backup prévio ou dry-run.
- **Ordem de aplicação** — migrations numeradas sequencialmente
  (timestamp ou versão). Nunca aplique fora de ordem.

### Operações com lock

| Operação | Lock | Risco | Alternativa |
|----------|------|-------|-------------|
| `ADD COLUMN` (com DEFAULT) | `ACCESS EXCLUSIVE` breve | Baixo em PG 11+ | — |
| `ADD COLUMN` (sem DEFAULT, NOT NULL) | `ACCESS EXCLUSIVE` longo | Alto, tabela grande | nullable, backfill, NOT NULL |
| `DROP COLUMN` | `ACCESS EXCLUSIVE` | Médio | Marcar deprecated, remover depois |
| `RENAME COLUMN` | `ACCESS EXCLUSIVE` breve | Baixo no BD, alto na app | Dual-column durante transição |
| `CREATE INDEX` | `SHARE` (bloqueia escrita) | Alto em produção | `CREATE INDEX CONCURRENTLY` |
| `ALTER COLUMN TYPE` | `ACCESS EXCLUSIVE` longo | Alto | Nova coluna + migrate + contract |

### Zero-downtime

- Use `CREATE INDEX CONCURRENTLY` (PostgreSQL) para índices em
  produção.
- Backfill de dados em lotes (batch), com pausa entre lotes para
  não saturar o BD.
- Dual-write: aplicação escreve nas duas colunas durante transição.
- Feature flags para ativar novo schema gradualmente.

## Indexação

### Quando indexar

- Colunas em WHERE, JOIN, ORDER BY frequentes.
- FK (para acelerar JOIN e ON DELETE CASCADE).
- Colunas com alta seletividade (poucos valores repetidos).

### Quando não indexar

- Tabelas pequenas (< 1000 linhas) — sequential scan é mais rápido.
- Colunas com baixa seletividade (ex: booleano em tabela uniforme).
- Colunas com escrita frequente e leitura rara — custo de manutenção.

### Tipos de índice

| Tipo | Uso |
|------|-----|
| B-tree (default) | Igualdade e range |
| Hash | Apenas igualdade |
| GIN | JSONB, full-text, arrays |
| GiST | Geométrico, range types |
| BRIN | Dados ordenados naturalmente (timestamp) |
| Partial (`WHERE`) | Subconjunto frequente da tabela |
| Composite | Consultas com múltiplas colunas fixas |

## Checklist de Revisão de Modelo

Use este checklist ao revisar artefatos de modelagem (DBML, SQL,
migration files):

### Schema

- [ ] Toda tabela tem PK definida
- [ ] FKs com ON DELETE apropriado (não CASCADE por padrão)
- [ ] Colunas NOT NULL onde ausência não faz sentido
- [ ] Constraints CHECK para regras de domínio simples
- [ ] UNIQUE em chaves naturais do negócio
- [ ] Nomes de tabelas no plural, colunas no singular (ou convenção
      do projeto)
- [ ] Sem colunas órfãs (sem uso na aplicação)
- [ ] Tipos adequados (ver tabela de tipos acima)
- [ ] Sem `TEXT` sem limite onde `VARCHAR(n)` basta
- [ ] Timestamps com fuso (`TIMESTAMPTZ`)

### Migration

- [ ] Migration é reversível (tem rollback ou plano documentado)
- [ ] Backward-compatible (não quebra deploy anterior)
- [ ] Uma alteração lógica por migration
- [ ] Sem operação com lock longo em tabela grande sem alternativa
- [ ] `CREATE INDEX CONCURRENTLY` para índices em produção
- [ ] Backfill planejado para dados existentes
- [ ] Rollback testado em ambiente de teste
- [ ] Sem dados hardcoded de seed em migration de schema

### Performance

- [ ] Índices em colunas de WHERE/JOIN/ORDER BY frequentes
- [ ] FKs indexadas (para JOIN e CASCADE)
- [ ] Sem índice redundante (prefixo de índice composto)
- [ ] Particionamento avaliado para tabelas > 10M linhas
- [ ] Consultas N+1 identificadas e resolvidas no nível do schema
      (JOIN, lateral, materialized view)

### Segurança

- [ ] Dados sensíveis (PII) identificados e com proteção
      (criptografia, máscara, coluna separada)
- [ ] Sem senha ou segredo em coluna de texto plano
- [ ] Auditoria (created_at, updated_at, created_by) onde aplicável

## Ferramentas e Formatos

| Ferramenta | Uso |
|-----------|-----|
| DBML | Modelagem visual versionável |
| pg-schema-dbml | Extrair DBML do schema PostgreSQL real |
| RosettaDB / diff | Comparar DBML com schema real |
| Flyway / Alembic / golang-migrate | Frameworks de migration |
| dbml2sql | Gerar DDL a partir de DBML |

## Red Flags

- Migration sem rollback
- `DROP COLUMN` sem período de depreciação
- `ALTER COLUMN TYPE` em tabela grande sem plano de migração
- FK sem índice na coluna referenciada
- `SELECT *` em código de aplicação (quebra com nova coluna)
- Tabela sem PK
- Coluna nullable sem motivo documentado
- Enum nativo do BD (rígido para adicionar valores)
- Índice em coluna booleana com distribuição uniforme
- Migration que mistura DDL e DML sem motivo
