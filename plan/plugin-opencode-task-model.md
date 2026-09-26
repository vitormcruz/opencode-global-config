# Esboço: plugin provisório opencode-task-model

Insumo para planejamento posterior. Não executado ainda.

## Contexto

- Objetivo: permitir spawn de subagentes com modelo especificado por chamada
  na tool `task`.
- O OpenCode nativo (1.18.31) não aceita `model` no spawn; a precedência
  atual (frontmatter do agente, senão herdar do pai) fica intacta.
- Solução escolhida: plugin `lars-hagen/opencode-task-model` (npm,
  versão pinada).
- Status: PROVISÓRIO. Remover quando o OpenCode nativo suportar `model` na
  `task` (rastreio: PR anomalyco/opencode#34947, issue #6651, issue #17595).

## Mudanças propostas (5 pontos)

### 1. harness-conf/opencode.json (fonte canônica)

```json
"plugin": [
    "@slkiser/opencode-quota",
    "opencode-task-model@1.3.1"
]
```

Versão pinada exata (recomendação do upstream, evita alias `@latest`).
O adapter copia o arquivo inteiro, então a mudança propaga pros dois SOs
sem tocar em `src/`.

### 2. README.md (nova seção "Plugins", após "Variáveis de ambiente")

```markdown
## Plugins

- `@slkiser/opencode-quota`: quota de tokens no toast/TUI.
- `opencode-task-model@1.3.1` (PROVISÓRIO): adiciona `model`, `reasoning`,
  `background` e `worktree` por chamada na tool `task`. Instalado porque o
  OpenCode nativo ainda não aceita modelo no spawn (rastreio: PR
  anomalyco/opencode#34947, issue #6651). Remover quando a versão nativa
  suportar `model` na task; o pin é atualizado manualmente com
  `npm view opencode-task-model version`.
```

### 3. harness-conf/AGENTS.base.md (guarda de custo e comportamento)

```markdown
## Tool task (plugin opencode-task-model)

- O plugin aceita `model` e `reasoning` extras na tool `task`. Por padrão,
  omita os dois: a precedência nativa (modelo do agente no frontmatter,
  senão herda do pai) permanece canônica.
- Use `model` explícito apenas quando o briefing do humano ou do plano
  pedir um modelo específico para a subtask.
- `background: true` dá acesso local pleno ao subagente; use apenas com
  escopo aprovado e preferindo `worktree: true` para escrita.
- Prompts delegados não resolvem `@arquivo`: inclua o conteúdo no texto.
```

### 4. tests/test_opencode_plugins.py (novo, unit)

```python
from pathlib import Path
import json
import re

import pytest


PROVISORY_PLUGIN = "opencode-task-model"


@pytest.mark.unit
def test_plugins_are_pinned_to_exact_versions(repo_root: Path):
    config = json.loads(
        (repo_root / "harness-conf" / "opencode.json").read_text(
            encoding="utf-8"
        )
    )
    for entry in config.get("plugin", []):
        spec = entry.split("@")[-1] if "@" in entry else ""
        assert re.fullmatch(r"\d+\.\d+\.\d+", spec), (
            f"plugin sem pin exato: {entry}"
        )


@pytest.mark.unit
def test_provisory_task_model_plugin_is_documented(repo_root: Path):
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    assert PROVISORY_PLUGIN in readme
    assert "PROVISÓRIO" in readme
```

- O primeiro teste impede pin frouxo no repo inteiro.
- O segundo funciona como lembrete de remoção: quando a entrada sumir do
  config, o teste quebra o par com o README.

### 5. Sem mudanças em src/ nem adapters

- `tests/integration/integration_context.py` já zera `config["plugin"]` no
  contexto de integração, então o plugin não contamina a suíte Docker.
- A entry TUI opcional (`opencode-task-model/tui` no `tui.json`) fica fora
  do escopo inicial; picker de subagentes é conveniência, não requisito.

## Fases para o planejamento

### Fase 0 — Revisão de segurança do upstream (barreira, obrigatória)

Regra do repo: import externo exige revisão de TODO o conteúdo copiado.

1. Clonar o upstream em `/tmp/opencode` e fixar o SHA do commit da release
   correspondente ao pin (v1.3.1).
2. Ler TODO o código que roda no processo do OpenCode (`src/`, entrypoints,
   scripts de build/publish) procurando: prompt injection, comandos shell,
   URLs externas, escrita fora do escopo, exfiltração de dados.
3. Conferir o diff entre o SHA revisado e o tarball publicado no npm
   (`npm pack opencode-task-model@1.3.1`), quando aplicável.
4. Registrar em `UPSTREAM.md` (padrão de skills, adaptado para plugin):
   origem, SHA, data da revisão, findings e instruções de sync.
5. Local sugerido: `harness-conf/plugins/opencode-task-model/UPSTREAM.md`.
6. Gate: findings bloqueantes abortam o esboço; findings de risco viram
   mitigação documentada no README ou no AGENTS.base.md.

### Fase 1 — Aplicação

1. Editar `harness-conf/opencode.json` com o pin.
2. Adicionar a seção "Plugins" no README.md.
3. Adicionar a guarda no `harness-conf/AGENTS.base.md`.
4. Criar `tests/test_opencode_plugins.py`.
5. Commit: `feat(harness): adiciona plugin provisorio opencode-task-model`.

### Fase 2 — Validação

1. Suíte completa no ambiente corrente: `.venv/bin/pytest -m all`
   (WSL/Linux) ou `.\.venv\Scripts\pytest.exe -m all` (Windows).
2. Reiniciar o OpenCode e confirmar: plugin carregado, `task` com os args
   novos, precedência nativa preservada sem `model`.
3. Smoke test: spawn com `model` explícito num provider barato e conferir
   o modelo efetivo no child session.

### Fase 3 — Acompanhamento do upstream nativo

1. Observar PR #34947 / issue #6651 no repositório do OpenCode (ou o
   schema https://opencode.ai/config.json ganhando a permissão
   `model_override`).
2. Quando nativo: remover a entrada do plugin, o parágrafo do README, a
   guarda do AGENTS.base.md e revisitar `tests/test_opencode_plugins.py`.
3. Commit de remoção: `chore(harness): remove plugin provisorio
   opencode-task-model (suporte nativo)`.

## Critérios de aceitação

- `harness-conf/opencode.json` com pin exato e JSON válido.
- README e AGENTS.base.md atualizados; teste de pin e de paridade
  README/config passando.
- Suíte completa verde no ambiente alvo.
- `UPSTREAM.md` com SHA revisado e findings registrados.
- Sem mudança de comportamento para agentes que não usam os args novos.

## Riscos e observações

- O plugin sobrescreve a `task` built-in para todos os agentes; a revisão
  de segurança é a barreira principal.
- Reimplementa o spawn via API de client: `@file` e referências de agente
  em prompts delegados vão como texto (guarda no AGENTS.base.md cobre).
- `background: true` libera `bash`/`write`/`edit` no child por padrão;
  deny rules do config valem como kill switch.
- Projeto de mantenedor único, baixa adoção (2 stars); risco de
  abandono mitigado pelo pin e pelo status provisório.
- O `worker.md` mantém `model:` no frontmatter como fallback canônico,
  independente do plugin.
