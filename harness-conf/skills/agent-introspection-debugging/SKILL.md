---
name: agent-introspection-debugging
description: >
  Use quando o próprio agente estiver falhando de forma repetida: chamadas
  de ferramenta repetidas sem progresso, tentativas que não avançam,
  consumo de tokens sem resultado, raciocínio degradado pelo crescimento do
  contexto, ou estado do ambiente divergente do esperado. Protocolo de
  autodiagnóstico em quatro fases: capturar a falha, classificar o padrão,
  aplicar recuperação contida e reportar. Triggers: "agente repetindo",
  "agente em loop", "agente travado", "sem progresso", "loop de ferramenta",
  "mesma chamada", "varredura às cegas", "queimando tokens",
  "consumindo tokens sem progresso", "limite de chamadas",
  "looping on the same tools", "repeated retries", "same tool call",
  "agent stuck", "runaway agent", "max tool calls", "context degraded".
---

# Autodiagnóstico do agente

Use esta skill quando a execução do próprio agente estiver falhando de forma
repetida: chamadas de ferramenta em loop, tentativas sem avanço, consumo de
tokens sem progresso ou desvio da tarefa original.

É um workflow, não um runtime: a skill ensina o agente a se diagnosticar de
forma sistemática antes de escalar para o humano.

## Quando ativar

- Falha por limite máximo de chamadas de ferramenta
- Tentativas repetidas sem progresso novo
- Crescimento do contexto degradando a qualidade do raciocínio
- Estado do ambiente divergente do esperado (arquivo, branch, serviço, caminho)
- Falha de ferramenta provavelmente recuperável com diagnóstico e ação menor

## Escopo

Ativar para:

- capturar o estado da falha antes de tentar de novo às cegas;
- diagnosticar padrões de falha típicos de agente;
- aplicar recuperação contida (ação mínima que muda a superfície do
  diagnóstico);
- produzir relatório legível para o próximo agente ou para o humano.

Não usar como fonte principal para:

- verificação de mudança de código: use a suíte de testes do repo;
- debug de bug no código do projeto: é debugging convencional, não
  autodiagnóstico;
- promessa de auto-recuperação que o harness não executa.

## Loop de quatro fases

### Fase 1: captura da falha

Antes de tentar se recuperar, registre a falha com precisão.

Capture:

- tipo de erro, mensagem e stack trace, quando houver;
- sequência das últimas chamadas de ferramenta que importam;
- o que o agente estava tentando fazer;
- pressão de contexto: prompts repetidos, logs colados enormes, planos
  duplicados;
- premissas de ambiente a verificar: cwd, branch, estado de serviço,
  arquivos esperados.

Modelo mínimo:

```markdown
## Captura da falha
- Sessão / tarefa:
- Objetivo em andamento:
- Erro:
- Último passo bem-sucedido:
- Última ferramenta / comando que falhou:
- Padrão repetido observado:
- Premissas de ambiente a verificar:
```

### Fase 2: diagnóstico por padrão

Antes de mudar qualquer coisa, encaixe a falha num padrão conhecido.

| Padrão | Causa provável | Verificação |
| --- | --- | --- |
| Máximo de chamadas / mesmo comando repetido | loop sem saída | inspecione as últimas N chamadas por repetição |
| Mesmo arquivo lido em faixas diferentes | varredura às cegas | localize com grep ou índice antes de ler de novo |
| Contexto estourado / raciocínio degradado | notas e logs sem limite | busque duplicação no contexto recente |
| ECONNREFUSED / timeout | serviço fora ou porta errada | confira saúde, URL e porta do serviço |
| 429 / cota esgotada | tempestade de retry sem backoff | conte chamadas repetidas e o espaçamento |
| Arquivo sumiu depois de escrever / diff velho | race, cwd ou branch trocado | reverifique caminho, cwd e git status |
| Teste ainda falha depois do "fix" | hipótese errada | isole o teste que falha e rededuza o bug |

Perguntas de diagnóstico:

- é falha de lógica, de estado, de ambiente ou de política?
- o agente perdeu o objetivo real e passou a otimizar subtarefa errada?
- a falha é determinística ou transitória?
- qual a menor ação reversível que valida o diagnóstico?

### Fase 3: recuperação contida

Recupere com a menor ação que muda a superfície do diagnóstico.

Ações seguras:

- parar as tentativas repetidas e reenunciar a hipótese;
- aparar contexto de baixo sinal, mantendo objetivo ativo, bloqueios e
  evidência;
- reverificar o estado real de filesystem, branch e processo;
- estreitar a tarefa para um comando, um arquivo ou um teste;
- trocar raciocínio especulativo por observação direta;
- escalar ao humano quando o risco for alto ou o bloqueio for externo.

Não prometa ação de autocura não suportada ("resetar estado do agente",
"alterar config do harness") sem executá-la de fato com ferramentas reais
do ambiente corrente.

Checklist:

```markdown
## Ação de recuperação
- Diagnóstico escolhido:
- Menor ação executada:
- Por que é segura:
- Evidência que provaria a correção:
```

### Fase 4: relatório de autodiagnóstico

Feche com um relatório que torne a recuperação legível para o próximo
agente ou para o humano.

```markdown
## Relatório de autodiagnóstico
- Sessão / tarefa:
- Falha:
- Causa raiz:
- Ação de recuperação:
- Resultado: sucesso | parcial | bloqueado
- Risco de queima de tokens e tempo:
- Follow-up necessário:
- Mudança preventiva a codificar depois:
```

## Heurísticas de recuperação

Prefira as intervenções nesta ordem:

1. Reenuncie o objetivo real em uma frase.
2. Verifique o estado do mundo em vez de confiar na memória.
3. Encolha o escopo que falha.
4. Rode uma verificação discriminante.
5. Só então tentar de novo.

Padrão ruim: repetir a mesma ação três vezes com redação levemente
diferente.

Padrão bom: capturar a falha, classificar o padrão, rodar uma verificação
direta e mudar o plano apenas se a verificação sustentar a mudança.

## Padrão de saída

Com a skill ativa, não termine a resposta apenas com "corrigi". Sempre
informe:

- o padrão da falha;
- a hipótese de causa raiz;
- a ação de recuperação;
- a evidência de que a situação melhorou ou segue bloqueada.
