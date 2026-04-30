# Plano — Implementação do Agente `curador-produto`

Status: AGUARDANDO APROVAÇÃO DO HUMANO

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

#### FINALIZAÇÃO (spawnado por `orq`)
1. Revisão final de documentação e estrutura do que foi produzido
2. Verifica aderência ao Mapa do Produto
3. Atualiza docs se necessário (retorna "Docs atualizados")
4. Exclui o arquivo de planejamento

### 2.3 Limites explícitos (o que NÃO faz)
- Não cria escopo nem requisitos
- Não define o conteúdo do Mapa (orienta o processo se solicitado)
- Não executa código nem testes
- Não revisa segurança, modelagem ou código

---

## 3. Artefato: `agents/curador-produto.md`

### 3.1 Frontmatter (seguindo convenções do repo)

```yaml
---
description: >
  Valida entrada contra Mapa do Produto e faz revisão final
  de documentação e estrutura (PT-BR)
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
2. **Modo VAL** — único modo, com duas variantes:
   - Validação de Entrada
   - Finalização
3. **Mapa do Produto** — regras de guarda (P19–P22)
4. **Limites** — o que não faz (P23)
5. **Contrato de retorno** — resumo ≤ 5 linhas (P2)
6. **Confirmações e interação com humano** — padrão do repo

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

## 6. Checklist de implementação

- [ ] Criar `agents/curador-produto.md`
- [ ] Adicionar teste em `tests/opencode-int-test/agents-test.bats`
- [ ] Atualizar `AGENTS.md` com nova entrada
- [ ] Rodar `make test` para validar
- [ ] Excluir este arquivo de plano após conclusão

---

## 7. Notas

- O workflow não prescreve formato do Mapa do Produto (P20).
  O agente deve orientar o humano quando solicitado, mas a
  decisão de conteúdo é sempre do humano.
- A exclusão do arquivo de planejamento na Finalização é uma
  ação destrutiva — o agente deve confirmar com o humano antes
  de excluir (coerência com as regras globais do repo).
