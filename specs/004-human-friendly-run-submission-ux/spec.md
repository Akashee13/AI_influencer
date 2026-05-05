# Feature Specification: Human-Friendly Run Submission UX

Feature ID: 004-human-friendly-run-submission-ux
Status: In Progress
Created: 2026-05-05
Owner: Repository maintainers

## Summary

The dashboard submit-run experience is too context-heavy for human operators. It needs a guided flow that explains what a workflow does, which inputs are required, what is locked by the repo, what is optional, and when the run is actually ready to submit.

Source trigger:

- Operator feedback on 2026-05-05 that the current UI is only usable by someone who already understands the system.

## Problem Statement

The current dashboard exposes internal concepts such as face-lock behavior, scene-reference handling, filename prefixing, and raw generation overrides with very little progressive guidance. An operator can technically submit a run, but only if they already know which workflows need a scene reference, which ones lock the anchor face in repo config, and which inputs are safe to ignore. That makes the tool feel like a maintainer console instead of a human-friendly production surface.

## Goals

1. Make workflow choice understandable in plain language.
2. Show a live checklist of what is required before a run can be submitted.
3. Separate required operator steps from optional advanced controls.
4. Preserve the existing gateway contract and workflow behavior.

## Non-Goals

1. Redesigning the runs gallery beyond the failure-state improvements already delivered.
2. Changing workflow JSON semantics or gateway request payload shape.
3. Replacing the existing prompt-section authoring model.

## User Story

As an operator, I want the dashboard to tell me what this workflow needs and what I can safely ignore, so I can launch a valid run without having repo-specific context in my head.

## Functional Requirements

### FR-1 Gap closure

The submit-run surface must present the workflow in human language, including whether the face is workflow-locked, whether a scene reference is required, and whether the run is text-first or reference-guided.

### FR-2 Surface ownership

The source of truth for capability detection remains the workflow defaults returned by the gateway. The UI may translate those capabilities into friendlier labels, summaries, and readiness states, but it must not invent behavior that conflicts with the gateway or workflow JSON.

### FR-3 Validation

An operator must be able to open the dashboard, choose a workflow, understand the required inputs from the UI alone, and submit or intentionally postpone a run without confusion about missing prerequisites.

### FR-4 Progressive disclosure

Low-level options such as filename prefix, seed, batch size, width, and height must be moved into an advanced section so first-time operators see only the primary workflow decision, prompt authoring, and required references.

### FR-5 Readiness feedback

The UI must show a live readiness summary that reflects the selected workflow and any uploaded references, including clearly naming the next action when the run is not ready.

## Success Metrics

1. A first-time operator can identify the next required action from the submit surface without trial-and-error.
2. Valid workflows still submit through the same `/generate` contract.
3. Workflows with locked face references and workflows requiring scene references are both accurately represented.

## Risks

1. The UI could oversimplify workflow capabilities and imply optionality where the gateway still requires an asset.
2. Hiding advanced controls too aggressively could make power-user iteration slower if the controls become hard to discover.
