<!-- TEMPLATE: snippet da seção "Instruções por Agente" colado no
     AGENTS.md do projeto-alvo, com uma subseção por agente do
     workflow. -->
### Instruções por Agente

Cada agente lê a própria subseção no início de qualquer
tarefa. Esta seção não contém comando de suíte. A ideia é 
orientar ações para agentes específicos em fases delimitadas

Se o humano recusar instrução para um agente, registre
`SEM INSTRUÇÕES A PEDIDO DO HUMANO`.

### eng-software

Sempre execute os testes automatizados relacionados às modificações feitas
por você para verificar se ocorreu alguma regressão. Corrija imediatamente
qualquer erro encontrado.

### dba

SEM INSTRUÇÕES A PEDIDO DO HUMANO

### front

Sempre execute os testes automatizados relacionados às modificações feitas
por você para verificar se ocorreu alguma regressão. Corrija imediatamente
qualquer erro encontrado.

### sec

SEM INSTRUÇÕES A PEDIDO DO HUMANO

### qa

Execute script agregador dos testes por especialidade na **etapa de testes**. 

### rev

SEM INSTRUÇÕES A PEDIDO DO HUMANO

### curador-produto

Valide a evidência de execução do script agregador dos testes por especialidade na **etapa de testes apenas**.
