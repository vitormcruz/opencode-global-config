# ADR-0002: Testes de integração com modelo on-premises

- **Status:** Aceita
- **Data:** 2026-08-16
- **Escopo:** Testes de integração OpenCode, Bonsai, llama-server, Docker e WSL/Linux

## Contexto

Os testes de integração usavam um modelo externo e podiam enviar prompts, código
ou artefatos do repositório para um provedor fora do ambiente local. Isso
contradizia a garantia de privacidade exigida para os harnesses OpenCode e
Copilot CLI.

O OpenCode aceita um endpoint de modelo arbitrário, mas o Copilot CLI autentica
no backend do GitHub e não oferece essa configuração. O caminho local escolhido
precisa, portanto, manter os testes comportamentais no OpenCode e limitar o
Copilot a verificações que não fazem inferência.

O hardware de referência é uma NVIDIA RTX A1000 Laptop com 6 GB de VRAM e
32 GB de RAM. O Bonsai 27B 1-bit tem cerca de 3,54 GB e oferece tool calling,
enquanto as variantes menores são text-only. O servidor precisa permanecer
fora do container para que os pesos sejam carregados uma vez e reutilizados.

Durante a validação, o `llama-server` sem `--ctx-size` reservou o contexto
máximo de treino do modelo, 164.352 tokens. O KV cache chegou a cerca de 9 GB,
o RSS foi 12,3 GB e 3,3 GB do processo foram enviados para swap. A lentidão
resultante era causada principalmente por thrashing, não pela ausência de CUDA.

Em 2026-08-17, depois dos ajustes D18/D20, as medições no WSL registraram
geração e avaliação de prompt em 6,3 tok/s. Um prompt de 2.357 tokens levou
377 s para ingestão. A igualdade anômala entre essas taxas indica que o kernel
do quant ternário `Q1_0` desta build não tem caminho em lote: cada token de
prompt custa aproximadamente o mesmo que um token gerado.

O backend efetivo era `cpu`, na CPU i7-13800H (AVX2, sem AVX-512; 6 P-cores e
8 E-cores), com RSS de 1,28 GB, swap praticamente livre, `ctx-size` 16.384 e
quatro slots. `GET /metrics` retornou 501 porque o servidor não foi iniciado
com `--metrics`. Esses números descrevem esta máquina e não são critério de
desempenho para outras.

Com o mesmo prompt, omitir `chat_template_kwargs.enable_thinking=false` gerou
400 tokens de raciocínio em 85,6 s e retornou texto vazio. Com o parâmetro, a
resposta levou 1,5 s, gerou dois tokens e retornou `Sim`. `reasoning_budget: 0`
não funcionou nesta build.

## Decisão

Os IDs `AD-N` correspondem diretamente às decisões `D-N` do plano que originou
este registro.

| ID | Decisão | Rationale resumido |
|---|---|---|
| AD-1 | D1 — Copilot: smoke determinístico. | Sem endpoint arbitrário; interceptar internals é frágil. |
| AD-2 | D2 — Enforcement de privacidade em runtime. | Config prova intenção; rede prova isolamento. |
| AD-3 | D3 — Somente Bonsai 27B 1-bit (`Q1_0`). | Cabe na VRAM alvo e mantém tool calling. |
| AD-4 | D4 — `llama-server` no host WSL, fora do container. | Evita recarregar pesos na imagem ou por teste. |
| AD-5 | D5 — Não implementar modelo alternativo. | Um caminho reduz escopo; fallback exige replan. |
| AD-6 | D6 — Usar rede Docker dedicada com `--internal`. | Bloqueia egress e mantém acesso controlado ao host. |
| AD-7 | D7 — Permitir rede no build e isolar o runtime. | Download ocorre antes de conteúdo do repositório. |
| AD-8 | D8 — Provider Bonsai local; sem modelo selecionável. | Seleção dinâmica reintroduz provider externo. |
| AD-9 | D9 — `BonsaiServer` persistente. | Fixture reutiliza pesos e processo. |
| AD-10 | D10 — Remover código e testes de seleção de modelo. | Sem alternativas, seleção é código morto. |
| AD-11 | D11 — Enforce privacidade por config e por rede. | Cobre intenção e isolamento efetivo. |
| AD-12 | D12 — `--sleep-idle-seconds 600` nativo. | Libera memória sem watchdog ou corrida de teardown. |
| AD-13 | D13 — Integração somente em WSL/Linux. | OpenCode com endpoint arbitrário roda no WSL suportado. |
| AD-14 | D14 — Proxy TCP local. | Publica OpenCode sem `-p` e mantém isolamento. |
| AD-15 | D15 — Release fixado provisionado automaticamente. | Sem compilação ou instalação manual. |
| AD-16 | D16 — Timeout só guarda contra travamento. | CPU e recarga podem ser lentas sem falha. |
| AD-17 | D17 — Detectar capacidade CUDA pelo runtime. | `nvidia-smi` pode existir sem `libcudart`/`libcublas`. |
| AD-18 | D18 — Amostragem fixa; sem projector. | Temp/seed fixos melhoram repetibilidade. |
| AD-19 | D19 — Desempenho é propriedade do ambiente. | Sem pacotes de sistema, ambiente portátil e seguro. |
| AD-20 | D20 — `--ctx-size` fixo em 16.384 tokens. | Reduz KV cache; contexto do cliente é distinto. |
| AD-21 | D21 — Consolidar decisões neste ADR ao final. | Preserva o estado real após remoção do plano. |
| AD-22 | D22 — Reuso de prefixo: trabalho futuro. | Separar preparação de inferência antes de implementar. |
| AD-23 | D23 — Rejeitar `-t` explícito derivado da máquina. | O padrão do llama.cpp foi superior nas medições. |
| AD-24 | D24 — Asserir raciocínio desligado. | Evita regressão silenciosa e falha enganosa. |
| AD-25 | D25 — Rejeitar reduzir o servidor a um slot. | Quatro slots já reutilizaram cache; um slot foi pior. |
| AD-26 | D26 — Captura por log só em ambiguidade. | D27 respondeu sem instrumentação. |
| AD-27 | D27 — Medir reuso real pelo tempo de testes consecutivos. | Evitou proxy e verbosidade temporários. |
| AD-28 | D28 — Encerrar a rodada sem otimização adicional. | A evidência não sustenta implementar D22. |

### Detalhamento das decisões não óbvias

O Copilot permanece em smoke tests porque não há contrato suportado para
redirecionar seu backend LLM. Tentar interceptar chamadas internas faria o
harness depender de detalhes não documentados. Os testes comportamentais,
incluindo agentes, comandos e skills, rodam no OpenCode contra o Bonsai local.

`nvidia-smi` não prova que um binário CUDA pode executar no WSL: ele pode ser
exposto pelo driver do Windows enquanto o linker não encontra
`libcudart.so.12` e `libcublas.so.12`. O D17 testa essas bibliotecas e rebaixa
para Vulkan ou CPU sem instalar nada.

Timeout não mede sucesso. Uma máquina somente com CPU ou o primeiro request após
o sleep pode ser muito mais lenta. Os valores existentes servem apenas para
evitar bloqueio infinito durante uma falha real; nenhum teste exige latência.

A suíte não instala pacotes de sistema. `apt`, `sudo` e alteração de
`LD_LIBRARY_PATH` mutariam a máquina, variariam por distribuição e transformariam
um teste em uma operação de provisionamento. O binário fixado é baixado para o
cache do usuário; CUDA continua sendo uma escolha do ambiente.

O contexto mínimo no cliente e `--ctx-size` no servidor são controles distintos.
O primeiro reduz arquivos, ferramentas e ruído enviados em um prompt. O segundo
define a reserva do KV cache na inicialização do `llama-server`; reduzir o
primeiro não reduz a reserva do segundo.

### Resultados da rodada de otimização

D23 foi rejeitada. O padrão sem `-t` atingiu 6,262 tok/s de prompt e 5,003
tok/s de geração; `-t 6` atingiu 5,563 e 4,849, e `-t 14` atingiu 6,118 e
4,851, respectivamente. Nenhuma opção explícita superou o padrão.

D25 também foi rejeitada. Com quatro slots, as chamadas levaram 283,7 s e
84,4 s, com 1.311 `cached_tokens`; com um slot, 300,1 s e 86,7 s, com os mesmos
1.311 tokens. O segundo request com um slot foi 2,8% mais lento. Uma repetição
isolada do cache passou de 300,7 s para 83,2 s, redução de 72,3%, confirmando
que o servidor reutiliza prefixos sem exigir o slot único.

D26 não precisou ligar a verbosidade do servidor: D27 mediu os testes reais
consecutivos em 328,18 s, 245,18 s e 239,13 s. Há reuso real, mas parcial.
Esses testes isolados levaram de quatro a seis vezes mais que a suíte completa,
que executa 24 testes comportamentais em cerca de 22 minutos, aproximadamente
55 s por teste. A inconsistência indica que preparação — subida de container,
reinício do OpenCode e montagem de contexto — compõe parcela relevante do
cenário isolado, além da inferência.

D22 permanece aberto como trabalho futuro. Antes de qualquer implementação, é
obrigatório separar, em cada teste, o tempo de preparação do tempo de inferência.
Sem essa medição, o percentual de reuso isolado não justifica otimizar um
gargalo que pode não dominar a suíte.

## Implementação atual

### Modelo e servidor

`tests/integration/model/bonsai_server.py` usa somente a biblioteca padrão,
baixa `Bonsai-27B-Q1_0.gguf` e o binário do release fixado
`prism-b9596-9fcaed7` para o cache do usuário. A linha de comando efetiva
contém:

- `--ctx-size 16384`, vindo da constante nomeada `CONTEXT_SIZE`;
- `--jinja`, `--temp 0`, `--seed 42` e `--sleep-idle-seconds 600`;
- nenhum `--mmproj` e nenhum download do projector de visão.

Após o reinício explícito com `--down` e `--up`, o runtime observado foi:

| Métrica | Resultado |
|---|---|
| `/props` — `n_ctx` | 16.384 |
| `/props` — seed e temperature | 42 e 0,0 |
| `VmSwap` do processo | 0 kB |
| RSS do `llama-server` | 5.494.084 kB, aproximadamente 5,5 GB |

O detector escolheu o caminho CPU no WSL porque o runtime CUDA não estava
disponível. Isso é informativo e não é falha da suíte.

### OpenCode, Docker e proxy

O provider efetivo é `bonsai-local/bonsai-27b`, apontando para o
`llama-server` no host. O container usa somente a rede
`opencode-test-net` com `--internal`, mapeia o gateway real em
`host.docker.internal` e não usa publicação Docker com `-p`.

O acesso do host ao OpenCode passa por um proxy TCP limitado a `127.0.0.1`.
`--up`, `--rebuild`, `--down` e as fixtures controlam o PID persistido em
`/tmp/<container>-proxy.pid`. Se o container não fica pronto depois de o proxy
ser iniciado, o lifecycle agora encerra o proxy antes de propagar o erro; o
mesmo vale para o restart usado pelos contextos isolados.

O processo órfão encontrado usava deliberadamente porta 4198, IP antigo
`172.20.0.2` e o arquivo customizado
`/tmp/opencode-skill-debug-proxy.pid`. Ele foi iniciado no modo interno
`--proxy` fora de uma instância `DockerSession`; por isso o `--down` padrão só
conhecia outro PID e não podia encerrá-lo. O processo foi terminado e o arquivo
residual removido. O caminho suportado agora também limpa o proxy nos erros de
prontidão, que antes eram uma saída adicional do lifecycle.

### Testes e estado de validação

Os testes unitários do `BonsaiServer` e do `DockerSession` cobrem o novo
argumento, a ausência do projector e a limpeza do proxy após falha de prontidão.
Os testes OpenCode selecionados executaram contra o servidor local.

A suíte também envia uma mensagem curta pelo OpenCode efetivo e exige texto na
resposta. Se o raciocínio voltar a ser gerado, a falha orienta explicitamente a
verificar o repasse de `chat_template_kwargs.enable_thinking=false` ao provider
local, em vez de atribuir o problema ao conteúdo da resposta.

A execução solicitada da suíte terminou com 485 testes aprovados e 14 falhas
ambientais: Node/Playwright ausentes, Docling ausente, `crwl` ausente e
`codebase-memory-mcp` sem Node disponível. Nenhuma falha foi por estouro de
contexto, e nenhum pacote foi instalado para mascarar essas ausências.

## Consequências

- Prompts e artefatos do runtime OpenCode não dependem de provider externo.
- A rede interna e o teste de egress tornam a garantia de privacidade verificável.
- A amostragem determinística reduz divergência entre execuções do mesmo commit.
- O limite de 16.384 tokens elimina a reserva de KV cache de 164.352 tokens e
  torna estouro de contexto uma falha explícita, não uma degradação silenciosa.
- CPU é um caminho válido, mas pode deixar a suíte lenta; lentidão não reprova o
  teste.
- Após 10 minutos o modelo dorme e o primeiro request seguinte pode recarregá-lo.
- D22 não será implementada sem medir separadamente preparação e inferência por
  teste; a rodada de otimização está encerrada até então.
- O ambiente precisa fornecer WSL/Linux, Docker e os CLIs/recursos exigidos por
  cada marcador; a suíte não os instala automaticamente.
- Copilot CLI continua validando apenas o contrato de instalação e execução,
  não o comportamento de um agente.

## Alternativas rejeitadas

- **Provider externo nos testes comportamentais:** viola a garantia de privacidade
  e torna os resultados dependentes de rede e serviço remoto.
- **Modelos Bonsai menores que 27B:** são text-only e não têm o tool calling
  necessário para testar agentes.
- **Bonsai Ternary 27B:** seus 6,67 GB de pesos não cabem integralmente na VRAM
  alvo; o offload acrescentaria custo e variabilidade.
- **Qwen ou outro fallback automático:** aumentaria o escopo e esconderia uma
  insuficiência do único modelo aprovado.
- **CUDA como pré-requisito:** impediria CI e máquinas CPU; `nvidia-smi` também
  não demonstra que o runtime CUDA está instalado.
- **Watchdog próprio para o modelo:** duplicaria o sleep nativo e reintroduziria
  corridas entre derrubar o processo e atender uma requisição.
- **Publicar a porta do container com `-p`:** a rede `--internal` não permite
  essa rota de forma confiável e a publicação enfraqueceria o desenho isolado.
- **Reservar o contexto máximo de treino:** causa pressão de memória antes de
  qualquer request; reduzir somente o contexto enviado pelo cliente não resolve.
- **Instalar dependências de sistema durante os testes:** torna o ambiente
  mutável, não reprodutível e contrário ao D19.
- **`-t 6` ou `-t 14` explícito:** ambos ficaram abaixo do padrão do llama.cpp
  em prompt e geração; D23 foi rejeitada.
- **Um único slot no `llama-server`:** não aumentou o reuso e piorou a segunda
  chamada em 2,8%; D25 foi rejeitada.
- **Implementar D22 com o reuso isolado:** a discrepância com a suíte completa
  não separa preparação de inferência; D28 encerrou a rodada sem essa mudança.

## Asserções executáveis

Executar dentro do WSL/Linux, no diretório do repositório:

```bash
python3 tests/integration/model/bonsai_server.py --down
python3 tests/integration/model/bonsai_server.py --up
curl -s http://127.0.0.1:8080/props | tr "," "\n" | grep n_ctx
grep VmSwap /proc/<pid-do-llama-server>/status
ps -eo pid,rss,args | grep llama-server
```

As verificações da suíte e do isolamento são:

```bash
.venv/bin/pytest -m "unit or tools or opencode"
.venv/bin/pytest -m opencode \
  tests/integration/test_skills_activation.py::test_effective_provider_disables_thinking
docker exec opencode-config-test curl -s \
  http://host.docker.internal:8080/v1/models
docker exec opencode-config-test curl -s \
  https://api.openai.com
git grep -n "pytest.skip" -- tests
git grep -nE "sudo|apt-get|LD_LIBRARY_PATH" -- tests/
```

O primeiro request Docker deve retornar o JSON do Bonsai. A tentativa externa
deve falhar por DNS ou conexão, e não ser aprovada por uma resposta HTTP.
Além disso, a busca no checkout, excluindo `plan/`, por referências ao seletor
de modelo legado deve retornar vazia; a integração não deve conter
`pytest.skip` nem comandos de instalação de sistema.

Para verificar o lifecycle do proxy:

```bash
python3 tests/integration/docker/container_test_opencode.py --rebuild
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:4196/
ss -ltnp | grep 4196
python3 tests/integration/docker/container_test_opencode.py --down
```

O proxy deve aparecer somente em `127.0.0.1`; depois de `--down`, a mesma URL
deve recusar a conexão e nenhum processo `container_test_opencode.py --proxy`
deve permanecer.
