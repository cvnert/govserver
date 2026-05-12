param(
    [int]$Port = 5173
)

$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path (Join-Path $PSScriptRoot "dist\index.html"))) {
    Write-Error "Built frontend not found. Run 'npm run build' first."
}

$cmd = "Set-Location '$PSScriptRoot'; python -m http.server $Port -d dist --bind 127.0.0.1"
Start-Process -FilePath "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $cmd

Write-Host "Gov RAG frontend started in background on http://127.0.0.1:$Port"
