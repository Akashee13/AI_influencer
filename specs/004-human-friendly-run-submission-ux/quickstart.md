# Quickstart: Human-Friendly Run Submission UX

## Source Trigger

- Operator feedback on 2026-05-05: the submit-run UX is too context-heavy and is hard to use without repo knowledge.

## Goal

Use this document to inspect the original operator pain and verify the guided submit-run redesign.

## Reproduction

1. Open [dashboard.html](/Users/akash/Documents/PetProjects/AI Influencer/web/dashboard.html).
2. Inspect the submit surface before patching.
3. Confirm that workflow capability understanding depends on small helper text and prior system knowledge.
4. Confirm that advanced controls are mixed with required inputs in the same primary panel.

## Validation

1. Apply the guided submit-run redesign in [dashboard.html](/Users/akash/Documents/PetProjects/AI Influencer/web/dashboard.html).
2. Load the page and choose a workflow.
3. Confirm the UI clearly states what is locked, what is required, and whether the run is ready.
4. Confirm advanced controls are available but not in the operator’s main path.
5. Submit a valid run and confirm the request still succeeds through the existing gateway path.
