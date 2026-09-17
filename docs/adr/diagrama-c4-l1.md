# Diagrama C4 L1: contexto do sistema

Este diagrama resume o contexto do `opencode-global-config` a partir das ADRs
0001–0006 e do código existente. O sistema é a fonte canônica das configurações
e do bootstrap dos harnesses instalados.

```mermaid
C4Context
    title Contexto do opencode-global-config

    Person(humano, "Humano", "Mantém a fonte canônica e aciona o bootstrap.")
    System(repo, "opencode-global-config", "Configuração e bootstrap user-space.")
    System_Ext(opencode, "OpenCode", "Harness que consome a configuração global.")
    System_Ext(copilot, "Copilot CLI", "Harness que consome a configuração sincronizada.")
    System_Ext(dependencias, "Dependências locais", "CLIs e runtimes gerenciados.")

    Rel(humano, repo, "Edita artefatos e aciona o bootstrap")
    Rel(humano, opencode, "Usa")
    Rel(humano, copilot, "Usa")
    Rel(repo, opencode, "Materializa a configuração global")
    Rel(repo, copilot, "Sincroniza a configuração")
    Rel(repo, dependencias, "Detecta e provisiona em user-space")
```
