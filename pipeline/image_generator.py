"""
Image Generator - Uses Stable Diffusion XL to generate images for each scene

Локальный запуск:
- Установите: pip install torch diffusers transformers accelerate
- Используйте config.py для настройки
"""
import os
import json
import logging
import time
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from config import (
    STABILITY_API_KEY, STABILITY_API_URL,
    IMAGE_WIDTH, IMAGE_HEIGHT, OUTPUT_DIR, TEMP_DIR,
    INSTAGRAM_FORMATS, DEFAULT_FORMAT,
    USE_LOCAL_SDXL
)

logger = logging.getLogger(__name__)

# Try to import diffusers for local SDXL
try:
    from diffusers import StableDiffusionXLPipeline
    import torch
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False


class ImageGenerator:
    """Generate images using Stable Diffusion XL"""
    
    def __init__(self, output_dir: str = TEMP_DIR, format_name: str = DEFAULT_FORMAT):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = STABILITY_API_KEY
        self.api_url = STABILITY_API_URL
        self.format_name = format_name
        
        # Get Instagram format settings
        format_config = INSTAGRAM_FORMATS.get(format_name, INSTAGRAM_FORMATS[DEFAULT_FORMAT])
        self.width = format_config["width"]
        self.height = format_config["height"]
        
        # Try to load local SDXL pipeline
        self.pipeline = None
        if USE_LOCAL_SDXL and DIFFUSERS_AVAILABLE:
            try:
                logger.info("Loading local SDXL pipeline...")
                self.pipeline = StableDiffusionXLPipeline.from_pretrained(
                    "stabilityai/stable-diffusion-xl-base-1.0",
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    variant="fp16" if torch.cuda.is_available() else None
                )
                if torch.cuda.is_available():
                    self.pipeline = self.pipeline.to("cuda")
                logger.info("Local SDXL pipeline loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load local SDXL: {e}")
                self.pipeline = None
    
    def generate_image(self, prompt: str, scene_id: int) -> str:
        """
        Generate an image for a scene using SDXL
        
        Args:
            prompt: Text description for the image
            scene_id: Scene identifier
            
        Returns:
            Path to the generated image
        """
        logger.info(f"Generating image for scene {scene_id}: {prompt[:50]}...")
        
        output_path = self.output_dir / f"scene_{scene_id:03d}_image.png"
        
        # Try local SDXL first
        if self.pipeline is not None:
            try:
                self._generate_local_sdxl(prompt, output_path)
                logger.info(f"Generated image via local SDXL: {output_path}")
                return str(output_path)
            except Exception as e:
                logger.warning(f"Local SDXL failed: {e}")
        
        # Try API if key available
        if self.api_key:
            try:
                self._generate_via_api(prompt, output_path)
                logger.info(f"Generated image via API: {output_path}")
                return str(output_path)
            except Exception as e:
                logger.warning(f"API generation failed: {e}, using placeholder")
        
        # Fallback: Generate artistic placeholder
        self._generate_placeholder(prompt, output_path)
        logger.info(f"Generated placeholder: {output_path}")
        return str(output_path)
    
    def _generate_local_sdxl(self, prompt: str, output_path: Path):
        """Generate image using local SDXL via Diffusers"""
        import torch
        
        result = self.pipeline(
            prompt=prompt,
            width=self.width,
            height=self.height,
            num_inference_steps=30,
            guidance_scale=7.5
        )
        
        image = result.images[0]
        image.save(output_path, "PNG")
    
    def _generate_via_api(self, prompt: str, output_path: Path):
        """Generate image using Stability AI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/png"
        }
        
        # For SDXL, we use the image generation endpoint
        # Note: This uses Stability AI's image generation, not video
        response = requests.post(
            "https://api.stability.ai/v2beta/image-generation/text-to-image",
            headers=headers,
            json={
                "prompt": prompt,
                "width": IMAGE_WIDTH,
                "height": IMAGE_HEIGHT,
                "steps": 30,
                "seed": int(time.time() * 1000) % 1000000
            },
            timeout=120
        )
        
        response.raise_for_status()
        
        # Save the image
        with open(output_path, "wb") as f:
            f.write(response.content)
    
    def _generate_placeholder(self, prompt: str, output_path: Path):
        """
        Generate artistic placeholder image
        Используется когда нет доступа к SDXL
        """
        # Create a creative placeholder image with correct dimensions
        img = Image.new('RGB', (self.width, self.height))
        
        # Generate colors based on prompt hash
        np.random.seed(hash(prompt) % (2**32))
        r = np.random.randint(50, 200)
        g = np.random.randint(50, 200)
        b = np.random.randint(100, 255)
        
        # Create gradient background
        pixels = img.load()
        for y in range(self.height):
            for x in range(self.width):
                factor = (x + y) / (self.width + self.height)
                pr = int(r * (1 - factor * 0.5))
                pg = int(g * (1 - factor * 0.3))
                pb = int(b)
                pixels[x, y] = (pr, pg, pb)
        
        # Add scene identifier
        draw = ImageDraw.Draw(img)
        
        # Draw some geometric patterns for visual interest
        center_x, center_y = self.width // 2, self.height // 2
        
        # Outer circle
        outer_size = min(self.width, self.height) // 3
        draw.ellipse(
            [center_x - outer_size, center_y - outer_size, 
             center_x + outer_size, center_y + outer_size],
            outline=(255, 255, 255), width=3
        )
        
        # Inner circle
        inner_size = outer_size // 2
        draw.ellipse(
            [center_x - inner_size, center_y - inner_size, 
             center_x + inner_size, center_y + inner_size],
            outline=(255, 255, 255), width=2
        )
        
        # Cross pattern
        margin = min(self.width, self.height) // 10
        draw.line([(center_x, margin), (center_x, self.height - margin)], 
                  fill=(255, 255, 255), width=2)
        draw.line([(margin, center_y), (self.width - margin, center_y)], 
                  fill=(255, 255, 255), width=2)
        
        # Add prompt text (truncated)
        text = f"Scene: {prompt[:30]}..." if len(prompt) > 30 else f"Scene: {prompt}"
        # Note: In production, use a proper font file
        # For now, we'll skip text drawing as we don't have fonts
        
        # Save
        img.save(output_path, "PNG")
    
    def generate_all_images(self, scenes: List[Dict[str, Any]]) -> List[str]:
        """
        Generate images for all scenes
        
        Args:
            scenes: List of scene dictionaries
            
        Returns:
            List of image file paths
        """
        logger.info(f"Generating {len(scenes)} images...")
        
        image_paths = []
        for scene in scenes:
            scene_id = scene["scene_id"]
            description = scene.get("description", "")
            prompt = scene.get("prompt", description)
            
            image_path = self.generate_image(prompt, scene_id)
            image_paths.append(image_path)
        
        logger.info(f"Generated {len(image_paths)} images")
        return image_paths


def generate_image(prompt: str, scene_id: int, output_dir: str = TEMP_DIR) -> str:
    """Convenience function to generate a single image"""
    generator = ImageGenerator(output_dir)
    return generator.generate_image(prompt, scene_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test image generation
    generator = ImageGenerator()
    
    test_scenes = [
        {"scene_id": 1, "description": "A sunrise over mountains", "prompt": "Mountain sunrise, golden light"},
        {"scene_id": 2, "description": "Ocean waves on beach", "prompt": "Ocean waves, blue water"},
    ]
    
    paths = generator.generate_all_images(test_scenes)
    
    print("Generated images:")
    for path in paths:
        print(f"  - {path}")