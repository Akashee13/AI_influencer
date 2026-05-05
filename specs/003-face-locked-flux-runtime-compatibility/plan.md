# Implementation Plan: Face-Locked FLUX Runtime Compatibility

Feature: [003-face-locked-flux-runtime-compatibility](./spec.md)
Created: 2026-05-05
Status: Draft

## Goal

Restore successful execution for the default face-locked FLUX workflow while keeping gateway behavior, workflow bindings, and older workflow paths stable.

## Constitution Check

### Article I: Regression-Safe Evolution

The default QA run proved that workflow discovery, scene-reference upload, and gateway submission are currently working. Any compatibility fix must avoid regressing:

- workflow listing from `/workflows`
- scene-reference upload through `/upload/reference-url`
- gateway submission for face-locked workflows
- submission behavior for older non-face-locked workflows

### Article II: Workflow Contract First

The affected contract is the face-locked FLUX workflow path for `mumbai-yoga-anchor-faceid-v1.json`, specifically the expectation that:

- anchor identity remains workflow-bound
- scene reference remains operator-editable
- the workflow actually executes on the installed runtime stack

This is a runtime compatibility failure, not a user-input ownership failure, but the contract must still describe which runtime assumptions the workflow depends on.

### Article III: Gateway Is the Operational Source of Truth

The gateway remains the operational truth for workflow execution, but it is only as correct as the workflow JSON and installed ComfyUI/custom-node stack it submits against. The plan should treat the likely ownership split as:

- workflow JSON defines the sampler/model path
- gateway submits and records runtime state
- ComfyUI core plus PuLID-Flux/custom sampler versions define whether that path is executable

### Article VI: Validation Before Merge

Validation must include:

- reproducing the current QA failure
- applying the runtime/workflow fix
- re-running the same default QA pass
- confirming image generation and output capture
- checking one older workflow path for non-regression

## Technical Approach

### 1. Root cause framing

The source QA report shows the request reaches runtime execution and fails inside `SamplerCustomAdvanced` during FLUX model forward execution. The concrete error is:

- `forward_orig() got an unexpected keyword argument 'timestep_zero_index'`

This strongly suggests a signature mismatch between the installed ComfyUI FLUX model path and the custom sampler or PuLID-Flux integration being exercised by the workflow.

### 2. Intended fix shape

Likely fix directions to evaluate:

1. Align the installed ComfyUI core and custom-node versions so the current workflow path is valid again.
2. Adjust the workflow to use a compatible sampler/model path if the current stack no longer supports this call path.
3. Improve gateway or QA reporting if generation can fail while the run still appears superficially complete.

The implementation should prefer the smallest change that restores the intended face-locked workflow behavior without changing its user-facing contract.

### 3. Validation strategy

Manual checks:

- run the default QA pass again against `mumbai-yoga-anchor-faceid-v1.json`
- confirm the run no longer throws the recorded `timestep_zero_index` error
- confirm the run yields an output artifact
- verify at least one legacy workflow still submits

Repo-level checks:

- syntax or config validation for any edited scripts
- workflow/config sanity review for any changed workflow JSON or binding files

## Files In Scope

- [spec.md](/Users/akash/Documents/PetProjects/AI Influencer/specs/003-face-locked-flux-runtime-compatibility/spec.md)
- [plan.md](/Users/akash/Documents/PetProjects/AI Influencer/specs/003-face-locked-flux-runtime-compatibility/plan.md)
- [tasks.md](/Users/akash/Documents/PetProjects/AI Influencer/specs/003-face-locked-flux-runtime-compatibility/tasks.md)
- [quickstart.md](/Users/akash/Documents/PetProjects/AI Influencer/specs/003-face-locked-flux-runtime-compatibility/quickstart.md)
- [report.md](/Users/akash/Documents/PetProjects/AI Influencer/docs/gap-finding/20260505_194255_mumbai-yoga-anchor-faceid-v1.json_b55a20dc/report.md)
- [run.json](/Users/akash/Documents/PetProjects/AI Influencer/docs/gap-finding/20260505_194255_mumbai-yoga-anchor-faceid-v1.json_b55a20dc/run.json)
- [mumbai-yoga-anchor-faceid-v1.json](/Users/akash/Documents/PetProjects/AI Influencer/comfyui/workflows/mumbai-yoga-anchor-faceid-v1.json)
- [workflow_bindings.json](/Users/akash/Documents/PetProjects/AI Influencer/comfyui/workflow_bindings.json)
- [comfyui_gateway.py](/Users/akash/Documents/PetProjects/AI Influencer/services/comfyui_gateway.py)
- [qa_harness.py](/Users/akash/Documents/PetProjects/AI Influencer/scripts/qa_harness.py)

## Validation Strategy

1. Reproduce the QA gap.
2. Identify whether the minimal viable fix belongs in workflow JSON, runtime version alignment, or gateway reporting.
3. Implement the fix after spec approval.
4. Re-run the same default QA path through the harness.
5. Confirm output capture and one older workflow non-regression path.
