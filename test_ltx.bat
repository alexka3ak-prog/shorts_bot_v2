@echo off
REM Test script for AutoVideo + LTX 2.3

cd /d %~dp0..

echo ========================================
echo Testing ComfyUI Connection...
echo ========================================

python -c "import requests; r=requests.get('http://127.0.0.1:8188/system_stats', timeout=5); print('ComfyUI OK' if r.status_code==200 else 'ComfyUI ERROR')" 2>nul

if errorlevel 1 (
    echo ERROR: ComfyUI not running!
    echo Start ComfyUI first: cd D:\ComfyUI ^&^& python main.py
    pause
    exit 1
)

echo.
echo Checking LTX nodes...
python -c "
import sys
sys.path.insert(0, '.')
from pipeline.comfyui_video import ComfyUIVideoGenerator
g = ComfyUIVideoGenerator()
nodes = g.check_ltx_nodes()
for name, present in nodes.items():
    print(f'[{chr(88) if present else chr(73)}] {name}')
"

echo.
echo ========================================
echo Testing Video Generation...
echo ========================================

python -c "
import sys
sys.path.insert(0, '.')
from pipeline import ImageGenerator, ComfyUIVideoGenerator
import os
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
except Exception as e:
    print(f'ERROR: {e}')
"

echo.
pause