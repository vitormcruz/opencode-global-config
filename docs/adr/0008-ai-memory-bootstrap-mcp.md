# ADR-0008: Provisionamento ai-memory e declaração condicional de MCP

- **Status:** Aceita
- **Data:** 2026-09-27
- **Escopo:** bootstrap, adapters OpenCode e Copilot CLI, configuração e testes

## Contexto

O piloto do ai-memory já usa Docker local, volume persistente e hooks do
OpenCode. A adoção pelo bootstrap exige a mesma configuração em máquinas novas,
sem sudo e sem declarar um MCP que não tenha servidor disponível.

O arquivo `harness-conf/opencode.json` é a fonte canônica. No Linux e no WSL,
`~/.config/opencode/opencode.json` aponta para esse arquivo por symlink. O
adapter não pode editar o alvo do symlink para condicionar a declaração.
O Copilot CLI mantém MCPs em `~/.copilot/mcp-config.json`, que também pode
conter servidores definidos pelo usuário.

## Decisão

O bootstrap provisiona o ai-memory em user-space e grava um marcador somente
depois de validar wrapper, imagem, container, volume e hooks. O bootstrap só
permite a declaração MCP quando esse marcador existe.

O wrapper vem de um release HTTPS do repositório oficial e passa por SHA-256
fixado no código. Após a revalidação de segurança do `sec`, o humano decidiu
“usar a versão nova” em 2026-09-27. A referência linux/amd64 aprovada é:

`akitaonrails/ai-memory:latest@sha256:5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e`

O índice OCI validado tem o digest
`sha256:a626d115e0350afe934954c02c9064d30b708c58316763a9c6674ef5d0c8e3d9`.
A referência preserva a tag `latest`, mas o digest fixa a imagem selecionada.
O container solicita publicação de `127.0.0.1:49374`, monta
`~/.local/share/ai-memory/` em `/data` e usa a rede Docker `internal`.
O bootstrap inspeciona a publicação efetiva. Se o Docker não ativar o bind
loopback nessa rede, o host usa o IPv4 privado do container na bridge
`internal`, depois de validar a conectividade. O bootstrap não configura
credenciais nem provider de LLM.

O adapter OpenCode mantém o symlink canônico quando o provisionamento está
completo e o MCP usa o endpoint loopback. Quando o marcador está ausente, o
adapter substitui o symlink por uma cópia filtrada de `opencode.json`. Quando o
host usa a bridge `internal`, o adapter materializa uma cópia local com o
endpoint ativo. O adapter nunca escreve através do symlink nem altera a fonte
canônica.

O adapter Copilot converte `mcp.ai-memory` para `mcpServers.ai-memory` somente
quando o marcador existe. O merge preserva outras entradas. Uma entrada
`ai-memory` diferente já existente bloqueia a escrita e permanece intacta.
Antes de cada alteração, o adapter cria backup de `mcp-config.json`.

Quando Docker está ausente ou o provisionamento falha, o bootstrap remove o
marcador, desativa os hooks gerados e remove a declaração ai-memory gerenciada
do Copilot. O bootstrap informa uma instrução user-space e não habilita MCP em
nenhum adapter.

O comando `opencode-bootstrap --rollback-ai-memory` para e remove o container,
remove os wrappers e hooks gerados, remove as declarações gerenciadas, restaura
`opencode.jsonc` do backup e preserva o volume de dados.

## Consequências

- Sem Docker, o bootstrap continua configurando os harnesses sem o MCP
  ai-memory. O retorno não indica falha quando o único impedimento é Docker
  ausente.
- No POSIX, `opencode.json` é um arquivo regular filtrado enquanto o marcador
  não existe. A configuração canônica permanece intacta.
- Quando a publicação loopback não fica ativa na rede `internal`, o endpoint
  MCP usa o IPv4 privado do container. O bootstrap confirma a conexão do host
  antes de habilitar as declarações nos harnesses; a configuração OpenCode
  local registra o endpoint e não altera o arquivo canônico.
- O wrapper tem checksum esperado no código. Mudança de checksum bloqueia a
  substituição e informa como fazer backup antes do upgrade.
- O bootstrap não atualiza uma imagem já presente. A imagem fixada por digest
  não acompanha mudanças implícitas da tag `latest`.
- Cada upgrade exige decisão humana e atualização explícita dos pins do wrapper,
  do índice OCI e da plataforma, após revalidação de segurança. Esse processo
  ocorreu em 2026-09-27, quando o humano aprovou “usar a versão nova”.
- A rede internal impede rota de saída padrão para o container. Quando o Docker
  publica a porta, o host acessa pelo loopback. Sem publicação efetiva, o host
  acessa o IPv4 privado pela bridge internal; nenhum listener do host é aberto.
- A wiki persiste em texto claro no diretório local. O rollback preserva esse
  diretório para evitar perda de memória. No POSIX, o bootstrap restringe o
  acesso ao usuário que executa o provisionamento.
- O plugin de hooks é gerado pelo instalador oficial e não é versionado.
- Os hooks de compactação continuam limitados ao OpenCode. O Copilot recebe
  somente o endpoint MCP.

## Alternativas consideradas

- **Declarar MCP em todos os casos:** rejeitada. Uma máquina sem Docker teria
  configuração ativa sem servidor.
- **Editar o `opencode.json` canônico na máquina:** rejeitada. A edição
  atravessaria o symlink POSIX e alteraria a fonte versionada.
- **Manter o symlink e sobrescrever seu alvo:** rejeitada. O adapter não pode
  editar symlinks nem alterar a fonte canônica.
- **Configuração local adicional para OpenCode:** rejeitada nesta
  implementação. O carregamento conjunto de `opencode.json` e `opencode.jsonc`
  não faz parte deste contrato; a cópia filtrada tem resultado testável.
- **Sobrescrever `mcpServers.ai-memory` no Copilot:** rejeitada. A entrada pode
  pertencer ao usuário e não pode ser substituída sem decisão explícita.
- **Rede Docker com egress aberto:** rejeitada. O container não precisa de rota
  externa durante a operação normal.

## Asserções executáveis

A fixture lê os valores das tabelas e os compara com a configuração, o código
e os testes existentes. A spec `docs/specs/Seguranca.md` também executa os
requisitos de segurança.

### A8-01: declaração MCP sem credenciais (origem: [Decisão](#decisão))

| Entrada | Resultado esperado |
|---|---|
| Arquivo de configuração canônica | `harness-conf/opencode.json` |
| Campo de servidores MCP | `mcp` |
| Chave do servidor | `ai-memory` |
| URL MCP canônica | `http://127.0.0.1:49374/mcp` |
| Campos de credencial proibidos | `headers,environment,token,apiKey` |
| Veredito | [pass](- "?=vereditoA801") |

[Executar A8-01](- "verificarA801()").

### A8-02: marcador, isolamento e pins (origem: [Decisão](#decisão))

| Entrada | Resultado esperado |
|---|---|
| Marcador de prontidão | `.bootstrap-provisioned` |
| Chamada de gravação do marcador | `_write_ready_marker(context.paths, network_is_owned)` |
| SHA-256 do wrapper | `49c965a0319dbe9c525d552a9a4c8b3464e5dd278e36d5dc7a03edee8b5502e6` |
| Digest do índice OCI | `a626d115e0350afe934954c02c9064d30b708c58316763a9c6674ef5d0c8e3d9` |
| Tag da imagem | `akitaonrails/ai-memory:latest` |
| Digest linux/amd64 | `5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e` |
| Opção de rede isolada | `--internal` |
| Teste dos pins aprovados | `test_ai_memory_upstream_release_pins_match_reviewed_artifacts` |
| Veredito | [pass](- "?=vereditoA802") |

[Executar A8-02](- "verificarA802()").

### A8-03: adapters condicionais (origem: [Decisão](#decisão))

| Entrada | Resultado esperado |
|---|---|
| Função de filtro OpenCode | `filter_ai_memory_config` |
| Função de gate do marcador | `is_ai_memory_provisioned` |
| Método de materialização filtrada | `materialize_filtered_config` |
| Método de merge Copilot | `_sync_mcp_config` |
| Teste OpenCode sem provisionamento | `test_opencode_without_provisioned_ai_memory_filters_symlink_config` |
| Teste Copilot com servidor existente | `test_copilot_adapter_merges_ai_memory_without_losing_existing_servers` |
| Teste Copilot sem provisionamento | `test_copilot_adapter_removes_ai_memory_entry_when_provisioning_is_incomplete` |
| Veredito | [pass](- "?=vereditoA803") |

[Executar A8-03](- "verificarA803()").

[Executar as verificações deste ADR](- "executarVerificacoes()").

O veredito agregado é [pass](- "?=veredito").
