param(
    [string]$SessionId = $(Get-Date -Format 'yyyyMMdd-HHmmss'),
    [string]$AgentRole = 'orchestrator',
    [string]$SessionMode = 'execution'
)

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$logsDir = Join-Path $root '.agent-work\telemetry'
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

$traceId = [guid]::NewGuid().ToString()
$fileName = "$SessionId.jsonl"
$outputPath = Join-Path $logsDir $fileName

$event = [ordered]@{
    timestamp_utc = (Get-Date).ToUniversalTime().ToString("o")
    trace_id      = $traceId
    event_type    = 'session_started'
    agent_role    = $AgentRole
    session_mode  = $SessionMode
    session_id    = $SessionId
    message       = 'Telemetry session initialized.'
}

$event | ConvertTo-Json -Compress | Set-Content -LiteralPath $outputPath -Encoding utf8

Write-Output $outputPath
