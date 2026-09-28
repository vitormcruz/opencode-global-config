# Specs executáveis de segurança

As tabelas definem as entradas e os resultados esperados. A fixture lê cada
valor da spec e confere o código, a configuração e os testes relacionados.
Os requisitos de segurança registrados para E10 são a [origem][origem-sec].

[origem-sec]:
  ../../plan/otimizacao-custo-contexto.md#e10--ai-memory-no-bootstrap-e-config-canônica

[Executar todas as verificações](- "executarVerificacoes()").

## Provisionamento local do ai-memory

O provisionamento habilita o MCP somente depois de validar wrapper, container,
rede, volume e hooks. Os testes pytest usam fakes e não iniciam Docker.

### SEC-01: Origem e TLS (origem: [requisitos de E10][origem-sec])

O wrapper vem da release oficial por HTTPS, com validação TLS ativa.

| Entrada | Resultado esperado |
|---|---|
| Versão da release | `v2.4.1` |
| URL de download | `https://github.com/akitaonrails/ai-memory/releases/download/v2.4.1/ai-memory-wrapper` |
| Esquema da URL | `https` |
| Veredito | [pass](- "?=vereditoSec01") |

[Executar SEC-01](- "verificarSec01()").

### SEC-02: Integridade do wrapper e pin da imagem (origem: [requisitos de E10][origem-sec])

O bootstrap aceita o wrapper somente quando o SHA-256 corresponde ao pin.
A referência da imagem mantém o digest linux/amd64 aprovado.

| Entrada | Resultado esperado |
|---|---|
| SHA-256 do wrapper | `49c965a0319dbe9c525d552a9a4c8b3464e5dd278e36d5dc7a03edee8b5502e6` |
| Digest do índice OCI | `a626d115e0350afe934954c02c9064d30b708c58316763a9c6674ef5d0c8e3d9` |
| Tag da imagem | `akitaonrails/ai-memory:latest` |
| Digest linux/amd64 | `5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e` |
| Referência | `akitaonrails/ai-memory:latest@sha256:5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e` |
| Veredito | [pass](- "?=vereditoSec02") |

[Executar SEC-02](- "verificarSec02()").

### SEC-03: Bind de loopback e fallback (origem: [requisitos de E10][origem-sec])

O container publica a porta somente no loopback. Sem publicação efetiva, o
bootstrap usa o IPv4 privado da bridge e valida o Host antes de habilitar MCP.

| Entrada | Resultado esperado |
|---|---|
| Host do bind loopback | `127.0.0.1` |
| Porta MCP | `49374` |
| Bind Docker | `127.0.0.1:49374:49374` |
| URL MCP no loopback | `http://127.0.0.1:49374/mcp` |
| URL de bridge no teste | `http://172.30.0.2:49374/mcp` |
| Hosts permitidos | `localhost,127.0.0.1,::1,host.docker.internal,$container_ip` |
| Status HTTP aceito | `405` |
| Status HTTP rejeitado | `403` |
| Veredito | [pass](- "?=vereditoSec03") |

[Executar SEC-03](- "verificarSec03()").

### SEC-04: Porta ocupada (origem: [requisitos de E10][origem-sec])

Uma porta ocupada interrompe o provisionamento antes da criação do container.
O bootstrap informa como liberar o bind.

| Entrada | Resultado esperado |
|---|---|
| Host ocupado | `127.0.0.1` |
| Porta ocupada | `49374` |
| Endereço ocupado | `127.0.0.1:49374` |
| Trecho da mensagem | `libere a porta antes de reexecutar` |
| Veredito | [pass](- "?=vereditoSec04") |

[Executar SEC-04](- "verificarSec04()").

### SEC-05: Drift do plugin (origem: [requisitos de E10][origem-sec])

O bootstrap informa quando o instalador altera o hash do plugin gerado.

| Entrada | Resultado esperado |
|---|---|
| Caminho do plugin | `~/.config/opencode/plugins/ai-memory.ts` |
| Aviso de drift | `AVISO: o hash de ai-memory.ts mudou após install-hooks` |
| Veredito | [pass](- "?=vereditoSec05") |

[Executar SEC-05](- "verificarSec05()").

### SEC-06: Idempotência e upgrade (origem: [requisitos de E10][origem-sec])

Uma segunda execução não baixa o wrapper nem puxa a imagem novamente. Um hash
divergente bloqueia a substituição até o backup e a reexecução explícitos.

| Entrada | Resultado esperado |
|---|---|
| Execuções do provisionamento | `2` |
| Downloads totais do wrapper | `1` |
| Pulls totais da imagem | `1` |
| Upgrade com hash divergente | `bloqueado` |
| Trecho da instrução de backup | `backup` |
| Trecho da instrução de reexecução | `reexecute` |
| Veredito | [pass](- "?=vereditoSec06") |

[Executar SEC-06](- "verificarSec06()").

### SEC-07: Dados sensíveis (origem: [requisitos de E10][origem-sec])

O volume contém dados sensíveis. No POSIX, o bootstrap restringe o acesso ao
usuário. O marcador MCP fica fora do volume e o rollback preserva os dados.

| Entrada | Resultado esperado |
|---|---|
| Diretório de dados | `~/.local/share/ai-memory/` |
| Marcador MCP | `~/.local/state/ai-memory/.bootstrap-mcp-url` |
| Modo POSIX | `0700` |
| Conteúdo após rollback | `preserved` |
| Veredito | [pass](- "?=vereditoSec07") |

[Executar SEC-07](- "verificarSec07()").

### SEC-08: Rollback (origem: [requisitos de E10][origem-sec])

O rollback remove os artefatos gerenciados, restaura a configuração anterior e
preserva o volume.

| Entrada | Resultado esperado |
|---|---|
| Comando de rollback | `--rollback-ai-memory` |
| Configuração restaurada | `~/.config/opencode/opencode.jsonc` |
| Marcador removido | `~/.local/state/ai-memory/.bootstrap-mcp-url` |
| Volume preservado | `~/.local/share/ai-memory/` |
| Arquivo de dados preservado | `memory.sqlite` |
| Veredito | [pass](- "?=vereditoSec08") |

[Executar SEC-08](- "verificarSec08()").

### SEC-09: Docker ausente (origem: [requisitos de E10][origem-sec])

Sem Docker, o bootstrap desativa a declaração MCP nos dois harnesses e informa
uma instalação em user-space sem elevação.

| Entrada | Resultado esperado |
|---|---|
| Condição | `Docker ausente` |
| Chave MCP | `ai-memory` |
| Resultado OpenCode | `ausente` |
| Resultado Copilot | `ausente` |
| Instrução sem elevação | `não use sudo` |
| Veredito | [pass](- "?=vereditoSec09") |

[Executar SEC-09](- "verificarSec09()").

### SEC-10: Merge Copilot (origem: [requisitos de E10][origem-sec])

O adapter preserva servidores existentes e cria backup antes de gravar a
declaração ai-memory.

| Entrada | Resultado esperado |
|---|---|
| Arquivo de configuração Copilot | `~/.copilot/mcp-config.json` |
| Servidor preexistente | `existing-server` |
| URL preexistente | `http://127.0.0.1:49375/mcp` |
| URL MCP ai-memory | `http://127.0.0.1:49374/mcp` |
| Arquivo de backup | `mcp-config.json` |
| Veredito | [pass](- "?=vereditoSec10") |

[Executar SEC-10](- "verificarSec10()").

### SEC-11: Segredos (origem: [requisitos de E10][origem-sec])

O arquivo canônico declara o MCP sem campos de credencial.

| Entrada | Resultado esperado |
|---|---|
| Arquivo canônico | `harness-conf/opencode.json` |
| Chave MCP | `ai-memory` |
| URL MCP canônica | `http://127.0.0.1:49374/mcp` |
| Campos de credencial | `headers,environment,token,apiKey` |
| Veredito | [pass](- "?=vereditoSec11") |

[Executar SEC-11](- "verificarSec11()").

### SEC-21: Egress (origem: [requisitos de E10][origem-sec])

O container usa uma rede Docker sem rota de saída padrão. O fallback da SEC-03
continua dentro da bridge privada.

| Entrada | Resultado esperado |
|---|---|
| Rede Docker | `ai-memory-internal` |
| Opção de isolamento | `--internal` |
| Estado internal esperado | `true` |
| Rota padrão de saída | `sem rota de saída padrão` |
| Veredito | [pass](- "?=vereditoSec21") |

[Executar SEC-21](- "verificarSec21()").

O veredito agregado é [pass](- "?=vereditoAiMemory").

[Verificar o veredito agregado](- "executarVerificacoesAiMemory()").

O veredito da spec é [pass](- "?=veredito").
