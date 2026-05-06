# Plano — Implementação do Agente `rev` (Revisor Integrativo)

Status: AGUARDANDO APROVAÇÃO DO HUMANO

---

## 1. Resumo

Criar `agents/rev.md` — executor que:
- Verifica consistência entre partes do plano/construção
- Verifica aderência ao plano aprovado
- Não corrige — devolve relatório estruturado
- Correções simples → `eng-software`; complexas →
  especialista (`dba`, `sec`, etc.)
- Localiza e executa harness antes de finalizar
- Produz evidências de execução do harness

---

## 2. Comportamentos extraídos do workflow

### 2.1 Premissas que o afetam

| # | Regra | Origem |
|---|-------|--------|
| P2 | Resultado no arquivo + resumo curto (≤ 5 linhas) ao `orq` | Premissa 2 |
| P3 | Instância nova a cada fase | Premissa 3 |
| P6 | Agnóstico do workflow — descreve capacidades, não fases | Premissa 6 |
| P12 | Revisão híbrida: `rev` é integrativo, não corrige | Premissa 12 |
| P13 | Sempre instância limpa, sem histórico | Premissa 13 |
| P14 | Base de revisão: plano aprovado + insumos do humano | Premissa 14 |
| P31 | Harness definido no Mapa do Produto | Premissa 31 |
| P32 | Localiza harness antes de executar | Premissa 32 |
| P33 | Produz evidências de execução do harness | Premissa 33 |

### 2.2 Capacidades do `rev`

> **Premissa 6**: o prompt descreve o que `rev` sabe
> fazer, sem mencionar fases do workflow. Quem decide
> quando spawná-lo é o `orq`.

`rev` possui **uma capacidade** (revisão integrativa)
aplicável a qualquer artefato estruturado:

1. Receber um artefato com seções produzidas por agentes
   diferentes (plano, resumos, código, docs).
2. Verificar:
   - Consistência entre seções (modelo BD vs plano de
     código vs segurança vs testes vs documentação)
   - Aderência ao plano aprovado
   - Contradições, lacunas ou desvios entre partes
3. Persistir relatório na seção dedicada do arquivo.
4. Retornar resumo ≤ 5 linhas ao solicitante.

### 2.3 Formato do relatório (saída)

O relatório de `rev` difere do formato dos especialistas.
Especialistas usam: Achado · Ação · Severidade.
`rev` entrega **achados integrativos**:

```markdown
## Revisão Integrativa

### Achados

| # | Tipo | Descrição | Partes envolvidas | Severidade |
|---|------|-----------|-------------------|------------|
| 1 | Inconsistência | ... | dba ↔ eng | bloqueante |
| 2 | Lacuna | ... | sec ↔ qa | melhoria |

### Recomendação

- Achado 1: delegar a [especialista] ou aplicar por
  eng-software
- Achado 2: ...

### Veredicto

[ ] Aprovado sem ressalvas
[ ] Aprovado com melhorias opcionais
[ ] Bloqueado — resolver achados bloqueantes antes de
    prosseguir
```

### 2.4 Limites explícitos (o que NÃO faz)

- Não corrige artefatos (código, SQL, configs)
- Não executa testes
- Não planeja implementação
- Não revisa domínios específicos (BD, segurança) — isso
  é papel dos especialistas
- Não atualiza o Mapa do Produto (papel do
  `curador-produto`)
- Pode consultar o humano para esclarecer dúvidas
  (premissa 4)

### 2.5 Harness catalogado para `rev` (workflow §catálogo)

O workflow define 4 sugestões de harness para `rev`:

| Regra | Tipo | Fase |
|-------|------|------|
| Markdown lint (markdownlint) | tool | val |
| Link check (markdown-link-check) | tool | val |
| Consistência cross-artefato | prompt | val |
| Aderência ao plano | prompt | val |

O harness efetivo é definido no Mapa do Produto de cada
projeto. O prompt de `rev` deve implementar a lógica de
localização (P32) e produção de evidências (P33).

---

## 3. Artefato: `agents/rev.md`

### 3.1 Frontmatter

```yaml
---
description: >
  Revisor integrativo: verifica consistência entre
  artefatos (BD, código, segurança, testes, docs) e
  aderência ao plano aprovado. Não corrige — devolve
  relatório estruturado para eng-software ou
  especialista aplicar (PT-BR)
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

**Justificativa `mode: primary`**: agentes spawnados que
podem consultar o humano (premissa 4) devem ser primários
no VS Code.

**Justificativa `edit: allow`**: persiste relatório no
arquivo de planejamento.

**Justificativa `bash: allow`**: precisa executar scripts
de harness (markdownlint, markdown-link-check) quando o
Mapa do Produto os define.

### 3.2 Corpo (estrutura planejada)

Seguindo convenção do `qa.md` (agente mais recente):

1. **Identidade** — revisor integrativo, PT-BR, nunca
   corrige. Pode ser acionado por humano ou outros
   agentes.
2. **O que você faz** — descrição de capacidades (sem
   mencionar fases do workflow):
   - Revisão integrativa de artefatos
3. **Contrato Operacional**:
   - Chamado por outro agente: persistir no arquivo +
     resumo ≤ 5 linhas
   - Chamado pelo humano: interação livre
   - Harness: localizar no Mapa do Produto e executar
   - Falha: registrar impedimento e informar solicitante
4. **Capacidade: Revisão integrativa** — checklist:
   - Consistência BD ↔ código
   - Consistência segurança ↔ implementação
   - Cobertura de testes ↔ requisitos
   - Documentação ↔ Mapa do Produto
   - Aderência ao plano aprovado
   - Contradições ou lacunas entre seções
5. **Formato de saída** — tabela de achados +
   recomendação + veredicto
6. **Regras de delegação** — achados simples →
   eng-software; complexos → especialista
7. **Limites** — o que NÃO faz
8. **Evidências de Execução** — lista de evidências
   (script ou checklist estruturado)
9. **Interação com Humano** — por outro agente vs direto
10. **Skills de referência** — consultar quando relevante

### 3.3 Skills de referência para o corpo

| Skill | Uso no `rev` |
|-------|-------------|
| `code-review-and-quality` | Framework de revisão multi-eixo — adaptar eixos para o contexto integrativo (consistência, aderência, completude) |
| `documentation-and-adrs` | Verificar se decisões estão documentadas e se docs aderem a padrões |

**Por que essas e não outras**:
- `code-review-and-quality` oferece um modelo mental
  estruturado de revisão (5 eixos) que `rev` pode
  adaptar ao escopo integrativo.
- `documentation-and-adrs` oferece critérios para
  avaliar se documentação produzida é consistente.
- Skills de domínio (`security-and-hardening`,
  `test-driven-development`) são do escopo dos
  especialistas, não de `rev`.

O prompt de `rev` deve referenciar essas skills com a
instrução "consulte a skill X quando relevante" — sem
reproduzir o conteúdo.

---

## 4. Compatibilidade VS Code

O `vscode-sync.ps1` já converte `agents/*.md` →
`*.agent.md`:
- Strip-AgentFrontmatter mantém apenas `description`
- Resultado: `rev.agent.md` em
  `%APPDATA%\Code\User\prompts\`
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
- [ ] Rodar `make test` — validar que o novo agente é
      listado
- [ ] Verificar que `vscode-sync.ps1` gera `rev.agent.md`
- [ ] Atualizar `AGENTS.md` (description do rev no bloco
      de agentes disponíveis)

---

## 7. Decisões para o humano

1. **Formato do relatório**: o formato proposto em 2.3 é
   adequado? Prefere outro layout?
2. **Checklist integrativo**: as dimensões em 3.2 §4
   (BD↔código, segurança↔impl, testes↔requisitos,
   docs↔Mapa, aderência ao plano) cobrem o esperado?
3. **Skills de referência**: concordas com
   `code-review-and-quality` e `documentation-and-adrs`
   como referências? Quer adicionar outra?
4. **bash: allow**: necessário para executar scripts de
   harness (markdownlint, link-check). Confirma?
