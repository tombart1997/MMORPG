$ErrorActionPreference = 'Stop'
$forgeRoot = Split-Path -Parent $PSScriptRoot
Set-Location $forgeRoot
$uvTool = Join-Path $forgeRoot '.backends/setup-tools/bin/uv.exe'
if (!(Test-Path -LiteralPath $uvTool)) {
    py -3.12 -m pip install --target .backends/setup-tools uv==0.8.22
    if ($LASTEXITCODE) { throw 'Failed to install the isolated setup helper' }
}
if (!(Test-Path -LiteralPath '.backends/TRELLIS/.git')) {
    git clone https://github.com/microsoft/TRELLIS.git .backends/TRELLIS
}
git -C .backends/TRELLIS checkout 442aa1e1afb9014e80681d3bf604e8d728a86ee7
git -C .backends/TRELLIS submodule update --init --recursive
if ($LASTEXITCODE) { throw 'Failed to check out pinned TRELLIS and FlexiCubes sources' }
if (!(Test-Path -LiteralPath '.backends/trellis-venv/Scripts/python.exe')) {
    & $uvTool venv --python 3.11 .backends/trellis-venv
    if ($LASTEXITCODE) { throw 'Isolated TRELLIS Python environment creation failed' }
}
& $uvTool pip install --python .backends/trellis-venv/Scripts/python.exe torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu118
if ($LASTEXITCODE) { throw 'PyTorch installation failed' }
& $uvTool pip install --python .backends/trellis-venv/Scripts/python.exe numpy==1.26.4 spconv-cu117==2.3.6 easydict==1.13 safetensors==0.6.2 huggingface-hub==0.35.3 rembg==2.0.67 onnxruntime==1.23.1 trimesh==4.9.0 plyfile==1.1.2 tqdm==4.67.1 opencv-python-headless==4.11.0.86 transformers==4.51.3 'utils3d @ git+https://github.com/EasternJournalist/utils3d.git@9a4eb15e4021b67b12c460c7057d642626897ec8'
if ($LASTEXITCODE) { throw 'TRELLIS dependencies failed' }
& .backends/trellis-venv/Scripts/python.exe backends/trellis/runner.py --check
if ($LASTEXITCODE) { throw 'Real sparse convolution compatibility probe failed' }
& .backends/trellis-venv/Scripts/python.exe backends/trellis/runner.py --download
if ($LASTEXITCODE) { throw 'Pinned MIT model download failed' }
Write-Output 'Installed. Full multi-image inference and mesh verification must pass before the UI marks this backend available.'
