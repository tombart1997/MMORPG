param([switch]$Editor, [switch]$Test, [switch]$Headless, [switch]$Windowed,
    [ValidateSet('combat_smoke', 'melee_commitment', 'zone_loop')] [string]$Suite = 'combat_smoke')
$projectRoot = Split-Path -Parent $PSScriptRoot
$gamePath = Join-Path $projectRoot 'game'
$localPath = Join-Path $gamePath '.local'
New-Item -ItemType Directory -Force $localPath, "$localPath/roaming", "$localPath/local" | Out-Null
$previousAppData = $env:APPDATA
$previousLocalAppData = $env:LOCALAPPDATA
try {
    $env:APPDATA = "$localPath/roaming"
    $env:LOCALAPPDATA = "$localPath/local"
    $godotArgs = @('--path', $gamePath, '--log-file', "$localPath/godot.log")
    if ($Editor) { $godotArgs += '--editor' }
    if ($Headless -or ($Test -and -not $Windowed)) { $godotArgs += '--headless' }
    if ($Test) {
        & godot --headless --path $gamePath --log-file "$localPath/import.log" --editor --import --quit | Out-Host
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        $godotArgs += @('--fixed-fps', '60', '--script', "res://tests/$Suite.gd")
    }
    & godot @godotArgs | Out-Host
    $result = $LASTEXITCODE
} finally {
    $env:APPDATA = $previousAppData
    $env:LOCALAPPDATA = $previousLocalAppData
}
exit $result
