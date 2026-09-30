# Plano — Revisão de Comunicação e Planejamento dos Agentes

## Overview

O humano anotou problemas de comunicação e de planejamento no uso dos
agentes. Este plano percorre os problemas item a item: para cada um,
ajustamos a formulação da regra e conferimos o resultado esperado
(comportamento observável e forma de verificar). As regras aprovadas
são aplicadas diretamente nos arquivos de configuração, validadas regra
a regra e testadas em uso real com o humano. Ao final, o trabalho gera
um insumo para o `devflow` adequar as mudanças ao padrão do repo, em
outra sessão, acionada pelo humano: o `devflow` não participa da
execução deste plano.

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
- Termo técnico em inglês de uso consagrado (config, docs, repo e
  similares) é jargão consagrado: não é abreviação a expandir.
- Sigla interna do projeto ou do plano, e termo de domínio afastado,
  exigem nome por extenso no primeiro uso, em linguagem simples.

Verificação: conversa roteirizada em que o agente explica uma decisão;
a transcrição não pode ter abreviação de palavra, sigla própria ou sigla
interna sem definição; sigla técnica consagrada e jargão consagrado em
inglês (config, docs, repo) são aceitos. Caso futuro da suíte de
comunicação.

**Item 2 — Referências ao plano (aprovado).** Destino: `AGENTS.base.md`,
seção Comunicação, subseção "Conversa sobre plano" (reformulação):

- Plano e artefatos de estado são do agente; o humano não os lê.
- Toda pergunta, decisão ou discussão é autocontida: traga a fase atual,
  o trecho relevante e o escopo da questão, em termos simples.
- Traduza sempre: o humano só conhece os conceitos discutidos com ele.
  Nunca use número, código, sigla ou identificador interno do plano na
  conversa; apresente o conceito, contextualizado. Conceito discutido
  há muito tempo é reapresentado em uma linha antes de novo uso: o
  humano pode não lembrar.
- Apresente por partes: uma etapa ou decisão por vez. Resumo de etapas
  é permitido; ao encerrar, um resumo dirigido do todo, também por
  partes.
- Antes de enviar a apresentação de um ponto ao humano, aplique o teste
  da reapresentação: escreva a versão que você escreveria se ele
  tivesse acabado de responder "não entendi", e envie essa. Nela, o
  mecanismo concreto vem antes da referência ao plano; jargão interno
  não aparece: todo conceito é apresentado por extenso, na conversa. O
  exemplo é ferramenta condicional: um exemplo curto quando o ponto for
  abstrato ou complexo e o exemplo ajudar o humano a decidir.

Verificação: conversa roteirizada com várias decisões em jogo; a
transcrição não contém número, código ou identificador interno do
plano: todo conceito chega traduzido e conceito antigo é reapresentado
ao ser retomado; na apresentação de ponto técnico complexo, a primeira
versão já traz mecanismo concreto, sem jargão interno, e, quando o
ponto for abstrato ou complexo, exemplo curto que ajuda a decidir; o
humano não precisa pedir reapresentação. Caso futuro da suíte de
comunicação.

**Item 3 — Volume na comunicação (aprovado).** Destino: `AGENTS.base.md`,
seção Comunicação, seção Concisão (acréscimo operacional):

- Uma decisão dependente por resposta. Duas ou mais decisões
  dependentes? Separe e apresente uma por turno. Exceção: até quatro
  perguntas autocontidas e independentes podem ser agrupadas em uma
  mensagem (regra de perguntas múltiplas); pergunta que exija premissa
  extensa sai do grupo e vai sozinha.
- Sem limite fixo de linhas: a resposta inclui o contexto e a
  consequência necessários à decisão em andamento.
- Explicação longa vira blocos progressivos: apresente um bloco por
  vez. O retorno do humano orienta: seguindo o fio (responde, concorda,
  continua), bloco entendido, avance para o próximo; dúvida ou
  reclamação num bloco, resolva aquele bloco antes de avançar. Blocos
  já entendidos não são repetidos.
- Antes de enviar, confira: a resposta tem uma única ação ou decisão?
  Se não, corte o excedente e guarde para o turno seguinte.
- Ao sinal de confusão, responda primeiro à dúvida concreta:
  reexplique só o ponto afetado, sem repetir blocos já entendidos.
  Inclua a premissa ou o detalhe que faltou quando necessário, mesmo
  que a resposta não fique menor.
- Retomada do ponto anterior só ao mudar de assunto, após intervalo
  longo, ou ao sinal de confusão; não em toda mensagem.
- Responda integralmente ao que foi perguntado.

Verificação: conversa roteirizada; nenhuma resposta concentra mais de
uma decisão dependente por turno; agrupamento de até quatro perguntas
autocontidas e independentes não é violação; pergunta de premissa
extensa não entra em grupo; explicação longa aparece
em blocos apresentados um por vez; bloco com dúvida ou reclamação é
resolvido antes de avançar; blocos entendidos não são repetidos;
retomada apenas em mudança de assunto, intervalo ou confusão; resposta
a reclamação de confusão foca o ponto afetado, sem repetir blocos
entendidos, e inclui premissa faltante quando é o caso; entrega
solicitada vem completa e não conta como violação do volume. Caso
futuro da suíte de comunicação.

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
- Sem limite fixo de linhas: inclua o contexto e a consequência
  necessários à decisão em andamento; explicação longa vira blocos
  progressivos (regra do item 3) ou bullets.

Verificação: conversa roteirizada com várias decisões pendentes; a
transcrição mostra uma decisão dependente por rodada; até quatro
perguntas autocontidas e independentes (entendíveis sem as outras, sem
contexto novo) podem ser agrupadas; contexto de pergunta sem abreviação
nem confusão. Caso futuro da suíte de comunicação.

**Item 5 — Uso da tool de pergunta (aprovado; simplificado na rodada
5).** Destino: skill `question-orchestration` (acréscimo, seção "Uso da
tool de pergunta"):

- Pergunte em texto livre como padrão; a resposta do humano vem como
  veio.
- A tool é exceção para casos muito simples: decisão clara e
  alternativas enumeráveis e determinísticas (poucas, completas,
  mutuamente exclusivas).
- Questão nova ou complexa: texto, nunca tool.
- Cada alternativa descreve a consequência real da escolha; nunca opção
  de enchimento.

Verificação: conversa roteirizada; a tool aparece apenas para decisões
claras com alternativas enumeráveis e determinísticas; questão nova ou
complexa vem em texto; toda alternativa tem descrição de consequência
real. Caso futuro da suíte de comunicação.

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
- Recomende uma opção quando houver contexto suficiente para comparar
  consequências. Em pergunta de descoberta, peça o contexto sem
  antecipar uma escolha.

Fechamento do plano (skill `question-orchestration`):

- Ao fechar o plano, apresente uma conferência final resumida: escopo
  coberto (tópicos curtos), o que ficou de fora (só com autorização
  registrada) e os riscos que poderiam mudar a escolha. Peça a
  aprovação em seguida. Aprofunde um tópico somente se o humano pedir.
  Nada é aprovado sem ter sido apresentado antes; o resumo não
  substitui a apresentação.

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
sobre detalhe de escrita do plano; recomendação justificada presente
nas perguntas de decisão e ausente apenas nas de descoberta; no
fechamento, a conferência final é
resumida (escopo, exclusões autorizadas, riscos), a aprovação vem em
seguida e o aprofundamento de tópico só ocorre a pedido do humano. Caso
futuro da suíte de comunicação.

**Item 8 — Esquecer o protocolo e resumo não apresentado (aprovado).**
Sintomas já cobertos por outros itens: texto demais, pelo item 3
(checagem pré-envio); resumo com informação não apresentada, pelo item
3 (resposta se sustenta sozinha) e item 7 (humano só conhece o que foi
apresentado na conversa). Peça nova aprovada: âncora de recarga.

Destino: `AGENTS.base.md`, seção Compactação de contexto (acréscimo):

- Mantenha registrado no artefato persistente (plano) o estado da
  tarefa: skills em uso e decisões abertas. Após compactação, releia o
  registro e recarregue o que a tarefa precisa: a recarga não depende
  de lembrar o que a compactação apagou.
- Sem artefato persistente, reconstrua as skills pelas instruções do
  próprio agente e pela tarefa; decisão aberta que não puder ser
  reconstruída, consulte o humano antes de ação dependente.
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
recarregada antes da resposta seguinte e o protocolo volta a valer. Em
todos, o registro de estado (skills em uso, decisões abertas) existe no
artefato e permite reconstruir o que recarregar; roteiro adicional com
agente sem artefato persistente: reconstrói as skills pelas próprias
instruções e pela tarefa, e decisão aberta irreconstrutível vira
consulta ao humano antes de ação dependente. Casos futuros da suíte de
comunicação.

**Item 9 — Dúvida trava ação (aprovado).** Destino: skill
`question-orchestration` (acréscimo, seção "Confirmação e continuidade
de decisões"):

- Dúvida em aberto trava ação: enquanto uma pergunta ao humano estiver
  sem resposta, ou uma contestação estiver em resolução, não execute
  ação dependente (editar, delegar, commitar, avançar de fase). Resolva
  a dúvida primeiro.
- Fechamento com pendência: o plano pode ser concluído com pendência
  condicionante desde que a tarefa dependente fique travada como
  bloqueadora e a decisão pendente seja explícita; a aprovação do plano
  não aprova a pendência.

Verificação: conversa roteirizada com dúvida levantada no meio; a
transcrição não mostra ação dependente da dúvida pendente entre a
dúvida e a resolução; ação sem relação com a dúvida não é violação; no
fechamento com pendência, a tarefa dependente aparece travada como
bloqueadora e a decisão pendente explícita. Caso futuro da suíte de
comunicação.

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

**Decisão nova (rodada 4) — Reestruturação do produto do plano
(aprovada).** O humano redirecionou o final do plano: as regras
aprovadas são aplicadas diretamente nos arquivos de configuração
(Fase 1, executor orquestrado daqui com revisão independente); o insumo
ao `devflow` encolhe para a adequação das mudanças ao padrão do
projeto (sincronização de agente/workflow/testes, suíte completa,
formato, Fase 2); e nova Fase 3 de teste prático: um planejamento real
conduzido pelo humano com o agente planejador, tema escolhido na hora,
para exercitar o protocolo de comunicação no uso real. As conferências
rego a regra (ambiente isolado) e o teste prático se complementam: os
dois permanecem. Task List reescrita.

### Ajustes da quinta rodada de revisão (revisão dupla, discutidos com o humano)

**Achado 1 (rodada 5, parte 1) — Tradução sempre, identificador nunca
(aprovado com reforço do humano).** Contradição entre "nunca
referencie identificador" (item 2 original) e "jargão interno só com
tradução imediata" (teste da reapresentação). Decisão do humano, mais
rígida que as duas: sem referência a internalidades do plano em
nenhum caso; o agente traduz sempre; o humano só conhece os conceitos
discutidos com ele e, mesmo assim, se passou muito tempo, pode não
lembrar — conceito antigo é reapresentado em uma linha antes de novo
uso. Aplicado no item 2 e na verificação.

**Achado 2 (rodada 5, parte 1) — Volume e perguntas conciliados
(aprovado).** O item 3 ("uma ideia central por resposta") contradizia o
item 4 (agrupamento de até quatro perguntas); a verificação do item 4
também se contradizia na mesma frase. Ajuste: a regra de volume vira
"uma decisão dependente por resposta", com a exceção explícita nas duas
regras e verificações: até quatro perguntas autocontidas e
independentes podem ser agrupadas.

**Achado 3 (rodada 5, parte 1) — Ordem de aplicação e atribuições
(aprovado).** A Task 2 estava paralela à Task 1, mas as conferências
das regras de planejamento dependem da skill de perguntas já corrigida
(a conversa antes/depois exige que só a regra testada mudou); e a task
atribuía apresentação abstraída ao `rev`. Ajustes: Task 2 depende da
Task 1; cobertura total vai para `smart-planner` e `rev`; apresentação
abstraída para `smart-planner` e `devflow`. Confirmado com o humano o
fluxo geral: validação autônoma regra a regra no ambiente isolado,
adequação ao padrão, e só então uma única sincronização da instalação
oficial com tudo validado, antes do teste prático (passo explícito
acrescentado à Task 6).

**Achado 4 (rodada 5, parte 1) — Execução da adequação (resolvido por
revisão de premissa).** A fase de adequação misturava registro e
execução sem dizer como o `devflow`, sem terminal, executaria a suíte.
A pergunta do humano ("por que o devflow vai fazer alguma coisa agora?
Ele nem está sendo utilizado") expôs a premissa errada de todo o plano.

**Decisão nova (rodada 5) — Premissa de execução sem `devflow`
(aprovada).** O `devflow` não participa da execução deste plano.
Toda a execução é orquestrada pelo planejador com o humano: executor
aplica as regras e valida (ambiente isolado), revisor independente
confere, humano testa em uso real com a instalação oficial
sincronizada. Ao terminar, o trabalho gera um insumo para o `devflow`
adequar o que foi feito ao padrão do repo (sincronização de
agente/workflow/testes, suíte completa, formato), em OUTRA sessão,
acionada pelo humano; nada é executado pelo `devflow` aqui. Task List
reescrita com a premissa; Overview ajustado.

**Achado 5 (rodada 5, parte 1) — Verificação da tool (resolvido por
simplificação do humano).** O revisor apontou que a verificação tratava
qualquer resposta do humano como confirmação de entendimento. Ao
discutir, o humano simplificou a regra inteira, rejeitando o critério de
entendimento: a tool é exceção para casos muito simples — decisão clara
e alternativas enumeráveis e determinísticas; questão nova ou complexa
vem em texto, nunca tool. Sem critério de entendimento na regra ou na
verificação. Revoga o "entendimento confirmado" acrescentado na
terceira rodada.

**Achado 6 (rodada 5, parte 1) — Teste prático inconclusivo
(aprovado).** A etapa do teste prático aceitava qualquer tema; um
planejamento sem nenhuma situação de decisão terminaria "concluído" sem
exercitar o protocolo. Ajuste na Task 5: registrar quais situações do
protocolo ocorreram; sem situação de decisão, o teste é inconclusivo e
repetido com outro tema; a etapa não registra aprovação sem observação.

**Decisão nova (rodada 5) — Blocos progressivos de contexto
(aprovada).** Ao discutir a crítica da parte 2 ao limite fixo de
tamanho (~5 linhas, retomada em toda mensagem), o humano propôs
apresentar o contexto em blocos, um por vez: o retorno do humano
orienta (seguindo o fio, bloco entendido, avance; dúvida ou reclamação
num bloco, resolva-o antes de avançar; blocos entendidos não são
repetidos). Ajustes: sem limite fixo de linhas (a resposta inclui o
contexto e a consequência necessários à decisão em andamento); a
retomada do ponto anterior acontece só ao mudar de assunto, após
intervalo longo, ou ao sinal de confusão; responder integralmente ao
que foi perguntado. Substitui o "divida acima de ~5 linhas ou 2
parágrafos" e a reapresentação compulsória de toda mensagem. Aplicado
nos itens 3 e 4.

**Ajuste de alto impacto (rodada 5, parte 2) — Registro de estado para
a recarga (aprovado).** A regra de recarga dependia de lembrar o que a
compactação apagou. Ajuste no item 8: manter registrado no artefato
persistente (plano) o estado da tarefa (skills em uso, decisões
abertas); após compactação, reler o registro e recarregar o que a
tarefa precisa. Verificação estendida aos três roteiros.

**Ajuste de alto impacto (rodada 5, parte 2) — Conferência final
resumida do plano (aprovado).** Antes da aprovação final, o agente
confere com o humano: escopo coberto, exclusões autorizadas e riscos
que poderiam mudar a escolha. Com a modulação do humano: a conferência
é resumida por padrão (tópicos curtos); aprofunda um tópico somente a
pedido; nada é aprovado sem ter sido apresentado antes. Regra nova no
item 7 (fechamento do plano, skill `question-orchestration`), com
verificação no fechamento da conversa.

### Ajustes da sexta rodada de revisão (revisão dupla)

**Diretiva do humano (rodada 6).** Achados puramente organizacionais do
plano (contagem de seções, estrutura, redação de tarefas e riscos) são
ajustados pelo planejador sem consulta ao humano; o que muda premissa,
definição ou comportamento continua sendo discutido com ele.

**Achados 1, 4 e 5 (rodada 6, parte 1) — Organizacionais (aplicados
direto).** 1: tarefas e risco citavam quatro seções de decisões com o
plano já tendo cinco rodadas; corrigido para "regras originais e as
cinco rodadas de ajustes, prevalecendo a decisão posterior; texto
revogado não é aplicado", e o critério "texto idêntico ao aprovado"
passou a "texto fiel às regras vigentes". 4: risco de regressão agora
declara que a suíte completa roda na sessão posterior de adequação e
exige preservar a configuração anterior antes da sincronização única da
instalação oficial, com restauração em caso de regressão no teste
prático. 5: risco do teste prático sem decisão alinhado ao critério de
teste inconclusivo.

**Achado 2 (rodada 6, parte 1 e reformulação 1 da parte 2) — Resposta à
confusão (aprovado).** A regra anterior (menos linhas que a original,
nunca acrescentar detalhe) podia impedir a correção de premissa e a
resposta integral. Nova regra no item 3: ao sinal de confusão, responda
primeiro à dúvida concreta; reexplique só o ponto afetado, sem repetir
blocos já entendidos; inclua a premissa ou o detalhe que faltou quando
necessário, mesmo que a resposta não fique menor. Verificação
atualizada.

**Achado 3 (rodada 6, parte 1) — Registro de estado sem artefato
(aprovado).** Agentes sem plano/artefato próprio ficavam sem caminho
para a recarga. Novo bullet no item 8: sem artefato persistente,
reconstrua as skills pelas instruções do próprio agente e pela tarefa;
decisão aberta que não puder ser reconstruída, consulte o humano antes
de ação dependente. Verificação estendida com roteiro adicional.

**Reformulação 2 (rodada 6, parte 2) — Exemplo no teste da
reapresentação (aprovado).** "Exemplo antes do geral" virou obrigação
de exemplo sempre, texto extra em ponto simples. Ajuste no item 2: o
exemplo é ferramenta condicional; exemplo curto quando o ponto for
abstrato ou complexo e o exemplo ajudar o humano a decidir. Verificação
atualizada.

**Reformulação 3 (rodada 6, parte 2) — Recomendação em toda pergunta
(aprovado).** Recomendar antes de conhecer o contexto, em pergunta de
descoberta, induz a resposta e gera correção depois. Novo bullet na
regra de perguntas do item 7: recomende uma opção quando houver
contexto suficiente para comparar consequências; em pergunta de
descoberta, peça o contexto sem antecipar uma escolha. Verificação
atualizada.

**Ajuste de alto impacto (rodada 6, parte 2) — Agrupamento e premissa
extensa (aprovado).** A maior parte da sugestão já estava coberta pela
regra de agrupamento aprovada na rodada 5. Refinamento aprovado no item
3: pergunta que exija premissa extensa sai do grupo e vai sozinha,
mesmo sendo independente. Verificação atualizada.

## Task List

**Modelos registrados para a execução (decisão do humano):** executor
`zai-coding-plan/glm-5.3-flash` (instâncias do `eng-software`); revisor
`opencode/glm-5.3` (instâncias do `rev`). Reutilizar em novas
instâncias até o humano alterá-las.

**Diretiva de eficiência do executor (decisão do humano):** as
instâncias executoras agrupam chamadas de ferramenta independentes numa
mesma resposta e consolidam verificações num único comando sempre que
possível, evitando requisições repetidas e gasto desnecessário de
tokens.

**Piloto da conferência antes/depois (Task 1, etapa 2a) — mecanismo
validado.** Ambiente isolado com HOME/XDG próprios em
`/tmp/opencode/conf-validacao/`; corridas com `opencode run --pure
--format json`, mesmo modelo nas duas (`zai-coding-plan/glm-5.3-flash`),
roteiro idêntico; estado ANTES do commit 31dddfe, regra aplicada via
hunk isolado de c4e90cd; `AGENTS.md` do ambiente regenerado após edição.
Regra piloto (item 2, identificador interno): ANTES violou, DEPOIS
traduziu por extenso. Instalação oficial intacta (checksum). Custo:
1-2 min por regra. Decisão do planejador: o plano do repo permanece
acessível no checkout do ambiente (cenário realista; condição comum às
duas corridas). Transcrições em `transcripts/antes.md` e `depois.md` do
ambiente.

**Conferências antes/depois (Task 1, etapa 2b) — resultados.** 22
corridas, ~38 min de modelo. Efeito comprovado: identificador interno
(piloto), volume/resposta à confusão, blocos adaptativos, contestação
de premissa, recomendação com contexto, fechamento com conferência.
Sem contraste (já obedecia): distinção comunicação/entrega e resumo
fiel. Não conferíveis no mecanismo (`--pure`): recarga pós-compactação
(item 8) e dimensão tool da pergunta (item 5); validação fica para o
teste prático (Fase 2). Sem efeito detectável: regra de abreviações
(item 1). Evidências em `/tmp/opencode/conf-validacao/` (transcripts,
relatorio-etapa2b.md, commits do ambiente 3c08c4e..aba1d26). Achados
pendentes de decisão humana: item 1 × jargão consagrado; fala
intermediária em inglês; zona cinzenta fechamento × dúvida travada.

**Decisão do humano (execução, achado 1): item 1 × jargão consagrado.**
Aceito o empate: "config", "docs", "repo" e similares são jargão
consagrado, não abreviação a expandir. Item 1 do plano atualizado com o
bullet do jargão consagrado em inglês e verificação ajustada. Aplicado
em `AGENTS.base.md` no commit `0e07247` (junto com o bullet de pendência
condicionante na skill `question-orchestration`).

**Decisão do humano (execução, achado 2): fala intermediária em inglês
nas corridas de conferência.** Ignorar, atribuindo ao modo de execução
headless dos testes (`opencode run --pure`), não às regras nem ao modelo
de interação com o humano. Sem registro no insumo do devflow e sem ação
neste escopo; se reaparecer em conversa interativa real, tratar como
problema novo.

**Decisão do humano (execução, achado 3): fechamento com pendência
condicionante.** Esclarecido no item 9: o plano pode ser concluído com
pendência condicionante desde que a tarefa dependente fique travada
como bloqueadora e a decisão pendente seja explícita; a aprovação do
plano não aprova a pendência. Verificação do item 9 estendida ao
fechamento.

### Fase 1: Aplicação direta das regras

- [x] **Task 1: Aplicar as regras de comunicação.** CONCLUÍDA:
  aplicação no commit `c4e90cd`; conferências antes/depois em ambiente
  isolado (etapas 2a e 2b, evidências em `/tmp/opencode/conf-validacao/`);
  três achados decididos pelo humano (`f9feec0`, `7f6ac87`, `d4f5e44`);
  ajustes pós-decisão aplicados no commit `0e07247`.
  - **Description:** aplicar nos arquivos de configuração as regras de
    comunicação aprovadas nas seções de decisões deste plano (regras
    originais e as cinco rodadas de ajustes; em conflito, prevalece a
    decisão posterior; texto revogado não é aplicado).
    Destinos: `AGENTS.base.md` (itens 1, 2, 3, 8; acréscimos de Concisão
    do item 4; distinção comunicação/entrega com escopo de volume; resumo
    fiel; recarga geral de skills após compactação) e skill
    `question-orchestration` (itens 4, 5, 6, 7, 9, 11). Ao gravar cada
    regra, compatibilizar o arquivo de destino (regra nova vale sobre o
    trecho antigo; voltar ao humano só se o ajuste mudar comportamento
    não coberto). Cada regra ou grupo pequeno é validado pela
    conferência antes/depois em ambiente isolado, com evidência
    (transcrições, commit do repo do ambiente, resultado por critério).
  - **Acceptance criteria:**
    - [x] Regras aplicadas com texto fiel às regras vigentes
          (precedência da decisão posterior), no destino correto.
    - [x] Nenhum trecho dos arquivos de destino contradiz a regra
          aplicada.
    - [x] Cada regra ou grupo com evidência de conferência completa.
  - **Verification:** revisão independente (Task 3) contra as regras
    originais e as cinco rodadas de ajustes; evidências das
    conferências.
  - **Dependencies:** None
  - **Files likely touched:** `harness-conf/AGENTS.base.md`,
    `harness-conf/skills/question-orchestration/SKILL.md`
  - **Estimated scope:** M

- [x] **Task 2: Aplicar as regras de planejamento.** CONCLUÍDA:
  aplicação no commit `34d6b83` (6 arquivos, +88/-36); conferências
  antes/depois em ambiente isolado (montagem ANTES `3b55c0a` = comunicação
  `0e07247` + planejamento `31dddfe`; DEPOIS `e889854` = planejamento
  `34d6b83`). Resultados: cobertura total do planejador com contraste
  forte (viola → obedece); plano abstraído do orquestrador com contraste
  parcial; cobertura do revisor sem contraste (já apontava omissão);
  pergunta em texto livre sem contraste; apresentação abstraída do
  planejador INCONCLUSIVA no mecanismo (roteiro não provocou o momento
  da apresentação após 2 tentativas) — validação comportamental fica
  para o teste prático (Fase 2), cenário real do comportamento. Efeito
  colateral observado apenas no ambiente de conferência: `bash: deny`
  no frontmatter do orquestrador provoca erro 403 determinístico do
  provider no modo `opencode run` (contorno `bash: allow` local);
  registrado como observação para o insumo do `devflow` (Fase 3), sem
  ação neste escopo. Evidências em
  `/tmp/opencode/conf-validacao/relatorio-task2-conferencias.md`.
  - **Description:** aplicar as regras de planejamento aprovadas nos
    agentes e workflows: `smart-planner` (cobertura total; apresentação
    abstraída), `rev` (cobertura total), `devflow` (remoção da
    duplicação do protocolo de perguntas, sem exigência universal de
    opções; ciclo de vida do arquivo do plano; plano abstraído na
    apresentação;
    sem permissão de terminal e sem commit, revogado na rodada 4),
    skills `planning-and-task-breakdown` e `spec-driven-development`
    (sentido de "humano aprovou o plano") e
    `docs/workflow-agentes-dev.md` (sentido corrigido; ciclo de vida do
    plano). Mesma compatibilização e conferência antes/depois (ambiente
    isolado) para as regras de comportamento.
  - **Acceptance criteria:**
    - [x] Regras aplicadas com texto fiel às regras vigentes
          (precedência da decisão posterior), nos destinos corretos.
    - [x] Nenhum trecho contradiz regra aplicada; `devflow` sem
          permissão de terminal (confirmado: `bash: deny`, sem commit
          próprio; `eng-software` único committer).
    - [x] Evidências de conferência para as regras de comportamento.
  - **Verification:** revisão independente (Task 3); evidências.
  - **Dependencies:** Task 1 (comunicação primeiro: as conferências
    desta tarefa dependem da skill de perguntas já corrigida)
  - **Files likely touched:** `harness-conf/agents/smart-planner.md`,
    `harness-conf/agents/devflow.md`, `harness-conf/agents/rev.md`,
    `harness-conf/skills/planning-and-task-breakdown/SKILL.md`,
    `harness-conf/skills/spec-driven-development/SKILL.md`,
    `docs/workflow-agentes-dev.md`
  - **Estimated scope:** M

- [x] **Task 3: Revisão independente da aplicação.** CONCLUÍDA:
  instância nova do revisor (opencode/glm-5.3) auditou os commits
  `c4e90cd`, `0e07247`, `34d6b83` e `f9c61d6` contra as regras vigentes
  (originais + cinco rodadas, precedência da posterior). Veredito:
  **APROVADO COM RESSALVAS**. Seis eixos OK (fidelidade, revogação,
  compatibilização, matriz do insumo, evidências, não-regressão).
  4 achados, nenhum bloqueante:
  1. (média) `smart-planner.md` mantém exemplo residual com
     identificador interno do plano ("adicionei D2"), em conflito com a
     proibição total do item 2; o revisor classifica como correção
     mecânica de decisão já aprovada (compatibilização de trechos
     conflitantes, rodada 1).
  2. (baixa) description da skill `question-orchestration` resume
     "blocos adaptativos (até 4 perguntas por rodada)" sem capturar o
     padrão novo "uma pergunta por rodada"; opcional.
  3. (baixa) `devflow.md` usa critério "decisão não-trivial/trivial" no
     contrato com agentes spawnados, divergente do critério vigente da
     skill (sobe ao humano o que muda premissa, escopo, comportamento ou
     risco); zona cinzenta, opcional.
  4. (baixa) bullet de recomendação na skill fundiu texto novo com
     antigo; semântica preservada, localização diverge do aprovado;
     opcional.
  Decisões do humano sobre os achados:
  - Achado 1: APLICAR correção via executor (reformular o exemplo de
    smart-planner.md sem identificador interno do plano).
  - Achado 2: APLICAR ajuste na description da skill
    `question-orchestration` (registrar "uma pergunta por rodada como
    padrão" junto do teto de 4 no agrupamento excepcional), na mesma
    rodada do executor do achado 1.
  - Achado 3: APLICAR alinhamento do critério de escalonamento em
    `devflow.md` (substituir "decisão trivial/não-trivial" pelo critério
    objetivo: sobe ao humano o que muda premissa, escopo, comportamento
    ou risco), na mesma rodada do executor.
  - **Description:** instância independente do revisor confere a
    aplicação: fidelidade às regras vigentes (regras originais e as
    cinco rodadas de ajustes, com precedência da posterior),
    compatibilização dos arquivos de destino e evidências das
    conferências. Relatório e veredito registrados no arquivo deste
    plano.
  - **Acceptance criteria:**
    - [x] Fidelidade: aplicado = regras vigentes (precedência da
          decisão posterior; texto revogado não aplicado).
    - [x] Evidências de conferência completas.
  - **Verification:** relatório com aprovação ou achados.
  - **Dependencies:** Task 1, Task 2
  - **Files likely touched:** nenhum (relatório no plano)
  - **Estimated scope:** S

- [x] **Task 4: Seção de casos no insumo de testes.** CONCLUÍDA:
  seção "14. Casos de teste das regras de comunicação e planejamento"
  em `plan/insumo-testes-comportamento-agentes.md`, inserida após a
  seção de técnicas futuras sem renumerar as existentes (numeração 9-13
  mantida); matriz com 16 linhas (11 regras globais + 5 específicas de
  agente); diff limitado ao acréscimo (33 inserções, 0 remoções).
  Commit `f9c61d6`.
  - **Description:** acrescentar a
    `plan/insumo-testes-comportamento-agentes.md` seção com os casos de
    teste de comunicação, após a seção de técnicas futuras (simulação
    multi-turn), sem renumerar seções existentes. Cada regra de
    comportamento vira uma linha da matriz: a regra, o roteiro do caso e
    o agente. Instrução de execução (ordem de aplicação,
    compatibilização, conferência, evidência) não vira caso.
    Regra global de comunicação e protocolo de perguntas: caso com um
    agente. Regra específica de agente: caso com o agente afetado
    (`smart-planner`, `devflow`, `rev`). Reutiliza as técnicas já
    decididas no insumo (execução real, asserção de trajetória, juiz com
    rubrica, consenso).
  - **Acceptance criteria:**
    - [x] Uma regra de comportamento, uma linha na matriz (regra,
          roteiro, agente); nenhuma instrução de execução vira caso.
    - [x] Cobertura por regra: regra global de comunicação e protocolo
          de perguntas, caso com um agente; regra específica, caso com o
          agente afetado (`smart-planner`, `devflow`, `rev`).
    - [x] Separação comunicação/planejamento respeitada.
    - [x] Seções existentes não renumeradas; decisões existentes não
          alteradas.
  - **Verification:** conferência da seção contra as regras aprovadas;
    diff limitado ao acréscimo.
  - **Dependencies:** Task 1
  - **Files likely touched:** `plan/insumo-testes-comportamento-agentes.md`
  - **Estimated scope:** S

### Checkpoint: Aplicação revisada
- [ ] Aplicação conferida pelo revisor e aprovada pelo humano

### Fase 2: Teste prático em uso real

- [ ] **Task 5: Sincronizar instalação oficial e testar em uso real.**
  - **Description:** após a aplicação revisada, sincronizar a
    instalação oficial do humano com tudo o que foi validado (as
    mudanças chegam juntas, uma única sincronização) e conferir que a
    cópia que o assistente lê contém as regras novas. Então o humano
    conduz, em sessão nova, um
    planejamento real com o agente planejador (`smart-planner`), tema
    escolhido pelo humano na hora, para exercitar o protocolo de
    comunicação no uso real (complemento das conferências regra a regra,
    não substituição). Registrar quais situações do protocolo ocorreram
    (decisões pedidas, dúvidas, contestações, resumos). Se nenhuma
    situação de decisão aparecer, o teste é inconclusivo: repetir com
    outro tema; a etapa não registra aprovação sem ter observado o
    protocolo em ação. Ao fim, registro curto: o que fluiu, o que
    confundiu, ajustes de regra necessários (que voltam ao ciclo de
    ajuste) e percepção do humano.
  - **Acceptance criteria:**
    - [ ] Instalação oficial sincronizada antes do teste; a conversa
          roda com as regras novas.
    - [ ] Planejamento conduzido com o protocolo novo.
    - [ ] Situações do protocolo registradas; sem situação de decisão,
          teste marcado inconclusivo e repetido.
    - [ ] Percepção do humano registrada (o que fluiu, o que confundiu).
    - [ ] Desvios encontrados registrados como ajuste de regra ou
          observação.
  - **Verification:** transcrição e registro do resultado no plano.
  - **Dependencies:** Task 3, Task 4
  - **Files likely touched:** nenhum (registro no plano)
  - **Estimated scope:** S

### Checkpoint: Protocolo validado no uso real
- [ ] Humano valida o protocolo no uso real

### Fase 3: Insumo para o `devflow`

- [ ] **Task 6: Gerar insumo de adequação ao padrão do repo.**
  - **Description:** ao terminar o trabalho (aplicação, revisão e teste
    prático), registrar
    `plan/insumo-adequacao-padrao-comunicacao.md` para o `devflow`
    adequar o que foi feito ao padrão do repo, em outra sessão,
    acionada pelo humano. Conteúdo: o que mudou (arquivos e regras
    aplicadas); a adequação necessária — sincronização dos três lugares
    (definição do agente, workflow em docs/, testes em tests/agents/),
    execução da suíte completa do ambiente corrente sem deixar teste de
    fora (WSL/Linux: `.venv/bin/pytest -m all`; Windows:
    `.\.venv\Scripts\pytest.exe -m all`), ajustes de formato e
    consistência. Nada é executado pelo `devflow` nesta sessão; o
    insumo é o entregável final deste trabalho, e o `devflow` o executa
    com sua delegação própria (checkpoint delegado a subagente
    comitador).
  - **Acceptance criteria:**
    - [ ] Insumo autocontido: o `devflow` executa a adequação sem
          contexto desta sessão.
    - [ ] Lista completa de mudanças e da sincronização necessária.
    - [ ] Sem execução de adequação nesta sessão.
  - **Verification:** leitura do insumo contra as mudanças aplicadas.
  - **Dependencies:** Task 5
  - **Files likely touched:** `plan/insumo-adequacao-padrao-comunicacao.md`
    (novo)
  - **Estimated scope:** S

### Checkpoint: Insumo pronto
- [ ] Insumo registrado para o humano acionar o `devflow` em outra
      sessão

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Regra redigida sem efeito no comportamento | Alta | Protocolo de conferência antes/depois com mesmo roteiro em ambiente isolado; não mudou, ajustar redação |
| Executor aplicar regra divergente do aprovado | Alta | Revisão independente da aplicação (fidelidade às regras vigentes: regras originais e cinco rodadas, precedência da posterior); conferência item a item |
| Regressão em testes de agentes/workflows | Alta | Revisar os asserts existentes ao sincronizar os três lugares; suíte completa na sessão posterior de adequação; antes da sincronização única da instalação oficial, preservar a configuração anterior para reversão; regressão no teste prático: restaurar e registrar impedimento |
| Ambiente isolado não reproduz a instalação oficial | Média | Validar o mecanismo antes do primeiro uso; conferir que o agente lê as regras do ambiente |
| Teste prático sem tema definido | Baixa | Tema sem situação de decisão: registrar teste inconclusivo e repetir com outro tema; não declarar o protocolo validado |
| Sessão paralela na worktree misturando commits | Média | Commits só com o arquivo próprio; conferir stat do commit |
| Insumo de testes com decisões fechadas sendo alterado | Média | Acréscimo de seção sem renumerar; diff limitado ao acréscimo |

## Open Questions

Nenhuma; todos os ramos foram resolvidos com o humano.
