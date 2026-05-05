---
name: qa-gap-finding-agent
description: Use when the user wants to QA a ComfyUI workflow run against an expected outcome, especially for anchor-face consistency and scene-reference adaptation, and wants a markdown gap report saved under docs/gap-finding.
---

# QA Gap Finding Agent

This skill runs a structured QA pass for the AI Influencer generation system.

Use it when the user wants to:

- test a workflow against a reference post or scene image
- validate fixed anchor identity vs editable scene inspiration
- compare output with an expected outcome
- produce a markdown gap report under `docs/gap-finding`

## Core Contract

This skill is the reasoning layer. The bundled helper script is the deterministic execution layer.

- The skill should ask for missing QA intent and interpret the outcome.
- The script should handle gateway workflow discovery, upload, submission, polling, artifact download, and report scaffolding.

Do not replace judgment with a fixed script when the user wants qualitative evaluation.

## Inputs To Gather

Ask for or confirm:

1. workflow name
2. scene reference Instagram post or direct image URL, when the workflow supports scene guidance
3. expected outcome in plain language

Common expectation dimensions:

- face consistency to workflow anchor
- scene/style similarity to the reference
- wardrobe adaptation quality
- background adaptation quality
- overall realism

## Local Defaults

Before asking for gateway connection details, check for:

- `qa_harness.local.json` in the repo root

If present, use it for defaults:

- `gateway_url`
- `gateway_token`
- `default_workflow`
- `default_scene_url`
- `default_filename_prefix`

This file is intentionally gitignored.

## Execution Path

Preferred execution path:

1. Use `scripts/qa_harness.py` with CLI prefills for workflow and scene URL.
2. Let the script:
   - discover workflows from the gateway
   - upload scene reference
   - submit the run
   - poll to completion
   - download the first output
   - create the run directory under `docs/gap-finding`
3. After the script finishes, inspect:
   - generated `report.md`
   - generated `run.json`
   - downloaded output image path
4. Ask the user focused follow-up questions if the script report is incomplete.
5. Refine the report if needed so it becomes a useful engineering gap document.

## When To Ask Follow-Ups

Ask a follow-up when any of these are unclear:

- what “success” means for this run
- whether face consistency or scene imitation is the higher priority
- whether outfit similarity is desired or should be deliberately changed
- whether a partial pass is acceptable

Keep follow-ups short and concrete.

## Output Requirements

Every QA run should leave a folder under:

- `docs/gap-finding/<timestamp>_<workflow>_<prompt_id>/`

Expected artifacts:

- `report.md`
- `run.json`
- downloaded first output image, when available

The report should contain:

- workflow
- prompt ID
- source reference URL
- expected outcome
- structured ratings
- top gaps
- recommended fixes
- runtime metadata

## Recommended Workflow

### For a new QA pass

1. Confirm the workflow and reference URL.
2. Ask the user for expected outcome.
3. Run:
   - `python3 scripts/qa_harness.py --workflow ... --scene-url ...`
4. Wait for the script to complete.
5. Review the resulting report with the user and tighten any vague findings.

### For a follow-up analysis pass

1. Open the latest folder under `docs/gap-finding/`.
2. Read `report.md`.
3. Convert the reported gaps into:
   - concrete code/workflow fixes
   - spec/task updates
   - next QA experiment suggestions

## Notes

- For face-locked workflows, the face source should come from repo configuration, not user upload.
- Scene reference should remain operator-editable when the workflow contract allows it.
- The skill should prefer truthfulness over optimism: if a run proves the workflow is preserving the wrong thing, say so clearly.
