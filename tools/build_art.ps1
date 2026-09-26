param([ValidateSet('all','forest','briarwake','briarling','turnwarden_v2')][string]$Asset='all')
$projectRoot = Split-Path -Parent $PSScriptRoot
$previousResources = $env:BLENDER_USER_RESOURCES
try {
    $env:BLENDER_USER_RESOURCES = Join-Path $projectRoot 'game/.local/blender'
    & blender --background --factory-startup --python-exit-code 1 --python "$projectRoot/blender/scripts/build_benchmark.py" -- $Asset *> "$projectRoot/game/.local/benchmark_build.log"
    $result = $LASTEXITCODE
} finally { $env:BLENDER_USER_RESOURCES = $previousResources }
Get-Content "$projectRoot/game/.local/benchmark_build.log" -Tail 10
exit $result
