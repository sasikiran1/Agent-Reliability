# Harness safety check only. Every OS/Docker/HTTP operation below is mocked.
$ErrorActionPreference='Stop'
$runner=Join-Path $PSScriptRoot 'environment_feasibility.ps1'
$original=(Get-Location).Path
$sandbox=Join-Path $original ('data/setup/cleanup-test-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Force $sandbox | Out-Null
$arsMock=@{freeCalls=0;stopCalled=$false}
function Get-CimInstance { $arsMock.freeCalls++; if ($arsMock.freeCalls -eq 1) { [pscustomobject]@{FreePhysicalMemory=3145728} } else { [pscustomobject]@{FreePhysicalMemory=1000000} } }
function Invoke-RestMethod { [pscustomobject]@{success=$true} }
function docker {
    switch ($args[0]) {
        'image' { '[{"RepoDigests":["mock@sha256:not-real"]}]' }
        'run' { 'mock-container-id' }
        'stats' { '{"mock":true}' }
        'inspect' { '{"State":{"Running":false},"mock":true}' }
        'logs' { throw 'deliberately injected log-capture failure' }
        'stop' { $arsMock.stopCalled=$true;'mock-stopped' }
        default { throw 'Unexpected mocked Docker operation' }
    }
    $global:LASTEXITCODE=0
}
$observedError=$null
try {
    Set-Location $sandbox
    try { & $runner | Out-Null } catch { $observedError=$_.Exception.Message }
} finally { Set-Location $original }
$outcome=Get-ChildItem -Path $sandbox -Recurse -Filter outcome.json | Select-Object -First 1
$report=[ordered]@{live_model=$false;real_container_launched=$false;intervention='mocked low RAM and log capture exception';stop_called=$arsMock.stopCalled;outcome_preserved=[bool]$outcome;expected_error=$observedError;passed=($arsMock.stopCalled -and [bool]$outcome -and $observedError -eq 'deliberately injected log-capture failure')}
$report | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $sandbox 'validation.json')
$report | ConvertTo-Json
if (-not $report.passed) { exit 1 }
