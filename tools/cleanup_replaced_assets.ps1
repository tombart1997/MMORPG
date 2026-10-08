$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$migration = Get-Content -Raw (Join-Path $workspace 'docs/full_asset_rebuild/migration_manifest.json') | ConvertFrom-Json
if ($migration.missing.Count -ne 0) { throw 'Replacement catalogue is incomplete.' }
function Remove-WorkspaceItem([string]$relative) {
    $target = [IO.Path]::GetFullPath((Join-Path $workspace $relative))
    if (-not $target.StartsWith($workspace + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "Outside workspace: $target" }
    if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
}
$shaderDirectory = Join-Path $workspace 'game/assets/shaders'
New-Item -ItemType Directory -Force -Path $shaderDirectory | Out-Null
foreach ($shader in @('world_kit/cinder_ground.gdshader','world_kit/contact_shadow.gdshader','creatures/creature_surface.gdshader')) {
    $source = Join-Path $workspace ('game/assets/' + $shader)
    $target = Join-Path $shaderDirectory (Split-Path -Leaf $shader)
    if (Test-Path -LiteralPath $source) { Move-Item -LiteralPath $source -Destination $target -Force }
    if (Test-Path -LiteralPath ($source+'.uid')) { Move-Item -LiteralPath ($source+'.uid') -Destination ($target+'.uid') -Force }
    $old = 'res://assets/' + $shader
    $new = 'res://assets/shaders/' + (Split-Path -Leaf $shader)
    foreach ($relativeFile in (& rg --files (Join-Path $workspace 'game') -g '*.gd' -g '*.tres' -g '*.tscn')) {
        $content = [IO.File]::ReadAllText($relativeFile)
        if ($content.Contains($old)) { [IO.File]::WriteAllText($relativeFile,$content.Replace($old,$new)) }
    }
}
foreach ($folder in @('benchmark','characters','creatures','mounts','weapons','world_kit','forge_rebuild','reviewed')) { Remove-WorkspaceItem ('game/assets/'+$folder) }
Remove-WorkspaceItem 'game/review_assets'
Remove-WorkspaceItem 'game/scripts/visuals/humanoid_paint.gd'
Remove-WorkspaceItem 'game/scripts/visuals/humanoid_paint.gd.uid'
# Preserve new editable scenes and topology-free binding samples; remove all old meshes.
foreach ($file in Get-ChildItem -LiteralPath (Join-Path $workspace 'blender') -Recurse -File | Where-Object { $_.Extension -in @('.blend','.blend1','.blend2','.blend@','.glb','.obj','.fbx') -and $_.FullName -notmatch '\\multiview_rebuild\\|\\[.]venv\\' }) {
    Remove-WorkspaceItem ($file.FullName.Substring($workspace.Length+1))
}
# These flat exports are intermediate body plans; the game uses their named variants.
foreach ($file in Get-ChildItem -LiteralPath (Join-Path $workspace 'game/assets/generated') -Filter *.glb -File | Where-Object { $_.BaseName -notin @('warrior','bay_horse') }) {
    $baseName = $file.BaseName
    Remove-WorkspaceItem ($file.FullName.Substring($workspace.Length+1))
    Remove-WorkspaceItem (($file.FullName+'.import').Substring($workspace.Length+1))
    foreach ($texture in Get-ChildItem -LiteralPath $file.DirectoryName -File | Where-Object { $_.Name.StartsWith($baseName+'_') }) { Remove-WorkspaceItem ($texture.FullName.Substring($workspace.Length+1)) }
}
Write-Host 'Removed superseded runtime models, baked surfaces, intermediate exports and legacy authoring meshes.'
