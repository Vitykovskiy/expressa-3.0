# E2E Test Template

## Summary

- Task type: `e2e`
- Owner contour: `qa-e2e`
- Parent initiative: `<issue id or URL>`
- Parent block task: `<issue id or URL>`
- GitHub Issue: `<issue id or URL>`
- Current project status: `<Ready/In Progress/Blocked/Waiting for Testing/Testing/Waiting for Fix/Done>`
- Claim path: `<already In Progress / Waiting for Testing -> Testing / Ready -> In Progress>`

## Validation Scope

- Environment: `<environment>`
- Scenarios: `<scenario ids>`
- Acceptance source: `<artifact>`

## Canonical Inputs

- `docs/analysis/user-scenarios.md`
- `docs/analysis/version-scope-and-acceptance.md`
- `docs/runbooks/e2e-validation-runbook.md`
- `<deployment result or environment evidence>`

## Dependencies

- Depends on: `<issue links or none>`
- Dependency status: `<done / not blocking / blocked>`

## Definition Of Ready

- `<why the e2e task is allowed to start now>`
- `<which status transition made this task claimable>`
- `<what environment and evidence must already exist>`

## Test Cases

| Case | Scenario | Expected result |
| --- | --- | --- |
| `<case>` | `<scenario>` | `<result>` |

## Completion Criteria

- [ ] all critical scenarios pass
- [ ] acceptance criteria are satisfied
- [ ] blocking defects are recorded and routed correctly

## Definition Of Done

- `<test evidence, defect links, and completion conditions required to close the task>`

## Evidence And Handoff

- Validation report: `<path or link>`
- Screenshots or videos: `<path or link>`
- Defects created or updated: `<issue links or none>`
- Release recommendation: `<go / no-go / blocked>`
