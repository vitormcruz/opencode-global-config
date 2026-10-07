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

### 2.2. Agente Guardião da Governança (`curador-produto`)
- [ ] `harness-conf/agents/curador-produto.md`:
  - Atualizar descrição e escopo de atuação.
  - Inverter a proibição: agora **deve** gerar e manter Testes por Especialidade em arquivo próprio.
  - Adicionar capacidade/instrução para validação ativa de links na tabela de Elementos de Especificação.
  - Remover referências à seção "Estratégias de Indexação de Código".
  - Atualizar formato de saída e mensagens de lacuna (`agents/references/mensagens-curadoria.md`).

### 2.3. Templates em `default-artifacts`
- [ ] `harness-conf/agents/default-artifacts/doc-readme-template.md`:
  - Renomear título e cabeçalho para **Especificação do Produto**.
  - Remover seção `## Estratégias de Indexação de Código`.
  - Remover seção `## Testes por Especialidade` (passa a apenas linkar o arquivo dedicado).
- [ ] `harness-conf/agents/default-artifacts/testes-por-especialidade-template.md`:
  - Adaptar para servir de template do arquivo independente `docs/testes-por-especialidade.md`.
- [ ] `harness-conf/agents/default-artifacts/instrucoes-por-agente-template.md`:
  - Integrar à nova estrutura da seção `## Diretrizes e Regras de Produto`.

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
- [ ] Reestruturar a âncora de governança para o bloco em destaque `## Diretrizes e Regras de Produto`, com links para a especificação geral, testes por especialidade e instruções inline.

### 2.6. Tooling e Código de Scaffold
- [ ] `src/opencode_config/cli/scaffold_mapa.py`:
  - Atualizar constantes de templates (`HARNESS_TEMPLATE`, seções de documentação).
  - Remover geração de `Estratégias de Indexação de Código`.
  - Gerar o arquivo dedicado para `testes-por-especialidade.md`.

### 2.7. Suíte de Testes Automatizados
- [ ] `tests/scaffold/test_mapa_produto.py`: Atualizar asserções de templates e scaffolds.
- [ ] `tests/agents/test_workflow_consistency.py`: Garantir consistência das menções e skills.
- [ ] `tests/agents/test_devflow.py`: Atualizar asserções que validam comportamento do orquestrador.

---

## 3. Fases de Execução da Migração

1. **Fase 1 — Conceitualização (Em andamento)**:
   - Concluir redação de Governança, Ideação e Desenvolvimento no novo framework (`docs/framework-desenvolvimento-agentico.md`).
2. **Fase 2 — Adaptação dos Templates**:
   - Ajustar `doc-readme-template.md`, `testes-por-especialidade-template.md` e `instrucoes-por-agente-template.md`.
3. **Fase 3 — Atualização do `curador-produto`**:
   - Implementar novas regras e validação ativa de links no prompt do agente curador.
4. **Fase 4 — Desacoplamento dos Agentes Operacionais**:
   - Atualizar os prompts dos agentes especialistas para consumir apenas as diretrizes no `AGENTS.md`.
5. **Fase 5 — Atualização de Código e Scaffold**:
   - Ajustar o CLI de scaffold para refletir a nova estrutura de arquivos.
6. **Fase 6 — Validação e Testes**:
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
- O arquivo **Instruções por Agente** funciona como um ponto de
  configuração por repositório. Ele reúne as instruções específicas que
  o responsável pelo projeto decidir fixar para cada agente.
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
  independente, mas ainda contém frases que atribuem sua execução ao
  `qa` e a validação da evidência ao `curador-produto`. Essas frases
  precisam ser revistas em conjunto com as instruções por agente.
- `instrucoes-por-agente-template.md` já recebeu as instruções de
  execução do `qa` e de validação do `curador-produto`. Essas instruções
  devem ser tratadas como defaults ajustáveis por projeto.
- O framework já descreve os três documentos, mas a redação deve deixar
  explícito que o template de testes define o contrato e o template de
  instruções oferece um ponto de configuração por repositório.
