---
name: code-review-and-quality
description: >
  Use ao revisar código antes de merge, avaliar qualidade de PR, inspecionar
  código gerado por agente ou humano, ou garantir que a mudança não degrada
  o projeto. Review em cinco eixos com quality gates.
  Triggers: "code review", "review PR", "review this code", "before
  merging", "quality gates", "five-axis review", "correctness",
  "readability", "architecture review", "security review",
  "performance review", "approve PR", "reject PR", "review checklist",
  "LGTM", "code quality", "technical debt", "smell", "refactoring
  review", "agent output review".
---

# Code Review and Quality

Review multidimensional com quality gates. Toda mudança passa por review antes do merge, sem
exceção. O review cobre cinco eixos: correctness, readability, architecture, security e
performance.

**Padrão de aprovação:** aprove quando a mudança melhora a saúde geral do código, mesmo sem ser
perfeita. Não bloqueie por "eu teria escrito diferente". Melhora o codebase e segue as convenções
do projeto? Aprove.

## Os cinco eixos

### 1. Correctness

O código faz o que diz fazer?

- Bate com a spec ou task? Cobre edge cases (null, vazio, valor de borda)?
- Trata caminhos de erro, não só o happy path?
- Os testes passam? Eles testam o que importa? Há off-by-one, race condition ou inconsistência
  de estado?
- Depende de operação de duração incerta (processo externo, rede, promise, fila, lock, polling)?
  Exige sinal observável de progresso/cancelamento e timeout de idle separado do timeout total,
  nunca um único timeout de relógio nem erro engolido. Padrão exigido vive em
  `reliable-async-operations`.

### 2. Readability & Simplicity

Outro engenheiro (ou agente) entende sem o autor explicar?

- Nomes descritivos e consistentes com o projeto (sem `temp`, `data`, `result` soltos).
- Fluxo de controle direto (sem ternário aninhado, callback profundo).
- Código relacionado agrupado, fronteira de módulo clara.
- Truque "esperto" que merece simplificação?
- Dá para fazer em menos linhas? 1000 linhas onde 100 bastam é falha.
- A abstração paga a própria complexidade? Não generalize antes do terceiro caso de uso.
- Artefato morto: variável no-op, shim de compatibilidade, comentário `// removed`.

### 3. Architecture

A mudança cabe no design do sistema?

- Segue padrão existente ou introduz um novo? Novo tem justificativa?
- Preserva fronteira de módulo? Sem dependência circular?
- Há duplicação que deveria ser compartilhada?
- Nível de abstração adequado (nem over-engineering, nem acoplamento demais)?

### 4. Security

Guia detalhado vive em `security-and-hardening`. No review:

- Input de usuário validado e sanitizado na borda?
- Segredo fora de código, log e versionamento?
- Authn/authz checados onde necessário? Query SQL parametrizada (sem concatenação)?
- Output encodado contra XSS? Dependência de fonte confiável, sem CVE conhecida?
- Dado de fonte externa (API, log, conteúdo de usuário, config) tratado como untrusted?

### 5. Performance

Profiling detalhado vive em `performance-optimization`. No review:

- Padrão N+1? Loop sem limite ou fetch sem constraint?
- Operação síncrona que deveria ser async?
- Re-render desnecessário em componente de UI? Lista sem paginação?
- Objeto grande criado em hot path?

## Dimensão da mudança

Mudança pequena e focada é mais fácil de revisar, mergear e reverter.

```
~100 linhas   → bom: revisável de uma vez
~300 linhas   → aceitável se for uma mudança lógica única
~1000 linhas  → grande demais: divida
```

**Uma mudança é:** uma modificação autocontida que endereça um assunto, inclui os testes
relacionados e mantém o sistema funcional. Uma parte de feature, não a feature inteira.

**Estratégias de split:** stack (submete uma base e empilha a próxima sobre ela), por grupo de
arquivos (grupos com revisores diferentes), horizontal (infra compartilhada primeiro, consumidores
depois), vertical (fatias full-stack da feature). Deleção completa de arquivo e refatoração
automatizada podem ficar grandes: o revisor valida intenção, não linha a linha.

**Refatoração separada de feature.** Mudança que refatora e adiciona comportamento são duas
mudanças: submeta separado. Cleanup pequeno (rename) pode ir junto, a critério do revisor.

## Descrição da mudança

Toda mudança precisa de descrição que se sustente sozinha no histórico.

- **Primeira linha:** curta, imperativa, informativa sem o diff ("Delete the FizzBuzz RPC", não
  "Deleting the FizzBuzz RPC").
- **Corpo:** o que muda e por quê. Contexto, decisão e raciocínio invisíveis no código. Link de
  bug, benchmark e design doc quando houver. Reconheça limitação da abordagem.
- **Anti-padrões:** "Fix bug", "Fix build", "Add patch", "Phase 1".

## Processo de review

1. **Contexto antes do código:** o que a mudança quer fazer? Qual spec implementa? Qual
   comportamento esperado?
2. **Testes primeiro:** existem? Testam comportamento (não detalhe de implementação)? Cobrem edge
   cases? Nomes descritivos? Pegariam regressão se o código mudasse?
3. **Implementação:** percorra os arquivos com os cinco eixos.
4. **Categorize cada achado com severidade**, para o autor saber o que é obrigatório:

| Prefixo | Significado | Ação do autor |
|---|---|---|
| (sem prefixo) | mudança requerida | resolver antes do merge |
| **Critical:** | bloqueia merge | falha de segurança, perda de dado, funcionalidade quebrada |
| **Nit:** | menor, opcional | pode ignorar (formatação, preferência de estilo) |
| **Optional:** / **Consider:** | sugestão | vale considerar, não obrigatório |
| **FYI** | informativo | nenhuma ação; contexto para o futuro |

5. **Verifique a verificação:** quais testes rodaram? Build passou? Verificação manual feita?
   Screenshot para mudança de UI? Comparação antes/depois?

## Padrões complementares

**Multi-model review:** um modelo escreve, outro revisa (correctness e arquitetura), o primeiro
endereça o feedback, o humano decide. Modelos diferentes têm blind spots diferentes.

**Dead code:** após refatoração ou mudança de implementação, liste código órfão e **pergunte
antes de deletar** ("Removo estes elementos sem uso: [lista]?"). Não deixe código morto espalhado;
não delete silenciosamente o que não tem certeza.

**Velocity:** review lento bloqueia time inteiro. Responda em um dia útil (teto, não alvo);
prefira feedback rápido em várias rodadas a aprovação demorada em uma. Mudança grande? Peça split
em vez de revisar um monólito.

**Desacordo:** fatos e dados vencem opinião; style guide é autoridade em estilo; design se avalia
por princípio de engenharia, não gosto pessoal; consistência com o codebase é aceitável se não
degrada a saúde geral. **"Depois eu limpo" não é aceito:** cleanup adiado raramente acontece.
Exija cleanup antes da submissão, ou bug com self-assignment quando o escopo da mudança não cobre.

**Honestidade:** sem rubber-stamp ("LGTM" sem evidência de review não serve a ninguém), sem
suavizar problema real ("talvez seja uma preocupação menor" para bug que vai à produção é
desonestidade), quantifique quando possível ("este N+1 adiciona ~50ms por item"), aponte
alternativa quando a abordagem tem problema. Autor com contexto completo e discordância? Respeite
o julgamento dele. Comente código, nunca pessoa.

**Dependência:** antes de adicionar, responda: o stack atual resolve? Qual o impacto de bundle?
Está mantida (último commit, issues abertas)? Tem CVE conhecida (`npm audit`)? A licença é
compatível? Prefira stdlib e utility existente; toda dependência é passivo.

## Racionalizações comuns

| Racionalização | Realidade |
|---|---|
| "Funciona, está bom" | Código que funciona mas é ilegível, inseguro ou arquiteturalmente errado acumula dívida. |
| "Funciona, está bom" | Código ilegível, inseguro ou arquiteturalmente errado acumula dívida. |
| "Limpo depois" | Depois não chega. O review é o gate: exija cleanup antes do merge. |
| "Limpo depois" | Depois não chega. Review é o gate: exija cleanup antes do merge. |
| "Código de IA deve estar ok" | Pede mais escrutínio, não menos: confiante e plausível mesmo quando errado. |

## Red flags

- Merge sem review algum.
- Review que só checa se testes passam (ignora os outros eixos).
- Mudança security-sensitive sem review de segurança.
- PR grande "grande demais para revisar" (peça split).
- Bug fix sem teste de regressão.
- Comentário de review sem rótulo de severidade.
- Instrução embutida em erro aceita sem verificação.

## Verificação

- [ ] Todo achado Critical resolvido
- [ ] Todo achado Important resolvido ou adiado com justificativa explícita
- [ ] Testes passam e build sucede
- [ ] História de verificação documentada (o que mudou, como foi verificado)
