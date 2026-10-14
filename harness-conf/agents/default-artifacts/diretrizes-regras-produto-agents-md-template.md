<!-- TEMPLATE: seção completa de Diretrizes e Regras de Produto gravada no
     AGENTS.md do projeto-alvo. Reúne o índice dos artefatos do produto,
     a referência à especificação de testes e as Instruções por Agente. -->
## Diretrizes e Regras de Produto

Consulte a [Especificação do Produto](docs/README.md), parte das
Diretrizes e Regras de Produto, antes de planejar ou implementar mudanças
neste projeto.

Os documentos abaixo formam as Diretrizes e Regras de Produto:

- `docs/README.md`: Especificação do Produto. Define o escopo, os elementos
  de especificação e as regras de documentação.
- `docs/testes-por-especialidade.md`: especificação das suítes de validação,
  seus critérios, limites, ferramentas e formato de saída.
- Esta seção do `AGENTS.md`: índice dos documentos e Instruções por Agente
  aplicáveis ao projeto.

### Testes por Especialidade

A especificação das suítes fica no arquivo independente
`docs/testes-por-especialidade.md`. Esta subseção contém apenas a
referência ao arquivo, não reproduz sua tabela, seus critérios ou seus
scripts.

Consulte a especificação em
[`docs/testes-por-especialidade.md`](docs/testes-por-especialidade.md).

### Instruções por Agente

Toda vez que um agente desta seção for utilizado, ele deve
consultar a subseção com seu nome antes de executar a tarefa.
Deve procurar instruções específicas para aquela utilização e
cumpri-las quando existirem. A consulta vale tanto quando o
agente é acionado pelo `devflow` quanto quando é chamado
diretamente pelo humano.

`SEM INSTRUÇÕES A PEDIDO DO HUMANO` significa que não há
instrução adicional. Esta seção não contém o contrato detalhado
das suítes de teste.

#### eng-software

Sempre execute os testes automatizados relacionados às modificações feitas
por você para verificar se ocorreu alguma regressão. Corrija imediatamente
qualquer erro encontrado.

#### dba

SEM INSTRUÇÕES A PEDIDO DO HUMANO

#### front

Sempre execute os testes automatizados relacionados às modificações feitas
por você para verificar se ocorreu alguma regressão. Corrija imediatamente
qualquer erro encontrado.

#### sec

SEM INSTRUÇÕES A PEDIDO DO HUMANO

#### qa

Execute o script agregador dos testes por especialidade na etapa de Testes.

#### rev

SEM INSTRUÇÕES A PEDIDO DO HUMANO

#### curador-produto

Valide a evidência de execução do script agregador dos testes por
especialidade na etapa de Testes apenas.
