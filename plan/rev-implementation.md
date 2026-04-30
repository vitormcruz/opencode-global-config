# Plano — Implementação do Agente `rev` (Revisor Integrativo)

Status: AGUARDANDO APROVAÇÃO DO HUMANO

---

## 1. Resumo

Criar `agents/rev.md` — executor modo `val` que:
- Verifica consistência entre partes do plano/construção
- Verifica aderência ao plano aprovado
- Não corrige — devolve relatório estruturado
- Correções simples vão para `eng-software`; complexas,
  delegadas ao especialista (`dba`, `sec`, etc.)

---

## 2. Comportamentos extraídos do workflow

### 2.1 Premissas que o afetam

| # | Regra | Origem |
|---|-------|--------|
| P2 | Resultado no arquivo + resumo curto (≤ 5 linhas) ao `orq` | Premissa 2 |
| P3 | Instância nova a cada fase | Premissa 3 |
| P11 | Revisão híbrida: `rev` é integrativo, não corrige | Premissa 11 |
| P12 | Sempre instância limpa, sem histórico | Premissa 12 |
| P13 | Base de revisão: plano aprovado + insumos do humano | Premissa 13 |

### 2.2 O que `rev` faz (diagrama + tabela de especialidades)

`rev` é spawnado por `orq` em **duas fases**:

#### REVISÃO DO PLANO
1. Recebe o arquivo de planejamento (já com resumos de
   `dba`, `sec`, `qa`)
2. Verifica:
   - Consistência entre seções (modelo BD vs plano de código
     vs requisitos de segurança vs plano de testes)
   - Aderência ao plano original aprovado pelo humano
   - Contradições ou lacunas entre as partes
3. Persiste relatório na seção dedicada do arquivo
4. Retorna resumo ≤ 5 linhas ao `orq`

#### REVISÃO DA CONSTRUÇÃO
1. Recebe o arquivo de planejamento (já com resumos dos
   revisores especializados pós-construção)
2. Verifica:
   - Consistência entre artefatos construídos
   - Aderência ao plano aprovado (código vs plano)
   - Divergências entre o que foi planejado e implementado
3. Persiste relatório na seção dedicada do arquivo
4. Retorna resumo ≤ 5 linhas ao `orq`

### 2.3 Formato do relatório (saída)

O relatório de `rev` difere do formato dos especialistas.
Especialistas usam: Achado · Ação · Severidade.
`rev` entrega **achados integrativos** — formato proposto:

```markdown
## Revisão Integrativa — [Plano|Construção]

### Achados

| # | Tipo | Descrição | Partes envolvidas | Severidade |
|---|------|-----------|-------------------|------------|
| 1 | Inconsistência | ... | dba ↔ eng | bloqueante |
| 2 | Lacuna | ... | sec ↔ qa | melhoria |

### Recomendação

- Achado 1: delegar a [especialista] ou aplicar por eng-software
- Achado 2: ...

### Veredicto

[ ] Aprovado sem ressalvas
[ ] Aprovado com melhorias opcionais
[ ] Bloqueado — resolver achados bloqueantes antes de prosseguir
```

### 2.4 Limites explícitos (o que NÃO faz)

- Não corrige artefatos (código, SQL, configs)
- Não executa testes
- Não planeja implementação
- Não revisa domínios específicos (BD, segurança) — isso é
  papel dos especialistas
- Não interage com o humano para coleta de requisitos
  (pode consultar para esclarecer dúvidas — premissa 4)

---

## 3. Artefato: `agents/rev.md`

### 3.1 Frontmatter

```yaml
---
description: >
  Revisor integrativo do workflow multi-agente. Verifica
  consistência entre partes (BD, código, segurança, testes) e
  aderência ao plano aprovado. Não corrige — devolve relatório
  estruturado para eng-software ou especialista aplicar.
  Spawnado por orq nas fases de revisão.
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

**Justificativa `mode: primary`**: conforme decisão do plano do
`orq`, agentes spawnados que podem precisar consultar o humano
(premissa 4) devem ser primários no VS Code.

**Justificativa `edit: allow`**: precisa persistir o relatório
no arquivo de planejamento.

### 3.2 Corpo (estrutura planejada)

1. **Identidade** — revisor integrativo, PT-BR, nunca corrige
2. **Contexto de entrada** — o que espera receber:
   - Caminho do arquivo de planejamento
   - Fase atual (revisão do plano ou da construção)
   - Arquivo já deve conter resumos dos especialistas
3. **Processo de revisão** — checklist integrativo:
   - Consistência BD ↔ código
   - Consistência segurança ↔ implementação
   - Cobertura de testes ↔ requisitos
   - Aderência ao plano aprovado
   - Contradições ou lacunas entre seções
4. **Formato de saída** — relatório estruturado (tabela de
   achados + recomendação + veredicto)
5. **Contrato com `orq`** — persistir no arquivo, retornar
   resumo ≤ 5 linhas
6. **Regras de delegação** — achados simples → eng-software;
   achados complexos de domínio → especialista
7. **Confirmações** — premissa 4: pode consultar humano para
   esclarecer dúvidas; não precisa de confirmação por etapa
   (é read-mostly + relatório)

---

## 4. Compatibilidade VS Code

O `vscode-sync.ps1` já converte `agents/*.md` → `*.agent.md`:
- Strip-AgentFrontmatter mantém apenas `description`
- Resultado: `rev.agent.md` em `%APPDATA%\Code\User\prompts\`
- Nenhuma modificação necessária no script de sync

---

## 5. Modificações em testes

### 5.1 Teste existente: `tests/opencode-int-test/agents-test.bats`

Adicionar:

```bats
@test "behavioral: GET /agent lista o agente rev" {
  run curl -sf "${OPENCODE_BASE_URL}/agent"
  assert_success
  assert_output --partial "rev"
}
```

### 5.2 Nenhum outro teste existente é afetado

Os demais arquivos de teste (`commands-test.bats`,
`skills-activation-test.bats`, etc.) não tocam em agentes.

---

## 6. Checklist de entrega

- [ ] Criar `agents/rev.md` com frontmatter + corpo
- [ ] Adicionar teste em `agents-test.bats`
- [ ] Rodar `make test` — validar que o novo agente é listado
- [ ] Verificar que `vscode-sync.ps1` gera `rev.agent.md`
- [ ] Atualizar `AGENTS.md` (description do rev no bloco de
      agentes disponíveis)

---

## 7. Decisões para o humano

1. **Formato do relatório**: o formato proposto em 2.3 é
   adequado? Prefere outro layout?
2. **Checklist integrativo**: as dimensões de consistência
   listadas em 3.2 §3 cobrem o que espera? Quer adicionar
   ou remover alguma?
3. **Interação com humano**: `rev` deve perguntar ao humano
   apenas em caso de dúvida (mínimo) ou também apresentar
   achados intermediários antes de finalizar?
