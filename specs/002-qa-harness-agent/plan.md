# Implementation Plan: QA Harness Agent

Feature: [002-qa-harness-agent](./spec.md)
Created: 2026-05-05
Status: Draft

## Goal

Create a lightweight interactive QA harness that tests workflows through the gateway and writes structured markdown reports for regression analysis and creative quality review.

## Constitution Check

### Article I: Regression-Safe Evolution

This feature is additive and must not modify generation behavior. It exercises existing gateway behavior and documents results.

### Article III: Gateway Is the Operational Source of Truth

The harness will use gateway endpoints rather than direct ComfyUI submission so the QA path reflects production behavior.

### Article V: Operator Clarity

The harness will prompt only for inputs that matter and will keep face-vs-scene concerns aligned with the selected workflow capabilities.

### Article VI: Validation Before Merge

The harness itself will be validated via syntax checks and by running at least one manual QA flow.

## Technical Approach

### 1. Add a new interactive CLI script

File:

- `scripts/qa_harness.py`

Responsibilities:

- fetch workflows from gateway
- allow operator selection
- upload scene reference URL when needed
- submit run
- poll status
- fetch final run detail
- download first output
- ask review questions
- write markdown report

### 2. Artifact storage

Store outputs under:

- `data/qa_runs/<timestamp>_<prompt_id>/`

Artifacts:

- downloaded result image
- `report.md`
- optional metadata JSON

### 3. Operator review model

Use human-in-the-loop prompts instead of pretending to do automatic visual judgment without a vision service.

### 4. Spec alignment

Add a dedicated feature package under:

- `specs/002-qa-harness-agent/`

## Files In Scope

- [qa_harness.py](/Users/akash/Documents/PetProjects/AI Influencer/scripts/qa_harness.py)
- [spec.md](/Users/akash/Documents/PetProjects/AI Influencer/specs/002-qa-harness-agent/spec.md)
- [plan.md](/Users/akash/Documents/PetProjects/AI Influencer/specs/002-qa-harness-agent/plan.md)
- [tasks.md](/Users/akash/Documents/PetProjects/AI Influencer/specs/002-qa-harness-agent/tasks.md)
- [quickstart.md](/Users/akash/Documents/PetProjects/AI Influencer/specs/002-qa-harness-agent/quickstart.md)

## Validation Strategy

1. Python compile check for the harness.
2. Manual QA flow against one scene-guided workflow.
3. Verify report output exists and includes structured fields.
