# Prompt — agente Windows — Task 4.5

Você é o executor autônomo da validação Windows da Task 4.5 no repositório
`opencode-config`. Edite os arquivos, escreva ou ajuste testes, valide ponta a
ponta e faça o commit ao final. Não entregue apenas diagnóstico ou sugestões.

## Autorização

O humano autorizou explicitamente:

- alterar os arquivos necessários;
- criar ou atualizar testes;
- atualizar `README.md` e `plan/mcp-to-cli-migration.md` quando diretamente
  relacionados;
- executar instalações em user-space sem administrador;
- criar o commit final sem pedir nova confirmação.

Não faça push. Não use `git reset --hard`, `git checkout`, rebase destrutivo ou
reverta alterações existentes. Preserve mudanças intencionais de outros
agentes. Não faça commit se a validação continuar incompleta ou bloqueada.

**Autoexclusão obrigatória:** este arquivo é um prompt temporário. Antes do
commit final, apague somente
`docs/prompts/task-4.5-windows.md`. Não apague o prompt do agente OpenCode.

## Repositório e fonte da verdade

- Checkout Windows: `C:\Users\ur5y\Projetos\opencode-config`
- Branch esperada: `master-nova`
- Plano: `plan/mcp-to-cli-migration.md`
- Estado parcial já commitado: `28791d4`
- Leia o plano inteiro antes de agir, incluindo AD-1..AD-12, Task 4.5,
  acceptance criteria, verification, riscos e checkpoints.
- Leia `AGENTS.md` e as instruções específicas do Copilot.
- Antes de buscar código, tente `codebase-memory` conforme as instruções do
  repo. Use grep/glob/read apenas como fallback se o índice estiver
  indisponível.

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

## Arquitetura aprovada

A migração substitui MCP local por CLIs:

- Crawl4AI: `crwl`
- codebase-memory: `codebase-memory-mcp cli`

O Windows deve ser nativo:

- PowerShell nativo;
- sem WSL;
- sem administrador;
- sem instalações manuais;
- sem comandos `wsl` nas skills;
- OpenCode roda somente em WSL/Linux;
- Windows usa somente o adapter Copilot.

Não reabra AD-1..AD-12. Não reintroduza MCP local, Docker para Crawl4AI,
wrappers shell paralelos ou URLs corporativas hardcoded.

O mirror Playwright é uma configuração do ambiente, não do repositório. Use a
variável `PLAYWRIGHT_DOWNLOAD_HOST` com o valor fornecido pelo humano. A rota
validada é a rota nativa do mirror, sem o segmento `/api/`. Nunca grave o
hostname corporativo em código, teste, default ou documentação versionada.

As configurações locais de npm e pip podem apontar para registries
corporativos. Não copie essas URLs para o repositório. Não adicione
`strict-ssl=false` ao código ou à configuração versionada.

## Falha observada

Evidências:

`C:\Users\ur5y\AppData\Local\Temp\opencode-config-task45-validation-20260810-1700`

Resultado:

- `--check-only`: exit `0`;
- `--yes`: ficou sem stdout/stderr por mais de 10 minutos e foi interrompido;
- `crwl`: não encontrado;
- `crawl4ai-setup`: não encontrado;
- `docling`: não encontrado;
- `npm`: `10.9.2`;
- `npx`: `10.9.2`;
- `codebase-memory-mcp`: não encontrado;
- `opencode-config-check`: não encontrado;
- `import opencode_config`: passou;
- pytest: `332 passed`, `26 failed`, `24 deselected`, `15 errors`.

Os logs do pipx mostram o estado real:

- pipx: `C:\Users\ur5y\AppData\Roaming\Python\Python314\Scripts\pipx.exe`;
- venvs: `C:\Users\ur5y\AppData\Local\pipx\pipx\venvs`;
- apps: `C:\Users\ur5y\.local\bin`;
- o caminho antigo esperado pelo bootstrap era
  `C:\Users\ur5y\AppData\Local\pipx\bin`;
- `crawl4ai` expôs `crwl.exe` e `crawl4ai-setup.exe` em `.local\bin`;
- `opencode-config-check.exe` também existia em `.local\bin`;
- pipx informou que `.local\bin` não estava no PATH;
- `docling` iniciou uma instalação pesada e o processo ficou silencioso porque
  `run_command` captura stdout/stderr;
- codebase-memory e Playwright não chegaram a ser instalados porque o
  bootstrap foi interrompido.

O mirror Playwright, quando configurado externamente com a rota correta,
retornou `200` para os artefatos e o diagnóstico isolado conseguiu instalar
Chrome, headless shell, FFmpeg e Winldd. O problema anterior não foi TLS nem
incompatibilidade do Python.

## Correções já iniciadas

Inspecione o diff e os testes do commit `28791d4`. Verifique, complete ou
corrija estas áreas:

1. `src/opencode_config/lib/paths.py`
   - `pipx_bin` Windows deve ser `%USERPROFILE%\.local\bin`.

2. `src/opencode_config/bootstrap/installers/core.py`
   - validar entrypoints realmente expostos pelo pipx;
   - usar `pipx install --force` para reparar instalações existentes;
   - não chamar `crawl4ai-setup` se `crwl` não foi exposto;
   - tratar npm e npx como dependências independentes;
   - validar npm e npx depois de instalar Node;
   - verificar que `.venv` importa `opencode_config` e `pytest`;
   - tratar PATH case-insensitive no Windows;
   - persistir somente em user-space, sem elevação.

3. `src/opencode_config/bootstrap/main.py`
   - importar o PATH persistido do usuário;
   - pré-carregar `pipx_bin`, `npm_bin` e `bin_dir` no contexto Windows;
   - não persistir alterações durante `--check-only`;
   - passar o ambiente efetivo do contexto para a detecção.

4. `src/opencode_config/bootstrap/interactive.py`
   - o detector deve receber o ambiente efetivo do contexto.

5. `scripts/bootstrap_repo/configurar-repo.ps1`
   - permanecer fino, com aproximadamente 40 linhas ou menos;
   - importar o PATH do usuário antes de procurar Python;
   - executar o módulo Python canônico;
   - recarregar o PATH após o bootstrap;
   - não conter lógica de instalação.

Confira o PATH real, não somente o PATH do processo:

```powershell
[Environment]::GetEnvironmentVariable("Path", "User")
reg query HKCU\Environment /v Path
```

O próximo PowerShell precisa localizar os executáveis. Alterar somente
`$env:Path` do processo atual não é suficiente.

## Investigação e TDD

Reproduza primeiro em PowerShell nativo. Examine os logs antes de alterar.
Para qualquer comportamento novo ou bug corrigido:

1. escreva o teste de regressão;
2. confirme RED;
3. implemente a correção mínima;
4. confirme GREEN;
5. execute a regressão completa.

Cubra, no mínimo:

- PATH de usuário e processo, case-insensitive e idempotente;
- persistência real no registro do usuário;
- `--check-only` sem alterações persistidas;
- detecção usando o PATH efetivo do contexto;
- pipx usando `.local\bin`;
- validação de `crwl`, `crawl4ai-setup`, `docling` e
  `opencode-config-check`;
- npm e npx independentes;
- `.venv` com `opencode_config` e pytest;
- instalação de browser realmente concluída.

Não conclua que uma instalação travou apenas porque não há stdout. Se docling
ou crawl4ai forem lentos, torne progresso e erro observáveis. Use timeout
acionável quando necessário. Não use fallback silencioso, broad catch ou
sucesso falso. Se `crawl4ai-setup` retornar exit `0` contendo
`Failed to install browsers`, trate isso como falha e adicione teste.

## Testes

Execute:

```powershell
.\.venv\Scripts\pytest.exe tests\bootstrap tests\lib -q
.\.venv\Scripts\pytest.exe -m "unit or tools" -q
.\.venv\Scripts\pytest.exe -m "unit or tools or copilot" -q
.\.venv\Scripts\pytest.exe -m copilot -q
```

Não use `pytest.skip`, não remova testes e não enfraqueça as asserções.
Se testes Linux/WSL-only estiverem marcados como `tools` e forem executados
no Windows, corrija os marcadores/contratos sem esconder falhas reais e
confirme que a suíte Linux continua verde.

Investigue separadamente:

- testes do adapter OpenCode executados no Windows;
- testes de docling sem docling;
- testes Playwright sem browser;
- testes codebase-memory sem binário;
- testes Copilot sem o comando `copilot`.

Para `copilot`, consulte o plano antes de decidir se é pré-requisito externo ou
dependência que precisa entrar no bootstrap. Se for parte do acceptance
criterion, implemente instalação user-space com TDD, npm/npx e sem registry
hardcoded. Se for pré-requisito externo, documente corretamente e não declare
Task 4.5 verde sem evidência real.

## Validação ponta a ponta

Defina somente no ambiente o mirror fornecido pelo humano:

```powershell
$env:PLAYWRIGHT_DOWNLOAD_HOST = "<mirror-corporativo-validado-sem-/api>"
.\scripts\bootstrap_repo\configurar-repo.ps1 --check-only
.\scripts\bootstrap_repo\configurar-repo.ps1 --yes
```

Permita tempo suficiente para instalações legítimas, monitore os logs e não
interrompa somente por ausência de stdout.

Abra uma nova sessão PowerShell e valide:

```powershell
Get-Command crwl
Get-Command crawl4ai-setup
Get-Command docling
Get-Command npm
Get-Command npx
Get-Command codebase-memory-mcp
Get-Command opencode-config-check

crwl --help
crawl4ai-setup --help
docling --help
npm --version
npx --version
codebase-memory-mcp cli --help
opencode-config-check
.\.venv\Scripts\python.exe -c "import opencode_config; import pytest"
```

Execute os seis fluxos reais da Task 4.5:

1. web-research com `crwl`;
2. code discovery com `codebase-memory-mcp cli`;
3. doc-extract;
4. md-export;
5. svg-to-image;
6. browser-testing.

Use os harnesses e contratos existentes. Não substitua fluxos reais por testes
unitários. Preserve evidências e registre exit codes.

Faça a varredura final em `.copilot`:

- nenhum comando executável pode usar `wsl`;
- nenhum comando executável pode usar `/mnt/c`;
- não confunda menções explicativas em documentação com comandos;
- corrija qualquer instrução operacional proibida.

## Conclusão, tracking e commit

Só declare sucesso se:

- o bootstrap Windows zero-admin terminar;
- uma nova sessão localizar todos os entrypoints;
- os seis fluxos passarem;
- `%USERPROFILE%\.copilot` estiver populado;
- pytest Windows estiver verde;
- nenhum comando de skill usar `wsl` ou `/mnt/c`;
- README e plano estiverem coerentes;
- nenhuma URL corporativa estiver hardcoded;
- os testes Linux/WSL relevantes não regredirem.

Atualize Task 4.5 e o checkpoint no plano com causa raiz, arquivos, testes,
comandos, exit codes, evidências e limitações reais.

Antes do commit:

```powershell
git diff --check
git status --short
git diff
```

Faça um commit Conventional Commit em PT-BR, modo caveman, por exemplo:

```text
fix(bootstrap): corrigir PATH Windows e entrypoints user-space
```

Antes desse commit final, apague este arquivo de prompt conforme a instrução
de autoexclusão no início. Não apague o prompt OpenCode.

Ao terminar, informe SHA, causa raiz, arquivos, testes, acceptance criteria,
evidências e qualquer limitação residual. Não diga “OK” se houver critério
pendente.
