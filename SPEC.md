# Video Generation Pipeline Specification

## Project Overview
- **Project Name**: AutoVideo Generator
- **Type**: Automated video generation system
- **Core Functionality**: Takes a text idea and automatically generates a complete video by creating scenes using AI models (LLM for script, Stable Diffusion XL for images, LTX 2.3 for video)
- **Target Users**: Content creators, marketers, automated video producers

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Text Idea     │────>│  Qwen3-VL LLM    │────>│  JSON Script    │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          v
┌─────────────────────────────────────────────────────────────────────┐
│                         Scene Loop                                   │
│  ┌─────────────┐    ┌─────────────────┐    ┌──────────────────┐    │
│  │ SDXL Image  │---->│  LTX 2.3 Video │---->│  Video Segments  │    │
│  │ Generation  │    │   Generation    │    │                  │    │
│  └─────────────┘    └─────────────────┘    └────────┬─────────┘    │
└──────────────────────────────────────────────────────┘              │
                                                               v
                                                       ┌─────────────┐
                                                       │   Concatenate│
                                                       │   Scenes    │
                                                       └──────┬──────┘
                                                              v
                                                       ┌─────────────┐
                                                       │ Final Video │
                                                       │   Output    │
                                                       └─────────────┘
```

## Functionality Specification

### Core Features

1. **Text Idea Input**
   - Accept text prompt/idea via CLI argument or API
   - No user interaction required during processing

2. **JSON Script Generation (Qwen3-VL)**
   - Parse text idea into structured scenes
   - Each scene contains:
     - `scene_id`: Unique identifier
     - `description`: Visual description for image generation
     - `prompt`: Video generation prompt
     - `duration`: Estimated duration (seconds)
     - `transition`: Transition effect to next scene

3. **Image Generation (Stable Diffusion XL)**
   - Use Stability AI API or local SDXL model
   - Generate high-quality images for each scene
   - Resolution: 1024x1024 (configurable)

4. **Video Generation (LTX 2.3)**
   - Convert static image to video using LTX 2.3
   - Apply animations and transitions
   - Duration per scene: 3-5 seconds

5. **Video Concatenation**
   - Merge all scene videos into single file
   - Apply smooth transitions between scenes
   - Output format: MP4 (H.264)

6. **Output**
   - Save final video to output directory
   - Generate metadata JSON with scene details

### API Integration

- **Qwen3-VL**: Use together.ai API or similar
- **Stable Diffusion XL**: Stability AI API
- **LTX 2.3**: LTX Studio API or local model

## Technical Implementation

### File Structure
```
/workspace/project/
├── main.py                 # Main entry point
├── config.py               # Configuration settings
├── pipeline/
│   ├── __init__.py
│   ├── script_generator.py    # LLM script generation
│   ├── image_generator.py     # SDXL image generation
│   ├── video_generator.py     # LTX video generation
│   └── video_concatenator.py  # FFmpeg concatenation
├── output/                 # Generated files
├── requirements.txt
└── SPEC.md
```

### Dependencies
- requests (API calls)
- moviepy (video editing)
- pillow (image processing)
- ffmpeg (video processing)

## Acceptance Criteria

1. ✓ System accepts text idea as input
2. ✓ Generates valid JSON script with scene breakdown
3. ✓ Creates unique image for each scene using SDXL
4. ✓ Converts each image to video using LTX 2.3
5. ✓ Concatenates all scene videos into single output
6. ✓ Runs fully automatically without user interaction
7. ✓ Outputs final video file in MP4 format
8. ✓ Provides console progress feedback