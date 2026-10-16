param([switch]$BuildOnly)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$gamePath = Join-Path $projectRoot 'game'
$localPath = Join-Path $gamePath '.local'
$outputPath = Join-Path $gamePath 'builds/windows-release'
$godotCommand = (Get-Command godot -ErrorAction Stop).Source
$console = Join-Path (Split-Path -Parent $godotCommand) 'Godot_console.exe'
if (Test-Path -LiteralPath $console) { $godotCommand = $console }
$version = (& $godotCommand --version | Select-Object -First 1).Trim()
$templateVersion = ($version -split '\.')[0..2] -join '.'
$templateVersion += '.stable'
$templateFolder = Join-Path $localPath "roaming/Godot/export_templates/$templateVersion"
$templateFile = Join-Path $templateFolder 'windows_release_x86_64.exe'
if (-not (Test-Path -LiteralPath $templateFile)) {
    $installedTemplate = Join-Path $env:APPDATA "Godot/export_templates/$templateVersion/windows_release_x86_64.exe"
    $cachedTemplate = Join-Path $projectRoot '.local/godot_release/templates/windows_release_x86_64.exe'
    $source = if (Test-Path -LiteralPath $installedTemplate) { $installedTemplate } elseif (Test-Path -LiteralPath $cachedTemplate) { $cachedTemplate } else { $null }
    if (-not $source) { throw "Install Godot $templateVersion export templates in the editor before building Release." }
    New-Item -ItemType Directory -Force $templateFolder | Out-Null
    Copy-Item -LiteralPath $source -Destination $templateFile
}
New-Item -ItemType Directory -Force $outputPath, "$localPath/roaming", "$localPath/local" | Out-Null
$previousAppData = $env:APPDATA
$previousLocalAppData = $env:LOCALAPPDATA
try {
    $env:APPDATA = "$localPath/roaming"
    $env:LOCALAPPDATA = "$localPath/local"
    $buildLog = "$localPath/release-export.log"
    # Windows PowerShell treats native stderr as an error record, including
    # Godot's harmless certificate-store message in restricted environments.
    $ErrorActionPreference = 'Continue'
    & $godotCommand --headless --path $gamePath --log-file $buildLog --export-release 'Windows Release' "$outputPath/Ironfield.exe" | Out-Host
    $ErrorActionPreference = 'Stop'
    if ($LASTEXITCODE -ne 0) { throw "Release export failed ($LASTEXITCODE). See $buildLog" }
    if (Select-String -LiteralPath $buildLog -Pattern 'SCRIPT ERROR:|ERROR: (?!Failed to read the root certificate store)' -Quiet) { throw "Release export reported errors. See $buildLog" }
    if (-not $BuildOnly) {
        $gameProcess = Start-Process -FilePath "$outputPath/Ironfield.exe" -WorkingDirectory $outputPath -ArgumentList @('--log-file', "$localPath/release-game.log") -PassThru
        Write-Output "Started Release: $outputPath/Ironfield.exe (PID $($gameProcess.Id))"
    }
} finally {
    $env:APPDATA = $previousAppData
    $env:LOCALAPPDATA = $previousLocalAppData
}
