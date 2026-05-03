# ComfyUI Workflow Guide

## Current Goal
Use ComfyUI to produce a first consistent still-image workflow before adding advanced identity nodes.

## Phase 1 Workflow

### Baseline Nodes
1. Load Checkpoint
2. CLIP Text Encode (positive)
3. CLIP Text Encode (negative)
4. Empty Latent Image
5. KSampler
6. VAE Decode
7. Save Image

### Basic Wiring
- `Load Checkpoint` model -> `KSampler` model
- `Load Checkpoint` clip -> both `CLIP Text Encode` nodes
- positive conditioning -> `KSampler` positive
- negative conditioning -> `KSampler` negative
- `Empty Latent Image` -> `KSampler` latent_image
- `KSampler` samples -> `VAE Decode` samples
- `Load Checkpoint` vae -> `VAE Decode` vae
- `VAE Decode` image -> `Save Image` images

## Recommended Starter Settings
- resolution: 832x1216 or 768x1152
- steps: 24-30
- cfg: 5.5-7
- sampler: euler or dpmpp_2m
- scheduler: normal
- batch: 1

## First Prompt Shape
Positive:
"photorealistic Indian woman, 23 year old Bangalore Gen Z girl, medium brown skin, expressive dark eyes, black slightly wavy hair, oversized light blue shirt over white tank top, subtle dewy makeup, small hoop earrings, candid lifestyle photo outside Bangalore cafe near metro street, natural daylight, realistic smartphone photo"

Negative:
"plastic skin, extra fingers, duplicate person, glamour model, western celebrity, doll face, heavy makeup, unrealistic background, blurred face, overprocessed skin"

## Phase 2 Additions
After the first working generation:
- save 3-5 best portraits
- add identity-preserving nodes
- move to scene variants

## Phase 3 Video
Use still outputs first for:
- reel covers
- story stills
- storyboard frames

Then add:
- talking-head animation
- image-to-video motion workflow
