# Tasks: Regression-Safe Workflow Governance

Feature: [001-regression-safe-workflow-governance](./spec.md)

## Phase 1: Governance Foundation

- [x] Create Spec Kit-compatible repository scaffolding under `.specify/` and `specs/`.
- [x] Write project constitution focused on regression safety, workflow contracts, runtime truth, and validation discipline.
- [x] Write initial feature spec for workflow governance and non-regression requirements.
- [x] Write implementation plan aligned to current repository architecture.
- [x] Write operator quickstart for manual validation.

## Phase 2: Binding and Contract Separation

- [x] Keep workflow-to-anchor binding in repository config file rather than editable UI state.
- [x] Ensure face-ID workflow exposes separate face and scene reference roles.
- [x] Ensure gateway exposes workflow capabilities needed by the UI.

Files:

- [workflow_bindings.json](/Users/akash/Documents/PetProjects/AI Influencer/comfyui/workflow_bindings.json)
- [mumbai-yoga-anchor-faceid-v1.json](/Users/akash/Documents/PetProjects/AI Influencer/comfyui/workflows/mumbai-yoga-anchor-faceid-v1.json)
- [comfyui_gateway.py](/Users/akash/Documents/PetProjects/AI Influencer/services/comfyui_gateway.py)

## Phase 3: Runtime Parity

- [x] Align CLI submit behavior with gateway asset-preparation behavior.
- [x] Enforce locked face usage for face-bound workflows.
- [x] Preserve editable scene reference submission for scene-capable workflows.

Files:

- [comfyui_gateway.py](/Users/akash/Documents/PetProjects/AI Influencer/services/comfyui_gateway.py)
- [comfyui_generate.py](/Users/akash/Documents/PetProjects/AI Influencer/scripts/comfyui_generate.py)

## Phase 4: UI Truthfulness

- [x] Remove misleading editable anchor-face controls for locked workflows.
- [x] Keep scene reference upload/link controls enabled where supported.
- [x] Surface locked face binding clearly in the operator UI.

Files:

- [dashboard.html](/Users/akash/Documents/PetProjects/AI Influencer/web/dashboard.html)

## Phase 5: Validation and Non-Regression

- [x] Compile-check Python entry points.
- [x] Syntax-check dashboard script.
- [ ] Validate face-ID workflow through gateway.
- [ ] Validate face-ID workflow through CLI.
- [ ] Validate one legacy workflow for non-regression.

## Exit Criteria

- [x] Constitution, spec, plan, tasks, and quickstart are present in repo.
- [ ] Face-locked workflow behaves as “fixed identity, editable scene inspiration”.
- [ ] Gateway, UI, and CLI describe the same workflow contract.
- [ ] Older accepted workflow behavior remains intact.
