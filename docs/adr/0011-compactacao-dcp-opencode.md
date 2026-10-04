# ADR-0011: Compactação de contexto por decisão do agente

- **Status:** Aceita
- **Data:** 2026-10-04
- **Escopo:** `harness-conf/dcp.jsonc`, `harness-conf/AGENTS.base.md`,
  `src/opencode_config/harnesses/opencode.py`, `README.md`

## Contexto

Sessões longas de agentes enchem a janela de contexto. Compactar é uma
decisão de julgamento: o agente sabe quando o histórico acumulado já é
grande e parou de servir à tarefa corrente; nenhum número fixo de
tokens captura esse juízo, e um limite arbitrário ou comprime cedo
demais ou deixa o contexto crescer sem necessidade.

A compactação nativa do OpenCode (`/compact` e a auto-compactação por
limite da janela) é destrutiva ou reativa: reescreve o histórico ou só
age perto do estouro. O plugin npm `@tarquinen/opencode-dcp` registra a
tool `compress`: o próprio agente escolhe os trechos antigos, escreve
os resumos e o histórico persistido permanece íntegro (a substituição
por placeholders acontece só no envio ao modelo). Fora do modo manual
do plugin, a tool fica à disposição do agente, que a aciona por
iniciativa própria; o plugin também aceita configurar os gatilhos
automáticos, que podem ficar inertes.

Harnesses variam em capacidade de compactação, e a política precisa
funcionar em qualquer um deles.

## Decisão

A compactação de contexto é iniciada pelo agente, por julgamento, sem
limite fixo de tokens: o agente comprime quando o contexto está grande
e o conteúdo antigo já não serve à tarefa corrente. A política é
definida por capacidade do harness, sem enumerar produtos:

1. **Tool que preserva o histórico**: o agente usa a própria tool
   (caso do OpenCode com o DCP: `compress`), comprimindo trechos
   antigos em resumo sem apagar o histórico.
2. **Apenas comando manual**: o agente pede ao humano, já com a
   mensagem de compactação redigida (o que comprimir e como).
3. **Sem compactação ao alcance do agente**: o agente salva o estado
   essencial em arquivo e segue em sessão nova, lendo só o que importa;
   não pede compactação ao humano.

No OpenCode, o `dcp.jsonc` canônico não configura nenhum gatilho
operante: os limites de contexto do plugin existem apenas como valores
inertes (inatingíveis, portanto sem nudges) e o modo manual do plugin
permanece desligado, pois ele bloqueia a execução da tool pelo agente
até um comando do humano. Assim, a única via de compressão é a decisão
do próprio agente, guiado pela política da seção "Compactação de
contexto" do `AGENTS.base.md`. O arquivo é sincronizado pelo adapter
OpenCode para o user-space (symlink POSIX, cópia sincronizada
Windows), nas tuplas de destinos das strategies, sem mudança no
contrato `HarnessAdapter`. O Copilot não recebe destino DCP.

A auto-compactação nativa do OpenCode permanece ativa como rede de
segurança: se disparar, uma fronteira foi perdida.

## Consequências

- A chamada de compactação acontece no momento certo pelo critério de
  quem vê o contexto: o próprio agente, guiado pela política da seção
  "Compactação de contexto" do `AGENTS.base.md`.
- Nenhum parâmetro numérico operante para calibrar por modelo ou
  janela; a manutenção do comportamento é textual (a política), não de
  constantes. Os limites inertes no config blindam contra defaults do
  upstream em bump.
- O gatilho automático do DCP (nudges acima de limite) fica inoperante;
  a decisão do agente é o único caminho da compressão.
- O modo manual do plugin não serve a este desenho: além de suprimir o
  caminho automático, ele exige comando do humano antes de cada
  compressão, o que retiraria do agente a decisão.
- O histórico persistido fica íntegro, o que permite auditoria
  pós-fato pelo banco de sessões.
- Rollback em dois níveis: `compress.permission = "deny"`
  desregistra a tool sem desinstalar; remoção completa tira a spec do
  array `plugin`, o `dcp.jsonc` e o destino do adapter.
- AGPL-3.0-or-later: o repo declara apenas a string de spec e mantém
  config autoral; nenhuma distribuição de código do plugin.

## Alternativas consideradas

- Gatilho automático por limite de contexto (default do plugin):
  rejeitada porque desloca a decisão para um número; o limite certo
  varia com a tarefa e o modelo, e o nudge empurra compressão
  mecânica, não julgamento. A compressão por iniciativa do agente
  cobre o caso com menos parâmetros.
- Modo manual do plugin (`manualMode.enabled`): rejeitada porque, no
  plugin 3.1.15, ele não só desliga o gatilho automático como BLOQUEIA
  a execução da tool pelo agente até que um comando do humano a
  habilite (evidenciado na validação funcional: o agente tentou
  comprimir seguindo a política e o plugin recusou). O agente deixaria
  de poder chamar a compressão, contrariando o requisito.
- Manter `/compact` como mecanismo principal: rejeitada porque é
  comando de usuário, não é acionável pelo agente em sessão autônoma e
  reescreve o histórico, sem base para auditoria.
- Estender a compactação ao Copilot CLI via MCP de resumos: rejeitada
  porque o MCP gera resumos sem remover mensagens da janela do host;
  sem evicção não há recuperação de tokens. Nesse harness vale o degrau
  da política: nova sessão com estado salvo em arquivo.

## Asserções executáveis

A fixture Concordion deste ADR expõe `executarVerificacoes()` e
`veredito`. A diretiva `execute` executa as verificações da decisão. A
diretiva `assertEquals` fixa o veredito esperado.

- [Executar as verificações deste ADR](#execute=executarVerificacoes()).
- A fixture valida a decisão implementada: a spec do plugin está
  pinada no array `plugin` de `harness-conf/opencode.json`; o
  `harness-conf/dcp.jsonc` não opera em modo manual
  (`manualMode` ausente ou desligado) e não tem gatilho operante
  (limites de contexto só como valores inertes), com `autoUpdate`
  desligado e gate `allow` na tool `compress`; as duas strategies do
  OpenCode declaram o destino `dcp.jsonc` e o adapter Copilot não
  declara nenhum destino DCP; o `README.md` documenta o plugin para o
  humano.
- O veredito agregado da implementação é [pass](#assertEquals=veredito).
