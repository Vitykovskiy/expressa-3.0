# Contour Task Matrix

Use this file to decompose approved analysis into contour-specific execution tasks.

## Rules

- one row per task
- one task owns one contour
- one `block_delivery` row represents one integrated deliverable and acts as the parent for child implementation rows
- cross-contour work is split into linked tasks
- dependencies must reference the upstream task names or issue IDs explicitly
- deploy and e2e work are separate rows, not hidden inside implementation rows
- child implementation rows must reference their parent block task explicitly
- rows may depend on a specific bounded `system_analysis` slice and should name that slice explicitly when it is not the only analysis issue for the initiative
- when implementation is blocked by missing specification, record a linked `system_analysis` follow-up row or issue with explicit clarification scope

## Matrix

| Task | Task type | Owner contour | Parent block task | Depends on | Input artifacts | Expected result |
| --- | --- | --- | --- | --- | --- | --- |
| `<task>` | `business_analysis` | `business-analyst` | `n/a` | `<dependencies>` | `<business context>` | `<result>` |
| `<task>` | `system_analysis` | `system-analyst` | `n/a` | `<dependencies>` | `<intake artifacts>` | `<result>` |
| `<task>` | `block_delivery` | `<system-analyst/or configured owner>` | `n/a` | `<dependencies>` | `<canonical analysis package>` | `<integrated deliverable ready for validation>` |
| `<task>` | `implementation` | `<frontend/backend/devops/qa-e2e>` | `<block_delivery task>` | `<dependencies>` | `<analysis artifacts>` | `<result>` |
| `<task>` | `deploy` | `devops` | `<block task or n/a>` | `<dependencies>` | `<rollout artifacts>` | `<result>` |
| `<task>` | `e2e` | `qa-e2e` | `<block task>` | `<dependencies>` | `<scenario and acceptance artifacts>` | `<integrated validation result>` |
