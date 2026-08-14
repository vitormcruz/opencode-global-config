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

### D13 — Execucao exclusivamente no WSL/Linux

A suite de integracao do OpenCode roda **somente no WSL/Linux**. Windows esta
fora do escopo deste plano.

Rationale: apenas o OpenCode permite apontar para um modelo arbitrario, e o
OpenCode e o harness suportado no WSL/Linux. O harness Copilot, unico no
Windows, ficou restrito a smoke tests deterministicos por D1 — ele nao executa
inferencia e portanto nao precisa do Bonsai.

Consequencias operacionais:

- Nao investigar, diagnosticar ou corrigir ausencia de `llama-server`,
  `python3` ou falhas TLS/Schannel no PATH do Windows. Sao irrelevantes.
- Toda validacao de runtime (download dos pesos, `llama-server`, Docker,
  `pytest -m opencode`) acontece no WSL/Linux.
- O acesso ao HuggingFace deve ser testado a partir do WSL antes de qualquer
  conclusao sobre CA corporativa ou mirror. Se o download falhar **no WSL**,
  ai sim solicitar CA aprovada ou mirror ao humano — nunca desabilitar TLS.

### D14 — Publicacao da porta via proxy TCP no host

Em rede Docker `--internal`, `-p 127.0.0.1:4196:4096` nao publica a porta: o
container responde internamente em `127.0.0.1:4096`, mas o host nao alcanca
`127.0.0.1:4196`. A solucao e um proxy TCP em stdlib rodando no host.

- Bind exclusivo em `127.0.0.1:4196`, encaminhando para o IP do container na
  rede `opencode-test-net`.
- O `-p` do Docker e **removido** do `docker run`.
- Lifecycle explicito em `--up`, `--down`, `--rebuild` e na fixture.
- Nao anexar segunda rede ao container, nao publicar porta Docker e nao
  liberar egress.
- O gateway real mapeado para `host.docker.internal` e o bloqueio de saida
  externa permanecem intactos.

Rationale: preserva o isolamento comprovado por D6/D11 e restabelece o acesso
do host ao OpenCode sem abrir nenhuma rota nova para fora.

### D15 — Provisionamento automatico do `llama-server` no `BonsaiServer`

O `BonsaiServer` passa a provisionar tambem o binario, nao apenas os pesos.

- Fonte: release **fixado** `prism-b9596-9fcaed7` do fork
  `PrismML-Eng/llama.cpp` (Apache 2.0), que publica binarios pre-compilados
  para CUDA, ROCm, Vulkan e CPU. Nao ha compilacao local.
- Deteccao de backend replicando `scripts/download_binaries.sh` do
  `Bonsai-demo`:
  1. `nvcc` ou `nvidia-smi` presente → CUDA (tag `12.8` se versao >= 12.8,
     senao `12.4`)
  2. `rocminfo` / `rocm-smi` / `hipcc` → ROCm 7.2
  3. `vulkaninfo` → Vulkan
  4. nenhum → CPU (`ubuntu-x64`)
- Destino: `~/.cache/opencode-config/llama/`, ao lado dos pesos. O
  `llama-server` extraido de la e usado diretamente.
- Fica no `BonsaiServer`, **nao no bootstrap**: e dependencia exclusiva dos
  testes de integracao, e o bootstrap nao deve baixar centenas de MB para
  quem so quer usar o repositorio.
- Falha de download produz mensagem acionavel. Nunca `pytest.skip`.

Rationale: elimina qualquer escolha manual e qualquer compilacao. A versao
fixada garante reprodutibilidade e imunidade a quebras por release novo — o
mesmo que o `Bonsai-demo` faz.

### D16 — Timeout nunca e criterio de falha

Timeout como assercao de desempenho ("responda em N segundos ou falhe") esta
proibido: transforma lentidao em falha e gera intermitencia.

O parametro `timeout` permanece **apenas** como guarda contra travamento, com
valor alto o bastante para nunca ser atingido por uma maquina lenta (ex.:
600s em `urlopen`). Consequencias:

- Nenhum teste falha por lentidao; apenas por travamento real.
- A suite permanece interrompivel — `timeout=None` (bloqueio infinito) foi
  descartado por remover a rede de seguranca.

Rationale: uma maquina so-CPU pode ser uma ordem de grandeza mais lenta que
uma com CUDA. Um limite alto nao penaliza quem roda em GPU, porque nunca e
alcancado.

### D17 — Deteccao de backend valida capacidade real, nao sintoma

A deteccao do D15 e ingenua: trata a presenca de `nvidia-smi` como prova de
CUDA. No WSL, `nvidia-smi` vem do driver do Windows e existe mesmo sem o
runtime CUDA instalado — o binario CUDA e baixado e falha ao carregar por
falta de `libcudart.so.12` e `libcublas.so.12`.

A deteccao passa a verificar a **capacidade efetiva**:

- Antes de escolher CUDA, confirmar que `libcudart.so.12` e `libcublas.so.12`
  sao resolviveis pelo linker.
- Se nao forem, descer para Vulkan e, na ausencia deste, para CPU.
- Nada e instalado: sem `apt`, sem `sudo`, sem dependencia nova e sem
  manipular `LD_LIBRARY_PATH`.
- Ao rebaixar o backend, o `BonsaiServer` imprime uma linha informando que
  CUDA foi ignorado por falta de runtime, com o comando de instalacao para
  quem quiser acelerar depois. E informativo, nunca obrigatorio.

Rationale: a suite precisa passar em qualquer maquina sem intervencao manual —
esse criterio sustenta o plano inteiro. Instalar CUDA como pre-requisito
transformaria um teste automatizado em algo dependente de setup nao
documentado. Isto **reforca** o D15: o provisionamento continua automatico,
fixado no mesmo release e sem compilacao; apenas a deteccao deixa de confiar
em um sintoma. Os pesos 1-bit tem 3,54 GB e cabem folgados em RAM, e o D16 ja
removeu tempo como criterio de falha — CPU e um caminho valido.

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
- [x] `BonsaiServer.ensure_up()` baixa os GGUF apenas quando ausentes, sobe o
      `llama-server` e aguarda `GET /v1/models` responder 200
- [x] Se o servidor ja estiver rodando na porta, reusa sem subir outro
- [x] `stop()` encerra o processo; `require_available()` falha com mensagem
      acionavel quando indisponivel
- [x] CLI `--up` / `--down` / `--status` funciona

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

**Description:** Expor o `BonsaiServer` no escopo de toda a suite via fixture
session-scoped e cobrir o utilitario com testes unitarios. As fixtures OpenCode
e Docker dependem dela, garantindo que o modelo esteja disponivel antes do
container.

**Acceptance criteria:**
- [x] Fixture `bonsai_server` com `scope="session"` chama `ensure_up()` uma
      unica vez por execucao da suite
- [x] O teardown **nao** derruba o servidor (requisito de D9/D12)
- [x] Falhas de pre-requisito usam `pytest.fail` com instrucao acionavel,
      nunca `skip`
- [x] Testes unitarios usam mocks; nao dependem do servidor real

**Verification:**
- [x] `.venv/bin/pytest tests/integration/model/test_bonsai_server.py -m unit`
      passa sem o `llama-server` no ar

**Dependencies:** Task 1

**Files likely touched:**
- `tests/integration/conftest.py`
- `tests/integration/model/test_bonsai_server.py` (novo)

**Estimated scope:** S

---

### Checkpoint: Fundacao

- [ ] O `llama-server` sobe, responde e dorme apos 10 min de ociosidade
- [x] Testes unitarios do utilitario passam sem o servidor no ar
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
- [x] Nenhuma referencia a `opencode/big-pickle` ou provider externo na config
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
- [x] `git grep OPENCODE_TEST_MODEL` retorna vazio (exceto `plan/`)
- [x] `OPENCODE_CONFIG` nao e montada, propagada nem mesclada no runtime de
      integracao
- [x] Nenhuma mensagem no repo sugere OpenAI, Anthropic ou Ollama como modelo
      de teste
- [ ] A suite roda sem nenhuma variavel de modelo definida

**Verification:**
- [x] `.venv/bin/pytest -m "unit or tools"` passa
- [x] `git grep -n "OPENCODE_TEST_MODEL" -- . ':!plan'` nao retorna nada

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
- [x] Nenhuma variavel de modelo e necessaria
- [ ] Revisar com o humano antes de prosseguir

---

### Fase 3: Isolamento e enforcement

#### Task 5: Rede Docker `--internal` para o container de teste

**Description:** Criar e usar a rede `opencode-test-net` com
`docker network create --internal`, conectando o container de teste apenas a
ela. O gateway real da bridge e descoberto antes de mapear
`host.docker.internal` para alcancar o `llama-server` no host.

**Acceptance criteria:**
- [x] `DockerSession` cria a rede quando ausente e usa `--network opencode-test-net`
- [x] Rede existente e validada como `Internal=true`; o gateway real e
      descoberto antes do mapeamento de `host.docker.internal`
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
- [x] Teste de config: falha se a config efetiva declarar qualquer provider
      alem de `bonsai-local`
- [x] Teste de config tambem fixa o modelo `bonsai-local/bonsai-27b` e a URL
      local esperada
- [x] Teste de rede: executa dentro do container uma tentativa de conexao a um
      host externo e **exige** que ela falhe
- [x] Respostas HTTP externas nao sao confundidas com bloqueio; somente erros
      de DNS, conexao ou timeout aprovam o enforcement
- [x] Ambos usam `pytest.fail` com mensagem explicando a violacao de privacidade

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

#### Task 7: Eliminar timeout como criterio de falha (D16)

**Description:** Garantir que nenhum teste falhe por lentidao do modelo. O
primeiro request apos o sleep de ociosidade paga a recarga, e uma maquina
so-CPU pode ser uma ordem de grandeza mais lenta que uma com CUDA.

**Acceptance criteria:**
- [ ] `urlopen(...)` em `behavioral_helper.py` usa valor alto (ex.: 600s),
      atuando apenas como guarda contra travamento, nunca como assercao
- [ ] Nenhum teste usa tempo de resposta como criterio de aprovacao
- [ ] `test_agents.py`, `test_commands.py`, `test_prompts.py` e
      `test_skills_activation.py` passam com o Bonsai
- [x] Assercoes rigidas demais para um modelo menor sao afrouxadas sem perder
      o proposito do teste

**Verification:**
- [ ] `.venv/bin/pytest -m opencode` passa duas vezes seguidas
- [ ] A segunda execucao reaproveita o servidor (mais rapida)
- [ ] Nenhum limite curto de tempo permanece como criterio de aprovacao

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
- [x] `README.md` documenta: baixar/subir o Bonsai, requisito de disco
      (~4,2 GB), `bonsai_server.py --up/--down`, e o sleep de 10 minutos
- [x] A secao de variaveis de ambiente nao cita mais `OPENCODE_TEST_MODEL`
- [x] `AGENTS.md:214` atualizado para o novo pre-requisito
- [x] A garantia de privacidade e explicada: build tem rede, runtime e isolado

**Verification:**
- [x] Leitura manual: um dev novo consegue rodar a suite so com o README
- [x] Nenhuma linha ultrapassa 120 colunas

**Dependencies:** Task 7

**Files likely touched:**
- `README.md`
- `AGENTS.md`

**Estimated scope:** S

---

### Checkpoint: Completo

- [ ] Suite de integracao roda 100% contra o modelo on-premises
- [ ] Nenhum modelo externo e alcancavel em runtime
- [x] Documentacao atualizada
- [ ] Pronto para revisao

**Bloqueio de verificação:** Docker, `llama-server` e os pesos Bonsai não estão
disponíveis no ambiente atual. As verificações de runtime permanecem pendentes
em WSL/Linux com os pré-requisitos ativos.

---

## Replan — Fase 5: Runtime comprovado

Contexto do replan (pos-commit `bc80a0a`): a migracao foi implementada, mas o
runtime nunca foi comprovado de ponta a ponta. Diagnostico do working tree:

- O proxy TCP **foi escrito mas nao ligado**. Existem `_run_tcp_proxy`,
  `_proxy_connection`, `start_proxy`, `stop_proxy`, `proxy_pid_path` e as
  flags CLI `--proxy*` em `container_test_opencode.py`, porem:
  - `start_container()` ainda passa `-p 127.0.0.1:4196:4096` e **nunca chama**
    `start_proxy()`;
  - `down()` **nunca chama** `stop_proxy()`;
  - `_wait_until_ready()` aguarda em `127.0.0.1:4196`, porta que ninguem
    publica na rede interna.
- A rede `--internal` esta correta: bloqueia DNS/egress e o container alcanca
  o gateway real e o Bonsai.
- O `BonsaiServer` baixa os pesos GGUF mas nao provisiona o `llama-server`,
  e agora falha cedo quando o executavel nao esta no PATH.

#### Task 9: Ligar o proxy TCP ao lifecycle

**Description:** Concluir a implementacao iniciada no working tree, conectando
o proxy ja escrito ao ciclo de vida do container. Inspecionar o diff atual
antes de escrever codigo novo — nao reescrever o que ja existe.

Alteracoes necessarias em
`tests/integration/docker/container_test_opencode.py`:

1. Remover `-p 127.0.0.1:{host_port}:{container_port}` do `docker run` em
   `start_container()`.
2. Apos o container estar em execucao, descobrir seu IP via `container_ip()` e
   chamar `start_proxy(ip)`.
3. Chamar `_wait_until_ready()` somente depois que o proxy estiver ativo.
4. Chamar `stop_proxy()` em `down()` e no caminho de `--rebuild`, antes de
   remover o container.
5. Garantir que a fixture derrube o proxy de forma coerente com o lifecycle do
   container.

**Acceptance criteria:**
- [ ] `docker run` nao contem mais `-p`
- [ ] `--up` e `--rebuild` sobem container e proxy; `--down` derruba ambos
- [ ] Executar `--up` duas vezes nao deixa dois proxies vivos (o PID antigo e
      encerrado antes de iniciar outro)
- [ ] O proxy escuta exclusivamente em `127.0.0.1`, nunca em `0.0.0.0`
- [ ] Nenhuma segunda rede e anexada ao container

**Verification:**
- [ ] `python3 tests/integration/docker/container_test_opencode.py --rebuild`
      inicia o container com sucesso
- [ ] `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:4196/` retorna
      `200` no host
- [ ] `--down` seguido de `curl` na mesma URL falha (proxy encerrado)
- [ ] `ss -ltnp | grep 4196` mostra bind em `127.0.0.1`, nao `0.0.0.0`

**Dependencies:** Task 5

**Files likely touched:**
- `tests/integration/docker/container_test_opencode.py`
- `tests/integration/docker/test_container_test_opencode.py`
- `tests/integration/conftest.py`

**Estimated scope:** M

---

#### Task 11: Provisionar o `llama-server` automaticamente (D15)

**Description:** Estender o `BonsaiServer` para baixar tambem o binario, nao
apenas os pesos. Hoje ele falha cedo quando o executavel nao esta no PATH, o
que exige instalacao manual.

Release fixado: `prism-b9596-9fcaed7` em
`https://github.com/PrismML-Eng/llama.cpp/releases/download/prism-b9596-9fcaed7/`

Assets Linux x64 disponiveis:
- CUDA 12.8: `llama-prism-b9596-9fcaed7-bin-linux-cuda-12.8-x64.tar.gz`
- CUDA 12.4: `llama-prism-b9596-9fcaed7-bin-linux-cuda-12.4-x64.tar.gz`
- ROCm 7.2: `llama-prism-b9596-9fcaed7-bin-ubuntu-rocm-7.2-x64.tar.gz`
- Vulkan:   `llama-prism-b9596-9fcaed7-bin-ubuntu-vulkan-x64.tar.gz`
- CPU:      `llama-prism-b9596-9fcaed7-bin-ubuntu-x64.tar.gz`

Ordem de deteccao (identica a `download_binaries.sh` do `Bonsai-demo`):
`nvcc`/`nvidia-smi` → CUDA · `rocminfo`/`rocm-smi`/`hipcc` → ROCm ·
`vulkaninfo` → Vulkan · nenhum → CPU.

**Acceptance criteria:**
- [ ] `ensure_up()` baixa e extrai o binario para
      `~/.cache/opencode-config/llama/` quando ausente
- [ ] A deteccao escolhe o asset correto para o hardware local
- [ ] Um `llama-server` ja presente no cache nao e rebaixado
- [ ] Falha de download produz mensagem acionavel; nunca `pytest.skip`
- [ ] Nenhuma dependencia nova: download e extracao com a stdlib
      (`urllib`, `tarfile`)

**Verification:**
- [ ] Com o cache vazio, `bonsai_server.py --up` baixa binario e pesos e sobe
      o servidor
- [ ] `~/.cache/opencode-config/llama/` contem um `llama-server` executavel
- [ ] Em maquina com NVIDIA, os logs do `llama-server` indicam uso de GPU

**Dependencies:** Task 1

**Files likely touched:**
- `tests/integration/model/bonsai_server.py`
- `tests/integration/model/test_bonsai_server.py`

**Estimated scope:** M

---

#### Task 12: Endurecer a deteccao de backend (D17)

**Description:** Corrigir a deteccao de backend do `BonsaiServer` para validar
capacidade real antes de escolher CUDA, com rebaixamento automatico para
Vulkan e depois CPU, e mensagem informativa quando o rebaixamento ocorrer.

**Acceptance criteria:**
- [ ] CUDA so e escolhido se `libcudart.so.12` e `libcublas.so.12` forem
      resolviveis pelo linker
- [ ] Sem runtime CUDA, o backend cai para Vulkan e, na ausencia deste, CPU
- [ ] O rebaixamento imprime uma linha informativa com o comando de instalacao
- [ ] Nenhuma instalacao, `sudo`, dependencia nova ou `LD_LIBRARY_PATH`
- [ ] Se um binario ja baixado nao corresponder ao backend detectado, ele e
      substituido em vez de reutilizado

**Verification:**
- [ ] Teste unitario com o probe de biblioteca mockado cobre os tres caminhos:
      CUDA disponivel, CUDA ausente com Vulkan, e so CPU
- [ ] No WSL sem runtime CUDA, `bonsai_server.py --up` sobe o servidor e serve
      `/v1/models`
- [ ] `.venv/bin/pytest -m "unit or tools"` passa

**Dependencies:** Task 11

**Files likely touched:**
- `tests/integration/model/bonsai_server.py`
- `tests/integration/model/test_bonsai_server.py`

**Estimated scope:** S

---

#### Task 10: Validar o runtime completo no WSL/Linux

**Description:** Executar a suite de verdade, no WSL/Linux (D13), com o
`llama-server` servindo o Bonsai e o container isolado. Esta task e de
validacao: so gera codigo se algum criterio falhar.

**Acceptance criteria:**
- [ ] O container alcanca `/v1/models` no Bonsai via `host.docker.internal`
- [ ] `api.openai.com` permanece inacessivel por DNS e por conexao
- [ ] A suite `-m opencode` conecta ao servico e passa **duas vezes seguidas**
- [ ] A configuracao efetiva usa exclusivamente `bonsai-local/bonsai-27b`
- [ ] `OPENCODE_CONFIG` continua ausente de `tests/integration`
- [ ] Nenhum `pytest.skip`, dependencia nova ou fallback de modelo

**Verification:**
- [ ] `docker exec opencode-config-test curl -s --max-time 5
      http://host.docker.internal:8080/v1/models` retorna JSON
- [ ] `docker exec opencode-config-test curl -s --max-time 5
      https://api.openai.com` falha
- [ ] `.venv/bin/pytest -m "unit or tools or opencode"` passa duas vezes
- [ ] `git grep -n "OPENCODE_CONFIG" -- tests/integration` nao retorna nada

**Dependencies:** Task 9, Task 11, Task 12

**Files likely touched:**
- nenhum, se todos os criterios passarem

**Estimated scope:** S

---

### Checkpoint: Runtime comprovado

- [ ] Host alcanca o OpenCode; OpenCode alcanca o Bonsai; ninguem alcanca a
      internet
- [ ] Suite verde duas vezes seguidas
- [ ] Revisar com o humano antes de finalizar

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Copilot CLI nao permite endpoint LLM arbitrario | Alto | D1: harness Copilot fica em smoke tests deterministicos |
| Modelos Bonsai < 27B nao tem tool calling | Alto | Restringir a escolha as variantes 27B |
| Repos 27B privados no HF exigem `BONSAI_TOKEN` | — | **Resolvido:** repos ja publicos (`gated=false`) |
| Hardware insuficiente para servir 27B | Baixo | D3: variante 1-bit cabe nos 6 GB de VRAM |
| Tool calling do Bonsai 1-bit insuficiente para agentes | Medio | D5: tratado via replan, sem fallback pre-construido |
| Bonsai 1-bit mais lento que o modelo anterior | Medio | D16: timeout deixa de ser criterio de falha |
| Recarga apos o sleep de ociosidade atrasa o primeiro request | Baixo | D16: guarda alta, nunca atingida |
| Maquina sem GPU: modelo em CPU, muito mais lento | Medio | D15 escolhe build CPU; D16 evita falha por lentidao |
| `nvidia-smi` sem runtime CUDA (tipico no WSL) | Alto | D17: valida `libcudart`/`libcublas` e rebaixa o backend |
| Maquina com pouca memoria (< ~5 GB livres) | Baixo | Falha explicita do `llama-server`; documentar requisito |
| Release fixado do fork sai do ar | Baixo | Versao fixada e verificavel; trocar exige replan |
| `host.docker.internal` indisponivel em rede `--internal` | Medio | Task 5: fallback para o IP do gateway da bridge |

## Open Questions

_(nenhuma pendente)_
