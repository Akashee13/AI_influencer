# Spec Kit Workspace

This repository uses a Spec-Driven Development layout compatible with GitHub Spec Kit conventions.

Core artifacts:

- `.specify/memory/constitution.md`: project-wide non-negotiable engineering rules
- `specs/<feature>/spec.md`: product and behavioral requirements
- `specs/<feature>/plan.md`: implementation approach and validation strategy
- `specs/<feature>/tasks.md`: execution checklist tied back to the plan
- `specs/<feature>/quickstart.md`: operator flow for manual validation

Working rule:

No substantial behavior change to the ComfyUI gateway, dashboard, CLI, or workflow bindings should be made without first updating or creating a matching spec package.
