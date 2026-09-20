param([switch]$Editor, [switch]$Test, [switch]$Headless, [switch]$Windowed,
    [ValidateSet('all', 'combat_smoke', 'melee_commitment', 'zone_loop', 'character_pipeline', 'rpg_progression', 'settlement_loop', 'mmorpg_loop', 'skill_combat')] [string]$Suite = 'all')
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
        if (Select-String -Path "$localPath/import.log" -Pattern 'SCRIPT ERROR:|ERROR: (?!Failed to read the root certificate store)' -Quiet) { exit 1 }
        $testSuites = if ($Suite -eq 'all') { @('combat_smoke', 'melee_commitment', 'zone_loop', 'character_pipeline', 'rpg_progression', 'settlement_loop', 'mmorpg_loop', 'skill_combat') } else { @($Suite) }
        $result = 0
        foreach ($testSuite in $testSuites) {
            $testArgs = $godotArgs + @('--fixed-fps', '60', '--script', "res://tests/$testSuite.gd")
            & godot @testArgs | Out-Host
            $suiteResult = $LASTEXITCODE
            Copy-Item -LiteralPath "$localPath/godot.log" -Destination "$localPath/$testSuite.log" -Force
            if ($suiteResult -ne 0 -or (Select-String -Path "$localPath/godot.log" -Pattern 'SCRIPT ERROR:|ERROR: (?!Failed to read the root certificate store)' -Quiet)) { $result = 1; break }
        }
    } else {
        & godot @godotArgs | Out-Host
        $result = $LASTEXITCODE
    }
} finally {
    $env:APPDATA = $previousAppData
    $env:LOCALAPPDATA = $previousLocalAppData
}
exit $result
