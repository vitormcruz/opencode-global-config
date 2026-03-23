---
name: aws-add-account-sso
description: Adiciona novos perfis AWS SSO para contas adicionais no ~/.aws/config
---

Voce e uma skill para onboarding de novas contas AWS via SSO.

## Objetivo

Adicionar perfis AWS CLI para novas contas AWS acessiveis pelo portal SSO, com aliases consistentes.

## Quando usar

Use esta skill quando o humano pedir algo como:
- "adicione uma nova conta AWS"
- "crie um perfil para esta conta"
- "configure acesso para outra conta"
- "adicione aliases novos no aws config"

## Entrada esperada

Receba do agente principal:
- nome da conta AWS desejada, ou account id
- prefixo/alias desejado
- ambiente(s) desejado(s): `nprd`, `prd`, `hmg`, etc.
- profile SSO base, se relevante
- regiao padrao desejada

## Fluxo obrigatorio

1. Validar se o AWS CLI esta disponivel.
2. Validar se existe sessao SSO utilizavel.
3. Identificar a conta alvo com:
   - `aws sso list-accounts`
4. Listar roles disponiveis na conta:
   - `aws sso list-account-roles --account-id <id>`
5. Mapear roles para aliases propostos.
6. Mostrar ao humano:
   - conta encontrada
   - account id
   - roles encontradas
   - aliases que serao criados
7. Pedir confirmacao explicita antes de editar `~/.aws/config`.
8. So apos confirmacao:
   - adicionar os perfis no `~/.aws/config`
9. Validar cada novo perfil com:
   - `aws sts get-caller-identity --profile <profile>`

## Regras de nomenclatura

- Use aliases consistentes com o padrao informado pelo humano.
- Prefira:
  - `<prefixo>-<conta>-nprd`
  - `<prefixo>-<conta>-prd`
- Nao sobrescreva aliases existentes sem avisar.
- Se houver conflito de nome, proponha alternativa objetiva.

## Regras de seguranca

- Nunca presumir que a role e readonly.
- Nunca ler segredos.
- Nunca criar perfis sem mostrar antes ao humano o que sera escrito.
- Nunca alterar outras entradas do `~/.aws/config` sem necessidade.

## Saida esperada

A skill deve devolver ao agente principal:
- conta encontrada
- account id
- roles disponiveis
- aliases propostos
- bloco exato que sera inserido no `~/.aws/config`
- comando de validacao de cada profile

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
