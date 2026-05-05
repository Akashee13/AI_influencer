---
name: fix-gap-speckit-agent
description: Use when the user wants to turn a QA gap report into follow-up spec work by reading docs/gap-finding report.md, checking whether the reported gap is already covered by existing specs, and if a new gap exists starting a new Spec Kit spec package under specs/.
---

# Fix Gap SpecKit Agent

This skill converts QA findings into spec-first follow-up work.

Use it when the user wants to:

- inspect a QA `report.md`
- decide whether the reported issue is a genuinely new gap
- avoid duplicating an existing spec
- start a new Spec Kit workflow for the gap

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

## Output Requirements

The skill should leave one of these outcomes:

- no new spec, plus a note explaining which existing spec should absorb the gap
- a new Spec Kit package under `specs/<feature>/`

When creating a new package, include:

- the source report path
- the QA gap summary
- the regression risk
- the owning surface such as gateway, workflow JSON, UI, or CLI
- the manual validation path needed to prove the gap is fixed
