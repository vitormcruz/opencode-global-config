---
name: aws-sso-login
description: Valida ou renova a sessao AWS SSO para um profile informado
---

Voce e uma skill para autenticacao AWS SSO via AWS CLI.

## Objetivo

Garantir que o agente consiga usar um `--profile` AWS com sessao SSO valida antes de iniciar investigacoes.

## Quando usar

Use esta skill quando:
- o humano pedir login na AWS
- o agente receber erro de sessao expirada
- comandos AWS falharem por falta de autenticacao SSO
- for necessario validar se um profile ainda esta autenticado

## Entrada esperada

Receba do agente principal:
- `profile`
- opcionalmente `region`
- opcionalmente contexto humano, como "vou investigar ECS" ou "vou adicionar nova conta"

## Fluxo obrigatorio

1. Validar se o AWS CLI esta disponivel.
2. Verificar se o profile existe:
   - `aws configure list --profile <profile>`
3. Testar autenticacao atual com:
   - `aws sts get-caller-identity --profile <profile>`
4. Se funcionar:
   - informar que a sessao esta valida
   - devolver `account id`, `arn` e `region`
5. Se falhar por expiracao/ausencia de login:
   - executar `aws sso login --profile <profile>`
6. Informar ao humano que o navegador pode abrir ou que ele precisara confirmar o codigo/device flow.
7. Depois do login, validar novamente com:
   - `aws sts get-caller-identity --profile <profile>`
8. Devolver o resultado final ao agente principal.

## Regras

- Sempre usar o `profile` informado explicitamente.
- Nao alterar `~/.aws/config`.
- Nao trocar aliases automaticamente.
- Nao tentar criar profile novo; isso pertence a outra skill.
- Se o login falhar, devolver o erro resumido e o ponto de bloqueio.

## Saida esperada

A skill deve devolver ao agente principal:
- profile validado
- se a sessao ja estava valida ou foi renovada
- account id
- arn do caller identity
- regiao efetiva
- eventual erro, se houver

## Exemplos de uso

Validar sessao:
```bash
aws sts get-caller-identity --profile atlas-a12345-nprd
```

Renovar sessao:
```bash
aws sso login --profile atlas-a12345-nprd
```
