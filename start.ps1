param(
    [int]$Port = 8081
)

$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Python virtual environment not found: $python"
}

Write-Host "Starting Gov RAG on http://127.0.0.1:$Port"
& $python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
