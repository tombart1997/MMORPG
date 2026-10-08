param([ValidatePattern('^[a-z][a-z0-9_]*$')] [string]$Asset)
$projectRoot = Split-Path -Parent $PSScriptRoot
$arguments = @("$projectRoot/tools/export_multiview_assets.py")
if ($Asset) { $arguments += @('--asset', $Asset) }
& python @arguments
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& python "$projectRoot/tools/configure_generated_imports.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& python "$projectRoot/tools/migrate_multiview_assets.py" --apply
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output 'New multi-view assets exported. Run ./tools/run.ps1 -Test to import and validate them in Godot.'
