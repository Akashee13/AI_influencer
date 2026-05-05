# Implementation Plan: Regression-Safe Workflow Governance

Feature: [001-regression-safe-workflow-governance](./spec.md)
Created: 2026-05-05
Status: Draft

## Goal

Establish a Spec Kit-compliant governance baseline and align workflow identity binding, scene-reference behavior, and runtime parity across gateway, UI, and CLI without regressing older accepted behavior.

## Constitution Check

### Article I: Regression-Safe Evolution

Risk surfaces:

- workflow selection and defaults
- face reference locking
- scene reference editing
- CLI vs gateway submission behavior
- legacy workflow handling in the dashboard

Mitigation:

- isolate workflow-to-face binding in repository config
- keep workflow contracts explicit in metadata returned by gateway
- validate one legacy workflow alongside the new face-ID workflow

### Article II: Workflow Contract First

Chosen ownership:

- workflow JSON describes node structure and input roles
- `comfyui/workflow_bindings.json` owns workflow-to-anchor binding
- gateway normalizes runtime behavior
- UI renders only the controls allowed by gateway-exposed capabilities

### Article III: Gateway Is the Operational Source of Truth

Gateway remains the canonical operational adapter. CLI must reuse equivalent asset-preparation and binding logic.

### Article IV: Deterministic Identity Behavior

Face-locked workflows must:

- force repository-bound anchor face
- keep blank seed behavior randomized
- preserve deterministic intent for non-blank default seed

### Article V: Operator Clarity

UI must:

- remove misleading editable face-upload affordance on locked workflows
- keep scene-upload affordance enabled when supported
- clearly display locked face binding

## Technical Approach

### 1. Governance scaffolding

Add Spec Kit-style repository structure:

- `.specify/memory/constitution.md`
- `specs/001-regression-safe-workflow-governance/spec.md`
- `specs/001-regression-safe-workflow-governance/plan.md`
- `specs/001-regression-safe-workflow-governance/tasks.md`
- `specs/001-regression-safe-workflow-governance/quickstart.md`

Use that structure as the required workflow for future non-trivial changes, not just as bootstrap scaffolding.

### 2. Binding source of truth

Add a repo config file:

- `comfyui/workflow_bindings.json`

Responsibilities:

- map workflow filename to anchor face image
- map workflow filename to repository asset path
- declare whether the workflow face is locked

### 3. Workflow contract alignment

Ensure the face-ID workflow JSON exposes separate input roles for:

- `face_reference_image`
- `scene_reference_image`

### 4. Runtime parity

Align:

- `services/comfyui_gateway.py`
- `scripts/comfyui_generate.py`

Shared behaviors:

- workflow name injection for binding lookup
- repository asset copy into ComfyUI input
- locked face enforcement
- scene reference application without face replacement

### 5. UI alignment

Update `web/dashboard.html` so that:

- locked face upload controls are hidden or non-editable
- scene reference controls remain available
- locked face binding is shown as repository-owned state

## Files In Scope

- [services/comfyui_gateway.py](/Users/akash/Documents/PetProjects/AI Influencer/services/comfyui_gateway.py)
- [scripts/comfyui_generate.py](/Users/akash/Documents/PetProjects/AI Influencer/scripts/comfyui_generate.py)
- [web/dashboard.html](/Users/akash/Documents/PetProjects/AI Influencer/web/dashboard.html)
- [mumbai-yoga-anchor-faceid-v1.json](/Users/akash/Documents/PetProjects/AI Influencer/comfyui/workflows/mumbai-yoga-anchor-faceid-v1.json)
- [workflow_bindings.json](/Users/akash/Documents/PetProjects/AI Influencer/comfyui/workflow_bindings.json)
- [.specify/memory/constitution.md](/Users/akash/Documents/PetProjects/AI Influencer/.specify/memory/constitution.md)
- [spec.md](/Users/akash/Documents/PetProjects/AI Influencer/specs/001-regression-safe-workflow-governance/spec.md)
- [tasks.md](/Users/akash/Documents/PetProjects/AI Influencer/specs/001-regression-safe-workflow-governance/tasks.md)

## Validation Strategy

### Manual validation

1. Select face-ID workflow in UI.
2. Confirm locked face is shown and not user-editable.
3. Confirm scene reference upload and URL fetch remain editable.
4. Submit face-ID workflow through UI.
5. Submit the same workflow through gateway curl.
6. Submit the same workflow through CLI helper.
7. Validate one legacy workflow still pre-fills and submits as expected.

### Code validation

1. Python compile check for gateway and CLI.
2. Basic JS syntax check for dashboard script.

## Open Constraints

1. ComfyUI runtime success still depends on installed models and nodes on VM.
2. Deterministic identity is bounded by the model stack, not just application logic.
3. The current spec governs image workflows only; video-reference workflows remain out of scope.
