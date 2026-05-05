---
name: fix-gap-speckit-agent
description: Use when the user wants to turn a QA gap report into follow-up spec and implementation work by reading docs/gap-finding report.md, checking whether the reported gap is already covered by existing specs, creating or extending the right Spec Kit package under specs/, and then executing the relevant tasks with validation.
---

# Fix Gap SpecKit Agent

This skill converts QA findings into spec-first follow-up work and then carries the fix through implementation.

Use it when the user wants to:

- inspect a QA `report.md`
- decide whether the reported issue is a genuinely new gap
- avoid duplicating an existing spec
- start a new Spec Kit workflow for the gap
- implement the follow-up tasks from the matching spec package
- re-run validation and update the spec artifacts with results

## Inputs To Gather

Ask for or confirm only when needed:

1. report path
2. whether to use the latest QA report by default
3. preferred feature slug, if the user already has one

If the user does not specify a report path, default to the latest folder under `docs/gap-finding/`.

## Execution Path

Preferred execution path:

1. Read `.specify/memory/constitution.md`.
2. Run `python3 skills/fix-gap-speckit-agent/scripts/report_gap_scan.py`.
3. Inspect the chosen `report.md` and the scan output.
4. Treat a gap as "new" only when it is not already covered by the current spec set in `specs/`.
5. If the gap is already covered, point to the matching spec package and extend that package instead of creating a duplicate.
6. If the gap is new, run `python3 skills/fix-gap-speckit-agent/scripts/init_gap_spec.py --gap-summary ...`.
7. Fill in the generated `spec.md`, `plan.md`, `tasks.md`, and `quickstart.md` using the repo's existing Spec Kit style.
8. Read the matching `tasks.md` and execute the relevant tasks unless the user explicitly asked for spec work only.
9. Validate the implementation using the validation steps from the matching spec package.
10. Update `tasks.md` checkboxes and any affected spec artifacts to reflect what was actually completed, what remains open, and what evidence was gathered.

## New-Gap Heuristic

The helper script gives a first-pass answer. The skill must still use judgment.

Treat the gap as new when:

- the report describes a runtime or workflow failure not mentioned in existing specs
- the closest existing spec does not already require the missing behavior
- the fix would need new observable requirements, not just a task update

Treat the gap as existing when:

- the current specs already call for the behavior and only implementation is missing
- the report is evidence for a validation task inside an existing spec

## SpecKit Workflow

When a new gap exists:

1. Create the next numbered feature package under `specs/`.
2. Write `spec.md` first with observable behavior and risk framing.
3. Write `plan.md` with a constitution check and validation strategy.
4. Write `tasks.md` with file-oriented work and explicit validation steps.
5. Write `quickstart.md` with the manual repro or validation flow.

Do not implement the code fix before the spec package exists.

When the gap already maps to an existing package:

1. Treat that package as the source of truth.
2. Read `tasks.md`, `plan.md`, and `quickstart.md`.
3. Execute the open tasks that are directly supported by the current report and repo state.
4. Keep the implementation aligned with the existing spec instead of branching into a second package.

## Implementation Workflow

After the spec package is identified:

1. Start with the investigation tasks that confirm root cause and owning surface.
2. Implement the smallest fix that satisfies the existing spec requirements.
3. Preserve previously working behavior called out in the constitution and plan.
4. Run the validation steps from the package, including the same QA path that produced the report.
5. Update task checkboxes only for work actually completed.
6. If validation fails, record that in the spec artifacts and leave the remaining tasks open.

Do not stop after writing spec artifacts unless the user explicitly asks for spec-only output.

## Task Update Rules

When this skill executes implementation work:

- mark completed tasks in `tasks.md`
- add narrowly scoped new tasks if the report exposed missing work not already represented
- keep failed or unverified work unchecked
- reflect major new evidence in `spec.md`, `plan.md`, or `quickstart.md` when it changes the understanding of the gap

## Validation Expectations

Prefer the validation path already captured in the matching spec package.

For QA-driven runtime gaps, validation usually means:

- rerunning the same workflow and reference path
- confirming the original failure is gone
- confirming output artifacts are present when expected
- checking one older path for non-regression when the package requires it

## Output Requirements

The skill should leave one of these outcomes:

- no new spec, plus a note explaining which existing spec should absorb the gap
- a new Spec Kit package under `specs/<feature>/`
- a completed or partially completed implementation pass tied to the matching spec package

When creating a new package, include:

- the source report path
- the QA gap summary
- the regression risk
- the owning surface such as gateway, workflow JSON, UI, or CLI
- the manual validation path needed to prove the gap is fixed

When implementation is attempted, also leave:

- updated task status in `tasks.md`
- any code, workflow, or config changes needed for the fix
- validation evidence or a short note explaining what still blocks completion
