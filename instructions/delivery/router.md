# Implementation Router

Task type: `implementation`

Primary executor: exactly one contour role per session.

Use this branch only when the currently selected issue has `task_type = implementation`.

This task belongs to exactly one parent `block_delivery` issue and carries one contour-owned delivery scope.

Choose one role file and read only that file next:

- `instructions/delivery/roles/frontend.md`
- `instructions/delivery/roles/backend.md`
- `instructions/delivery/roles/devops.md`
- `instructions/delivery/roles/qa-e2e.md`

Do not read multiple contour role files in one session unless the task is explicitly a workflow-maintenance task for the template itself.
Do not execute another contour's implementation work under an integration, cleanup, or incidental-change rationale. Cross-contour implementation must return to decomposition as separate linked tasks.
