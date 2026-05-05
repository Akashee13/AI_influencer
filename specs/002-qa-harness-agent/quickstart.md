# Quickstart: QA Harness Agent

## Run

```bash
cd "/Users/akash/Documents/PetProjects/AI Influencer"
python3 scripts/qa_harness.py
```

## Local Defaults

You can store local-only defaults in:

```text
qa_harness.local.json
```

This file is gitignored. Start from:

- [qa_harness.local.example.json](/Users/akash/Documents/PetProjects/AI%20Influencer/qa_harness.local.example.json)

Example:

```json
{
  "gateway_url": "http://127.0.0.1:9000",
  "gateway_token": "replace-this-with-a-real-long-secret",
  "default_workflow": "mumbai-yoga-anchor-faceid-v1.json",
  "default_scene_url": "https://www.instagram.com/p/DXoinABDVRc/",
  "default_filename_prefix": "qa-mumbai-yoga-anchor-faceid-v1.json"
}
```

## What It Does

1. Prompts for gateway URL and token.
2. Lists workflows from the gateway.
3. Asks for expected outcome and scene reference link if applicable.
4. Uploads the scene reference through the gateway.
5. Submits the run and polls until completion.
6. Downloads the first output into `data/qa_runs/...`.
7. Asks for structured QA judgments.
8. Writes a markdown gap report.

## Output

Each QA run creates a folder under:

```text
docs/gap-finding/<timestamp>_<workflow>_<prompt_id>/
```

Expected artifacts:

- `report.md`
- `run.json`
- downloaded result image when available
