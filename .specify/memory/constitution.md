# AI Influencer Constitution

Version: 1.1.0
Ratified: 2026-05-05
Last Amended: 2026-05-05

## Purpose

This constitution governs all product and engineering changes in the AI Influencer repository. It exists to prevent regressions while the system evolves from ad hoc prompt tooling into a repeatable workflow platform for anchor-consistent image generation.

## Article I: Regression-Safe Evolution

1. New capabilities MUST preserve previously accepted behavior unless a spec explicitly deprecates that behavior.
2. Any change to workflow selection, prompt assembly, face binding, scene reference handling, generation submission, polling, deletion, or download behavior MUST document backward-compatibility impact before implementation.
3. When a new requirement conflicts with existing behavior, the conflict MUST be resolved in spec artifacts first, not implicitly in code.

Rationale:
This project has repeatedly regressed older workflow requirements while adding new features. Preventing silent breakage is the highest-order engineering requirement.

## Article II: Workflow Contract First

1. Every workflow exposed in the UI or gateway MUST have a documented contract for:
   - identity source
   - scene/reference source
   - editable inputs
   - locked inputs
   - deterministic vs randomized seed behavior
2. Workflow-to-anchor bindings MUST live in repository configuration, not in user-entered UI state.
3. Face identity and scene inspiration MUST be modeled as separate concerns whenever the product promises fixed identity with editable scene/style reference.

Rationale:
The system serves multiple workflow modes. Hidden coupling between workflow JSON, UI fields, and gateway overrides causes drift and confusing behavior.

## Article III: Gateway Is the Operational Source of Truth

1. The gateway MUST remain the authoritative runtime adapter between repository intent and ComfyUI execution.
2. The dashboard UI and CLI helper MUST not implement incompatible submit logic.
3. If the gateway performs critical preparation steps, those steps MUST either be shared or replicated explicitly in the CLI path.

Rationale:
The gateway is where workflow config, auth, override normalization, input asset preparation, status tracking, and download behavior converge.

## Article IV: Deterministic Identity Behavior

1. If a workflow declares a locked anchor identity, the user MUST not be able to override that identity through the UI or request payload.
2. If the submitted seed equals the workflow default seed, the implementation MUST aim for deterministic output behavior within the limits of the installed ComfyUI/model stack.
3. If the seed is blanked intentionally, the system MUST randomize seed generation explicitly rather than accidentally reusing prior workflow defaults.

Rationale:
Identity consistency is the central product promise. Seed handling and locked-face handling are not cosmetic details; they define core correctness.

## Article V: Operator Clarity

1. The UI MUST reflect actual system behavior:
   - locked inputs must look locked
   - editable inputs must be operable
   - loading, success, and error states must be visible
2. Any workflow that uses repository-bound assets MUST surface those bindings clearly to the operator.
3. If the UI cannot represent a workflow contract honestly, the workflow MUST not be exposed until the UI is updated.

Rationale:
False affordances cause user error and wasted generation runs.

## Article VI: Validation Before Merge

1. Every feature spec MUST include manual validation steps for:
   - gateway path
   - UI path when applicable
   - CLI path when applicable
2. Workflow-affecting changes MUST verify both success paths and non-regression paths.
3. Documentation-only changes are exempt from runtime validation but MUST stay consistent with real repository behavior.

Rationale:
This project spans Python, HTML/JS, workflow JSON, and remote ComfyUI runtime behavior. Validation must reflect that multi-surface reality.

## Article VII: Living Spec Discipline

1. Any repository change beyond trivial housekeeping MUST follow the Spec Kit workflow by creating or updating the matching package under `specs/` before implementation proceeds.
2. Significant changes MUST begin with or update:
   - `spec.md`
   - `plan.md`
   - `tasks.md`
3. Specs MUST describe observable behavior, not just implementation ideas.
4. Plans MUST identify which existing behavior is at risk.
5. Tasks MUST be traceable to concrete files and validation steps.
6. Implementing code, workflow, UI, or runtime-affecting docs without the matching Spec Kit package is non-compliant unless the change is purely trivial housekeeping.

Rationale:
The repository is transitioning from exploratory hacking to controlled product iteration. Specification must become the default workflow for changes rather than an optional afterthought.

## Non-Negotiable Gates

Before implementation begins on a feature, the plan MUST answer:

1. What previously working behavior could regress?
2. Which surface owns the truth: workflow JSON, binding config, gateway, UI, or CLI?
3. How is identity preserved?
4. How is scene/style reference preserved?
5. What proves the old path still works after the new path ships?
6. Which Spec Kit package owns this change?

## Amendment Policy

This constitution may be amended only when:

1. The change is written explicitly.
2. The reason for amendment is stated.
3. Any affected specs or plans are updated in the same change set.

Amendment reason for Version 1.1.0:

- Make Spec Kit workflow mandatory for repository changes so future work consistently starts from `spec.md`, `plan.md`, and `tasks.md` instead of bypassing governance.
