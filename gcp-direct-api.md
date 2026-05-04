# Direct GCP API Flow

This removes the need for an SSH tunnel from your laptop.

## Architecture

1. `ComfyUI` stays on the VM and continues listening on `127.0.0.1:8188`.
2. `comfyui_gateway.py` runs on the same VM, talks to ComfyUI locally, and exposes a small authenticated API on port `9000`.
3. Your laptop hits the VM's public IP on `:9000`.

## Files

- Gateway service: [services/comfyui_gateway.py](/Users/akash/Documents/PetProjects/AI Influencer/services/comfyui_gateway.py)
- Deploy helper: [scripts/deploy_comfyui_gateway.sh](/Users/akash/Documents/PetProjects/AI Influencer/scripts/deploy_comfyui_gateway.sh)
- Locked workflow: [comfyui/workflows/mumbai-yoga-anchor-v1.json](/Users/akash/Documents/PetProjects/AI Influencer/comfyui/workflows/mumbai-yoga-anchor-v1.json)

## One-time VM setup

Copy the repo to the VM if it is not already there, then on the VM:

```bash
cd ~/ai-influencer
printf 'COMFYUI_GATEWAY_TOKEN=%s\n' 'replace-with-a-long-random-token' > .env.gateway
sudo ./scripts/deploy_comfyui_gateway.sh ~/ai-influencer
```

## Open the VM firewall

In GCP, create an ingress rule for TCP `9000` and restrict the source IP to your own IP if possible.

If using `gcloud`, it would look like:

```bash
gcloud compute firewall-rules create comfyui-gateway-9000 \
  --allow tcp:9000 \
  --direction INGRESS \
  --source-ranges YOUR.PUBLIC.IP.ADDRESS/32 \
  --target-tags comfyui-gateway
```

Then add the network tag `comfyui-gateway` to the VM.

## Health check

From your laptop:

```bash
curl http://VM_EXTERNAL_IP:9000/healthz
```

## Submit

From your laptop:

```bash
curl -X POST http://VM_EXTERNAL_IP:9000/generate \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer replace-with-a-long-random-token' \
  -d '{
    "workflow": "mumbai-yoga-anchor-v1.json",
    "overrides": {
      "filename_prefix": "mumbai-yoga-mirror",
      "positive_prompt": "ultra realistic mirror selfie photo of the same face identity as the selected Indian yoga instructor anchor, premium Indian wellness creator look, fair-light wheatish Indian skin with warm golden undertones, distinctly Indian facial features, deep black-brown Indian eyes, fit toned feminine body, black athletic sports bra, taupe high-waisted yoga leggings, upscale apartment mirror selfie, realistic smartphone photo, natural daylight, sharp focus, crisp facial details",
      "negative_prompt": "western celebrity face, generic international model face, non-Indian face, plastic skin, glossy skin, over-smoothed skin, blurry, blur, out of focus, soft focus, bad anatomy, cartoon, illustration",
      "seed": 774215085774890
    }
  }'
```

Expected response:

```json
{
  "ok": true,
  "workflow": "mumbai-yoga-anchor-v1.json",
  "client_id": "...",
  "prompt_id": "...",
  "status": "submitted"
}
```

## Poll status

```bash
curl -H 'Authorization: Bearer replace-with-a-long-random-token' \
  http://VM_EXTERNAL_IP:9000/status/PROMPT_ID
```

Suggested backoff for long-running jobs:

1. start at `5s`
2. double each time
3. cap at `60s`

Example sequence: `5s`, `10s`, `20s`, `40s`, `60s`, `60s`...

## Inspect history

```bash
curl -H 'Authorization: Bearer replace-with-a-long-random-token' \
  http://VM_EXTERNAL_IP:9000/history/PROMPT_ID
```

## Inspect queue

```bash
curl -H 'Authorization: Bearer replace-with-a-long-random-token' \
  http://VM_EXTERNAL_IP:9000/queue
```

## Why this is better

- no local tunnel required
- ComfyUI stays private on `127.0.0.1`
- only the small gateway is exposed
- workflow and seed stay locked in the repo
- submit is fire-and-forget by default
- polling works better for `~500s` average generations
