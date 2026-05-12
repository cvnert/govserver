param(
    [int]$Port = 8081
)

$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Python virtual environment not found: $python"
}

$cmd = "Set-Location '$PSScriptRoot'; & '$python' -m uvicorn app.main:app --host 127.0.0.1 --port $Port"
Start-Process -FilePath "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $cmd

Write-Host "Gov RAG started in background on http://127.0.0.1:$Port"
