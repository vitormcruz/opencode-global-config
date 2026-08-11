# Prompt — agente OpenCode/WSL — validação e integração

Você é o executor autônomo da validação OpenCode no ambiente WSL/Linux do
repositório `opencode-config`. Edite arquivos, escreva ou ajuste testes,
valide a integração real com Docker/OpenCode e faça o commit ao final. Não
entregue apenas diagnóstico ou sugestões.

## Autorização

O humano autorizou explicitamente:

- alterar os arquivos necessários;
- criar ou atualizar testes;
- corrigir a integração OpenCode;
- atualizar `README.md` e `plan/mcp-to-cli-migration.md` quando diretamente
  relacionados;
- criar o commit final sem pedir nova confirmação.

Não faça push. Não use `git reset --hard`, `git checkout`, rebase destrutivo ou
reverta alterações existentes. Preserve mudanças do agente Windows. Não misture
alterações Windows no commit OpenCode sem necessidade. Não faça commit se a
integração continuar bloqueada.

**Autoexclusão obrigatória:** este arquivo é um prompt temporário. Antes do
commit final, apague somente
`docs/prompts/opencode-wsl-validation.md`. Não apague o prompt Windows.

## Repositório e fonte da verdade

- Root WSL: `/mnt/c/Users/ur5y/Projetos/opencode-config`
- Branch esperada: `master-nova`
- Plano: `plan/mcp-to-cli-migration.md`
- Estado parcial atual: commit `28791d4`
- Leia o plano inteiro e `AGENTS.md` antes de agir.
- Não reabra AD-1..AD-12.
- OpenCode é exclusivo de Linux/WSL.
- Windows usa Copilot; não altere o adapter OpenCode para Windows.
- Não reintroduza MCP local, servidores MCP locais ou Docker para Crawl4AI.
- Docker é permitido somente para a infraestrutura de teste OpenCode.
- Antes de buscar código, tente codebase-memory conforme as instruções do repo.

## Skills obrigatórias

Carregue e aplique:

- `planning-and-task-breakdown`
- `test-driven-development`
- `tests-as-spec`
- `code-explorer-priority`
- `api-and-interface-design`
- `code-simplification`
- `code-review-and-quality`
- `debugging-and-error-recovery`
- `security-and-hardening`
- `documentation-and-adrs`
- `git-workflow-and-versioning`
- `caveman`
- `spec-driven-development`

## Estado conhecido

O pacote e a suíte unit/tools já foram migrados para pytest.

Baseline WSL confirmado:

```bash
.venv/bin/pytest -m "unit or tools" -q
```

Resultado: `373 passed, 26 deselected`.

A execução abaixo produziu 24 erros:

```bash
.venv/bin/pytest -m "unit or tools or opencode" -q
```

Resultado anterior:

- `371 passed`;
- `2 deselected`;
- `24 errors`.

Todos os erros observados foram falhas da fixture por conexão recusada em:

`http://127.0.0.1:4196`

A fixture `tests/integration/conftest.py` exige que o serviço OpenCode esteja
respondendo. A mensagem acionável existente aponta para:

```bash
python3 tests/integration/docker/container_test_opencode.py --up
```

Não altere os testes para ignorar a fixture, usar skip ou mascarar a ausência
do serviço. Primeiro suba e verifique a infraestrutura real.

## Arquivos importantes

- `tests/integration/conftest.py`
- `tests/integration/behavioral_helper.py`
- `tests/integration/docker/container_test_opencode.py`
- `tests/integration/docker/Dockerfile`
- `tests/integration/test_agents.py`
- `tests/integration/test_commands.py`
- `tests/integration/test_prompts.py`
- `tests/integration/test_skills_activation.py`
- `tests/adapters/test_opencode_adapter.py`
- `src/opencode_config/adapters/opencode.py`
- `src/opencode_config/bootstrap/main.py`
- `scripts/bootstrap_repo/configurar-repo.sh`
- `README.md`
- `plan/mcp-to-cli-migration.md`

O orquestrador Docker usa:

- imagem: `opencode-config-test:latest`;
- container: `opencode-config-test`;
- host: `127.0.0.1:4196`;
- porta interna: `4096`;
- `--up`: reutiliza ou cria;
- `--rebuild`: reconstrói;
- `--down`: para;
- `--models`: lista modelos.

Os testes que enviam prompts exigem `OPENCODE_TEST_MODEL`. Não invente modelo,
token, credencial ou endpoint. Use um modelo aprovado e já configurado no
ambiente. Se a variável estiver ausente, examine a configuração existente e
`--models` sem expor segredos. Se não houver modelo aprovado, registre bloqueio
real e não declare sucesso falso.

## Procedimento obrigatório

1. Registrar estado:

```bash
git status --short
git branch --show-current
git diff --check
```

2. Ler o plano inteiro e localizar o checkpoint OpenCode/WSL.

3. Rodar o baseline unit/tools para confirmar ausência de regressões.

4. Verificar pré-requisitos:

```bash
docker --version
docker info
python3 --version
.venv/bin/python -c "import opencode_config; import pytest"
```

5. Verificar `OPENCODE_TEST_MODEL` sem imprimir segredos.

6. Subir o serviço:

```bash
python3 tests/integration/docker/container_test_opencode.py --up
```

Se a imagem não existir, permita o build. Se falhar, preserve:

```bash
docker ps -a
docker logs opencode-config-test
```

7. Verificar resposta real:

```bash
curl -fsS http://127.0.0.1:4196/
```

ou use equivalente Python da biblioteca padrão.

8. Executar primeiro:

```bash
.venv/bin/pytest -m opencode -q
```

9. Depois executar:

```bash
.venv/bin/pytest -m "unit or tools or opencode" -q
```

10. Se houver falha:

- reproduza o teste isoladamente;
- localize a camada causadora;
- escreva teste de regressão antes do código;
- confirme RED, implemente, confirme GREEN;
- não use skip, xfail artificial, broad catch ou fallback silencioso;
- repita o teste direcionado e a suíte completa.

## Validação do adapter e da migração

Execute no WSL:

```bash
./scripts/bootstrap_repo/configurar-repo.sh --check-only
./scripts/bootstrap_repo/configurar-repo.sh --yes
```

Confirme:

- links canônicos em `~/.config/opencode`;
- `OPENCODE_ENABLE_EXA` conforme contrato;
- adapter OpenCode executado somente no WSL/Linux;
- adapter Copilot não executado no Linux;
- comportamento idempotente;
- backups preservados quando destinos já existem.

Valide os entrypoints relevantes:

```bash
opencode-config-check
opencode-doc-extract --help
opencode-md-export --help
opencode-svgtoimage --help
opencode-browser-test --help
crwl --help
codebase-memory-mcp cli --help
```

Não instale ou reintroduza MCP local. O uso permitido é o CLI aprovado
`codebase-memory-mcp cli`.

Confirme que Docker está sendo usado somente para o teste OpenCode e não para
Crawl4AI. Não crie container Crawl4AI.

## Regras de teste, segurança e documentação

- TDD para qualquer mudança comportamental;
- testes devem verificar comportamento, não implementação interna;
- não use skip;
- não remova testes para obter verde;
- não coloque modelo ou credencial default;
- não grave tokens, certificados privados, URLs sensíveis ou credenciais;
- não use `strict-ssl=false` no código;
- não hardcode URLs corporativas;
- preserve line endings LF nos arquivos executados no WSL/Linux;
- use `git mv` para movimentos/renomeações versionadas;
- não ultrapasse 120 colunas em Markdown.

Atualize `plan/mcp-to-cli-migration.md` somente com o resultado real:

- causa do bloqueio;
- serviço/modelo utilizado, sem expor segredos;
- comandos e códigos de saída;
- testes e evidências;
- estado do checkpoint.

Atualize README somente se a documentação estiver diretamente incorreta para
executar a integração OpenCode.

## Critérios de conclusão

Só declare sucesso se:

- o serviço responder em `127.0.0.1:4196`;
- `pytest -m opencode -q` estiver verde;
- `pytest -m "unit or tools or opencode" -q` estiver verde;
- o baseline `pytest -m "unit or tools" -q` continuar verde;
- o adapter OpenCode WSL estiver validado;
- nenhum adapter OpenCode for executado no Windows;
- nenhum MCP local ou Docker Crawl4AI tiver sido reintroduzido;
- documentação e plano estiverem coerentes;
- nenhum segredo tiver sido adicionado.

Depois dos testes, pare o container:

```bash
python3 tests/integration/docker/container_test_opencode.py --down
```

Preserve a imagem se for útil para reprodutibilidade e registre evidências
antes de limpar recursos.

## Revisão e commit

Antes do commit:

```bash
git diff --check
git status --short
git diff
```

Confirme que alterações Windows do outro agente não foram revertidas e que
nenhum segredo foi adicionado.

Antes do commit final, apague este arquivo conforme a instrução de autoexclusão
no início. Não apague o prompt Windows.

Faça um commit Conventional Commit em PT-BR, modo caveman, por exemplo:

```text
fix(opencode): validar integracao Docker WSL
```

O commit é autorizado por esta mensagem. Não peça confirmação adicional.

Ao terminar, informe SHA, causa raiz, arquivos, testes e contagens, acceptance
criteria, evidências, status do container e qualquer bloqueio residual. Não
diga “OK” se algum critério permanecer pendente.
