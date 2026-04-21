# AutoVideo + LTX 2.3 Test Script

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing ComfyUI Connection..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check ComfyUI
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8188/system_stats" -TimeoutSec 5
    Write-Host "[OK] ComfyUI is running!" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] ComfyUI not running!" -ForegroundColor Red
    Write-Host "Start ComfyUI first: cd D:\ComfyUI ; python main.py" -ForegroundColor Yellow
    Read-Host
    exit 1
}

Write-Host ""
Write-Host "Checking LTX nodes..." -ForegroundColor Cyan

# Import and check nodes
python -c @"
import sys
sys.path.insert(0, '.')
from pipeline.comfyui_video import ComfyUIVideoGenerator
g = ComfyUIVideoGenerator()
nodes = g.check_ltx_nodes()
for name, present in nodes.items():
    status = '[OK]' if present else '[--]'
    print(f'{status} {name}')
" 2>$null

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Video Generation..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Test generation
python -c @"
import sys
import os
sys.path.insert(0, '.')
from pipeline import ImageGenerator, ComfyUIVideoGenerator

os.makedirs('output/temp', exist_ok=True)

print('Generating test image...')
img_gen = ImageGenerator('output/temp', 'reels')
test_image = img_gen.generate_image('a cute cat on a rocket in space', 1)
print(f'Image: {test_image}')

print('Generating video via LTX 2.3...')
video_gen = ComfyUIVideoGenerator()
try:
    output = video_gen.generate_video_ltx(
        image_path=test_image,
        prompt='smooth movement, cinematic lighting',
        output_path='output/test_video.mp4',
        model_name='ltx-2.3-22b-dev-fp8.safetensors'
    )
    print(f'Video: {output}')
    print('SUCCESS!')
except Exception as e:
    print(f'ERROR: {e}')
"

Write-Host ""
Read-Host "Press Enter to exit"