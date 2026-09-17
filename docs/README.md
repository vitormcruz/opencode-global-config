# Mapa do Produto

Este documento é a fonte de verdade do produto. Define o escopo do que será
construído, os artefatos que devem ser produzidos em cada ciclo de
desenvolvimento e as regras que governam como esses artefatos são criados e
mantidos. É lido por agentes e humanos antes de qualquer ciclo de
implementação.

## Definição de Escopo

O analista deve elicitar, para cada história de usuário:
- Regras de Negócio (comportamentos e restrições que o pacote de
  configuração deve impor)
- Requisitos funcionais e não funcionais
- Critérios de aceitação por exemplos
- Organizar tudo por histórias de usuário
- Critérios de aceitação devem referenciar:
    - Requisitos funcionais, que, por sua vez, referenciam regras de
      negócio, ou;
    - Requisitos não funcionais.
- Nenhum requisito pode ficar sem critério, e vice-versa
- Toda Regra de Negócio deve ter pelo menos um Requisito Funcional
  associado
- Nem todo Requisito Funcional precisa necessariamente ter uma Regra de
  Negócio associada
- Requisitos Não Funcionais associados a uma história ficam no arquivo
  da história e são validados por critérios de aceite daquela história
- Requisitos Não Funcionais gerais (transversais, sem história
  específica) são:
    - Consolidados em `docs/specs/rnf-gerais.md`
    - Derivados em Critérios de Aceitação no mesmo arquivo, com uma
      seção para cada RNF
- O humano pode iniciar o workflow imediatamente após elicitar uma
  história — nesse caso a história fica apenas no arquivo de planejamento
  do devflow e pode ser descartada após o ciclo.
- O humano pode também elicitar múltiplas histórias antecipadamente para
  iniciar os workflows posteriormente, uma por vez — nesse caso o
  analista salva cada história em `docs/backlog/` (um arquivo Markdown
  por história).

---

## Elementos de Especificação

| Elemento | Formato/Ferramenta | Agente Responsável | Destino |
|----------|-------------------|-------------------|---------|
| Regras de Negócio | Lista Numerada | eng-software | docs/specs/regras-negocio.md |
| Critérios de Aceite + Requisitos | Concordion-Markdown — spec executável (Concordion/Groovy) | eng-software | docs/specs/ |
| RNFs Gerais | Concordion-Markdown — spec executável (Concordion/Groovy) | eng-software | docs/specs/rnf-gerais.md |
| Regras de Produto | Tabela | eng-software | nenhum |
| ADR (Arquitetura) | Concordion-Markdown (asserção executável obrigatória) | eng-software | docs/adr/ |
| Arquitetura (Diagrama Gerado) | Mermaid — C4 L1/L2/L3 gerado dos ADRs | eng-software | docs/adr/diagrama-c4-l1.md, docs/adr/diagrama-c4-l2.md, docs/adr/diagrama-c4-l3.md |
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
- Especificação executável É UM TESTE: toda spec executável pertence
  à suíte da sua especialidade e roda dentro dela (ex.: spec de
  segurança roda na suíte `testes-produto/seguranca`)

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

##### UPSTREAM.md (skills externas)
- Regra canônica na seção "Upstream de Skills Externas" do `AGENTS.md`;
  este documento referencia, não duplica
- Presente em toda skill baseada em repositório externo

##### README — Dependências
- Regra canônica na seção "README" do `AGENTS.md`; este documento
  referencia, não duplica
- Atualizada sempre que bootstrap, scripts, skills ou requisitos de
  instalação mudarem

---

## Estratégias de Indexação de Código

| Ferramenta | Uso | Instalação |
|-----------|-----|-----------|
| codebase-memory CLI | Grafo de código e docs; navegação estrutural e consulta de seções. | `codebase-memory-mcp cli` |

---

## Testes por Especialidade

Scripts por especialidade e o agregador `testes-produto`.
Interface JSON: `{ status, findings[] }`. Exit 0 = pass,
exit 1 = fail. Sem argumentos.

O agregador `testes-produto` chama as suítes definidas nesta seção e
consolida o relatório. Falha se qualquer suíte falhar.

Critérios e ferramentas saem da entrevista de curadoria.

**PROIBIDO:** bypassar, comentar, remover ou condicionar
qualquer verificação. Ferramenta ausente não justifica
remoção — reporte finding com instrução de instalação.

### Dois níveis de teste

1. **Testes da aplicação** — validam o produto em
   desenvolvimento. Rodam via suítes/agregador
   `testes-produto`, executados pelo agente `qa` na fase
   Testes do workflow, sempre que se desenvolve funcionalidade.
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

O `AGENTS.md` do projeto mantém apenas a tabela índice das
suítes com link para esta seção
(`docs/README.md#testes-por-especialidade`).

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
- Specs executáveis da especialidade backend (Concordion-Markdown de
  `docs/specs/`), rodadas via Concordion com tradutor Python interno
  à suíte; spec falhando = bloqueante

**Ferramentas:** pytest (`.venv` do SO), ruff, shellcheck,
PSScriptAnalyzer, pytest-cov, Concordion (tradutor Python)

**Critérios:** qualquer teste falho, violação de lint ou cobertura
abaixo de 70% = finding bloqueante. Ferramenta ausente = finding
bloqueante com instrução de instalação (não remove o check).

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
- Specs executáveis da especialidade segurança (ex.: asserções de
  threat model e ADRs de segurança em Concordion-Markdown), rodadas
  via Concordion com tradutor Python interno à suíte; spec falhando
  = bloqueante

**Ferramentas:** gitleaks, pip-audit, bandit, Concordion (tradutor
Python)

**Critérios:** segredo detectado, vulnerabilidade high/critical ou
achado SAST high/critical = finding bloqueante. Ferramenta ausente =
finding bloqueante com instrução de instalação (não remove o check).
Ferramentas com rede seguem retry 3x; esgotado = finding bloqueante
com instrução de rede.

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
