# ADR-0006: Camada MCP opcional com fallback CLI garantido

- **Status:** Aceita
- **Data:** 2026-09-13
- **Escopo:** adapters de harness, bootstrap, skills

## Contexto

A ADR-0001 eliminou os MCPs locais e adotou CLIs nativos (AD-1). Revisão
arquitetural de 13/09/2026 avaliou readotar o modo MCP para ferramentas
específicas. Medição local com o codebase-memory 0.10.8 mostrou custo
desfavorável no cenário vigente: ~5.100 tokens fixos por sessão (modo MCP)
contra ~100-150 tokens por busca via CLI, com break-even em torno de 40
buscas por sessão. A adoção foi adiada; esta ADR padroniza como ferramentas
podem entrar na camada MCP.

## Decisão

O padrão permanece CLI-first. A camada MCP é opcional, por ferramenta:

| ID | Decisão aceita |
|---|---|
| MD-1 | Adição de ferramenta à camada MCP exige decisão humana explícita, após avaliação de prós e contras. Nenhuma adição é automática. |
| MD-2 | A avaliação verifica, pela ferramenta: suporte oficial (mantido pelo próprio projeto); instalação user-space simples, sem containers ou sidecars; uso pelo menos tão bom quanto o CLI atual; funcionamento nativo nos sistemas operacionais suportados, sem ponte complexa. Reprovada em qualquer critério, fica só CLI. |
| MD-3 | A avaliação mede custo/benefício localmente (custo fixo de contexto por sessão vs custo por uso via CLI, break-even, ganhos de tempo e de confiabilidade) e cita fonte oficial. |
| MD-4 | Aprovada, o adapter/bootstrap é o escritor único das entradas MCP nos arquivos canônicos de configuração de cada harness gerenciado, preservando servers definidos manualmente pelo humano; instaladores nativos das ferramentas não rodam. |
| MD-5 | Toda ferramenta com modo MCP mantém o caminho CLI documentado na skill como plano B permanente (hierarquia: MCP > cli > busca textual). |

## Consequências

- Nenhuma ferramenta em MCP nesta data; vereditos e medições da avaliação de
  13/09/2026 (incluindo a postergação do codebase-memory) estão no artefato
  de planejamento da época em `plan/`.
- Reavaliar quando mudar o cálculo de custo dos harnesses (ex.: carregamento
  de tools sob demanda) ou o padrão de uso das ferramentas.
- Skills não assumem tools MCP até existir adição específica aprovada.

## Alternativas rejeitadas

- Adotar MCP imediatamente: o custo fixo medido não se paga no cenário
  vigente.
- Proibir MCP permanentemente: descarta ganhos em cenários onde o custo é
  baixo.
- Instaladores nativos escrevendo as configs: conflito com a fonte de verdade
  única do repo (ADR-0004).

## Asserções executáveis

- Decisão de processo; sem testes novos obrigatórios.
- Revisões verificam ausência de entradas MCP não aprovadas nas configs
  canônicas dos harnesses gerenciados.
