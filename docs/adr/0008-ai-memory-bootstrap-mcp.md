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
fixado no código. A imagem permanece `akitaonrails/ai-memory:latest`, conforme
decisão humana. O container solicita publicação de `127.0.0.1:49374`, monta
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
- O bootstrap não atualiza uma imagem já presente; `:latest` pode divergir
  entre máquinas até uma instalação limpa.
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

A fixture Concordion deste ADR expõe `executarVerificacoes()` e `veredito`.
A diretiva `execute` verifica configuração canônica, provisionamento,
condicionalidade nos adapters e cobertura dos testes. A diretiva `assertEquals`
fixa o veredito esperado.

- [Executar as verificações deste ADR](#execute=executarVerificacoes()).
- A spec `docs/specs/Seguranca.md` executa as asserções SEC-01..SEC-11 e
  SEC-21.
- `tests/bootstrap/test_ai_memory_provision.py` usa fakes para download,
  Docker, porta ocupada, idempotência, drift e rollback.
- `tests/harnesses/test_opencode.py` verifica o filtro POSIX e a configuração
  canônica sem credenciais.
- `tests/harnesses/test_copilot.py` verifica o merge aditivo, o backup e a
  preservação de entradas do usuário.
- O veredito agregado da decisão é [pass](#assertEquals=veredito).
