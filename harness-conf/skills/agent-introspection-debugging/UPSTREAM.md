# Metadados do Upstream

repositorio: https://github.com/affaan-m/ECC.git
branch: main
description_lang: pt-br
commit: d29cf651c795869f733669c33e3d33dfd8307d10
data_commit: 2026-08-12 03:58:14 +0000
sincronizado_em: 2026-10-04 22:33 UTC

## Arquivos sincronizados

- LICENSE

## Nao sincronizado

- SKILL.md  (versao adaptada para OpenCode - mantenha manualmente)

## Como atualizar

Execute a partir da raiz do repo:

    harness-skills sync agent-introspection-debugging

Para verificar se ha atualizacoes sem sincronizar:

    harness-skills sync agent-introspection-debugging --check-only

## Licenca

MIT License
- Copyright (c) affaan-m/ECC

## Adaptacao da description

description_note: >
  Description convertida para PT-BR seguindo a convenção das demais skills
  do repo, com triggers de ativação em PT e EN preservados da origem.
  Conversão reversível a pedido do humano.

## Notas locais

### Revisão de segurança da importação

- Data: 2026-10-04.
- Escopo revisado: os três arquivos importados (SKILL.md adaptado
  PT-BR, LICENSE MIT e UPSTREAM.md de metadados), no commit upstream
  d29cf651c795869f733669c33e3d33dfd8307d10.
- Método: leitura integral dos três arquivos, procurando prompt
  injection, comandos ou execução de código, URLs e indícios de
  exfiltração de dados.
- Veredito: limpo, sem achados. SKILL.md contém apenas o protocolo de
  autodiagnóstico (blocos de código são templates de relatório em
  markdown, não comandos executáveis) e nenhuma URL. LICENSE é o texto
  MIT padrão. UPSTREAM.md aponta só para o repo upstream declarado
  (github.com/affaan-m/ECC) e para o comando de sync do próprio repo.
- Recomendação para o próximo sync: repetir a revisão de segurança
  obrigatória antes de aplicar, lendo o diff do conteúdo copiado
  do upstream (references, SKILL.md alterado, LICENSE), sem confiar
  em "só mudou coisa pequena".
