# Plano — Revisão de Comunicação e Planejamento dos Agentes

## Overview

O humano anotou problemas de comunicação e de planejamento no uso dos
agentes. Este plano percorre os problemas item a item: para cada um,
ajustamos a formulação da regra e conferimos o resultado esperado
(comportamento observável e forma de verificar). O produto final é um
insumo de revisão e ajuste, autocontido, a ser executado pelo `devflow`,
que adapta ao projeto global (`harness-conf/`) o que for validado aqui.

Duas frentes, já acordadas em conversa anterior:

- **Comunicação**: regras que valem para todos os agentes. Testes de
  diálogo cobrem todos.
- **Planejamento**: protocolo específico de `smart-planner` e `devflow`.
  Revisores só entram se suas instruções mudarem.

## Problemas relatados pelo humano (insumo, 2026-09-27)

1. Abreviações demais na comunicação.
2. Referências a numerações do plano sem contexto: o humano não lê o
   plano; o agente apresenta o que está sendo discutido em termos
   simples, contextualizado, por partes; resumo dirigido ao final.
3. Texto demais quando o humano reclama, em vez de separar em partes.
4. Várias perguntas ao mesmo tempo exigindo muito contexto; o agente
   superestima a memória e a capacidade de processamento do humano.
5. Tool de pergunta com alternativas para questões sem entendimento
   confirmado, com alternativas aleatórias; usar só em escolhas
   fechadas e óbvias.
6. Contestação de premissa: assumir que o humano não leu o restante;
   reapresentar e, se necessário, ajustar o conteúdo dependente.
7. Perguntas demais sobre detalhe de escrita do plano; perguntar só o
   que afeta o resultado.
8. Esquecer o protocolo: texto longo ou resumo com informação que o
   humano não passou.
9. Avançar para ações durante resolução de dúvidas, sem terminar a
   discussão.
10. Planejador e revisor tratarem alteração como simples ou postergável
    sem autorização; padrão é cobrir tudo, salvo ordem explícita.
11. Pedir confirmação para detalhe de implementação que não muda
    premissas.

## Architecture Decisions

### Diretriz de localização (decisão do planejador, detalhe de
### implementação)

- Regras gerais de comunicação: `harness-conf/AGENTS.base.md`, seção
  Comunicação.
- Protocolo de perguntas, confirmação e ritmo da conversa: skill
  `question-orchestration`.
- Cobertura de escopo do planejamento e revisão: `smart-planner` e
  revisores.

### Regras aprovadas (item a item)

**Ramo do insumo 1 — Conferência do resultado na execução (aprovado).**
Depois de aplicar uma regra no arquivo do agente, confirmar que o agente
passou a se comportar diferente: conversar com o agente usando o mesmo
roteiro, antes e depois da mudança, e comparar as duas conversas.
Comportamento não mudou: a regra está mal escrita e é ajustada.

Detalhes operacionais (decisão do planejador, detalhe de implementação):
uma regra ou grupo pequeno por vez; diálogo de referência em sessão
limpa antes da mudança; mesmo diálogo depois; comparar respostas, uso de
ferramentas e ações; em marcos, mostrar trecho curto da conversa ao
humano para validar clareza.

**Ramo do insumo 2 — Casos de teste (aprovado).** O insumo de testes de
comportamento (`plan/insumo-testes-comportamento-agentes.md`) ganha
seção com os casos derivados das regras aprovadas: cada regra vira
roteiro de conversa que o teste verifica. Regra global de comunicação e
protocolo de perguntas: caso com um agente. Regra específica de agente:
caso com o agente afetado. Os casos reutilizam as técnicas já decididas
no insumo (execução real, asserção de trajetória, juiz com rubrica,
consenso).

**Ramo do insumo 3 — Ordem de aplicação (aprovado).** Regras de
comunicação primeiro (valem para todos os agentes e baseiam as conversas
de verificação), depois as de planejamento (`smart-planner`, `devflow` e
revisores).

**Item 1 — Abreviações (aprovado).** Destino: `AGENTS.base.md`, seção
Comunicação, subseção "Sem abreviações":

- Escreva palavras por extenso; não abrevie palavras nem crie siglas
  próprias.
- Sigla consagrada da área técnica (TDD, API, CI) pode aparecer sem
  expansão.
- Sigla interna do projeto ou do plano, e termo de domínio afastado,
  exigem nome por extenso no primeiro uso, em linguagem simples.

Verificação: conversa roteirizada em que o agente explica uma decisão;
a transcrição não pode ter abreviação de palavra, sigla própria ou sigla
interna sem definição; sigla técnica consagrada é aceita. Caso futuro da
suíte de comunicação.

**Item 2 — Referências ao plano (aprovado).** Destino: `AGENTS.base.md`,
seção Comunicação, subseção "Conversa sobre plano" (reformulação):

- Plano e artefatos de estado são do agente; o humano não os lê.
- Toda pergunta, decisão ou discussão é autocontida: traga a fase atual,
  o trecho relevante e o escopo da questão, em termos simples.
- Nunca referencie número, código, sigla ou link interno do plano:
  apresente o conteúdo discutido, contextualizado.
- Apresente por partes: uma etapa ou decisão por vez. Resumo de etapas
  é permitido; ao encerrar, um resumo dirigido do todo, também por
  partes.
- Antes de enviar a apresentação de um ponto ao humano, aplique o teste
  da reapresentação: escreva a versão que você escreveria se ele
  tivesse acabado de responder "não entendi", e envie essa. Nela, o
  mecanismo concreto vem antes da referência ao plano; um exemplo vem
  antes do geral; jargão interno (número de item, task, achado) só com
  tradução imediata.

Verificação: conversa roteirizada com várias decisões em jogo; a
transcrição não pode ter número, código ou link do plano sem o conteúdo
contextualizado; na apresentação de ponto técnico complexo, a primeira
versão já traz mecanismo concreto e exemplo, sem jargão interno, e o
humano não precisa pedir reapresentação. Caso futuro da suíte de
comunicação.

**Item 3 — Volume na comunicação (aprovado).** Destino: `AGENTS.base.md`,
seção Comunicação, seção Concisão (acréscimo operacional):

- Uma ideia central por resposta. Duas ou mais ideias? Separe e
  apresente uma por turno.
- Antes de enviar, confira: a resposta tem uma única ação ou decisão?
  Se não, corte o excedente e guarde para o turno seguinte.
- Reclamação de confusão: reapresente o ponto em menos linhas do que a
  mensagem original. Nunca reescreva tudo nem acrescente detalhe.
- Cada resposta se sustenta sozinha: antes da novidade, reapresente em
  uma linha o ponto da conversa a que ela se refere.

Verificação: conversa roteirizada; nenhuma resposta concentra mais de
uma ideia central por turno; resposta a reclamação de confusão menor
que a original; entrega solicitada vem completa e não conta como
violação do volume. Caso futuro da suíte de comunicação.

**Item 4 — Perguntas múltiplas (aprovado).** Destinos: skill
`question-orchestration` (trecho "Perguntas em blocos adaptativos",
reformulação) e `AGENTS.base.md` (seção Concisão, acréscimo).

Skill `question-orchestration`:

- Uma pergunta por rodada é o padrão.
- Agrupe só quando as duas condições valem: cada pergunta é entendível
  sem as outras, e nenhuma exige contexto novo nem lembrança de turnos
  anteriores. Mesmo assim, no máximo 4.
- Perguntas dependentes entre si: uma por vez, na ordem da dependência.
- Pergunta que exige contexto novo: apresente sozinha, com o contexto
  reapresentado.

`AGENTS.base.md` (Concisão):

- Menor é melhor, desde que não gere abreviação nem confusão.
- Texto acima de ~5 linhas ou 2 parágrafos: divida em partes ou
  converta em bullets antes de enviar.

Verificação: conversa roteirizada com várias decisões pendentes; a
transcrição mostra uma pergunta decisória por rodada; agrupamento só de
perguntas autocontidas e independentes (entendíveis sem as outras, sem
contexto novo), no máximo 4; contexto de pergunta sem abreviação nem
confusão. Caso futuro da suíte de comunicação.

**Item 5 — Uso da tool de pergunta (aprovado).** Destino: skill
`question-orchestration` (acréscimo, seção "Uso da tool de pergunta"):

- Pergunte em texto livre como padrão; a resposta do humano vem como
  veio.
- Use a tool apenas quando: a questão já foi apresentada e entendida na
  conversa, as alternativas são poucas, completas e mutuamente
  exclusivas, e cada uma tem consequência distinta que o humano precisa
  escolher.
- Questão nova ou complexa: apresente em texto primeiro; a tool, se
  couber, vem depois do entendimento confirmado.
- Cada alternativa descreve a consequência real da escolha; nunca opção
  de enchimento.

Verificação: conversa roteirizada; a tool aparece só depois do
contexto apresentado em texto, com entendimento confirmado (resposta do
humano à apresentação) antes da chamada da tool, e apenas para escolhas
fechadas; toda alternativa tem descrição de consequência real. Caso
futuro da suíte de comunicação.

**Item 6 — Contestação de premissa (aprovado).** Destino: skill
`question-orchestration` (acréscimo, seção "Confirmação e continuidade
de decisões"):

- Contestação de premissa ou de parte do que foi explicado: assuma que
  o humano não leu o restante da mensagem original. Corrija o ponto
  contestado, verifique o que dependia da premissa contestada e
  reapresente o conteúdo dependente, ajustado se necessário. Não
  presuma que o restante foi lido ou aceito.

Verificação: conversa roteirizada com contestação de premissa no meio;
a resposta seguinte corrige o ponto, identifica o conteúdo dependente e
o reapresenta ajustado. Caso futuro da suíte de comunicação.

**Item 7 — Plano abstraído e perguntas (aprovado).** Destinos: skill
`question-orchestration` (acréscimos), `smart-planner`, `devflow`,
skills `planning-and-task-breakdown` e `spec-driven-development`,
`docs/workflow-agentes-dev.md` (ajustes de sentido).

Princípio do plano abstraído (skill `question-orchestration`):

- O humano aprova o plano, não o arquivo: aprova o plano que lhe foi
  apresentado na conversa, não o documento físico que o agente edita.
  Cabe ao agente abstrair o plano físico: traduzir o documento em
  conteúdo significativo, apresentado por partes, para aprovação e
  discussão. O arquivo fica como artefato interno, commitado e
  consultável para auditoria.

Regra de perguntas (skill `question-orchestration`):

- Pergunte só o que tem efeito no resultado para o humano: decisão de
  escopo, comportamento ou risco. Detalhe de escrita do plano ou do
  artefato é do agente: resolva dentro do escopo aprovado e registre,
  sem perguntar.

Efeitos nos pontos da pesquisa:

- `smart-planner`: substituir "mostre o diff ao humano" e "mostrar o
  plano completo" por apresentação abstraída na conversa, por partes; o
  diff fica como evidência interna do commit; "cat plans/<arquivo>.md"
  vira nota de auditoria (o arquivo reflete o estado; a conversa carrega
  o contexto).
- `devflow`: "Apresentar plano ao humano para aprovação" com o sentido
  de plano abstraído na conversa, não o arquivo.
- `planning-and-task-breakdown`: checklist "Humano revisou e aprovou o
  plano" com o sentido de plano apresentado na conversa.
- `spec-driven-development`: "The plan must be reviewable: the human
  can read it" muda para apresentação abstraída na conversa; o diagrama
  "Human reviews" por fase mantém o gate, com o sentido de conteúdo
  apresentado.
- `docs/workflow-agentes-dev.md`: "Humano aprova o plano antes da
  construção" mantém o texto, com o sentido corrigido.

Verificação: conversa roteirizada de planejamento; a transcrição não
apresenta diff, plano completo ou caminho de arquivo ao humano; toda
aprovação é sobre conteúdo apresentado na conversa; nenhuma pergunta
sobre detalhe de escrita do plano. Caso futuro da suíte de comunicação.

**Item 8 — Esquecer o protocolo e resumo não apresentado (aprovado).**
Sintomas já cobertos por outros itens: texto demais, pelo item 3
(checagem pré-envio); resumo com informação não apresentada, pelo item
3 (resposta se sustenta sozinha) e item 7 (humano só conhece o que foi
apresentado na conversa). Peça nova aprovada: âncora de recarga.

Destino: `AGENTS.base.md`, seção Compactação de contexto (acréscimo):

- Após compactação de contexto, antes de prosseguir a tarefa em
  andamento, recarregue as skills cujo conteúdo sustenta essa tarefa. O
  mesmo vale ao perceber que instruções de uma skill já adotada deixaram
  de ser seguidas.
- Compactação de contexto ou desvio do protocolo de perguntas (volume,
  ritmo, uso da tool): recarregue a skill `question-orchestration`
  antes da próxima resposta ao humano. A recarga vale para quem conduz
  conversa de decisão com o humano usando a skill (`smart-planner`,
  `devflow`, `analista` em entrevista direta); demais agentes de domínio
  não recarregam o protocolo e seguem as regras
  gerais de comunicação do arquivo global, recarregado a cada sessão.

Verificação: conversa roteirizada longa com compactação no meio; após a
compactação, a skill é recarregada e o protocolo (uma pergunta por
rodada, volume por turno) se mantém. Segundo roteiro, com skill de
domínio carregada e compactação no meio: a skill é recarregada antes de
prosseguir a tarefa. Terceiro roteiro, sem compactação: o agente desvia
do protocolo (volume, ritmo, uso da tool) no meio da conversa; a skill é
recarregada antes da resposta seguinte e o protocolo volta a valer.
Casos futuros da suíte de comunicação.

**Item 9 — Dúvida trava ação (aprovado).** Destino: skill
`question-orchestration` (acréscimo, seção "Confirmação e continuidade
de decisões"):

- Dúvida em aberto trava ação: enquanto uma pergunta ao humano estiver
  sem resposta, ou uma contestação estiver em resolução, não execute
  ação dependente (editar, delegar, commitar, avançar de fase). Resolva
  a dúvida primeiro.

Verificação: conversa roteirizada com dúvida levantada no meio; a
transcrição não mostra ação dependente da dúvida pendente entre a
dúvida e a resolução; ação sem relação com a dúvida não é violação.
Caso futuro da suíte de comunicação.

**Item 10 — Cobertura total (aprovado).** Destinos: `smart-planner` e
revisor (`rev`).

`smart-planner`:

- Cobertura total é o padrão: todo o escopo solicitado entra no plano.
  Julgamento próprio de "alteração simples" ou "postergável" não reduz
  escopo; omissão ou postergação de item exige autorização explícita do
  humano.

Revisor (`rev`):

- Verifique cobertura total: o resultado cobre todo o escopo aprovado.
  Item faltante é achado, ainda que julgado simples ou postergável; a
  decisão de aceitar a falta é do humano.

Verificação: conversa roteirizada com escopo de pesos variados; o plano
cobre todos os itens, salvo omissão ou adiamento com autorização
explícita do humano registrada; o relatório do revisor aponta omissões
não autorizadas. Caso futuro da suíte de comunicação.

**Item 11 — Detalhe de implementação não se discute (aprovado).**
Destino: skill `question-orchestration` (acréscimo, junto à regra de
perguntas do item 7):

- Antes de perguntar ou pedir confirmação, classifique a questão: é
  detalhe de implementação ou decisão de resultado? Detalhe de
  implementação não se discute com o humano: decida dentro do escopo
  aprovado, registre no artefato e siga. Só traz ao humano o que muda
  premissa, escopo, comportamento ou risco, ou algo novo não abordado
  no planejamento.

Verificação: conversa roteirizada; nenhuma pergunta sobre detalhe de
implementação; decisões internas registradas no artefato; toda pergunta
trata de premissa, escopo, comportamento, risco ou ponto novo. Caso
futuro da suíte de comunicação.

### Ajustes da revisão independente (discutidos com o humano)

**Achado 1 — Distinção comunicação e entrega (aprovado).** O revisor
apontou que a regra de volume fragmentaria entregas completas. A
decisão do humano define a distinção: comunicação é o que o humano
processa na conversa, por partes; entrega é o que ele consome fora da
conversa, completa. Destino: `AGENTS.base.md`, seção Concisão
(acréscimo):

- Distinga comunicação de entrega: comunicação é o que o humano precisa
  processar na conversa para entender, decidir ou validar; entrega é o
  que ele consome fora da conversa, no formato que pediu.
- Comunicação vai por partes: uma coisa por vez; conteúdo com vários
  itens é anunciado no total e apresentado item por item, ou poucos
  relacionados por vez; nunca tudo de uma vez, salvo pedido.
- Entrega vai completa: densa e no formato pedido, sem as regras de
  ritmo da conversa.
- O limite de ~5 linhas e o ritmo de uma ideia por resposta valem para
  a conversa decisória com o humano e substituem a orientação anterior
  de volume nesse contexto. Entregas solicitadas, relatos entre agentes
  e evidências permanecem completos.
- Numa pergunta, preserve primeiro o contexto e a consequência da
  escolha; distribua por turnos apenas decisões independentes.

Verificação: conversa roteirizada com conteúdo de múltiplos itens a
validar; a transcrição mostra anúncio do total e apresentação por
partes; entrega solicitada vem completa no formato pedido. Caso futuro
da suíte de comunicação.

**Achado 2 — Divergência de perguntas no orquestrador (aprovado).** O
revisor apontou conflito entre as regras novas de perguntas e trechos do
`devflow` (checklist exigindo opções com trade-offs para toda pergunta;
agrupamento de perguntas por serem curtas e relacionadas). Decisão do
humano: remover do `devflow` os trechos que duplicam o protocolo de
perguntas, mantendo só a referência à skill `question-orchestration`
como fonte única (o `devflow` já a declara fonte única; os trechos
duplicavam). Controles operacionais do mediador que não duplicam a skill
(limite de rodadas de reformulação, continuidade da mediação, uso do
prompt-improver para briefing) ficam. O checklist de qualidade de
pergunta perde a exigência universal de opções com trade-offs (contraria
o texto livre como padrão): mantém decisão explícita, contexto e
pergunta autocontida; apresentação, alternativas e agrupamento seguem
exclusivamente a skill. O `dba` fica como está: pergunta só
o que falta no modelo (decisão de resultado) e consulta o registro antes
de perguntar.

Verificação: leitura do `devflow` após o ajuste: nenhum trecho define
regra de pergunta (opções, agrupamento, ritmo); a referência à skill como
fonte única permanece. Caso futuro da suíte de comunicação.

**Achado 3 — Verificações alinhadas às regras (aprovado).** O revisor
apontou três verificações mais duras que as regras, que reprovariam
comportamento correto. Correção: cada verificação espelha a regra com as
mesmas exceções:

- Abreviações: "sem abreviação de palavra, sigla própria ou sigla
  interna sem definição; sigla técnica consagrada é aceita".
- Perguntas: "uma pergunta decisória por rodada; agrupamento só de
  perguntas triviais e independentes, cada uma entendível sem as outras".
- Dúvida trava ação: "nenhuma ação dependente da dúvida pendente entre a
  dúvida e a resolução; ação sem relação com a dúvida não é violação".

Verificação: conferência do texto de verificação de cada regra contra o
texto da regra; nenhuma verificação reprova comportamento que a regra
permite. Caso futuro da suíte de comunicação.

**Achado 4 — Resumo fiel (aprovado).** O revisor apontou lacuna: nenhuma
regra impede o resumo de atribuir ao humano decisão que ele não tomou
(invenção de consenso). O humano confirmou a lacuna e aprovou regra.
Destino: `AGENTS.base.md`, seção Concisão (acréscimo):

- Resumo fiel: só atribua ao humano decisão, fato ou preferência que ele
  escreveu; silêncio ou resposta ambígua não é aprovação. O resumo não
  trata como conhecida informação que não foi apresentada na conversa;
  conteúdo do plano necessário ao fechamento é reapresentado em uma
  linha.

Verificação: conversa roteirizada em que o humano aprova um ponto e fica
em silêncio sobre outro; o resumo seguinte não atribui decisão sobre o
ponto em silêncio; plano contém ponto nunca apresentado na conversa e o
resumo não o cita como conhecido (ou o reapresenta em uma linha). Caso
futuro da suíte de comunicação.

**Achado 5 — Cobertura de casos por regra (aprovado).** O revisor apontou
que "caso com qualquer agente" não comprova alcance e que os revisores
ficam sem caso. Decisão do humano: regra genérica de comunicação e
protocolo de perguntas são validados com um agente só (a regra mora em
arquivo global; um caso garante); regra específica de agente é validada
com o agente afetado. Ajuste na Task 3: casos de comunicação e do
protocolo de perguntas com um agente; casos de regras específicas com
cada agente afetado (`smart-planner`, `devflow`, `rev`).

Verificação: a seção de casos define, para cada regra, o agente do caso:
regra global, um agente; regra específica, o agente afetado. Caso futuro
da suíte de comunicação.

**Achado 6 — Ciclo de vida do arquivo do plano (aprovado).** O revisor
leu conflito entre a regra do plano abstraído (arquivo commitado e
consultável para auditoria) e o ciclo de vida do plano no workflow de dev
(temporário, excluído no encerramento). Decisão do humano: a regra de
comunicação fica como aprovada, sem acréscimo; o problema é de redação no
workflow e no `devflow`. Ajuste: nos trechos sobre o arquivo do plano em
`docs/workflow-agentes-dev.md` e `devflow`, explicitar o ciclo de vida
(commitado durante o trabalho como ponto de salvamento e consultável
para auditoria; excluído no encerramento com autorização humana), sem
contradizer a regra do plano abstraído.

Verificação: leitura dos trechos ajustados: ciclo de vida explícito e
sem contradição com a regra do plano abstraído. Caso futuro da suíte de
comunicação.

**Achado 7 — Conferência manual na execução (aprovado).** O revisor
apontou dependência de infraestrutura futura (simulação multi-turn) para
a conferência antes/depois. Decisão: a conferência na execução é manual.
Ajuste no protocolo de conferência (ramo do insumo 1):

- A conferência na execução é manual e roda em ambiente de teste
  isolado: pasta temporária com instalação própria do assistente,
  montada a partir de uma versão conhecida do repo (commit anotado). A
  instalação oficial do usuário nunca é alterada; nenhum comando de
  configuração é executado na máquina. Sequência: montar o ambiente
  com a configuração original; conversa "antes" com o agente, em
  sessão limpa, com o roteiro da regra; aplicar a regra nova no
  arquivo específico do teste, dentro do ambiente isolado; conferir
  que a regra está no arquivo final; conversa "depois" com o mesmo
  agente, modelo e roteiro. A única diferença entre as duas conversas
  é a regra testada. A
  evidência é a transcrição das duas conversas, o commit do repo
  usado e o resultado conferido contra os critérios objetivos da
  regra. O mecanismo exato de montar o ambiente isolado é detalhe do
  executor, validado antes do primeiro uso. A suíte automatizada de conversas é
  futura, registrada no insumo de testes
  (`plan/insumo-testes-comportamento-agentes.md`, seção de simulação
  multi-turn), e substituirá a conferência manual quando construída.

Verificação: o protocolo de conferência no insumo distingue conferência
manual (execução) da suíte automatizada (futura, no insumo de testes).
Caso futuro da suíte de comunicação.

**Achado 8 — Compatibilização na aplicação (aprovado).** O revisor apontou
que a consolidação exigia cópia fiel sem etapa de compatibilização; o
executor manteria trechos divergentes. Decisão do humano: a regra nova
vale sobre o trecho antigo; o executor ajusta o trecho conflitante para
seguir a regra nova, sem perguntar; volta ao humano só se o ajuste mudar
comportamento que a regra nova não cobre. Ajuste na Task 1 (e no insumo):

- Ao gravar cada regra no arquivo de destino, confira o arquivo por
  trechos que conflitam com a regra nova e ajuste-os para segui-la: a
  regra nova vale sobre o trecho antigo. Volte ao humano só se o ajuste
  mudar comportamento que a regra nova não cobre.

Verificação: ao aplicar cada regra, o executor confere o arquivo de
destino e ajusta trechos conflitantes; nenhum trecho contradiz a regra
aplicada. Caso futuro da suíte de comunicação.

### Ajustes da segunda rodada de revisão (discutidos com o humano)

**Achado 1 (rodada 2) — Textos de verificação divergentes (aprovado).**
As correções aprovadas na primeira rodada estavam em seção separada
enquanto os textos originais das regras mantinham verificações antigas,
mais duras. Decisão: aplicar as correções direto nos textos de
verificação dos itens 1, 3, 4 e 9, existindo uma única versão; a seção
de ajustes fica como registro do que foi decidido.

**Achado 2 (rodada 2) — Alcance do protocolo de perguntas (rejeitado).**
O revisor sugeriu regra global mandando todo agente carregar a skill de
perguntas ao conversar com o humano. Decisão do humano: rejeitado.
Agentes de domínio tipicamente não falam diretamente com o humano;
passam pelo `devflow`, que media as perguntas. Chamados diretamente,
fazem trabalho técnico e não precisam do protocolo de perguntas. As
regras gerais de comunicação continuam valendo para todos via
`AGENTS.base.md`; o protocolo de perguntas fica para quem conduz
conversa de decisão (`smart-planner` e `devflow`).

**Achado 3 (rodada 2) — Sincronização de agente, workflow e testes
(aprovado).** O revisor apontou que a remoção dos trechos duplicados no
`devflow` quebra referências no workflow (`docs/workflow-agentes-dev.md`)
e nos testes (`tests/agents/`). Instrução ao insumo (e à Task 1):

- Mudança em agente ou workflow sincroniza os três lugares: a definição
  do agente, o workflow em docs/ e os testes em tests/agents/. Ao final,
  a suíte completa do ambiente corrente roda sem deixar teste de fora
  (WSL/Linux: `.venv/bin/pytest -m all`; Windows:
  `.\.venv\Scripts\pytest.exe -m all`).

Verificação: suíte completa do ambiente corrente passa após as mudanças.

**Achado 4 (rodada 2) — Commit do plano pelo orquestrador (aprovado;
revogado na rodada 4).**
O revisor apontou o conflito entre plano commitado durante o trabalho e
a permissão de terminal negada ao `devflow`. Decisão do humano: ajuste
geral — o orquestrador é quem controla o plano e commita os checkpoints
dele. Ajustes:

- `devflow`: permissão de execução liberada para git, restrita ao
  arquivo de planejamento (instrução: terminal apenas para checkpoint do
  plano; mecanismo exato, pattern de permissão ou allow com restrição
  escrita, é detalhe do executor).
- `docs/workflow-agentes-dev.md` e roteamento em `AGENTS.base.md`:
  `eng-software` permanece o único committer de código; o `devflow`
  commita os checkpoints do arquivo de planejamento.
- Princípio geral: quem controla o artefato persistente commita seus
  checkpoints (o `smart-planner` já o pratica com o próprio plano).

Verificação: o `devflow` cria checkpoint do arquivo do plano; a suíte de
consistência (permissões e workflows) passa.

Revogação (rodada 4, decisão do humano): o `devflow` não commita e não
recebe permissão de terminal; o checkpoint do arquivo de planejamento é
delegado a subagente comitador, como no funcionamento atual.
`eng-software` permanece o único committer de código. Sem mudança em
`docs/workflow-agentes-dev.md` nem no roteamento de `AGENTS.base.md`.

**Achado 5 (rodada 2) — Evidência da conferência (aprovado).** O revisor
apontou que as transcrições antes/depois não têm destino nem controle de
agente, modelo e roteiro. Instrução ao insumo (protocolo de conferência):

- Cada conferência registra em arquivo de evidência (em `plan/`,
  artefato auxiliar do workflow): as duas transcrições, antes e depois
  da mudança, com agente, modelo, roteiro usado e data; e o resultado
  por critério da regra (passou ou falhou). O arquivo acompanha o plano
  no encerramento e é excluído junto.

Verificação: cada regra aplicada tem arquivo de evidência com as duas
transcrições e o resultado por critério.

**Achado 6 (rodada 2) — Matriz de casos só com regra de comportamento
(aprovado).** O revisor apontou ambiguidade entre regra comportamental e
instrução de execução na tarefa de casos. Instrução à Task 3 (e à seção
de casos do insumo de testes):

- A seção de casos traz uma matriz explícita: para cada linha, a regra,
  o roteiro do caso e o agente. Só regra de comportamento entra na
  matriz. Instrução de execução (ordem de aplicação, compatibilização,
  conferência antes/depois, evidência, sincronização de testes,
  checkpoint do plano delegado a subagente comitador) não vira caso.

Verificação: a matriz cobre as regras de comportamento, uma a uma;
nenhuma instrução de execução aparece como caso.

### Ajustes da terceira rodada de revisão (discutidos com o humano)

**Achado 1 (rodada 3) — Consolidação com conjunto completo (aprovado).**
As tarefas de consolidar e revisar o insumo cobrem as três seções de
decisões do plano (regras originais, ajustes da primeira rodada e
ajustes da segunda rodada), incluindo sincronização de testes, commit do
plano e evidência da conferência. Aplicado nas Tasks 1 e 2.

**Achado 2 (rodada 3) — Tarefa de casos segue a matriz (aprovado).**
A tarefa de casos passou a exigir a matriz (regra, roteiro, agente) só
com regra de comportamento; instrução de execução não vira caso.
Aplicado na Task 3.

**Achado 3 (rodada 3) — Agente revisor inexistente no repo (aprovado).**
O plano citava o agente "revisor" como destino, mas não existe arquivo
dele em `harness-conf/agents/` (é agente exclusivo do OpenCode, definido
fora do repo, sem arquivo editável por este projeto). Decisão: o destino
da regra de cobertura total é o `rev`; as listas de agentes afetados
perdem o "revisor".

**Achado 4 (rodada 3) — Materialização da configuração na conferência
(aprovado; substituído na rodada 4 pelo ambiente isolado).** O arquivo
de regras do repo (`harness-conf/`) não é o carregado pelo agente: o
adapter materializa a configuração final no destino do harness (ex.:
`~/.config/opencode/AGENTS.md`). Sessão limpa sozinha não garante
configuração nova. Ajuste original no protocolo de conferência: após
aplicar a regra, materializar a configuração (rodar o bootstrap do
repo, que regenera os arquivos do harness) e abrir sessão nova do
agente para a conversa "depois"; a evidência registra a versão testada
(commit da configuração materializada). Na rodada 4, a decisão foi
substituída pelo ambiente de teste isolado: o bootstrap da instalação
oficial deixou de ser executado.

**Achado 5 (rodada 3) — Recarga delimitada (aprovado).** A âncora de
recarga do item 8 (todos recarregam `question-orchestration` após
compactação) conflitava com a rejeição, na segunda rodada, do protocolo
de perguntas para agentes de domínio. Ajuste: a recarga vale para quem
conduz conversa de decisão com o humano (`smart-planner`, `devflow`);
agentes de domínio seguem as regras gerais de comunicação do arquivo
global, recarregado a cada sessão.

**Achado 6 (rodada 3) — Verificação com entendimento confirmado
(aprovado).** A regra do item 5 exige questão "apresentada e entendida"
antes da tool, mas a verificação checava só o contexto apresentado.
Ajuste: a verificação passa a exigir que a transcrição mostre o
entendimento confirmado (resposta do humano à apresentação em texto)
antes da chamada da tool.

**Achado 7 (rodada 3) — Resumo sem informação não apresentada
(aprovado).** A regra do resumo fiel cobria atribuição de decisão não
tomada, mas o sintoma original (resumo que cita como conhecida
informação do plano nunca apresentada na conversa) não tinha teste
direto. Ajuste: a regra do resumo fiel ganha "o resumo não trata como
conhecida informação que não foi apresentada na conversa; conteúdo do
plano necessário ao fechamento é reapresentado em uma linha"; a
verificação ganha o roteiro do ponto nunca apresentado.

### Ajustes da quarta rodada de revisão (discutidos com o humano)

**Achado 1 (rodada 4) — Quatro seções de decisões e precedência
(aprovado).** A correção da rodada 3 citava três seções antes de a
seção da terceira rodada existir; hoje são quatro. Ajuste: as tarefas
de consolidar e revisar citam as quatro seções, com a regra de
precedência ("em caso de conflito, prevalece a decisão posterior"), e a
estrutura do insumo troca "revisores" por `rev`. Aplicado nas Tasks 1
e 2.

**Achado 2 (rodada 4) — Escopo das regras de volume (aprovado).** As
regras de volume ("uma ideia central por resposta", ~5 linhas) valiam
para qualquer comunicação e fragmentariam relatos entre agentes,
evidências e o contexto necessário à decisão; conviviam em ambiguidade
com a orientação atual de 20-30 linhas do arquivo global. Ajuste na
regra da distinção comunicação/entrega: o limite e o ritmo valem para a
conversa decisória com o humano e substituem a orientação anterior de
volume nesse contexto; entregas, relatos entre agentes e evidências
permanecem completos; numa pergunta, contexto e consequência vêm antes
da divisão por turnos de decisões independentes.

**Achado 3 (rodada 4) — Recarga estendida ao `analista` (aprovado).**
A delimitação por enumeração fechada (`smart-planner`, `devflow`)
excluiu o `analista`, que conduz entrevista direta de escopo com o
humano usando `question-orchestration`. Ajuste no item 8: a recarga
vale para quem conduz conversa de decisão com o humano usando a skill
(`smart-planner`, `devflow`, `analista` em entrevista direta); demais
agentes de domínio não recarregam o protocolo.

**Decisão nova (rodada 4) — Recarga geral de skills após compactação
(aprovada).** Levantada pelo humano ao discutir a recarga: a compactação
apaga do histórico o conteúdo de qualquer skill carregada (o agente
perde as instruções e a memória de tê-las carregado; só a lista de
skills e as regras globais permanecem no prompt). Regra nova no item 8,
arquivo global: após compactação, antes de prosseguir a tarefa em
andamento, recarregar as skills cujo conteúdo sustenta a tarefa; o
mesmo vale ao perceber que instruções de skill já adotada deixaram de
ser seguidas. Vale para qualquer agente; verificação própria com skill
de domínio.

**Achado 4 (rodada 4) — Checklist do `devflow` sem exigência universal
de opções (aprovado).** O checklist de qualidade de pergunta,
preservado na primeira rodada como controle operacional, exige opções
com trade-offs para toda pergunta, contrariando o texto livre como
padrão. Ajuste: o checklist mantém decisão explícita, contexto e
pergunta autocontida (e o limite de reformulações/continuidade), mas
perde a exigência universal de opções; apresentação, alternativas e
agrupamento seguem exclusivamente a skill. Nota: a sugestão de limitar
"confirmar cada ramo independente" às decisões que mudam o resultado já
está coberta pelas regras dos itens 7 e 11 (perguntar só o que afeta o
resultado; detalhe de implementação não se discute); sem regra nova.

**Achado 5 (rodada 4) — Verificações alinhadas às exceções das regras
(aprovado).** Duas verificações mais duras que as regras: a do item 4
exigia perguntas "triviais" para agrupar (a regra permite autocontidas
e independentes); a do item 10 exigia cobertura sem exceção (a regra
permite omissão ou adiamento autorizado). Ajuste: verificação do item 4
aceita agrupamento de perguntas autocontidas e independentes, no máximo
4; verificação do item 10 aceita omissão ou adiamento com autorização
explícita do humano registrada, e o revisor aponta omissões não
autorizadas.

**Achado 6 (rodada 4) — Verificação do gatilho de desvio (aprovado).**
A regra de recarga tem dois gatilhos (compactação e desvio observado do
protocolo), mas a verificação só cobria compactação. Ajuste: terceiro
roteiro na verificação do item 8, sem compactação: o agente desvia do
protocolo no meio da conversa; a skill é recarregada antes da resposta
seguinte e o protocolo volta a valer.

**Decisão nova (rodada 4) — Teste da reapresentação (aprovada).**
Levantada pelo humano ao observar que a primeira apresentação de um
ponto costuma sair pior que a reapresentação pedida após um "não
entendi": na primeira, o agente escreve para quem acompanha o
racicínio interno (vocabulário do revisor, referências ao plano,
mecanismo comprimido); só na segunda escreve para o humano sem o plano
na cabeça. Regra nova no item 2, arquivo global: antes de enviar a
apresentação de um ponto, escrever a versão que escreveria após um "não
entendi" e enviar essa (mecanismo concreto antes da referência; exemplo
antes do geral; jargão interno só com tradução imediata). Verificação
própria: ponto técnico complexo apresentado certo de primeira, sem
pedido de reapresentação.

**Decisão nova (rodada 4) — Revogação do commit pelo orquestrador
(aprovada).** Ao discutir o risco de liberação de terminal ampla, o
humano revogou a decisão da segunda rodada: o `devflow` não commita o
plano e não recebe permissão de terminal; o checkpoint do arquivo de
planejamento é delegado a subagente comitador, como no funcionamento
atual. `eng-software` permanece o único committer de código.

**Achado 7 (rodada 4) — Permissão de terminal do `devflow` (resolvido
por reversão).** O revisor apontou o risco de a restrição ao checkpoint
existir só na instrução escrita, com permissão técnica ampla. Com a
revogação acima, o `devflow` mantém o terminal negado e não há
liberação a restringir; o achado fica resolvido sem ajuste adicional.

**Achado 8 (rodada 4) — Identificação da configuração nas conversas
(resolvido por decisão de ambiente isolado).** O revisor apontou que a
conferência não garantia qual configuração o agente lia na conversa
"antes" nem identificava com segurança a versão da configuração
"depois", e que o bootstrap mexeria nos dois harnesses e no ambiente do
usuário. Decisão do humano, em substituição ao bootstrap da instalação
oficial: ambiente de teste isolado (pasta temporária com instalação
própria do assistente, montada de uma versão conhecida do repo; a
instalação oficial nunca é alterada). A versão das duas conversas fica
conhecida por construção; a única diferença entre elas é a regra
testada. Aplicado no protocolo de conferência (achado 7 da primeira
rodada) e na substituição do achado 4 da terceira rodada.

## Task List

### Fase 1: Insumo de revisão e ajuste

- [ ] **Task 1: Consolidar o insumo de revisão e ajuste.**
  - **Description:** criar
    `plan/insumo-revisao-comunicacao-planejamento-agentes.md`,
    consolidando as regras e instruções das quatro seções de decisões
    deste plano ("Regras aprovadas", "Ajustes da revisão independente",
    "Ajustes da segunda rodada de revisão" e "Ajustes da terceira rodada
    de revisão"), prevalecendo a decisão posterior em caso de conflito,
    com texto completo, destino
    (arquivo e seção), protocolo de conferência e instruções de execução
    ao `devflow` (ordem de aplicação, uma regra por vez, conferência
    antes/depois, compatibilização na aplicação, sincronização de
    agente/workflow/testes, checkpoint do plano delegado a subagente
    comitador, evidência
    da conferência). Estrutura do insumo:
    contexto de origem; regras de comunicação (todos os agentes); regras
    de planejamento (`smart-planner`, `devflow`, `rev`); protocolo de
    conferência com evidência; ordem de aplicação; compatibilização na aplicação
    (regra nova vale sobre trecho antigo; conferir arquivo de destino por
    conflitos; voltar ao humano só se o ajuste mudar comportamento não
    coberto); sincronização de agente, workflow e testes; casos de teste
    (referência à seção nova do insumo de testes).
  - **Acceptance criteria:**
    - [ ] Todas as regras e instruções das quatro seções de decisões estão
          no insumo, com texto idêntico ao aprovado e destino por
          arquivo e seção.
    - [ ] Nenhuma regra além das aprovadas; nada inventado.
    - [ ] Protocolo de conferência (com evidência), ordem de aplicação,
          sincronização e checkpoint do plano (delegado a subagente
          comitador) incluídos.
    - [ ] Autocontido: sem citar identificadores, números de item ou
          vocabulário interno deste plano.
  - **Verification:**
    - [ ] Conferência item a item contra as quatro seções de decisões.
    - [ ] Busca por referências internas ao plano (números de item,
          "ramo", "task") no texto do insumo.
  - **Dependencies:** None
  - **Files likely touched:**
    `plan/insumo-revisao-comunicacao-planejamento-agentes.md` (novo)
  - **Estimated scope:** S

- [ ] **Task 2: Revisão independente do insumo.**
  - **Description:** instância independente do revisor verifica o insumo
    contra este plano.
  - **Acceptance criteria:**
    - [ ] Fidelidade: conjunto completo — regras e instruções das quatro
          seções de decisões, idênticas às aprovadas, com a decisão
          posterior prevalecendo em conflito.
    - [ ] Cobertura: os 11 problemas relatados têm regra.
    - [ ] Autocontenção confirmada.
  - **Verification:** relatório de revisão com aprovação ou achados.
  - **Dependencies:** Task 1
  - **Files likely touched:** nenhum (relatório)
  - **Estimated scope:** S

### Checkpoint: Insumo pronto
- [ ] Insumo revisado e aprovado
- [ ] Apresentação das partes ao humano para aprovação

### Fase 2: Casos de teste

- [ ] **Task 3: Seção de casos no insumo de testes.**
  - **Description:** acrescentar a
    `plan/insumo-testes-comportamento-agentes.md` seção com os casos de
    teste de comunicação, após a seção de técnicas futuras (simulação
    multi-turn), sem renumerar seções existentes. Cada regra de
    comportamento vira uma linha da matriz: a regra,     o roteiro do caso e
    o agente. Instrução de execução (ordem de aplicação,
    compatibilização, conferência, evidência, sincronização de testes,
    checkpoint do plano delegado a subagente comitador) não vira caso. Regra global de
    comunicação e protocolo de perguntas: caso com um agente. Regra
    específica de agente: caso com o agente afetado (`smart-planner`,
    `devflow`, `rev`). Reutiliza as técnicas já decididas no
    insumo (execução real, asserção de trajetória, juiz com rubrica,
    consenso).
  - **Acceptance criteria:**
    - [ ] Uma regra de comportamento, uma linha na matriz (regra,
          roteiro, agente); nenhuma instrução de execução vira caso.
    - [ ] Cobertura por regra: regra global de comunicação e protocolo
          de perguntas, caso com um agente; regra específica, caso com o
          agente afetado (`smart-planner`, `devflow`, `rev`).
    - [ ] Separação comunicação/planejamento respeitada.
    - [ ] Seções existentes não renumeradas; decisões existentes não
          alteradas.
  - **Verification:** conferência da seção contra as regras aprovadas;
    diff limitado ao acréscimo.
  - **Dependencies:** Task 1
  - **Files likely touched:** `plan/insumo-testes-comportamento-agentes.md`
  - **Estimated scope:** S

- [ ] **Task 4: Revisão independente final.**
  - **Description:** instância independente nova do revisor verifica o
    conjunto (insumo + seção de casos).
  - **Acceptance criteria:**
    - [ ] Achados da Task 2 resolvidos (se houve).
    - [ ] Seção de casos fiel às regras e às técnicas do insumo.
  - **Verification:** relatório de revisão com aprovação ou achados.
  - **Dependencies:** Task 3
  - **Files likely touched:** nenhum (relatório)
  - **Estimated scope:** S

### Checkpoint: Conjunto completo
- [ ] Insumo e seção de casos revisados
- [ ] Apresentação final ao humano

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Regra redigida sem efeito no comportamento | Alta | Protocolo de conferência antes/depois com mesmo roteiro; não mudou, ajustar redação |
| Executor inventar regra não aprovada | Alta | Revisor confere fidelidade item a item; critério "nenhuma regra além das aprovadas" |
| Sessão paralela na worktree misturando commits | Média | Commits só com o arquivo próprio; conferir stat do commit |
| Insumo de testes com decisões fechadas sendo alterado | Média | Acréscimo de seção sem renumerar; diff limitado ao acréscimo |

## Open Questions

Nenhuma; todos os ramos foram resolvidos com o humano.
