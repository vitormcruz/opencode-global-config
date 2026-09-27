# Metadados do Upstream

repositorio: https://github.com/mattpocock/skills.git
branch: main
description_lang: pt-br
description_note: Converted to Brazilian Portuguese and enriched with trigger terms.
commit: c55ee46073ed923f86ce59a5eb3b6d895095d1b7
data_commit: 2026-09-18 11:12:29 +0100
sincronizado_em: 2026-09-22 23:30 UTC

## Arquivos sincronizados

- SKILL-MECHANICS.md  (skills/productivity/writing-for-agents/SKILL-MECHANICS.md)

## Nao sincronizado

- SKILL.md  (versao adaptada para OpenCode - mantenha manualmente)

## Como atualizar

Execute a partir da raiz do repo:

    opencode-skills sync writing-for-agents

Para verificar se ha atualizacoes sem sincronizar:

    opencode-skills sync writing-for-agents --check-only

## Licenca

MIT License - Copyright (c) 2026 Matt Pocock
https://github.com/mattpocock/skills/blob/main/LICENSE

## Adaptacao da description

Description converted to Brazilian Portuguese and enriched with trigger
terms, following the canonical pattern "Use ao... Triggers: ...". The body
keeps the upstream English wording and only uses line wrapping at 120 columns.

## Notas locais

- `agents/openai.yaml` contém `display_name` e `short_description` para a UI
  do ecossistema OpenAI. O OpenCode não usa esse arquivo, que não foi copiado.

Conteúdo total revisado na importação (commit citado acima):

- `SKILL.md`: texto metodológico sobre escrita de documentos para agentes
  (context pointers, information hierarchy, completion criteria, leading
  words, pruning). Sem comandos, sem URLs externas, sem instruções dirigidas
  ao agente executivo além do método, sem risco de injection.
- `SKILL-MECHANICS.md`: texto metodológico sobre frontmatter, modo de
  invocação e router skills. Mesmo perfil, limpo.
- `agents/openai.yaml`: apenas `display_name` e `short_description` para UI.
  Limpo; não copiado por irrelevância ao OpenCode.
