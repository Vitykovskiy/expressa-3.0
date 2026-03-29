# Glossary

## Business Terms

- Business task intake: structured clarification stage that turns a raw request into a fixed business problem statement, user scenarios, scope, and acceptance expectations.
- Initiative: a top-level outcome that anchors the issue-driven delivery chain.
- First version: the narrowest release scope that still produces meaningful business value.

## Technical Terms

- Canonical source of truth: the authoritative repository artifact where project state must be persisted.
- Contour: a development boundary with its own owner, such as `frontend`, `backend`, `devops`, or `qa-e2e`.
- Environment check: validation of local tooling, repository wiring, GitHub access, and baseline readiness.
- Guardrail: a configured category of change that still requires explicit human approval in otherwise autonomous workflows.
- Workflow state file: `.ai-dev-template.workflow-state.json`, the repository file that stores `current_stage`.

## Working Definitions

- Ready: sufficiently clarified to begin the current task without guessing core behavior or contracts.
- Done: delivered for the current task, persisted in canonical artifacts, and reflected in GitHub state with the required closure evidence.
- Initiative complete: contour development is finished, deployment succeeded, and e2e validation passed.
- Blocked: cannot continue because of an unresolved dependency, missing access, or missing specification that must be routed into the appropriate follow-up issue.
