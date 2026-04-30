# Plano — Implementação do Agente `dba`

Status: AGUARDANDO APROVAÇÃO DO HUMANO

---

## 1. Resumo

Substituir `agents/analista-bd.md` por `agents/dba.md` — executor
com modos plan · build · val, alinhado ao workflow multi-agente.
O `dba` absorve o conhecimento do `analista-bd` e evolui para
atender às premissas do workflow (2, 3, 11, 12, 13, 14).

---

## 2. Análise: analista-bd → dba (preservar / evoluir / descartar)

### 2.1 PRESERVAR (incorporar no dba)

| Elemento | Motivo |
|----------|--------|
| Foco em DBML conceitual + SQL de migração | Core do papel |
| Boas práticas de migração (expand/contract, backfill, rollback) | Expertise técnica sólida |
| Regras de DBML como artefato conceitual (não DDL) | Separação conceitual/físico |
| Proatividade: localizar artefatos no repo | Útil em qualquer modo |
| Seção "Arquitetura de migrações" | Gate antes de gerar SQL |
| Formatos de saída (Modo A e Modo B) | Base para plan/build |
| Entradas a coletar (SGBD, convenções, restrições) | Checklist útil |

### 2.2 EVOLUIR

| Elemento atual | Evolução necessária |
|----------------|---------------------|
| Modo A (PLANEJAR) | → modo `plan` — mantém essência, mas resultado vai no **arquivo de planejamento** (não só na conversa) + resumo ≤ 5 linhas ao orq |
| Modo B (CONSTRUIR) | → modo `build` — além de gerar artefatos, **informa eng-software** quais classes/comportamentos alterar (registro no arquivo) |
| Confirmações por etapa (Modo A) | Manter, mas adequar ao contrato: humano pode interagir direto (premissa 4) |
| Máxima autonomia (Modo B) | Manter, mas registrar impedimentos no arquivo se falhar (premissa 5) |
| `mode: subagent` | → `mode: primary` (necessário no VS Code para interação com humano) |
| Sem modo de validação | → modo `val` — revisar e corrigir artefatos de BD, devolver resumo (achado · ação · severidade) |
| Aprovação via frase-chave `HUMANO APROVOU:` | Manter — compatível com premissa 4 |

### 2.3 DESCARTAR

| Elemento | Motivo |
|----------|--------|
| Header "Você é o Analista-BD" | Renomear para `dba` |
| `webfetch: deny` / `websearch: deny` explícitos | Manter deny, mas simplificar (herança do padrão) |
| Texto "Este agente pode ser acionado por HUMANO ou OUTROS AGENTES" | Redundante — todo executor do workflow é spawnado pelo orq |

---

## 3. Requisitos extraídos do workflow

### 3.1 Premissas aplicáveis

| # | Regra |
|---|-------|
| P2 | Resultado persistido no arquivo de planejamento + resumo curto (≤ 5 linhas) de volta ao `orq` |
| P3 | Instância nova a cada fase — sem carregar contexto de fases anteriores |
| P11 | Revisor especializado: revisa e corrige artefatos da sua área, devolve resumo estruturado |
| P12 | Revisores são instâncias limpas com contexto limpo — nunca revisa o que construiu |
| P13 | Avalia com base no plano aprovado e insumos originais do humano |
| P14 | Formato do resumo: achado · ação · severidade (bloqueante ou melhoria) |

### 3.2 Ações por fase

#### modo `plan` (PLANEJAMENTO)
- Recebe insumo via arquivo de planejamento
- Modela dados: DBML conceitual + estratégia de migração
- Consulta humano para alinhar (premissa 4)
- Persiste plano no arquivo de planejamento
- Retorna resumo ≤ 5 linhas ao orq

#### modo `build` (CONSTRUÇÃO)
- Recebe plano aprovado via arquivo de planejamento
- Cria/atualiza: DBML, SQL (up/down), scripts de migração
- **Informa eng-software** — registra no arquivo quais
  classes/comportamentos precisam ser alterados pelo eng
- Executa com máxima autonomia (sem consultar humano exceto
  desvio material)
- Se falhar: registra impedimento no arquivo, retorna ao orq
- Persiste artefatos e retorna resumo ≤ 5 linhas

#### modo `val` (VALIDAÇÃO / REVISÃO)
- Instância limpa — sem contexto de fases anteriores
- Lê artefatos de BD produzidos + plano aprovado + insumos
- Revisa e **corrige** artefatos (premissa 11)
- Formato de retorno (premissa 14):
  ```
  - **Achado**: <o que estava errado>
  - **Ação**: <o que foi corrigido>
  - **Severidade**: bloqueante | melhoria
  ```
- Persiste resumo na seção de revisão do arquivo
- Retorna resumo ≤ 5 linhas ao orq

---

## 4. Estrutura do agente `agents/dba.md`

### 4.1 Frontmatter

```yaml
---
description: >
  Analista de banco de dados do workflow multi-agente.
  Modela dados (DBML conceitual + SQL), cria migrações seguras,
  informa eng-software sobre classes/comportamentos a alterar,
  e revisa/corrige artefatos de BD. Modos: plan, build, val.
  Spawnado pelo orq. Pode consultar o humano diretamente.
mode: primary
temperature: 0.2
permission:
  edit: allow
  bash: allow
  webfetch: deny
  websearch: deny
  task:
    "*": deny
---
```

### 4.2 Corpo (seções planejadas)

1. **Identidade** — PT-BR, foco em modelagem conceitual e
   migrações seguras
2. **Contrato com o workflow** — premissas 2, 3, 11-14;
   resultado no arquivo + resumo curto
3. **Modos de operação**
   - `plan` — modelar dados (baseado no antigo Modo A)
   - `build` — construir artefatos (baseado no antigo Modo B)
     + informar eng-software
   - `val` — revisar e corrigir (modo novo)
4. **Detecção de modo** — identificar qual modo foi solicitado
   pelo orq (via arquivo de planejamento ou instrução direta)
5. **DBML** — regras preservadas do analista-bd (conceitual,
   não DDL)
6. **Boas práticas de migração** — preservadas do analista-bd
7. **Entradas a coletar** — preservadas (SGBD, processo de
   migração, convenções, restrições)
8. **Proatividade** — localizar artefatos no repo
9. **Arquitetura de migrações** — gate preservado
10. **Formatos de saída por modo**
11. **Interação com humano** — pode consultar diretamente;
    regra da frase-chave `HUMANO APROVOU:` mantida
12. **Tratamento de falha** — registrar impedimento no arquivo,
    retornar ao orq

---

## 5. Estratégia de transição

### 5.1 Renomeação do arquivo

```bash
git mv agents/analista-bd.md agents/dba.md
```

Preserva histórico git. Edições feitas **após** o mv.

### 5.2 Referências a atualizar

| Arquivo | Mudança |
|---------|---------|
| `rules/DEVELOPING.MD` | `@analista-bd` → `@dba` (linhas 44, 45, 47, 54, 75, 88) |
| `rules/fluxo_dev.md` | `@analista-bd` → `@dba` (linhas 31, 73, 110) |
| `AGENTS.md` | Atualizar description e nome do agente |
| `plan/orq-implementation.md` | Referências descritivas — atualizar menções |
| `tests/opencode-int-test/agents-test.bats` | Trocar "analista-bd" → "dba" (linhas 15-18) |
| `tests/scripts/bootstrap_repo/repo-structure-test.bats` | Trocar "analista-bd" → "dba" (linhas 190-191) |

### 5.3 Nota sobre `rules/DEVELOPING.MD` e `rules/fluxo_dev.md`

Estes arquivos descrevem o fluxo antigo (pré-workflow). A
referência será atualizada de `@analista-bd` para `@dba`,
mas o conteúdo desses arquivos pode precisar de refatoração
futura para alinhar com o novo workflow. **Fora do escopo
deste plano** — apenas atualizar o nome.

---

## 6. Modificações em testes

### 6.1 `tests/opencode-int-test/agents-test.bats`

Alterar o teste existente:

```bats
# DE:
@test "behavioral: GET /agent lista o agente analista-bd" {
  ...
  assert_output --partial "analista-bd"
}

# PARA:
@test "behavioral: GET /agent lista o agente dba" {
  ...
  assert_output --partial "dba"
}
```

### 6.2 `tests/scripts/bootstrap_repo/repo-structure-test.bats`

Alterar o teste existente:

```bats
# DE:
@test "agents/analista-bd.md tem frontmatter" {
  run grep -c "^---$" "$REPO_ROOT/agents/analista-bd.md"
  ...
}

# PARA:
@test "agents/dba.md tem frontmatter" {
  run grep -c "^---$" "$REPO_ROOT/agents/dba.md"
  ...
}
```

### 6.3 Nenhum novo arquivo de teste necessário

O agente `dba` é coberto pelos testes existentes (após
atualização de nome). Não há script novo para testar.

---

## 7. Checklist de entrega

- [ ] `git mv agents/analista-bd.md agents/dba.md`
- [ ] Reescrever conteúdo de `agents/dba.md` (frontmatter + corpo)
- [ ] Atualizar `rules/DEVELOPING.MD` (@analista-bd → @dba)
- [ ] Atualizar `rules/fluxo_dev.md` (@analista-bd → @dba)
- [ ] Atualizar `AGENTS.md` (nome + description)
- [ ] Atualizar `plan/orq-implementation.md` (menções)
- [ ] Atualizar `tests/opencode-int-test/agents-test.bats`
- [ ] Atualizar `tests/scripts/bootstrap_repo/repo-structure-test.bats`
- [ ] Rodar `make test`
- [ ] Verificar que `vscode-sync.ps1` gera `dba.agent.md`

---

## 8. Decisões para o humano

1. **Modos antigos vs novos** — o analista-bd usa "Modo A" e
   "Modo B" como nomenclatura. O workflow usa `plan`, `build`,
   `val`. Proposta: adotar a nomenclatura do workflow. OK?

2. **rules/DEVELOPING.MD e fluxo_dev.md** — estes arquivos
   descrevem o fluxo antigo. Apenas renomear referências agora,
   ou já deprecar/refatorar esses arquivos? (Recomendo: apenas
   renomear neste plano, refatorar depois.)

3. **Harness do dba** — o workflow define uma seção "Harness
   por Agente" para `dba` mas está vazia. Incluir algum harness
   na v1 ou deixar vazio por enquanto?

4. **Formato do "informa eng-software"** — no modo build, o dba
   deve registrar no arquivo de planejamento uma seção tipo
   "Impacto no código" listando classes/interfaces a alterar.
   Proposta de formato:
   ```markdown
   ### Impacto no código (para eng-software)
   - Classe/módulo X: adicionar campo Y
   - Interface Z: novo método W
   ```
   OK ou prefere outro formato?
