---
description: Atualiza skills com UPSTREAM.md uma por vez
---

Atualize as skills atualizaveis deste repositorio uma por vez.

Siga este fluxo estritamente:

1. Descubra as skills atualizaveis executando `bash scripts/skills/list-updatable`.
2. Se nao houver nenhuma skill, informe claramente que nao existem skills atualizaveis e encerre.
3. Processe as skills exatamente na ordem retornada pelo helper.
4. Para cada skill:
   - execute `bash scripts/skills/update-upstream-skill "<skill>"`
   - atualize somente essa skill antes de qualquer pergunta sobre a proxima
   - produza um resumo curto com `Skill`, `Resultado` e `Detalhe`
5. Depois de concluir cada skill, se ainda houver outra pendente, pergunte ao humano usando `functions.question` se deseja continuar.
6. A pergunta entre skills deve ter apenas estas opcoes:
   - `Continuar`
   - `Parar`
7. Se o humano responder `Parar`, encerre imediatamente.
8. Se o helper reportar `no-clear-update-flow`, `ambiguous-update-flow`, `non-interactive-mode-not-found` ou `error`, resuma isso brevemente e ainda pergunte se deve seguir para a proxima skill.
9. Nao atualize varias skills em lote.
10. Nao pule a confirmacao entre uma skill e outra.
11. Nao invente mecanismos de sync fora do que estiver documentado no `UPSTREAM.md` e resolvido pelos helpers.
12. Nao rode comandos em paralelo.

Formato esperado apos cada skill:

- Skill: `<nome>`
- Resultado: `<status curto>`
- Detalhe: `<1 linha>`

Ao final, informe tambem quando nao houver mais skills pendentes.
