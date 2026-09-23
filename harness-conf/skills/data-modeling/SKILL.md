---
name: data-modeling
description: >
  Use ao projetar ou alterar schema de banco, criar ou revisar migrations,
  modelar entidades e relacionamentos, definir constraints e índices,
  avaliar normalização/desnormalização ou planejar migração com
  zero-downtime. Revisa artefatos de BD (DBML, SQL, migration files).
  Triggers: "modelagem", "modelagem de dados", "data modeling", "schema", "schema
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

Guia para projetar, evoluir e revisar schema de banco relacional. Carregue **antes** de criar ou
alterar artefato de BD.

## Princípios

1. **Schema é contrato:** toda alteração de schema muda o contrato entre aplicação e banco.
   Trate como API pública.
2. **Reversibilidade obrigatória:** toda migration tem rollback ou plano de reversão documentado.
   Migration irreversível exige aprovação explícita do humano.
3. **Backward-compatible primeiro:** alteração aditiva (coluna nullable nova, tabela nova) antes
   de breaking change. Breaking change em múltiplas etapas (expand → migrate → contract).
4. **Constraint é documentação executável:** NOT NULL, UNIQUE, CHECK e FK expressam regra de
   negócio no schema, não só na aplicação.
5. **Nomes estáveis:** renomear coluna e tabela custa caro. Escolha nome claro desde o início;
   evite abreviação obscura.

## Modelagem Conceitual e Lógica

### Entidades e Relacionamentos

- Identifique entidades a partir dos substantivos do domínio.
- Relacionamentos: 1:1, 1:N, N:M. N:M sempre gera tabela associativa.
- Cardinalidade mínima e máxima explícitas (opcional vs obrigatório).
- Entidade fraca depende de chave da entidade forte: chave composta ou FK NOT NULL.

### Normalização

| Forma | Regra | Quando desnormalizar |
|---|---|---|
| 1NF | Valores atômicos, sem grupo repetido | — |
| 2NF | Sem dependência parcial de chave composta | Tabela de cache materializado |
| 3NF | Sem dependência transitiva | Leitura intensiva sem JOIN aceitável |
| BCNF | Toda dependência funcional tem superchave como determinante | Raro desnormalizar |

Desnormalização é decisão consciente: documente o motivo, a consulta beneficiada e o custo de
escrita adicional.

### Chaves

- **PK:** prefira UUID ou bigserial. Evite PK natural mutável.
- **FK:** NOT NULL quando o relacionamento é obrigatório. ON DELETE apropriado (CASCADE,
  SET NULL, RESTRICT).
- **Chave natural:** UNIQUE constraint quando existir (ex.: email, CPF). Não use como PK se for
  mutável.

## Tipos e Constraints

### Escolha de tipos

| Categoria | Prefira | Evite |
|---|---|---|
| Texto curto | `VARCHAR(n)` com limite real | `TEXT` sem limite |
| Texto longo | `TEXT` | `VARCHAR(MAX)` sem necessidade |
| Inteiro | `INTEGER` ou `BIGINT` conforme escala | `SMALLINT` sem necessidade |
| Decimal | `NUMERIC(p,s)` para dinheiro | `FLOAT`/`DOUBLE` para valor monetário |
| Booleano | `BOOLEAN` | `CHAR(1)` ou `INT` |
| Data/hora | `TIMESTAMPTZ` (com fuso) | `TIMESTAMP` sem fuso |
| Enum | Tabela de referência com FK | `ENUM` nativo (rígido para alterar) |
| JSON | `JSONB` (PostgreSQL) para dado semi-estruturado | `JSON` sem índice |
| Identificador | `UUID` ou `BIGSERIAL` | `INT` autoincremento em sistema distribuído |

### Constraints essenciais

- **NOT NULL** em toda coluna que não aceita ausência. Prefira NOT NULL + DEFAULT a nullable.
- **CHECK** para regra de domínio simples (ex.: `quantidade >= 0`, `status IN ('ativo','inativo')`).
- **UNIQUE** para invariante de unicidade do negócio.
- **FK** para integridade referencial. Sem FK órfã.

## Migrações Seguras

### Padrão Expand-Migrate-Contract

Para alteração breaking (renomear coluna, mudar tipo, remover coluna):

1. **Expand:** adicione coluna/tabela nova (backward-compatible).
2. **Migrate:** copie dados, dual-write na aplicação.
3. **Contract:** remova a coluna antiga após validação.

Cada etapa é uma migration separada, deployável independentemente.

### Regras de migration

- **Uma alteração por migration:** não misture DDL de tabelas diferentes sem motivo.
- **Idempotente quando possível:** `IF NOT EXISTS`, `IF EXISTS`.
- **Rollback testado:** execute o rollback em ambiente de teste antes de aplicar em produção.
- **Dado em produção exige backup prévio** ou dry-run.
- **Ordem de aplicação:** numeração sequencial (timestamp ou versão). Nunca aplique fora de ordem.

### Operações com lock

| Operação | Lock | Risco | Alternativa |
|---|---|---|---|
| `ADD COLUMN` (com DEFAULT) | `ACCESS EXCLUSIVE` breve | Baixo em PG 11+ | — |
| ADD COLUMN (NOT NULL sem DEFAULT) | ACCESS EXCLUSIVE longo | Alto em tabela grande | nullable, backfill, NOT NULL |
| `DROP COLUMN` | `ACCESS EXCLUSIVE` | Médio | Marcar deprecated, remover depois |
| `RENAME COLUMN` | `ACCESS EXCLUSIVE` breve | Baixo no BD, alto na app | Dual-column na transição |
| `CREATE INDEX` | `SHARE` (bloqueia escrita) | Alto em produção | `CREATE INDEX CONCURRENTLY` |
| `ALTER COLUMN TYPE` | `ACCESS EXCLUSIVE` longo | Alto | Coluna nova + migrate + contract |

### Zero-downtime

- `CREATE INDEX CONCURRENTLY` (PostgreSQL) para índice em produção.
- Backfill em lote (batch), com pausa entre lotes para não saturar o BD.
- Dual-write: aplicação escreve nas duas colunas durante a transição.
- Feature flag para ativar o schema novo gradualmente.

## Indexação

### Quando indexar

- Coluna em WHERE, JOIN e ORDER BY frequente.
- FK (acelera JOIN e ON DELETE CASCADE).
- Coluna com alta seletividade (poucos valores repetidos).

### Quando não indexar

- Tabela pequena (< 1000 linhas): sequential scan é mais rápido.
- Coluna de baixa seletividade (ex.: booleano em tabela uniforme).
- Coluna com escrita frequente e leitura rara: custo de manutenção.

### Tipos de índice

| Tipo | Uso |
|---|---|
| B-tree (default) | Igualdade e range |
| Hash | Só igualdade |
| GIN | JSONB, full-text, arrays |
| GiST | Geométrico, range types |
| BRIN | Dado ordenado naturalmente (timestamp) |
| Partial (`WHERE`) | Subconjunto frequente da tabela |
| Composite | Consulta com múltiplas colunas fixas |

## Checklist de Revisão de Modelo

Use ao revisar artefato de modelagem (DBML, SQL, migration files).

### Schema

- [ ] Toda tabela tem PK definida
- [ ] FK com ON DELETE apropriado (não CASCADE por padrão)
- [ ] Coluna NOT NULL onde ausência não faz sentido
- [ ] CHECK para regra de domínio simples
- [ ] UNIQUE em chave natural do negócio
- [ ] Nome de tabela no plural e coluna no singular (ou convenção do projeto)
- [ ] Sem coluna órfã (sem uso na aplicação)
- [ ] Tipo adequado (ver tabela acima); sem `TEXT` sem limite onde `VARCHAR(n)` basta
- [ ] Timestamp com fuso (`TIMESTAMPTZ`)

### Migration

- [ ] Migration é reversível (rollback ou plano documentado)
- [ ] Backward-compatible (não quebra o deploy anterior)
- [ ] Uma alteração lógica por migration
- [ ] Sem operação de lock longo em tabela grande sem alternativa
- [ ] `CREATE INDEX CONCURRENTLY` para índice em produção
- [ ] Backfill planejado para dado existente
- [ ] Rollback testado em ambiente de teste
- [ ] Sem dado de seed hardcoded em migration de schema

### Performance

- [ ] Índice em coluna de WHERE/JOIN/ORDER BY frequente
- [ ] FK indexada (JOIN e CASCADE)
- [ ] Sem índice redundante (prefixo de índice composto)
- [ ] Particionamento avaliado para tabela > 10M linhas
- [ ] N+1 resolvido no nível do schema (JOIN, lateral, materialized view)

### Segurança

- [ ] Dados sensíveis (PII) identificados e protegidos (criptografia, máscara, coluna separada)
- [ ] Sem senha ou segredo em coluna de texto plano
- [ ] Auditoria (created_at, updated_at, created_by) onde aplicável

## Ferramentas

| Ferramenta | Uso |
|---|---|
| DBML | Modelagem visual versionável |
| pg-schema-dbml | Extrair DBML do schema PostgreSQL real |
| RosettaDB / diff | Comparar DBML com schema real |
| Flyway / Alembic / golang-migrate | Framework de migration |
| dbml2sql | Gerar DDL a partir de DBML |

## Red flags

- Migration sem rollback ou sem plano de reversão.
- `DROP COLUMN` sem período de deprecação.
- `ALTER COLUMN TYPE` em tabela grande sem plano de migração.
- FK sem índice na coluna referenciada.
- `SELECT *` em código de aplicação (quebra com coluna nova).
- Tabela sem PK; coluna nullable sem motivo documentado.
- Enum nativo do BD (rígido para adicionar valor).
- Índice em coluna booleana de distribuição uniforme.
- Migration que mistura DDL e DML sem motivo.
