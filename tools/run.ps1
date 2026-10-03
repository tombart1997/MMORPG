param([switch]$Editor, [switch]$Test, [switch]$Headless, [switch]$Windowed,
    [ValidateSet('all', 'combat_smoke', 'melee_commitment', 'zone_loop', 'character_pipeline', 'rpg_progression', 'settlement_loop', 'mmorpg_loop', 'skill_combat', 'farming_stress', 'farming_loop', 'art_benchmark', 'first_hour', 'route_mount', 'first_map_expansion', 'combat_creation_review', 'second_region', 'remaster_streaming', 'remaster_traversal', 'townfolk_review', 'hero_combat_review', 'jade_visual_review', 'world_landscape', 'world_visual_review', 'character_motion', 'presentation_upgrade', 'field_feedback_review')] [string]$Suite = 'all')
$projectRoot = Split-Path -Parent $PSScriptRoot
$gamePath = Join-Path $projectRoot 'game'
$localPath = Join-Path $gamePath '.local'
New-Item -ItemType Directory -Force $localPath, "$localPath/roaming", "$localPath/local" | Out-Null
$previousAppData = $env:APPDATA
$previousLocalAppData = $env:LOCALAPPDATA
try {
    $env:APPDATA = "$localPath/roaming"
    $env:LOCALAPPDATA = "$localPath/local"
    $godotArgs = @('--path', $gamePath)
    if (-not $Test) { $godotArgs += @('--log-file', "$localPath/godot.log") }
    if ($Editor) { $godotArgs += '--editor' }
    if ($Headless -or ($Test -and -not $Windowed)) { $godotArgs += '--headless' }
    if ($Test) {
        & godot --headless --path $gamePath --log-file "$localPath/import.log" --editor --import --quit | Out-Host
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        if (Select-String -Path "$localPath/import.log" -Pattern 'SCRIPT ERROR:|ERROR: (?!Failed to read the root certificate store)' -Quiet) { exit 1 }
        $testSuites = if ($Suite -eq 'all') { @('combat_smoke', 'melee_commitment', 'zone_loop', 'character_pipeline', 'rpg_progression', 'settlement_loop', 'mmorpg_loop', 'skill_combat', 'farming_loop', 'route_mount', 'first_map_expansion', 'combat_creation_review', 'second_region', 'remaster_streaming', 'remaster_traversal', 'townfolk_review', 'hero_combat_review', 'jade_visual_review', 'world_landscape', 'character_motion', 'presentation_upgrade', 'field_feedback_review') } else { @($Suite) }
        $result = 0
        foreach ($testSuite in $testSuites) {
            $suiteLog = "$localPath/$testSuite.log"
            $testArgs = $godotArgs + @('--log-file', $suiteLog) + $(if ($testSuite -eq 'world_visual_review') { @('--script', "res://tests/$testSuite.gd") } else { @('--fixed-fps', '60', '--script', "res://tests/$testSuite.gd") })
            & godot @testArgs | Out-Host
            $suiteResult = $LASTEXITCODE
            if ($suiteResult -ne 0 -or (Select-String -Path $suiteLog -Pattern 'SCRIPT ERROR:|ERROR: (?!Failed to read the root certificate store)' -Quiet)) { $result = 1; break }
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
