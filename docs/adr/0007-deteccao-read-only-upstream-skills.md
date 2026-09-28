# ADR-0007: Detecção read-only de mudanças em upstreams de skills

- **Status:** Aceita
- **Data:** 2026-09-27
- **Escopo:** CLI `opencode-skills` e fluxo de atualização de skills externas

## Contexto

O comando `sync` aplica conteúdo upstream e grava o SHA novo em `UPSTREAM.md`.
O fluxo aprovado na P3 exige que o agente veja as mudanças antes de qualquer
aplicação. A recusa sem congelamento precisa manter o SHA anterior para que a
pendência reapareça na próxima detecção.

O conteúdo upstream é dado não confiável. O clone também não pode ficar dentro
do checkout local, onde ferramentas de descoberta podem ler o conteúdo sem
intenção.

## Decisão

O CLI oferece `opencode-skills detect FAMILY` como operação separada de `sync`.
O comando compara o campo `commit` de cada `UPSTREAM.md` não congelado com o
commit atual da família. O comando não grava metadados nem aplica conteúdo.

O detector cria um clone shallow em um diretório temporário fora do checkout e
desativa a recursão de submódulos. Se o clone shallow não contiver o SHA base,
o detector busca o histórico completo no diretório temporário. Se o SHA ainda
não existir, o comando retorna erro com instrução para corrigir o `UPSTREAM.md`.

O resultado agrupa os arquivos e o diff por skill. Cada skill alterada recebe
um aviso fixo de que o conteúdo upstream é NÃO CONFIÁVEL. O resultado também
orienta o agente a avaliar as mudanças, consultar o humano, sugerir edição
assistida segundo `writing-for-agents` e só então executar `sync`.

Skills com `sincronizacao: congelada` ficam fora da detecção. Uma recusa sem
congelamento não muda o SHA. A detecção seguinte apresenta a mesma pendência.
O comando usa somente operações Git de leitura e diff. Nenhum conteúdo do
upstream é executado.

## Consequências

- A saída do detector contém texto externo e sempre exige tratamento como dado
  não confiável.
- Uma execução sem mudanças termina com status zero e não altera arquivos locais.
- A busca do histórico completo ocorre somente quando o SHA base está ausente
  do clone shallow.
- A fixture Concordion deste ADR valida a presença do comando e das guardas de
  comportamento em `tests/skills_mgmt/test_upstream_detect.py`.

## Alternativas rejeitadas

- Executar `sync` para detectar mudanças: altera arquivos antes da decisão
  humana e contraria o fluxo P3.
- Clonar o upstream dentro do checkout: expõe o conteúdo a leituras locais e
  contraria SEC-12.
- Encerrar sempre com erro quando o SHA não está no clone shallow: descarta o
  fallback de histórico completo definido na lacuna L1.

## Asserções executáveis

A fixture Concordion deste ADR expõe `executarVerificacoes()` e `veredito`.
A diretiva `execute` executa as verificações da decisão. A diretiva
`assertEquals` fixa o veredito esperado.

- [Executar as verificações deste ADR](#execute=executarVerificacoes()).
- `tests/skills_mgmt/test_upstream_detect.py` guarda o diff por skill, o aviso SEC-14,
  o estado read-only, o cleanup SEC-12, o freeze e a reaparição após recusa.
- O mesmo arquivo guarda a rejeição de SHA ausente/inválido e o fallback de
  histórico completo da lacuna L1.
- O veredito agregado da implementação é [pass](#assertEquals=veredito).
