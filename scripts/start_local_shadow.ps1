<#
Read-only local companion for a Windows Hearthstone client.
It never sends input to Hearthstone and never uploads a raw Power.log.
#>
[CmdletBinding()]
param(
    [string]$PowerLog = "C:\Program Files (x86)\Hearthstone\Logs\Power.log",
    [string]$Python = "python",
    [int]$IntervalSeconds = 5,
    [string]$OutputDirectory = (Join-Path $env:LOCALAPPDATA "LushiAgent\shadow")
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath $PowerLog -PathType Leaf)) {
    throw "Power.log was not found: $PowerLog"
}
if ($IntervalSeconds -lt 2) {
    throw "IntervalSeconds must be at least 2."
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$sanitized = Join-Path $OutputDirectory "live.sanitized.json"
$report = Join-Path $OutputDirectory "live.shadow.json"
$backlog = Join-Path $OutputDirectory "live.shadow.backlog.jsonl"
$lastSignature = ""

Write-Host "Lushi local shadow mode started. Ctrl+C stops it."
Write-Host "Raw log remains on this computer: $PowerLog"
Write-Host "Reports: $OutputDirectory"

while ($true) {
    try {
        $item = Get-Item -LiteralPath $PowerLog
        $signature = "$($item.Length):$($item.LastWriteTimeUtc.Ticks)"
        if ($signature -ne $lastSignature) {
            & $Python "$repo\scripts\import_power_log.py" $PowerLog --output $sanitized
            if ($LASTEXITCODE -ne 0) { throw "Power.log import failed ($LASTEXITCODE)." }
            & $Python "$repo\scripts\shadow_power_log.py" $sanitized --output $report --backlog $backlog
            if ($LASTEXITCODE -ne 0) { throw "Shadow analysis failed ($LASTEXITCODE)." }
            $result = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
            $summary = $result.summary
            Write-Host ("[{0}] games={1}; red={2}; amber={3}; advice={4}" -f `
                (Get-Date -Format "HH:mm:ss"), $result.game_count,
                $summary.red_divergence_count, $summary.amber_divergence_count,
                $summary.action_recommendations_emitted)
            $lastSignature = $signature
        }
    }
    catch {
        Write-Warning $_.Exception.Message
    }
    Start-Sleep -Seconds $IntervalSeconds
}
