# Tasks: Face-Locked FLUX Runtime Compatibility

Feature: [003-face-locked-flux-runtime-compatibility](./spec.md)

## Phase 1: Investigation

- [x] Inspect the failing QA artifacts in `docs/gap-finding/20260505_194255_mumbai-yoga-anchor-faceid-v1.json_b55a20dc/`.
- [x] Confirm whether the root cause is workflow-path incompatibility, runtime version drift, or gateway reporting drift.
- [x] Identify the smallest owning surface that can restore compatibility without changing the user-facing workflow contract.

## Phase 2: Implementation

- [x] Update the relevant workflow, runtime assumptions, or gateway handling to eliminate the `timestep_zero_index` execution failure.
- [x] Update gateway and QA harness handling so terminal ComfyUI execution errors are recorded as errors instead of misleading completed runs.
- [x] Add targeted gateway logging for request intake, override application, input-asset assignment, prompt submission, and terminal error extraction so the next runtime iteration is diagnosable from logs.
- [x] Update the dashboard result gallery and detail view so failed runs render as failed states with error context instead of generic empty preview cards.
- [ ] Preserve locked anchor-face behavior and editable scene-reference behavior for `mumbai-yoga-anchor-faceid-v1.json`.
- [ ] Keep workflow discovery and submission behavior aligned with the existing gateway contract.
- [x] Update the affected spec artifacts and validation notes to capture the repeated failing QA evidence and the current repair path.
- [ ] Deploy the updated gateway/runtime changes to the environment that serves the live QA path.

## Phase 3: Validation

- [x] Reproduce the original failure once from the saved QA report and run metadata.
- [x] Compare the saved failing QA runs to confirm the issue is stable across reruns and not a one-off gateway artifact.
- [x] Re-run the default QA pass through `scripts/qa_harness.py`.
- [x] Confirm the rerun is now surfaced as `status: error` with `error_text` instead of being masked as completed.
- [ ] Confirm the rerun produces at least one output artifact and no `forward_orig() ... timestep_zero_index` failure.
- [ ] Confirm the QA report can evaluate image quality dimensions instead of stopping at execution failure.
- [ ] Run one older workflow submission path as a non-regression check.
