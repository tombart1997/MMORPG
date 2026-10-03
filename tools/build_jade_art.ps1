param([ValidateSet('all','hero','creatures','equipment')][string]$Asset='all')
$projectRoot = Split-Path -Parent $PSScriptRoot
$localPath = Join-Path $projectRoot 'game/.local'
New-Item -ItemType Directory -Force $localPath | Out-Null
$previousResources = $env:BLENDER_USER_RESOURCES
try {
    $env:BLENDER_USER_RESOURCES = Join-Path $localPath 'blender'
    foreach ($kind in @('hero','creatures','equipment')) {
        if ($Asset -ne 'all' -and $Asset -ne $kind) { continue }
        $blenderArgs = if ($kind -eq 'hero') { @('--background', "$projectRoot/blender/characters/warden_high.blend") } else { @('--background','--factory-startup') }
        $blenderArgs += @('--python-exit-code','1','--python',"$projectRoot/blender/scripts/build_jade_$kind.py")
        & blender @blenderArgs *> "$localPath/jade_${kind}_build.log"
        $result = $LASTEXITCODE
        Get-Content "$localPath/jade_${kind}_build.log" -Tail 5
        if ($result -ne 0) { exit $result }
    }
} finally { $env:BLENDER_USER_RESOURCES = $previousResources }
exit 0
