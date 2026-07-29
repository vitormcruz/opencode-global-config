# Mensagens Pré-definidas — Curadoria

## docs/README.md ou Harness não encontrado(s)

Este projeto ainda não possui **docs/README.md** e/ou
**Harness por agente** — os dois artefatos que sustentam
este workflow de desenvolvimento.

O **docs/README.md** é o contrato mínimo de especificação
e documentação do projeto: define o quê deve existir, como é
confeccionado e onde fica. Contém 3 seções obrigatórias:
Definição de Escopo, Elementos de Especificação e
Estratégias de Indexação de Código. Sem ele, eu (curador)
não tenho critério objetivo para validar aderência.

O **Harness por agente** traduz regras de qualidade em
scripts de contenção executados por cada agente, usando
ferramentas preferencialmente determinísticas. Fica no
topo do `AGENTS.md` do projeto. Transforma validação em
verificação reproduzível e automática.

**Recomendação:** interrompa o workflow e chame o agente
`curador-produto-editor` para o setup inicial — ele guia o
processo seção por seção com sua aprovação a cada etapa.
