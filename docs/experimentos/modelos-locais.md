# Experimento de modelos locais rápidos

## Estado da execução

- Data: 2026-08-18.
- Branch: `master-nova`.
- Escopo: Qwen3-0.6B contra Bonsai; Needle 2 permanece rejeitado.
- Estado: concluído no WSL/Linux, com harness experimental selecionável.
- Decisão: recomendar Qwen somente por seleção explícita; manter Bonsai como
  fallback e provider padrão.

A primeira tentativa no Windows foi bloqueada por Docker, pytest e caches
ausentes. A execução foi retomada no WSL confirmado pelo humano. As
pré-condições foram validadas antes da alteração do harness; não houve mudança
de provider padrão nem de histórico.

## Pré-condições verificadas

### Licença

| Componente | Origem fixada | Evidência | Resultado |
|---|---|---|---|
| Qwen3-0.6B | `Qwen/Qwen3-0.6B` | Apache-2.0 no model card e `LICENSE` | Aprovado |
| GGUF | `Qwen/Qwen3-0.6B-GGUF` | Apache-2.0 no repositório do artefato | Aprovado |
| Runtime | `PrismML-Eng/llama.cpp` | MIT no release `prism-b9596-9fcaed7` | Aprovado |

Fontes oficiais consultadas em 2026-08-18:

- https://huggingface.co/Qwen/Qwen3-0.6B
- https://huggingface.co/Qwen/Qwen3-0.6B-GGUF
- https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/raw/main/LICENSE
- https://raw.githubusercontent.com/PrismML-Eng/llama.cpp/prism-b9596-9fcaed7/LICENSE

### Artefato fixado

- Repositório: `Qwen/Qwen3-0.6B-GGUF`.
- Commit do repositório: `23749fefcc72300e3a2ad315e1317431b06b590a`.
- Arquivo: `Qwen3-0.6B-Q8_0.gguf`.
- Tamanho declarado: `639446688` bytes.
- LFS OID SHA-256: `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
- Xet hash: `18d608d38b934c86fc3f3a050157b2d4df8d12330de6d13af3ba201edd0e6539`.

A identidade foi conferida pela API oficial do Hugging Face e o arquivo foi
baixado no WSL. O SHA-256 local resultou em
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
Bonsai foi validado localmente com tamanho `3803452480` e SHA-256
`17ef842e47450caeb8eaa3ebfbbab5d2f2278b62b79be107985fb69a2f819aa0`.

## Evidências de execução

| Verificação | Resultado |
|---|---|
| `docker info` no WSL | Aprovado: Docker `29.5.2` |
| `.venv/bin/pytest --version` no WSL | Aprovado: pytest `9.1.1` |
| Caches Bonsai/Qwen | Provisionados e verificados no WSL |
| JSON de integração | Aprovado com `json.loads` |
| Testes unitários do contrato | `51 passed` |
| Provider padrão permanente | Continua `bonsai-local/bonsai-27b` |

O código cria a rede Docker com `--internal`, conecta o container somente a essa
rede e verifica acesso externo em
`tests/integration/test_privacy_enforcement.py`. Os quatro testes de privacidade
passaram tanto com Bonsai quanto com Qwen; isso comprova rede interna, endpoint
local e bloqueio de acesso externo durante as execuções.

## Gates de decisão

| Gate vinculante | Resultado | Evidência |
|---|---|---|
| Licença permissiva e gratuita | Aprovado | Fontes oficiais acima |
| Artefato íntegro e provisionado | Aprovado | SHA-256 local confere |
| Zero egress/telemetria | Aprovado | 4/4 testes de privacidade por modelo |
| 100% de `pytest -m opencode` | Aprovado | 50/50 testes por modelo |
| Ganho de duração >=30% | Aprovado | 64,20% no mesmo WSL |
| Bonsai continua padrão/fallback | Aprovado | Configuração permanente preservada |

Qwen3-0.6B atende aos gates e pode ser usado no experimento por seleção
explícita. A substituição automática do provider padrão permanece fora do
escopo; Bonsai continua como padrão e fallback.

## Medição comparativa

| Modelo | Comando | Testes | Duração |
|---|---|---:|---:|
| Bonsai | `pytest -m opencode --local-model bonsai` | 50 passed | 1560,50 s |
| Qwen3-0.6B | `pytest -m opencode --local-model qwen3-0.6b` | 50 passed | 558,70 s |

Ganho: `(1560,50 - 558,70) / 1560,50 = 64,20%`, superior ao mínimo de 30%.

## Reprodutibilidade

Para reproduzir, use o WSL/Linux com os artefatos já fixados e execute os dois
comandos da tabela. Nenhum timeout novo ou ajuste de timeout é necessário.
