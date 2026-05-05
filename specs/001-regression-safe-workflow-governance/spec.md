# Feature Specification: Regression-Safe Workflow Governance

Feature ID: 001-regression-safe-workflow-governance
Status: Draft
Created: 2026-05-05
Owner: Repository maintainers

## Summary

The repository needs a governed workflow model that prevents new features from breaking earlier requirements. In particular, workflow-bound anchor identity, scene reference editing, gateway/CLI parity, and UI truthfulness must be specified before additional workflow logic is changed.

## Problem Statement

Recent iterations added face-ID and reference-image capabilities, but some updates introduced regressions:

- older workflow expectations were broken by new behavior
- face image ownership moved ambiguously between workflow JSON, UI inputs, and runtime logic
- scene reference behavior became unclear or disabled in workflows that should allow it
- gateway and CLI behavior drifted

The system needs a stable contract that defines what each workflow controls and what each surface is allowed to edit.

## Goals

1. Preserve existing accepted gateway/UI behavior while new workflow capabilities are added.
2. Make workflow-to-anchor identity ownership explicit and repository-controlled.
3. Keep scene/reference uploads editable when a workflow promises “fixed face, variable inspiration”.
4. Ensure UI, gateway, CLI, and workflow configuration describe the same behavior.
5. Create spec artifacts that future changes must extend rather than bypass.

## Non-Goals

1. Introduce video-reference generation in this feature.
2. Redesign the entire dashboard information architecture.
3. Replace ComfyUI or the current FLUX-based generation stack.

## User Stories

### Story 1: Locked Anchor Identity

As an operator, when I choose a face-locked workflow, I want the anchor face to come from repository configuration automatically so I do not accidentally replace it through the UI.

Acceptance criteria:

- Selecting a face-locked workflow does not require a user-uploaded face image.
- The UI clearly communicates that face identity is locked to repository config.
- The runtime always uses the repository-bound anchor face for that workflow.

### Story 2: Editable Scene Reference

As an operator, when I choose a face-locked workflow, I still want to upload or paste a scene/reference image so the output can follow that style or composition while retaining the workflow’s anchor identity.

Acceptance criteria:

- Scene reference upload remains editable for workflows that support scene inspiration.
- Face reference and scene reference do not overwrite each other internally.
- The workflow contract makes clear which node/input is face identity and which is scene inspiration.

### Story 3: Operational Consistency

As an operator or maintainer, I want the dashboard and CLI helper to behave consistently with the gateway so that successful runs in one path do not fail in another due to missing preparation logic.

Acceptance criteria:

- Gateway and CLI submit the same logical workflow after repository-bound assets are prepared.
- Runtime-preparation differences are documented or eliminated.
- Validation proves parity for at least one face-locked workflow.

### Story 4: Non-Regression Discipline

As a maintainer, I want future changes to start from a written spec and task list so that new requirements stop silently overriding older ones.

Acceptance criteria:

- A written constitution exists in the repository.
- A feature-level spec, plan, and tasks file exist for this effort.
- Future workflow changes can reference these artifacts directly.

## Functional Requirements

### FR-1 Workflow binding configuration

The repository MUST support a config-driven mapping from workflow name to anchor identity binding data, including:

- locked anchor face image filename
- source path in repository
- whether face reference is locked to the workflow

### FR-2 Workflow contract exposure

The gateway MUST expose enough workflow metadata for the UI to know whether a workflow supports:

- face reference input
- scene reference input
- locked face binding

### FR-3 Face and scene separation

For any workflow promising fixed face plus scene inspiration:

- face identity input and scene reference input MUST be represented separately
- a user scene upload MUST not replace the workflow-bound face input

### FR-4 UI truthfulness

The dashboard MUST:

- hide or disable user controls that are not actually editable
- keep scene reference controls available when the workflow supports them
- display the locked face binding clearly

### FR-5 Gateway and CLI parity

The gateway and CLI helper MUST both prepare repository-bound input assets before submission for workflows that depend on them.

### FR-6 Seed semantics

The system MUST preserve current seed rules:

- default workflow seed remains deterministic intent
- blank seed means explicit randomization

### FR-7 Validation checklist

This feature MUST ship with a manual validation flow covering:

- face-locked workflow through gateway
- face-locked workflow through UI
- face-locked workflow through CLI
- one legacy workflow non-regression path

## Success Metrics

1. A face-locked workflow can be selected in the UI without asking the user for anchor face input.
2. A scene reference can still be uploaded for that workflow.
3. Gateway and CLI both submit the workflow successfully after required model assets are present.
4. Existing text/reference workflows keep their previous operator behavior.

## Risks

1. Workflow JSON and runtime bindings may drift if not documented together.
2. UI may display editable controls for unsupported workflow roles.
3. ComfyUI model or node availability can still block runtime success independently of spec compliance.
