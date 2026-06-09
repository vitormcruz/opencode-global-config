#Requires -Version 5.1
<#
.SYNOPSIS
    Sincroniza configuracoes do opencode-config para o GitHub Copilot (Windows).

.DESCRIPTION
    Copia e converte agents, skills, commands para os destinos globais do
    Copilot, e sincroniza .github\copilot-specific.instructions.md para as
    instructions globais em .copilot\instructions.

.PARAMETER Yes
    Executa sem pedir confirmacao.

.PARAMETER Help
    Exibe esta ajuda.

.PARAMETER DestRoot
    Substitui o diretorio raiz de destino (usado em testes automatizados).
    Quando definido, os destinos passam a ser:
      $DestRoot\.copilot\skills\
      $DestRoot\.copilot\instructions\
      $DestRoot\AppData\Roaming\Code\User\prompts\
      $DestRoot\AppData\Roaming\Code\User\mcp.json

.EXAMPLE
    .\scripts\bootstrap_repo\copilot-sync.ps1 -Yes
#>
[CmdletBinding()]
param(
    [switch]$Yes,
    [switch]$Help,
    [string]$DestRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ──────────────────────────────────────────────────────────────
# Ajuda
# ──────────────────────────────────────────────────────────────

function Show-Usage {
    Write-Host @"
copilot-sync.ps1

Copia e converte configuracoes do opencode-config para o GitHub Copilot (Windows).

Uso:
  .\scripts\bootstrap_repo\copilot-sync.ps1 [-Yes]

Opcoes:
  -Yes      Nao pergunta confirmacao
  -Help     Mostra esta ajuda

O que e sincronizado:
  skills\*\         -> %USERPROFILE%\.copilot\skills\
  agents\*.md       -> %APPDATA%\Code\User\prompts\*.agent.md
  commands\*.md     -> %APPDATA%\Code\User\prompts\*.prompt.md
  copilot-instrs    -> %USERPROFILE%\.copilot\instructions\copilot-specific.instructions.md
  MCPs (exa,crawl4ai) -> %APPDATA%\Code\User\mcp.json
  MCPs CLI (crawl4ai,codebase-memory,doctree) -> %USERPROFILE%\.config\mcp\servers.json
"@
}

if ($Help) {
    Show-Usage
    exit 0
}

# ──────────────────────────────────────────────────────────────
# Caminhos
# ──────────────────────────────────────────────────────────────

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path

if ($DestRoot) {
    $SkillsDir       = Join-Path $DestRoot ".copilot\skills"
    $InstructionsDir = Join-Path $DestRoot ".copilot\instructions"
    $PromptsDir      = Join-Path $DestRoot "AppData\Roaming\Code\User\prompts"
    $McpJson         = Join-Path $DestRoot "AppData\Roaming\Code\User\mcp.json"
    $McpServersJson  = Join-Path $DestRoot ".config\mcp\servers.json"
    $BackupRoot      = Join-Path $DestRoot "copilot-backup"
} else {
    $SkillsDir       = Join-Path $env:USERPROFILE ".copilot\skills"
    $InstructionsDir = Join-Path $env:USERPROFILE ".copilot\instructions"
    $PromptsDir      = Join-Path $env:APPDATA "Code\User\prompts"
    $McpJson         = Join-Path $env:APPDATA "Code\User\mcp.json"
    $McpServersJson  = Join-Path $env:USERPROFILE ".config\mcp\servers.json"
    $BackupRoot      = Join-Path $env:USERPROFILE ".config\copilot-backup"
}

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupDir = Join-Path $BackupRoot $Timestamp

# ──────────────────────────────────────────────────────────────
# Utilitarios
# ──────────────────────────────────────────────────────────────

function Say([string]$Msg) { Write-Host $Msg }

# UTF-8 sem BOM — necessario para YAML/frontmatter ser lido corretamente
$Utf8NoBom = New-Object System.Text.UTF8Encoding $false
function Write-Utf8NoBom([string]$Path, [string]$Content) {
    [System.IO.File]::WriteAllText($Path, $Content, $Utf8NoBom)
}

function Ensure-Dir([string]$Path) {
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Backup-IfExists([string]$Path) {
    if (-not (Test-Path $Path)) { return }
    Ensure-Dir $BackupDir
    $base = Join-Path $BackupDir (Split-Path -Leaf $Path)
    $out  = $base
    $i    = 1
    while (Test-Path $out) {
        $out = "$base.$i"
        $i++
    }
    Copy-Item -Path $Path -Destination $out -Recurse -Force
}

function ConvertTo-WslPath([string]$WinPath) {
    $p = $WinPath.Replace('\', '/')
    if ($p -match '^([A-Za-z]):(.*)') {
        return "/mnt/$($Matches[1].ToLower())$($Matches[2])"
    }
    return $p
}

function Confirm-Action {
    if ($Yes) { return }
    $ans = Read-Host "Aplicar estas alteracoes? [y/N]"
    if ($ans -notmatch '^[yY]') {
        Say "Cancelado."
        exit 1
    }
}

# ──────────────────────────────────────────────────────────────
# Strip-AgentFrontmatter
# Mantem apenas 'description' do frontmatter YAML.
# ──────────────────────────────────────────────────────────────

function Strip-AgentFrontmatter([string]$Content) {
    $lines   = $Content -split "`n"
    $inFm    = $false
    $fmDone  = $false
    $desc    = ""
    $cont    = ""
    $body    = [System.Collections.Generic.List[string]]::new()

    foreach ($line in $lines) {
        if ($line -match '^---\s*$') {
            if (-not $fmDone) {
                if (-not $inFm) { $inFm = $true; continue }
                else            { $fmDone = $true; continue }
            }
        }
        if ($inFm -and -not $fmDone) {
            if ($line -match '^description:') {
                $desc = $line; $cont = "desc"
            } elseif ($line -match '^  ' -and $cont -eq "desc") {
                $desc += "`n$line"
            } else {
                $cont = "other"
            }
            continue
        }
        if ($fmDone) { $body.Add($line) }
    }

    return "---`n$desc`n---`n" + ($body -join "`n")
}

# ──────────────────────────────────────────────────────────────
# Filter-AgentsMd
# Remove secoes OpenCode-especificas do AGENTS.md.
# ──────────────────────────────────────────────────────────────

function Filter-AgentsMd([string]$Content) {
    $removeHeadings = @(
        'Atalho: "configure este repo"',
        'Configuracao Global via Links Simbolicos',
        'Configuracao Global via Links Simbolicos',
        'Upstream de Skills Externas',
        'Manutencao de Upstream',
        'Manutencao de Upstream'
    )

    $lines          = $Content -split "`n"
    $result         = [System.Collections.Generic.List[string]]::new()
    $skipUntilLevel = 0

    foreach ($line in $lines) {
        $level = 0
        if ($line -match '^(#{1,6})\s') { $level = $Matches[1].Length }

        if ($skipUntilLevel -gt 0) {
            if ($level -gt 0 -and $level -le $skipUntilLevel) {
                $skipUntilLevel = 0
            } else {
                continue
            }
        }

        if ($level -gt 0) {
            $heading = $line -replace '^#{1,6}\s+', ''
            foreach ($r in $removeHeadings) {
                if ($heading -like "*$r*") {
                    $skipUntilLevel = $level
                    break
                }
            }
            if ($skipUntilLevel -gt 0) { continue }
        }

        $result.Add($line)
    }

    return $result -join "`n"
}

# ──────────────────────────────────────────────────────────────
# Rewrite-ScriptRefs
# Copia scripts referenciados no SKILL.md e reescreve os
# caminhos para usar 'wsl bash' ou 'wsl python'.
# ──────────────────────────────────────────────────────────────

function Rewrite-ScriptRefs([string]$SkillName, [string]$SkillDest) {
    $skillMd = Join-Path $SkillDest "SKILL.md"
    if (-not (Test-Path $skillMd)) { return }

    $original    = Get-Content $skillMd -Raw -Encoding UTF8
    $content     = $original
    $scriptsDest = Join-Path $SkillDest "scripts"
    $wslBase     = ConvertTo-WslPath $scriptsDest

    # Padrao 1: ~/.config/opencode/scripts/<nome>
    $pattern1 = [regex]'~/.config/opencode/scripts/(\S+)'
    foreach ($m in $pattern1.Matches($content)) {
        $name    = $m.Groups[1].Value
        $srcPath = Join-Path $RepoRoot "scripts\$name"
        if (Test-Path $srcPath) {
            Ensure-Dir $scriptsDest
            Copy-Item $srcPath (Join-Path $scriptsDest $name) -Force
            $wslPath = "$wslBase/$name"
            $content = $content.Replace("~/.config/opencode/scripts/$name", "wsl bash $wslPath")
        }
    }

    # Padrao 2: ./scripts/<arquivo>
    $pattern2 = [regex]'\./scripts/(\S+)'
    foreach ($m in $pattern2.Matches($content)) {
        $fileName = $m.Groups[1].Value
        $srcPath  = Join-Path $RepoRoot "skills\$SkillName\scripts\$fileName"
        if (Test-Path $srcPath) {
            Ensure-Dir $scriptsDest
            Copy-Item $srcPath (Join-Path $scriptsDest $fileName) -Force
            $ext     = [System.IO.Path]::GetExtension($fileName)
            $wslPath = "$wslBase/$fileName"
            $cmd     = if ($ext -eq ".py") { "wsl python $wslPath" } else { "wsl bash $wslPath" }
            $content = $content.Replace("./scripts/$fileName", $cmd)
        }
    }

    if ($content -ne $original) {
        Write-Utf8NoBom $skillMd $content
    }
}

# ──────────────────────────────────────────────────────────────
# Adapt-SkillForCopilot
# Aplica adaptacoes especificas por skill ao SKILL.md copiado.
# Atualmente: web-research-exa-crawl4ai substitui 'websearch'
# pela tool real do Exa MCP (web_search_exa).
# ──────────────────────────────────────────────────────────────

function Adapt-SkillForCopilot([string]$SkillName, [string]$SkillDest) {
    if ($SkillName -ne "web-research-exa-crawl4ai") { return }

    $skillMd = Join-Path $SkillDest "SKILL.md"
    if (-not (Test-Path $skillMd)) { return }

    $original = Get-Content $skillMd -Raw -Encoding UTF8
    # Substitui referencias a 'websearch' pela tool do Exa MCP.
    # 'websearch/Exa' -> 'web_search_exa' (remove o sufixo /Exa redundante)
    $content  = $original -replace '`websearch/Exa`', '`web_search_exa`'
    $content  = $content  -replace 'websearch/Exa',   'web_search_exa'
    $content  = $content  -replace '`websearch`',     '`web_search_exa`'
    $content  = $content  -replace '\bwebsearch\b',   'web_search_exa'

    if ($content -ne $original) {
        Write-Utf8NoBom $skillMd $content
    }
}

function Sync-Skills {
    Say ""
    Say "--- Skills ---"
    Ensure-Dir $SkillsDir
    $count = 0

    foreach ($skillSrc in Get-ChildItem -Path (Join-Path $RepoRoot "skills") -Directory) {
        $skillMd = Join-Path $skillSrc.FullName "SKILL.md"
        if (-not (Test-Path $skillMd)) { continue }

        $dest = Join-Path $SkillsDir $skillSrc.Name
        Backup-IfExists $dest
        if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
        Copy-Item -Path $skillSrc.FullName -Destination $dest -Recurse -Force

        Rewrite-ScriptRefs $skillSrc.Name $dest
        Adapt-SkillForCopilot $skillSrc.Name $dest
        Say "OK    $($skillSrc.Name)"
        $count++
    }

    Say "      $count skill(s) sincronizada(s)"
}

# ──────────────────────────────────────────────────────────────
# Sync-Agents
# ──────────────────────────────────────────────────────────────

function Sync-Agents {
    Say ""
    Say "--- Agents ---"
    Ensure-Dir $PromptsDir
    $count = 0

    foreach ($agentSrc in Get-ChildItem -Path (Join-Path $RepoRoot "agents") -Filter "*.md") {
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($agentSrc.Name)
        $dest     = Join-Path $PromptsDir "$baseName.agent.md"
        Backup-IfExists $dest

        $raw       = Get-Content $agentSrc.FullName -Raw -Encoding UTF8
        $converted = Strip-AgentFrontmatter $raw
        Write-Utf8NoBom $dest $converted

        Say "OK    $baseName.agent.md"
        $count++
    }

    Say "      $count agent(s) sincronizado(s)"
}

# ──────────────────────────────────────────────────────────────
# Sync-Commands
# ──────────────────────────────────────────────────────────────

function Sync-Commands {
    Say ""
    Say "--- Commands ---"
    Ensure-Dir $PromptsDir
    $count = 0

    foreach ($cmdSrc in Get-ChildItem -Path (Join-Path $RepoRoot "commands") -Filter "*.md") {
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($cmdSrc.Name)
        $dest     = Join-Path $PromptsDir "$baseName.prompt.md"
        Backup-IfExists $dest
        Copy-Item -Path $cmdSrc.FullName -Destination $dest -Force
        Say "OK    $baseName.prompt.md"
        $count++
    }

    Say "      $count command(s) sincronizado(s)"
}

# ──────────────────────────────────────────────────────────────
# Sync-Instructions
# ──────────────────────────────────────────────────────────────

function Sync-Instructions {
    Say ""
    Say "--- Instructions ---"

    $source = Join-Path $RepoRoot ".github\copilot-specific.instructions.md"

    if (-not (Test-Path $source)) {
        Say "AVISO .github/copilot-specific.instructions.md nao encontrado"
        return
    }

    $dest = Join-Path $InstructionsDir "copilot-specific.instructions.md"

    Ensure-Dir (Split-Path -Parent $dest)
    Backup-IfExists $dest

    Copy-Item -Path $source -Destination $dest -Force
    Say "OK    copilot-specific.instructions.md (user global)"
}

# ──────────────────────────────────────────────────────────────
# Sync-Mcp
# ──────────────────────────────────────────────────────────────

function Sync-Mcp {
    Say ""
    Say "--- MCP ---"
    Ensure-Dir (Split-Path -Parent $McpJson)
    Backup-IfExists $McpJson

    $newServers = @{
        "exa" = [ordered]@{
            "command" = "npx"
            "args"    = @("-y", "exa-mcp-server")
        }
        "crawl4ai" = [ordered]@{
            "type" = "sse"
            "url"  = "http://localhost:11235/mcp/sse"
        }
    }

    if (Test-Path $McpJson) {
        try   { $data = Get-Content $McpJson -Raw | ConvertFrom-Json }
        catch { $data = [PSCustomObject]@{ servers = [PSCustomObject]@{} } }
    } else {
        $data = [PSCustomObject]@{ servers = [PSCustomObject]@{} }
    }

    if (-not @($data.PSObject.Properties | Where-Object { $_.Name -eq "servers" }).Count) {
        $data | Add-Member -MemberType NoteProperty -Name "servers" -Value ([PSCustomObject]@{})
    }

    $added = @()
    $updated = @()
    foreach ($key in $newServers.Keys) {
        $existing = $data.servers.PSObject.Properties[$key]
        if (-not $existing) {
            $data.servers | Add-Member -MemberType NoteProperty -Name $key -Value $newServers[$key]
            $added += $key
        } else {
            $currentJson = ($existing.Value | ConvertTo-Json -Depth 10 -Compress)
            $expectedJson = ($newServers[$key] | ConvertTo-Json -Depth 10 -Compress)
            if ($currentJson -ne $expectedJson) {
                $data.servers.PSObject.Properties.Remove($key)
                $data.servers | Add-Member -MemberType NoteProperty -Name $key -Value $newServers[$key]
                $updated += $key
            }
        }
    }

    $data | ConvertTo-Json -Depth 10 | Set-Content -Path $McpJson -Encoding UTF8

    return [PSCustomObject]@{
        Added = $added
        Updated = $updated
    }
}

function Sync-McpCli {
    Ensure-Dir (Split-Path -Parent $McpServersJson)
    Backup-IfExists $McpServersJson

    $newServers = @{
        "crawl4ai" = [ordered]@{
            "type" = "sse"
            "url"  = "http://localhost:11235/mcp/sse"
        }
        "codebase-memory" = [ordered]@{
            "command" = "codebase-memory-mcp"
            "args"    = @()
        }
        "doctree" = [ordered]@{
            "command" = "doctree-run"
            "args"    = @()
        }
    }

    if (Test-Path $McpServersJson) {
        try   { $data = Get-Content $McpServersJson -Raw | ConvertFrom-Json }
        catch { $data = [PSCustomObject]@{ servers = [PSCustomObject]@{} } }
    } else {
        $data = [PSCustomObject]@{ servers = [PSCustomObject]@{} }
    }

    if (-not @($data.PSObject.Properties | Where-Object { $_.Name -eq "servers" }).Count) {
        $data | Add-Member -MemberType NoteProperty -Name "servers" -Value ([PSCustomObject]@{})
    }

    $added = @()
    $updated = @()
    foreach ($key in $newServers.Keys) {
        $existing = $data.servers.PSObject.Properties[$key]
        if (-not $existing) {
            $data.servers | Add-Member -MemberType NoteProperty -Name $key -Value $newServers[$key]
            $added += $key
        } else {
            $currentJson = ($existing.Value | ConvertTo-Json -Depth 10 -Compress)
            $expectedJson = ($newServers[$key] | ConvertTo-Json -Depth 10 -Compress)
            if ($currentJson -ne $expectedJson) {
                $data.servers.PSObject.Properties.Remove($key)
                $data.servers | Add-Member -MemberType NoteProperty -Name $key -Value $newServers[$key]
                $updated += $key
            }
        }
    }

    $data | ConvertTo-Json -Depth 10 | Set-Content -Path $McpServersJson -Encoding UTF8

    return [PSCustomObject]@{
        Added = $added
        Updated = $updated
    }
}

# ──────────────────────────────────────────────────────────────
# Show-Plan / Main
# ──────────────────────────────────────────────────────────────

function Show-Plan {
    $nSkills   = @(Get-ChildItem -Path (Join-Path $RepoRoot "skills") -Directory |
                   Where-Object { Test-Path (Join-Path $_.FullName "SKILL.md") }).Count
    $nAgents   = @(Get-ChildItem -Path (Join-Path $RepoRoot "agents") -Filter "*.md").Count
    $nCommands = @(Get-ChildItem -Path (Join-Path $RepoRoot "commands") -Filter "*.md").Count

    Say "Repo:         $RepoRoot"
    Say "Skills:       $SkillsDir"
    Say "Instructions: $InstructionsDir"
    Say "Prompts:      $PromptsDir"
    Say "MCP:          $McpJson"
    Say "MCP CLI:      $McpServersJson"
    Say ""
    Say "Plano:"
    Say "  - Copiar $nSkills skill(s) para .copilot\skills\"
    Say "  - Converter $nAgents agent(s) para .agent.md"
    Say "  - Copiar $nCommands command(s) para .prompt.md"
    Say "  - Copiar .github/copilot-specific.instructions.md para .copilot\\instructions\\"
    Say "  - Configurar MCPs Copilot (exa, crawl4ai) em mcp.json"
    Say "  - Configurar MCPs CLI (crawl4ai, codebase-memory, doctree) em servers.json"
}

Show-Plan
Confirm-Action
Sync-Skills
Sync-Agents
Sync-Commands
Sync-Instructions
$mcpResult = Sync-Mcp
if ($mcpResult.Added.Count -gt 0 -or $mcpResult.Updated.Count -gt 0) {
    Say "OK    mcp.json (add: $((@($mcpResult.Added) -join ', ') -replace '^$', 'nenhum'); update: $((@($mcpResult.Updated) -join ', ') -replace '^$', 'nenhum'))"
} else {
    Say "OK    mcp.json (sem alteracoes necessarias)"
}
$mcpCliResult = Sync-McpCli
if ($mcpCliResult.Added.Count -gt 0 -or $mcpCliResult.Updated.Count -gt 0) {
    Say "OK    servers.json (add: $((@($mcpCliResult.Added) -join ', ') -replace '^$', 'nenhum'); update: $((@($mcpCliResult.Updated) -join ', ') -replace '^$', 'nenhum'))"
} else {
    Say "OK    servers.json (sem alteracoes necessarias)"
}
Say ""
Say "Pronto."
