param([ValidatePattern('^[a-z][a-z0-9_]*$')] [string]$Asset)
$projectRoot = Split-Path -Parent $PSScriptRoot
$localPath = Join-Path $projectRoot 'game/.local'
New-Item -ItemType Directory -Force $localPath, "$localPath/blender" | Out-Null
$previousResources = $env:BLENDER_USER_RESOURCES
try {
    $env:BLENDER_USER_RESOURCES = "$localPath/blender"
    $blenderArgs = @('--background', '--factory-startup', '--python-exit-code', '1')
    if ($Asset) {
        $sourcePath = Join-Path $projectRoot "blender/characters/$Asset.blend"
        $benchmarkSource = Join-Path $projectRoot "blender/benchmark/$Asset.blend"
        if (Test-Path -LiteralPath $benchmarkSource) { $sourcePath = $benchmarkSource }
        if (-not (Test-Path -LiteralPath $sourcePath)) { throw "Missing source: $sourcePath" }
        $blenderArgs += @($sourcePath, '--python', "$projectRoot/blender/scripts/export_asset.py", '--', $Asset)
    } else {
        $blenderArgs += @('--python', "$projectRoot/blender/scripts/build_benchmark.py")
    }
    & blender @blenderArgs 2>&1 |
        Tee-Object -FilePath "$localPath/asset_build.log"
    $result = $LASTEXITCODE
} finally {
    $env:BLENDER_USER_RESOURCES = $previousResources
}
if ($result -ne 0) { exit $result }
Write-Output 'Assets rebuilt. Run ./tools/run.ps1 -Test to import and validate them in Godot.'
