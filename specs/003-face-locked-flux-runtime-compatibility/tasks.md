# Tasks: Face-Locked FLUX Runtime Compatibility

Feature: [003-face-locked-flux-runtime-compatibility](./spec.md)

## Phase 1: Investigation

- [ ] Inspect the failing QA artifacts in `docs/gap-finding/20260505_194255_mumbai-yoga-anchor-faceid-v1.json_b55a20dc/`.
- [ ] Confirm whether the root cause is workflow-path incompatibility, runtime version drift, or gateway reporting drift.
- [ ] Identify the smallest owning surface that can restore compatibility without changing the user-facing workflow contract.

## Phase 2: Implementation

- [ ] Update the relevant workflow, runtime assumptions, or gateway handling to eliminate the `timestep_zero_index` execution failure.
- [ ] Preserve locked anchor-face behavior and editable scene-reference behavior for `mumbai-yoga-anchor-faceid-v1.json`.
- [ ] Keep workflow discovery and submission behavior aligned with the existing gateway contract.
- [ ] Update any affected docs or config that define the compatible runtime path.

## Phase 3: Validation

- [ ] Reproduce the original failure once from the saved QA report and run metadata.
- [ ] Re-run the default QA pass through `scripts/qa_harness.py`.
- [ ] Confirm the rerun produces at least one output artifact and no `forward_orig() ... timestep_zero_index` failure.
- [ ] Confirm the QA report can evaluate image quality dimensions instead of stopping at execution failure.
- [ ] Run one older workflow submission path as a non-regression check.
