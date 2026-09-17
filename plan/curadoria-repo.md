Status: REVISÃO DA CONSTRUÇÃO — itens a-h concluídos; modelo luna (max)

# Curadoria do Repo — opencode-global-config

## Insumo do humano

2026-09-14: "quero que o curador valide este repo."

## Verificações do devflow (2026-09-14, fase VALIDAÇÃO)

- `docs/README.md`: AUSENTE.
- Seção `## Testes por Especialidade` no `AGENTS.md`: AUSENTE.
- Workflows ativos em `plan/`: nenhum. Artefatos auxiliares existentes:
  `plan/mcp-codebase-memory-postergado.md` (registro de decisão),
  `plan/sec-shannon-integration.md` (Status: FUTURO).

## Gate de curadoria

Decidido em 2026-09-14 pelo humano: **tratar a curadoria agora**.
A curadoria é conduzida pelas fases de dev: planejamento item a item com
aprovação humana, construção com curador escrevendo docs/spec e
eng-software implementando testes-produto com TDD, validação final verde.

## Mapa de modelos

Decidido em 2026-09-14 pelo humano:

- PLANEJAMENTO (entrevista de curadoria): glm-5.3 (modelo corrente, sem troca).
- REVISÃO DO PLANO: glm-5.3 (corrente, sem troca).
- CONSTRUÇÃO: luna (max), com o agente worker disponível como apoio (2026-09-14).
- REVISÃO DA CONSTRUÇÃO: glm-5.3 (rev já configurado com esse modelo).
- TESTES: a confirmar com o humano na transição.

## Perguntas

### Rodada 3 — seção Elementos de Especificação (aberta em 2026-09-14)

Contexto: rodada 2 aprovada e já gravada em `docs/README.md`. Agora se
aprova a tabela de elementos + Regras de Documentação, adaptadas ao perfil
infra. Elementos já decididos fora: Modelo de Dados (DBML), Threat Model e
Identidade Visual (rodada 1) e Matriz ACL (rodada 2). Pontos de decisão
real nas perguntas P3.a–P3.e abaixo.

**Proposta de texto da seção:**

```markdown
## Elementos de Especificação

| Elemento | Formato/Ferramenta | Agente Responsável | Destino |
|----------|-------------------|-------------------|---------|
| Regras de Negócio | Lista Numerada | eng-software | docs/specs/regras-negocio.md |
| Critérios de Aceite + Requisitos | Concordion-Markdown — spec executável (Concordion/Groovy) | eng-software | docs/specs/ |
| RNFs Gerais | Concordion-Markdown — spec executável (Concordion/Groovy) | eng-software | docs/specs/rnf-gerais.md |
| Regras de Produto | Tabela | eng-software | nenhum |
| ADR (Arquitetura) | Concordion-Markdown (asserção executável obrigatória) | eng-software | docs/adr/ |
| Arquitetura (Diagrama Gerado) | Mermaid — C4 L1/L2 gerado dos ADRs | eng-software | docs/adr/diagrama-c4-l1.md, docs/adr/diagrama-c4-l2.md |
| UPSTREAM.md (skills externas) | Markdown padronizado | eng-software | harness-conf/skills/<skill>/UPSTREAM.md |
| README — Dependências | Markdown (seção do README) | eng-software | README.md |

### Regras de Documentação

#### Regras Gerais
- Documentação complementa o código, não o repete
- Doc derivável do código não se armazena — gere sob demanda
- Doc desatualizada é pior que ausência de doc
- Preferir formatos versionáveis (Markdown)
- Preferir especificações executáveis a documentação passiva

##### Regras de Negócio
- Derivado das histórias de usuário
- Formato de lista numerada, cada uma com a regra descrita claramente
- Cada regra deve ter um identificador único (ex: RN-001) para ser
  referenciada pelos requisitos funcionais
- Nenhuma Regra de Negócio pode ficar sem Requisito Funcional associado

##### Critérios de Aceite + Requisitos
- Cada funcionalidade deve ter arquivo de spec separado
- Critérios de aceite organizados por funcionalidade com base em coesão
- Cada critério de aceite deve referenciar o requisito (funcional ou não
  funcional) ao qual pertence
- Requisitos funcionais devem referenciar a(s) regra(s) de negócio que
  os originam (ex: RN-001)
- Nenhum requisito funcional ou não funcional pode ficar sem critério
  de aceite
- Todo exemplo da spec referencia a origem (requisito/regra) que o
  motivou
- Specs executadas pelo Concordion (fixtures Groovy); o texto é a spec —
  editar o texto muda o veredito do teste (link texto↔teste)

##### RNFs Gerais
- Arquivo sempre presente em `docs/specs/rnf-gerais.md`; fica vazio se
  não houver RNFs transversais
- Cada RNF com identificador (ex: `RNF-G-001`)
- Critérios executáveis; estratégia de execução avaliada por RNF

##### Regras de Produto
- Formato tabular: Regra | Descrição | Exceções
- Escopo: decisões que guiam a implementação (comportamentos padrão,
  limites, validações que o pacote deve impor)
- Descartadas junto com o arquivo de planejamento ao fim do ciclo

##### ADR (Arquitetura)
- Um arquivo Concordion-Markdown por decisão relevante em `docs/adr/`,
  numeração sequencial (padrão já existente no repo)
- Estrutura: Contexto | Decisão | Consequências | Alternativas
  consideradas | Asserção executável
- A asserção executável (fitness function) é OBRIGATÓRIA em todo ADR
  novo: valida que a decisão está implementada
- Os 6 ADRs legados (`docs/adr/0001`–`0006`) recebem retrofit para
  Concordion-Markdown com asserção executável — trabalho do ciclo de
  construção desta curadoria
- ADRs nunca são deletados — apenas superseded (novo ADR referencia o
  anterior)

##### Arquitetura (Diagrama Gerado)
- Gerado pelo eng-software a partir dos ADRs + análise do código
  (codebase-memory)
- Segue o modelo C4, apenas níveis 1 e 2:
  - L1 (diagrama-c4-l1.md): sistema e seus atores/sistemas externos
  - L2 (diagrama-c4-l2.md): containers internos (scripts, pacote
    Python, harness-conf, destinos sincronizados)
- Formato: bloco Mermaid (C4Context para L1, C4Container para L2)
- Regenerar sempre que um ADR for adicionado ou superseded
- Não editar manualmente — é artefato gerado

##### UPSTREAM.md (skills externas)
- Regra canônica na seção "Upstream de Skills Externas" do `AGENTS.md`;
  este documento referencia, não duplica
- Presente em toda skill baseada em repositório externo

##### README — Dependências
- Regra canônica na seção "README" do `AGENTS.md`; este documento
  referencia, não duplica
- Atualizada sempre que bootstrap, scripts, skills ou requisitos de
  instalação mudarem
```

**P3.a — Formato/ferramenta da spec executável** (Critérios de Aceite +
Requisitos e RNFs Gerais). EM EXPLORAÇÃO a pedido do humano (2026-09-14).
Critérios do humano: (1) flexibilidade comparável ao Concordion — exemplos
parametrizáveis, ligação rica spec↔código; (2) o artefato da spec funciona
também como documentação externa (legível/renderizável como doc do repo).

#### P3.a — Exploração de alternativas (2026-09-14)

**Ponte Concordion ↔ Python/pytest:** não existe binding oficial nem ponte
estável e mantida para Python (Concordion roda sobre Java/JUnit; há
Concordion.NET para .NET). Integração só seria possível rodando o motor
Java via subprocess — duas toolchains, cache de build Java e custo alto
para o benefício. Limitação declarada: análise por conhecimento do modelo,
sem verificação web; adoção/mantença podem ter mudado desde o treino.
Ferramenta ausente/morta na instalação vira finding bloqueante, conforme
interface de testes-produto.

**Alternativas no ecossistema Python/pytest:**

1. **pytest-bdd direto (Gherkin em `.feature`)**
   - Como funciona: specs Gherkin em `.feature`; steps ligados a funções
     Python via decoradores; `Esquema do Cenário` + `Exemplos`
     parametrizam; texto do step muda o teste (link texto↔teste forte).
   - Critério 1: atende bem (exemplos parametrizáveis, steps Python).
   - Critério 2: fraco — `.feature` não renderiza como doc do repo
     (GitHub mostra texto plano); doc externa teria que ser gerada
     (derivada, artefato duplo).
   - Custos: dev-dependency pytest-bdd; meio não é Markdown.

2. **Híbrido: Gherkin em Markdown, extraído para `.feature` e executado
   por pytest-bdd** (recomendação do curador)
   - Como funciona: spec fonte é Markdown com blocos ```gherkin (doc
     externa nativa); extrator fino gera `.feature` sob demanda em
     diretório temporário (não versionado — derivável); pytest-bdd
     executa o `.feature` gerado. Motor pronto, só o extrator é caseiro
     (~dezenas de linhas + testes).
   - Critério 1: atende — toda a flexibilidade do pytest-bdd
     (parametrização, steps Python).
   - Critério 2: atende — o Markdown é a fonte única, renderiza no
     GitHub e serve de doc externa.
   - Custos: extrator caseiro a manter (pequeno, testável, o repo já
     mantém tooling próprio); pipeline com etapa de geração.
   - Adequação à skill spec-executavel: Markdown como meio (favorecido
     pela skill) e Gherkin como formato (default da skill).

3. **doctest em Markdown (pytest `--doctest-glob`)**
   - Como funciona: blocos Python no Markdown executados como doctest
     com saída esperada; o próprio arquivo é doc e teste.
   - Critério 1: médio — sem vocabulário de negócio (Given/When/Then),
     sem parametrização de exemplos; ligação spec↔código é literal.
   - Critério 2: atende plenamente.
   - Custos: nenhum tooling novo; specs viram "exemplo de código com
     saída", não regra de negócio legível.

4. **byexample**
   - Como funciona: CLI que executa exemplos embutidos em
     Markdown/rST multi-linguagem (Python, shell etc.), com capturas e
     timeouts; relatório próprio.
   - Critério 1: médio — exemplos literais com capturas; não é spec de
     negócio parametrizável.
   - Critério 2: atende (Markdown).
   - Custos: ferramenta adicional fora do pytest; runner separado.

   Notas rápidas: `behave` e `radish` são variantes da opção 1 sem ganhar
   doc externa (`.feature`); notebooks executáveis (nbval/nbmake) foram
   descartados: JSON pesado, diff ruim, contra a regra de formatos
   versionáveis do template.

**Recomendação do curador:** opção 2 (híbrido). Fonte única em Markdown
atende o critério de documentação externa; o motor pytest-bdd entrega a
flexibilidade de Concordion que importa (exemplos parametrizados, texto do
step ligado ao teste); o custo caseiro fica restrito a um extrator fino
com testes próprios em `tests/`. Fallback pragmático: opção 1 (pytest-bdd
direto) se o humano rejeitar qualquer tooling caseiro.

#### P3.a — Avaliação das rotas A e B propostas pelo humano (2026-09-14)

Propostas do humano: (A) implementar em Python uma bridge mínima ao
modelo Concordion, evoluindo sob demanda; (B) rodar o motor oficial
Concordion com fixtures em Groovy (JVM/Gradle simplificado), só para as
specs executáveis. Limitação declarada: avaliação por conhecimento do
modelo, sem websearch; versões/adoção atuais exigem confirmação na
instalação (ferramenta ausente/morta = finding bloqueante, conforme
interface de testes-produto).

**Rota A — bridge Python própria (subset do modelo Concordion).** O
essencial do Concordion: parser das diretivas na spec
(set/execute/assertEquals/echo/verifyRows), binding comando↔função da
fixture, executor com comparação e a spec anotada como relatório. O
mínimo viável cobre set/execute/assertEquals em Markdown; verifyRows
(exemplos em tabela com veredito por linha) é a parte mais cara; o
relatório anotado completo fica de fora do "mínimo". Cada necessidade
futura é dev de framework, não de produto. Framework caseiro sem
comunidade: bugs de parser/executor caem no repo para sempre.

**Rota B — motor oficial Concordion + fixtures Groovy.** Plano:
`build.gradle` mínimo, fixtures Groovy enxutas, spec fonte em
Concordion-Markdown. Custos: JDK + Gradle user-space em WSL e Windows
(viável sem elevação: OpenJDK portável; Gradle wrapper baixa
distribution no primeiro run — rede); mais uma linguagem no repo;
integração com o orquestrador Python via subprocess que invoca o build
e parseia o XML JUnit (Concordion roda sobre JUnit; XML por fixture é
parseável) para montar `{ status, findings[] }`.

| Eixo | Rota A (bridge própria) | Rota B (oficial + Groovy) |
|------|------------------------|---------------------------|
| Risco | Alto: port parcial do motor, escopo crescente, sem comunidade | Médio: motor estável; risco em infra (JDK/Gradle/rede/parse) |
| Toolchain | Alinhado: 100% Python/pytest | Desalinhado: JVM + Groovy em 2 SOs, rede no 1º run |
| Tempo | Semanas de dev + manutenção contínua | Dias de setup + cola; JVM cold start cabe no teto de suíte fria (< 3 min) |
| Severidade | Falha do motor caseiro = bloqueante sem suporte externo | Falha de ambiente = bloqueante com instrução de instalação |
| Fingerprint/cache | Sem rede, sem fingerprint | Cache Gradle por hash; 1º run exige rede (retry 3x) |

**Veredito do curador: entre A e B, B é a melhor.** A é reimplementação
de framework — contraria o limite "não cria escopo"; o custo de A nunca
termina. B adota o motor de verdade e o esforço caseiro se limita à
cola de invocação (subprocess + parse XML), pequena e testável.
Condições para B: specs fonte em Concordion-Markdown como fonte única;
wrapper Python traduzindo resultado para `{ status, findings[] }`;
JDK+Gradle validados user-space no bootstrap dos dois SOs; aceitar rede
no primeiro run com retry.

#### P3.a — Resposta à pergunta de mérito: linguagem da spec (2026-09-14)

Pergunta do humano: como o híbrido Gherkin+pytest-bdd atenderia os
critérios, se o Concordion permite **qualquer** linguagem na confecção
da spec e o Gherkin impõe o seu formato?

**(a) O que Gherkin oferece e impõe.** Oferece: keywords localizáveis
(`# language: pt` → Dado/Quando/Então, E, Mas, Esquema do Cenário,
Exemplos); o CONTEÚDO de cada step é texto livre em qualquer língua — é
a frase do step que se liga ao código (matching com placeholders);
Esquema do Cenário parametriza por tabela; data tables e docstrings
carregam argumentos estruturados. Impõe: molde estrutural — cada linha
executável precisa de keyword no prefixo; prosa arbitrária solta no
documento NÃO é executável; a forma do documento é
Funcionalidade > Cenário > steps. "Apenas gherkin" significa, com
precisão: apenas o esqueleto é imposto; o vocabulário de negócio dentro
dos steps é livre.

**(b) O que Concordion oferece.** A spec é prosa livre (HTML ou
Markdown); diretivas embutidas (set/execute/assertEquals/echo/
verifyRows; no dialect Markdown, links discretos no texto) ligam
TRECHOS escolhidos da frase à fixture. Não há vocabulário controlado
nem molde: a linguagem da spec é livre de fato, no sentido levantado
pelo humano.

**Reconhecimento do curador:** o critério 1 da avaliação foi definido
estreito — "exemplos parametrizáveis + ligação spec↔código" — e nesse
sentido o híbrido atende. No sentido amplo levantado pelo humano
(liberdade de linguagem/estrutura na autoria da spec), o híbrido NÃO
atende: Gherkin troca liberdade de forma por vocabulário controlado (a
skill spec-executavel recomenda o molde como virtude — estrutura rígida,
leitura uniforme; é troca deliberada, não gratuíta).

**Critérios revisados:**
- 1a — parametrização + ligação spec↔teste: híbrido atende; B atende;
  A perseguiria a custo próprio.
- 1b — liberdade de linguagem/estrutura na autoria da spec (prosa
  instrumentável): SOMENTE B atende plenamente (motor oficial).
- 2 — artefato como doc externa: híbrido e B atendem (fonte Markdown).

**Efeito no veredito:** entre A e B permanece B. A distinção explícita
fortalece B: se 1b é requisito real do humano, B é a única rota que
atende; o híbrido só é equivalente se 1a bastar.

**Pergunta ao humano (P3.a, reformulada):** confirmar se 1b (liberdade
de linguagem/estrutura na autoria, só atendida pelo Concordion) é
requisito. Se sim, adotar a Rota B com as condições registradas; se 1a
bastar, o híbrido Gherkin+pytest-bdd é a opção de menor peso. Rota A
segue desaconselhada.

**P3.a ENCERRADA em 2026-09-14:** humano aprovou a Rota B (motor oficial
Concordion + fixtures Groovy) com as condições registradas — ver
## Decisões. Proposta de texto da seção atualizada nesta data
(tabela e Regras de Documentação agora refletem Concordion-Markdown).
P3.b–P3.e permanecem abertas.

**P3.b — Plano de Testes Manuais.** ENCERRADA em 2026-09-14: humano
decidiu REMOVER da tabela; plano manual sob demanda, sem artefato
obrigatório.

**P3.c — Diagrama de Arquitetura (C4 gerado).** ENCERRADA em
2026-09-14: humano decidiu MANTER (contrário à recomendação do
curador). Elemento reintroduzido na tabela proposta: Mermaid C4 L1/L2
gerado dos ADRs, agente eng-software, destino
`docs/adr/diagrama-c4-l1.md` e `docs/adr/diagrama-c4-l2.md`, com regra
de documentação própria — consta da proposta atualizada acima.

**P3.d — ADR com asserção executável.** ENCERRADA em 2026-09-14: humano
decidiu asserção executável OBRIGATÓRIA em todo ADR novo (contrário à
recomendação do curador). Regra do ADR atualizada na proposta acima.
Implicação: os 6 ADRs existentes (`docs/adr/0001` a `0006`) estão em
Markdown puro, sem asserção — tratamento definido na P3.f abaixo.

**P3.e — Agentes responsáveis.** ENCERRADA em 2026-09-14: humano
confirmou eng-software para TODOS os elementos da tabela (incluindo
UPSTREAM.md e README — Dependências).

**P3.f — Tratamento dos 6 ADRs existentes.** ENCERRADA em 2026-09-14:
humano decidiu RETROFIT (converter os 6 ADRs legados para
Concordion-Markdown com asserção executável; contrário à recomendação
do curador de exceção registrada). Retrofit é trabalho do ciclo de
construção desta curadoria.

**Rodada 3 — estado:** ENCERRADA em 2026-09-14. Todas as sub-perguntas
(P3.a–P3.f) decididas; texto final consolidado APROVADO pelo humano
(via devflow) e GRAVADO no `docs/README.md` (seção "Elementos de
Especificação" + Regras de Documentação, após a Definição de Escopo).

### Rodada 4 — seção Estratégias de Indexação de Código (aberta em 2026-09-14)

Contexto: o template default traz apenas uma tabela com o
codebase-memory CLI. O humano decidiu (P4.a) que só o codebase-memory é
estratégia de indexação de código: skill code-explorer-priority, ADRs e
AGENTS.md saíram da tabela. P4.b aprovado: só a tabela, sem texto
abaixo. O humano pediu para REVER O TEXTO AJUSTADO ANTES DE GRAVAR.

**Proposta de texto da seção (ajustada):**

```markdown
## Estratégias de Indexação de Código

| Ferramenta | Uso | Instalação |
|-----------|-----|-----------|
| codebase-memory CLI | Grafo de código e docs; navegação estrutural e consulta de seções. | `codebase-memory-mcp cli` |
```

**Estado:** ENCERRADA em 2026-09-14. Texto ajustado (tabela de 1 linha)
APROVADO pelo humano (via devflow) e GRAVADO no `docs/README.md`.

### Rodada 5 — seção Testes por Especialidade (aberta em 2026-09-14)

Seção mais densa; entrevista em blocos, UMA ESPECIALIDADE POR VEZ
(mediada pelo devflow):
- Bloco 1 (este): estrutura geral da seção + especialidades aplicáveis.
- Bloco 2: suíte backend (ferramentas com catálogo como referência,
  critérios, orçamento).
- Bloco 3: suíte segurança (idem).
- Bloco 4 (se couber): suítes dados/frontend, conforme P5.a.
- Bloco 5: orquestrador `testes-produto` (suítes chamadas, JSON
  agregado, tetos de orçamento, retry, cache/fingerprint).

Contexto do repo: Python em `src/` + `scripts/`, pytest em `tests/`
(markers unit/integration/agent_eval, `-m all`); sem BD de produto e
sem UI. Linguagem dos scripts já decidida na rodada 1: Python, JSON
`{ status, findings[] }`, sem argumentos, exit 0/1.

**Proposta de estrutura geral da seção (blocos invariantes do
template):**

```markdown
## Testes por Especialidade

Scripts por especialidade e o orquestrador `testes-produto`.
Interface JSON: `{ status, findings[] }`. Exit 0 = pass,
exit 1 = fail. Sem argumentos.

O orquestrador chama as suítes definidas nesta seção e agrega o
relatório. Falha se qualquer suíte falhar.

Critérios, orçamento e ferramentas saem da entrevista de
curadoria. Fingerprint e cache ficam em `testes-produto/target/`
e não são versionados.

**PROIBIDO:** bypassar, comentar, remover ou condicionar
qualquer verificação. Ferramenta ausente não justifica
remoção — reporte finding com instrução de instalação.

### Dois níveis de teste

1. **Testes da aplicação** — validam o produto em
   desenvolvimento. Rodam via suítes/orquestrador
   `testes-produto` na fase Testes do workflow, sempre que
   se desenvolve funcionalidade.
2. **Testes dos scripts de teste** — os scripts de suíte e
   o orquestrador são código e têm testes próprios. Esta
   seção é a especificação executável deles: os testes dos
   scripts cobrem exatamente o que ela define (suítes,
   interface JSON, orçamento, proibições). Rodam SOMENTE
   quando os scripts mudam — por exemplo, curadoria
   alterando ferramentas ou critérios por orientação do
   humano —, nunca no ciclo normal de desenvolvimento.

O `AGENTS.md` do projeto mantém apenas a tabela índice das
suítes com link para esta seção
(`docs/README.md#testes-por-especialidade`).
```

**P5.a — Especialidades aplicáveis.** ENCERRADA em 2026-09-14: humano
escolheu reduzir às aplicáveis — `testes-produto/backend` +
`testes-produto/seguranca`; sem suítes pass-through de dados/frontend;
especialidades novas entram depois por curadoria. (Opções originais:
manter 4 com pass-through; reduzir às aplicáveis; outro recorte.)

**P5.b — Nomes canônicos.** ENCERRADA em 2026-09-14: manter os nomes
canônicos backend/seguranca (aderentes à interface, à tabela índice do
AGENTS.md e ao template).

**P5.c — Blocos invariantes.** ENCERRADA em 2026-09-14: aprovados como
no template (PROIBIDO, Dois níveis de teste, nota do AGENTS.md), sem
adaptação.

**Bloco 1 — estado:** ENCERRADO em 2026-09-14. P5.a (reduzir para
backend + seguranca), P5.b (nomes canônicos backend/seguranca) e P5.c
aprovados; estrutura geral da seção APROVADA (gravação no fechamento
da rodada 5). Nota: o texto da estrutura já diz "o orquestrador chama
as suítes definidas nesta seção", cobrindo a adaptação da interface
(que menciona "quatro suítes") ao recorte aprovado.

### Rodada 5, bloco 2 — suíte `testes-produto/backend` (aberto em 2026-09-14)

Referência: catálogo testes-produto-catalog (backend: análise estática,
cobertura mínima, testes). Contexto do repo: pytest com markers
unit/integration/agent_eval e atalho `-m all`; executável do `.venv`
por SO (`.venv/bin/pytest` no WSL/Linux, `.\.venv\Scripts\pytest.exe`
no Windows); scripts bash e PowerShell no bootstrap; regra do repo:
suíte completa do ambiente corrente, sem seleção reduzida.

**Proposta de subseção (rascunho atualizado pós P5.2.a–P5.2.e):**

```markdown
### backend

**Arquivo:** `testes-produto/backend`

**Descrição:** Testes e análise do pacote Python e dos scripts do repo.

**O que deve conter:**
- Suíte pytest completa do ambiente corrente (`-m all`, executável do
  `.venv` do SO); teste falho = bloqueante
- Análise estática Python: ruff; violação = bloqueante
- Análise estática shell: shellcheck nos scripts `.sh`; violação =
  bloqueante
- Análise estática PowerShell: PSScriptAnalyzer nos scripts `.ps1`;
  violação = bloqueante
- Cobertura: pytest-cov; cobertura total abaixo de 70% = bloqueante.
  Enquanto o repo estiver abaixo de 70%, o ciclo de construção
  implementa testes até atingir o mínimo (não é finding passivo)

**Ferramentas:** pytest (`.venv` do SO), ruff, shellcheck,
PSScriptAnalyzer, pytest-cov

**Critérios:** qualquer teste falho, violação de lint ou cobertura
abaixo de 70% = finding bloqueante. Ferramenta ausente = finding
bloqueante com instrução de instalação (não remove o check).
```

**Ajuste decorrente da P5.2.e na estrutura geral (aplicar na gravação
final da rodada 5):** na intro aprovada no bloco 1, a frase "Critérios,
orçamento e ferramentas saem da entrevista de curadoria." passa a
"Critérios e ferramentas saem da entrevista de curadoria." (sem nota
explicativa; a decisão sobre orçamento vive apenas em ## Decisões
deste plan).

**P5.2.a — Check principal.** ENCERRADA em 2026-09-14: pytest `-m all`
(executável do `.venv` do SO, suíte completa do ambiente corrente),
bloqueante.

**P5.2.b — Análise estática.** ENCERRADA em 2026-09-14: ruff (Python),
shellcheck (`.sh`) e PSScriptAnalyzer (`.ps1`), todos bloqueantes.

**P5.2.c — mypy.** ENCERRADA em 2026-09-14: FORA da suíte
(recomendação do curador aceita).

**P5.2.d — Cobertura.** ENCERRADA em 2026-09-14: humano rejeitou
baseline congelado; mínimo de 70% (pytest-cov), bloqueante. Enquanto o
repo estiver abaixo de 70%, o ciclo de construção desta curadoria
implementa testes até atingir o mínimo (não é finding passivo).

**P5.2.e — Orçamento.** ENCERRADA em 2026-09-14: humano REMOVEU o
conceito de orçamento deste repo (após esclarecimento de que teto não
interrompe teste). Nenhuma duração é comparada a teto; suítes rodam até
o fim. Adaptação explícita registrada na subseção e na intro da seção
(ver "Ajuste decorrente" acima); a interface-testes-produto é
referência, o spec efetivo é a seção.

**Bloco 2 — estado:** ENCERRADO em 2026-09-14. Subseção backend
APROVADA pelo humano (via devflow) como no rascunho final: pytest
`-m all` + ruff + shellcheck + PSScriptAnalyzer bloqueantes; cobertura
mínima 70% bloqueante (abaixo disso a construção implementa testes até
atingir); sem mypy; sem bloco de orçamento. Gravação no fechamento da
rodada 5.

### Rodada 5, bloco 3 — suíte `testes-produto/seguranca` (aberto em 2026-09-14)

Referência: catálogo testes-produto-catalog (segurança: SAST, secrets
scan, dependency check, DAST). Contexto do repo: sem aplicação web
publicada, sem BD, scripts user-space; dependências Python em
pyproject/`.venv`; plano FUTURO de Shannon CLI
(`plan/sec-shannon-integration.md`) — não é check agora; quando Shannon
entrar, nova curadoria decide.

**Proposta de subseção (rascunho final pós P5.3.a–P5.3.d):**

```markdown
### segurança

**Arquivo:** `testes-produto/seguranca`

**Descrição:** Segurança — secrets, dependências, análise estática de
segurança.

**O que deve conter:**
- Secrets scan: gitleaks no repositório inteiro; segredo detectado =
  bloqueante
- Auditoria de dependências Python: pip-audit (cruza dependências com
  bases de CVE/OSV); vulnerabilidade high/critical = bloqueante;
  demais severidades = melhoria
- SAST: bandit no código Python próprio; achado high/critical =
  bloqueante; demais = melhoria

**Ferramentas:** gitleaks, pip-audit, bandit

**Critérios:** segredo detectado, vulnerabilidade high/critical ou
achado SAST high/critical = finding bloqueante. Ferramenta ausente =
finding bloqueante com instrução de instalação (não remove o check).
Ferramentas com rede seguem retry 3x; esgotado = finding bloqueante
com instrução de rede.
```

Nota da entrevista: o pedido do humano por "alguma coisa com CVE
também" é atendido pelo pip-audit (cobertura de CVE de dependências);
bandit cobre SAST do código próprio. Sem bloco de orçamento (padrão
decidido no bloco 2).

**P5.3.a — Escopo.** ENCERRADA em 2026-09-14: recorte CONFIRMADO —
secrets + pip-audit + SAST; sem DAST.

**P5.3.b — Secrets scan.** ENCERRADA em 2026-09-14: gitleaks.

**P5.3.c — SAST.** ENCERRADA em 2026-09-14: bandit. Nota do humano:
"bandit, mas quero alguma coisa com cve também" — cobertura de CVE
atendida pelo pip-audit do recorte (validada na aprovação da
subseção).

**P5.3.d — Severidades.** ENCERRADA em 2026-09-14: high/critical
bloqueante, demais melhoria; segredo sempre bloqueante.

**Bloco 3 — estado:** ENCERRADO em 2026-09-14. Subseção segurança
APROVADA pelo humano (via devflow) como no rascunho final: gitleaks +
pip-audit + bandit; severidades high/critical bloqueante; retry 3x;
sem bloco de orçamento. Gravação no fechamento da rodada 5.

### Rodada 5, bloco 4 — agregador `testes-produto` (retomado em 2026-09-14)

Referência: interface-testes-produto.md (contrato de saída, retry,
proibições, pass-through, cobertura estática; seção "## Agregador"
após a renomeação) e template default (subseção "### Agregador").
Adaptações já decididas: suítes definidas na seção = backend +
seguranca; SEM conceito de orçamento/tetos; sem parágrafos de
negação na spec; papéis explícitos (script agrega; `qa` executa na
fase Testes; curador valida evidência; devflow não executa).

**Proposta de subseção (rascunho para o docs/README.md):**

```markdown
### Agregador

**Arquivo:** `testes-produto`

Chama as suítes definidas nesta seção (`testes-produto/backend` e
`testes-produto/seguranca`) e consolida o relatório no fim.
`status` é `fail` se qualquer suíte falhar. Não reabre entrevista
nem inventa check. Executado pelo agente `qa` na fase Testes do
workflow; o `curador-produto` valida a evidência da execução.

- Interface JSON `{ status, findings[] }` em stdout, UTF-8; progresso
  em stderr; exit 0 = pass, 1 = fail; sem argumentos; idempotente
- Suíte que não executa (crash ou exit inesperado) = finding
  bloqueante com instrução de correção
- Retry de rede é interno a cada suíte (3 tentativas; esgotado =
  finding bloqueante com instrução de rede)
- Os scripts de suíte e o agregador são código de produção: entram
  no mesmo scan e no mesmo nível de qualidade (ruff, pytest,
  cobertura) — proibido afrouxar o gate para código de teste
```

**Perguntas válidas (re-apresentadas pós-renomeação; só o termo e os
papéis mudaram):**

**Bloco 4 — estado:** ENCERRADO em 2026-09-14, com feedback do humano
("não perguntar o óbvio nem o que já está na definição básica"):
- P5.4.a: chamada nominal CONFIRMADA (backend + seguranca; nova
  especialidade entra por curadoria).
- P5.4.b: suíte que morre sem JSON = falha bloqueante com instrução
  (fail-closed; padrão da interface; humano confirmou "é claro").
- P5.4.c: SEM cache/fingerprint — decisão registrada só no plan.
- P5.4.d: código de suíte e agregador no mesmo gate de produção
  (já fixado na interface, "Cobertura Estática").

**REGRA DE MEDIAÇÃO (humano, 2026-09-14, obrigatória daqui em
diante):** perguntas UMA POR VEZ; antes de formular, verificar se a
resposta já consta da interface, dos templates ou de decisões
anteriores — nada de perguntar o já decidido/definido.

**Rodada 5 — estado:** ENCERRADA em 2026-09-14. Seção completa
"Testes por Especialidade" GRAVADA no `docs/README.md` (intro com
agregador e sem frases de orçamento/cache; blocos invariantes;
subseções backend, segurança e Agregador aprovadas). Na gravação: a
frase "Fingerprint e cache ficam em `testes-produto/target/`..." foi
omitida por coerência com P5.4.c (conceito removido; sem frase de
negação).

### Rodada 6 — `AGENTS.md` (aberta em 2026-09-14)

Escopo: gravar no `AGENTS.md` do repo (1) a tabela índice
`## Testes por Especialidade` com link âncora para
`docs/README.md#testes-por-especialidade` e (2) a seção
`## Instruções por Agente`. Base:
`default-artifacts/testes-por-especialidade-template.md` (já
renomeado para agregador) e
`default-artifacts/instrucoes-por-agente-template.md`.

**Proposta de tabela índice (derivada das decisões já tomadas;
nenhuma decisão nova):**

```markdown
## Testes por Especialidade

| Especialidade | Script |
|---------------|--------|
| backend | `testes-produto/backend` |
| segurança | `testes-produto/seguranca` |

Agregador: `testes-produto`

Executado pelo agente `qa` na fase Testes; a evidência é
validada pelo `curador-produto`.

Spec: [docs/README.md#testes-por-especialidade](docs/README.md#testes-por-especialidade)
```

**Proposta de Instruções por Agente:** subseções para os agentes do
workflow (eng-software, dba, front, sec, qa, rev, curador-produto),
todas com `SEM INSTRUÇÕES A PEDIDO DO HUMANO` (fallback do
template), salvo instrução que o humano definir.

**P6.a — Instruções por Agente.** ENCERRADA em 2026-09-14: SEM
INSTRUÇÕES A PEDIDO DO HUMANO para todos os 7 agentes. Tabela índice
aprovada sem objeção.

**Rodada 6 — estado:** ENCERRADA em 2026-09-14. Gravado no
`AGENTS.md` do repo: seção `## Testes por Especialidade` (tabela
índice backend/segurança + Agregador + papéis + link âncora para
`docs/README.md#testes-por-especialidade`) e seção
`## Instruções por Agente` (7 subseções com SEM INSTRUÇÕES A PEDIDO
DO HUMANO).

**Entrevista de curadoria: CONCLUÍDA em 2026-09-14.** Nenhuma
pergunta aberta.

## Correção de papéis e renomeação do script — diffs a aprovar (2026-09-14)

Desenho-alvo confirmado pelo humano (fontes: `qa.md`, `devflow.md`,
`docs/workflow-agentes-dev.md`, regras 27/28): o script
`testes-produto` é AGREGADOR mecânico das suítes; o agente `qa` o
executa na fase Testes; o `curador-produto` só lê a evidência; o
`devflow` (orquestrador do workflow) não executa testes de produto.
RENOMEAÇÃO aprovada: "orquestrador" sai da documentação referente ao
script, que passa a ser chamado AGREGADOR; "orquestrador" fica
reservado ao agente devflow. Diffs refeitos com o termo agregador; a
aprovar UM A UM pelo humano antes de gravar. Escalonamento: renomeação
nos demais arquivos (devflow.md, qa.md, dba.md, eng-software.md,
sec.md, docs/workflow-agentes-dev.md) + scaffold_mapa.py + testes do
scaffold + suíte verde no fim = UM item único da fase de construção.

### Diff 1 — `harness-conf/agents/default-artifacts/doc-readme-template.md`

a) Intro da seção "Testes por Especialidade" (atual):

```markdown
Scripts por especialidade e o orquestrador `testes-produto`.
Interface JSON: `{ status, findings[] }`. Exit 0 = pass,
exit 1 = fail. Sem argumentos.

O orquestrador chama as quatro suítes e agrega o relatório.
Falha se qualquer suíte falhar.
```

→ corrigido:

```markdown
Scripts por especialidade e o agregador `testes-produto`.
Interface JSON: `{ status, findings[] }`. Exit 0 = pass,
exit 1 = fail. Sem argumentos.

O agregador `testes-produto` chama as quatro suítes e
consolida o relatório. Falha se qualquer suíte falhar.
Quem o executa na fase Testes é o agente `qa`; o
`curador-produto` valida a evidência.
```

b) "Dois níveis de teste", item 1 (atual):

```markdown
1. **Testes da aplicação** — validam o produto em
   desenvolvimento. Rodam via suítes/orquestrador
   `testes-produto` na fase Testes do workflow, sempre que
   se desenvolve funcionalidade.
```

→ corrigido:

```markdown
1. **Testes da aplicação** — validam o produto em
   desenvolvimento. Rodam via suítes/agregador
   `testes-produto`, executados pelo agente `qa` na fase
   Testes do workflow, sempre que se desenvolve funcionalidade.
```

c) Subseção "### Orquestrador" (atual):

```markdown
### Orquestrador

**Arquivo:** `testes-produto`

Chama as quatro suítes (`testes-produto/backend`,
`testes-produto/dados`, `testes-produto/seguranca`,
`testes-produto/frontend`) e agrega o
relatório no fim. `status` é `fail` se qualquer suíte
falhar. Não reabre entrevista nem inventa check.
```

→ corrigido:

```markdown
### Agregador

**Arquivo:** `testes-produto`

Chama as quatro suítes (`testes-produto/backend`,
`testes-produto/dados`, `testes-produto/seguranca`,
`testes-produto/frontend`) e consolida o
relatório no fim. `status` é `fail` se qualquer suíte
falhar. Não reabre entrevista nem inventa check.
Executado pelo agente `qa` na fase Testes do workflow; o
`curador-produto` valida a evidência da execução.
```

### Diff 2 — `harness-conf/agents/default-artifacts/testes-por-especialidade-template.md`

Atual:

```markdown
Orquestrador: `testes-produto`

Spec: [docs/README.md#testes-por-especialidade](docs/README.md#testes-por-especialidade)
```

→ corrigido:

```markdown
Agregador: `testes-produto`

Executado pelo agente `qa` na fase Testes; a evidência é
validada pelo `curador-produto`.

Spec: [docs/README.md#testes-por-especialidade](docs/README.md#testes-por-especialidade)
```

### Diff 3 — `harness-conf/agents/references/interface-testes-produto.md`

Seção "## Orquestrador" (atual):

```markdown
## Orquestrador

- Comando sem argumentos (padrão: `testes-produto`)
- Chama as quatro suítes (backend, dados, segurança, frontend)
  e agrega `findings`
- `status` é `fail` se qualquer suíte falhar
- Não substitui a entrevista de ferramentas por especialidade
```

→ corrigido:

```markdown
## Agregador

- Comando sem argumentos (padrão: `testes-produto`)
- Chama as quatro suítes (backend, dados, segurança, frontend)
  e consolida `findings`
- `status` é `fail` se qualquer suíte falhar
- Execução na fase Testes do workflow: agente `qa` (o script
  apenas agrega suítes)
- Evidência da execução validada pelo `curador-produto`
- Não substitui a entrevista de ferramentas por especialidade
```

### Diff 4 — `harness-conf/agents/references/mensagens-curadoria.md`

a) Atual (parágrafo explicativo):

```markdown
Especialidade — que traduz regras de qualidade em suítes
(backend, dados, segurança, frontend) e no orquestrador
`testes-produto`. O `AGENTS.md` mantém só a tabela índice
```

→ corrigido:

```markdown
Especialidade — que traduz regras de qualidade em suítes
(backend, dados, segurança, frontend) e no agregador
`testes-produto`. O `AGENTS.md` mantém só a tabela índice
```

b) Atual (recomendação):

```markdown
conduzirão o trabalho: o `devflow` media o processo seção a seção com
sua aprovação, o `curador-produto` especifica os artefatos e o
`eng-software` implementa os scripts. Se preferir seguir
```

→ corrigido:

```markdown
conduzirão o trabalho: o `devflow` media o processo seção a seção com
sua aprovação, o `curador-produto` especifica os artefatos, o
`eng-software` implementa os scripts e o `qa` executa o
`testes-produto` na fase Testes. Se preferir seguir
```

### Diff 5 — `harness-conf/agents/curador-produto.md`

Substituições por trecho (onde "orquestrador" se refere ao SCRIPT
`testes-produto`; ocorrências que se referem ao devflow permanecem):

a) Frontmatter, description (atual: "valida evidência
   do orquestrador no fim da fase Testes") → "valida evidência
   do agregador no fim da fase Testes".

b) Capacidade 1, item 4 (atual):

```markdown
4. **Testes por Especialidade** — spec das suítes e do
   orquestrador `testes-produto` (suítes, interface
   JSON, orçamento, proibições).
```

→ corrigido:

```markdown
4. **Testes por Especialidade** — spec das suítes e do
   agregador `testes-produto`, executado pelo `qa` na fase
   Testes (suítes, interface JSON, orçamento, proibições).
```

c) Capacidade 2, fluxo de entrevista, item 2 (atual: "Entreviste
   especialidades (backend, dados, segurança, frontend) e o
   orquestrador `testes-produto` na seção do `docs/README.md`.") →
   "... e o agregador `testes-produto` na seção do
   `docs/README.md`.".

d) Capacidade 2, "Orientação ao humano" (atual):

```markdown
níveis de teste: (1) testes da aplicação rodam via
suítes/orquestrador `testes-produto` na fase Testes,
sempre que se desenvolve funcionalidade; (2) testes dos
```

→ corrigido:

```markdown
níveis de teste: (1) testes da aplicação rodam via
suítes/agregador `testes-produto`, executados pelo agente
`qa` na fase Testes, sempre que se desenvolve
funcionalidade; (2) testes dos
```

e) Capacidade 3 — título e texto (atuais):

```markdown
### 3. Validar evidência do orquestrador

Não valida evidências na Construção nem na Revisão da
Construção. Valida no fim da fase Testes se o
orquestrador `testes-produto` rodou.
```

→ corrigidos:

```markdown
### 3. Validar evidência do agregador

Não valida evidências na Construção nem na Revisão da
Construção. Valida no fim da fase Testes se o agente `qa`
executou o agregador `testes-produto` (o devflow,
orquestrador do workflow, não executa testes de produto).
```

   E no passo 2 da mesma capacidade (atual: "Ler a evidência do
   orquestrador no arquivo de planejamento") → "Ler a evidência do
   agregador no arquivo de planejamento".

f) Capacidade 4 (atual):

```markdown
Ao final do trabalho de curadoria, os scripts de
testes-produto implementados são executados. Você verifica
o sucesso (verde) — validação objetiva que resolve a regra
"não valida o que editou".
```

→ corrigido:

```markdown
Ao final do trabalho de curadoria, os scripts de
testes-produto implementados são executados. Você verifica
o sucesso (verde) — validação objetiva que resolve a regra
"não valida o que editou". Papéis: na fase Testes do
workflow, o executor de rotina do `testes-produto` é o
`qa`; o devflow (orquestrador do workflow) não executa
testes de produto; você valida a evidência.
```

g) Formato de Saída "Validação de Testes": na tabela,
   "| orquestrador | testes-produto |" →
   "| agregador | testes-produto |"; em Falhas,
   "- **orquestrador**: evidência ausente." →
   "- **agregador**: evidência ausente.".

### Diff 6 — `harness-conf/skills/testes-produto-catalog/SKILL.md`

a) Frontmatter, description (atual: "e o orquestrador
   testes-produto.") → "e o agregador testes-produto.".

b) Corpo (atual):

```markdown
Exit code: 0 = pass, 1 = fail. O orquestrador chama as
quatro suítes e agrega `findings`. Falha se qualquer
suíte falhar.
```

→ corrigido:

```markdown
Exit code: 0 = pass, 1 = fail. O agregador `testes-produto`
chama as quatro suítes e consolida `findings`. Falha se
qualquer suíte falhar. Executado pelo agente `qa` na fase
Testes do workflow; a evidência é validada pelo
`curador-produto`.
```

### Reflexo no rascunho da rodada 5 (aplicar na gravação final)

a) Subseção do bloco 4 passa a se chamar "### Agregador", com o
   texto (alinhado ao Diff 1c):

```markdown
### Agregador

**Arquivo:** `testes-produto`

Chama as suítes definidas nesta seção (`testes-produto/backend` e
`testes-produto/seguranca`) e consolida o relatório no fim.
`status` é `fail` se qualquer suíte falhar. Não reabre entrevista
nem inventa check. Executado pelo agente `qa` na fase Testes do
workflow; o `curador-produto` valida a evidência da execução.
```

b) A intro da estrutura geral (aprovada no bloco 1) também usa
   "orquestrador": ao gravar a seção final, aplicar a renomeação —
   "Scripts por especialidade e o agregador `testes-produto`." e
   "O agregador `testes-produto` chama as suítes definidas nesta
   seção e consolida o relatório."

O bloco 4 da rodada 5 fica pausado até a renomeação ser aprovada e
aplicada; as perguntas P5.4.a–P5.4.d continuam válidas.

## Emendas pós-revisão do plano — diffs a aprovar (2026-09-14)

Origem: revisão do plano (relatório do `rev` em ## Relatórios); 4
bloqueantes com resolução decidida pelo humano + melhorias 5-11
incorporadas à construção. Diffs a aprovar pelo humano (via devflow)
antes de aplicar. Nenhum arquivo editado ainda.

Estado corrente do pacote: APLICADO em 2026-09-14 (todas as emendas
aprovadas pelo humano, via devflow). Resumo da aplicação:
- Ema v2 (regra intacta + exceção `testes-produto/` como código
  produtivo suscetível a testes): aplicada ao `AGENTS.md`.
- Emb: CANCELADA (sem aplicação; agregador permanece como gravado).
- Emc (Dois níveis, path `testes-produto/tests/`): aplicada ao
  `docs/README.md`.
- Emd v2 (interface: Agregador puro + specs por especialidade via
  Concordion como infra interna + path da suíte meta): aplicada.
- Eme v2 (template: bullet de specs por especialidade nas 4 subseções
  + path da suíte meta no nível 2 + residual "orquestrador"
  resolvido): aplicada.
- Emf v2 (tabela índice com reflexos do modelo novo): aplicada.
- Emg (curador-produto.md: path da suíte meta): aplicada.
- Emh (C4 L1/L2/L3 com gate de julgamento): aplicada ao
  `docs/README.md` (tabela + regra).
- Emi (specs executáveis por especialidade: bullets + Ferramentas nas
  subseções backend/segurança + regra de alocação em Elementos):
  aplicada ao `docs/README.md`.
Verificação pós-aplicação (grep): "verificador de specs" ausente em
todos os arquivos (Emb cancelada de fato); `testes-produto/tests/`
presente nos 6 arquivos esperados; `docs/README.md` sem ocorrência de
"orquestrador".

### Ema — `AGENTS.md` do repo: regra de runners (achado 1)

**Ema v1 — RECUSADA pelo humano (2026-09-14).** Redação proposta
(veto só para runner trivial; scripts de suíte e agregador têm testes
próprios em `testes-produto/tests/`). Motivo da recusa, literal: a
regra continua valendo; testes-produto não são testes, são código
produtivo das validações usadas pelos agentes e são suscetíveis a
testes; não relaxar a regra, no máximo criar exceção para os scripts
dentro de `testes-produto/`. Histórico preservado.

**Ema v2 — redação corrente.** Atual:

```markdown
- Não crie testes para scripts cuja única função é executar ou orquestrar
  testes.
```

→ corrigido (regra intacta + exceção explícita):

```markdown
- Não crie testes para scripts cuja única função é executar ou orquestrar
  testes. Exceção: scripts dentro de `testes-produto/` não são testes —
  são código produtivo das validações usadas pelos agentes e, como
  tais, são suscetíveis a testes (suíte meta em
  `testes-produto/tests/`, que roda quando os scripts mudam).
```

### Emb — `docs/README.md`: subseção Agregador (achado 3) — CANCELADA

CANCELADA pela reversão do achado 3 (2026-09-14): o agregador volta
ao papel puro; a subseção Agregador gravada permanece como está (sem
"verificador de specs"). Histórico da proposta v1 (Concordion direto
no agregador) preservado no histórico desta seção e em ## Decisões.

### Emi — `docs/README.md`: specs executáveis por especialidade (reversão do achado 3)

a) Subseção backend — "O que deve conter" (atual) termina em:

```markdown
- Cobertura: pytest-cov; cobertura total abaixo de 70% = bloqueante.
  Enquanto o repo estiver abaixo de 70%, o ciclo de construção
  implementa testes até atingir o mínimo (não é finding passivo)
```

→ acrescenta ao final do bloco:

```markdown
- Specs executáveis da especialidade backend (Concordion-Markdown de
  `docs/specs/`), rodadas via Concordion com tradutor Python interno
  à suíte; spec falhando = bloqueante
```

E **Ferramentas** passa a: pytest (`.venv` do SO), ruff, shellcheck,
PSScriptAnalyzer, pytest-cov, Concordion (tradutor Python).

b) Subseção segurança — "O que deve conter" (atual) termina em:

```markdown
- SAST: bandit no código Python próprio; achado high/critical =
  bloqueante; demais = melhoria
```

→ acrescenta ao final do bloco:

```markdown
- Specs executáveis da especialidade segurança (ex.: asserções de
  threat model e ADRs de segurança em Concordion-Markdown), rodadas
  via Concordion com tradutor Python interno à suíte; spec falhando
  = bloqueante
```

E **Ferramentas** passa a: gitleaks, pip-audit, bandit, Concordion
(tradutor Python).

c) Seção "Elementos de Especificação", regra "##### Critérios de
Aceite + Requisitos" (atual) termina em:

```markdown
- Specs executadas pelo Concordion (fixtures Groovy); o texto é a spec —
  editar o texto muda o veredito do teste (link texto↔teste)
```

→ acrescenta ao final:

```markdown
- Especificação executável É UM TESTE: toda spec executável pertence
  à suíte da sua especialidade e roda dentro dela (ex.: spec de
  segurança roda na suíte `testes-produto/seguranca`)
```

### Emc — `docs/README.md`: "Dois níveis de teste", nível 2 (achado 2)

Atual:

```markdown
2. **Testes dos scripts de teste** — os scripts de suíte e
   o agregador são código e têm testes próprios. Esta
   seção é a especificação executável deles: os testes dos
   scripts cobrem exatamente o que ela define (suítes,
   interface JSON, proibições). Rodam SOMENTE
   quando os scripts mudam — por exemplo, curadoria
   alterando ferramentas ou critérios por orientação do
   humano —, nunca no ciclo normal de desenvolvimento.
```

→ corrigido:

```markdown
2. **Testes dos scripts de teste** — os scripts de suíte e
   o agregador são código e têm testes próprios, em
   `testes-produto/tests/`, fora da suíte `-m all` (separação por
   path, sem marker novo). Esta
   seção é a especificação executável deles: os testes dos
   scripts cobrem exatamente o que ela define (suítes,
   interface JSON, proibições). Rodam SOMENTE
   quando os scripts mudam — por exemplo, curadoria
   alterando ferramentas ou critérios por orientação do
   humano —, nunca no ciclo normal de desenvolvimento.
```

### Emd — `interface-testes-produto.md`: seção Agregador + suíte meta (achados 2 e 3, v2 pós-reversão)

Atual:

```markdown
## Agregador

- Comando sem argumentos (padrão: `testes-produto`)
- Chama as quatro suítes (backend, dados, segurança, frontend)
  e consolida `findings`
- `status` é `fail` se qualquer suíte falhar
- Execução na fase Testes do workflow: agente `qa` (o script
  apenas agrega suítes)
- Evidência da execução validada pelo `curador-produto`
- Não substitui a entrevista de ferramentas por especialidade
```

→ corrigido:

```markdown
## Agregador

- Comando sem argumentos (padrão: `testes-produto`)
- Chama as quatro suítes (backend, dados, segurança, frontend)
  e consolida `findings`
- `status` é `fail` se qualquer suíte falhar
- Execução na fase Testes do workflow: agente `qa` (o script
  apenas agrega suítes)
- Evidência da execução validada pelo `curador-produto`
- Não substitui a entrevista de ferramentas por especialidade
- Especificação executável É UM TESTE: cada suíte roda
  internamente as specs executáveis da sua especialidade via
  Concordion (tradutor Python como infra interna da suíte, como o
  pytest é do backend)
- Os testes dos scripts de suíte e do agregador (suíte meta) vivem
  em `testes-produto/tests/`: fora da suíte `-m all` (separação por
  path, sem marker novo), rodam quando os scripts mudam
```

### Eme — `doc-readme-template.md`: reflexos (achados 2 e 3, v2 pós-reversão)

a) Nas subseções de especialidade (backend, dados, segurança,
frontend), o "O que deve conter" de cada uma ganha o bullet:

```markdown
- Specs executáveis da especialidade (quando o projeto usa spec
  executável), rodadas via Concordion com tradutor Python interno à
  suíte; spec falhando = bloqueante
```

b) "Dois níveis de teste", nível 2 — atual (inclui a ocorrência
residual de "orquestrador"):

```markdown
2. **Testes dos scripts de teste** — os scripts de suíte e
   o orquestrador são código e têm testes próprios. Esta
   seção é a especificação executável deles: os testes dos
   scripts cobrem exatamente o que ela define (suítes,
   interface JSON, proibições). Rodam SOMENTE
   quando os scripts mudam — por exemplo, curadoria
   alterando ferramentas ou critérios por orientação do
   humano —, nunca no ciclo normal de desenvolvimento.
```

→ corrigido:

```markdown
2. **Testes dos scripts de teste** — os scripts de suíte e
   o agregador são código e têm testes próprios, em
   `testes-produto/tests/`, fora da suíte `-m all` (separação por
   path, sem marker novo). Esta
   seção é a especificação executável deles: os testes dos
   scripts cobrem exatamente o que ela define (suítes,
   interface JSON, proibições). Rodam SOMENTE
   quando os scripts mudam — por exemplo, curadoria
   alterando ferramentas ou critérios por orientação do
   humano —, nunca no ciclo normal de desenvolvimento.
```

### Emf — `testes-por-especialidade-template.md`: reflexos (achados 2 e 3, v2 pós-reversão)

Atual:

```markdown
Agregador: `testes-produto`

Executado pelo agente `qa` na fase Testes; a evidência é
validada pelo `curador-produto`.

Spec: [docs/README.md#testes-por-especialidade](docs/README.md#testes-por-especialidade)
```

→ corrigido:

```markdown
Agregador: `testes-produto`

Chama as suítes da tabela e consolida o relatório; cada suíte roda
os checks e as specs executáveis da sua especialidade (via
Concordion, quando o projeto usa spec executável). Executado pelo
agente `qa` na fase Testes; a evidência é validada pelo
`curador-produto`. Testes dos scripts de suíte e do agregador:
`testes-produto/tests/`.

Spec: [docs/README.md#testes-por-especialidade](docs/README.md#testes-por-especialidade)
```

### Emg — `curador-produto.md`: referências do curador com o path da suíte meta (achado 2)

Atual (capacidade 2, "Orientação ao humano"):

```markdown
critérios por orientação do humano), nunca no ciclo
normal de desenvolvimento.
```

→ corrigido:

```markdown
critérios por orientação do humano), nunca no ciclo normal de
desenvolvimento — vivem em `testes-produto/tests/`, fora da
suíte `-m all` (separação por path, sem marker novo).
```

### Emh — `docs/README.md`: Elementos de Especificação — L3 no C4 (mudança nova)

a) Tabela, linha (atual):

```markdown
| Arquitetura (Diagrama Gerado) | Mermaid — C4 L1/L2 gerado dos ADRs | eng-software | docs/adr/diagrama-c4-l1.md, docs/adr/diagrama-c4-l2.md |
```

→ corrigida:

```markdown
| Arquitetura (Diagrama Gerado) | Mermaid — C4 L1/L2/L3 gerado dos ADRs | eng-software | docs/adr/diagrama-c4-l1.md, docs/adr/diagrama-c4-l2.md, docs/adr/diagrama-c4-l3.md |
```

b) Regra (atual):

```markdown
##### Arquitetura (Diagrama Gerado)
- Gerado pelo eng-software a partir dos ADRs + análise do código
  (codebase-memory)
- Segue o modelo C4, apenas níveis 1 e 2:
  - L1 (diagrama-c4-l1.md): sistema e seus atores/sistemas externos
  - L2 (diagrama-c4-l2.md): containers internos (scripts, pacote
    Python, harness-conf, destinos sincronizados)
- Formato: bloco Mermaid (C4Context para L1, C4Container para L2)
- Regenerar sempre que um ADR for adicionado ou superseded
- Não editar manualmente — é artefato gerado
```

→ corrigida:

```markdown
##### Arquitetura (Diagrama Gerado)
- Gerado pelo eng-software a partir dos ADRs + análise do código
  (codebase-memory)
- Segue o modelo C4, níveis 1, 2 e 3:
  - L1 (diagrama-c4-l1.md): sistema e seus atores/sistemas externos
  - L2 (diagrama-c4-l2.md): containers internos (scripts, pacote
    Python, harness-conf, destinos sincronizados)
  - L3 (diagrama-c4-l3.md): componentes internos dos containers
- Gate de julgamento do L3: o diagrama não cobre todo o código; o
  eng-software inclui apenas as partes mais importantes ou
  complexas; componentes iguais e padronizados, repetidos, não
  entram. O critério de seleção é do eng-software na geração
- Formato: bloco Mermaid (C4Context para L1, C4Container para L2,
  C4Component para L3)
- Regenerar sempre que um ADR for adicionado ou superseded
- Não editar manualmente — é artefato gerado
```

## Curadoria — progresso e roteiro

Material base lido (2026-09-14):
- `harness-conf/agents/default-artifacts/doc-readme-template.md`
- `harness-conf/agents/default-artifacts/testes-por-especialidade-template.md`
- `harness-conf/agents/default-artifacts/instrucoes-por-agente-template.md`
- `harness-conf/agents/references/interface-testes-produto.md`
- `harness-conf/agents/references/principios-documentacao.md`
- `harness-conf/agents/references/mensagens-curadoria.md` (ausência já
  detectada pelo devflow; gate respondido = tratar agora)

Roteiro previsto (cada rodada só avança após aprovação explícita):
1. Rodada 1: fundações — pasta docs, enquadramento, linguagem dos scripts.
2. Rodada 2: seção Definição de Escopo do `docs/README.md`.
3. Rodada 3: seção Elementos de Especificação (spec executável quando
   couber; skill spec-executavel na entrevista).
4. Rodada 4: seção Estratégias de Indexação de Código.
5. Rodada 5: seção Testes por Especialidade — especialidades aplicáveis,
   ferramentas (catálogo como referência), tetos de orçamento,
   pass-through para suíte sem ferramentas.
6. Rodada 6: `AGENTS.md` — tabela índice com link âncora
   (`docs/README.md#testes-por-especialidade`) + Instruções por Agente.
7. Fechamento: persistência de tudo aprovado; scripts de suíte são
   implementados depois pelo eng-software (nenhum script antes do fim
   da entrevista); verificação de execução verde ao final.

Intercorrência (2026-09-14): correção de papéis + renomeação
orquestrador→agregador — 6 diffs aprovados e APLICADOS;
RESSALVA: 3 ocorrências do termo (referentes ao script) escaparam
dos diffs e somam-se ao item único de renomeação da construção
(ver ## Decisões). Bloco 4 retomado.

Pendências obrigatórias da fase de CONSTRUÇÃO desta curadoria
(decididas em 2026-09-14; lista consolidada no fechamento e emendada
pós-revisão do plano):
- (a) Implementar `testes-produto/backend` e
  `testes-produto/seguranca` + agregador `testes-produto` (Python,
  interface JSON `{ status, findings[] }`, sem argumentos, exit 0/1)
  conforme a seção "Testes por Especialidade" do `docs/README.md`.
  Schema de findings: `interface-testes-produto.md` como referência
  normativa (melhoria 6). Agregador com papel puro: chama as suítes e
  consolida; specs executáveis rodam DENTRO da suíte da especialidade
  (reversão do achado 3).
- (b) Instalação das ferramentas no bootstrap user-space (dois SOs):
  ruff, shellcheck, PSScriptAnalyzer, pytest-cov, gitleaks, pip-audit,
  bandit; incluir pwsh no WSL/Linux (para PSScriptAnalyzer) e
  shellcheck no Windows (melhoria 9). Atualizar a seção de
  dependências do `README.md` (melhoria 11).
- (c) Retrofit dos 6 ADRs legados (`docs/adr/0001`–`0006`) para
  Concordion-Markdown com asserção executável (P3.f) e geração dos
  diagramas C4 L1/L2 (`docs/adr/diagrama-c4-l1.md`,
  `docs/adr/diagrama-c4-l2.md`) e L3 SELETIVO
  (`docs/adr/diagrama-c4-l3.md` — gate de julgamento: apenas partes
  importantes/complexas; sem componentes padronizados repetidos;
  critério do eng-software na geração) a partir dos ADRs (P3.c +
  mudança nova L3) — artefatos
  com destino definido na tabela de Elementos; a revisão final de
  documentação cobra a existência (item incluído pelo curador: constava
  da spec aprovada e faltava na lista (a)-(h) recebida). Criar
  `docs/specs/rnf-gerais.md` vazio com estrutura mínima (achado 4).
- (d) Setup Concordion/Groovy: `build.gradle` mínimo, fixtures,
  tradutor Python Concordion (XML JUnit → JSON da interface) como
  infra INTERNA das suítes de especialidade (não do agregador; modelo
  novo: especificação executável é um teste e pertence à suíte da
  especialidade; specs classificadas por especialidade), JDK+Gradle
  user-space validados no bootstrap (P3.a; nota de
  glossário já aplicada na decisão P3.a — melhoria 8).
- (e) Renomeação orquestrador→agregador nos demais arquivos
  (devflow.md, qa.md, dba.md, eng-software.md, sec.md,
  docs/workflow-agentes-dev.md) + ocorrências residuais (a ocorrência
  do template nível 2 é resolvida pela emenda Eme(b); curador-produto.md
  capacidade 2 e SKILL.md do catálogo conforme registrado) + emenda da
  regra de runners do `AGENTS.md` (ema; achado 1).
- (f) `src/opencode_config/cli/scaffold_mapa.py` + testes do scaffold
  alinhados à spec nova (termos e papéis).
- (g) Cobertura mínima 70% (pytest-cov): implementar testes até
  atingir o mínimo (P5.2.d) — não é finding passivo. Fontes medidas
  na cobertura: `src/` + `scripts/` + `testes-produto/` (melhoria 5).
- (h) Testes dos scripts de teste (suíte meta): spec executável deles
  é a seção "Testes por Especialidade"; path canônico
  `testes-produto/tests/`, fora da suíte `-m all` (melhoria 10, achado
  2); rodam quando os scripts mudam (incluindo a presente construção).
- Fechamento da construção: suíte `testes-produto` VERDE no fim
  (verificação do curador; executor de rotina na fase Testes é o
  `qa`).

Gravações realizadas até aqui no `docs/README.md`: cabeçalho +
Definição de Escopo (rodada 2); Elementos de Especificação (rodada
3); Estratégias de Indexação (rodada 4); Testes por Especialidade
completa, com subseções backend, segurança e Agregador (rodada 5).
`AGENTS.md` recebeu a tabela índice e as Instruções por Agente na rodada 6;
as emendas pós-revisão foram aplicadas antes da construção.

## Decisões

- 2026-09-14: gate de curadoria = tratar agora (humano, via question).
- 2026-09-14: mapa de modelos parcial = planejamento com glm-5.3; resto
  a decidir com plano completo (humano, via question).
- 2026-09-14, rodada 1 (humano, via question mediada pelo devflow):
  - P1: pasta de documentação = `docs/`; artefato central =
    `docs/README.md`.
  - P2: enquadramento = adaptar ao perfil infra (escopo por história de
    usuário; elementos reconhecem ADR em `docs/adr/`, `UPSTREAM.md`
    das skills, README de dependências; sem DBML, UI ou threat model
    de fluxo autenticado).
  - P3: linguagem dos scripts de suíte `testes-produto/` = Python,
    interface JSON `{ status, findings[] }`, sem argumentos, exit 0/1;
    testes dos scripts espelham em `tests/`.
- Rodada 1 encerrada em 2026-09-14.
- 2026-09-14, rodada 2 (humano, via question mediada pelo devflow):
  - P2.a: terminologia = "história de usuário" (não "demanda de
    mudança"; recomendação do curador não aceita).
  - P2.b: bloco RN-ACL removido (sem perfis nem autenticação no repo).
  - P2.c: `docs/specs/rnf-gerais.md` sempre presente (vazio se não
    houver RNF transversal).
  - Seção "Definição de Escopo" APROVADA para persistência.
- Rodada 2 encerrada em 2026-09-14. Primeira gravação de
  `docs/README.md` realizada (cabeçalho "Mapa do Produto" + intro
  seguem o template default, ajustáveis na revisão final).
- 2026-09-14, rodada 3, P3.a (humano, via question mediada pelo
  devflow): formato da spec executável = Rota B — motor oficial
  Concordion com fixtures Groovy. Condições aprovadas: spec fonte em
  Concordion-Markdown como fonte única (doc externa); wrapper Python no
  orquestrador traduz XML JUnit para `{ status, findings[] }`; JDK +
  Gradle user-space validados no bootstrap dos dois SOs; rede no
  primeiro run com retry (3 tentativas; esgotado = finding bloqueante).
  Nota de glossário (emenda pós-revisão, melhoria 8): onde esta decisão
  diz "orquestrador" referindo-se ao script `testes-produto`, lê-se
  AGREGADOR (renomeação aprovada em 2026-09-14).
  Rotas A (bridge própria) e híbrido pytest-bdd rejeitadas.
- P3.a encerrada em 2026-09-14; P3.b–P3.e abertas.
- 2026-09-14, rodada 3 (humano, via question mediada pelo devflow):
  - P3.b: Plano de Testes Manuais REMOVIDO da tabela (manual sob
    demanda, sem artefato obrigatório).
  - P3.c: Diagrama de Arquitetura C4 MANTIDO (contrário à recomendação
    do curador): Mermaid C4 L1/L2 gerado dos ADRs, eng-software,
    `docs/adr/diagrama-c4-l1.md` e `docs/adr/diagrama-c4-l2.md`.
  - P3.d: asserção executável OBRIGATÓRIA em ADR novo (contrário à
    recomendação do curador); tratamento dos 6 legados em Markdown
    puro ficou como item P3.f a aprovar.
- P3.b/P3.c/P3.d encerradas em 2026-09-14; P3.e aberta (com diff
  respondido) e P3.f aberta.
- 2026-09-14, rodada 3 (humano, via question mediada pelo devflow):
  - P3.e: eng-software responsável por TODOS os elementos da tabela.
  - P3.f: RETROFIT dos 6 ADRs legados para Concordion-Markdown com
    asserção executável (contrário à recomendação do curador);
    trabalho do ciclo de construção desta curadoria.
- Rodada 3: todas as sub-perguntas (P3.a–P3.f) decididas em
  2026-09-14. Falta aprovação final do texto consolidado da seção
  para gravar no `docs/README.md`.
- 2026-09-14: texto final consolidado da seção Elementos de
  Especificação APROVADO pelo humano (via devflow). Rodada 3
  ENCERRADA; seção gravada no `docs/README.md`.
- 2026-09-14, rodada 4 (humano, via question mediada pelo devflow):
  - P4.a: tabela só com a linha codebase-memory CLI — skill
    code-explorer-priority, ADRs e AGENTS.md removidos da seção
    (entendimento do humano: só o codebase-memory é estratégia de
    indexação de código).
  - P4.b: só a tabela, sem texto abaixo (recomendação aprovada).
  - Humano quer rever o texto ajustado antes de gravar.
- 2026-09-14: texto final da seção Estratégias de Indexação de Código
  (tabela de 1 linha, codebase-memory CLI) APROVADO pelo humano (via
  devflow). Rodada 4 ENCERRADA; seção gravada no `docs/README.md`.
- 2026-09-14, rodada 5, bloco 1 (humano, via question mediada pelo
  devflow):
  - P5.a: reduzir às especialidades aplicáveis —
    `testes-produto/backend` + `testes-produto/seguranca`; sem
    pass-through de dados/frontend; novas especialidades entram por
    curadoria (recomendação do curador aceita).
  - P5.b: nomes canônicos backend/seguranca mantidos.
  - P5.c: blocos invariantes (PROIBIDO, Dois níveis de teste, nota do
    AGENTS.md) como no template.
  - Estrutura geral da seção APROVADA (gravação no fechamento da
    rodada 5).
- Bloco 1 da rodada 5 encerrado em 2026-09-14; bloco 2 (suíte backend)
  aberto.
- 2026-09-14, rodada 5, bloco 2 (humano, via question mediada pelo
  devflow):
  - P5.2.a: check principal = pytest `-m all` (executável do `.venv`
    do SO, suíte completa do ambiente corrente), bloqueante.
  - P5.2.b: ruff + shellcheck + PSScriptAnalyzer, todos bloqueantes.
  - P5.2.c: mypy FORA da suíte.
  - P5.2.d: cobertura mínima de 70% (pytest-cov), bloqueante —
    rejeitado baseline congelado; abaixo de 70%, o ciclo de construção
    desta curadoria implementa testes até atingir (não é finding
    passivo).
  - P5.2.e: conceito de orçamento REMOVIDO deste repo — nenhum teto de
    tempo; suítes rodam até o fim. Adaptação explícita na seção;
    interface-testes-produto é referência, o spec efetivo é a seção.
  - Ajuste na aprovação parcial: humano mandou REMOVER o bloco
    "**Orçamento:** ..." da subseção backend e a nota de negação da
    intro — "não tem motivo em ter uma seção de negação". A spec não
    contém parágrafo sobre orçamento; a decisão vive apenas em
    ## Decisões deste plan. Intro da seção: só a frase corrigida
    ("Critérios e ferramentas saem da entrevista de curadoria.").
- Bloco 2 da rodada 5: sub-perguntas decididas em 2026-09-14;
  aguardando aprovação final da subseção backend.
- 2026-09-14: subseção backend APROVADA pelo humano (via devflow)
  como no rascunho final (sem bloco de orçamento). Bloco 2 da rodada 5
  ENCERRADO.
- 2026-09-14, rodada 5, bloco 3 (humano, via question mediada pelo
  devflow):
  - P5.3.a: recorte confirmado — secrets + pip-audit + SAST; sem DAST.
  - P5.3.b: secrets scan = gitleaks.
  - P5.3.c: SAST = bandit; cobertura de CVE (pedido do humano)
    atendida pelo pip-audit.
  - P5.3.d: severidades — segredo sempre bloqueante; pip-audit e
    bandit bloqueantes em high/critical, demais melhoria.
- Bloco 3 da rodada 5: sub-perguntas decididas em 2026-09-14;
  aguardando aprovação final da subseção segurança.
- Bloco 3 da rodada 5: sub-perguntas decididas em 2026-09-14;
  aguardando aprovação final da subseção segurança.
- 2026-09-14: subseção segurança APROVADA pelo humano (via devflow)
  como no rascunho final. Bloco 3 da rodada 5 ENCERRADO; bloco 4
  (orquestrador) aberto.
- 2026-09-14, correção de papéis do orquestrador (humano, via devflow):
  "O orquestrador NÃO EXECUTA TESTES DE PRODUTO." Sentido canônico
  confirmado com fontes (qa.md, devflow.md, workflow-agentes-dev.md):
  script `testes-produto` = agregador das suítes; executor na fase
  Testes = agente `qa` (passo 6.1); devflow nunca executa;
  curador-produto valida a evidência. Aprovado: corrigir os 6 arquivos
  de texto com diffs aprovados UM A UM antes de gravar; diffs
  propostos na seção "Correção de papéis do orquestrador — diffs a
  aprovar". Bloco 4 pausado até concluir a correção.
- 2026-09-14, retificação da correção de papéis (humano, via devflow):
  - Desenho-alvo confirmado pelo próprio humano: script como
    AGREGADOR mecânico executado pelo `qa`; o curador só lê a
    evidência (idem workflow-agentes-dev.md, regras 27/28).
  - RENOMEAÇÃO: "orquestrador" sai da documentação referente ao
    script `testes-produto`, que passa a ser chamado AGREGADOR;
    "orquestrador" fica reservado ao agente devflow.
  - Escalonamento: 6 diffs refeitos com o termo agregador; renomeação
    nos demais arquivos (devflow.md, qa.md, dba.md, eng-software.md,
    sec.md, docs/workflow-agentes-dev.md) + scaffold_mapa.py + testes
    do     scaffold + suíte verde no fim = UM item único da fase de
    construção.
- 2026-09-14: 6 diffs da renomeação APROVADOS pelo humano UM A UM
  (via devflow) e APLICADOS nos arquivos: doc-readme-template.md
  (intro, Dois níveis item 1, subseção agora "### Agregador"),
  testes-por-especialidade-template.md, interface-testes-produto.md
  (seção agora "## Agregador"), mensagens-curadoria.md (2 trechos),
  curador-produto.md (8 pontos) e SKILL.md do catálogo (description +
  corpo). Intercorrência RESOLVIDA. Ressalva: 3 ocorrências do termo
  referente ao SCRIPT escaparam dos diffs apresentados e NÃO foram
  editadas (fora do aprovado): doc-readme-template.md (item 2 de
  "Dois níveis de teste": "scripts de suíte e o orquestrador são
  código"), curador-produto.md (capacidade 2, "Orientação ao humano":
  "scripts de suíte e do orquestrador — os scripts são código") e
  SKILL.md do catálogo ("Cada suíte e o orquestrador `testes-produto`
  são scripts" + trigger "orquestrador" na description). Somadas ao
  item único de renomeação da construção.
- 2026-09-14, rodada 5, bloco 4 consolidado (humano, via devflow):
  P5.4.a confirmada; P5.4.b fail-closed (padrão da interface);
  P5.4.c sem cache/fingerprint (registro só no plan); P5.4.d mesmo
  gate da interface. REGRA DE MEDIAÇÃO nova: perguntas uma por vez;
  não perguntar o já decidido/definido nos artefatos base. Bloco 4 e
  rodada 5 ENCERRADOS; seção completa "Testes por Especialidade"
  gravada no `docs/README.md` (frase de fingerprint/cache omitida por
  coerência com P5.4.c).
- 2026-09-14, rodada 6 (humano, via devflow): P6.a = SEM INSTRUÇÕES
  A PEDIDO DO HUMANO para os 7 agentes; tabela índice aprovada.
  Rodada 6 ENCERRADA e ENTREVISTA DE CURADORIA CONCLUÍDA: seções
  gravadas no `AGENTS.md` (Testes por Especialidade + Instruções por
  Agente). Ver ## Relatórios para o fechamento verificado.
- 2026-09-14, emendas pós-revisão do plano (humano, via devflow;
  achados do `rev`):
  - Achado 1: regra de runners do `AGENTS.md` — Ema v1 (reformulação
    "veto só para runner trivial") RECUSADA pelo humano: a regra
    original continua valendo; direção aprovada é exceção explícita
    para `testes-produto/` (scripts não são testes; são código
    produtivo das validações usadas pelos agentes, suscetíveis a
    testes; suíte meta em `testes-produto/tests/`). Redação corrente:
    Ema v2.
  - Achado 2: suíte meta (testes dos scripts de teste) fica em
    `testes-produto/tests/`, FORA da suíte `-m all` (separação por
    path, sem marker novo, sem mexer na ADR-0005); frase "rodam SOMENTE
    quando os scripts mudam" permanece literal. Referências do curador
    ganham indicativo do path.
  - Achado 3: o AGREGADOR chama o tradutor Concordion DIRETO
    (contrário à recomendação de suíte separada): emenda da subseção
    Agregador no `docs/README.md` e nos templates; "não inventa check"
    permanece (o check Concordion é definido na seção).
  - Achado 4: criação de `docs/specs/rnf-gerais.md` (vazio, estrutura
    mínima) entra no item (c) da construção.
  - Melhorias 5-11 incorporadas aos itens de construção (ver lista
    consolidada). Diffs de emenda na seção "## Emendas pós-revisão do
    plano — diffs a aprovar"; nenhum arquivo editado ainda.
  - Nota de contexto do humano sobre o achado 3 (2026-09-14):
    decisão "Concordion direto no agregador" MANTIDA naquele momento;
    justificativa registrada: verificação de documento de regra é
    questão de agregação, não especialidade. [SUBSTITUÍDA no mesmo dia
    pela reversão abaixo.]
- 2026-09-14, mudanças novas na seção Elementos de Especificação
  (humano, via devflow):
  - Nível 3 no modelo C4: o diagrama de arquitetura ganha L3
    (componentes), novo destino `docs/adr/diagrama-c4-l3.md`; o humano
    quer testar com esse nível.
  - Gate de julgamento no L3: o diagrama NÃO cobre todo o código;
    o eng-software (quem gera) julga e inclui apenas as partes mais
    importantes ou complexas; componentes iguais e padronizados,
    repetidos, não entram. Critério explícito na regra: seletividade
    por importância/complexidade, a cargo do eng-software na geração.
  - Emenda correspondente: diff Emh (aplicável ao `docs/README.md`
    deste repo; o template default segue com L1/L2 genéricos, não
    afetado).
- 2026-09-14, REVERSÃO do achado 3 com modelo novo (humano, via
  devflow; justificativa literal): "Se eu tenho um documento que
  descreve a segurança da aplicação, e tenho um concordion para
  implementá-lo, esse teste escrito em Concordion (uma especificação
  executável É UM TESTE) faz parte da suite de segurança. O mesmo
  vale para as outras especialidades."
  - Modelo novo (substitui "Concordion direto no agregador"):
    especificação executável É UM TESTE e todo teste pertence à suíte
    da sua especialidade; specs executáveis são classificadas por
    especialidade; cada suíte roda internamente as specs da sua
    especialidade via Concordion + tradutor Python (tradutor é infra
    interna das suítes, como o pytest é do backend); o agregador
    volta ao papel puro — chama as suítes e consolida, NÃO chama
    Concordion direto; a subseção Agregador gravada permanece como
    está.     Emendas reescritas: Emb CANCELADA; Emi nova; Emd/Eme/Emf
    ajustadas; Emc/Emg válidas; Emh aprovada.
- 2026-09-14: TODAS as emendas pendentes APROVADAS pelo humano (via
  devflow): Ema v2, Emc, Emd v2, Eme v2, Emf v2, Emg, Emi (Emh e Ema
  v2 já aprovadas; Emb cancelada). Emendas APLICADAS no mesmo dia em:
  `AGENTS.md` (Ema v2), `docs/README.md` (Emc, Emh, Emi),
  `interface-testes-produto.md` (Emd v2), `doc-readme-template.md`
  (Eme v2), `testes-por-especialidade-template.md` (Emf v2) e
  `curador-produto.md` (Emg). Verificação
  grep: termos coerentes, sem "verificador de specs", path da suíte
  meta presente. Pacote de emendas marcado APLICADO.

## Relatórios

- 2026-09-14 (curador-produto): detectada perda de conteúdo no plan — a
  avaliação das rotas A/B (P3.a) e a atualização de Status feitas pelo
  curador não estavam no arquivo ao retomar a sessão (sobrescrita
  externa provável, fontes: mediação de question). Avaliação A/B
  reaplicada integralmente nesta sessão, agora combinada com a resposta
  à pergunta de mérito sobre linguagem da spec. `docs/README.md`
  conferido intacto. Recomendação ao devflow: regravar o plan apenas
  por edição incremental (append/merge), nunca por sobrescrita integral
  de snapshot.

- 2026-09-14 (curador-produto): FECHAMENTO DA ENTREVISTA DE CURADORIA.
  Verificação objetiva:
  - `docs/README.md`: as 4 seções obrigatórias presentes e completas —
    Definição de Escopo (história de usuário, sem RN-ACL);
    Elementos de Especificação (tabela com 8 elementos, C4 reintegrado,
    ADR Concordion-Markdown com asserção obrigatória + retrofit,
    UPSTREAM.md e README-Dependências referenciais, agente
    eng-software em todas as linhas, Regras de Documentação
    coerentes); Estratégias de Indexação (tabela de 1 linha,
    codebase-memory CLI); Testes por Especialidade (intro com
    AGREGADOR, blocos invariantes, subseções backend, segurança e
    Agregador; sem mypy, sem orçamento, sem cache/fingerprint).
  - Termos coerentes: `orquestrador` NÃO ocorre no `docs/README.md`;
    `Agregador` ocorre no `AGENTS.md` apenas na seção nova (linha 186);
    papéis explícitos (qa executa; curador-produto valida evidência;
    devflow fora da execução) consistentes nos dois arquivos.
  - `AGENTS.md`: `## Testes por Especialidade` (tabela índice +
    Agregador + link âncora) e `## Instruções por Agente` (7
    subseções SEM INSTRUÇÕES A PEDIDO DO HUMANO) gravadas.
  - Achado de coerência (bloqueante para a construção, não para a
    entrevista): `AGENTS.md`, regra "Não crie testes para scripts cuja
    única função é executar ou orquestrar testes" (seção Regras
    Obrigatórias Para Testes) conflita com a spec nova (scripts de
    suíte e agregador são código de produção com testes próprios —
    "Dois níveis de teste" + regra do mesmo gate) e ainda usa
    "orquestrar". Resolver junto do item (e)/(h) da construção:
    ajustar a regra para excluir do veto os scripts de testes-produto
    (que têm lógica de verificação) ou reformulá-la para o runner
    trivial.
  - Entrevista concluída com todas as aprovações registradas em
    ## Decisões; nenhum item pendente de decisão humana.

### Revisão do Plano — 2026-09-14

Autor: rev (instância limpa, chamada pelo devflow para a fase REVISÃO DO
PLANO). Objeto: `plan/curadoria-repo.md` (decisões, renomeação aplicada,
itens a–h, mapa de modelos), `docs/README.md` (4 seções gravadas) e
`AGENTS.md` (tabela índice + Instruções por Agente). Verificação de fatos
embutida: grep de "orquestrador" no repo, existência de `docs/adr/0001`–
`0006`, `src/opencode_config/cli/scaffold_mapa.py`,
`tests/scaffold/test_mapa_produto.py`, `docs/specs/` (inexistente),
`docs/backlog/` (inexistente), `## Agregador` na interface-testes-produto.

#### Revisão Integrativa (rev)

##### Achados

| # | Achado | Ação recomendada | Severidade |
|---|--------|------------------|------------|
| 1 | Contradição (CONHECIDA, confirmada): regra do `AGENTS.md` "Não crie testes para scripts cuja única função é executar ou orquestrar testes" (seção Regras Obrigatórias Para Testes) conflita com a spec nova ("Dois níveis de teste" + Agregador: scripts de suíte são código de produção com testes próprios) e ainda usa "orquestrar" | Devflow media aprovação humana da nova redação (excluir scripts testes-produto do veto ou limitá-la ao runner trivial); eng-software aplica no item (e) | bloqueante |
| 2 | Contradição (NOVA): "testes dos scripts de teste rodam SOMENTE quando os scripts mudam... nunca no ciclo normal" (`docs/README.md`) vs `AGENTS.md` "o agente roda sempre a suíte completa do ambiente corrente, sem deixar teste de fora" + suíte backend = `-m all` (atalho para unit or integration). Testes em `tests/` com markers da taxonomia atual rodam em toda execução; excluí-los exige mecanismo de seleção não previsto (marker novo fora de `-m all` contraria a regra e a ADR-0005) | Decidir na revisão do plano: marker próprio + emenda da regra do `AGENTS.md` (somar ao item (e)), ou redefinir "somente quando mudam" como escopo de alteração, não de seleção de execução; gravar a decisão no item (h) | bloqueante |
| 3 | Lacuna (NOVA): integração do Concordion com o fluxo de testes indefinida. A decisão P3.a exige "wrapper Python no orquestrador [agregador] traduz XML JUnit para `{ status, findings[] }`" e o item (d) o implementa, mas a seção gravada define chamada nominal apenas backend + seguranca (P5.4.a), nenhuma subseção menciona Concordion e o agregador "não inventa check". Onde o wrapper roda (dentro do backend? suíte nova via curadoria? chamada direta do agregador?) não é especificável sem violar a spec gravada | Devflow media decisão humana; emenda da seção "Testes por Especialidade" pelo curador-produto (ou nova especialidade por curadoria); atualizar item (d) com o ponto de integração | bloqueante |
| 4 | Lacuna (NOVA): regra gravada "Arquivo sempre presente em `docs/specs/rnf-gerais.md`; fica vazio se não houver RNFs transversais" + destino na tabela de Elementos, mas nenhum item (a)–(h) cria `docs/specs/rnf-gerais.md` (pasta `docs/specs/` não existe). O item (c) cobre apenas retrofit dos ADRs + diagramas C4; a spec nasceria violada | Incluir criação de `docs/specs/rnf-gerais.md` (vazio) no item (c) da construção; decisão do curador, registro no plan | bloqueante |
| 5 | Lacuna: "cobertura total abaixo de 70%" não define as fontes medidas (`src/`? `src/` + `scripts/`? + `testes-produto/`?). A subseção Agregador inclui scripts de suíte no "mesmo nível de qualidade (ruff, pytest, cobertura)", mas a regra do backend não delimita a medição | Definir fontes da medição no item (g) antes da construção | melhoria |
| 6 | Lacuna: schema de `findings[]` (campos: severity, message, arquivo?) não consta da seção gravada, que é o "spec efetivo"; a interface-testes-produto.md é apenas referência (P5.2.e/P5.4.d). Implementador do item (a) não tem os campos no spec normativo | Registrar no item (a) que o schema de findings segue a interface-testes-produto.md como referência normativa para os campos | melhoria |
| 7 | Contradição interna do plan (stale): trecho "Gravações realizadas até aqui... `AGENTS.md` intocado (rodada 6 cuidará dele)" contraria o estado final registrado em ## Decisões e ## Relatórios (rodada 6 encerrada, `AGENTS.md` gravado). Risco de confusão na construção | Edição simples (devflow ou eng-software): atualizar o trecho de progresso para refletir o fechamento | melhoria |
| 8 | Inconsistência terminológica: decisão ATIVA da P3.a (linha do ## Decisões) usa "wrapper Python no orquestrador" no sentido do script `testes-produto`; pós-renomeação, "orquestrador" é o devflow. Registro histórico é aceitável, mas a decisão é referência do item (d) | Nota de glossário no item (d): na decisão P3.a, "orquestrador" lê-se "agregador" | melhoria |
| 9 | Lacuna: dependências implícitas de SO no item (b): PSScriptAnalyzer exige pwsh (PowerShell Core) no WSL/Linux; shellcheck exige instalação user-space no Windows; pip-audit/gitleaks exigem rede. Sem pwsh nomeado no bootstrap, a suíte backend teria finding bloqueante crônico no WSL | Incluir pwsh e shellcheck/Windows na lista do item (b) e na seção de dependências do README | melhoria |
| 10 | Lacuna: placement dos testes dos scripts de teste indefinido — rodada 1 diz "espelham em `tests/`"; `AGENTS.md` diz "testes de scripts ficam em `tests/scripts/`"; `testes-produto/` na raiz sugeriria `tests/testes-produto/`. Três leituras possíveis | Definir path canônico no item (h) antes da construção | melhoria |
| 11 | Lacuna: item (b) não registra a atualização da seção de dependências do `README.md`, exigida pela regra canônica do `AGENTS.md` quando o bootstrap muda; risco de esquecimento na construção | Incluir a atualização do README de dependências como entregável do item (b) | melhoria |

##### Veredicto

[ ] Aprovado sem ressalvas
[ ] Aprovado com melhorias opcionais
[x] Bloqueado — resolver achados bloqueantes (1–4) antes de prosseguir
    para a CONSTRUÇÃO. Nota: o achado 1 já é conhecido e coberto pelo
    item (e); os achados 2, 3 e 4 exigem decisão de plano (mediada pelo
    devflow com o humano) e ajuste na lista (a)–(h) e/ou emenda da
    seção gravada pelo curador-produto.

Pontos verificados sem achado: coerência de termos agregador/testes-produto
entre `docs/README.md` e `AGENTS.md`; papéis (qa executa, curador-produto
valida, devflow fora da execução) consistentes nos dois arquivos; texto
gravado adere às decisões (intro sem orçamento, sem frase de cache, subseções
backend/segurança/Agregador fiéis aos rascunhos aprovados); diffs 1–6 da
renomeação aplicados (interface com "## Agregador" confirmado); lista do
item (e) cobre todas as ocorrências residuais de "orquestrador" (script)
confirmadas por grep em devflow.md, qa.md, dba.md, eng-software.md, sec.md,
workflow-agentes-dev.md, doc-readme-template.md, curador-produto.md e
SKILL.md do catálogo; `docs/adr/0001`–`0006` existem (item c procedente);
scaffold e seus testes existem e usam termo antigo (item f procedente);
mapa de modelos com pendências conscientes (luna condicional; testes/revisão
a decidir) — processo, não achado.

##### Evidências (rev)

- [x] Artefatos lidos: `plan/curadoria-repo.md` (1300 linhas),
      `docs/README.md` (244 linhas), `AGENTS.md` (262 linhas)
- [x] Plano aprovado consultado: sim (decisões e specs gravadas no plan)
- [x] Checklist integrativo: 8 dimensões verificadas (coerência entre
      artefatos, aderência às decisões, contradições conhecidas e novas,
      completude a–h, riscos de construção, qualidade de spec,
      verificação de fatos no repo, termos/papéis)
- [x] Achados encontrados: 11 total, 4 bloqueantes (1 conhecido + 3 novos)

### Verificação de resolução — 2026-09-14

Autor: rev (instância limpa, chamada pelo devflow para verificar a
resolução dos bloqueantes 1–4 do relatório "Revisão do Plano —
2026-09-14"). Objeto: emendas marcadas APLICADAS em `AGENTS.md`,
`docs/README.md`, `harness-conf/agents/references/interface-testes-produto.md`,
`harness-conf/agents/default-artifacts/doc-readme-template.md`,
`harness-conf/agents/default-artifacts/testes-por-especialidade-template.md`
e `harness-conf/agents/curador-produto.md`; itens (a)–(h); `pyproject.toml`
(viabilidade da separação por path).

#### Verificação por bloqueante

| # | Bloqueante original | Verificação da resolução | Estado |
|---|---------------------|--------------------------|--------|
| 1 | Regra de runners do `AGENTS.md` conflitava com a spec nova | Ema v2 aplicada verbatim (regra intacta + exceção `testes-produto/` com path da suíte meta); coexiste coerente com "Testes de scripts ficam em `tests/scripts/`" (regra geral para `scripts/`, exceção para `testes-produto/`) | RESOLVIDO |
| 2 | "Rodam SOMENTE quando os scripts mudam" sem mecanismo de separação do `-m all` | `testes-produto/tests/` fora do `-m all` registrado nos 6 arquivos (docs/README.md Emc, interface Emd v2, template Eme v2b, tabela índice Emf v2, curador Emg, AGENTS.md Ema v2); viável na prática: `testpaths = ["tests"]` no pyproject já exclui o path da coleta (sem marker novo, ADR-0005 intacta); item (h) carrega o path canônico | RESOLVIDO |
| 3 | Ponto de integração do Concordion não especificável sem violar a spec gravada | Modelo novo aplicado com consistência: bullets de specs + "Concordion (tradutor Python)" em Ferramentas nas subseções backend/segurança (Emi a/b); regra "Especificação executável É UM TESTE" em Elementos (Emi c); agregador puro no `docs/README.md` (Emb cancelada de fato — "verificador de specs" ausente); interface e templates alinhados (Emd v2/Eme v2/Emf v2); itens (a) e (d) registram o desenho (specs DENTRO da suíte; tradutor como infra interna) | RESOLVIDO |
| 4 | `docs/specs/rnf-gerais.md` sem item de criação na lista (a)–(h) | Item (c) da construção inclui a criação (vazio, estrutura mínima); arquivo ainda não existe porque a CONSTRUÇÃO não iniciou — correto, o achado era de lacuna no plano | RESOLVIDO |

Emh e Ema v2 conferidas nos artefatos: tabela e regra do `docs/README.md`
com C4 L1/L2/L3 + gate de julgamento + C4Component; template default
permanece L1/L2 genérico, conforme decidido. `docs/README.md` sem
ocorrência de "orquestrador"; papéis (qa executa, curador valida,
devflow fora) consistentes; tabela índice do `AGENTS.md` alinhada às
subseções backend/segurança/Agregador.

#### Achados

| # | Achado | Ação recomendada | Severidade |
|---|--------|------------------|------------|
| 1 | Melhoria 7 da ronda anterior permanece aberta: trecho "Gravações realizadas até aqui... `AGENTS.md` intocado (rodada 6 cuidará dele)" segue stale no plan (contraria o estado final registrado em ## Decisões e ## Relatórios); não era objeto das emendas | Edição simples (devflow ou eng-software) na abertura da CONSTRUÇÃO | melhoria |
| 2 | Termo `-m all` (atalho pytest/ADR-0005 deste repo) nos artefatos genéricos de curadoria (doc-readme-template nível 2, interface-testes-produto, curador-produto.md): projeto-alvo sem pytest não terá esse atalho; aplicação fiel ao diff aprovado, portanto decisão ratificada | Generalizar a redação em curadoria futura (ex.: "fora da suíte padrão de testes") | melhoria |

#### Veredicto

[ ] Aprovado sem ressalvas
[x] Aprovado com melhorias opcionais — bloqueantes 1–4 encerrados; plano
    liberado para a CONSTRUÇÃO (mapa de modelos pendente, já registrado
    no Status)
[ ] Bloqueado — resolver achados bloqueantes antes de prosseguir

#### Evidências (rev)

- [x] Artefatos lidos: `plan/curadoria-repo.md` (1775 linhas),
      `docs/README.md`, `AGENTS.md`, `interface-testes-produto.md`,
      `doc-readme-template.md`, `testes-por-especialidade-template.md`,
      `curador-produto.md`, `pyproject.toml`
- [x] Plano aprovado consultado: sim (## Decisões + emendas APLICADAS)
- [x] Checklist integrativo: 6 dimensões (aderência às resoluções
      decididas, consistência entre os 6 arquivos editados, termos e
      papéis, viabilidade técnica da separação por path, achados novos
      pós-emenda, estado das melhorias prévias)
- [x] Achados encontrados: 2 total (2 melhorias, 0 bloqueantes);
      bloqueantes 1–4 = RESOLVIDOS

## Construção: fatia curatorial documental (2026-09-17)

### Status da fatia

CONCLUÍDA, sem bloqueio. Foram executados somente os itens documentais (c) e
(e) solicitados para esta instância. A fase geral continua em CONSTRUÇÃO para
os itens restantes.

### Item (c) — specs e ADRs

- Criado `docs/specs/rnf-gerais.md` com a estrutura mínima e sem RNF
  transversal definido.
- Os ADRs `0001` a `0006` foram preservados na numeração e nas decisões.
- Cada ADR agora contém diretivas Concordion-Markdown `execute` e
  `assertEquals`, com veredito esperado `pass`.
- O ADR-0003 recebeu as seções de alternativas consideradas e de asserção
  executável, que não existiam.
- Criados os três diagramas C4 em Mermaid:
  `docs/adr/diagrama-c4-l1.md`, `docs/adr/diagrama-c4-l2.md` e
  `docs/adr/diagrama-c4-l3.md`.
- O L3 registra o critério seletivo: inclui decisões arquiteturais e
  complexidade de ambiente; exclui wrappers finos, helpers repetidos,
  dataclasses e testes.
- Os diagramas foram baseados nas ADRs 0001–0006 e nos módulos existentes de
  bootstrap, factory, adapters, sincronização e ambiente Windows.

### Item (e) — renomeação documental

- Renomeadas as referências ao script `testes-produto` de `orquestrador` para
  `agregador` em `devflow.md`, `qa.md`, `dba.md`, `eng-software.md`, `sec.md`
  e `docs/workflow-agentes-dev.md`.
- Corrigidos os dois locais residuais ainda presentes em
  `curador-produto.md` e `testes-produto-catalog/SKILL.md`.
- O terceiro local residual registrado no plano, em
  `default-artifacts/doc-readme-template.md`, já estava corrigido para
  `agregador`; nenhuma alteração adicional foi necessária.
- Mantidas as ocorrências que nomeiam o agente `devflow` ou a orquestração do
  workflow.

### Arquivos alterados nesta fatia

- `docs/specs/rnf-gerais.md`
- `docs/adr/0001-migracao-mcp-para-cli.md`
- `docs/adr/0002-testes-integracao-modelo-onpremises.md`
- `docs/adr/0003-qwen3-padrao-integracao-opencode.md`
- `docs/adr/0004-adapters-harness-multiplataforma.md`
- `docs/adr/0005-taxonomia-testes.md`
- `docs/adr/0006-camada-mcp-opcional-com-fallback-cli.md`
- `docs/adr/diagrama-c4-l1.md`
- `docs/adr/diagrama-c4-l2.md`
- `docs/adr/diagrama-c4-l3.md`
- `harness-conf/agents/devflow.md`
- `harness-conf/agents/qa.md`
- `harness-conf/agents/dba.md`
- `harness-conf/agents/eng-software.md`
- `harness-conf/agents/sec.md`
- `docs/workflow-agentes-dev.md`
- `harness-conf/agents/curador-produto.md`
- `harness-conf/skills/testes-produto-catalog/SKILL.md`
- `plan/curadoria-repo.md`

### Verificações objetivas

- Confirmada a existência dos seis ADRs legados, dos três diagramas C4 e do
  arquivo `docs/specs/rnf-gerais.md`.
- Confirmada a presença de `#execute=` e `#assertEquals=` em cada ADR legado.
- Confirmada a ausência do termo antigo referente ao script nos arquivos
  aprovados do item (e).
- Confirmadas as ocorrências preservadas quando o termo nomeia o agente
  `devflow` ou a orquestração do workflow.
- Nenhum script, teste automatizado, suíte de especialidade, agregador ou
  suíte meta foi criado, alterado ou executado nesta fatia.
- A documentação de dependências e o bootstrap ficaram sem alteração; essa
  entrega pertence ao item (b), sob responsabilidade do `eng-software`.

### Bloqueios

Nenhum bloqueio real identificado. Nenhuma decisão humana nova foi aberta.

## Construção: implementação de código e infra (2026-09-17)

### Estado da implementação

Itens (a), (b), (d), (f), (g) e (h) foram implementados. Os itens
documentais (c) e (e) permanecem concluídos na fatia curatorial anterior.
O trabalho não executou `testes-produto/backend`, `testes-produto/seguranca`,
`testes-produto` nem `testes-produto/tests/`, conforme a restrição desta fase.

Commits de construção já criados:

- `757a0a6` — `feat(testes-produto): implement suites e agregador`
- `6fcc952` — `feat(bootstrap): adicionar toolchain das suites de produto`
- `f6aee5c` — `feat(scaffold): alinhar mapa ao contrato de testes-produto`
- `109d000` — `fix(skills): remover atribuicao morta no update`
- `83c4dcc` — `docs(curadoria): registrar mapa e contratos do repo`
- `9945a59` — `fix(bootstrap): instalar shellcheck no Windows`

### Item (a) — suites e contrato

- Criado o pacote `src/opencode_config/product_tests/` com contrato JSON,
  execução observável de processos, retry de rede, tradutor JUnit,
  suite backend, suite de segurança, agregador e entrypoint comum.
- Criados `testes-produto/backend`, `testes-produto/seguranca` e
  `testes-produto/__main__.py`. O agregador também foi registrado como
  console script `testes-produto` no `pyproject.toml`.
- O diretório `testes-produto/` precisa coexistir com
  `testes-produto/tests/`. Por isso, o agregador local usa `python
  testes-produto`; a instalação editable fornece o comando `testes-produto`.
  Essa decisão preserva o path canônico da suíte meta sem criar um arquivo e
  um diretório com o mesmo nome.
- O schema implementado contém somente `status` e `findings[]`, com os campos
  `severity`, `tool` e `message` definidos na referência normativa.
- Crash, exit inesperado, ferramenta ausente e JSON inválido produzem finding
  `bloqueante`. O agregador chama somente as duas suites e não chama
  Concordion.

### Item (b) — bootstrap e dependências

- `PRODUCT_DEPENDENCY_REGISTRY` e `ALL_DEPENDENCY_REGISTRY` incluem ruff,
  shellcheck, pwsh, PSScriptAnalyzer, pytest-cov, gitleaks, pip-audit,
  bandit, JDK e Gradle.
- Instaladores user-space foram adicionados para pipx tools, archives
  portáteis, PSScriptAnalyzer e pytest-cov. WSL/Linux recebe pwsh e Windows
  recebe shellcheck.
- `README.md` e `scripts/bootstrap_repo/README.md` documentam as novas
  dependências e comandos sem elevação.
- `src/opencode_config/cli/skills_sync.py` removeu uma atribuição morta que
  impedia o gate ruff.

### Item (d) — Concordion/Groovy

- Criados `build.gradle`, `settings.gradle`, fixtures Groovy de backend e
  segurança e specs fonte `docs/specs/Backend.md` e
  `docs/specs/Seguranca.md`.
- `concordion.py` traduz XML JUnit para o contrato JSON. A execução usa
  Gradle, JDK e retry de rede no primeiro download.
- `docs/specs/rnf-gerais.md` continua presente como artefato vazio definido
  na fatia documental.

### Item (f) — scaffold

- `scaffold_mapa.py` passou a mencionar agregador, papéis `qa`/
  `curador-produto`, duas suites, specs Concordion e a suíte meta.
- Foram adicionados testes específicos em
  `tests/cli/test_scaffold_mapa_curadoria.py`; os testes existentes do
  scaffold permaneceram intactos.

### Item (g) — cobertura

- Fontes medidas: `src/`, `scripts/` e `testes-produto/`.
- `pyproject.toml` exclui apenas `testes-produto/tests/` da medição, porque
  essa pasta contém testes meta fora do `testpaths` normal.
- Cobertura própria atingiu 74,68% com `pytest -m unit`; o gate de 70% passou.

### Item (h) — suíte meta

- Criado `testes-produto/tests/test_interface_meta.py`, fora de `tests/` e
  fora da coleta de `testpaths = ["tests"]`.
- A suíte meta cobre as duas suites, o agregador, argumentos, JSON e exit
  code. Ela não foi executada nesta fase.

### Arquivos principais criados ou alterados pelo eng-software

- `src/opencode_config/product_tests/`
- `testes-produto/`
- `tests/product_tests/`
- `tests/bootstrap/test_product_dependencies.py`
- `tests/cli/test_scaffold_mapa_curadoria.py`
- `src/opencode_config/bootstrap/{registry.py,detect.py,installers/}`
- `src/opencode_config/cli/scaffold_mapa.py`
- `src/opencode_config/cli/skills_sync.py`
- `pyproject.toml`, `build.gradle`, `settings.gradle`
- `README.md`, `scripts/bootstrap_repo/README.md`

### Evidências de Testes — Construção

- [x] Testes novos: 40 testes próprios executáveis e 5 testes meta criados;
      o ciclo inicial apresentou falha de importação antes da implementação.
- [x] Testes TDD direcionados: `694 passed, 103 deselected` em
      `pytest -m unit`.
- [x] Smoke da suíte normal: `761 passed, 31 deselected` em
      `pytest -m all --ignore=tests/test_taxonomy.py`; os 6 testes de
      `tests/test_taxonomy.py` passaram em execução separada.
- [x] Cobertura: `75%` no relatório final, `74,68%` calculado pelo gate,
      acima do mínimo de 70%.
- [x] Análise estática: `ruff check src scripts testes-produto` verde.
- [x] Shell lint: `shellcheck scripts/bootstrap_repo/configurar-repo.sh` verde.
- [x] Compilação Python: `python -m py_compile` dos três entrypoints verde.
- [x] Regressão incremental: testes direcionados executados após cada ajuste;
      testes de bootstrap, scaffold e skills verdes.
- [x] Smoke final direcionado: `112 passed` cobrindo product_tests, bootstrap,
      scaffold e consistência do workflow.
- [x] Suítes de especialidade, agregador e suíte meta: não executados por
      regra operacional da Construção.
- [x] Gate de refatoração: sem impacto no plano; a separação do agregador em
      `__main__.py` foi registrada como decisão de empacotamento necessária
      para manter o path canônico `testes-produto/tests/`.

### Limitações da execução local

- `pwsh`, PSScriptAnalyzer, gitleaks, pip-audit, bandit e Java não estavam no
  PATH desta máquina. O bootstrap registra instalação user-space para todos;
  nenhum check foi removido ou convertido em pass-through.
- Gradle estava disponível, mas sem JDK. A execução Concordion foi deixada
  para a fase Testes, como exige o contrato do workflow.
- Nenhum bloqueio de implementação foi identificado.
