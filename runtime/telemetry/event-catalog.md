# Event Catalog

This catalog keeps runtime traces consistent across agents and subagents.

## Core Events

| Event | Purpose |
| --- | --- |
| `session_started` | Marks a new agent session or subagent run. |
| `task_selected` | Records which task or issue the agent chose to work on. |
| `subagent_spawned` | Records creation of a subagent and its assigned scope. |
| `subagent_finished` | Records the completion status of a subagent. |
| `tool_called` | Records a discrete tool invocation before it runs. |
| `tool_finished` | Records the result of a tool invocation. |
| `attempt_started` | Records a discrete action the agent is trying. |
| `attempt_finished` | Records a successful attempt and its result. |
| `attempt_failed` | Records an attempt that did not complete. |
| `retry_scheduled` | Records that the agent plans another attempt. |
| `blocker_detected` | Records a blocking condition that must be resolved elsewhere. |
| `workaround_applied` | Records a fallback path chosen after a failure or limitation. |
| `decision_recorded` | Records a branch point or policy choice. |
| `handoff_written` | Records output that hands work to another role or session. |
| `session_finished` | Marks the end of the session or subagent run. |

## Suggested Reason Codes

Use stable reason codes so traces can be aggregated later.

| Reason code | Meaning |
| --- | --- |
| `missing_input` | Required context or artifact was unavailable. |
| `tool_failure` | A command, API call, or helper failed. |
| `network_failure` | Remote access or network request failed. |
| `auth_failure` | Authentication or token access failed. |
| `schema_mismatch` | A structured payload did not match expected shape. |
| `repo_state_conflict` | Repository state contradicted the planned operation. |
| `sandbox_limit` | Local execution was limited by the environment. |
| `workflow_inconsistency` | Workflow docs or state were contradictory. |
| `unsafe_assumption` | The agent rejected an assumption as too risky. |
| `temporary_workaround` | The agent chose a fallback path to keep moving. |
| `deferred_github_sync` | GitHub-side setup work was deferred while local bootstrap continued. |

`decision_recorded` should be used for high-impact workflow choices such as:

- deciding whether PR creation is allowed for the current repository;
- deciding whether autonomous routing may stop because no eligible path remains;
- deciding whether a missing direct frame link is a true implementation blocker or only a traceability gap that still allows `system_analysis` to continue from Figma Make context.
- deciding whether setup may continue in degraded local-first mode because GitHub bootstrap is temporarily unavailable.
