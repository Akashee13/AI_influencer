#!/usr/bin/env python3
"""Create a new Spec Kit package for a newly discovered QA gap."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SPECS_DIR = ROOT / "specs"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48] or "gap-follow-up"


def next_feature_id() -> int:
    existing = []
    for path in SPECS_DIR.iterdir():
        if not path.is_dir():
            continue
        prefix = path.name.split("-", 1)[0]
        if prefix.isdigit():
            existing.append(int(prefix))
    return (max(existing) + 1) if existing else 1


def write(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new spec package from a QA gap.")
    parser.add_argument("--gap-summary", required=True, help="Short summary of the new gap.")
    parser.add_argument("--title", help="Feature title. Defaults to the gap summary.")
    parser.add_argument("--slug", help="Feature slug. Defaults to a slugified title.")
    parser.add_argument("--report", help="Source report path for traceability.")
    args = parser.parse_args()

    title = args.title or args.gap_summary
    slug = args.slug or slugify(title)
    feature_id = next_feature_id()
    feature_name = f"{feature_id:03d}-{slug}"
    feature_dir = SPECS_DIR / feature_name
    feature_dir.mkdir(parents=True, exist_ok=False)

    report_line = args.report or "Report path not recorded."
    today = date.today().isoformat()

    spec_md = f"""# Feature Specification: {title}

Feature ID: {feature_id:03d}-{slug}
Status: Draft
Created: {today}
Owner: Repository maintainers

## Summary

{args.gap_summary}

Source QA report:

- `{report_line}`

## Problem Statement

Describe the observed gap, the operator-visible failure, and why existing behavior is insufficient.

## Goals

1. Define the missing behavior in observable terms.
2. Prevent regression of previously accepted behavior.
3. Tie the fix to the owning runtime surface.

## Non-Goals

1. List adjacent work that should stay out of scope.

## User Story

As an operator, I want the reported gap resolved in a way that is validated through the repo's real workflow surfaces.

## Functional Requirements

### FR-1 Gap closure

Define the required user-visible behavior that closes this QA gap.

### FR-2 Surface ownership

State whether the source of truth is the gateway, workflow JSON, UI, CLI, or config binding.

### FR-3 Validation

Define what manual or runtime evidence proves the gap is fixed.

## Success Metrics

1. The QA gap is no longer reproducible on the intended path.
2. Existing expected behavior still works.

## Risks

1. Capture the most likely regressions or runtime mismatches.
"""

    plan_md = f"""# Implementation Plan: {title}

Feature: [{{feature_name}}](./spec.md)
Created: {today}
Status: Draft

## Goal

Translate the QA gap into a safe, validated implementation plan.

## Constitution Check

### Article I: Regression-Safe Evolution

List the previously working behavior that could regress.

### Article II: Workflow Contract First

State the contract surface affected by this gap.

### Article III: Gateway Is the Operational Source of Truth

Explain whether the gateway must change or stay aligned with another surface.

### Article VI: Validation Before Merge

Describe the validation path required before implementation is considered done.

## Technical Approach

### 1. Root cause framing

Summarize the failure mode from the QA report.

### 2. Intended fix shape

Describe the likely implementation approach without writing code yet.

### 3. Validation strategy

List the manual and automated checks to run.

## Files In Scope

- [spec.md]({feature_dir / "spec.md"})
- [plan.md]({feature_dir / "plan.md"})
- [tasks.md]({feature_dir / "tasks.md"})
- [quickstart.md]({feature_dir / "quickstart.md"})

## Validation Strategy

1. Reproduce the QA gap.
2. Implement the fix after spec approval.
3. Re-run the relevant QA or operator flow.
"""
    plan_md = plan_md.replace("{feature_name}", feature_name)

    tasks_md = f"""# Tasks: {title}

Feature: [{{feature_name}}](./spec.md)

## Phase 1: Spec Refinement

- [ ] Tighten the problem statement from the QA report evidence.
- [ ] Confirm the owning surface and regression risk.
- [ ] Finalize the validation path.

## Phase 2: Implementation

- [ ] Make the minimal code or workflow changes needed to close the gap.
- [ ] Keep gateway, workflow, UI, and CLI behavior aligned as required by the spec.

## Phase 3: Validation

- [ ] Reproduce the original gap before the fix.
- [ ] Re-run the relevant QA or operator flow after the fix.
- [ ] Confirm no regression on the previously accepted path.
"""
    tasks_md = tasks_md.replace("{feature_name}", feature_name)

    quickstart_md = f"""# Quickstart: {title}

## Source Report

- `{report_line}`

## Goal

Use this document to reproduce the QA gap and verify the fix once implementation begins.

## Reproduction

1. Open the source QA report.
2. Follow the same operator path that exposed the gap.
3. Capture the failing behavior before applying a fix.

## Validation

1. Apply the implementation tied to this spec package.
2. Re-run the same QA path.
3. Confirm the reported gap is gone and adjacent behavior still works.
"""

    write(feature_dir / "spec.md", spec_md)
    write(feature_dir / "plan.md", plan_md)
    write(feature_dir / "tasks.md", tasks_md)
    write(feature_dir / "quickstart.md", quickstart_md)

    print(feature_dir.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
