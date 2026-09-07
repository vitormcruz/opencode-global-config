# Metadados do Upstream

repositorio: https://github.com/kayquer/portugues-tecnico-controlado.git
branch: main
description_lang: pt-br
description_note: >
  Mantida em PT-BR (lingua de origem). A description upstream ja vem rica
  em triggers explicitos; copiada sem alteracao na importacao inicial.
commit: cfdffad0ed98cdebfb7f591481889090a4f4e65b
data_commit: 2026-08-17 22:51:45 -0300
sincronizado_em: 2026-09-07 01:35 UTC

## Arquivos sincronizados

- references/ingles.md
- references/lexico.md
- references/ortografia-ptbr.md

## Nao sincronizado

- SKILL.md  (versao adaptada para OpenCode - mantenha manualmente)

## Como atualizar

Execute a partir da raiz do repo:

    opencode-skills sync portugues-tecnico-controlado

Para verificar se ha atualizacoes sem sincronizar:

    opencode-skills sync portugues-tecnico-controlado --check-only

## Licenca

MIT License - Copyright (c) 2026 Kayque Rotondo (kayquer)
https://github.com/kayquer/portugues-tecnico-controlado/blob/main/LICENSE

## Adaptacao da description

Nenhuma adaptacao necessaria: a description de origem ja lista triggers
explicitos ('portugues controlado', 'PTC', 'tira a ambiguidade',
'simplifica esse procedimento', 'reescreve esse runbook', entre outros) e
o frontmatter segue o padrao OpenCode (name + description + version).
O SKILL.md foi copiado literalmente na importacao inicial.

Revisao de seguranca (importacao inicial): APROVADA. Todo o conteudo
copiado (SKILL.md + 3 references) foi lido por completo: sem prompt
injection, sem comandos/executaveis, sem exfiltracao; unicas URLs sao
fontes publicas legitimas (asd-ste100.org, asd-europe.org,
academia.org.br, doras.dcu.ie).
