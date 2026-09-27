# ADR-0009: Referências a skills de domínio nos perfis do Copilot

- **Status:** Aceita
- **Data:** 2026-09-27
- **Escopo:** perfis de agentes materializados pelo adapter Copilot

## Contexto

O adapter Copilot mantém as skills globais em `.copilot/skills/` e as skills
de domínio em `.copilot/referencias/skills/`. A pasta auxiliar fica fora da
descoberta automática do Copilot.

O Copilot precisa receber a descrição da skill e o caminho da cópia auxiliar
para carregar a skill sob demanda. O perfil fonte continua exclusivo do repo.

## Decisão

O adapter deriva as referências do mapa global `permission.skill` e das
permissões `skill` de cada agente. O adapter gera o bloco somente na cópia
materializada do perfil e somente para skills de domínio autorizadas naquele
perfil.

Cada entrada contém a descrição completa de `SKILL.md` na fonte do repo e o
caminho absoluto resolvido para o `SKILL.md` copiado em
`.copilot/referencias/skills/`. O adapter não lê o corpo da cópia auxiliar para
gerar o bloco. Agentes sem skills de domínio autorizadas não recebem o bloco.

## Consequências

- O Copilot lê cada skill autorizada sob demanda pelo caminho absoluto.
- Caminhos dependem do diretório de usuário usado na sincronização.
- O bloco não altera os perfis versionados no repo.
- A descrição permanece completa, incluindo os triggers registrados na fonte.
- O corpo da skill não entra no perfil gerado.

## Alternativas consideradas

- Inserir referências nos perfis fonte: rejeitada porque também alteraria os
  agentes consumidos pelo OpenCode.
- Ler a descrição da cópia auxiliar: rejeitada porque a pasta auxiliar não é a
  fonte canônica usada pelo adapter.
- Repetir todas as skills em cada perfil: rejeitada porque ignora as permissões
  por agente e aumenta o contexto carregado.

## Asserções executáveis

A fixture Concordion deste ADR expõe `executarVerificacoes()` e `veredito`.
A diretiva `execute` executa as verificações da decisão. A diretiva
`assertEquals` fixa o veredito esperado.

- [Executar as verificações deste ADR](#execute=executarVerificacoes()).
- `tests/harnesses/test_copilot.py` verifica permissão por perfil, descrição
  completa, caminho absoluto, fonte intacta e exclusão do corpo auxiliar.
- O veredito agregado da implementação é [pass](#assertEquals=veredito).
