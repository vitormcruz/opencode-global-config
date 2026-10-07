# Plano de Migração — Framework de Desenvolvimento Agêntico

Este documento registra as anotações, decisões, impactos e etapas necessárias para migrar a base atual do projeto para a arquitetura definida no novo **Framework de Desenvolvimento Agêntico**.

---

## 1. Visão Geral da Mudança

| Aspecto | Modelo Anterior | Novo Framework |
|---|---|---|
| **Conceito Central de Governança** | Regras e links dispersos ("Mapa do Produto") | **Diretrizes e Regras de Produto** como conceito unificador |
| **Especificação Geral** | `docs/README.md` como "Mapa do Produto", com 4 seções | **Especificação Geral do Produto**, com foco em escopo, elementos de especificação e documentação |
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
- [ ] `docs/README.md`: Atualizar estrutura para refletir a Especificação Geral do Produto (separando Testes por Especialidade em arquivo próprio).

### 2.2. Agente Guardião da Governança (`curador-produto`)
- [ ] `harness-conf/agents/curador-produto.md`:
  - Atualizar descrição e escopo de atuação.
  - Inverter a proibição: agora **deve** gerar e manter Testes por Especialidade em arquivo próprio.
  - Adicionar capacidade/instrução para validação ativa de links na tabela de Elementos de Especificação.
  - Remover referências à seção "Estratégias de Indexação de Código".
  - Atualizar formato de saída e mensagens de lacuna (`agents/references/mensagens-curadoria.md`).

### 2.3. Templates em `default-artifacts`
- [ ] `harness-conf/agents/default-artifacts/doc-readme-template.md`:
  - Renomear título e cabeçalho para **Especificação Geral do Produto**.
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
