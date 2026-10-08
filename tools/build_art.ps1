param([ValidatePattern('^[a-z][a-z0-9_]*$')][string]$Asset='all')
# Keep the previous entry point on the current reviewed source catalogue.
$mapped = switch ($Asset) {
    'briarwake' { 'fracture' }
    'briarling' { 'young' }
    'turnwarden_v2' { 'warrior' }
    default { $Asset }
}
if ($mapped -in @('all','forest')) { & "$PSScriptRoot/build_assets.ps1" }
else { & "$PSScriptRoot/build_assets.ps1" -Asset $mapped }
exit $LASTEXITCODE
