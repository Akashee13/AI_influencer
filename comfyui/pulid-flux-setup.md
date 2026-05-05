# PuLID-Flux Setup

This setup enables the face-first workflow:

- `mumbai-yoga-anchor-faceid-v1.json`

It is intended for:

- strong anchor face retention
- prompt-controlled clothes
- prompt-controlled background
- less dependence on a scene reference image

## What To Install

Custom node:

- `ComfyUI-PuLID-Flux`

Model files expected by the workflow:

- `ComfyUI/models/pulid/pulid_flux_v0.9.0.safetensors`
- `ComfyUI/models/clip/clip_l.safetensors`
- `ComfyUI/models/clip/t5xxl_fp8_e4m3fn.safetensors`
- `ComfyUI/models/clip/EVA02_CLIP_L_336_psz14_s6B.pt` if auto-download fails
- `ComfyUI/models/vae/ae.safetensors`
- `ComfyUI/models/unet/flux1-dev-fp8.safetensors`
- `ComfyUI/models/insightface/models/antelopev2/*`

## VM Commands

Run on the ComfyUI VM:

```bash
cd ~/comfy/custom_nodes
git clone https://github.com/balazik/ComfyUI-PuLID-Flux.git
cd ~/comfy/custom_nodes/ComfyUI-PuLID-Flux
python3 -m pip install -r requirements.txt
python3 -m pip install facexlib insightface onnxruntime-gpu
mkdir -p ~/comfy/models/pulid
mkdir -p ~/comfy/models/clip
mkdir -p ~/comfy/models/vae
mkdir -p ~/comfy/models/unet
mkdir -p ~/comfy/models/insightface/models
```

## Runtime Mismatch Fix (timestep_zero_index)

If runs fail with:

`forward_orig() got an unexpected keyword argument 'timestep_zero_index'`

use the repo repair script from the VM checkout:

```bash
cd ~/ai-influencer
chmod +x scripts/fix_flux_timestep_zero_index.sh
sudo ./scripts/fix_flux_timestep_zero_index.sh
```

What this does:

- updates `ComfyUI-PuLID-Flux` to latest upstream
- reinstalls node Python dependencies
- installs a small startup patch under `~/comfy/custom_nodes/ai_influencer_runtime_compat`
- restarts ComfyUI

This patch is a bridge for mixed-version stacks. Keep ComfyUI and custom nodes aligned as the long-term state.

## Required Downloads

Download these into the matching folders above:

- PuLID Flux model:
  - [pulid_flux_v0.9.0.safetensors](https://huggingface.co/guozinan/PuLID/blob/main/pulid_flux_v0.9.0.safetensors?download=true)
- AntelopeV2 InsightFace bundle:
  - [antelopev2](https://huggingface.co/MonsterMMORPG/tools/tree/main)
- EVA CLIP manual fallback:
  - [EVA02_CLIP_L_336_psz14_s6B.pt](https://huggingface.co/QuanSun/EVA-CLIP/blob/main/EVA02_CLIP_L_336_psz14_s6B.pt?download=true)

If your VM already has these FLUX assets, keep the filenames aligned with the workflow:

- `flux1-dev-fp8.safetensors`
- `t5xxl_fp8_e4m3fn.safetensors`
- `clip_l.safetensors`
- `ae.safetensors`

## Restart

After installing the node and model files:

```bash
pkill -f main.py || true
cd ~/comfy
nohup python3 main.py --listen 0.0.0.0 --port 8188 > ~/comfy.log 2>&1 &
sleep 5
tail -50 ~/comfy.log
```

Then restart the gateway:

```bash
cd ~/ai-influencer
pkill -f comfyui_gateway.py || true
nohup python3 services/comfyui_gateway.py > ~/comfyui-gateway.log 2>&1 &
sleep 2
tail -20 ~/comfyui-gateway.log
```

## Workflow Behavior

Use `mumbai-yoga-anchor-faceid-v1.json` when:

- anchor face consistency matters most
- you want to change clothes
- you want to change background
- you do not want the source image to dominate the composition

This workflow expects:

- `Anchor Face Reference` in the UI
- no `Scene Reference Image`

## Notes

- The workflow uses `PulidFluxInsightFaceLoader` with `CPU` by default for safety.
- If your ComfyUI stack supports the GPU provider cleanly, you can change that node later.
- The current workflow does not rely on a negative prompt branch.
