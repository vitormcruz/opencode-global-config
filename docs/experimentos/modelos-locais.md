# Experimento de modelos locais rápidos

## Estado da execução

- Data: 2026-08-18.
- Branch: `master-nova`.
- Escopo: Qwen3-0.6B Q8_0 como modelo único da integração OpenCode.
- Estado: migração concluída; Needle 2 permanece fora de escopo.
- Decisão: usar exclusivamente `qwen-local/qwen3-0.6b` no WSL/Linux.

## Pré-condições verificadas

### Licença

| Componente | Origem fixada | Evidência | Resultado |
|---|---|---|---|
| Qwen3-0.6B | `Qwen/Qwen3-0.6B` | Apache-2.0 no model card e `LICENSE` | Aprovado |
| GGUF | `Qwen/Qwen3-0.6B-GGUF` | Apache-2.0 no repositório | Aprovado |
| Runtime Prism | `PrismML-Eng/llama.cpp` | MIT no release `prism-b9596-9fcaed7` | Aprovado |
| `libgomp.so.1` | Debian Snapshot, `libgomp1 12.2.0-14+deb12u1 amd64` | GPLv3-or-later + GCC Runtime Library Exception 3.1 | Aprovado |

Fontes oficiais consultadas em 2026-08-18:

- https://huggingface.co/Qwen/Qwen3-0.6B
- https://huggingface.co/Qwen/Qwen3-0.6B-GGUF
- https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/raw/main/LICENSE
- https://raw.githubusercontent.com/PrismML-Eng/llama.cpp/prism-b9596-9fcaed7/LICENSE
- https://snapshot.debian.org/package/gcc-12/12.2.0-14+deb12u1/
- https://gcc.gnu.org/onlinedocs/libgomp/

### Artefato fixado

- Repositório: `Qwen/Qwen3-0.6B-GGUF`.
- Commit do repositório: `23749fefcc72300e3a2ad315e1317431b06b590a`.
- Arquivo: `Qwen3-0.6B-Q8_0.gguf`.
- Tamanho declarado: `639446688` bytes.
- SHA-256: `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.

O harness valida o SHA-256 antes de iniciar o servidor e rejeita artefatos
incorretos. O bootstrap não baixa pesos; o provisionamento ocorre sob demanda
no cache local do usuário.

## Contrato final

- Provider único: `qwen-local`.
- Modelo único: `qwen-local/qwen3-0.6b`.
- Endpoint: `http://host.docker.internal:8080/v1`.
- Runtime: binário Prism `prism-b9596-9fcaed7` em
  `~/.cache/opencode-config/llama/`.
- Pesos: `~/.cache/opencode-config/models/Qwen3-0.6B-Q8_0.gguf`.
- Runtime OpenMP: `~/.cache/opencode-config/runtime/libgomp/12.2.0-14+deb12u1-amd64/`.
- Pacote libgomp SHA-256:
  `48fec46bda7f5b1638b9e959889bfbc20491247d402d120bb152687eb48143d7`.
- Biblioteca libgomp SHA-256:
  `f9a9ad78a8dc39c0e90a265ffa551fae6c92a40f360889b44a7e141f9a2adfb1`.
- Execução: offline depois do provisionamento, sem telemetria, egress ou
  handoff em cloud.

## Evidências de execução

| Verificação | Resultado |
|---|---|
| `docker info` no WSL | Aprovado na validação do experimento |
| `.venv/bin/pytest --version` no WSL | Aprovado na validação do experimento |
| Cache e checksum Qwen | Provisionado e verificado |
| JSON de integração | Um único provider local; aprovado com `json.loads` |
| Rede Docker | `opencode-test-net` com `Internal=true` |
| Endpoint | Gateway interno para `host.docker.internal:8080` |
| Privacidade | Rede interna, config, endpoint local e egress bloqueado |
| Gate OpenCode | Aprovado no WSL/Linux: 50 testes passaram em 568,10 s |
| Runtime OpenMP | Provisionada pelo bootstrap; carregada pelo `ld-linux` sem `LD_LIBRARY_PATH` |
| Busca global `libgomp` | Nenhuma instalação global; somente a copia em cache foi carregada |

A suíte padrão é executada com:

```bash
.venv/bin/pytest -m opencode
```

O harness usa proxy limitado a `127.0.0.1`, não aceita overlays externos e não
altera os valores de timeout existentes. Falhas de provisionamento ou de
inferência do Qwen são explícitas.

O pacote Debian e a biblioteca extraida permanecem identificados por versão,
arquitetura e SHA-256 no cache. A redistribuicao deve conservar os avisos
GPLv3 e a GCC Runtime Library Exception 3.1; o bootstrap nao instala
`libgomp1` no sistema e nao provisiona pesos Qwen.

## Reprodutibilidade e rollback

No WSL/Linux com Docker, execute o comando padrão acima. O primeiro uso pode
provisionar a runtime libgomp, o binário Prism e os pesos Qwen; execuções
seguintes reutilizam o cache verificado e não exigem rede. Para desligamento
manual do runtime:

```bash
python3 tests/integration/model/local_model_server.py --down
```

O rollback suportado é `git revert` do conjunto da migração. Não há seletor de
modelo alternativo nem fallback silencioso. Needle 2 e Copilot não fazem parte
desta alteração.
