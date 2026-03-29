# Runbooks

This directory stores the repository-native operational instructions used by `deploy` and `e2e` tasks.

Required runbooks:

- `deployment-runbook.md` for rollout steps, rollback, health checks, and monitoring evidence.
- `e2e-validation-runbook.md` for test environment readiness, evidence collection, and defect routing.

Rules:

- keep these documents current as environments, rollout paths, or validation mechanics change;
- treat them as canonical inputs for deployment and integrated validation tasks;
- update them in the repository together with the operational changes they describe.
