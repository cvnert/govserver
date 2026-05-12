param(
    [int]$Port = 5173
)

$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error "Python is required to serve the built frontend."
}

if (-not (Test-Path (Join-Path $PSScriptRoot "dist\index.html"))) {
    Write-Error "Built frontend not found. Run 'npm run build' first."
}

Write-Host "Starting Gov RAG frontend on http://127.0.0.1:$Port"
python -m http.server $Port -d dist --bind 127.0.0.1
