# Prompt — agente Windows — validação do AWS CLI

Você é o executor autônomo da validação do AWS CLI v2 no ambiente Windows
nativo do repositório `opencode-config`. Edite arquivos, escreva ou ajuste
testes quando necessário, valide o bootstrap real sem administrador e faça o
commit ao final. Não entregue apenas diagnóstico ou sugestões.

## Autorização

O humano autorizou explicitamente:

- alterar os arquivos necessários para corrigir o bootstrap do AWS CLI;
- criar ou atualizar testes automatizados;
- atualizar `README.md` e `plan/mcp-to-cli-migration.md` quando diretamente
  relacionados à validação;
- fazer o commit ao final, sem pedir nova confirmação.

Não faça push. Não use `git reset --hard`, `git checkout`, rebase destrutivo,
`git clean` ou reverta alterações existentes. Preserve alterações que já
estiverem no worktree. Não misture correções Docling ou OpenCode no commit,
exceto se forem indispensáveis para o contrato AWS CLI.

**Autoexclusão obrigatória:** este arquivo é um prompt temporário. Antes do
commit final, apague somente
`docs/prompts/aws-cli-windows-validation.md`. Não apague outros prompts.

## Repositório e fonte da verdade

- Repositório: `opencode-config`
- Branch esperada: `master-nova`
- No Windows, use a raiz local do clone, normalmente
  `C:\Users\ur5y\Projetos\opencode-config`.
- Plano aprovado: `plan/mcp-to-cli-migration.md`
- Regras gerais: `AGENTS.md` e `.github/copilot-specific.instructions.md`.
- Leia o plano inteiro e `AGENTS.md` antes de agir.
- A decisão AD-13 está aprovada e não deve ser reaberta.
- Não altere a arquitetura OpenCode/WSL nem reintroduza MCP local.
- Windows usa somente o adapter Copilot; OpenCode é exclusivo de WSL/Linux.

O worktree pode conter alterações não commitadas da correção Docling
multiplataforma. Registre o estado inicial, preserve essas alterações e não as
inclua no seu commit se não forem parte desta validação.

## Objetivo exato

Validar a única pendência Windows relacionada ao inventário de skills:

```text
aws --version
```

O AWS CLI v2 é uma dependência obrigatória do bootstrap nos dois sistemas e é
usado por:

- `agents/aws-analista.md`;
- `skills/aws-sso-login/SKILL.md`;
- `skills/aws-add-account-sso/SKILL.md`.

A validação não exige credenciais AWS, perfil configurado, login SSO,
requisições à AWS ou alteração de `~/.aws/config`. Não execute operações
remotas. Basta confirmar que o executável está instalado, acessível em um novo
PowerShell e que o bootstrap preserva esse estado.

Os seis fluxos Copilot já foram validados no Windows: `crwl`,
`codebase-memory-mcp cli`, Docling, Pandoc, SVG-to-image e browser-testing.
Não os reimplemente nem reabra seus problemas. Só repita testes deles se uma
alteração compartilhada tornar isso necessário.

## AD-13 aprovado

O AWS CLI v2 deve ser instalado pelo script oficial da AWS, em modo
user-local, sem `sudo` e sem administrador.

URLs oficiais permitidas:

- Linux/WSL:
  `https://awscli.amazonaws.com/v2/install.sh`
- Windows:
  `https://awscli.amazonaws.com/v2/install.ps1`

No Windows, o contrato aprovado é:

- script oficial `install.ps1`;
- execução silenciosa com `-Quiet`;
- versão opcional com `-Version <X.Y.Z>`;
- destino user-local padrão em
  `%LOCALAPPDATA%\Programs\Amazon\AWSCLIV2`;
- nenhuma execução com `-System`;
- nenhuma elevação UAC;
- o MSI user-local gerencia o PATH.

Não troque o instalador por MSI per-machine, Chocolatey, winget, instalação
manual global ou workaround local. Não fixe URL corporativa, certificado,
proxy, mirror ou bypass TLS no repositório. Se a rede exigir configuração
corporativa, use apenas variáveis ou arquivos temporários aprovados pelo
humano e registre a limitação sem desativar a validação TLS.

## Skills obrigatórias

Carregue e aplique:

- `planning-and-task-breakdown`
- `test-driven-development`
- `tests-as-spec`
- `code-explorer-priority`
- `code-review-and-quality`
- `debugging-and-error-recovery`
- `security-and-hardening`
- `documentation-and-adrs`
- `git-workflow-and-versioning`
- `caveman`
- `spec-driven-development`

## Descoberta e escopo técnico

Antes de procurar código, tente o codebase-memory conforme as instruções do
repositório. No Windows, use o cliente disponível no ambiente, por exemplo:

```powershell
codebase-memory-mcp cli list_projects
```

Se o ambiente fornecer o wrapper `mcp`, use o equivalente documentado em
`.github/copilot-specific.instructions.md`. Só use `rg`, `glob` ou leitura
direta como fallback quando o CLI não responder ou quando o caminho já estiver
confirmado.

Arquivos principais:

- `src/opencode_config/bootstrap/registry.py`
- `src/opencode_config/bootstrap/detect.py`
- `src/opencode_config/bootstrap/main.py`
- `src/opencode_config/bootstrap/installers/core.py`
- `src/opencode_config/bootstrap/installers/__init__.py`
- `src/opencode_config/bootstrap/interactive.py`
- `tests/bootstrap/test_detect.py`
- `tests/bootstrap/test_installers.py`
- `tests/bootstrap/test_entrypoints.py`
- `scripts/bootstrap_repo/configurar-repo.ps1`
- `README.md`
- `plan/mcp-to-cli-migration.md`

O registro atual deve conter `aws-cli`, comando `aws`, versão mínima maior ou
igual a 2 e método user-local para Windows. O instalador compartilhado deve
usar o script oficial correto por sistema. No Windows, ele deve executar
PowerShell sem `-System`; no Linux, não pode perder `--install-dir`,
`--bin-dir`, `--quiet` ou a persistência do PATH.

## Procedimento obrigatório

### 1. Registrar o estado inicial

No PowerShell:

```powershell
git status --short
git branch --show-current
git diff --check
$PSVersionTable.PSVersion
python --version
```

Se `python` não existir, use o comando Python já reconhecido pelo entrypoint e
registre o diagnóstico; não instale Python como administrador.

### 2. Ler o contexto aprovado

Leia o plano inteiro, incluindo AD-13, Task 4.2, Task 4.5, Task 6.3 e o
checkpoint final. Não replaneje as decisões aprovadas. Compare o código atual
com o contrato do plano antes de editar.

### 3. Validar o estado sem instalar

Execute:

```powershell
.\scripts\bootstrap_repo\configurar-repo.ps1 --check-only
```

Confirme:

- exit code `0`;
- a tabela detecta `aws-cli` como presente, ausente ou outdated;
- versão, caminho e método aparecem;
- `--check-only` não altera arquivos nem instala dependências;
- nenhum pedido de elevação ocorre.

Se o `aws` já estiver presente, capture somente versão e caminho. Não capture
variáveis de ambiente completas, tokens ou arquivos de credenciais.

### 4. Validar a instalação real

Se o AWS CLI estiver ausente ou outdated, execute o bootstrap aprovado:

```powershell
.\scripts\bootstrap_repo\configurar-repo.ps1 --yes
```

Se o bootstrap pedir seleção interativa, não contorne o contrato: use
`--yes`. Registre exit code, saída relevante e o bloco de comandos manuais,
sem incluir segredos.

Confirme que:

- não houve UAC nem solicitação de administrador;
- o instalador usado foi o script oficial;
- `-Quiet` foi usado;
- `-System` não apareceu;
- falhas de outras dependências não ocultaram a situação do AWS CLI;
- o diretório user-local esperado foi usado;
- o PATH de usuário foi persistido de forma idempotente.

Se for necessário corrigir código, escreva primeiro um teste pytest que
reproduza a falha. Confirme RED, implemente a correção, confirme GREEN e teste
também o caminho Linux/WSL por mocks ou testes parametrizados. Não adicione
testes que dependam de credenciais AWS.

### 5. Validar em um novo PowerShell

Feche a sessão usada no bootstrap e abra uma nova janela nativa do PowerShell
5.1, sem WSL. Nessa nova sessão, execute:

```powershell
aws --version
Get-Command aws
```

O primeiro comando deve retornar exit code `0` e mostrar `aws-cli/2.`. Registre
a saída e o caminho do executável. Se o comando não for encontrado, verifique
o PATH de usuário persistido e o comportamento do entrypoint antes de editar
qualquer código. Não resolva o problema com um PATH hardcoded no repositório.

Também confirme a presença dos artefatos sincronizados:

```powershell
Test-Path "$env:USERPROFILE\.copilot\agents\aws-analista.md"
Test-Path "$env:USERPROFILE\.copilot\skills\aws-sso-login\SKILL.md"
Test-Path "$env:USERPROFILE\.copilot\skills\aws-add-account-sso\SKILL.md"
```

Não execute `aws sts`, `aws sso login`, `aws configure` ou qualquer comando que
exija perfil, rede AWS ou credenciais. A presença do CLI é o escopo desta
validação.

### 6. Validar idempotência

Com o AWS CLI presente, execute novamente apenas o fluxo necessário do
bootstrap, preferencialmente:

```powershell
.\scripts\bootstrap_repo\configurar-repo.ps1 --check-only
```

Se a implementação exigir confirmação da instalação no-op, execute
`--yes` novamente e confirme que não reinstala, não muda a versão e não cria
duplicatas no PATH. Não remova uma instalação funcional para testar.

### 7. Testes

Sem alteração de código, execute pelo menos os testes já existentes
relacionados:

```powershell
pytest -m unit tests/bootstrap/test_detect.py tests/bootstrap/test_installers.py
```

Se houver alteração compartilhada no bootstrap, execute também:

```powershell
pytest -m "unit or tools or copilot" -q
```

Não use `skip`, `xfail` artificial, catches amplos, fallback silencioso ou
remoção de teste. Se uma dependência externa não estiver disponível, o teste
deve falhar com mensagem acionável, conforme as regras do repositório.

## Segurança e compatibilidade

- Não use administrador, `-System`, `sudo`, Chocolatey ou instalação global.
- Não execute comandos de escrita na AWS.
- Não leia nem registre credenciais, tokens, perfis ou certificados privados.
- Não desative TLS nem use `strict-ssl=false`.
- Não adicione hostname corporativo, CA ou mirror ao código.
- Preserve o contrato Linux/WSL ao tocar no instalador compartilhado.
- Preserve o adapter Copilot e não execute o adapter OpenCode no Windows.
- Não reintroduza MCP local, Docker de Crawl4AI, `.bats`, Makefile ou scripts
  paralelos por sistema operacional.
- Use `git mv` em qualquer movimento/renomeação versionada.
- Mantenha arquivos executados no Windows em formato compatível e Markdown
  abaixo de 120 colunas.

## Critérios de conclusão

Só declare sucesso se todos forem verdadeiros:

- `configurar-repo.ps1 --check-only` terminou com exit `0`;
- o bootstrap `--yes` foi executado ou o AWS CLI já estava presente e válido;
- não houve elevação nem instalação global;
- `aws --version` funcionou em uma nova sessão PowerShell;
- a versão retornada é AWS CLI v2;
- `Get-Command aws` aponta para um caminho user-local;
- as três cópias de skills/agente AWS existem em `%USERPROFILE%\.copilot`;
- a detecção subsequente mostra `aws-cli` como presente e não outdated;
- os testes relacionados passaram;
- nenhuma regressão Linux/WSL foi introduzida pelo diff;
- o plano e a documentação refletem apenas o resultado observado;
- nenhum segredo ou configuração corporativa foi versionado.

Se um critério falhar por uma limitação real do ambiente, preserve as
evidências, informe o bloqueio claramente e não declare sucesso falso. Não faça
commit de uma validação incompleta, salvo se houver uma correção de código
independente e testada que deva ser preservada.

## Plano e evidências

Use uma pasta temporária fora do repositório, por exemplo:

```powershell
$evidence = Join-Path $env:TEMP "opencode-config-aws-cli-validation"
New-Item -ItemType Directory -Force $evidence | Out-Null
```

Registre nessa pasta somente saídas não sensíveis, códigos de saída, versão,
caminho, data e sistema operacional. Não copie `%USERPROFILE%\.aws`,
variáveis de ambiente completas ou logs que possam conter credenciais.

Atualize `plan/mcp-to-cli-migration.md` somente com evidências reais da
validação AWS. Marque a pendência `aws --version` como concluída apenas após a
nova sessão PowerShell. Não marque o OpenCode/WSL como concluído neste trabalho.

Atualize `README.md` apenas se a documentação do AWS CLI estiver incorreta.
Não faça refatorações ou limpeza fora do escopo.

## Revisão e commit

Antes do commit:

```powershell
git diff --check
git status --short
git diff
```

Confirme que alterações preexistentes foram preservadas e que o diff contém
somente a correção/testes/documentação AWS e a remoção deste prompt temporário.

Apague somente este arquivo:

```powershell
Remove-Item -LiteralPath "docs/prompts/aws-cli-windows-validation.md"
```

Faça um commit Conventional Commit em PT-BR, modo caveman. Exemplos:

```text
test(bootstrap): validar AWS CLI Windows
fix(bootstrap): corrigir AWS CLI Windows
```

Escolha `test` se não houver correção de código e `fix` se houver correção
funcional. O commit é autorizado por este prompt. Não peça confirmação
adicional e não faça push.

Ao terminar, informe o SHA, a versão e o caminho do AWS CLI, os comandos
executados e seus exit codes, testes, critérios atendidos, pasta de evidências,
alterações realizadas e qualquer bloqueio residual. Não diga “OK” se algum
critério permanecer pendente.
