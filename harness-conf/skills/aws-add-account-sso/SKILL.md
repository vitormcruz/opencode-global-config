---
name: aws-add-account-sso
description: >
  Use para adicionar perfis AWS SSO de novas contas no ~/.aws/config, com
  aliases por ambiente e confirmação explícita antes de editar.
  Triggers: "adicionar conta AWS", "novo perfil AWS", "aliases aws config".
---

Onboarding de novas contas AWS via SSO: cria perfis no `~/.aws/config` com aliases consistentes.

## Entrada esperada

- Nome da conta AWS desejada ou account id.
- Prefixo/alias desejado.
- Ambiente(s): `nprd`, `prd`, `hmg`, etc.
- Profile SSO base, se relevante.
- Região padrão.

## Fluxo obrigatório

1. Valide que o AWS CLI está disponível.
2. Valide que existe sessão SSO utilizável.
3. Identifique a conta alvo: `aws sso list-accounts`
4. Liste as roles da conta: `aws sso list-account-roles --account-id <id>`
5. Mapeie as roles para os aliases propostos.
6. Mostre ao humano: conta encontrada, account id, roles encontradas e aliases que serão criados.
7. Edite o `~/.aws/config` somente após confirmação explícita do humano.
8. Valide cada novo perfil: `aws sts get-caller-identity --profile <profile>`

## Nomenclatura

- Siga o padrão informado pelo humano; prefira `<prefixo>-<conta>-nprd` e `<prefixo>-<conta>-prd`.
- Não sobrescreva alias existente sem avisar; em conflito de nome, proponha alternativa objetiva.

## Segurança

- Não presuma que a role é readonly. Não leia segredos.
- Mostre ao humano o que será escrito antes de escrever.
- Não altere outras entradas do `~/.aws/config` sem necessidade.

## Saída esperada

Conta encontrada, account id, roles disponíveis, aliases propostos, bloco exato a inserir no
`~/.aws/config` e comando de validação de cada perfil.

Exemplo de bloco:

```ini
[profile atlas-a12345-nprd]
sso_session = empresa
sso_account_id = 123456789012
sso_role_name = AppTeam-NPRD
region = sa-east-1
output = json

[profile atlas-a12345-prd]
sso_session = empresa
sso_account_id = 123456789012
sso_role_name = AppTeam-PRD
region = sa-east-1
output = json
```
