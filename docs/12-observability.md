# Observability And Local Telemetry

## Purpose

This document defines the local runtime trace format used to analyze agent execution friction, failed attempts, retries, blockers, and workarounds.

The goal is to make workflow failures diagnosable without committing noisy runtime artifacts to the repository.

## Storage Location

- write telemetry to `.agent-work/telemetry/`;
- keep the directory gitignored and treat it as local runtime evidence;
- use one file per session or trace tree, appended as needed;
- do not commit trace files unless a task explicitly requires that output.
- keep the tracked helper files and schema under `runtime/telemetry/`.

## Format

Use UTF-8 JSONL.

Each line is one event object with a small, stable schema.

Required fields:

- `timestamp_utc`
- `trace_id`
- `event_type`
- `agent_role`
- `session_mode`

Recommended fields:

- `session_id`
- `parent_span_id`
- `span_id`
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
- `metadata`

For `decision_recorded` events that govern delivery actions, prefer metadata such as:

- `delivery_policy.pull_requests_enabled`
- `delivery_policy.creation_mode`
- `delivery_policy.action_requested`
- `delivery_policy.action_allowed`
- `delivery_policy.config_source`
- `backlog_recheck_performed`
- `remaining_eligible_issue_ids`
- `setup.bootstrap_mode`
- `setup.deferred_github_reconciliation`
- `setup.local_bootstrap_complete`

## Event Taxonomy

Emit events for:

- `session_started`
- `task_selected`
- `subagent_spawned`
- `subagent_finished`
- `tool_called`
- `tool_finished`
- `attempt_started`
- `attempt_finished`
- `attempt_failed`
- `decision_recorded`
- `retry_scheduled`
- `blocker_detected`
- `workaround_applied`
- `handoff_written`
- `session_finished`

## Logging Rules

- log what the agent attempted, what failed, what changed, and what was retried;
- record a short structured decision summary instead of free-form hidden reasoning;
- capture blocker details and workaround rationale before continuing;
- correlate child activity to parent activity with `trace_id` plus `parent_span_id` when subagents or nested tools are involved;
- redact secrets, tokens, credentials, and other sensitive payloads from telemetry;
- keep the trace append-only so later analysis can reconstruct the sequence of events;
- prefer concise reason codes such as `missing_input`, `tool_failure`, `network_failure`, `auth_failure`, `schema_mismatch`, `repo_state_conflict`, `sandbox_limit`, `workflow_inconsistency`, `unsafe_assumption`, or `temporary_workaround`.
- when autonomous routing ends, record why the orchestrator concluded that no eligible path remained and whether a final Issue/Project re-read was performed.
- when PR or merge policy is evaluated, record the config source, the requested action, and whether the action was allowed or denied.
- when setup continues in local-first fallback mode, emit a `decision_recorded` event before the fallback action with the blocking condition, the local bootstrap step that continues, and whether GitHub reconciliation is deferred.
- when setup defers GitHub bootstrap, emit a `workaround_applied` or `handoff_written` event that names the deferred reconciliation so later sessions can resume it without guessing.

The canonical event schema and starter assets live under `runtime/telemetry/`.

## Analysis Use

Use the trace to answer questions such as:

- where the agent got stuck;
- which tool or command failed;
- whether the agent retried the right thing;
- which workaround was chosen and why;
- whether the failure was caused by missing inputs, environment limits, or workflow ambiguity.
