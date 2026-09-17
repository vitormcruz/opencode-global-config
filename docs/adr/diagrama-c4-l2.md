# Diagrama C4 L2: containers

O nível 2 mostra os containers definidos pelos entrypoints e pelo pacote
Python. Os destinos dos harnesses aparecem como sistemas externos porque ficam
fora do checkout.

```mermaid
C4Container
    title Containers do opencode-global-config

    Person(humano, "Humano", "Aciona o bootstrap e usa os harnesses.")

    System_Boundary(repo, "opencode-global-config") {
        Container(entrypoints, "Entrypoints de bootstrap", "Bash e PowerShell", "Validam Python e delegam ao bootstrap.")
        Container(pacote, "Pacote opencode_config", "Python", "Detecta dependências e aplica adapters.")
        Container(configuracao, "harness-conf", "Markdown e JSON", "Fonte de agents, skills, commands e opencode.json.")
    }

    System_Ext(opencode_destino, "Config global do OpenCode", "~/.config/opencode ou %USERPROFILE%\\.config\\opencode")
    System_Ext(copilot_destino, "Config do Copilot CLI", "~/.copilot ou %USERPROFILE%\\.copilot")
    System_Ext(dependencias, "Dependências locais", "CLIs e runtimes do registro do bootstrap")

    Rel(humano, entrypoints, "Executa")
    Rel(entrypoints, pacote, "Delegam a execução")
    Rel(pacote, configuracao, "Lê a fonte canônica")
    Rel(pacote, opencode_destino, "Cria links POSIX ou sincroniza cópia Windows")
    Rel(pacote, copilot_destino, "Sincroniza cópia")
    Rel(pacote, dependencias, "Detecta e instala")
```
