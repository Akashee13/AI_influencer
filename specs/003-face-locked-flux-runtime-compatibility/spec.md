# Feature Specification: Face-Locked FLUX Runtime Compatibility

Feature ID: 003-face-locked-flux-runtime-compatibility
Status: Draft
Created: 2026-05-05
Owner: Repository maintainers

## Summary

The repository needs a compatibility guardrail for face-locked FLUX workflows so the default `mumbai-yoga-anchor-faceid-v1.json` path can complete image generation on the installed ComfyUI stack instead of failing during sampler execution.

Source QA report:

- `docs/gap-finding/20260505_194255_mumbai-yoga-anchor-faceid-v1.json_b55a20dc/report.md`

## Problem Statement

The latest QA pass proved that workflow selection, scene-reference upload, and gateway submission all work, but the face-locked FLUX workflow still fails before producing an image. The run reached `SamplerCustomAdvanced` and crashed with `TypeError: forward_orig() got an unexpected keyword argument 'timestep_zero_index'`.

This leaves the system in a misleading state:

- the operator can start a default QA pass successfully
- the gateway marks the run as completed from its perspective
- no image is generated or downloadable
- the QA process cannot evaluate anchor retention, scene adaptation, wardrobe adaptation, or realism

Existing specs cover workflow governance and the QA harness flow, but they do not yet require runtime compatibility checks or operator-visible handling for this class of ComfyUI stack mismatch.

## Goals

1. Define the operator-visible behavior required for a face-locked FLUX workflow to complete on the installed runtime stack.
2. Make runtime ownership explicit across workflow JSON, gateway behavior, and the ComfyUI/PuLID-Flux environment.
3. Prevent future runtime-signature mismatches from silently blocking the default face-locked workflow.
4. Reuse the existing default QA pass as proof that the workflow is operational again.

## Non-Goals

1. Redesign the visual prompt content or creative direction of the workflow.
2. Replace the current gateway architecture or ComfyUI deployment model.
3. Fully automate visual quality grading after the run completes.

## User Stories

### Story 1: Restored default face-locked run

As an operator, I want the default face-locked workflow to complete image generation through the gateway so the QA process can evaluate the actual output instead of stopping at a runtime error.

Acceptance criteria:

- Running the default QA pass against `mumbai-yoga-anchor-faceid-v1.json` completes without the `timestep_zero_index` signature error.
- The run record includes at least one output artifact or download path.
- The QA report can judge the produced image instead of recording an execution-blocking failure.

### Story 2: Runtime compatibility ownership

As a maintainer, I want the repo to state which surface owns compatibility between workflow design and the installed ComfyUI/PuLID-Flux stack so failures like this are caught and fixed intentionally.

Acceptance criteria:

- The spec identifies the gateway/runtime stack as the operational source of truth for execution compatibility.
- Any required workflow or runtime adjustment is documented as part of the fix path.
- Validation proves the fix on the same workflow and input path that failed.

### Story 3: Non-regression for other paths

As a maintainer, I want the compatibility fix to preserve previously accepted gateway and workflow behavior so the runtime repair does not break older workflows or workflow metadata exposure.

Acceptance criteria:

- Existing workflow discovery still works.
- Scene-reference upload still works for the face-locked workflow.
- At least one older workflow path still submits successfully after the compatibility fix.

## Functional Requirements

### FR-1 Gap closure

The default face-locked FLUX workflow MUST complete end-to-end generation on the maintained runtime stack without failing at sampler/model execution due to incompatible call signatures.

### FR-2 Surface ownership

The fix package MUST identify which combination of these surfaces owns the runtime compatibility contract:

- workflow JSON
- gateway execution path
- ComfyUI core version
- custom sampler path
- PuLID-Flux node stack

The gateway remains the operational source of truth for the execution path, but the spec MUST record any runtime or workflow constraints required for compatibility.

### FR-3 Validation

The fix MUST be validated by re-running the same default QA pass that produced the source report and confirming that:

- the run no longer fails with `forward_orig() got an unexpected keyword argument 'timestep_zero_index'`
- the run produces a downloadable output artifact or equivalent captured image result
- the resulting QA report can evaluate image quality dimensions instead of stopping at runtime failure

### FR-4 Failure transparency

If a runtime mismatch still occurs, the gateway or QA path MUST expose it clearly enough that operators and maintainers can distinguish:

- request-submission success
- execution failure before image generation
- missing output artifact capture

### FR-5 Non-regression validation

The fix MUST verify that:

- workflow discovery still returns `mumbai-yoga-anchor-faceid-v1.json`
- scene-reference upload still succeeds for that workflow
- at least one previously accepted non-face-locked workflow path still submits successfully

## Success Metrics

1. A rerun of the default QA pass produces an image instead of the recorded sampler/model signature error.
2. The generated run exposes an output artifact that the QA harness can download or reference locally.
3. The face-locked workflow remains selectable and scene-reference capable on the gateway path.
4. A legacy workflow path remains operational after the compatibility fix.

## Risks

1. Fixing the sampler/runtime mismatch may require version alignment that affects other workflows.
2. A workflow-only patch could mask a deeper ComfyUI or custom-node incompatibility.
3. Output download behavior may remain broken even after generation succeeds, so validation must check both generation and artifact capture.
