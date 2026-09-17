# Diagrama C4 L3: componentes selecionados

O L3 aplica um critério seletivo. Entram somente componentes que concentram
decisões arquiteturais ou complexidade de ambiente: fluxo do bootstrap,
registro e factory de harnesses, strategies por sistema operacional,
materialização, sincronização e persistência de variáveis no Windows.

Wrappers finos, dataclasses, helpers puros repetidos e testes ficam fora. O
diagrama não representa todos os arquivos nem repete componentes padronizados.

```mermaid
C4Component
    title Componentes selecionados do pacote opencode_config

    Container_Boundary(pacote, "Pacote opencode_config") {
        Component(bootstrap_run, "bootstrap.main.run", "Python", "Coordena bootstrap e adapters.")
        Component(dependency_flow, "detect_dependencies + DEPENDENCY_REGISTRY", "Python", "Detecta dependências por ambiente.")
        Component(harness_factory, "criar_adapters + HARNESSES", "Python", "Seleciona harnesses e injeta strategies.")
        Component(opencode_adapter, "OpenCodeAdapter", "Python", "Aplica a configuração do OpenCode.")
        Component(opencode_strategy, "OpenCodePosix + OpenCodeWindows", "Python", "Materializa a configuração por SO.")
        Component(copilot_adapter, "CopilotAdapter", "Python", "Sincroniza a configuração do Copilot CLI.")
        Component(sync_lib, "lib.sync", "Python", "Copia, faz backup, remove e cria symlink.")
        Component(windows_env, "lib.windows_env", "Python", "Persiste HKCU\\Environment e notifica o Explorer.")
    }

    Rel(bootstrap_run, dependency_flow, "Detecta dependências")
    Rel(bootstrap_run, harness_factory, "Seleciona e aplica")
    Rel(harness_factory, opencode_adapter, "Cria")
    Rel(harness_factory, copilot_adapter, "Cria")
    Rel(opencode_adapter, opencode_strategy, "Delega materialização")
    Rel(opencode_adapter, sync_lib, "Usa para backup e sincronização")
    Rel(opencode_adapter, windows_env, "Usa no Windows")
    Rel(copilot_adapter, sync_lib, "Usa para cópia e backup")
```
