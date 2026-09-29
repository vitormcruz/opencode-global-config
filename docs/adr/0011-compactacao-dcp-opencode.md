# ADR-0011: Compactação DCP como mecanismo preferido no OpenCode

- **Status:** Aceita
- **Data:** 2026-09-29
- **Escopo:** `harness-conf/opencode.json`, `harness-conf/dcp.jsonc`,
  `src/opencode_config/harnesses/opencode.py`, `README.md`

## Contexto

Sessões longas enchem a janela de contexto. O `/compact` nativo do
OpenCode é comando de usuário: o agente não consegue dispará-lo e o
histórico é reescrito no processo. A política vigente orientava os
agentes a preferir mecanismos automatizados (auto-compactação por
threshold, nova sessão com estado persistido) e a pedir `/compact` ao
humano como último recurso.

O plugin npm `@tarquinen/opencode-dcp` registra a tool `compress`: o
próprio agente decide quando comprimir, escolhe os trechos e escreve os
resumos; nudges empurram a chamada quando o contexto cruza o limite
configurado. O histórico persistido nunca é alterado: a substituição
por placeholders acontece só no envio ao modelo. O plugin vale apenas
no OpenCode. No GitHub Copilot CLI a compactação é host-level e não é
acionável pelo agente; recuperar tokens exige re-seed em chat novo.

A presença do plugin no repo se dá pelo config canônico
(`harness-conf/opencode.json`, spec pinada no array `plugin`) e pela
config própria do plugin (`harness-conf/dcp.jsonc`), ambas
materializadas pelo bootstrap para o user-space do OpenCode.

## Decisão

No OpenCode com o plugin DCP ativo, a tool `compress` é o mecanismo
automatizado preferido de compactação; `/compact` passa a fallback. A
auto-compactação nativa (`compaction.auto`) permanece rede de
segurança. No Copilot CLI nada muda: compactação host-level, com
recuperação por re-seed em chat novo.

O adapter OpenCode estende os destinos de sincronização com
`harness-conf/dcp.jsonc` → `dcp.jsonc` no user-space, nas duas
strategies (symlink POSIX e cópia sincronizada Windows). O contrato
`HarnessAdapter` em si não muda: o destino entra nas tuplas de
destinos, forma canônica de variação por SO. O Copilot fica fora do
escopo: nenhum destino DCP no adapter Copilot.

## Consequências

- O agente comprime contexto sem depender de comando do humano; os
  nudges do plugin puxam a chamada quando o contexto cruza o limite.
- `/compact` segue disponível como fallback e a auto-compactação
  nativa segue ativa; thresholds do DCP posicionados abaixo do gatilho
  nativo mantêm o plugin como primeiro mecanismo.
- O histórico persistido fica íntegro: placeholders só na requisição,
  o que permite auditoria pós-fato pelo banco de sessões.
- Rollback em dois níveis: `compress.permission = "deny"` desregistra
  a tool sem desinstalar; remoção completa tira a spec do array
  `plugin`, o `dcp.jsonc` e o destino do adapter.
- AGPL-3.0-or-later: o repo declara apenas a string de spec e mantém
  config autoral; nenhuma distribuição de código do plugin.
- A política de compactação nos textos dos agentes (`AGENTS.base.md`
  e docs de workflow) é atualizada em mudança separada, que depende de
  aprovação humana.

## Alternativas consideradas

- Manter `/compact` como mecanismo principal: rejeitada porque é
  comando de usuário, não é acionável pelo agente em sessão autônoma e
  apresentou regressão conhecida de contexto.
- Estender a compactação ao Copilot CLI via MCP de resumos: rejeitada
  porque o MCP gera resumos sem remover mensagens da janela do host;
  sem evicção não há recuperação de tokens, e o re-seed em chat novo
  já é o comportamento atual.
- Criar destino genérico de config no contrato `HarnessAdapter`:
  rejeitada porque a variação por SO já é canonicamente expressa nas
  tuplas de destinos das strategies; mudar a interface sem uma segunda
  implementação que a exija é especulação.

## Asserções executáveis

A fixture Concordion deste ADR expõe `executarVerificacoes()` e
`veredito`. A diretiva `execute` executa as verificações da decisão. A
diretiva `assertEquals` fixa o veredito esperado.

- [Executar as verificações deste ADR](#execute=executarVerificacoes()).
- A fixture valida a decisão implementada: a spec do plugin está
  pinada no array `plugin` de `harness-conf/opencode.json`; o
  `harness-conf/dcp.jsonc` existe com `autoUpdate` desligado e gate
  `allow` na tool `compress`; as duas strategies do OpenCode declaram
  o destino `dcp.jsonc` e o adapter Copilot não declara nenhum destino
  DCP; o `README.md` documenta o plugin para o humano.
- O veredito agregado da implementação é [pass](#assertEquals=veredito).
