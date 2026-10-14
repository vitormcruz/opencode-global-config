# Plano de Migração — Framework de Desenvolvimento Agêntico

Este documento registra as anotações, decisões, impactos e etapas necessárias para migrar a base atual do projeto para a arquitetura definida no novo **Framework de Desenvolvimento Agêntico**.

---

## 1. Visão Geral da Mudança

| Aspecto | Modelo Anterior | Novo Framework |
|---|---|---|
| **Conceito Central de Governança** | Regras e links dispersos ("Mapa do Produto") | **Diretrizes e Regras de Produto** como conceito unificador |
| **Especificação** | `docs/README.md` como "Mapa do Produto", com 4 seções | **Especificação do Produto**, com foco em escopo, elementos de especificação e documentação |
| **Validação de Links** | Curador não validava links para as especificações | `curador-produto` orienta e **valida ativamente a integridade dos links** das especificações |
| **Indexação de Código** | Seção obrigatória nas diretrizes de produto | **Removida** das diretrizes de produto (tratada como infraestrutura de tooling) |
| **Testes por Especialidade** | Seção embutida dentro do `docs/README.md` | **Arquivo próprio** (`docs/testes-por-especialidade.md`) referenciado pela especificação geral |
| **Instruções por Agente** | Seção solta no `AGENTS.md` | Subseção **inline** dentro de `## Diretrizes e Regras de Produto` no `AGENTS.md` |
| **Acoplamento dos Agentes** | Prompts apontando diretamente para caminhos físicos (`docs/README.md`) | **Agnósticos**: consultam apenas as referências da seção de diretrizes do `AGENTS.md` |
| **Papel do `curador-produto`** | Focado em editar seções do README e checar agregador | Único agente que conhece a governança, valida links, audita diretrizes e faz a ponte com o humano |

---

## 2. Inventário de Artefatos Impactados

### 2.1. Documentação de Especificação
- [ ] `docs/framework-desenvolvimento-agentico.md`: Documento em construção com as três dimensões (Governança, Ideação, Desenvolvimento).
- [ ] `docs/workflow-agentes-dev.md`: Documento legado a ser atualizado ou substituído após a conclusão do novo framework.
- [ ] `docs/README.md`: Atualizar estrutura para refletir a Especificação do Produto (separando Testes por Especialidade em arquivo próprio).
- [x] `docs/testes-por-especialidade.md`: Criar a especificação própria das
  suítes ao lado da Especificação do Produto.

### 2.2. Agente Guardião da Governança (`curador-produto`)
- [x] `harness-conf/agents/curador-produto.md`:
  - Atualizar descrição e escopo de atuação para três seções na Especificação do Produto.
  - Inverter a proibição: agora **deve** gerar e manter Testes por Especialidade em arquivo próprio.
  - Atualizar o fluxo de entrevista, validação e detecção de artefatos para a especificação separada.
- [ ] `harness-conf/agents/curador-produto.md`:
  - Adicionar validação ativa de links na tabela de Elementos de Especificação.
  - Remover referências à seção "Estratégias de Indexação de Código".
- [x] `harness-conf/agents/references/mensagens-curadoria.md`:
  - Atualizar mensagens de lacuna para considerar `docs/testes-por-especialidade.md`
    e o índice correspondente no `AGENTS.md`.

### 2.3. Templates em `default-artifacts`
- [x] `harness-conf/agents/default-artifacts/doc-readme-template.md`:
  - Renomear título e cabeçalho para **Especificação do Produto**.
  - Remover seção `## Testes por Especialidade` (passa a apenas linkar o arquivo dedicado).
- [x] `harness-conf/agents/default-artifacts/testes-por-especialidade-template.md`:
  - Adaptar para servir de template do arquivo independente `docs/testes-por-especialidade.md`.
- [x] `harness-conf/agents/default-artifacts/diretrizes-regras-produto-agents-md-template.md`:
  - Criar o template completo da seção `## Diretrizes e Regras de Produto`
    gravada no `AGENTS.md`, incorporando as Instruções por Agente e apenas
    referenciando os dois arquivos de especificação.
- [x] `harness-conf/agents/default-artifacts/instrucoes-por-agente-template.md`:
  - Remover o template separado depois de incorporar seu conteúdo ao
    template completo das Diretrizes.

### 2.4. Agentes Operacionais (Desacoplamento e Agnosticismo)
Remover caminhos físicos hardcoded (`docs/README.md`) e padronizar orientação para consultar `AGENTS.md -> ## Diretrizes e Regras de Produto`:
- [ ] `harness-conf/agents/eng-software.md`
- [ ] `harness-conf/agents/dba.md`
- [ ] `harness-conf/agents/sec.md`
- [ ] `harness-conf/agents/qa.md`
- [ ] `harness-conf/agents/front.md`
- [ ] `harness-conf/agents/rev.md`
- [ ] `harness-conf/agents/devflow.md`

### 2.5. Raiz do Repositório (`AGENTS.md`)
- [x] Reestruturar a âncora de governança para o bloco em destaque `## Diretrizes e Regras de Produto`, com links para a especificação geral, o arquivo independente de testes e instruções inline. A especificação de testes não é reproduzida.

### 2.6. Tooling e Código de Scaffold
- [x] `src/opencode_config/cli/scaffold_mapa.py`:
  - Atualizar as constantes de documentação para referenciar o contrato separado.
  - Remover do scaffold do README a cópia detalhada da especificação de testes.
  - Atualizar o índice de testes para apontar para `docs/testes-por-especialidade.md`.
- [x] `src/opencode_config/cli/scaffold_mapa.py`:
  - Gerar `testes-por-especialidade.md` no mesmo diretório do README e manter
    no `AGENTS.md` somente a referência para esse arquivo.

### 2.7. Suíte de Testes Automatizados
- [x] `tests/scaffold/test_mapa_produto.py`: Atualizar asserções de templates e scaffolds.
- [x] `tests/cli/test_scaffold_mapa_curadoria.py`: Atualizar asserções do scaffold
  para a especificação separada.
- [x] `tests/agents/test_curador_produto.py`: Atualizar asserções do contrato do
  curador e das mensagens de lacuna.
- [ ] `tests/agents/test_workflow_consistency.py`: Garantir consistência das menções e skills.
- [ ] `tests/agents/test_devflow.py`: Atualizar asserções que validam comportamento do orquestrador.

---

## 3. Fases de Execução da Migração

1. **Fase 1 — Conceitualização (Em andamento)**:
   - Concluir redação de Governança, Ideação e Desenvolvimento no novo framework (`docs/framework-desenvolvimento-agentico.md`).
2. **Fase 2 — Adaptação dos Templates (parcialmente concluída)**:
   - Ajustar `doc-readme-template.md`, `testes-por-especialidade-template.md` e
     `diretrizes-regras-produto-agents-md-template.md`.
3. **Fase 3 — Atualização do `curador-produto` (parcialmente concluída)**:
   - Implementar novas regras e validação ativa de links no prompt do agente curador.
4. **Fase 4 — Desacoplamento dos Agentes Operacionais**:
   - Atualizar os prompts dos agentes especialistas para consumir apenas as diretrizes no `AGENTS.md`.
5. **Fase 5 — Atualização de Código e Scaffold (parcialmente concluída)**:
   - Ajustar o CLI de scaffold para refletir a nova estrutura de arquivos.
6. **Fase 6 — Validação e Testes (concluída para esta fatia)**:
   - Rodar suíte completa de testes (`pytest -m all`) e corrigir eventuais regressões.

---

## 4. Decisões Consolidadas para a Próxima Revisão

### 4.1. Separação entre especificação do produto e especificação de testes

- A **Especificação do Produto** não deve conter a especificação detalhada
  de Testes por Especialidade.
- **Testes por Especialidade** permanece em arquivo próprio, na mesma pasta
  da Especificação do Produto.
- O arquivo de Especificação do Produto pode manter apenas uma referência
  curta para o arquivo de testes, porque a governança anterior definiu que
  esse vínculo deve existir. Essa referência não deve reproduzir conteúdo
  da especificação de testes.
- O `AGENTS.md` também referencia o arquivo efetivo de Testes por
  Especialidade dentro da seção **Diretrizes e Regras de Produto**.

### 4.2. Separação entre regras de teste e configuração por agente

- O arquivo **Testes por Especialidade** define:
  - suítes e scripts;
  - contrato de saída;
  - critérios;
  - limites;
  - ferramentas;
  - escopo de cada especialidade;
  - agregador.
- A subseção **Instruções por Agente**, dentro das Diretrizes e Regras de
  Produto, funciona como um ponto de configuração por repositório. Ela
  reúne as instruções específicas que o responsável pelo projeto decidir
  fixar para cada agente.
- Ainda está em decisão quais regras do framework serão obrigatórias para
  todos os agentes e quais poderão ser definidas ou ajustadas nesse
  ponto de configuração.
- As instruções atuais do `qa` e do `curador-produto` são uma proposta de
  configuração, não uma decisão final sobre o que ficará amarrado ao
  framework.
- Na próxima revisão, remover do template de Testes por Especialidade as
  referências operacionais ao `qa`, ao `curador-produto` e à etapa do
  workflow, caso elas não sejam necessárias para definir o contrato da
  suíte.

### 4.3. Flexibilidade das Instruções por Agente

- As instruções são copiadas para o `AGENTS.md` de cada projeto e podem
  ser ajustadas pelo responsável do projeto.
- O template deve funcionar como um hotspot de configuração, sem
  presumir que todo comportamento operacional será igual em todos os
  repositórios.
- A fronteira entre regras obrigatórias do framework e instruções abertas
  por projeto ainda será decidida. Essa decisão deve ser registrada antes
  da atualização definitiva dos agentes e do scaffold.

### 4.4. Estado observado nos templates

- `doc-readme-template.md` já não contém a seção detalhada de Testes por
  Especialidade. Ainda mantém uma referência ao arquivo próprio, o que é
  compatível com a arquitetura se essa referência curta for mantida.
- `testes-por-especialidade-template.md` já é uma especificação
  independente e não atribui mais a execução a um agente ou fase
  específicos.
- `diretrizes-regras-produto-agents-md-template.md` reúne a estrutura da
  seção das Diretrizes e as instruções de execução do `qa` e de validação
  do `curador-produto`. Essas instruções devem ser tratadas como defaults
  ajustáveis por projeto.
- O framework já descreve os três documentos, mas a redação deve deixar
  explícito que `doc-readme-template.md` e
  `testes-por-especialidade-template.md` definem arquivos próprios, enquanto
  o template das Diretrizes define a seção que os referencia e contém as
  Instruções por Agente.

### 4.5. Atualização desta revisão — 2026-10-09

- O `curador-produto` passou a tratar `docs/README.md` como a
  Especificação do Produto e `docs/testes-por-especialidade.md` como o
  contrato separado das suítes.
- As mensagens de curadoria passaram a detectar a ausência dos dois
  documentos e do índice de testes no `AGENTS.md`.
- O scaffold deixou de copiar a especificação detalhada de testes para o
  README e passou a apontar o índice para o arquivo separado.
- Os testes de agentes, scaffold e CLI foram atualizados. A suíte completa
  passou com `961 passed, 42 skipped, 31 deselected`.
- Permanecem para as próximas fatias a validação ativa dos links, a
  integração das Instruções por Agente à nova estrutura e o desacoplamento
  dos agentes operacionais e do `AGENTS.md` raiz.

### 4.6. Estrutura única das Diretrizes no `AGENTS.md` — 2026-10-13

- O `AGENTS.md` deve ter uma única seção de nível 2 chamada
  **Diretrizes e Regras de Produto**, localizada no final do arquivo.
- Essa seção reúne o link para a Especificação do Produto, a referência ao
  arquivo independente de Testes por Especialidade, a descrição dos
  artefatos gerados e a subseção **Instruções por Agente**.
- A subseção **Testes por Especialidade** contém somente a referência ao
  arquivo próprio. Não copia tabela, critérios, ferramentas ou scripts.
- Os nomes dos agentes ficam um nível abaixo de **Instruções por Agente**.
  A hierarquia deve deixar explícito que testes e instruções fazem parte das
  Diretrizes e Regras de Produto.
- Prompts, skills, templates e testes devem consultar os nomes lógicos das
  subseções, sem depender do nível Markdown ou de uma posição física fixa.
- O scaffold deve gerar a mesma hierarquia quando criar o índice no
  `AGENTS.md`.

### 4.7. Condensação da Construção no Fluxo — 2026-10-13

- O item `4.1` reúne a execução da construção e a sequência técnica dos
  agentes previstos no plano (`dba`, `front` quando aplicável e
  `eng-software`).
- O item `4.2` passa a tratar apenas do gate de refatoração, das mudanças no
  planejamento e da transição para a Revisão da Construção.
- Depois de cada correção, o `devflow` sempre consulta o humano antes de
  iniciar uma nova revisão. Somente uma resposta afirmativa permite
  re-revisão; essa decisão impede loops infinitos.
- Na Finalização, o ciclo de correção e revalidação também exige um gate
  humano antes de cada nova revalidação. Se o humano mandar parar, o Fluxo
  registra as lacunas e preserva o Arquivo de Planejamento e os artefatos
  auxiliares, sem declarar conclusão.
- A tabela de agentes continua descrevendo apenas as etapas genéricas do
  Desenvolvimento. **Inicialização** permanece no Fluxo Detalhado e na
  implementação do `devflow`, não como coluna ou etapa genérica.

### 4.8. Terminologia e referências — 2026-10-13

- Referências ativas a **Mapa do Produto** devem usar **Diretrizes e Regras
  de Produto** e **Especificação do Produto**, conforme o documento citado.
- A migração alcança `AGENTS.md`, os prompts que consultam documentação, o
  Fluxo de Definição de Escopo, o scaffold e os testes dos contratos.
- Ocorrências históricas no próprio plano e nomes técnicos legados, como
  `scaffold_mapa.py` e `test_mapa_produto.py`, permanecem sem renomeação.

### 4.9. Template da seção de Diretrizes no `AGENTS.md` — 2026-10-14

- `doc-readme-template.md` continua definindo o arquivo da Especificação do
  Produto.
- `testes-por-especialidade-template.md` continua definindo o arquivo
  independente de Testes por Especialidade e o contrato das suítes.
- `instrucoes-por-agente-template.md` deixa de existir como template separado.
- `diretrizes-regras-produto-agents-md-template.md` passa a definir a seção
  completa `## Diretrizes e Regras de Produto` no `AGENTS.md`, incluindo o
  índice dos dois arquivos independentes e a subseção **Instruções por
  Agente**. A seção não replica a especificação de testes.

### 4.10. Referência única para Testes por Especialidade — 2026-10-14

- `docs/testes-por-especialidade.md` é criado ao lado de `docs/README.md` e
  concentra a especificação detalhada das suítes.
- `docs/README.md` mantém apenas uma referência para esse arquivo.
- `AGENTS.md` mantém apenas uma referência para esse arquivo dentro das
  Diretrizes e Regras de Produto.
- O scaffold cria os dois arquivos juntos e nunca copia a especificação
  detalhada para o README ou para o `AGENTS.md`.
