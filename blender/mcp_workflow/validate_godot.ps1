param([switch]$Capture, [string]$Godot = 'C:\Program Files\Godot\Godot_console.exe')
$ErrorActionPreference = 'Stop'
$project = Join-Path $PSScriptRoot 'godot_check'
$runtime = Join-Path $PSScriptRoot 'runtime'
New-Item -ItemType Directory -Force $runtime | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'output/oathkeeper_sword.glb') -Destination (Join-Path $project 'sword.glb') -Force
& $Godot --headless --path $project --editor --import --quit --log-file (Join-Path $runtime 'godot_import.log') | Out-Host
if ($LASTEXITCODE -ne 0) { throw 'Godot import failed' }
& $Godot --headless --path $project --script res://verify.gd --log-file (Join-Path $runtime 'godot_verify.log') | Out-Host
if ($LASTEXITCODE -ne 0) { throw 'Godot verification failed' }
if ($Capture) {
    $arguments = @('--path', ('"'+$project+'"'), '--script', 'res://verify.gd', '--log-file', ('"'+(Join-Path $runtime 'godot_capture.log')+'"'), '--', '--capture')
    Start-Process -FilePath $Godot -ArgumentList $arguments -WindowStyle Hidden -Wait
}
$logs = @((Join-Path $runtime 'godot_import.log'), (Join-Path $runtime 'godot_verify.log'))
if ($Capture) { $logs += Join-Path $runtime 'godot_capture.log' }
foreach ($log in $logs) {
    if (Select-String -LiteralPath $log -Pattern 'SCRIPT ERROR:|ERROR:' -Quiet) { throw "Engine error: $log" }
}
Get-Content (Join-Path $PSScriptRoot 'output/godot_validation.json')
