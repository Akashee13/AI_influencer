# Implementation Plan: Human-Friendly Run Submission UX

Feature: [004-human-friendly-run-submission-ux](./spec.md)
Created: 2026-05-05
Status: In Progress

## Goal

Translate operator feedback into a safer, guided submit-run experience without changing the gateway payload contract.

## Constitution Check

### Article I: Regression-Safe Evolution

Previously working behavior that could regress:

- workflow capability detection from `/workflows`
- face-reference upload and URL fetch flows
- scene-reference upload and URL fetch flows
- advanced override fields that map to `/generate`
- prompt-section editing and preset application

### Article II: Workflow Contract First

The affected contract surface is the dashboard rendering of gateway-provided workflow defaults. The request sent to `/generate` must remain structurally unchanged.

### Article III: Gateway Is the Operational Source of Truth

The gateway remains the source of truth for workflow capability metadata. This change is UI-only unless a missing capability signal is discovered during implementation.

### Article VI: Validation Before Merge

Validation requires:

1. Inspecting at least one workflow that locks face identity.
2. Inspecting at least one workflow that requires a scene reference.
3. Verifying the UI clearly reports readiness and missing prerequisites.
4. Confirming a valid submit still sends the same payload shape to `/generate`.

## Technical Approach

### 1. Root cause framing

The current submit card is organized around internal fields instead of operator decisions. Required and optional inputs are mixed together, and the only meaningful guidance lives in small helper text that assumes familiarity with face-lock and scene-guidance concepts.

### 2. Intended fix shape

Restructure the left submit panel into guided sections:

- session access
- workflow selection with plain-language summary
- live readiness checklist
- required reference inputs
- advanced controls in a collapsible section
- clearer submit CTA and status copy

Keep the existing prompt composition experience, but make the entry path to a valid run much easier.

### 3. Validation strategy

List the manual and automated checks to run:

1. `python3 -m py_compile` is not relevant for this HTML-only pass.
2. Inspect the generated DOM structure for the new guided sections and required IDs.
3. Sanity-check the submit logic to confirm `/generate` payload construction is unchanged.
4. Manually test the dashboard in a browser after patching when possible.

## Files In Scope

- [spec.md](/Users/akash/Documents/PetProjects/AI Influencer/specs/004-human-friendly-run-submission-ux/spec.md)
- [plan.md](/Users/akash/Documents/PetProjects/AI Influencer/specs/004-human-friendly-run-submission-ux/plan.md)
- [tasks.md](/Users/akash/Documents/PetProjects/AI Influencer/specs/004-human-friendly-run-submission-ux/tasks.md)
- [quickstart.md](/Users/akash/Documents/PetProjects/AI Influencer/specs/004-human-friendly-run-submission-ux/quickstart.md)
- [dashboard.html](/Users/akash/Documents/PetProjects/AI Influencer/web/dashboard.html)

## Validation Strategy

1. Confirm the old UX issue by inspecting the current form: internal concepts are exposed up front and missing prerequisites are not summarized.
2. Implement the guided UX directly in [dashboard.html](/Users/akash/Documents/PetProjects/AI Influencer/web/dashboard.html).
3. Re-open the page and verify the workflow summary, readiness checklist, advanced section, and submit CTA behavior.
4. Confirm no regression in submit payload construction.
