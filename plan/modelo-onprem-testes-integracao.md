# Implementation Plan: Modelo On-Premises para Testes de Integracao

## Overview

Substituir o modelo externo usado hoje nos testes de integracao dos harness
OpenCode e Copilot CLI por um modelo servido on-premises (ex.: "bonsai"),
garantindo que nenhum prompt, codigo ou artefato do repositorio saia para
provedores externos durante a execucao da suite.

Estado atual observado no repo:

- `tests/integration/config/opencode.test.json` fixa `opencode/big-pickle`
  para os agentes `plan` e `build` (provider externo).
- `tests/integration/docker/entrypoint.py` sobrescreve esse modelo com
  `OPENCODE_TEST_MODEL` e mescla `provider` vindo de `OPENCODE_CONFIG`.
- `tests/integration/docker/Dockerfile` baixa o OpenCode de
  `https://opencode.ai/install` durante o build.
- `tests/integration/test_copilot_cli.py` faz apenas smoke test
  (`--help`, `--version`); nao ha teste comportamental do Copilot CLI.
- Markers do pytest: `unit`, `tools`, `opencode`, `copilot`.

## Contexto Tecnico do Bonsai (pesquisa confirmada)

Fontes: `prismml.com/news/bonsai-27b`, `github.com/PrismML-Eng/Bonsai-demo`
(README, AGENTS.md, TOOLS.md). Licenca Apache 2.0.

- Servido por `llama-server` (llama.cpp) em `http://localhost:8080`, com API
  **OpenAI-compatible** (`/v1/chat/completions`).
- Com `--jinja`, aceita o array `tools` da OpenAI e devolve `tool_calls`
  estruturados — sem prompt hacks. Round-trip de tool completo verificado.
- Familias e tamanhos: `ternary` (default, GGUF Q2_0 ~6.7 GB + mmproj 0.9 GB)
  e `bonsai` 1-bit (GGUF Q1_0 ~3.5 GB + mmproj 0.9 GB), nos tamanhos 27B, 8B,
  4B e 1.7B.
- **Restricao critica:** somente os modelos **27B** tem tool calling. O guia
  oficial descreve 8B/4B/1.7B como "text-only, no tools wiring". Testes
  comportamentais de agente dependem de tool calling.
- Benchmark agentic/tool-calling: Ternary 27B = 74.0, 1-bit 27B = 66.0
  (baseline full-precision Qwen3.6 27B = 80.0).
- Enquanto os repositorios 27B estiverem privados no HuggingFace, o download
  exige `BONSAI_TOKEN` (token HF read-only).
- Setup: `./setup.sh` (baixa deps, modelos e binarios) e
  `./scripts/start_llama_server.sh`.

## Pesquisa de Alternativas (agosto 2026)

Hardware alvo confirmado: **NVIDIA RTX A1000 Laptop 6 GB VRAM, 32 GB RAM,
Intel i7-13800H**. Tamanhos aferidos via API do HuggingFace.

| Candidato | Licenca | Peso GGUF | Cabe em 6 GB VRAM | Tool calling |
|---|---|---|---|---|
| **Bonsai 27B 1-bit** (`Q1_0`) | Apache 2.0 | 3,54 GB (+0,59 mmproj Q8) | **Sim** | Sim (BFCL/Tau 66,0) |
| **Ternary Bonsai 27B** (`Q2_0`) | Apache 2.0 | 6,67 GB (+0,59) | Nao, offload parcial | Sim (74,0) |
| Qwen3.6-35B-A3B (MoE, 3B ativos) | Apache 2.0 | 9,4 GB (IQ1_M) a 16,8 GB (IQ4_NL) | Nao | Sim, forte |
| Nemotron-3.5-Lightning-30B-A3B | openmdw-1.1 (nao Apache) | 20,9 GB (NVFP4) a 23,7 GB (Q4_K_M) | Nao | Sim |
| LiquidAI LFM2.5-2.6B | lfm1.0 (licenca propria) | 1,48 a 2,68 GB | Sim | Sim, porem capacidade menor |

Conclusoes da pesquisa:

- **Licenciamento:** Bonsai e Qwen3.6 sao Apache 2.0 (open weights sem
  restricao de uso). Nemotron usa `openmdw-1.1` e LFM2.5 usa licenca propria
  `lfm1.0` — ambas exigem revisao juridica antes de uso corporativo.
- **Repos Bonsai 27B ja estao publicos** (`gated=false` na API do HF). O
  `BONSAI_TOKEN` mencionado na documentacao do demo nao e mais necessario,
  o que remove esse risco do plano.
- **Nenhuma alternativa supera o Bonsai na restricao de VRAM.** Apenas o
  Bonsai 27B 1-bit entrega capacidade de classe 27B com tool calling dentro
  de 6 GB. As alternativas MoE (Qwen3.6-35B-A3B, Nemotron) sao rapidas por
  terem poucos parametros ativos, mas precisam de 10-24 GB residentes em RAM.
- **Alternativa viavel de reserva:** Qwen3.6-35B-A3B em `UD-IQ2_M` (10,7 GB)
  rodando majoritariamente em RAM. MoE A3B mantem throughput aceitavel em
  CPU e a licenca e Apache 2.0.

## Architecture Decisions

### D1 — Harness Copilot fica restrito a testes deterministicos

O Copilot CLI autentica no backend do GitHub e nao permite apontar para um
endpoint LLM arbitrario. Portanto:

- O harness Copilot mantem apenas smoke tests deterministicos, sem inferencia
  (o padrao ja existente em `tests/integration/test_copilot_cli.py`).
- Todos os testes **comportamentais** de agentes, skills e comandos passam a
  rodar no OpenCode apontando para o modelo on-premises.

Rationale: assumir a limitacao real da ferramenta em vez de interceptar
internals nao documentados do Copilot (opcao descartada por fragilidade).

### D3 — Bonsai 27B 1-bit (`Q1_0`) como unico modelo

- Modelo unico: `Bonsai-27B-Q1_0.gguf` (3,54 GB) +
  `Bonsai-27B-mmproj-Q8_0.gguf`, que cabe inteiro nos 6 GB de VRAM da
  RTX A1000.
- **Sem variante selecionavel.** A Ternary 27B nao entra no escopo e nao ha
  variavel de ambiente para trocar de modelo. Se no futuro houver necessidade
  de outra variante, isso sera objeto de um novo planejamento.

Rationale: velocidade importa em suite de testes, e caber inteiro na VRAM
evita offload para CPU. Licenca Apache 2.0 e repositorio publico. Manter um
unico caminho suportado e coerente com D5 e D8.

### D5 — Sem modelo alternativo no escopo

O plano foca exclusivamente no Bonsai. Nenhum fallback (por exemplo
Qwen3.6-35B-A3B) sera implementado ou documentado como caminho suportado.
Se o tool calling do Bonsai 1-bit se mostrar insuficiente durante a execucao,
o assunto sera revisto em um replan.

Rationale: manter o escopo simples e evitar construir infraestrutura para um
problema que ainda nao ocorreu.

### D9 — `BonsaiServer` como utilitario de teste, com servidor persistente

Espelha o padrao ja existente em `container_test_opencode.py`/`DockerSession`:

- `tests/integration/model/bonsai_server.py` — classe `BonsaiServer`
  (stdlib pura), com `ensure_up()`, `stop()`, `require_available()` e CLI
  `--up` / `--down` / `--status`. Responsabilidades: baixar o GGUF do
  HuggingFace quando ausente, subir o `llama-server` com `--jinja` e aguardar
  o endpoint responder.
- `tests/integration/model/conftest.py` — fixture `bonsai_server` com
  `scope="session"`: o modelo e carregado uma unica vez por execucao da suite.
- `tests/integration/model/test_bonsai_server.py` — testes unitarios do
  utilitario.

**Requisito imprescindivel:** se o `llama-server` ja estiver rodando, a fixture
o reaproveita e **nao o derruba** no teardown. Carregar 3,5 GB de pesos leva
dezenas de segundos, e executar a suite varias vezes em sequencia e o padrao de
uso normal. O servidor permanece disponivel entre execucoes sucessivas.

### D11 — Enforcement de privacidade em duas camadas

Ambas as verificacoes entram na suite:

1. **Config:** assertar que a config efetiva do OpenCode nao declara nenhum
   provider externo.
2. **Rede:** de dentro do container, tentar alcancar um host externo e exigir
   que a conexao falhe.

Rationale: e literalmente um teste do proprio ambiente de teste, o que
normalmente seria excesso. Neste caso especifico se justifica, porque a
garantia buscada e de seguranca e privacidade — e a camada 1 sozinha so prova
intencao, nao isolamento.

### D12 — Sleep por ociosidade nativo do `llama-server`

O servidor sobe com `--sleep-idle-seconds 600` (recurso nativo do
`llama-server`, PR ggml-org/llama.cpp#18228).

- Apos 10 minutos sem requisicoes, o modelo e a KV cache saem da memoria
  sozinhos, liberando os ~4,1 GB de VRAM sem intervencao humana.
- Qualquer nova requisicao recarrega o modelo automaticamente; o processo
  permanece vivo e o endpoint continua respondendo.
- A fixture nunca derruba o servidor. O CLI `--down` fica disponivel para
  desligamento explicito.
- **Consequencia a tratar:** o primeiro request apos o sleep paga o custo de
  recarga. Os timeouts do `behavioral_helper` (hoje `urlopen(..., timeout=10)`)
  precisam ser ampliados para absorver isso.

Rationale: entrega o comportamento desejado sem watchdog, heartbeat ou estado
em disco. Como o servidor dorme em vez de morrer, nao ha corrida entre
"derrubar" e "usar" — a fonte classica de flakiness em watchdogs.

### D6 — Isolamento via rede Docker `--internal`

O container de teste roda em uma rede dedicada criada com
`docker network create --internal opencode-test-net`.

- A rede interna nao recebe rota para a internet: qualquer tentativa de
  alcancar um provider externo falha por construcao.
- O container continua alcancando o host pelo IP do gateway da bridge, que e
  onde o `llama-server` escuta (D4).

Rationale: isolamento real e verificavel, sem container de proxy adicional.

### D7 — Build com rede, runtime isolado

O download do OpenCode no build da imagem (`curl https://opencode.ai/install`)
e mantido.

Rationale: o `curl` ocorre antes do `COPY .`, portanto nenhum conteudo do
repositorio trafega. Baixar software nao caracteriza vazamento de dados. A
fronteira de privacidade fica explicita: **build tem rede, runtime e isolado**.

### D8 — Bonsai como modelo fixo; `OPENCODE_TEST_MODEL` removida

- `tests/integration/config/opencode.test.json` passa a declarar um provider
  OpenAI-compatible local apontando para o `llama-server`, e os agentes `plan`
  e `build` usam o modelo Bonsai.
- A variavel `OPENCODE_TEST_MODEL` deixa de existir. Nao ha modelo a escolher:
  a suite usa o modelo baixado localmente.
- Toda a logica de selecao de modelo e removida: `select_model_if_needed`,
  `choose_model_interactively`, `extract_models_from_config`,
  `_model_error`, a flag `--models` e o `require_model` do helper. As mensagens
  que sugerem OpenAI/Anthropic/Ollama desaparecem junto.
- O `entrypoint.py` deixa de aplicar modelo por variavel de ambiente.

Rationale: com um unico modelo on-premises suportado, tornar o modelo
configuravel reintroduz exatamente o risco que o plano quer eliminar.

### D10 — Remocao do codigo e dos testes de selecao de modelo

Decorrencia direta de D8. Sao removidos:

- `extract_models_from_config()`, `choose_model_interactively()`,
  `select_model_if_needed()` e `_model_error()` em
  `container_test_opencode.py`
- a flag `--models` do CLI e `DockerSession.list_models()`
- `OpenCodeClient.require_model()` em `behavioral_helper.py`
- os testes correspondentes em
  `tests/integration/docker/test_container_test_opencode.py`

Substituidos por testes que verificam o provider local: Bonsai declarado na
config efetiva e respondendo.

Rationale: codigo de selecao de modelo nao tem proposito quando existe um
unico modelo local, e as mensagens de erro citando OpenAI/Anthropic/Ollama
contradizem o objetivo de privacidade do plano.

### D4 — `llama-server` roda no host/WSL, fora do container

O servidor do modelo roda como servico de longa duracao no host (WSL), e o
container do OpenCode o acessa pela rede.

Rationale: o modelo tem entre 3,5 e 7 GB; embutir ou recarregar isso na
imagem de teste seria caro em build, disco e tempo de startup. Como servico
externo de longa duracao, o modelo e carregado uma vez e reaproveitado por
todas as execucoes da suite. O enforcement de D2 e feito restringindo a rede
do container para enxergar apenas o host do modelo.

### D2 — Privacidade com enforcement, nao apenas configuracao

Nao basta configurar o provider local. O plano deve incluir verificacao ativa:

- O ambiente de teste roda com rede isolada, enxergando apenas o servidor do
  modelo on-premises.
- Um teste falha se houver provider externo configurado na config efetiva.
- O download de artefatos pela internet durante o **build** da imagem
  (hoje `curl https://opencode.ai/install` no Dockerfile) e tratado como
  problema separado do isolamento em **runtime**.

## Task List

Ambiente de execucao: **WSL/Linux**. Comando de teste padrao:
`.venv/bin/pytest -m "unit or tools or opencode"`.

### Fase 1: Fundacao — servidor do modelo

#### Task 1: Criar `BonsaiServer` com download e start do `llama-server`

**Description:** Criar o utilitario que provisiona o modelo Bonsai e sobe o
`llama-server`, espelhando o padrao de `DockerSession` em
`tests/integration/docker/container_test_opencode.py` (stdlib pura, sem
dependencias novas).

Parametros fixos:
- GGUF: `prism-ml/Bonsai-27B-gguf` → `Bonsai-27B-Q1_0.gguf` (3,54 GB)
- mmproj: `Bonsai-27B-mmproj-Q8_0.gguf` (0,59 GB)
- Destino do download: `~/.cache/opencode-config/models/`
- Porta: `8080`; flags: `--jinja`, `--sleep-idle-seconds 600`
- Download via URL publica do HF (`gated=false`, sem token):
  `https://huggingface.co/prism-ml/Bonsai-27B-gguf/resolve/main/<arquivo>`

**Acceptance criteria:**
- [ ] `BonsaiServer.ensure_up()` baixa os GGUF apenas quando ausentes, sobe o
      `llama-server` e aguarda `GET /v1/models` responder 200
- [ ] Se o servidor ja estiver rodando na porta, reusa sem subir outro
- [ ] `stop()` encerra o processo; `require_available()` falha com mensagem
      acionavel quando indisponivel
- [ ] CLI `--up` / `--down` / `--status` funciona

**Verification:**
- [ ] `python3 tests/integration/model/bonsai_server.py --up` sobe o servidor
- [ ] `curl -s localhost:8080/v1/models` retorna JSON com o modelo
- [ ] `--up` executado duas vezes nao cria segundo processo

**Dependencies:** None

**Files likely touched:**
- `tests/integration/model/bonsai_server.py` (novo)
- `tests/integration/model/__init__.py` (novo, se necessario)

**Estimated scope:** M

---

#### Task 2: Fixture `bonsai_server` e testes do utilitario

**Description:** Expor o `BonsaiServer` a suite via fixture session-scoped e
cobrir o utilitario com testes unitarios, espelhando
`tests/integration/docker/conftest.py` e `test_container_test_opencode.py`.

**Acceptance criteria:**
- [ ] Fixture `bonsai_server` com `scope="session"` chama `ensure_up()` uma
      unica vez por execucao da suite
- [ ] O teardown **nao** derruba o servidor (requisito de D9/D12)
- [ ] Falhas de pre-requisito usam `pytest.fail` com instrucao acionavel,
      nunca `skip`
- [ ] Testes unitarios usam mocks; nao dependem do servidor real

**Verification:**
- [ ] `.venv/bin/pytest tests/integration/model/test_bonsai_server.py -m unit`
      passa sem o `llama-server` no ar

**Dependencies:** Task 1

**Files likely touched:**
- `tests/integration/model/conftest.py` (novo)
- `tests/integration/model/test_bonsai_server.py` (novo)

**Estimated scope:** S

---

### Checkpoint: Fundacao

- [ ] O `llama-server` sobe, responde e dorme apos 10 min de ociosidade
- [ ] Testes unitarios do utilitario passam sem o servidor no ar
- [ ] Revisar com o humano antes de prosseguir

---

### Fase 2: OpenCode apontando para o modelo local

#### Task 3: Configurar provider OpenAI-compatible local

**Description:** Substituir `opencode/big-pickle` em
`tests/integration/config/opencode.test.json` por um provider local que aponta
para o `llama-server`. O container alcanca o host via
`host.docker.internal` (adicionar `--add-host=host.docker.internal:host-gateway`
no `docker run`).

Shape esperado da config:

```json
{
  "provider": {
    "bonsai-local": {
      "npm": "@ai-sdk/openai-compatible",
      "options": { "baseURL": "http://host.docker.internal:8080/v1" },
      "models": { "bonsai-27b": { "name": "Bonsai 27B 1-bit" } }
    }
  },
  "agent": {
    "plan":  { "model": "bonsai-local/bonsai-27b" },
    "build": { "model": "bonsai-local/bonsai-27b" }
  }
}
```

**Acceptance criteria:**
- [ ] Nenhuma referencia a `opencode/big-pickle` ou provider externo na config
- [ ] O container resolve `host.docker.internal` e alcanca a porta 8080
- [ ] Uma mensagem enviada ao OpenCode retorna resposta gerada pelo Bonsai

**Verification:**
- [ ] `python3 tests/integration/docker/container_test_opencode.py --rebuild`
      sobe o container e o OpenCode responde
- [ ] Um prompt simples via API retorna texto nao vazio

**Dependencies:** Task 1

**Files likely touched:**
- `tests/integration/config/opencode.test.json`
- `tests/integration/docker/container_test_opencode.py`

**Estimated scope:** S

---

#### Task 4: Remover a selecao de modelo (D8 e D10)

**Description:** Eliminar `OPENCODE_TEST_MODEL` e toda a maquinaria de escolha
de modelo. Referencias mapeadas: `AGENTS.md:214`, `README.md:206,224`,
`behavioral_helper.py:76-80`, `docker/conftest.py:22`,
`container_test_opencode.py:113-176,315-319`, `entrypoint.py:49-60,88-101`,
`test_prompts.py:39-48`.

Remover: `extract_models_from_config`, `choose_model_interactively`,
`select_model_if_needed`, `_model_error`, `DockerSession.list_models`, a flag
`--models` do CLI, `OpenCodeClient.require_model`, `_apply_test_model` do
entrypoint e os testes correspondentes.

**Acceptance criteria:**
- [ ] `git grep OPENCODE_TEST_MODEL` retorna vazio (exceto `plan/`)
- [ ] Nenhuma mensagem no repo sugere OpenAI, Anthropic ou Ollama como modelo
      de teste
- [ ] A suite roda sem nenhuma variavel de modelo definida

**Verification:**
- [ ] `.venv/bin/pytest -m "unit or tools"` passa
- [ ] `git grep -n "OPENCODE_TEST_MODEL" -- . ':!plan'` nao retorna nada

**Dependencies:** Task 3

**Files likely touched:**
- `tests/integration/behavioral_helper.py`
- `tests/integration/docker/container_test_opencode.py`
- `tests/integration/docker/test_container_test_opencode.py`
- `tests/integration/docker/entrypoint.py`
- `tests/integration/docker/conftest.py`
- `tests/integration/test_prompts.py`

**Estimated scope:** M

---

### Checkpoint: OpenCode no modelo local

- [ ] A suite de integracao do OpenCode roda de ponta a ponta contra o Bonsai
- [ ] Nenhuma variavel de modelo e necessaria
- [ ] Revisar com o humano antes de prosseguir

---

### Fase 3: Isolamento e enforcement

#### Task 5: Rede Docker `--internal` para o container de teste

**Description:** Criar e usar a rede `opencode-test-net` com
`docker network create --internal`, conectando o container de teste apenas a
ela. Manter `--add-host=host.docker.internal:host-gateway` para alcancar o
`llama-server` no host.

**Acceptance criteria:**
- [ ] `DockerSession` cria a rede quando ausente e usa `--network opencode-test-net`
- [ ] O container alcanca `host.docker.internal:8080`
- [ ] O container **nao** alcanca nenhum host da internet

**Verification:**
- [ ] `docker exec opencode-config-test curl -s --max-time 5 https://example.com`
      falha
- [ ] A suite de integracao continua passando

**Dependencies:** Task 3

**Files likely touched:**
- `tests/integration/docker/container_test_opencode.py`
- `tests/integration/docker/test_container_test_opencode.py`

**Estimated scope:** S

---

#### Task 6: Testes de enforcement de privacidade (D11)

**Description:** Adicionar os dois testes que comprovam o isolamento.

**Acceptance criteria:**
- [ ] Teste de config: falha se a config efetiva declarar qualquer provider
      alem de `bonsai-local`
- [ ] Teste de rede: executa dentro do container uma tentativa de conexao a um
      host externo e **exige** que ela falhe
- [ ] Ambos usam `pytest.fail` com mensagem explicando a violacao de privacidade

**Verification:**
- [ ] `.venv/bin/pytest -m opencode -k enforcement` passa
- [ ] Introduzir um provider externo na config faz o teste 1 falhar
      (verificacao manual, revertida em seguida)

**Dependencies:** Task 5

**Files likely touched:**
- `tests/integration/test_privacy_enforcement.py` (novo)

**Estimated scope:** S

---

### Checkpoint: Isolamento comprovado

- [ ] Container comprovadamente sem acesso a internet
- [ ] Config sem qualquer provider externo
- [ ] Revisar com o humano antes de prosseguir

---

### Fase 4: Estabilizacao e documentacao

#### Task 7: Ajustar timeouts e estabilizar a suite comportamental

**Description:** O primeiro request apos o sleep de ociosidade paga a recarga
do modelo, e o Bonsai 1-bit e mais lento que o modelo externo anterior. Ampliar
os timeouts e revalidar os testes comportamentais.

**Acceptance criteria:**
- [ ] `urlopen(..., timeout=10)` em `behavioral_helper.py` ampliado para
      absorver a recarga do modelo
- [ ] `test_agents.py`, `test_commands.py`, `test_prompts.py` e
      `test_skills_activation.py` passam com o Bonsai
- [ ] Assercoes rigidas demais para um modelo menor sao afrouxadas sem perder
      o proposito do teste

**Verification:**
- [ ] `.venv/bin/pytest -m opencode` passa duas vezes seguidas
- [ ] A segunda execucao reaproveita o servidor (mais rapida)

**Dependencies:** Task 4, Task 6

**Files likely touched:**
- `tests/integration/behavioral_helper.py`
- `tests/integration/test_agents.py`
- `tests/integration/test_commands.py`
- `tests/integration/test_prompts.py`
- `tests/integration/test_skills_activation.py`

**Estimated scope:** M

---

#### Task 8: Atualizar documentacao

**Description:** Refletir o novo fluxo no `README.md` e no `AGENTS.md`,
removendo as instrucoes de `OPENCODE_TEST_MODEL` e documentando o
pre-requisito do `llama-server` local. Respeitar o limite de 120 colunas.

**Acceptance criteria:**
- [ ] `README.md` documenta: baixar/subir o Bonsai, requisito de disco
      (~4,2 GB), `bonsai_server.py --up/--down`, e o sleep de 10 minutos
- [ ] A secao de variaveis de ambiente nao cita mais `OPENCODE_TEST_MODEL`
- [ ] `AGENTS.md:214` atualizado para o novo pre-requisito
- [ ] A garantia de privacidade e explicada: build tem rede, runtime e isolado

**Verification:**
- [ ] Leitura manual: um dev novo consegue rodar a suite so com o README
- [ ] Nenhuma linha ultrapassa 120 colunas

**Dependencies:** Task 7

**Files likely touched:**
- `README.md`
- `AGENTS.md`

**Estimated scope:** S

---

### Checkpoint: Completo

- [ ] Suite de integracao roda 100% contra o modelo on-premises
- [ ] Nenhum modelo externo e alcancavel em runtime
- [ ] Documentacao atualizada
- [ ] Pronto para revisao

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Copilot CLI nao permite endpoint LLM arbitrario | Alto | D1: harness Copilot fica em smoke tests deterministicos |
| Modelos Bonsai < 27B nao tem tool calling | Alto | Restringir a escolha as variantes 27B |
| Repos 27B privados no HF exigem `BONSAI_TOKEN` | — | **Resolvido:** repos ja publicos (`gated=false`) |
| Hardware insuficiente para servir 27B | Baixo | D3: variante 1-bit cabe nos 6 GB de VRAM |
| Tool calling do Bonsai 1-bit insuficiente para agentes | Medio | D5: tratado via replan, sem fallback pre-construido |
| Bonsai 1-bit mais lento que o modelo anterior | Medio | Task 7: ampliar timeouts e revalidar assercoes |
| Recarga apos o sleep de ociosidade atrasa o primeiro request | Baixo | Task 7: timeout generoso no primeiro contato |
| `host.docker.internal` indisponivel em rede `--internal` | Medio | Task 5: fallback para o IP do gateway da bridge |

## Open Questions

_(nenhuma pendente)_
