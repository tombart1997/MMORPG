param([string]$Python = 'C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe')
$ErrorActionPreference = 'Stop'
$venv = Join-Path $PSScriptRoot '.venv'
& $Python -m venv --without-pip $venv
if ($LASTEXITCODE -ne 0) { throw 'Failed to create local Python environment' }
& $Python -m pip --python (Join-Path $venv 'Scripts/python.exe') install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Failed to install MCP dependencies' }
Write-Output 'Run launch.ps1, then connect the MCP stdio server using .venv/Scripts/python.exe server.py.'
