param(
    [string]$Blender = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe',
    [string]$BlendFile = ''
)
$ErrorActionPreference = 'Stop'
$workflow = $PSScriptRoot
$python = Join-Path $workflow '.venv/Scripts/python.exe'
$runtime = Join-Path $workflow 'runtime'
New-Item -ItemType Directory -Force $runtime | Out-Null
$listener = Get-NetTCPConnection -LocalPort 9877 -State Listen -ErrorAction SilentlyContinue
if ($listener) { throw 'Port 9877 is already in use. Reuse the existing studio or close its Blender instance first.' }
& $python -c 'import pathlib,secrets,sys; pathlib.Path(sys.argv[1]).write_text(secrets.token_hex(32))' (Join-Path $runtime 'token')
if ($LASTEXITCODE -ne 0) { throw 'Run setup.ps1 first.' }
$arguments = @('--factory-startup')
if ($BlendFile) { $arguments += ('"' + (Resolve-Path -LiteralPath $BlendFile).Path + '"') }
$arguments += @('--python', ('"' + (Join-Path $workflow 'bridge.py') + '"'))
$previousResources = $env:BLENDER_USER_RESOURCES
try {
    $env:BLENDER_USER_RESOURCES = Join-Path $runtime 'blender_user'
    $process = Start-Process -FilePath $Blender -ArgumentList $arguments -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $runtime 'blender_stdout.log') `
        -RedirectStandardError (Join-Path $runtime 'blender_stderr.log')
    $process.Id | Set-Content (Join-Path $runtime 'blender.pid')
    Write-Output "Blender studio process: $($process.Id). Local bridge: 127.0.0.1:9877."
} finally { $env:BLENDER_USER_RESOURCES = $previousResources }
