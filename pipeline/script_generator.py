"""
Script Generator - Uses LLM (Qwen3 via Ollama) to generate JSON video script from text idea

Локальный запуск через Ollama:
1. Установите Ollama: https://ollama.com
2. Запустите: ollama serve
3. Скачайте модель: ollama pull qwen3:8b
   (или qwen3:4b для более слабых ПК - 2.5GB)
"""
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from config import QWEN_MODEL_SIZE

logger = logging.getLogger(__name__)

# Ollama local endpoint
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_API_URL = f"{OLLAMA_BASE_URL}/api/generate"


def generate_script(idea: str, num_scenes: int = 4) -> List[Dict[str, Any]]:
    """
    Generate a JSON script from a text idea using Qwen3 (локально через Ollama)
    
    Args:
        idea: Text idea description
        num_scenes: Number of scenes to generate
        
    Returns:
        List of scene dictionaries
    """
    logger.info(f"Generating script for idea: {idea}")
    
    # Try local Ollama first
    try:
        return _generate_via_ollama(idea, num_scenes)
    except Exception as e:
        logger.warning(f"Ollama not available: {e}, using fallback generator")
        return _generate_fallback_script(idea, num_scenes)


def _generate_via_ollama(idea: str, num_scenes: int) -> List[Dict[str, Any]]:
    """Generate script using local Ollama with Qwen3"""
    
    # Qwen3 model: qwen3:8b, qwen3:4b, qwen3:14b, qwen3:32b и т.д.
    ollama_model = f"qwen3:{QWEN_MODEL_SIZE}"
    
    prompt = f"""Ты - креативный сценарист видео. На основе следующей идеи создай JSON-сценарий для видео из {num_scenes} сцен.

ИДЕЯ: {idea}

Сгенерируй JSON-массив сцен. Каждая сцена должна содержать точно эти поля:
- scene_id: integer (1, 2, 3, и т.д.)
- description: string (детальное визуальное описание для генерации изображения)
- prompt: string (промпт для генерации видео с инструкциями по движению)
- duration: float (длительность в секундах, 3-5)
- transition: string (эффект перехода: "fade", "dissolve", "slide_left", "slide_right", "zoom")

Верни ТОЛЬКО валидный JSON, без объяснений или markdown форматирования.
Пример формата:
[
  {{
    "scene_id": 1,
    "description": "Огромная космическая туманность с закрученными цветами фиолетового и синего",
    "prompt": "Медленное вращение и пульсирующее свечение, звезды мерцают на фоне",
    "duration": 4.0,
    "transition": "fade"
  }}
]"""

    payload = {
        "model": ollama_model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.7,
            "num_predict": 2000
        }
    }
    
    logger.info(f"Using Ollama model: {ollama_model}")
    
    response = requests.post(OLLAMA_API_URL, json=payload, timeout=180)
    response.raise_for_status()
    
    result = response.json()
    content = result.get("response", "")
    
    # Parse JSON from response
    try:
        script = json.loads(content)
        if isinstance(script, dict) and "scenes" in script:
            script = script["scenes"]
        logger.info(f"Generated {len(script)} scenes via Ollama")
        return script
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Ollama: {e}")
        logger.debug(f"Raw response: {content[:500]}")
        raise


def _generate_fallback_script(idea: str, num_scenes: int = 4) -> List[Dict[str, Any]]:
    """
    Fallback script generator when API is not available
    Generates creative scene descriptions based on the idea
    """
    logger.info("Using fallback script generator")
    
    # Creative scene templates based on idea keywords
    scenes = []
    transitions = ["fade", "dissolve", "slide_left", "zoom", "fade"]
    
    # Split idea into conceptually different parts or generate variations
    base_concepts = _extract_concepts(idea)
    
    for i in range(num_scenes):
        concept = base_concepts[i % len(base_concepts)] if base_concepts else idea
        
        scene = {
            "scene_id": i + 1,
            "description": f"Scene {i+1}: {concept}",
            "prompt": f"Subtle motion, gentle animation, cinematic lighting",
            "duration": 4.0,
            "transition": transitions[i % len(transitions)]
        }
        
        # Make each scene unique
        if i == 0:
            scene["description"] = f"Opening shot: {concept} - establishing wide view, dramatic introduction"
            scene["prompt"] = "Slow camera movement, dramatic lighting, atmospheric fog"
        elif i == num_scenes - 1:
            scene["description"] = f"Final scene: {concept} - conclusive ending, reflective mood"
            scene["prompt"] = "Gentle fade to conclusion, subtle particle effects, warm glow"
        else:
            scene["description"] = f"Middle progression: {concept} - developing narrative, dynamic action"
            scene["prompt"] = "Smooth motion, dynamic composition, flowing movement"
            
        scenes.append(scene)
    
    return scenes


def _extract_concepts(idea: str) -> List[str]:
    """Extract key concepts from the idea for varied scene generation"""
    # Simple keyword extraction
    words = idea.replace(",", " ").replace(".", " ").split()
    # Filter short words and get meaningful concepts
    concepts = [w for w in words if len(w) > 3]
    
    if not concepts:
        return [idea]
    
    # Return unique concepts up to 4
    return list(dict.fromkeys(concepts))[:4]


def validate_script(script: List[Dict[str, Any]]) -> bool:
    """
    Validate that the script has all required fields
    
    Args:
        script: List of scene dictionaries
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    required_fields = ["scene_id", "description", "prompt", "duration", "transition"]
    
    for i, scene in enumerate(script):
        for field in required_fields:
            if field not in scene:
                raise ValueError(f"Scene {i} missing required field: {field}")
    
    return True


if __name__ == "__main__":
    # Test the script generator
    logging.basicConfig(level=logging.INFO)
    
    test_idea = "A journey through space discovering new planets"
    script = generate_script(test_idea)
    
    print("Generated Script:")
    print(json.dumps(script, indent=2))
    
    validate_script(script)
    print("\n✓ Script validation passed")