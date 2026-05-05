# Tasks: Human-Friendly Run Submission UX

Feature: [004-human-friendly-run-submission-ux](./spec.md)

## Phase 1: Spec Refinement

- [x] Tighten the problem statement from operator evidence.
- [x] Confirm the owning surface and regression risk.
- [x] Finalize the validation path.

## Phase 2: Implementation

- [x] Redesign the submit-run UI into a guided human-friendly flow.
- [x] Add workflow summary and live readiness feedback driven by workflow capabilities.
- [x] Move low-level overrides into an advanced section without changing submit payload behavior.
- [x] Keep gateway, workflow, UI, and CLI behavior aligned as required by the spec.

## Phase 3: Validation

- [x] Reproduce the original gap before the fix by inspecting the current submit form.
- [x] Re-run the relevant operator flow after the fix at code level by inspecting the guided states and confirming script syntax.
- [x] Confirm no regression on the previously accepted path by preserving the existing `/generate` override assembly.
- [ ] Perform a live browser pass against the running dashboard.
