#!/usr/bin/env python3
"""Тест генерации LTX Video"""

import sys
sys.path.insert(0, '/workspace/project/shorts_bot_v2')

from pipeline.ltx_video import LTXVideoGenerator

def main():
    gen = LTXVideoGenerator()
    
    print(f"ComfyUI доступен: {gen.available}")
    
    if not gen.available:
        print("❌ ComfyUI не запущен!")
        print("   Запустите: python main.py --help")
        return 1
    
    # Тестовый промпт - простой, чтобы проверить работоспособность
    prompt = "A cute orange cat sitting on a windowsill"
    
    print(f"\n🎬 Генерирую видео: {prompt}")
    print("   (Это может занять несколько минут на GPU)")
    
    result = gen.generate_t2v(
        prompt=prompt,
        num_frames=61,   # Меньше кадров для быстрого теста
        width=512,
        height=384,
        steps=15,       # Меньше шагов для быстрого теста
    )
    
    if result:
        print(f"\n✅ Видео сохранено: {result}")
        return 0
    else:
        print("\n❌ Ошибка генерации!")
        return 1

if __name__ == "__main__":
    sys.exit(main())