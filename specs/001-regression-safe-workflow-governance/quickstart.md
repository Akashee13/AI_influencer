# Quickstart: Validate Regression-Safe Workflow Governance

## Purpose

Use this checklist to verify that the repository honors fixed anchor identity while still allowing scene inspiration and does not regress older workflow behavior.

## Preconditions

1. ComfyUI is running on the VM.
2. Required FLUX and PuLID model assets are installed.
3. Gateway is running on port `9000`.
4. Dashboard is served from the gateway root.

## Validation Flow

### A. Face-ID workflow through UI

1. Open the dashboard.
2. Select `mumbai-yoga-anchor-faceid-v1.json`.
3. Confirm the anchor face is shown as locked repository state.
4. Confirm the scene reference field is still editable.
5. Upload or fetch a scene reference image.
6. Submit a run.

Expected:

- face input is not operator-editable
- scene input is operator-editable
- submission succeeds

### B. Face-ID workflow through gateway

Submit:

```bash
curl -X POST http://127.0.0.1:9000/generate \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer replace-this-with-a-real-long-secret' \
  -d '{
    "workflow": "mumbai-yoga-anchor-faceid-v1.json",
    "wait": false,
    "overrides": {
      "filename_prefix": "faceid-spec-check"
    }
  }'
```

Expected:

- response contains `ok: true`
- response contains `prompt_id`

### C. Face-ID workflow through CLI

```bash
cd ~/ai-influencer
python3 scripts/comfyui_generate.py \
  --workflow comfyui/workflows/mumbai-yoga-anchor-faceid-v1.json \
  --wait
```

Expected:

- workflow submits without missing asset-preparation behavior

### D. Legacy workflow non-regression

```bash
cd ~/ai-influencer
python3 scripts/comfyui_generate.py \
  --workflow comfyui/workflows/mumbai-yoga-anchor-v1.json \
  --wait
```

Expected:

- prior text workflow still submits successfully
- workflow defaults and UI prefill still behave as before
