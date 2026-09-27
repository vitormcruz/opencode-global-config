# Diagrama C4 L2: containers

O nível 2 mostra os containers definidos pelos entrypoints e pelo pacote
Python. Os destinos dos harnesses aparecem como sistemas externos porque ficam
fora do checkout.

```mermaid
C4Container
    title Containers do opencode-global-config

    Person(humano, "Humano", "Aciona o bootstrap e usa os harnesses.")

    System_Boundary(repo, "opencode-global-config") {
        Container(entrypoints, "Entrypoints de bootstrap", "Bash e PowerShell", "Validam Python e delegam.")
        Container(pacote, "Pacote opencode_config", "Python", "Detecta dependências e aplica adapters.")
        Container(configuracao, "harness-conf", "Markdown e JSON", "Fonte de agents, skills, commands e opencode.json.")
    }

    System_Ext(opencode_destino, "Config global do OpenCode", "~/.config/opencode ou %USERPROFILE%\\.config\\opencode")
    System_Ext(copilot_destino, "Config do Copilot CLI", "~/.copilot ou %USERPROFILE%\\.copilot")
    System_Ext(opencode_runtime, "OpenCode", "Harness consumidor do MCP ai-memory")
    System_Ext(copilot_runtime, "Copilot CLI", "Harness consumidor do MCP ai-memory")
    System_Ext(dependencias, "Dependências locais", "CLIs e runtimes do registro do bootstrap")
    System_Ext(docker, "Docker Engine", "Runtime local do container ai-memory")
    System_Ext(ai_memory, "ai-memory MCP", "Servidor local em 127.0.0.1:49374")
    System_Ext(upstreams, "Repositórios upstream", "Fontes Git de conteúdo externo não confiável")

    Rel(humano, entrypoints, "Executa")
    Rel(entrypoints, pacote, "Delegam a execução")
    Rel(pacote, configuracao, "Lê a fonte canônica")
    Rel(pacote, opencode_destino, "Cria links POSIX ou sincroniza cópia Windows")
    Rel(pacote, copilot_destino, "Sincroniza cópia e referências por perfil")
    Rel(pacote, dependencias, "Detecta e instala")
    Rel(pacote, docker, "Provisiona wrapper, rede internal e container")
    Rel(opencode_runtime, ai_memory, "Consulta MCP após provisionamento")
    Rel(copilot_runtime, ai_memory, "Consulta MCP após provisionamento")
    Rel(pacote, upstreams, "Clona temporariamente para comparar commits")
```
