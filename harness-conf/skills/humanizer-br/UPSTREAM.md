# Metadados do Upstream

repositorio: https://github.com/carlosafjr-dev/humanizer-br.git
branch: master
description_lang: pt-br
description_note: >
  Mantida em PT-BR (lingua de origem) e enriquecida com triggers
  explicitos, incluindo o uso em toda comunicacao do chat (secao "Tom
  natural" do AGENTS.base.md).
commit: 161aef327d7f72a06e466e5485f8afa73e770805
data_commit: 2026-04-09 12:31:31 -0300
sincronizado_em: 2026-09-07 01:35 UTC

## Arquivos sincronizados

- references/aprofundador.md  (origem: skills/aprofundador/SKILL.md)
- LICENSE

## Nao sincronizado

- SKILL.md  (versao adaptada para OpenCode - mantenha manualmente)

## Como atualizar

Execute a partir da raiz do repo:

    opencode-skills sync humanizer-br

Para verificar se ha atualizacoes sem sincronizar:

    opencode-skills sync humanizer-br --check-only

## Licenca

MIT License - Copyright (c) 2026 carlosafjr-dev
https://github.com/carlosafjr-dev/humanizer-br/blob/master/LICENSE

## Adaptacao da description

A description de origem nao tinha triggers explicitos. A versao local foi
enriquecida com triggers ("humanizar", "texto parece IA", "remover cliches
de IA", "escrita natural", "tom natural", "anti-IA", "texto robotico",
"densidade intelectual", entre outros) e com o caso de uso de chat
(comunicacao natural em toda a sessao). O corpo ganhou a secao final
"Modulo complementar - Aprofundador" apontando para
references/aprofundador.md.

Revisao de seguranca (importacao inicial): APROVADA. Todo o conteudo
copiado (SKILL.md + skills/aprofundador/SKILL.md + LICENSE) foi lido por
completo: sem prompt injection, sem comandos/executaveis, sem URLs e sem
exfiltracao. Referencias bibliograficas apenas textuais.
