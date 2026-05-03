# ComfyUI API Runner

We now have a locked workflow at:

- [mumbai-yoga-anchor-v1.json](/Users/akash/Documents/PetProjects/AI Influencer/comfyui/workflows/mumbai-yoga-anchor-v1.json)

And a local runner script at:

- [comfyui_generate.py](/Users/akash/Documents/PetProjects/AI Influencer/scripts/comfyui_generate.py)

## What this does

The script:

1. loads the UI-exported workflow JSON
2. updates prompts/settings if you pass overrides
3. converts the UI workflow into ComfyUI's API prompt format
4. submits the job to your ComfyUI server over `http://127.0.0.1:8188`

## Basic usage

Keep the SSH tunnel to the VM open, then run from this repo:

```bash
python3 scripts/comfyui_generate.py --wait
```

That will submit the locked `mumbai-yoga-anchor-v1.json` workflow as-is.

## Override prompt/settings

```bash
python3 scripts/comfyui_generate.py \
  --positive-prompt "ultra realistic mirror selfie photo of the same face identity as the selected Indian yoga instructor anchor, premium Indian wellness creator look, fair-light wheatish Indian skin with warm golden undertones, distinctly Indian facial features, deep black-brown Indian eyes, fit toned feminine body, black athletic sports bra, taupe high-waisted yoga leggings, upscale apartment mirror selfie, realistic smartphone photo, natural daylight, sharp focus, crisp facial details" \
  --negative-prompt "western celebrity face, generic international model face, non-Indian face, plastic skin, glossy skin, over-smoothed skin, blurry, blur, out of focus, soft focus, bad anatomy, cartoon, illustration" \
  --control-after-generate fixed \
  --filename-prefix mumbai-yoga-mirror \
  --wait
```

## Useful overrides

- `--seed 774215085774890`
- `--control-after-generate fixed`
- `--width 896`
- `--height 1344`
- `--steps 50`
- `--cfg 2.0`
- `--sampler euler`
- `--scheduler normal`

## Current locked anchor settings

- workflow: `mumbai-yoga-anchor-v1.json`
- checkpoint: `flux1-dev-fp8.safetensors`
- seed: `774215085774890`
- control: `fixed`
- resolution: `896 x 1344`
- steps: `50`
- cfg: `2.0`
- sampler: `euler`
- scheduler: `normal`

## Important note

This script talks to `127.0.0.1:8188`, so your SSH tunnel must stay open:

```bash
gcloud compute ssh instance-20260501-111318 --zone asia-east1-c --project pet-slay -- -L 8188:127.0.0.1:8188
```
