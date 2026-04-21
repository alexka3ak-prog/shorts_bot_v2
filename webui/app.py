"""
Web UI для AutoVideo Generator
Простой и удобный интерфейс для генерации видео
"""
import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
import threading
import logging

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import AutoVideoPipeline
from config import INSTAGRAM_FORMATS, DEFAULT_FORMAT

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Глобальное состояние генерации
generation_state = {
    "status": "idle",  # idle, generating, completed, error
    "progress": 0,
    "message": "",
    "result_video": None,
    "error": None
}

# Lock для потокобезопасности
generation_lock = threading.Lock()


@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html', 
                          formats=INSTAGRAM_FORMATS,
                          default_format=DEFAULT_FORMAT)


@app.route('/api/generate', methods=['POST'])
def generate_video():
    """API для запуска генерации видео"""
    global generation_state
    
    with generation_lock:
        if generation_state["status"] == "generating":
            return jsonify({"error": "Генерация уже запущена"}), 400
        
        data = request.json
        idea = data.get('idea', '').strip()
        format_name = data.get('format', DEFAULT_FORMAT)
        num_scenes = int(data.get('scenes', 4))
        model_size = data.get('model', '8b')  # Получаем модель из запроса
        
        if not idea:
            return jsonify({"error": "Введите описание видео"}), 400
        
        # Сброс состояния
        generation_state = {
            "status": "generating",
            "progress": 0,
            "message": "Инициализация...",
            "result_video": None,
            "error": None,
            "model": model_size
        }
    
    # Запуск генерации в отдельном потоке
    def run_generation():
        global generation_state
        try:
            # Установить модель через переменную окружения
            os.environ['QWEN_MODEL_SIZE'] = model_size
            
            generation_state["progress"] = 10
            generation_state["message"] = "Генерация сценария..."
            
            pipeline = AutoVideoPipeline(format_name=format_name)
            final_video = pipeline.run(idea, num_scenes)
            
            generation_state["status"] = "completed"
            generation_state["progress"] = 100
            generation_state["message"] = "Готово!"
            generation_state["result_video"] = final_video
            
        except Exception as e:
            generation_state["status"] = "error"
            generation_state["error"] = str(e)
            generation_state["message"] = f"Ошибка: {str(e)}"
    
    thread = threading.Thread(target=run_generation)
    thread.start()
    
    return jsonify({"status": "started", "message": "Генерация началась"})


@app.route('/api/status')
def get_status():
    """Получить статус генерации"""
    return jsonify(generation_state)


@app.route('/api/download')
def download_video():
    """Скачать сгенерированное видео"""
    if generation_state["result_video"] and os.path.exists(generation_state["result_video"]):
        return send_file(generation_state["result_video"], 
                       as_attachment=True,
                       download_name='generated_video.mp4')
    return jsonify({"error": "Видео не найдено"}), 404


@app.route('/api/models')
def get_models():
    """Получить доступные модели"""
    # Здесь можно добавить проверку доступных моделей Ollama
    return jsonify({
        "llm_models": ["qwen3:8b", "qwen3:4b", "qwen3:14b"],
        "sdxl_models": ["stable-diffusion-xl-base-1.0"],
        "formats": list(INSTAGRAM_FORMATS.keys())
    })


def run_server(host='0.0.0.0', port=5000):
    """Запуск веб-сервера"""
    app.run(host=host, port=port, debug=True, threaded=True)


if __name__ == '__main__':
    print("🚀 Запуск Web UI...")
    print("Откройте в браузере: http://localhost:5000")
    run_server()