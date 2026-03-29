# Runtime Telemetry

Use this folder for the tracked telemetry spec and helper files. Actual runtime traces should be written to `.agent-work/telemetry/`, which is already gitignored.

## Layout

- `event-schema.json` - JSON Schema for one JSONL event.
- `event-catalog.md` - short taxonomy of supported event types and reason codes.
- `session-template.json` - starter metadata for a new trace session.
- `new-session.ps1` - helper that creates a new session file in `.agent-work/telemetry/`.

## Event Format

Each line in a log file is one JSON object.

Required fields:

- `timestamp_utc`
- `trace_id`
- `event_type`
- `agent_role`
- `session_mode`

Recommended fields:

- `session_id`
- `span_id`
- `parent_span_id`
- `task_type`
- `issue_id`
- `operation`
- `attempt`
- `status`
- `reason_code`
- `message`
- `inputs`
- `outputs`
- `duration_ms`

## Event Taxonomy

This telemetry is optimized for the failure patterns that matter during workflow analysis:

- `attempt_started`
- `attempt_finished`
- `attempt_failed`
- `task_selected`
- `subagent_spawned`
- `subagent_finished`
- `tool_called`
- `tool_finished`
- `retry_scheduled`
- `blocker_detected`
- `workaround_applied`
- `decision_recorded`
- `handoff_written`
- `session_started`
- `session_finished`

Recommended reason codes:

- `missing_input`
- `tool_failure`
- `network_failure`
- `auth_failure`
- `schema_mismatch`
- `repo_state_conflict`
- `sandbox_limit`
- `workflow_inconsistency`
- `unsafe_assumption`
- `temporary_workaround`

## Usage

1. Run `new-session.ps1` to create a new JSONL trace file under `.agent-work/telemetry/`.
2. Append one event per line as the agent progresses.
3. Keep secrets and large payloads out of the log body.
4. Use `trace_id`, `span_id`, and `parent_span_id` to connect orchestrator and subagent activity.
5. Use the log to reconstruct what the agent tried, what failed, and which workaround it chose.
