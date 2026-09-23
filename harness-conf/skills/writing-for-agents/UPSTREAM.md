# Metadados do Upstream

repositorio: https://github.com/mattpocock/skills
branch: main
commit: c55ee46073ed923f86ce59a5eb3b6d895095d1b7
data_commit: 2026-09-18 11:12:29 +0100
sincronizado_em: 2026-09-22 23:30 UTC

## Arquivos sincronizados

- SKILL-MECHANICS.md  (referência copiada fielmente do upstream, path
  `skills/productivity/writing-for-agents/SKILL-MECHANICS.md`)

## Nao sincronizado

- SKILL.md  (versão adaptada para OpenCode - description em PT-BR com
  triggers; corpo em inglês apenas com reflow a 120 colunas; mantenha
  manualmente)
- agents/openai.yaml  (metadata de interface do ecossistema OpenAI; sem uso
  no OpenCode, não copiado)

## Como atualizar

O sync automático via `opencode-skills sync` ainda não cobre este upstream
(registro no CLI pendente). Fluxo manual, a partir da raiz do repo:

    bash -c 'git clone --depth=1 https://github.com/mattpocock/skills /tmp/mattpocock-skills && cp /tmp/mattpocock-skills/skills/productivity/writing-for-agents/SKILL-MECHANICS.md harness-conf/skills/writing-for-agents/SKILL-MECHANICS.md && git -C /tmp/mattpocock-skills log -1 --format="%H %ci"'

O comando acima é mantido em linha única por requisito do parser
`_documented_commands` deste repo, que espera cada comando documentado numa
única linha iniciada pelo executável. Migrar para um script versionado com
`--yes` está previsto para a fase DEVFLOW, quando o sync for registrado no
CLI.

Depois, atualize `commit`, `data_commit` e `sincronizado_em` no topo deste
arquivo e confira se mudanças upstream afetam o `SKILL.md` local. O
`SKILL.md` nunca é sobrescrito pelo sync.

Antes de copiar qualquer conteúdo novo do upstream, revisão de segurança
obrigatória: ler todo o conteúdo procurando prompt injection, comandos
suspeitos, URLs e exfiltração.

## Segurança na importação (2026-09-22)

Conteúdo total revisado na importação (commit citado acima):

- `SKILL.md`: texto metodológico sobre escrita de documentos para agentes
  (context pointers, information hierarchy, completion criteria, leading
  words, pruning). Sem comandos, sem URLs externas, sem instruções dirigidas
  ao agente executivo além do método, sem risco de injection.
- `SKILL-MECHANICS.md`: texto metodológico sobre frontmatter, modo de
  invocação e router skills. Mesmo perfil, limpo.
- `agents/openai.yaml`: apenas `display_name` e `short_description` para UI.
  Limpo; não copiado por irrelevância ao OpenCode.

## Licenca

MIT License - Copyright (c) 2026 Matt Pocock
https://github.com/mattpocock/skills/blob/main/LICENSE

## Adaptacao da description

description_lang: pt-br
description_note: >
  Description converted to Brazilian Portuguese and enriched with trigger
  terms (repo decision for imported skills), following the canonical
  pattern "Use ao... Triggers: ...". Body kept in English (upstream
  wording); only line-wrapped to 120 columns without changing words.
