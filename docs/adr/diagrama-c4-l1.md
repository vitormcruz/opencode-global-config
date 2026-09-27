# Diagrama C4 L1: contexto do sistema

Este diagrama resume o contexto do `opencode-global-config` a partir das ADRs
0001–0009 e do código existente. O sistema é a fonte canônica das configurações
e do bootstrap dos harnesses instalados.

```mermaid
C4Context
    title Contexto do opencode-global-config

    Person(humano, "Humano", "Mantém a fonte canônica e aciona o bootstrap.")
    System(repo, "opencode-global-config", "Configuração e bootstrap user-space.")
    System_Ext(opencode, "OpenCode", "Harness que consome a configuração global.")
    System_Ext(copilot, "Copilot CLI", "Harness que consome a configuração sincronizada.")
    System_Ext(ai_memory, "ai-memory", "Servidor MCP local em container Docker.")
    System_Ext(dependencias, "Dependências locais", "CLIs e runtimes gerenciados.")
    System_Ext(upstreams, "Repositórios upstream", "Fontes Git de conteúdo externo não confiável.")

    Rel(humano, repo, "Edita artefatos e aciona o bootstrap")
    Rel(humano, opencode, "Usa")
    Rel(humano, copilot, "Usa")
    Rel(repo, opencode, "Materializa a configuração global")
    Rel(repo, copilot, "Sincroniza a configuração")
    Rel(repo, dependencias, "Detecta e provisiona em user-space")
    Rel(opencode, ai_memory, "Consulta MCP quando o provisionamento termina")
    Rel(copilot, ai_memory, "Consulta MCP quando o provisionamento termina")
    Rel(repo, ai_memory, "Provisiona com bind de loopback e rede internal")
    Rel(repo, upstreams, "Detecta diferenças sem aplicar conteúdo")
    Rel(repo, humano, "Apresenta diferenças para decisão")
```
