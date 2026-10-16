# Plano de Migração — Framework de Desenvolvimento Agêntico

Status: REVISÃO DA CONSTRUÇÃO — aguardando autorização humana para nova revisão independente

Este documento registra as anotações, decisões, impactos e etapas necessárias para migrar a base atual do projeto para a arquitetura definida no novo **Framework de Desenvolvimento Agêntico**.

## Regras de Produto

Esta unidade não altera comportamento de produto, formatos, máscaras ou
limites de domínio; ela corrige contratos documentais e testes do Framework.

| Campo | Tam. máx | Tipo/Formato | Máscara | Limite | Obs |
|---|---|---|---|---|---|
| Comportamento de produto | (a definir) | (a definir) | (a definir) | (a definir) | Sem alteração nesta unidade; qualquer mudança futura retorna ao gate humano |

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
- [x] `docs/workflow-agentes-dev.md`: Removido em 2026-10-15, por decisão humana. Não sincronizar e não esperar revisão.
- [x] `docs/workflow-definicao-escopo.md`: Atualizado para consumir a
  referência lógica à Especificação do Produto sem caminho físico fixo.
- [x] `docs/README.md`: Estrutura já reflete a Especificação do Produto e aponta para o arquivo próprio de testes.
- [x] `docs/testes-por-especialidade.md`: Criar a especificação própria das
  suítes ao lado da Especificação do Produto.

### 2.2. Agente Guardião da Governança (`curador-produto`)
- [x] `harness-conf/agents/curador-produto.md`:
  - Atualizar descrição e escopo de atuação para três seções na Especificação do Produto.
  - Inverter a proibição: agora **deve** gerar e manter Testes por Especialidade em arquivo próprio.
  - Atualizar o fluxo de entrevista, validação e detecção de artefatos para a especificação separada.
- [x] `harness-conf/agents/curador-produto.md`:
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
- [x] `harness-conf/agents/eng-software.md`
- [x] `harness-conf/agents/dba.md`
- [x] `harness-conf/agents/sec.md`
- [x] `harness-conf/agents/qa.md`
- [x] `harness-conf/agents/front.md`
- [x] `harness-conf/agents/rev.md`
- [x] `harness-conf/agents/devflow.md`
- [x] `harness-conf/agents/curador-produto.md`

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
- [x] `tests/agents/test_boilerplate_consistency.py`: Atualizar o contrato compartilhado para preservar o agnosticismo dos agentes.
- [x] `tests/agents/test_workflow_consistency.py`: Garantir consistência das menções e skills após os gates serem corrigidos.
- [x] `tests/agents/test_devflow.py`: Atualizar asserções que validam comportamento do orquestrador sem cristalizar o contrato antigo.
- [x] `tests/agents/test_review_suites_gate.py`: Proteger reexecução determinística, gates humanos e as quatro etapas genéricas.

---

## 3. Fases de Execução da Migração

1. **Fase 1 — Conceitualização (Em andamento)**:
   - Concluir redação de Governança, Ideação e Desenvolvimento no novo framework (`docs/framework-desenvolvimento-agentico.md`).
2. **Fase 2 — Adaptação dos Templates (parcialmente concluída)**:
   - Ajustar `doc-readme-template.md`, `testes-por-especialidade-template.md` e
     `diretrizes-regras-produto-agents-md-template.md`.
3. **Fase 3 — Atualização do `curador-produto` (concluída nesta unidade)**:
   - Implementar novas regras e validação ativa de links no prompt do agente curador.
4. **Fase 4 — Desacoplamento dos Agentes Operacionais (alterações feitas)**:
   - Os prompts dos agentes passaram a consumir as diretrizes no `AGENTS.md`. A revisão independente recusada não trava esta fase.
5. **Fase 5 — Atualização de Código e Scaffold (concluída na fatia anterior)**:
   - Ajustar o CLI de scaffold para refletir a nova estrutura de arquivos.
6. **Fase 6 — Validação e Testes (suíte executada)**:
   - A suíte `pytest -m all` passou depois das alterações. A revisão independente recusada não deixa esta fase parada.

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
- Decidido em 2026-10-15, seção 4.13: o Framework fica fixo para todos
  os projetos. A subseção **Instruções por Agente** só acrescenta ou
  troca regra local. Não repete dever do Framework e não cancela gate,
  orquestração nem commit.
- As instruções do `qa` e do `curador-produto` que só repetiam a fase de
  Testes saem do template. O Framework já fixa essas tarefas.
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
- A fronteira foi decidida em 2026-10-15, seção 4.13. O template e o
  `AGENTS.md` deste repositório foram atualizados nessa data. Os prompts
  dos agentes não mudam nesta decisão: eles já executam o dever quando o
  `devflow` aciona.

### 4.4. Estado observado nos templates

- `doc-readme-template.md` já não contém a seção detalhada de Testes por
  Especialidade. Ainda mantém uma referência ao arquivo próprio, o que é
  compatível com a arquitetura se essa referência curta for mantida.
- `testes-por-especialidade-template.md` já é uma especificação
  independente e não atribui mais a execução a um agente ou fase
  específicos.
- `diretrizes-regras-produto-agents-md-template.md` reúne a estrutura da
  seção das Diretrizes. As instruções do `qa` e do `curador-produto` que
  repetiam o Framework saíram em 2026-10-15. Permanecem, como acréscimo
  ajustável, as instruções do `eng-software` e do `front`.
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

### 4.11. Fonte de verdade para a sincronização futura — 2026-10-14

- `docs/framework-desenvolvimento-agentico.md` é a fonte de verdade para
  revisar e ajustar o `devflow`, os agentes, os workflows relacionados e os
  testes de contrato.
- O `devflow` e os agentes ainda não foram todos atualizados para refletir
  as mudanças do Framework. A próxima execução deste plano deve tratar essa
  sincronização como trabalho pendente.
- A revisão futura deve partir integralmente do novo Framework, e não
  presumir que o workflow antigo ou os prompts atuais já estejam
  sincronizados com ele.
- A regra de autonomia do Framework prevalece: detalhes de execução,
  implementação e ajustes locais permanecem com os agentes e o `devflow`.
  O humano só deve ser consultado quando houver mudança de premissa,
  escopo, comportamento, arquitetura, planejamento ou outra decisão fora
  do trabalho aprovado.
- Em falhas de testes automáticos determinísticos, o `devflow` deve
  reexecutar os testes até obter aprovação. Após três falhas consecutivas
  da mesma execução, deve consultar o humano sobre uma análise diagnóstica
  adicional, sem aceitar a falha nem avançar para a Finalização.

### 4.12. Correção dos achados bloqueantes — 2026-10-14

- Reexecução de testes automáticos determinísticos é obrigatória após cada
  correção; falha bloqueia `FINALIZAÇÃO`. Depois de três falhas consecutivas,
  o `devflow` consulta o humano sobre análise diagnóstica adicional e não
  permite avanço sem aprovação dos testes.
- O gate humano de refatoração apresenta exatamente as três opções do
  Framework: manter o plano e ajustar a implementação; aprovar ajuste
  mínimo do plano e registrá-lo; ou retornar ao Planejamento. O `devflow`
  medeia a decisão e o executor não escolhe por conta própria.
- Toda re-revisão e toda nova revalidação exigem resposta afirmativa do
  humano; não há acionamento automático.
- O workflow mantém somente Planejamento, Construção, Revisão e Testes como
  etapas genéricas. Inicialização ocorre antes da confirmação do escopo e
  Finalização é fluxo posterior; `VALIDAÇÃO` não é fase nem status do
  workflow.
- Falhas de agentes são registradas e encaminhadas para retentativa ou
  outro agente adequado; não podem ser puladas silenciosamente. Os prompts
  operacionais permanecem agnósticos do roteamento, e a política de
  instâncias distingue continuidade confiável de estado parcial ou
  contraditório.

### 4.13. Fronteira entre Framework e Instruções por Agente — 2026-10-15

- O Framework é global. Ele fixa o fluxo para todos os projetos.
- A subseção **Instruções por Agente** é por repositório. O humano
  acrescenta uma regra local ou troca o texto copiado do template. Não
  repete o que o Framework já manda, e não cancela gate, orquestração
  nem commit.
- No template, saem as instruções do `qa` e do `curador-produto` que só
  repetiam a fase de Testes. As duas ficam `SEM INSTRUÇÕES A PEDIDO DO
  HUMANO`.
- Ficam no template as instruções do `eng-software` e do `front` para
  rodar os testes das próprias alterações. Isso não está no Framework.
- O `AGENTS.md` deste repositório passa a usar o que sobrou no template.
  A cópia foi pedida pelo humano. Não cria sincronização automática com
  os outros projetos.
- Os prompts dos agentes foram atualizados nesta execução para refletir
  o contrato único de resposta a quem os aciona. O `qa` e o
  `curador-produto` continuam com suas responsabilidades próprias, sem
  depender de conhecimento do roteamento.

### 4.14. Agnosticismo — 2026-10-15

- O humano aprovou a redação da premissa 8. O Framework foi consultado
  integralmente, sem alteração, e permanece a fonte de verdade.
- Os prompts de `dba`, `eng-software`, `front`, `qa`, `sec`, `rev`,
  `curador-produto` e `analista` foram tornados agnósticos: não citam
  roteamento, devolvem pergunta, falha e decisão a quem os acionou e
  não dependem de caminhos físicos das especificações.
- As seções de interação dos agentes operacionais foram padronizadas para
  devolver dúvida, falha e decisão a quem os acionou, sem consulta direta
  ao humano ou ramo por origem. `harness-conf/AGENTS.base.md`, a mensagem
  de lacuna, a interface de Testes por Especialidade, as skills
  `testes-produto-catalog` e `documentation-and-adrs` e os templates foram
  ajustados somente nos termos obsoletos, preservando nomes e caminhos
  documentais legítimos.
- O `devflow` agora registra no Arquivo de Planejamento a origem do escopo
  quando aplicável, o executor e o modelo utilizados; a opção de retorno
  ao Planejamento registra o `Status` correspondente e a Finalização aciona
  o `eng-software` para criar ou atualizar artefatos de especificação.
- O `rev` aceita o plano ou os insumos originais recebidos como régua; o
  `eng-software` identifica a acomodação como terceira parte, devolve teste
  contraditório a quem o acionou e registra a decisão recebida.
- A Especificação do Produto, a especificação de Testes por Especialidade
  e o documento de definição de escopo foram alinhados sem alterar o
  Framework; o documento simples recebeu apenas a atualização do ponteiro
  para o Framework.
- A trava `tests/agents/test_agnosticismo_agentes.py` cobre os agentes,
  referências, `harness-conf/AGENTS.base.md`, skills e templates, com
  padrões explícitos para ramos de acionamento, mediação, Fluxo, fase e
  etapa e exceções legítimas justificadas. O teste falhou com 2 achados
  antes das correções e passou com 2 testes depois delas. Os testes
  existentes foram ajustados somente onde contradiziam o contrato novo.
- A seção 6.8, item 3, que ainda descrevia encaminhamento ao `devflow`,
  fica superada por esta seção. Não foram reorganizadas as subseções
  duplicadas do registro de execução.
- Permanecem aguardando decisão humana, fora desta correção: `AGENTS.md`,
  a skill `question-orchestration`, a regra de quem atualiza `Status`, o
  placeholder `## Evidências de Testes — <etapa>` e a tabela de roteamento
  do `AGENTS.base.md`.

## 5. Histórico de commits para revisão

A próxima revisão do Framework deve consultar os commits abaixo. A relação
inclui todos os commits que alteraram o novo documento do Framework ou este
plano durante a construção e o refinamento do fluxo. Commits automáticos de
checkpoint não fazem parte da relação.

| Data | Commit | Foco da alteração |
|---|---|---|
| 2026-10-06 | `4ec6bb9664af260e07a0e80b0608b5f8317c1243` | Cria o Framework de Desenvolvimento Agêntico e o diagrama base |
| 2026-10-07 | `b93209e2b016a485a90198caa856a5d1809c1b05` | Organiza a Governança de Produto |
| 2026-10-07 | `bb76f943b83538accb91e2dd0817e23f1ae2e7dd` | Atualiza as Diretrizes de Produto |
| 2026-10-07 | `27dc35dbab0efa103f79389322599e5aa109e30a` | Separa Especificações e Instruções |
| 2026-10-07 | `0c78873768d8d9a3e0e5c80e493f1096647ab171` | Atualiza Diretrizes e templates |
| 2026-10-07 | `ba6a4da91e0ddd91c0f12566a214e14b5f838ae1` | Salva ajustes nos contratos |
| 2026-10-08 | `d4c1179f67ea1f1b40f3ea7fdd7fd35a885d636f` | Reorganiza contratos do workflow |
| 2026-10-08 | `2af77702fb6767af76aab5bbee65a4fc4d1fd08d` | Consolida o contrato do planejamento |
| 2026-10-08 | `f7846faaf1ac65737798fabc5540cb1c0d73461f` | Reorganiza o ciclo de desenvolvimento |
| 2026-10-08 | `9bf58f25a0952cc4d5512517afaf616f6569d092` | Consolida o ciclo de desenvolvimento |
| 2026-10-08 | `be2963b65300a0d582616802d078c1689ddaae19` | Agrupa as etapas do desenvolvimento |
| 2026-10-09 | `b5a5e57837ae80f84aad15f9e3017fc8e1ad5a11` | Separa o fluxo das etapas |
| 2026-10-09 | `b94dcc00feba1e7e27e33b40fa78c39ba4e90ffc` | Organiza as premissas do fluxo |
| 2026-10-09 | `e25e1d19ea876761aa4c40ed7adb3e65e3c05bec` | Registra ajustes do fluxo |
| 2026-10-09 | `539e246b1ab191bb16d03d1e6ebc6746ae80053e` | Atualiza o plano de migração |
| 2026-10-09 | `79ab1f5ae56b331be278ae9fcd9b9664ab00320e` | Ajusta a política de instâncias |
| 2026-10-09 | `5531cc8bd0062779aaae1fbe37969b42b3c44f61` | Descreve a etapa de Ideação |
| 2026-10-09 | `8e1664cab1da5d54211e87a0a737ffa452f23f32` | Detalha o fluxo de desenvolvimento |
| 2026-10-09 | `fa0752b1c9fff3f6d29293605d35ce599dcd3066` | Simplifica o fluxo textual |
| 2026-10-14 | `42e52a3de1411a93af5a6e53473b9fa48e104731` | Consolida Diretrizes e gates humanos |
| 2026-10-14 | `e4059adee26300be3ef9267302e50168275845ea` | Separa a especificação de testes |
| 2026-10-14 | `e1125984c16cf30f76679ca3fcda3945887d6dad` | Adiciona diagrama de raias do fluxo detalhado |

## 6. Registro da execução

- **Início:** 2026-10-14.
- **Executor:** `eng-software`, com `gpt-5.6-luna` em esforço `max`.
- **Revisor:** `rev`, com `grok-4.7` em esforço `high`. A plataforma não
  expõe um identificador `grok7`; o modelo disponível foi aprovado como
  substituto.
- **Unidade inicial:** sincronizar a implementação pendente a partir de
  `docs/framework-desenvolvimento-agentico.md`, respeitando as fases,
  dependências e itens ainda não concluídos deste plano.
- **Handoff inicial:** o executor deve ler este plano e o Framework antes de
  escolher a primeira unidade coerente, executar somente o escopo aprovado,
  registrar o progresso no plano e retornar um resumo curto. A revisão será
  feita por uma nova instância independente depois da conclusão da unidade.

### 6.1. Unidade bloqueada na revisão — sincronização contratual

- **Data:** 2026-10-14.
- **Escopo executado:** primeira unidade coerente pendente: sincronizar os
  agentes operacionais, o `devflow`, o `curador-produto`, os workflows
  relacionados e os testes de contrato com
  `docs/framework-desenvolvimento-agentico.md`.
- **Resultado da execução:** a implementação inicial foi feita sem mudança de
  premissa, escopo, comportamento de produto ou arquitetura, mas ficou
  bloqueada na revisão independente. O workflow de desenvolvimento deixou de
  usar `VALIDAÇÃO` na lista de status, passou a refletir parcialmente a
  política de instâncias por unidade coerente e recebeu alguns gates humanos.
  Ainda existem trechos conflitantes que permitem comportamento proibido pelo
  Framework.
- **Governança:** o `curador-produto` agora explicita a validação ativa da
  integridade dos links e não trata Estratégias de Indexação como seção da
  especificação. Os agentes operacionais consultam `AGENTS.md` e as
  referências lógicas das Diretrizes e Regras de Produto, sem caminhos físicos
  de documentação em seus contratos.
- **Testes como especificação:** os contratos diretamente afetados foram
  atualizados no planejamento desta migração. O ciclo RED registrou 11 falhas
  e 99 sucessos em 110 testes direcionados antes da implementação; após os
  ajustes, a suíte direcionada de agentes foi declarada como passando com 203
  testes, mas a revisão encontrou evidência local que exige nova execução após
  as correções. A declaração não é aceita como aprovação final da unidade.
- **Arquivos alterados nesta unidade:**
  - `docs/workflow-agentes-dev.md`
  - `docs/workflow-definicao-escopo.md`
  - `harness-conf/agents/curador-produto.md`
  - `harness-conf/agents/dba.md`
  - `harness-conf/agents/devflow.md`
  - `harness-conf/agents/eng-software.md`
  - `harness-conf/agents/front.md`
  - `harness-conf/agents/qa.md`
  - `harness-conf/agents/rev.md`
  - `harness-conf/agents/sec.md`
  - `tests/agents/test_construction_clean_code_skills.py`
  - `tests/agents/test_curador_produto.py`
  - `tests/agents/test_devflow.py`
  - `tests/agents/test_executores_instrucoes.py`
  - `tests/agents/test_review_suites_gate.py`
  - `tests/agents/test_sec.py`
  - `tests/agents/test_workflow_consistency.py`
  - `tests/scaffold/test_mapa_produto.py`

### 6.2. Revisão independente — bloqueada

- **Data:** 2026-10-14.
- **Revisor:** `rev`, com `grok-4.7` em esforço `high`.
- **Veredicto:** bloqueada; a unidade não pode avançar para a próxima fase.
- **Achados bloqueantes:**
  1. falhas determinísticas ainda podem seguir para `FINALIZAÇÃO`;
  2. o gate de refatoração não exige uma decisão humana com as três opções;
  3. trechos do `devflow` ainda reabrem revisão automaticamente;
  4. o workflow conserva `VALIDAÇÃO` como fase e tabelas incompatíveis;
  5. inicialização e revalidação têm procedimentos conflitantes;
  6. os testes ainda cristalizam o contrato de reexecução opcional e não
     protegem os gates novos;
  7. o plano marcava a sincronização como concluída antes da aprovação.
- **Observações para a correção:** revisar a descrição abreviada da política de
  instâncias, remover referências operacionais a fases nos prompts dos
  especialistas quando isso quebrar o agnosticismo e eliminar a opção de
  pular falhas de agentes sem decisão compatível com o Framework.
- **Próximo handoff:** criar nova instância de `eng-software` para corrigir
  somente os achados desta revisão, reabrir os itens correspondentes e
  atualizar a evidência de testes. Não alterar escopo, premissas ou
  arquitetura sem retornar ao humano.
- **Decisão arquitetural:** nenhuma decisão nova; nenhum ADR criado.
- **Commit:** nenhum commit local criado, conforme autorização vigente.
- **Preservação:** `master-nova.bundle` já existia como arquivo não rastreado e
  não foi alterado.

### 6.3. Correção dos achados e handoff para nova revisão — autorizado

- **Data:** 2026-10-14, execução registrada às 16:01 (UTC-03:00).
- **Executor:** `eng-software`, em nova unidade independente, lendo novamente
  este plano e `docs/framework-desenvolvimento-agentico.md`.
- **Escopo autorizado:** corrigir somente os achados da seção 6.2 e as
  observações necessárias para evitar contradições. Não houve alteração de
  produto, arquitetura, premissas ou comportamento fora do Framework.
- **Correções aplicadas:**
  1. `docs/workflow-agentes-dev.md` e
     `harness-conf/agents/devflow.md` tornam obrigatória a reexecução
     determinística, bloqueiam `FINALIZAÇÃO` com falha e exigem consulta
     humana após três falhas consecutivas, sem avanço sem aprovação.
  2. O gate de refatoração lista as três opções do Framework, com mediação
     do `devflow`, resposta humana obrigatória e registro da decisão.
  3. Cada re-revisão exige a pergunta **"Resubmeter para revisão?"** e cada
     nova revalidação exige **"Continuar a revalidação?"**; resposta não
     afirmativa interrompe o fluxo e preserva as lacunas.
  4. O workflow foi consolidado nas quatro etapas genéricas Planejamento,
     Construção, Revisão e Testes. Inicialização ficou em um único
     procedimento anterior à confirmação do escopo e Finalização em um
     único fluxo posterior. `VALIDAÇÃO` não aparece como fase ou status.
  5. A política de instâncias, o agnosticismo dos agentes e o tratamento de
     falhas de agentes foram explicitados; falhas não podem ser puladas
     silenciosamente.
  6. Os testes de contrato foram reforçados para proteger cada gate, sem
     converter falha em aprovação nem remover a exigência de comportamento.
- **Arquivos tocados nesta correção:**
  - `docs/workflow-agentes-dev.md`;
  - `harness-conf/agents/curador-produto.md`,
    `harness-conf/agents/dba.md`, `harness-conf/agents/devflow.md`,
    `harness-conf/agents/eng-software.md`, `harness-conf/agents/front.md`,
    `harness-conf/agents/qa.md`, `harness-conf/agents/rev.md` e
    `harness-conf/agents/sec.md`;
  - `tests/agents/test_boilerplate_consistency.py`,
    `tests/agents/test_devflow.py` e
    `tests/agents/test_review_suites_gate.py`;
  - este arquivo de planejamento.
- **RED comprovado antes da implementação:** os 37 testes direcionados
  novos/afetados executaram com 10 falhas e 27 sucessos antes das correções.
- **Resultado direcionado após as correções:** 37 testes passaram em
  `tests/agents/test_devflow.py tests/agents/test_review_suites_gate.py`
  com `-m unit`.
- **Regressões corrigidas:** a primeira suíte completa após as correções
  encontrou 6 falhas de compatibilidade textual/contratual; os prompts,
  o workflow e os contratos foram ajustados sem afrouxar os gates. A suíte
  de regressão dos arquivos afetados passou com 86 testes.
- **Resultado final da suíte obrigatória:** `.\.venv\Scripts\pytest.exe -m all`
  passou com 975 testes, 42 skips, 31 deselected e 1 warning não bloqueante
  de flutuação de versão do plugin `@slkiser/opencode-quota`.
- **Análise estática e higiene:** `python -m compileall -q src tests` passou;
  `git diff --check` passou. Ruff não foi instalado nem executado, pois não
  está disponível nas dependências do repositório.
- **Gate de refatoração:** não houve mudança de implementação de produto a
  decidir nesta correção. Se uma nova revisão identificar mudança de plano,
  o `devflow` deverá interromper e apresentar as três opções; nenhum
  executor escolheu uma opção por conta própria.
- **Status da unidade:** não aprovada. A execução verde comprova os testes,
  mas não substitui a revisão independente. A autorização afirmativa para
  nova instância de `rev` foi registrada na seção 6.4.
- **Handoff autocontido:** a nova revisão deve ler este arquivo, a seção 6.2,
  a seção 6.3 e `docs/framework-desenvolvimento-agentico.md`; revisar
  `docs/workflow-agentes-dev.md`, `harness-conf/agents/*.md` afetados e os
  testes listados; conferir todos os sete achados e as três observações;
  não declarar aprovação a partir dos testes verdes; preservar
  `master-nova.bundle` e alterações alheias; e foi autorizada após o humano
  responder afirmativamente **"Resubmeter para revisão?"**.

### 6.4. Gate humano de re-revisão — aprovado

- **Data:** 2026-10-14.
- **Pergunta apresentada:** `Resubmeter para revisão?`
- **Decisão:** sim, resubmeter para revisão independente.
- **Ação autorizada:** criar uma nova instância de `rev`, com
  `grok-4.7` em esforço `high`, para verificar a unidade corrigida. A
  instância revisora não deve corrigir arquivos nem criar commit.

### 6.5. Segunda revisão independente — bloqueada

- **Data:** 2026-10-14.
- **Revisor:** `rev`, com `grok-4.7` em esforço `high`.
- **Veredicto:** bloqueada; a unidade continua sem aprovação técnica.
- **Achados bloqueantes:**
  1. a Revisão do Plano foi removida da sequência executável e a Construção
     pode começar sem aprovação humana;
  2. o diagrama não ramifica as três opções do gate de refatoração;
  3. a resposta negativa à revalidação ainda alcança a pergunta de exclusão
     do plano;
  4. o `curador-produto` mantém um procedimento próprio de revalidação e
     exclusão fora do gate único do `devflow`;
  5. os testes de contrato foram enfraquecidos para verificar contagens e
     presenças de strings, sem proteger ordem e desfechos.
- **Melhorias pendentes:** desenhar no diagrama o retorno após três falhas,
  alinhar a tabela do `eng-software` à mediação do `devflow` e consolidar os
  dois textos sobre níveis de teste.
- **Próximo handoff:** criar nova instância de `eng-software` para corrigir
  os itens de prosa, diagrama e agentes, e atualizar os testes de contrato
  para verificar comportamento e ordem. Não declarar aprovação antes de nova
  revisão independente.

### 6.6. Decisão humana sobre recusa da re-revisão do plano

- **Data:** 2026-10-15.
- **Pergunta:** se o humano recusar **"Resubmeter para revisão?"** na
  Revisão do Plano, o fluxo deve travar a Construção sem pedir aprovação,
  ou seguir para a apresentação e a aprovação do plano?
- **Decisão:** manter a regra já aprovada no Framework. A recusa impede
  nova revisão, mas o `devflow` ainda apresenta o plano e pede aprovação.
  A Construção só começa depois dessa aprovação. Sem aprovação, o status
  permanece `REVISÃO DO PLANO`.
- **Correção exigida:** reverter no Framework, no workflow e nos testes o
  trecho que transforma a recusa em bloqueio direto da Construção. A
  pergunta explícita **"Resubmeter para revisão?"** permanece.
- **Fora desta decisão:** não alterar os outros gates aprovados. A suíte
  completa, `compileall`, `git diff --check` e o registro final desta
  correção continuam pendentes desde a interrupção de 2026-10-14.

### 6.7. Restrição de escopo — 2026-10-15

- O humano determinou que nenhuma modificação em
  `docs/framework-desenvolvimento-agentico.md` está autorizada sem
  consentimento explícito. As edições já feitas nesse arquivo devem ser
  revertidas para o HEAD commitado.
- `docs/workflow-agentes-dev.md` será removido ao final deste trabalho.
  Não deve mais ser ajustado. As edições já feitas nele também devem ser
  revertidas, porque não haverá sincronização desse arquivo.
- A execução seguinte fica restrita aos agentes, testes de contrato e
  demais artefatos que continuam no produto. A unidade permanece sem
  aprovação independente.

### 6.8. Correção restrita dos contratos remanescentes — execução atual

- **Data:** 2026-10-15.
- **Executor:** `eng-software`, em instância independente, sem commit.
- **Fonte de verdade:** `docs/framework-desenvolvimento-agentico.md`,
  lido sem alteração. Os achados exclusivos de
  `docs/workflow-agentes-dev.md` e do diagrama foram ignorados conforme a
  decisão humana.
- **Escopo executado:** somente os contratos dos agentes operacionais,
  `devflow`, `curador-produto` e os testes de contrato diretamente
  necessários. Nenhuma decisão de produto, premissa ou arquitetura foi
  alterada.
- **Correções aplicadas:**
  1. A recusa de **"Resubmeter para revisão?"** no `devflow` impede apenas
     uma nova revisão; o plano ainda é apresentado para aprovação, e a
     Construção só começa após essa aprovação. Sem aprovação, permanece
     `REVISÃO DO PLANO`.
  2. O `devflow` mantém a ordem `qa → sec → curador-produto`, a
     reexecução determinística obrigatória, o bloqueio de
     `FINALIZAÇÃO`, a consulta após três falhas e o gate de refatoração
     com três opções mediadas. A revalidação recusada preserva lacunas e
     não declara conclusão.
  3. **Superado pela seção 4.14:** o `curador-produto` só revisa,
     revalida ou exclui mediante solicitação de quem o acionou; os
     agentes operacionais devolvem decisões e dúvidas a quem os acionou,
     sem depender do roteamento.
  4. Os contratos de teste verificam ordem, dependências e desfechos,
     sem consultar ou cristalizar o workflow antigo.
- **Arquivos desta correção:**
  - `harness-conf/agents/curador-produto.md`;
  - `harness-conf/agents/dba.md`;
  - `harness-conf/agents/devflow.md`;
  - `harness-conf/agents/eng-software.md`;
  - `harness-conf/agents/front.md`;
  - `harness-conf/agents/qa.md`;
  - `harness-conf/agents/rev.md`;
  - `harness-conf/agents/sec.md`;
  - `tests/agents/test_devflow.py`;
  - `tests/agents/test_executores_instrucoes.py`;
  - `tests/agents/test_review_suites_gate.py`;
  - `tests/agents/test_workflow_consistency.py`;
  - este arquivo de planejamento.
- **Arquivos protegidos preservados:** não foram alterados
  `docs/framework-desenvolvimento-agentico.md`,
  `docs/workflow-agentes-dev.md`, `docs/svgImage/FluxoDetalhado.svg`,
  `docs/workflow-definicao-escopo.md` nem `master-nova.bundle`. Os dois
  arquivos documentais (`docs/svgImage/FluxoDetalhado.svg` e
  `docs/workflow-definicao-escopo.md`) já tinham alterações alheias e não
  foram revertidos.
- **Resultado:** a suíte de contratos afetados passou com 113 testes.
  A primeira execução completa após os ajustes encontrou três falhas
  determinísticas locais, corrigidas sem afrouxar os testes, e um timeout
  externo do `npm view` do plugin de quota. A repetição obrigatória de
  `.\.venv\Scripts\pytest.exe -m all` passou com 974 testes, 42 skips,
  31 deselected e uma advertência não bloqueante de flutuação de versão
  do plugin `@slkiser/opencode-quota`.
- **Demais evidências:** `python -m compileall -q src tests` passou;
  `git diff --check` passou; o teste de largura dos agentes passou na
  suíte completa. Não houve falha atribuível à memória externa do
  Crawl4AI.
- **Handoff:** a unidade continua sem aprovação. A próxima revisão
  independente não está autorizada; o humano deve decidir explicitamente
  qualquer re-revisão. Preservar o bundle, as alterações alheias e os
  arquivos protegidos. Não declarar conclusão a partir dos testes verdes.

## Evidências de Testes — Construção

- [x] Testes de contrato em RED da unidade inicial: 110 executados, 11
      falharam e 99 passaram antes da implementação.
- [x] Testes de contrato em RED da correção: 37 executados, 10 falharam e
      27 passaram antes da implementação.
- [x] Testes direcionados da correção: 37 passaram.
- [x] Regressão dos arquivos afetados: 86 passaram.
- [x] Testes direcionados de agentes e scaffold: 235 passaram.
- [x] Suíte completa inicial da unidade: 966 passaram, 42 ignorados e 31
      desmarcados; a evidência histórica permanece registrada.
- [x] Suíte completa final desta correção: 975 passaram, 42 ignorados e 31
      desmarcados; uma advertência não bloqueante registrou divergência de
      versão do plugin `@slkiser/opencode-quota`.
- [x] Análise estática de sintaxe final: `python -m compileall -q src tests`
      passou.
- [ ] Ruff: indisponível no ambiente (`No module named ruff`); não há Ruff
      listado nas dependências de desenvolvimento do repositório.
- [x] `git diff --check`: passou.
- [x] Regressão incremental: testes direcionados foram executados após os
      ciclos de alteração; a suíte completa foi repetida após as seis
      regressões e terminou verde. Não foi executada após cada edição textual
      individual.
- [x] Gate de refatoração: o gate humano foi explicitado e protegido por
      contrato; não houve decisão de mudança de produto nesta unidade.
- [x] TDD do achado da seção 6.11: o teste de regressão falhou antes da
      implementação e, após a correção, o teste novo e os três testes
      afetados passaram (`4 passed, 22 deselected`).
- [x] Suíte completa após a correção da seção 6.11: 976 passaram, 42
      ignorados e 31 desmarcados; houve apenas a advertência não
      bloqueante de flutuação externa do plugin
      `@slkiser/opencode-quota`.
- [ ] Aprovação da revisão independente: pendente; testes verdes não
      equivalem à aprovação da unidade.

## Perguntas

- A recusa de **"Resubmeter para revisão?"** na Revisão do Plano foi
  decidida em 2026-10-15: ela não cria nova revisão, mas o plano ainda é
  apresentado para aprovação antes da Construção.
- A correção restante ficou restrita a agentes, testes e artefatos que
  continuam no produto. O Framework e `docs/workflow-agentes-dev.md` foram
  revertidos e não devem ser editados.
- Em 2026-10-15 o humano recusou a re-revisão da correção da seção 6.11.
  A unidade permanece sem aprovação independente e sem commit.
- Em 2026-10-15 o humano fechou a fronteira da seção 4.13: Framework
  global, instrução por projeto só acrescenta ou troca regra local.
  Autorizou tirar do template as cópias do `qa` e do `curador-produto`
  e copiar o restante para o `AGENTS.md` deste repositório.

### 6.8. Gate humano de re-revisão — aprovado

- **Data:** 2026-10-15.
- **Pergunta apresentada:** `Resubmeter para revisão?`
- **Decisão:** sim, resubmeter para revisão independente.
- **Escopo da revisão:** agentes, testes de contrato e artefatos que
  continuam no produto. O Framework commitado é a fonte de verdade e não
  pode ser alterado. `docs/workflow-agentes-dev.md` foi revertido e será
  removido no fim do trabalho. Não exigir sincronização desse arquivo.
- **Ação autorizada:** criar uma nova instância de `rev`, com
  `grok-4.7` em esforço `high`. A instância não corrige arquivos nem
  cria commit.

### 6.9. Terceira revisão independente — bloqueada

- **Data:** 2026-10-15.
- **Revisor:** `rev`, com `grok-4.7` em esforço `high`.
- **Veredicto:** bloqueada. Os gates do `devflow` e do `curador-produto`
  foram aceitos. Três contratos restantes ainda desviam do Framework.
- **Achados bloqueantes:**
  1. `harness-conf/agents/eng-software.md`, por volta das linhas 245-254:
     a opção de manter o plano ainda manda o executor ajustar a
     implementação e registrar a decisão, sem passar pelo `devflow`.
     As três opções devem apenas encaminhar ao `devflow` e aguardar a
     resposta humana. O teste deve falhar se qualquer opção for executada
     antes disso.
  2. `harness-conf/agents/qa.md`, por volta das linhas 149-151: critério
     não testável é reportado ao solicitante ou ao humano. Em trabalho
     orquestrado, o destino deve ser somente o `devflow`. O teste deve
     vetar destinatário humano nesse passo.
  3. `tests/agents/test_devflow.py`, `tests/agents/test_workflow_consistency.py`
     e `tests/agents/test_question_orchestration_adoption.py` ainda leem
     `docs/workflow-agentes-dev.md`. Essas leituras devem sair. O arquivo
     antigo não deve ser editado nem sincronizado.
- **Fora da correção:** `docs/svgImage/FluxoDetalhado.svg` tem divergências
  visuais registradas pelo revisor, mas não bloqueia esta unidade e não
  deve ser alterado agora. `docs/workflow-definicao-escopo.md` não
  contradiz o Framework.
- **Próximo handoff:** nova instância de `eng-software` corrige somente
  esses três achados, sem tocar no Framework, no workflow antigo, no SVG
  ou no bundle. A unidade continua sem aprovação.

### 6.10. Gate humano de re-revisão — aprovado

- **Data:** 2026-10-15.
- **Pergunta apresentada:** `Resubmeter para revisão?`
- **Decisão:** sim, resubmeter para revisão independente depois da
  correção dos três achados da seção 6.9.
- **Ação autorizada:** criar uma nova instância de `rev`, com
  `grok-4.7` em esforço `high`. A instância não corrige arquivos nem
  cria commit. O Framework e `docs/workflow-agentes-dev.md` continuam
  fora de edição.

### 6.11. Quarta revisão independente — bloqueada

- **Data:** 2026-10-15.
- **Revisor:** `rev`, com `grok-4.7` em esforço `high`.
- **Veredicto:** bloqueada por um achado. Os achados 1 e 2 da seção 6.9
  foram aceitos. Os gates do `devflow` e do `curador-produto` continuam
  fechados.
- **Achado bloqueante:** `tests/agents/test_workflow_consistency.py`,
  função `_read_workflow_docs`, ainda abre todo `docs/workflow-*.md`.
  Como `docs/workflow-agentes-dev.md` existe, os testes das linhas 637,
  670 e 741 ainda leem esse arquivo e o tratam como restrição executável.
- **Correção:** excluir `docs/workflow-agentes-dev.md` da leitura, de
  forma que a execução não o abra. Não basta apagar o caminho literal.
  Não editar o workflow antigo, o Framework, o SVG nem o bundle.
- **Execução da correção:** nesta instância independente de `eng-software`,
  `_read_workflow_docs` passou a excluir `workflow-agentes-dev.md` antes
  de chamar `_read_text`. Foi adicionada uma regressão que verifica tanto
  a preservação dos workflows restantes quanto a ausência de leitura do
  workflow legado.
- **Escopo preservado:** somente
  `tests/agents/test_workflow_consistency.py` e este plano foram alterados
  nesta unidade. `docs/workflow-agentes-dev.md`,
  `docs/framework-desenvolvimento-agentico.md`,
  `docs/svgImage/FluxoDetalhado.svg`, `docs/workflow-definicao-escopo.md`
  e `master-nova.bundle` não foram editados.
- **TDD:** o teste de regressão falhou antes da correção; após a correção,
  o teste novo e os três testes afetados passaram (`4 passed, 22
  deselected`).
- **Evidências:** `.\.venv\Scripts\pytest.exe -m all` passou com 976
  testes, 42 skips, 31 deselected e um warning não bloqueante sobre a
  flutuação externa de versão do plugin `@slkiser/opencode-quota`;
  `python -m compileall -q src tests` passou; `git diff --check` passou
  com warning preexistente de normalização CRLF em
  `tests/agents/test_review_suites_gate.py`.
- **Handoff:** a unidade permanece sem aprovação e sem commit. A próxima
  revisão independente ainda não está autorizada; aguardar decisão
  explícita do humano.

### 6.12. Recusa da re-revisão — 2026-10-15

- **Pergunta apresentada:** `Resubmeter para revisão?`
- **Decisão:** não resubmeter agora.
- **Efeito:** a correção da seção 6.11 fica sem revisão independente. A
  unidade não é declarada aprovada e não há commit.
- **Esclarecimento pedido pelo humano:** a opção de parada não descrevia
  uma lista de defeitos de produto. As pendências reais estão abaixo.
- **Pendências reais:**
  1. a exclusão da leitura de `docs/workflow-agentes-dev.md` foi
     implementada depois da quarta revisão e não foi reavaliada;
  2. `docs/svgImage/FluxoDetalhado.svg` permanece divergente do Framework
     e ficou fora da correção: loop automático de revisão, gate de
     refatoração sem os três desfechos e retorno das três falhas para
     Testes, em vez de Planejamento ou Construção;
  3. `docs/workflow-agentes-dev.md` foi removido na seção 6.15. A
     remoção não quebrou testes.
- **Não são pendências de produto:** os checkboxes antigos das seções 2
  e 3 ficaram desatualizados em relação às decisões posteriores. Eles
  não devem ser lidos como defeitos abertos.

### 6.13. Remoção do workflow antigo e reversão do SVG — 2026-10-15

- **Decisão:** remover agora `docs/workflow-agentes-dev.md` para descobrir
  quais testes ainda dependem dele. Não criar um substituto.
- **Decisão:** desfazer as alterações locais de
  `docs/svgImage/FluxoDetalhado.svg`. Outra sessão já está tratando as
  imagens e resolveu esse desenho. Não editar outros arquivos de imagem.
- **Fora desta ação:** não alterar o Framework, não criar commit e não
  declarar a unidade aprovada.

### 6.10. Correção dos três achados da terceira revisão — execução atual

- **Data:** 2026-10-15.
- **Executor:** `eng-software`, nesta instância independente, sem commit e
  sem declarar aprovação.
- **Escopo:** somente os três achados bloqueantes da seção 6.9. O
  Framework commitado foi consultado como fonte de verdade e não foi
  alterado. O `docs/workflow-agentes-dev.md`, o SVG, o fluxo de definição
  de escopo e o bundle foram preservados.
- **Arquivos alterados nesta execução:**
  `harness-conf/agents/eng-software.md`,
  `harness-conf/agents/qa.md`,
  `tests/agents/test_eng_software.py`,
  `tests/agents/test_qa.py`,
  `tests/agents/test_devflow.py`,
  `tests/agents/test_workflow_consistency.py`,
  `tests/agents/test_question_orchestration_adoption.py` e este plano.
- **Correções aplicadas:**
  1. `harness-conf/agents/eng-software.md`: as três linhas de opção do
     gate agora têm a mesma ação única — encaminhar o fato ao `devflow` e
     aguardar a resposta humana. O texto também impede ajuste, registro ou
     escolha antes dessa resposta.
  2. `harness-conf/agents/qa.md`: critério de aceitação não testável é
     encaminhado exclusivamente ao `devflow` para mediação no passo de
     planejamento orquestrado.
  3. Os testes que dependiam do workflow antigo foram desacoplados:
     `tests/agents/test_devflow.py`,
     `tests/agents/test_workflow_consistency.py` e
     `tests/agents/test_question_orchestration_adoption.py` agora usam o
     Framework quando a proteção continua necessária. Os novos contratos
     vivem em `tests/agents/test_eng_software.py` e
     `tests/agents/test_qa.py`.
- **TDD:** após os testes dos contratos, a execução direcionada ficou
  vermelha com 68 testes selecionados, 2 falhas e 66 aprovações; depois
  das correções dos agentes, os 68 testes passaram.
- **Evidências:** `.\.venv\Scripts\pytest.exe -m all` passou com 975
  testes, 42 skips, 31 deselected e um warning não bloqueante sobre a
  flutuação externa de versão do plugin `@slkiser/opencode-quota`;
  `python -m compileall -q src tests` passou; `git diff --check` passou,
  com warning de normalização CRLF em alteração preexistente de
  `tests/agents/test_review_suites_gate.py`.
- **Handoff:** a unidade continua sem aprovação. Não há autorização para
  nova revisão independente; aguardar decisão explícita do humano. A
  próxima instância deve conferir somente estes três achados, preservar
  alterações alheias e não editar os arquivos protegidos.

### 6.14. Inventário pré-remoção do workflow — 2026-10-15

- **Decisão humana:** remover `docs/workflow-agentes-dev.md` agora, sem
  substituir seu conteúdo, para identificar dependências de testes.
- **Inventário realizado antes da exclusão:** a busca literal por
  `docs/workflow-agentes-dev.md` e `workflow-agentes-dev` encontrou:
  - `AGENTS.md:131`;
  - `tests/agents/test_workflow_consistency.py:229,634` — um arquivo de
    teste e um teste explícito (`test_read_workflow_docs_does_not_open_legacy_workflow`);
  - `docs/workflow-agentico-simples.md:7`;
  - `plan/plano-migracao-framework-agentico.md:37,390,445,464,498,559,
    572,609,671,683,708,726,738,740,744,750,776,782,790,805`;
  - `plan/plano-revisao-comunicacao-planejamento-agentes.md:235,280,493,
    567,589,602,1080,1097`;
  - `plan/plugin-dcp-opencode.md:256,711,721,902,955,1370,1455,1523,
    1586,2327,2789`.
- **Ausências confirmadas:** nenhuma ocorrência em
  `harness-conf/agents/`, `src/` ou `scripts/`; nenhuma outra ocorrência
  em `tests/`. O arquivo removido não foi contado como referência.
- **Vínculo dos testes:** um teste explícito (em um arquivo) mencionava o
  nome, mas o contrato já verificava que o workflow legado não fosse
  aberto; não há, neste inventário, teste que dependa do conteúdo real do
  arquivo. A lista acima é o registro exigido antes da exclusão e as
  referências históricas fora do escopo serão preservadas.

### 6.15. Execução após a remoção — 2026-10-15

- **Alterações realizadas:** `docs/svgImage/FluxoDetalhado.svg` foi
  restaurado exatamente ao `HEAD`; `docs/workflow-agentes-dev.md` foi
  removido da worktree. Nenhum outro arquivo em `docs/svgImage` ou imagem
  foi alterado. `docs/workflow-definicao-escopo.md`,
  `docs/framework-desenvolvimento-agentico.md` e `master-nova.bundle`
  foram preservados.
- **Testes quebrados pela remoção:** nenhum. Não foi necessário alterar
  testes nem afrouxar contratos; o teste que mencionava o nome já
  verificava a exclusão do workflow legado da leitura. O arquivo de teste
  relacionado executou **26 passed**.
- **Evidências:** `.\.venv\Scripts\pytest.exe
  tests/agents/test_workflow_consistency.py` — 26 passed; `.\.venv\Scripts\
  pytest.exe -m all` — 976 passed, 42 skipped, 31 deselected e 1 warning
  não bloqueante sobre a flutuação externa de versão do plugin
  `@slkiser/opencode-quota`; `python -m compileall -q src tests` — passou;
  `git diff --check` — passou, com warning preexistente de normalização
  CRLF em `tests/agents/test_review_suites_gate.py`.
- **Estado:** sem commit e sem aprovação; o arquivo removido permanece
  ausente e o diff do SVG alvo está limpo.

### 6.16. Ponteiro do `AGENTS.md` — 2026-10-15

- **Decisão:** trocar a regra de sincronização que cita
  `docs/workflow-agentes-dev.md`. O destino passa a ser
  `docs/framework-desenvolvimento-agentico.md` e
  `docs/workflow-definicao-escopo.md`.
- **Fora desta decisão:** não recriar o workflow removido, não alterar o
  Framework, não editar as imagens e não criar commit. A menção histórica
  em `docs/workflow-agentico-simples.md` não entra nesta troca.

## Evidências de Testes — ponteiro do `AGENTS.md` — 2026-10-15

- **TDD/red:** o teste novo
  `test_agents_md_points_to_active_workflow_sources` falhou antes da
  alteração do `AGENTS.md` (1 failed), pois ainda encontrava o ponteiro
  legado.
- **Testes afetados:** `.\.venv\Scripts\pytest.exe
  tests/agents/test_workflow_consistency.py -q` — 27 passed.
- **Testes totais:** `.\.venv\Scripts\pytest.exe -m all` — 977 passed,
  42 skipped, 31 deselected e 1 warning não bloqueante sobre a flutuação
  externa de versão do plugin `@slkiser/opencode-quota`.
- **Compilação:** `python -m compileall -q src tests` — passou.
- **Integridade do diff:** `git diff --check` — passou; exibiu somente o
  warning preexistente de normalização CRLF em
  `tests/agents/test_review_suites_gate.py`.
- **Gate de refatoração:** sem refatoração; o escopo permaneceu limitado ao
  ponteiro do `AGENTS.md`, ao teste contratual e a esta evidência. Nenhum
  commit foi criado.

## Evidências de Testes — Agnosticismo e decisões humanas — 2026-10-15

- [x] TDD da trava de agnosticismo: `tests/agents/test_agnosticismo_agentes.py`
  foi executado em RED antes das correções (2 falhas) e passou depois.
- [x] Subconjunto afetado final:
  `.\.venv\Scripts\pytest.exe tests\agents tests\scaffold
  tests\test_agents_md.py` — 252 passaram.
- [x] Análise estática: `python -m compileall -q src tests` passou; Ruff
  não está disponível no ambiente (`No module named ruff`).
- [x] Decisões liberadas pelo humano:
  `test_executores_instrucoes.py`, `test_workflow_consistency.py`,
  `test_testes_produto_catalog.py`, a trava de agnosticismo, largura e
  estrutura — 94 passaram.
- [x] A primeira suíte completa após as correções encontrou uma expectativa
  obsoleta no catálogo (`docs/README.md`); o teste foi ajustado para exigir
  a referência pelas Diretrizes do `AGENTS.md`.
- [x] Suíte completa final:
  `.\.venv\Scripts\pytest.exe -m all` — 980 passaram, 42 ignorados,
  31 desmarcados e 1 warning não bloqueante sobre a flutuação externa
  de versão do plugin `@slkiser/opencode-quota`; não houve falha do
  Crawl4AI.
- [x] `git diff --check`: passou, com avisos de normalização CRLF
  preexistentes nos documentos alterados.
- [x] Framework, workflow legado, bundle e smart-planner foram preservados;
  o documento simples recebeu somente a troca do ponteiro para o Framework.
- [ ] Achado 26: alinhamento amplo do `docs/README.md` com Framework/workflows
  continua pendente conforme decisão humana.
