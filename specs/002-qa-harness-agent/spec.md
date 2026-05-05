# Feature Specification: QA Harness Agent

Feature ID: 002-qa-harness-agent
Status: Draft
Created: 2026-05-05
Owner: Repository maintainers

## Summary

The repository needs an operator-facing QA agent skill, supported by a deterministic helper harness, that can run a workflow against a scene reference, wait for the result, and write a structured markdown gap report describing how the generated output differs from the expected outcome.

## Problem Statement

The current system can generate images, but testing quality is still ad hoc. There is no repeatable operator flow for:

- choosing a workflow intentionally
- attaching a scene reference link
- waiting for completion
- collecting outcome expectations
- documenting gaps in a reusable, fix-oriented report

## Goals

1. Provide a QA agent skill for manual operator testing.
2. Support that skill with a deterministic helper harness script.
3. Route all generation through the gateway so QA reflects real production behavior.
4. Download the produced output locally into the repository for inspection.
5. Produce a markdown report that captures:
   - test inputs
   - expected outcome
   - observed result metadata
   - structured pass/partial/fail judgments
   - concrete fix gaps

## Non-Goals

1. Fully automated computer-vision grading with no human-in-the-loop.
2. Browser-native QA workflow inside the dashboard.
3. Video QA evaluation.

## User Story

As an operator, I want a QA agent that asks me for a workflow and a scene-reference Instagram post link, submits the job, waits for completion, and writes a gap-analysis markdown file so we can iterate systematically instead of guessing what broke.

## Functional Requirements

### FR-0 Skill wrapper

The repository MUST include a reusable skill that tells the agent how to run QA passes and where reports belong.

### FR-1 Interactive intake

The QA harness MUST ask the operator for:

- gateway base URL
- gateway token, if not already configured
- workflow selection
- expected outcome summary
- scene-reference Instagram link or direct image URL when the chosen workflow supports scene guidance

### FR-2 Gateway-based execution

The harness MUST:

- upload the scene reference through the gateway when provided
- submit the selected workflow through the gateway
- poll `/status/<prompt_id>` until completion using exponential backoff

### FR-3 Result capture

After completion, the harness MUST:

- fetch run detail or history
- download the first output if available
- store artifacts under a deterministic QA run directory in the repo

### FR-4 Operator-in-the-loop comparison

The harness MUST ask the operator to evaluate:

- face consistency
- scene/style similarity
- wardrobe adaptation quality
- overall pass/fail status
- top observed gaps

### FR-5 Report generation

The harness MUST write a markdown report containing:

- run metadata
- selected workflow
- source reference URL
- expected outcome
- local artifact paths
- structured findings
- recommended fixes

## Success Metrics

1. A non-technical operator can run a full QA pass through the QA skill workflow.
2. Each run creates a reusable markdown report in the repository.
3. Reports make fix gaps concrete enough to turn into follow-up tasks.

## Risks

1. The harness depends on gateway availability and token correctness.
2. Result quality judgment remains operator-assisted rather than fully automatic.
3. Downloaded artifacts may accumulate over time and require cleanup policy later.
