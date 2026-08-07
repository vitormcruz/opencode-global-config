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
      $DestRoot\.copilot\agents\

.EXAMPLE
    .\adapters\copilot-cli\copilot-cli-adapter.ps1 -Yes
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
copilot-cli-adapter.ps1

Copia e converte configuracoes do opencode-config para o GitHub Copilot (Windows).

Uso:
  .\adapters\copilot-cli\copilot-cli-adapter.ps1 [-Yes]

Opcoes:
  -Yes      Nao pergunta confirmacao
  -Help     Mostra esta ajuda

  O que e sincronizado:
   skills\*\         -> %USERPROFILE%\.copilot\skills\
  agents\*.md       -> %USERPROFILE%\.copilot\agents\*.agent.md
  commands\*.md     -> %USERPROFILE%\.copilot\skills\*\SKILL.md
  default-artifacts -> %USERPROFILE%\.copilot\agents\default-artifacts\
  copilot-instrs    -> %USERPROFILE%\.copilot\instructions\copilot-specific.instructions.md
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
    $AgentsDir       = Join-Path $DestRoot ".copilot\agents"
    $BackupRoot      = Join-Path $DestRoot "copilot-backup"
} else {
    $SkillsDir       = Join-Path $env:USERPROFILE ".copilot\skills"
    $InstructionsDir = Join-Path $env:USERPROFILE ".copilot\instructions"
    $AgentsDir       = Join-Path $env:USERPROFILE ".copilot\agents"
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
# Convert-AgentFrontmatter
# Traduz o frontmatter OpenCode para o formato do Copilot CLI.
# ──────────────────────────────────────────────────────────────

function Convert-AgentFrontmatter([string]$Content) {
    $lines = $Content -split "`n"
    if ($lines.Count -lt 2 -or $lines[0].Trim() -ne '---') { return $Content }
    $end = -1
    for ($i = 1; $i -lt $lines.Count; $i++) {
        if ($lines[$i].Trim() -eq '---') { $end = $i; break }
    }
    if ($end -lt 0) { return $Content }

    $descLines = [System.Collections.Generic.List[string]]::new()
    $inDescription = $false
    $permission = @{}
    $currentPermission = ""
    $mode = ""
    for ($i = 1; $i -lt $end; $i++) {
        $line = $lines[$i]
        if ($line -match '^description:') {
            $descLines.Add($line); $inDescription = $true; continue
        }
        if ($inDescription -and ($line.StartsWith(' ') -or [string]::IsNullOrWhiteSpace($line))) {
            $descLines.Add($line); continue
        }
        $inDescription = $false
        if ($line -match '^mode:\s*(\S+)') { $mode = $Matches[1]; continue }
        if ($line -match '^  (edit|bash|webfetch|websearch|task):\s*(.*)$') {
            $currentPermission = $Matches[1]
            $permission[$currentPermission] = $Matches[2].Trim().ToLowerInvariant()
            continue
        }
        if ($currentPermission -eq 'task' -and $line -match '^\s{4}') {
            $permission['task'] = $line.Trim().ToLowerInvariant()
        }
    }

    $tools = [System.Collections.Generic.List[string]]::new()
    $tools.Add('read')
    if ($permission['edit'] -eq 'allow') { $tools.Add('edit') }
    if ($permission['bash'] -eq 'allow') { $tools.Add('execute') }
    $tools.Add('search')
    if ($permission['webfetch'] -eq 'allow' -or $permission['websearch'] -eq 'allow') {
        $tools.Add('web')
    }
    if ($permission['task'] -like '*allow*') { $tools.Add('agent') }
    if ($descLines.Count -eq 0) {
        $descLines.Add('description: Agent OpenCode convertido para Copilot CLI')
    }

    $result = [System.Collections.Generic.List[string]]::new()
    $result.Add('---')
    foreach ($line in $descLines) { $result.Add($line) }
    $quotedTools = ($tools | ForEach-Object { '"' + $_ + '"' }) -join ', '
    $result.Add("tools: [$quotedTools]")
    if ($mode -eq 'subagent') { $result.Add('user-invocable: false') }
    $result.Add('---')
    for ($i = $end + 1; $i -lt $lines.Count; $i++) { $result.Add($lines[$i]) }
    return $result -join "`n"
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
    $skillMd = Join-Path $SkillDest "SKILL.md"
    if (-not (Test-Path $skillMd)) { return }

    $original = Get-Content $skillMd -Raw -Encoding UTF8
    $content = $original
    $lines = $original -split "`r?`n"
    if ($SkillName -notmatch '^[a-z0-9]+(?:-[a-z0-9]+)*$' -or $SkillName.Length -gt 64) {
        throw "Nome de skill invalido: $SkillName"
    }
    if ($lines.Count -eq 0 -or $lines[0].Trim() -ne '---') {
        $paragraph = [System.Collections.Generic.List[string]]::new()
        $started = $false
        foreach ($line in $lines) {
            if ([string]::IsNullOrWhiteSpace($line)) {
                if ($started) { break }
                continue
            }
            if (-not $started -and $line.TrimStart().StartsWith('#')) { continue }
            $started = $true
            $paragraph.Add($line.Trim())
        }
        $description = (($paragraph -join ' ') -replace '\s+', ' ').Trim()
        if ([string]::IsNullOrWhiteSpace($description)) { $description = "Skill $SkillName." }
        if ($description.Length -gt 1024) { $description = $description.Substring(0, 1024) }
        $content = "---`nname: $SkillName`ndescription: $description`n---`n`n" + $original.TrimEnd() + "`n"
    } else {
        $end = -1
        for ($i = 1; $i -lt $lines.Count; $i++) {
            if ($lines[$i].Trim() -eq '---') { $end = $i; break }
        }
        if ($end -lt 0) { throw "Frontmatter invalido: $skillMd" }
        $nameLine = $lines | Where-Object { $_ -match '^name:\s*(\S+)\s*$' } | Select-Object -First 1
        if ($nameLine) {
            $existingName = ([regex]::Match($nameLine, '^name:\s*(\S+)\s*$')).Groups[1].Value
            if ($existingName -ne $SkillName) { throw "name nao corresponde ao diretorio: $skillMd" }
        } else {
            $lines = @($lines[0], "name: $SkillName") + $lines[1..($lines.Count - 1)]
            $content = $lines -join "`n"
        }
        if (-not $content) { $content = $original }
    }
    # Substitui referencias a 'websearch' pela tool do Exa MCP.
    # 'websearch/Exa' -> 'web_search_exa' (remove o sufixo /Exa redundante)
    $content  = $content  -replace '`websearch/Exa`', '`web_search_exa`'
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
    Ensure-Dir $AgentsDir
    $count = 0

    foreach ($agentSrc in Get-ChildItem -Path (Join-Path $RepoRoot "agents") -Filter "*.md") {
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($agentSrc.Name)
        $dest     = Join-Path $AgentsDir "$baseName.agent.md"
        Backup-IfExists $dest

        $raw       = Get-Content $agentSrc.FullName -Raw -Encoding UTF8
        $converted = Convert-AgentFrontmatter $raw
        Write-Utf8NoBom $dest $converted

        Say "OK    $baseName.agent.md"
        $count++
    }

    Say "      $count agent(s) sincronizado(s)"
}

# ──────────────────────────────────────────────────────────────
# Sync-CommandsAsSkills
# ──────────────────────────────────────────────────────────────

function Sync-CommandsAsSkills {
    Say ""
    Say "--- Commands ---"
    Ensure-Dir $SkillsDir
    $count = 0

    foreach ($cmdSrc in Get-ChildItem -Path (Join-Path $RepoRoot "commands") -Filter "*.md") {
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($cmdSrc.Name)
        $dest     = Join-Path $SkillsDir $baseName
        Backup-IfExists $dest
        if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
        Ensure-Dir $dest
        switch ($baseName) {
            "index-codebase" { $description = "Indexa repo no codebase-memory. Ative quando humano pedir index codebase ou indexar repositorio." }
            "bench-indexing" { $description = "Benchmark de indexacao codebase-memory. Ative quando humano pedir bench indexing." }
            "sync-upstream-skills" { $description = "Sincroniza skills com upstream. Ative quando humano pedir sync upstream skills." }
            default { $description = "Executa o comando $baseName." }
        }
        $raw = Get-Content $cmdSrc.FullName -Raw -Encoding UTF8
        $body = $raw
        if ($raw -match '^---\s*\r?\n') {
            $body = $raw -replace '(?s)^---\s*\r?\n.*?\r?\n---\s*\r?\n', ''
        }
        $skillContent = "---`nname: $baseName`ndescription: $description`n---`n`n$($body.TrimEnd())`n"
        Write-Utf8NoBom (Join-Path $dest "SKILL.md") $skillContent
        Say "OK    $baseName/SKILL.md"
        $count++
    }

    Say "      $count command(s) convertido(s) em skills"
}

# ──────────────────────────────────────────────────────────────
# Sync-Instructions
# ──────────────────────────────────────────────────────────────

function Sync-DefaultArtifacts {
    Say ""
    Say "--- Default Artifacts ---"

    $src = Join-Path $RepoRoot "agents\default-artifacts"

    if (-not (Test-Path $src)) {
        Say "AVISO agents\default-artifacts nao encontrado"
        return
    }

    Ensure-Dir $AgentsDir
    $dest = Join-Path $AgentsDir "default-artifacts"
    Backup-IfExists $dest
    if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
    Copy-Item -Path $src -Destination $dest -Recurse -Force

    $n = @(Get-ChildItem -Path $dest -File -Recurse).Count
    Say "OK    default-artifacts ($n arquivo(s))"
}

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
    Say "Agents:       $AgentsDir"
    Say ""
    Say "Plano:"
    Say "  - Copiar $nSkills skill(s) para .copilot\skills\"
    Say "  - Converter $nAgents agent(s) para .agent.md"
    Say "  - Converter $nCommands command(s) em skills"
    Say "  - Copiar .github/copilot-specific.instructions.md para .copilot\\instructions\\"
    Say "  - Copiar agents\default-artifacts para .copilot\agents\default-artifacts"
}

Show-Plan
Confirm-Action
Sync-Skills
Sync-Agents
Sync-CommandsAsSkills
Sync-DefaultArtifacts
Sync-Instructions
Say ""
Say "Pronto."
