---
description: >
  Analisa e otimiza um arquivo AGENTS.md em dois estágios (descobribilidade e
  compressão); gera diff e relatório antes/depois e só aplica com aprovação
  explícita do humano
---

Otimizar um arquivo AGENTS.md apontado pelo humano: reduzir o custo de
contexto sem perder nenhuma regra operacional. O command NUNCA edita o
arquivo alvo por conta própria: o ciclo é analisar, propor diff, aguardar
aprovação e só então aplicar.

## Entrada

1. O humano indica o arquivo alvo (caminho do AGENTS.md). Se não indicar,
   pergunte antes de prosseguir.
2. Se o arquivo não existir ou estiver vazio, encerre com mensagem clara.
3. Trabalhe sempre sobre uma cópia de rascunho. O arquivo original permanece
   intocado até a aprovação final.

## Regra inviolável

- Nenhuma escrita no arquivo alvo antes de o humano aprovar o diff completo.
- A aprovação precisa ser uma resposta afirmativa explícita do humano a um
  diff apresentado. Silence ou continuidade de conversa não é aprovação.
- Ajustes pedidos geram novo rascunho, novo diff e nova rodada de
  aprovação.

## Estágio 1 — filtro de descobribilidade

Para cada linha ou bullet do arquivo, aplique o teste: "um agente descobre
essa linha em 10 segundos de leitura do contexto em que trabalha?". Marque
cada linha como MANTER ou CANDIDATA, com motivo de uma linha. É candidata a
sair a linha que:

- não muda o comportamento do agente em situação reconhecível (exposição,
  histórico, justificativa longa, elogio de ferramenta);
- não tem gatilho detectável no fluxo normal do trabalho (nomes de arquivo,
  comando, tipo de erro, evento são gatilhos; "seja cuidadoso" não é);
- repete o ambiente, informação que o agente recupera na hora em fonte
  melhor (README, config, saída de comando), pois isso é cache sujeito a
  ficar obsoleto;
- repete outra linha do próprio arquivo com outras palavras.

Em caso de dúvida, MANTER. Nenhuma linha sai sem motivo registrado.

## Estágio 2 — compressão com garantia de comportamento

Reescreva apenas as linhas marcadas como MANTER. Esta etapa nunca remove
regra; só reescreve. Quatro alavancas:

- No-op test: se o modelo já obedece à instrução por padrão, a frase só
  paga tokens para dizer nada. Aplique o teste frase a frase; quando a
  frase falhar, delete a frase inteira em vez de aparar palavras. Na dúvida
  sobre o padrão do modelo, mantenha a frase.
- Imperativo positivo: prefira afirmar o comportamento alvo ("escreva
  commits curtos") à proibição ("não escreva commits longos"). Proibição
  fica só quando é guardrail duro impossível de formular em positivo; nesse
  caso, emparelhe com o alvo positivo. A troca de formulação não pode
  alterar o comportamento exigido.
- Um termo por conceito: colapse sinônimos num termo canônico e use esse
  termo em todas as ocorrências. Preserve termos consagrados do domínio.
- Bullets: parágrafo que carrega mais de uma regra vira lista; uma regra
  por bullet, sem perder qualificadores.

## Relatório antes/depois

Apresente, sempre no mesmo ciclo do diff:

1. Contagem aproximada de tokens antes e depois. Declare o método usado
   (aproximação por caracteres divididos por 4 é aceitável; use
   ferramenta exata se houver disponível no ambiente).
2. Tabela de cobertura das regras operacionais: cada regra identificada no
   inventário original e sua presença no rascunho (presente, reescrita,
   removida). O leitor precisa conseguir verificar que nada sumiu sem
   explicação.
3. Lista do que saiu no estágio 1, cada item com o motivo registrado.
4. Diff unificado completo entre o original e o rascunho.

## Aprovação e aplicação

1. Apresente diff e relatório e pergunte ao humano se aplica.
2. Aplicar o rascunho ao arquivo alvo somente após resposta afirmativa
   explícita.
3. Se o humano pedir ajustes, revise o rascunho e reapresente diff e
   relatório. Nunca aplique ajustes parciais sem diff aprovado.
4. Depois de aplicar, informe o resultado com as contagens finais.

## Limites

- O command otimiza texto existente; não cria regras novas nem importa
  conteúdo de fora.
- Não toque em arquivos além do alvo indicado.
- Seções declaradas intocáveis pelo humano ficam fora dos dois estágios e
  aparecem no relatório apenas como preservadas.

Referência canônica do método de escrita para agentes: a skill
`writing-for-agents` deste repo (context pointers, information hierarchy,
no-op pruning). Este command é autocontido e funciona sem a skill carregada.
