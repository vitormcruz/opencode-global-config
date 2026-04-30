# Plano — Implementação do Agente `qa`

Status: AGUARDANDO APROVAÇÃO DO HUMANO

---

## 1. Resumo

Criar `agents/qa.md` — executor modos `plan` e `val` que:
- Planeja testes manuais, aceitação e exploratórios
- Revisa e corrige cobertura de testes
- Executa testes automatizados e manuais
- Devolve resumo estruturado (achado · ação · severidade)
- Não analisa código
- Não executa testes de segurança

---

## 2. Comportamentos extraídos do workflow

### 2.1 Premissas que o afetam

| # | Regra | Origem |
|---|-------|--------|
| P2 | Resultado no arquivo + resumo curto (≤ 5 linhas) de volta ao `orq` | Premissa 2 |
| P3 | Instância nova a cada fase | Premissa 3 |
| P11 | Revisão híbrida: especialistas + integrativa — `qa` é revisor especializado | Premissa 11 |
| P12 | Revisores são instâncias limpas com contexto limpo (sem viés de confirmação) | Premissa 12 |
| P13 | Avalia com base no plano aprovado e insumos originais do humano | Premissa 13 |
| P14 | Formato: achado · ação · severidade | Premissa 14 |
| P25 | Não analisa código — foca em execução de testes | Premissa 25 |
| P26 | Testes de segurança são do `sec`, não do `qa` | Premissa 26 |

### 2.2 Ações por fase do workflow

#### PLANEJAMENTO (modo plan, spawnado por `orq`)
1. Recebe requisitos/plano de código via arquivo de planejamento
2. Planeja:
   - Testes de aceitação (baseados em critérios do humano)
   - Testes exploratórios (cenários de borda, fluxos alternativos)
   - Testes manuais (quando automação não é viável/custo-benefício)
3. Persiste plano de testes no arquivo de planejamento
4. Retorna resumo ≤ 5 linhas ao `orq`

#### REVISÃO DO PLANO (modo val, instância limpa)
1. Revisa testabilidade do plano de implementação
2. Verifica se os critérios de aceitação são testáveis
3. Corrige lacunas no plano de testes (se houver)
4. Registra resumo no arquivo (achado · ação · severidade)
5. Retorna resumo ≤ 5 linhas ao `orq`

#### REVISÃO DA CONSTRUÇÃO (modo val, instância limpa)
1. Revisa cobertura de testes do código construído
2. Verifica se testes planejados foram implementados
3. Identifica cenários não cobertos
4. Corrige lacunas de cobertura (cria/ajusta testes)
5. Registra resumo no arquivo (achado · ação · severidade)
6. Retorna resumo ≤ 5 linhas ao `orq`

#### TESTES (modo val, spawnado por `orq`)
1. Executa testes automatizados (roda suíte do projeto)
2. Executa testes manuais planejados (quando aplicável)
3. Reporta resultado:
   - Se todos passam → resumo de sucesso
   - Se falham → lista falhas para `eng-software` corrigir
4. Persiste resultado no arquivo
5. Retorna resumo ≤ 5 linhas ao `orq`

### 2.3 Limites explícitos (o que NÃO faz)
- Não analisa código-fonte (P25)
- Não executa testes de segurança (P26) — responsabilidade do `sec`
- Não corrige código de produção — apenas testes
- Não faz revisão integrativa — responsabilidade do `rev`

---

## 3. Artefato: `agents/qa.md`

### 3.1 Frontmatter

```yaml
---
description: >
  Planeja e executa testes (aceitação, exploratórios, manuais),
  revisa cobertura e devolve resumo estruturado (PT-BR)
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

**Justificativa `mode: primary`**: o workflow permite que qualquer
agente consulte o humano (premissa 4). No VS Code, apenas agentes
primários spawnados por outro agente conseguem interagir com o
humano.

**Justificativa `bash: allow`**: o agente precisa executar testes
automatizados (rodar suíte de testes do projeto).

### 3.2 Corpo (estrutura planejada)

Seções do markdown:

1. **Identidade** — quem é, idioma PT-BR, pode ser acionado por
   humano ou por outros agentes
2. **Modo PLAN** — planejamento de testes:
   - Testes de aceitação (critérios do humano)
   - Testes exploratórios (cenários de borda)
   - Testes manuais (quando automação não é viável)
   - Entrega: plano de testes persistido no arquivo
3. **Modo VAL** — três variantes:
   - Revisão de testabilidade (REVISÃO DO PLANO)
   - Revisão de cobertura (REVISÃO DA CONSTRUÇÃO)
   - Execução de testes (TESTES)
4. **Limites** — o que não faz (P25, P26)
5. **Contrato de retorno** — resumo ≤ 5 linhas (P2);
   formato de revisão: achado · ação · severidade (P14)
6. **Confirmações e interação com humano** — padrão do repo
   (confirmação por etapa no plan, autonomia na execução)

---

## 4. Modificações em testes

### 4.1 `tests/opencode-int-test/agents-test.bats`

Adicionar teste:

```bash
@test "behavioral: GET /agent lista o agente qa" {
  run curl -sf "${OPENCODE_BASE_URL}/agent"
  assert_success
  assert_output --partial "qa"
}
```

### 4.2 Sincronização VS Code

O `vscode-sync.ps1` já converte `agents/*.md` → `*.agent.md`
automaticamente. Nenhuma alteração necessária no script.

---

## 5. Modificações em `AGENTS.md`

Adicionar entrada na seção de agentes:

```markdown
<agent>
<name>qa</name>
<description>Planeja e executa testes (aceitação, exploratórios,
manuais), revisa cobertura e devolve resumo estruturado
(PT-BR)</description>
</agent>
```

---

## 6. Checklist de implementação

- [ ] Criar `agents/qa.md`
- [ ] Adicionar teste em `tests/opencode-int-test/agents-test.bats`
- [ ] Atualizar `AGENTS.md` com nova entrada
- [ ] Rodar `make test` para validar
- [ ] Excluir este arquivo de plano após conclusão

---

## 7. Notas

- O `qa` tem `bash: allow` (diferente do `curador-produto`) porque
  precisa executar suítes de teste. Mas **não** deve usar bash para
  analisar código-fonte — apenas para rodar comandos de teste.
- Na fase TESTES, se testes falham, o `qa` apenas reporta ao `orq`.
  Quem corrige é o `eng-software`. O `qa` pode re-executar após
  correção se o humano autorizar (via `orq`).
- O formato do resumo de revisão segue a premissa 14:
  **Achado** → **Ação** → **Severidade** (bloqueante ou melhoria).
