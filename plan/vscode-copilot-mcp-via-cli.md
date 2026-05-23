# Plano: VS Code Copilot Chat usando MCP via Linha de Comando (CLI)

**Data:** 22/05/2026
**Status:** Análise concluída — viável

---

## 1. Resumo Executivo

É **viável** fazer o VS Code Copilot Chat interagir com servidores MCP através
de invocação por linha de comando. O Copilot Chat, em **Agent mode**, possui a
ferramenta `run_in_terminal` que permite executar comandos shell. Combinando
isso com um **wrapper CLI** que traduz chamadas de shell para o protocolo
MCP (JSON-RPC over stdio), é possível usar qualquer servidor MCP como se fosse
uma ferramenta de linha de comando.

Este plano detalha exclusivamente essa abordagem CLI.

---

## 2. Análise de Viabilidade

### 2.1. Como o Copilot Chat executa comandos CLI

O VS Code Copilot Chat, operando em **Agent mode**, possui acesso à ferramenta
`run_in_terminal` que permite:

- Executar comandos shell no terminal integrado do VS Code
- Capturar stdout/stderr dos comandos executados
- Executar comandos em foreground ou background
- Suporte a comandos multiline (heredocs, pipes, chaining)

**Limitação importante:** O Copilot Chat não possui um mecanismo nativo de
"tool use" que invoque processos externos diretamente — ele depende do
`run_in_terminal` para qualquer interação com o sistema operacional. Isso
significa que o Copilot precisa ser **instruído explicitamente** a usar os
comandos CLI do wrapper MCP.

### 2.2. Como o MCP funciona via CLI

O protocolo MCP define dois transportes principais:

| Transporte | Descrição | Uso típico |
|---|---|---|
| **stdio** | Cliente spawns servidor como subprocesso; comunicação via stdin/stdout com JSON-RPC | Servidores locais |
| **Streamable HTTP** | Comunicação via HTTP POST com SSE opcional | Servidores remotos |

O transporte **stdio** é o mais relevante para uso CLI: o cliente lança o
servidor como processo filho, envia mensagens JSON-RPC pelo stdin e lê
respostas pelo stdout. Mensagens são delimitadas por newlines.

O ciclo de vida de uma chamada MCP via stdio:

1. Cliente envia `initialize` (negociação de versão e capabilities)
2. Servidor responde com capabilities suportadas
3. Cliente envia `initialized` (notificação)
4. Cliente descobre ferramentas com `tools/list`
5. Cliente chama ferramenta com `tools/call`
6. Servidor retorna resultado
7. Cliente fecha stdin para encerrar

### 2.3. Viabilidade da integração Copilot Chat ↔ MCP via CLI

**Viável, com as seguintes condições:**

- O Copilot Chat precisa ser instruído a usar comandos CLI específicos
- É necessário um wrapper CLI que traduza chamadas de shell para JSON-RPC MCP
- O wrapper deve lidar com o ciclo de vida do servidor MCP (spawn, init, call,
  shutdown)
- Instruções customizadas (`.github/copilot-instructions.md`) são necessárias
  para guiar o Copilot a usar o wrapper corretamente

---

## 3. Wrappers CLI Encontrados

Estas ferramentas convertem ferramentas MCP em comandos CLI invocáveis,
exatamente o que é necessário para esta abordagem:

| Ferramenta | Linguagem | Destaques | URL |
|---|---|---|---|
| **mcp-cli-skill** | Python | Shell composition, pipe output, stdin JSON, suporta stdio + HTTP | github.com/wise-toddler/mcp-cli-skill |
| **mcp2cli** | Bun | Daemon + CLI, zero context cost, batch calls, modo remoto | github.com/rodaddy/mcp2cli |
| **mcpshim** | Go | Daemon + CLI, Unix socket, flags mapeiam para parâmetros MCP | mcpshim.dev |
| **mcp (avelino)** | Go | Binário único, proxy mode, suporte a registry | github.com/avelino/mcp |
| **mcpc (Apify)** | TS | Sessions, modo interativo + code mode, x402 payments | github.com/apify/mcp-cli |
| **mcpwrap** | TS | Lê config do OpenCode, OAuth reuso, schema-based CLI args | github.com/nanasi-apps/mcpwrap |
| **mcp-cli (philschmid)** | Bun | Connection pooling, tool filtering, grep de tools | github.com/philschmid/mcp-cli |

### 3.1. Recomendações por caso de uso

- **Para simplicidade e rapidez:** `mcp-cli-skill` (Python, `pipx install`)
- **Para performance:** `mcp (avelino)` (Go, binário único, sem dependências)
- **Para funcionalidade completa:** `mcp2cli` (Bun, daemon persistente, batch)
- **Para agentes AI:** `mcpc (Apify)` (code mode com JSON output, chaining)

---

## 4. Plano de Implementação

### Passo 1: Instalar um wrapper CLI

Escolha um dos wrappers listados na seção 3. Recomendações rápidas:

```bash
# Opção Python (simples)
pipx install mcp-cli-skill

# Opção Go (performance, binário único)
# Baixe de: github.com/avelino/mcp/releases

# Opção Bun (funcionalidade completa)
npm install -g mcp2cli
```

### Passo 2: Configurar servidores MCP no wrapper

O wrapper precisa saber quais servidores MCP usar. A maioria lê configurações
de arquivos JSON ou importa de configs existentes (Claude Desktop, etc.).

Exemplo com `mcp-cli-skill`:

```bash
# Adicionar servidor stdio (local)
mcp-call --add meu-servidor uvx algum-mcp-server --env API_KEY=abc123

# Adicionar servidor HTTP (remoto)
mcp-call --add-http minha-api http://localhost:8010/mcp

# Verificar configuração
mcp-call --servers
```

Exemplo com `mcp (avelino)`:

```bash
# Adicionar servidor
mcp add meu-servidor uvx algum-mcp-server

# Ou servidor HTTP
mcp add --url http://localhost:8010/mcp minha-api

# Listar configurados
mcp --list
```

### Passo 3: Verificar funcionamento do wrapper

Teste manualmente antes de integrar com o Copilot:

```bash
# Listar servidores e ferramentas disponíveis
mcp-call meu-servidor --tools

# Ver schema de uma ferramenta
mcp-call meu-servidor nome_da_tool --schema

# Chamar uma ferramenta com argumentos nomeados
mcp-call meu-servidor nome_da_tool --key=value

# Chamar com JSON via stdin
echo '{"param1": "valor"}' | mcp-call meu-servidor nome_da_tool
```

### Passo 4: Instruir o Copilot Chat a usar o wrapper

Crie ou edite `.github/copilot-instructions.md` no workspace para guiar o
Copilot a usar o wrapper CLI:

```markdown
## Uso de ferramentas MCP via CLI

Este projeto utiliza servidores MCP acessíveis via linha de comando.
Sempre que precisar usar essas ferramentas, utilize o wrapper CLI.

### Comando base

```
mcp-call <servidor> <tool> [opções]
```

### Fluxo de uso

1. Descubra ferramentas disponíveis:
   `mcp-call <servidor> --tools`

2. Veja o schema de uma ferramenta antes de chamar:
   `mcp-call <servidor> <tool> --schema`

3. Execute a ferramenta:
   `mcp-call <servidor> <tool> --param1=valor --param2=valor`

4. Para argumentos complexos, use JSON via stdin:
   `echo '{"key": "value"}' | mcp-call <servidor> <tool>`

### Servidores configurados

- `meu-servidor`: Descrição do que este servidor faz
  - Ferramentas: tool_a, tool_b, tool_c
  - Exemplo: `mcp-call meu-servidor tool_a --query="teste"`
```

### Passo 5: Habilitar Agent mode e testar

1. Abra o Copilot Chat no VS Code (`Ctrl+Alt+I`)
2. Selecione **Agent** mode no dropdown de agente
3. Faça uma pergunta que requeira uso de ferramentas MCP
4. Observe se o Copilot executa os comandos CLI no terminal integrado
5. Verifique nos **Agent Logs** as chamadas de ferramentas e comandos executados

### Passo 6: Opcional — Criar wrapper personalizado

Se os wrappers existentes não atendem, crie um script shell simples que fala
diretamente com o servidor MCP via stdio:

```bash
#!/bin/bash
# mcp-tool-wrapper.sh
# Uso: ./mcp-tool-wrapper.sh <server_command> <tool> [json_args]

SERVER_CMD=$1
TOOL=$2
ARGS=${3:-"{}"}

# Construir mensagens JSON-RPC (uma por linha)
REQUEST=$(printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"cli-wrapper","version":"1.0"}}}' \
  '{"jsonrpc":"2.0","method":"initialized","params":{}}' \
  "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"$TOOL\",\"arguments\":$ARGS}}"
)

# Enviar para servidor stdio e capturar última resposta
echo "$REQUEST" | $SERVER_CMD 2>/dev/null | tail -1
```

Torne executável e teste:

```bash
chmod +x mcp-tool-wrapper.sh
./mcp-tool-wrapper.sh "npx -y @modelcontextprotocol/server-exemplo" nome_da_tool '{"key": "value"}'
```

---

## 5. Padrões de Uso Avançado

### 5.1. Composição com pipes e shell scripting

Uma vantagem da abordagem CLI é a capacidade de compor chamadas MCP com
ferramentas shell padrão:

```bash
# Pipe output para jq para filtrar resultados
mcp-call github list_issues --state=open | jq '.[] | {number, title}'

# Usar output de um comando como input de outro
mcp-call filesystem search_files '{"path": "src/", "pattern": "*.ts"}' \
  | jq -r '.content[0].text | split("\n")[0]' \
  | xargs -I {} mcp-call filesystem read_file '{"path": "{}"}'

# Salvar resultado em variável shell
RESULT=$(mcp-call meu-servidor get_data --id=123)
mcp-call meu-servidor process_data --input="$RESULT"
```

### 5.2. Scripts bash gerados pelo Copilot

O Copilot pode gerar scripts bash completos que orquestram múltiplas chamadas
MCP em uma única execução:

```bash
#!/bin/bash
# Script gerado pelo Copilot para orquestrar múltiplas ferramentas MCP

# 1. Buscar dados do servidor A
mcp-call servidor_a fetch_records --limit=10 > /tmp/records.json

# 2. Processar com jq e enviar para servidor B
cat /tmp/records.json | jq '.[] | select(.status == "pending")' \
  | mcp-call servidor_b process_batch --input-json=-

# 3. Notificar resultado
mcp-call slack send_message \
  --channel="#engineering" \
  --text="Processamento concluído: $(cat /tmp/records.json | jq length) registros"
```

### 5.3. Daemon mode para performance

Alguns wrappers (mcp2cli, mcpshim) suportam modo daemon que mantém conexões
MCP persistentes, evitando o custo de spawn do servidor a cada chamada:

```bash
# Iniciar daemon (mcp2cli)
mcp2cli services

# Chamar ferramentas sem overhead de inicialização
mcp2cli n8n n8n_list_workflows --params '{}'
mcp2cli n8n n8n_get_workflow --params '{"id": "abc123"}'

# Batch de chamadas em uma única invocação
cat <<EOF | mcp2cli batch
{"service": "n8n", "tool": "n8n_list_workflows", "params": {}}
{"service": "n8n", "tool": "n8n_get_workflow", "params": {"id": "1"}}
EOF
```

---

## 6. Barreiras e Soluções

| Barreira | Impacto | Solução |
|---|---|---|
| Copilot não executa CLI sem instrução | Alto | Use `.github/copilot-instructions.md` com exemplos claros |
| Output CLI verboso consome tokens | Médio | Use flags `--json` ou pipe para `jq` para output conciso |
| Aprovação de segurança por comando | Médio | Use `/autoApprove` no Copilot CLI ou configure allowed patterns |
| Servidor MCP com inicialização lenta | Médio | Use wrapper com daemon mode (mcp2cli, mcpshim) |
| JSON-RPC complexo para wrapper custom | Baixo | Use wrappers existentes em vez de implementar do zero |
| Stderr do servidor polui output | Baixo | Wrappers redirecionam stderr automaticamente |

---

## 7. Referências

### Wrappers CLI

- mcp-cli-skill: github.com/wise-toddler/mcp-cli-skill
- mcp2cli: github.com/rodaddy/mcp2cli
- mcpshim: mcpshim.dev
- mcp (avelino): github.com/avelino/mcp
- mcpc (Apify): github.com/apify/mcp-cli
- mcpwrap: github.com/nanasi-apps/mcpwrap
- mcp-cli (philschmid): github.com/philschmid/mcp-cli

### Documentação Oficial

- MCP Specification — Transports: modelcontextprotocol.io/specification/draft/basic/transports
- VS Code Copilot CLI: code.visualstudio.com/docs/copilot/agents/copilot-cli
- GitHub MCP Server: github.com/github/github-mcp-server

### Projetos Relacionados

- mcp-agentic-coder (orquestração de AI CLIs via MCP): github.com/siraphob-vutthanun/mcp-agentic-coder
- executor-mcp (gerenciamento de processos CLI via MCP): github.com/XuNeo/executor-mcp
