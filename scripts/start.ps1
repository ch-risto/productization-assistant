param([string]$Python = '')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
if (!$Python) { $Python = Join-Path $projectRoot '.venv/Scripts/python.exe' }
if (!(Test-Path -LiteralPath $Python)) { throw 'Luo ensin .venv README-ohjeen mukaan tai anna -Python polku/python.exe.' }
& $Python scripts/seed.py
if ($LASTEXITCODE -ne 0) { throw 'Aineiston validointi epäonnistui.' }
& $Python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1
