# Quickstart: QA Harness Agent

## Run

```bash
cd "/Users/akash/Documents/PetProjects/AI Influencer"
python3 scripts/qa_harness.py
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
