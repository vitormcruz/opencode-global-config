---
name: tests-as-spec
description: >
  Use ao discutir intocabilidade de testes na construção, planejar alteração
  de testes existentes, avaliar contradição entre testes, revisar cobertura
  como proteção de spec, ou decidir se um teste pode ser removido ou
  alterado. Testes são a especificação executável do sistema.
  Triggers: "testes como especificação",
  "tests as spec", "teste é especificação", "testes são
  spec", "test specification", "intocável",
  "imutabilidade de teste", "teste contradiz",
  "alterar teste", "remover teste", "spec executável",
  "cobertura como spec". Complementar à skill
  test-driven-development (TDD cobre o ciclo de escrita;
  esta skill cobre o status dos testes após escritos).
---

# Testes como Especificação

Testes aprovados no planejamento são **especificação executável** do
sistema: um teste que passa expressa um comportamento que o sistema **deve**
ter. Alterar ou remover um teste equivale a alterar ou remover um
requisito. Consequências operacionais, por fase:

## Na construção

1. **Código errado, não o teste** — teste falho na construção: corrija o
   código de produção, nunca o teste. O teste é a especificação; o código,
   a implementação.

2. **Testes contraditórios → voltar ao planejamento** — impossível fazer um
   conjunto de testes passar porque eles se contradizem: algum foi
   planejado errado ou um teste preexistente deveria ter sido revisado como
   mudança de spec. Na construção, o teste nunca é alterado para resolver
   contradição; o planejamento é.

3. **Teste que passa sem código novo é suspeito** — teste recém-criado que
   passa de imediato pode não estar testando o que deveria. Investigue
   antes de prosseguir.

## No planejamento

4. **Único momento de alterar testes** — testes existentes são revisados
   apenas no planejamento, como mudança explícita de especificação, com
   registro no arquivo de planejamento (o que mudou, por quê, qual spec foi
   afetada). Novos testes também entram aqui.

5. **Mudança em múltiplos testes = refatoração de spec** — alterar vários
   testes existentes é refatoração de especificação: escopo definido,
   impacto mapeado, aprovação do humano.

6. **Exclusão de teste = exclusão de requisito** — remover um teste remove
   o requisito que ele guarda. Só com decisão explícita no planejamento e
   aprovação do humano, registrando qual requisito deixou de existir e por
   quê.

## Na revisão

7. **Queda de cobertura = spec desprotegida** — cobertura que cai após uma
   mudança significa parte da especificação sem guarda automatizada. Não é
   métrica de vaidade; é alarme. Reporte como achado.

## Aplicação por fase

| Fase | Regras | Ação |
|------|--------|------|
| Planejamento | 4, 5, 6 | Planejar mudanças de testes como mudança de spec, explicitamente |
| Construção | 1, 2, 3 | Nunca alterar teste; contradição → voltar ao planejamento |
| Revisão | 7 | Cobertura como indicador de proteção de spec |

## Relação com a skill TDD

Complementar a `test-driven-development`, sem sobreposição: TDD diz *como
escrever* testes (ciclo red → green → refactor, padrões); esta skill diz
*o que os testes significam* depois de escritos: são especificação,
imutáveis na construção, alteráveis apenas no planejamento.
