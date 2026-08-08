[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$python = Get-Command python -ErrorAction SilentlyContinue

if ($null -eq $python) {
    Write-Error "Python 3.10+ nao encontrado. Instale Python por usuario."
    exit 1
}

& $python.Source -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python encontrado, mas a versao minima e 3.10."
    exit 1
}

$env:PYTHONPATH = "$repoRoot\src;$env:PYTHONPATH"
& $python.Source -m opencode_config.bootstrap.main --repo-root $repoRoot @Arguments
exit $LASTEXITCODE
