# ADR-0004: Adapters de harness multiplataforma

- **Status:** Aceita
- **Data:** 2026-09-09
- **Escopo:** bootstrap, adapters OpenCode e Copilot CLI, testes, docs
- **Revoga:** AD-5 e AD-6 da ADR-0001

## Contexto

O bootstrap amarrava sistema operacional a harness: Linux/WSL configurava
somente o OpenCode e Windows somente o Copilot CLI. O adapter OpenCode
recusava execução no Windows e a escolha vivia espalhada em `if`s de SO no
bootstrap. Quem usava os dois clientes precisava de máquina por cliente, e
adicionar um harness novo exigia tocar o fluxo principal.

O repositório também tinha lógica duplicada de cópia sincronizada e backup
entre os dois adapters, e env vars de usuário no Windows dependiam de logoff
para o Explorer recarregar o ambiente.

## Decisão

O bootstrap passa a detectar o SO corrente e a configurar **todos os
harnesses instalados** naquele SO, por meio de um registry de harnesses
consumido através de um contrato comum. As decisões aceitas:

1. **Windows usa cópia sincronizada.** A config global materializada no
   Windows é sempre cópia sincronizada a cada execução (modelo já usado
   pelo adapter Copilot), sem symlink/junction. Evita depender de
   Developer Mode e privilégios; a contrapartida, divergência possível
   até o próximo sync, é aceita e documentada.
2. **Default: todos os harnesses instalados.** Harness ausente no PATH é
   ignorado com aviso, sem erro. A flag `--harness a,b` restringe a
   subconjunto.
3. **Env vars de usuário no Windows em `HKCU\Environment`.** Variáveis
   como `OPENCODE_ENABLE_EXA` são persistidas via `winreg`, com broadcast
   de `WM_SETTINGCHANGE` para o Explorer recarregar sem logoff. A
   persistência existente do PATH do usuário também passa a broadcastar,
   reusando a mesma função da lib — sem ctypes duplicados.
4. **Copilot CLI instalável pelo bootstrap em Linux/WSL.** A dependência
   `copilot` do registry passa a valer nos três ambientes, com install
   method npm em prefix user-space (`npm install --global --prefix
   ~/.local @github/copilot`). Máquina nova fica sem passos manuais.
5. **Testes de integração permanecem por SO atual.** `-m opencode` roda em
   WSL/Linux (Docker + llama-server local); `-m copilot` roda no Windows.
   O que virou multi-SO foram os testes unitários/tools dos adapters e do
   registry, com winreg falso injetável. Execução cruzada das integrações
   fica como questão aberta futura.
6. **Factory injeta strategy por SO; adapter é cego ao SO.** Cada harness
   com variação por SO expõe uma interface de strategy própria
   (`OpenCodeEnvStrategy`: config dir, materialização, env vars) com
   implementações POSIX (symlink + `.bashrc`) e Windows (cópia
   sincronizada + HKCU). A factory instancia o adapter já com a strategy
   do ambiente; o adapter não contém decisão de SO. Harness sem variação
   (Copilot) não ganha strategy. Reuso entre harnesses vem de utilitários
   de lib (`lib/sync.py`, `lib/windows_env.py`), não de hierarquia
   genérica. `opencode-adapter` e `opencode-copilot-adapter` continuam
   existindo como wrappers finos do CLI.
7. **Arquitetura completa, não remendo.** Registry central + contrato
   comum + migração dos dois adapters + ADR revogando AD-5/AD-6 + testes
   multi-SO, em vez de apenas remover os bloqueios pontuais.

## Implementação atual

- `src/opencode_config/harnesses/` concentra o contrato (`HarnessAdapter`),
  o registry (`HARNESSES`) e a factory que injeta a strategy por ambiente.
- `adapters/opencode.py` e `adapters/copilot.py` são wrappers finos dos
  entrypoints de console; a lógica vive em `harnesses/`.
- `lib/sync.py` (backup, cópia sincronizada, remoção, symlink seguro) e
  `lib/windows_env.py` (winreg lazy + broadcast) são compartilhados.
- No Windows o OpenCode materializa agentes, skills, commands e
  `opencode.json` como cópia sincronizada em
  `%USERPROFILE%\.config\opencode`; o `AGENTS.md` global segue arquivo
  regular com blocos gerenciados preservados.
- As variáveis de escape `OPENCODE_SKIP_OPENCODE_ADAPTER` e
  `OPENCODE_SKIP_COPILOT_ADAPTER` mantêm a semântica: pulam o harness
  correspondente.

## Consequências

- Qualquer SO configura qualquer harness instalado; o mesmo clone atende
  máquina com um ou ambos os clientes.
- No Windows a config pode divergir da fonte entre syncs; o bootstrap
  idempotente realinha a cada execução.
- Env vars de usuário no Windows passam a valer em novos processos sem
  logoff (processos já abertos seguem exigindo reinício).
- Adicionar harness novo é registrar entrada no registry (nome, factory,
  var de escape); o bootstrap não muda.
- O adapter OpenCode deixou de levantar `UnsupportedEnvironmentError` no
  Windows; a recusa por SO não existe mais em nenhum nível.

## Alternativas rejeitadas

- Manter a seleção fixa por SO: perpetuaria o bloqueio e a duplicação de
  fluxo entre plataformas.
- Symlink/junction no Windows: exigiria Developer Mode ou privilégio de
  administrador, violando o requisito user-space do repo.
- Hierarquia genérica de adapters com template method: acoplaria
  harnesses sem variação comum (Copilot não varia) e espalharia detalhes
  de SO; strategies por harness e utilitários de lib são mais simples.
- Esperar execução cruzada das integrações antes de unificar: o custo de
  manter o acoplamento era maior que o valor do cruzamento imediato.

## Asserções executáveis

- `pytest -m "unit or tools or opencode"` (WSL/Linux) e
  `pytest -m "unit or tools or copilot"` (Windows) validam adapters,
  factory, strategies e bootstrap.
- `tests/harnesses/` cobre o contrato, a injeção de strategy por
  ambiente e a materialização de cada SO (winreg falso, sem registro
  real).
- `tests/lib/test_windows_env.py` valida gravação em HKCU e broadcast
  com módulo `winreg` falso; `tests/bootstrap/` cobre o broadcast da
  persistência do PATH.
