# Specs executáveis de segurança

As decisões de segurança e os caminhos de execução devem permanecer
explícitos. A verificação da especialidade é
[executada pela fixture](#execute=executarVerificacoes()).

O veredito esperado é [pass](#assertEquals=veredito).

## Provisionamento local do ai-memory

O provisionamento não habilita MCP antes de concluir wrapper, container,
volume e hooks. As verificações abaixo cobrem os controles SEC-01..SEC-11 e
SEC-21. Os testes pytest fornecem fixtures locais e não iniciam Docker.

### SEC-01 — Origem e TLS

No POSIX, o wrapper vem da release oficial `v2.4.1`, por URL HTTPS fixa do
GitHub. O download mantém a validação TLS. O veredito é
[pass](#assertEquals=vereditoSec01) após
[executar a verificação](#execute=verificarSec01()).

### SEC-02 — Integridade do wrapper e pin da imagem

O bootstrap valida o wrapper pelo SHA-256
`49c965a0319dbe9c525d552a9a4c8b3464e5dd278e36d5dc7a03edee8b5502e6`.
O código registra o digest do índice OCI
`a626d115e0350afe934954c02c9064d30b708c58316763a9c6674ef5d0c8e3d9` e
usa a referência linux/amd64
`akitaonrails/ai-memory:latest@sha256:5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e`.
O veredito é [pass](#assertEquals=vereditoSec02) após
[executar a verificação](#execute=verificarSec02()).

### SEC-03 — Bind de loopback

O container publica a porta 49374 somente em `127.0.0.1`. Se Docker não
publicar a porta, o bootstrap usa o IPv4 privado do container na rede
`ai-memory-internal` como endpoint MCP, no formato
`http://<ipv4-da-bridge>:49374/mcp`. O fallback não publica porta no host.
O container define `AI_MEMORY_ALLOWED_HOSTS` com `localhost`, `127.0.0.1`,
`::1`, `host.docker.internal` e o próprio IPv4. O probe HTTP aceita `405`
após a validação de Host e rejeita `403`.
O veredito é [pass](#assertEquals=vereditoSec03) após
[executar a verificação](#execute=verificarSec03()).

### SEC-04 — Porta ocupada

A porta ocupada interrompe a criação e produz instrução acionável.
O veredito é [pass](#assertEquals=vereditoSec04) após
[executar a verificação](#execute=verificarSec04()).

### SEC-05 — Drift do plugin

Drift do hash do plugin gerado produz aviso explícito.
O veredito é [pass](#assertEquals=vereditoSec05) após
[executar a verificação](#execute=verificarSec05()).

### SEC-06 — Idempotência e upgrade

A segunda execução não baixa wrapper nem imagem. Hash divergente bloqueia
upgrade silencioso.
O veredito é [pass](#assertEquals=vereditoSec06) após
[executar a verificação](#execute=verificarSec06()).

### SEC-07 — Dados sensíveis

O volume contém dados sensíveis. O diretório POSIX permite acesso somente ao
usuário e permanece após rollback. O marcador `.bootstrap-mcp-url` fica em
`~/.local/state/ai-memory/`, fora do volume `~/.local/share/ai-memory/`.
O veredito é [pass](#assertEquals=vereditoSec07) após
[executar a verificação](#execute=verificarSec07()).

### SEC-08 — Rollback

O rollback remove container, hooks e MCP, restaura jsonc e preserva o volume.
O veredito é [pass](#assertEquals=vereditoSec08) após
[executar a verificação](#execute=verificarSec08()).

### SEC-09 — Docker ausente

Docker ausente interrompe o provisionamento e não declara MCP em nenhum harness.
O veredito é [pass](#assertEquals=vereditoSec09) após
[executar a verificação](#execute=verificarSec09()).

### SEC-10 — Merge Copilot

O merge Copilot preserva servers existentes e cria backup antes da escrita.
O veredito é [pass](#assertEquals=vereditoSec10) após
[executar a verificação](#execute=verificarSec10()).

### SEC-11 — Segredos

A declaração canônica não contém credenciais.
O veredito é [pass](#assertEquals=vereditoSec11) após
[executar a verificação](#execute=verificarSec11()).

### SEC-21 — Egress

O container usa a rede Docker `internal`, sem rota de saída padrão. O fallback
de SEC-03 usa o IPv4 privado dessa rede e não altera o isolamento.
O veredito é [pass](#assertEquals=vereditoSec21) após
[executar a verificação](#execute=verificarSec21()).

O veredito agregado dessas asserções é [pass](#assertEquals=vereditoAiMemory).
