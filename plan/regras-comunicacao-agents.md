# Plano: Regras de Comunicação no Contexto do Agente

## Overview

Corrigir falhas de comunicação recorrentes dos agentes, comprovadas em
sessão real: skill humanizer-br não carregada no início da conversa,
contextualização ausente nas discussões (códigos internos do plano usados
como memória compartilhada) e tradução literal de jargão consagrado
("cano" para pipe). Diagnóstico: regras de CONTEÚDO no AGENTS base são
seguidas; instruções de AÇÃO adiada ("carregue skill X antes de responder")
falham com frequência. Correção: mover o essencial para o AGENTS.base.md.

## Architecture Decisions

- **D1 — Essencial de comunicação embutido no AGENTS.base.md** (seção
  Comunicação), sem depender de carga de skill:
  (a) condensado da humanizer-br (~20 linhas);
  (b) condensado de contextualização (~6 linhas): plano e artefatos de
  estado são do agente, o humano não os lê; toda interação é autocontida;
  na conversa, nunca usar códigos internos (D2, task 5) sem explicar o que
  são;
  (c) bloco de jargão técnico com exemplos negativos (pipe nunca "cano",
  socket nunca "tomada", commit nunca "consolidação", branch nunca "ramo").
- **D2 — Alcance da contextualização estendido na skill
  question-orchestration:** "pergunta, confirmação ou decisão **ou
  discussão**" na seção Contextualização com artefato persistido.
- **D3 — Skills completas permanecem:** humanizer-br e
  portugues-tecnico-controlado continuam existindo para carga em textos
  densos; o AGENTS.base carrega o essencial para o dia a dia.
- **D4 — Sem breaking changes estruturais:** AGENTS.base é consumido pelo
  adapter OpenCode (AGENTS global gerado) e pelo Copilot (cópia
  .copilot/AGENTS.md); a mudança é de conteúdo, sem mexer no mecanismo.

## Task List

### Fase 1 — Conteúdo

- [x] Task 1: Três blocos novos no AGENTS.base.md
  - Description: adicionar à seção Comunicação de
    `harness-conf/AGENTS.base.md`:
    (a) "### Escrita natural (essencial)" — condensado da humanizer-br:
    travessão proibido (use vírgula, ponto ou parênteses); frases curtas
    (máx. ~25 palavras) com ritmo variado; sem trios mecânicos de
    adjetivos; sem adjetivos vagos ("robusto", "essencial", "abrangente");
    sem conectivos de enchimento ("além disso", "portanto" iniciando
    frase); sem gerúndio conclusivo; sem frases de chatbot ("espero que
    ajude", "ótima pergunta"); conclusão com fato concreto, não frase
    genérica. Fechar com: "Para textos densos (specs, docs, comunicações
    importantes), carregue a skill `humanizer-br`."
    (b) "### Conversa sobre plano" — plano e artefatos de estado são do
    agente; o humano não os lê; toda pergunta, decisão OU discussão é
    autocontida (fase, trecho relevante, escopo); na conversa, nunca
    referenciar códigos internos (D2, task 5) sem dizer o que são; nome e
    descrição valem mais que identificador.
    (c) "### Jargão técnico" — termos consagrados permanecem em inglês,
    sem tradução literal nem aportuguesamento, inclusive ao introduzir o
    conceito: pipe (nunca "cano"), socket (nunca "tomada"), symlink,
    commit (nunca "consolidação"), branch (nunca "ramo"), build, deploy,
    wrapper, fallback, checkpoint, staging; quando houver tradução comum
    ("link simbólico", "variável de ambiente"), qualquer forma serve;
    prosa em PT-BR, jargão em inglês.
    Reposicionar a regra existente de carga da humanizer (seção "Tom
    natural") para apontar ao condensado: o corpo segue com a regra de
    carga para textos densos. Linhas com no máximo 120 colunas.
  - Acceptance criteria:
    - [x] Os três blocos existem com os pontos acima, sem citar códigos
          de decisão deste plano.
    - [x] Nenhuma linha passa de 120 colunas.
    - [x] Regras existentes (língua, perfil, concisão) intactas.
  - Verification: leitura do diff + verificação de 120 colunas.
  - Dependencies: None
  - Files likely touched: `harness-conf/AGENTS.base.md`.
  - Estimated scope: Small
- [x] Task 2: Alcance de discussão na question-orchestration
  - Description: em `harness-conf/skills/question-orchestration/SKILL.md`,
    seção "Contextualização com artefato persistido", estender "toda
    interação com o humano — pergunta, confirmação ou decisão" para
    incluir "ou discussão". Sem outras alterações; description da skill
    intocada.
  - Acceptance criteria:
    - [x] A seção cobre explicitamente discussão livre, não só perguntas
          formais.
    - [x] Nada mais mudou na skill.
  - Verification: diff do arquivo.
  - Dependencies: None
  - Files likely touched:
    `harness-conf/skills/question-orchestration/SKILL.md`.
  - Estimated scope: Small

### Checkpoint: Fase 1

- [x] `.venv/bin/pytest -m all` verde no WSL (ajustes em
      `tests/test_agents_md.py` ou de consistência, se algum teste cobrir
      o conteúdo, são permitidos — registrados no relatório).
      Resultado: 724 passed, 28 deselected (agent_eval), 0 failed,
      0 ajustes de teste necessários.
- [x] Commits: `docs(agents): regras de comunicacao essenciais no AGENTS
      base` (task 1) e `docs(skills): contextualizacao cobre discussao`
      (task 2).

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Condensado grande demais inflaciona todo contexto | Med | Limite ~40 linhas no total dos três blocos; essencial apenas |
| Teste de consistência do AGENTS quebra | Baixo | Checkpoint roda `-m all`; ajustes registrados |
| Adapter Copilot espelhar mudança sem revisar | Baixo | Conteúdo é harness-agnóstico (vale para os dois) |

## Open Questions

- Nenhuma. Redações-chave aprovadas pelo humano na conversa.
