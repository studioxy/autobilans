$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $root ".venv"

if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
}

$python = Join-Path $venvPath "Scripts\python.exe"

& $python -m pip install --upgrade pip
& $python -m pip install -e "$root[dev]"

Write-Host ""
Write-Host "Setup complete."
Write-Host "Activate with: $venvPath\\Scripts\\Activate.ps1"
Write-Host "Then run:"
Write-Host "  python .\\scripts\\build_dataset_index.py --config .\\config\\local.example.yaml"
Write-Host "  python .\\scripts\\run_local_pipeline.py --config .\\config\\local.example.yaml --company 8spzoo --year 2025"
