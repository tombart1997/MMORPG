param([string]$ForgePath='C:\Users\Tom\Documents\2D_to_3D')
$ErrorActionPreference='Stop'
$forgeTarget=[IO.Path]::GetFullPath($ForgePath)
if (!(Test-Path -LiteralPath (Join-Path $forgeTarget 'forge/store.py'))) { throw 'Target must be an existing Asset Forge installation.' }
$manifest=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
$backupRoot=Join-Path $forgeTarget ('data/multiview_code_backups/'+(Get-Date -Format 'yyyyMMdd_HHmmss'))
foreach($entry in $manifest.files) {
    $source=Join-Path $PSScriptRoot $entry.path
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLower() -ne $entry.sha256) { throw "Patch file hash changed: $($entry.path)" }
    $target=[IO.Path]::GetFullPath((Join-Path $forgeTarget $entry.path))
    if (!$target.StartsWith($forgeTarget.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Patch path escapes the intended Forge directory.' }
    if (Test-Path -LiteralPath $target) {
        $backup=Join-Path $backupRoot $entry.path
        New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force | Out-Null
        Copy-Item -LiteralPath $target -Destination $backup
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $target
}
Write-Output "Installed source patch in $forgeTarget; original code copies are in $backupRoot. Run scripts/setup_trellis.ps1 for weights/dependencies, then restart Forge."
