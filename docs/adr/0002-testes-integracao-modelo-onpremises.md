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
