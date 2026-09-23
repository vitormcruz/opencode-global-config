---
name: aws-sso-login
description: >
  Use para validar ou renovar a sessão AWS SSO de um profile com aws sso
  login, antes de investigações com --profile.
  Triggers: "login AWS", "sessão expirada", "aws sso login".
---

Autenticação AWS SSO via AWS CLI: garante um `--profile` com sessão válida antes de investigações.

## Entrada esperada

- `profile` alvo.
- Opcional: `region` e contexto do humano (ex.: "vou investigar ECS").

## Fluxo obrigatório

1. Valide que o AWS CLI está disponível.
2. Verifique que o profile existe: `aws configure list --profile <profile>`
3. Teste a autenticação atual: `aws sts get-caller-identity --profile <profile>`
4. Sessão válida: devolva `account id`, `arn` e `region` e encerre.
5. Sessão expirada ou ausente: execute `aws sso login --profile <profile>`.
6. Avise o humano que o navegador pode abrir ou que o device flow pedirá confirmação.
7. Revalide com `aws sts get-caller-identity --profile <profile>` e devolva o resultado.

## Regras

- Use sempre o `profile` informado explicitamente.
- Não altere o `~/.aws/config`, não troque aliases, não crie profile novo (outra skill cobre isso).
- Login falhou? Devolva o erro resumido e o ponto exato do bloqueio.

## Saída esperada

Profile validado, situação da sessão (válida ou renovada), account id, arn do caller identity,
região efetiva e erro eventual.
