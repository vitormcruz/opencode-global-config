# Plano: Preâmbulo determinístico do curador-produto

**Resumo:**
Quando o curador detecta ausência de Mapa e/ou Harness, exibe uma mensagem pré-definida (copiar/colar literal) explicando ambos os conceitos, e depois sugere ao humano parar o workflow e chamar `editor-mapa-produto` na mão.

---

## Decisões alinhadas

- Mensagem única cobrindo Mapa + Harness (não separadas)
- Sempre exibida integralmente, mesmo se apenas Harness ausente (reforço pedagógico)
- Tom: direto e objetivo, 3–5 parágrafos curtos
- Local: `agents/references/mensagens-curadoria.md`
- Comportamento pós-mensagem: curador NÃO delega automaticamente ao editor; sugere ao humano parar e chamar o editor na mão
- Textos propostos pelo agente, revisados pelo humano
- **Texto final aprovado** (versão resumida, sem linha "Juntos"):

```
## ⚠️ Mapa do Produto ou Harness não encontrado(s)

Este projeto ainda não possui **Mapa do Produto** e/ou
**Harness por agente** — os dois artefatos que sustentam
este workflow de desenvolvimento.

O **Mapa do Produto** é o contrato mínimo de especificação
e documentação do projeto: define o quê deve existir, como é
confeccionado e onde fica. Sem ele, eu (curador) não tenho
critério objetivo para validar aderência.

O **Harness por agente** traduz regras de qualidade em
scripts de contenção executados por cada agente, usando
ferramentas preferencialmente determinísticas. Transforma
validação em verificação reproduzível e automática.

**Recomendação:** interrompa o workflow e chame o agente
`editor-mapa-produto` para o setup inicial — ele guia o
processo seção por seção com sua aprovação a cada etapa.
```

---

## Etapas do plano

### 1. Criar arquivo de mensagens
- Criar `agents/references/mensagens-curadoria.md` com o texto acima

### 2. Atualizar curador-produto.md
- Adicionar seção `## Mensagens Pré-definidas` referenciando o arquivo acima
- Alterar item 4 ("Detectar ausência") de "detecta → delega ao editor" para "detecta → exibe mensagem literal → sugere ao humano chamar editor na mão"
- Manter permissão `task: editor-mapa-produto: allow` (útil em outros cenários, como Mapa desatualizado), mas a regra de ausência agora é preâmbulo + sugestão manual

### 3. Atualizar workflow-curadoria.md
- No fluxo e no diagrama Mermaid, inserir etapa de preâmbulo entre DETECÇÃO e delegação: curador exibe mensagem → sugere parar → humano decide
- Documentar a existência do arquivo de mensagens e a regra de exibição integral
- Atualizar a nota da seção "Filosofia" para apontar para
  `agents/references/principios-documentacao.md` em vez de
  referenciar o `curador-produto.md`

### 4. Criar arquivo de referência de princípios de documentação
- Criar `agents/references/principios-documentacao.md` com o conteúdo
  da seção `## Princípios de Documentação` do `curador-produto.md`
  (Filosofia, Práticas, Exemplos por ecossistema, Contexto do projeto
  e Recomendação padrão) — fonte única, autossuficiente
- No `curador-produto.md`: substituir o conteúdo embutido por instrução
  de consultar `agents/references/principios-documentacao.md`
- No `editor-mapa-produto.md`: adicionar instrução de consultar
  `agents/references/principios-documentacao.md`; declarar que ao
  interagir com o humano durante a construção do Mapa (fluxo seção
  por seção), o agente adota comportamento de entrevistador conforme
  a skill `grill-me`
- Nos agentes que produzem documentação como parte do trabalho
  (`eng-software`, `dba`, `front`, `qa`, `sec`, `rev`): adicionar
  instrução de consultar `agents/references/principios-documentacao.md`
  ao escrever ou revisar documentação

---

## Arquivos relevantes
- `agents/references/mensagens-curadoria.md` — **CRIAR**
- `agents/references/principios-documentacao.md` — **CRIAR**
- `agents/curador-produto.md` — **MODIFICAR** (item 4, nova seção,
  permissões, substituir princípios embutidos por referência ao arquivo)
- `docs/workflow-curadoria.md` — **MODIFICAR** (fluxo + diagrama)
- `agents/editor-mapa-produto.md` — **MODIFICAR** (adicionar referência
  ao arquivo de princípios)
- `agents/eng-software.md` — **MODIFICAR** (adicionar referência ao
  arquivo de princípios)
- `agents/dba.md` — **MODIFICAR** (adicionar referência ao arquivo de
  princípios)
- `agents/front.md` — **MODIFICAR** (adicionar referência ao arquivo de
  princípios)
- `agents/qa.md` — **MODIFICAR** (adicionar referência ao arquivo de
  princípios)
- `agents/sec.md` — **MODIFICAR** (adicionar referência ao arquivo de
  princípios)
- `agents/rev.md` — **MODIFICAR** (adicionar referência ao arquivo de
  princípios)

## Verificação
- Confirmar instrução de copiar/colar literal no curador
- Confirmar diagrama de sequência atualizado no workflow
- `make test` para garantir que nada quebrou

## Consideração
Permissão task do curador→editor: recomendo **manter** — o curador pode precisar delegar em cenários de Mapa *desatualizado*. Apenas na detecção de **ausência** total o comportamento muda para preâmbulo + sugestão manual.
