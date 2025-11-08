# Vibe Voice TTS - RunPod Serverless Project

## Project Overview

This project runs a **ComfyUI Vibe Voice text-to-speech workflow** on RunPod serverless infrastructure. It takes an audio voice sample and text, then generates synthesized speech in that voice.

### Original Project
- **Base**: upscale2flare (image upscaling workflow)
- **Converted to**: Vibe Voice TTS (voice cloning workflow)
- **Date Modified**: 2025-11-08

---

## How It Works

### Architecture
```
User API Request → RunPod Handler → ComfyUI (with VibeVoice) → R2 Storage → Audio URL Response
```

### Workflow Pipeline
1. **LoadAudio**: Loads voice sample (e.g., Trump voice)
2. **VibeVoiceMultipleSpeakersNode**: Generates speech from text using voice cloning
3. **SaveAudioMP3**: Outputs MP3 file (320k quality)

### Input Format
```json
{
  "input": {
    "audio_url": "https://example.com/voice-sample.mp3",
    "workflow": { ... complete workflow JSON ... }
  }
}
```

### Output Format
```json
{
  "audio": [
    "https://pub-xxx.r2.dev/uuid_filename.mp3"
  ]
}
```

---

## Technical Specifications

### Models Used
- **VibeVoice-Large**: 18.7GB (from `aoi-ot/VibeVoice-Large`)
- **Tokenizer**: Qwen2.5-1.5B tokenizer files
- **VRAM Required**: ~20GB

### Custom Nodes
- **VibeVoice-ComfyUI**: Main TTS engine
  - Repo: `https://github.com/Enemyx-net/VibeVoice-ComfyUI`

### Storage
- **Cloudflare R2**: Audio file storage
- **Format**: MP3 (320k bitrate)

---

## Conversion Checklist

### ✅ Phase 1: Documentation & Setup
- [ ] Create claude.md documentation file
- [ ] Set up TodoWrite for progress tracking

### ✅ Phase 2: Create API Workflow
- [ ] Build proper API format workflow from UI version
- [ ] Add correct class_type for VibeVoiceMultipleSpeakersNode
- [ ] Map all parameters (text, model, settings)
- [ ] Save as workflow_api_vibevoice.json

### ✅ Phase 3: Update Dockerfile
**Remove:**
- [ ] Image upscaling models (epicrealism checkpoint, LoRAs, ControlNet, upscale models)
- [ ] Old custom nodes (AutomaticCFG, perturbed-attention, TiledDiffusion, post-processing)
- [ ] Old model directories

**Add:**
- [ ] Create /models/vibevoice/ directory structure
- [ ] Install VibeVoice-ComfyUI custom node
- [ ] Add huggingface-hub to pip dependencies
- [ ] Download VibeVoice-Large model (~18.7GB)
- [ ] Download Qwen2.5-1.5B tokenizer files (4 files)

### ✅ Phase 4: Modify Handler (rp_handler.py)
- [ ] Add download_audio() function
- [ ] Support audio_url input parameter
- [ ] Auto-inject audio into LoadAudio nodes
- [ ] Detect SaveAudioMP3 output nodes
- [ ] Upload MP3 files to R2 with correct ContentType
- [ ] Return audio URLs in response

### ✅ Phase 5: Update Examples
- [ ] Update input.json with audio workflow example
- [ ] Update response.json with audio output format

---

## Environment Variables Required

```bash
R2_ENDPOINT_URL=https://ACCOUNT_ID.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=your_bucket_name
R2_PUBLIC_URL=https://pub-xxx.r2.dev
```

---

## Key Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Container setup, model downloads, custom nodes |
| `src/rp_handler.py` | RunPod serverless handler (audio I/O) |
| `src/ComfyUI_API_Wrapper.py` | ComfyUI API client |
| `src/start.sh` | Container startup script |
| `workflow_api_vibevoice.json` | Vibe Voice workflow (API format) |
| `input.json` | Example API request |
| `response.json` | Example API response |

---

## Build & Deploy

### Local Build
```bash
docker build -t vibevoice-runpod .
```

### Deploy to RunPod
1. Push image to Docker Hub/Registry
2. Create RunPod serverless endpoint
3. Set environment variables
4. Test with sample request

---

## Workflow Parameters

### VibeVoiceMultipleSpeakersNode Settings
- **Model**: VibeVoice-Large
- **Language**: auto
- **Precision**: full precision
- **Temperature**: 1.3
- **Top-p**: 0.9
- **Top-k**: 0.8
- **Repetition Penalty**: 1.0
- **Random Seed**: 45, 42

---

## Notes

- Workflow format: API format (not UI format)
- Audio files saved to: `/root/comfy/ComfyUI/input/`
- Output directory: `/root/comfy/ComfyUI/output/`
- ComfyUI runs on: `http://127.0.0.1:8188`

---

## References

- [VibeVoice GitHub](https://github.com/Enemyx-net/VibeVoice-ComfyUI)
- [VibeVoice-Large Model](https://huggingface.co/aoi-ot/VibeVoice-Large)
- [Qwen2.5-1.5B Tokenizer](https://huggingface.co/Qwen/Qwen2.5-1.5B)
- [Original Project](https://github.com/dtarnow/upscale2flare)
