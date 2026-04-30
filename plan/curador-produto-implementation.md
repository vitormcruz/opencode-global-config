# Plano — Implementação do Agente `curador-produto`

Status: AGUARDANDO APROVAÇÃO DO HUMANO

> **workflow atualizado** — `docs/workflow-agentes.md` já reflete
> a participação do `curador-produto` nos loops de revisão.

---

## 1. Resumo

Criar `agents/curador-produto.md` — executor modo `val` que:
- Valida entrada contra o Mapa do Produto
- É guardião do Mapa (detecta ausência, sugere organização)
- Faz revisão final de documentação e estrutura
- Exclui o arquivo de planejamento ao fim do processo
- Nunca cria escopo nem requisitos

---

## 2. Comportamentos extraídos do workflow

### 2.1 Premissas que o afetam

| # | Regra | Origem |
|---|-------|--------|
| P2 | Resultado no arquivo + resumo curto (≤ 5 linhas) de volta ao `orq` | Premissa 2 |
| P3 | Instância nova a cada fase | Premissa 3 |
| P12 | Revisores são instâncias limpas com contexto limpo | Premissa 12 |
| P13 | Avalia com base no plano aprovado e insumos originais do humano | Premissa 13 |
| P19 | Exige "Mapa do Produto" no arquivo de contexto do agente | Premissa 19 |
| P20 | Conteúdo do Mapa é livre — cada projeto preenche | Premissa 20 |
| P21 | Guardião do Mapa — detecta ausência, sugere organização | Premissa 21 |
| P22 | Mapa deve ficar no início do arquivo de contexto | Premissa 22 |
| P23 | Valida, não define — não cria escopo/requisitos | Premissa 23 |

### 2.2 Ações por fase do workflow

#### VALIDAÇÃO DE ENTRADA (spawnado por `orq`)
1. Recebe requisitos do humano via arquivo de planejamento
2. Localiza o Mapa do Produto no arquivo de contexto do projeto
3. Se Mapa ausente:
   - Reporta ausência ao humano
   - Sugere organização inicial (sem impor)
   - Aguarda humano fornecer/aprovar conteúdo
4. Se Mapa presente:
   - Verifica consistência da entrada com o Mapa
   - Se OK → retorna "Entrada válida" (resumo ≤ 5 linhas)
   - Se inconsistente → reporta inconsistências ao humano,
     recebe ajustes, revalida, retorna resumo

#### REVISÃO DO PLANO (spawnado por `orq`, instância limpa)
1. Verifica se o plano prevê documentação conforme o Mapa do
   Produto (estrutura de diretórios, convenções, nomenclatura)
2. Se conforme → retorna resumo (achado · ação · severidade)
3. Se não conforme → retorna instruções de ajuste ao `orq`,
   que delega ao agente responsável (padrão ajustes integrativos)

#### REVISÃO DA CONSTRUÇÃO (spawnado por `orq`, instância limpa)
1. Verifica se a documentação produzida durante a construção
   está aderente ao Mapa do Produto
2. Se conforme → retorna resumo (achado · ação · severidade)
3. Se não conforme → retorna instruções de ajuste ao `orq`,
   que delega ao agente responsável (padrão ajustes integrativos)

#### FINALIZAÇÃO (spawnado por `orq`)
1. Revisão final de documentação e estrutura do que foi produzido
2. Verifica aderência ao Mapa do Produto
3. Atualiza docs se necessário (retorna "Docs atualizados")
4. Exclui o arquivo de planejamento

### 2.3 Limites explícitos (o que NÃO faz)
- Não cria escopo nem requisitos
- Não executa código nem testes
- Não corrige artefatos de código, BD ou segurança —
  devolve instruções ao `orq` para esses domínios

### 2.4 O que FAZ diretamente
- Atualiza o Mapa do Produto (seção no arquivo de contexto)
- Atualiza documentação de produto (README, convenções, etc.)
- Exclui arquivo de planejamento na Finalização

---

## 3. Artefato: `agents/curador-produto.md`

### 3.1 Frontmatter (seguindo convenções do repo)

```yaml
---
description: >
  Valida entrada contra Mapa do Produto, mantém o Mapa
  atualizado e faz revisão final de documentação (PT-BR)
mode: primary
temperature: 0.2
permission:
  edit: allow
  bash: deny
  webfetch: deny
  websearch: deny
  task:
    "*": deny
---
```

**Justificativa `mode: primary`**: o workflow exige que o agente
interaja diretamente com o humano (reportar inconsistências,
sugerir Mapa). No VS Code, apenas agentes primários spawnados
por outro agente conseguem fazer isso.

**Justificativa `bash: deny`**: o agente apenas lê e edita
arquivos de documentação. Não precisa executar comandos.

### 3.2 Corpo (estrutura planejada)

Seções do markdown:
1. **Identidade** — quem é, idioma PT-BR
2. **Modo VAL** — único modo, quatro variantes de atuação:
   - Validação de Entrada
   - Revisão do Plano (documentação planejada)
   - Revisão da Construção (documentação produzida)
   - Finalização
3. **Mapa do Produto** — regras de guarda (P19–P22)
4. **Princípios de documentação** — filosofia + práticas
   (seção 3.3 abaixo)
5. **Limites** — o que não faz (P23)
6. **Contrato de retorno** — resumo ≤ 5 linhas (P2);
   nas revisões usa formato achado · ação · severidade (P14)
7. **Confirmações e interação com humano** — padrão do repo

### 3.3 Princípios de documentação (conteúdo do prompt)

#### Filosofia (generalista)

1. **Código é documentação** — é o design da aplicação.
   Ferramentas que extraem conhecimento do código são
   preferíveis a docs manuais.
2. **Doc derivável não se armazena** — se pode ser gerada
   a partir do código, gere sob demanda.
3. **Doc é para público diferente do dev** — o dev prefere
   código. Doc vale quando contextualiza agentes, comunica
   com stakeholders, ou agrega abstração.
4. **Transformação justifica doc** — só manter doc separada
   se houver mudança de formato (texto→diagrama), abstração
   (código→visão condensada) ou sumarização (decisões
   dispersas→visão consolidada).
5. **Docs devem ser executáveis** — preferir especificações
   testáveis. Decisões arquiteturais viram fitness functions,
   critérios de aceitação viram specs executáveis.
6. **Brownfield é pragmático** — pode não comportar técnicas
   avançadas. Grafos de conhecimento do código (não-intrusivos)
   ajudam muito. Sugerir gradualismo.
7. **Doc atualizada ou nenhuma** — doc desatualizada é pior
   que ausência.

#### Práticas (generalista — independente de linguagem)

| Prática | Descrição |
|---------|-----------|
| Grafo de conhecimento do código | Extrair estrutura navegável para humanos e agentes |
| Specs executáveis (BDD) | Critérios de aceitação como testes automatizados |
| Fitness functions | Decisões arquiteturais como testes automatizados |
| Modelo de dados "as code" | Schema versionado + validação contra BD real (diff) |
| Diagramas em Mermaid | Formato textual, versionável, renderizável |
| Contract testing | Interfaces entre serviços como doc executável |
| API spec validada em CI | Spec (REST/async) validada contra implementação |
| ADRs executáveis | Decisões → testes; agente lê ADR e verifica conformidade |
| README mínimo | Aponta para fontes vivas; não repete |

#### Exemplos por ecossistema (referência, não prescrição)

| Prática | Exemplos |
|---------|----------|
| Grafo de conhecimento | Graphify (multi-linguagem, MCP server) |
| Specs executáveis | Cucumber (JVM/JS), Gauge, pytest-bdd |
| Fitness functions | ArchUnit (Java), ArchUnitTS, ArchUnitPython, go-arctest |
| Modelo "as code" | DBML + dbml2sql, RosettaDB diff, pg-schema-dbml |
| Diagramas derivados | C4-Auto (TS), C4InterFlow (C#), c4-skill (Claude) |
| Contract testing | Pact |
| API spec | OpenAPI, AsyncAPI |

#### Contexto do projeto (avaliar antes de sugerir)

- **Greenfield**: sugerir toolkit completo (grafo + specs +
  fitness + modelo as code + diagramas derivados)
- **Brownfield**: começar pelo grafo de conhecimento
  (não-intrusivo), modelo extraído do schema real, ADRs
  retroativos → migrar gradualmente para fitness functions

---

## 4. Modificações em testes

### 4.1 `tests/opencode-int-test/agents-test.bats`

Adicionar teste:
```bash
@test "behavioral: GET /agent lista o agente curador-produto" {
  run curl -sf "${OPENCODE_BASE_URL}/agent"
  assert_success
  assert_output --partial "curador-produto"
}
```

### 4.2 Sincronização VS Code

O `vscode-sync.ps1` já converte `agents/*.md` → `*.agent.md`
automaticamente. Nenhuma alteração necessária no script.

---

## 5. Modificações em `AGENTS.md`

Adicionar entrada na tabela de agentes:
```markdown
<agent>
<name>curador-produto</name>
<description>Valida entrada contra Mapa do Produto e faz revisão
final de documentação e estrutura (PT-BR)</description>
</agent>
```

---

## 6. Mudanças já aplicadas em `docs/workflow-agentes.md`

- Premissa 21: expandida — único agente que atualiza
  diretamente o Mapa do Produto
- Premissa 23: expandida — atualiza diretamente Mapa e
  docs de produto; delega outros domínios ao `orq`
- Tabela "Especialidades dos Agentes": coluna atualizada
- Diagrama mermaid — REVISÃO DO PLANO: `curador-produto`
  adicionado após `qa` e antes de `rev`
- Diagrama mermaid — REVISÃO DA CONSTRUÇÃO: idem
- Blocos `opt Ajustes integrativos`: incluem sub-bloco
  "Ajustes de documentação (curador-produto)"
- Harness: seção `### curador-produto` com 3 regras
  (Checklist do Mapa, Atualiza Mapa diretamente,
  Delega outros domínios)

---

## 7. Checklist de implementação

- [x] Atualizar `docs/workflow-agentes.md`
- [ ] Criar `agents/curador-produto.md`
- [ ] Adicionar teste em `tests/opencode-int-test/agents-test.bats`
- [ ] Atualizar `AGENTS.md` com nova entrada
- [ ] Rodar `make test` para validar
- [ ] Excluir este arquivo de plano após conclusão

---

## 8. Notas

- O workflow não prescreve formato do Mapa do Produto (P20).
  O agente deve orientar o humano quando solicitado, mas a
  decisão de conteúdo é sempre do humano.
- A exclusão do arquivo de planejamento na Finalização é uma
  ação destrutiva — o agente deve confirmar com o humano antes
  de excluir (coerência com as regras globais do repo).
- Nas revisões, `curador-produto` atua em paralelo com os
  revisores especializados e o `rev`. Não há dependência
  entre eles — o `orq` pode spawnar todos em sequência
  ou paralelamente conforme a plataforma suportar.
- O padrão de retorno nas revisões segue P14 (achado · ação
  · severidade), mesmo que o curador não corrija diretamente.
