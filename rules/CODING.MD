# Regras de Codificação

## Lingua

- Comentários em PT-BR
- Código em inglês, mas com termos de negócio em português, veja exemplos abaixo:

`` public void getNumeroCarteira{...} ``
`` public String getNumeroCarteira{...} ``

## Boas Práticas

Aplique:

- Clean Code
- TDD, antes de todo código de negócio
  - Escreva os testes de uma funcionalidade, execute-os, veja que TODOS os testes falharam
  - Se um teste passar sem ter código produtivo ainda escrito, ele está errado
  - Não siga para a escrita do código de produção que fara os testes passarem sem que todos os testes tenham falhado
  - Quando todos os testes tiverem falhado, implemente os testes 
  - Não escreva testes para funções muito simples como gettters e setters
  - Não escreva testes para estruturação/diagramação de tela.
  - Na dúvida **pergunte ao humano**
- 12Factor
