---
name: tests-as-spec
description: >
  Testes como especificação executável do sistema. Use
  quando: discutindo imutabilidade de testes na construção,
  planejando alteração de testes existentes, avaliando
  contradições entre testes, revisando cobertura como
  proteção de spec, ou decidindo se um teste pode ser
  removido/alterado. Triggers: "testes como especificação",
  "tests as spec", "teste é especificação", "testes são
  spec", "test specification", "intocável",
  "imutabilidade de teste", "teste contradiz",
  "alterar teste", "remover teste", "spec executável",
  "cobertura como spec". Complementar à skill
  test-driven-development (TDD cobre o ciclo de escrita;
  esta skill cobre o status dos testes após escritos).
---

# Testes como Especificação

## Princípio

Testes aprovados no plano são **especificação executável**
do sistema. Um teste que passa expressa um comportamento
que o sistema **deve** ter. Alterar ou remover um teste
equivale a alterar ou remover um requisito.

Esse princípio tem consequências operacionais em todas
as fases do desenvolvimento.

---

## Consequências operacionais

### Na construção

1. **Código errado, não teste** — se um teste falha na
   construção, o código de produção é quem deve ser
   alterado. Nunca o teste. O teste é a especificação;
   o código é a implementação.

2. **Testes contraditórios → voltar ao planejamento** —
   se não há como fazer um conjunto de testes passar
   porque eles se contradizem, é necessário voltar ao
   planejamento. Algum teste foi planejado errado ou
   um teste preexistente deveria ter sido revisado como
   mudança de spec mas não foi considerado. Na
   construção, o teste **nunca** é alterado para
   resolver contradição — o plano é.

3. **Teste que passa sem código novo é suspeito** — se
   um teste recém-criado passa imediatamente sem
   nenhuma implementação nova, ele pode não estar
   testando o que deveria. Investigar antes de
   prosseguir.

### No planejamento

4. **Único momento de alterar testes** — testes
   existentes só podem ser revisados durante o
   planejamento, como mudança explícita de
   especificação. Novos testes podem ser adicionados
   e testes antigos podem ser modificados, mas apenas
   nesta fase e com registro no arquivo de planejamento
   (o quê mudou, por quê, qual spec foi afetada).

5. **Alteração de múltiplos testes = refatoração de
   spec** — quando a mudança envolve vários testes
   existentes, é uma refatoração de especificação.
   Deve ser planejada como tal: escopo definido,
   impacto mapeado, aprovação do humano.

6. **Exclusão de teste = exclusão de requisito** —
   remover um teste é equivalente a remover um
   requisito do sistema. Só pode acontecer com
   decisão explícita no planejamento e aprovação do
   humano. Registrar qual requisito deixou de existir
   e por quê.

### Na revisão

7. **Queda de cobertura = spec perdeu proteção** — se
   a cobertura cai após uma mudança, significa que
   parte da especificação perdeu sua guarda
   automatizada. Não é métrica de vaidade; é alarme
   de spec desprotegida. Reportar como achado.

---

## Aplicação por fase

| Fase | Regras aplicáveis | Ação |
|------|-------------------|------|
| Planejamento | 4, 5, 6 | Planejar mudanças de spec (testes) explicitamente |
| Construção | 1, 2, 3 | Nunca alterar teste; contradição → voltar ao planejamento |
| Revisão | 7 | Cobertura como indicador de proteção de spec |

---

## Relação com skill TDD

Esta skill **complementa** `test-driven-development`:
- **TDD** cobre o ciclo de escrita (red → green →
  refactor) e padrões de teste.
- **tests-as-spec** cobre o **status** dos testes após
  escritos: são especificação, imutáveis na construção,
  alteráveis apenas no planejamento.

Não há sobreposição: TDD diz *como escrever* testes;
esta skill diz *o que testes significam* depois de
escritos.
