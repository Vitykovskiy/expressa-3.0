# Workflow

## Operating Model

The repository uses a two-mode workflow tracked by `.ai-dev-template.workflow-state.json`.

Allowed `current_stage` values:

1. `setup`
2. `issue_driven`

`setup` is the only repository-wide stage. After setup completes, the repository switches to `issue_driven` and all routing is performed through GitHub Issues, dependencies, owner contours, block-level delivery tasks, and GitHub Project state. If GitHub-side bootstrap is temporarily unavailable, setup may continue in a local-first fallback mode, record deferred reconciliation, and still complete the local bootstrap path instead of stalling.

`issue_driven` must not start from an empty backlog when GitHub access is available. Setup seeds the first `initiative` plus the first `business_analysis` issue before the repository leaves `setup`; if GitHub access is temporarily unavailable, the intended backlog is recorded as deferred reconciliation instead of blocking setup completion.

## Bootstrap State Rule

`.ai-dev-template.workflow-state.json` is the bootstrap guardrail that records the repository mode and the setup-to-operations transition.

Rules:

- read the file at the start of every session;
- use `current_stage` exactly as written;
- switch from `setup` to `issue_driven` when setup exit conditions are complete, including local-first fallback completion when GitHub-side bootstrap is temporarily unavailable;
- `current_stage` accepts exactly two repository-wide values: `setup` and `issue_driven`;
- in `issue_driven`, route work from GitHub task metadata, dependencies, owner contours, and GitHub Project state.

## Execution Mode Policy

`.ai-dev-template.config.json` may define `workflow.execution_mode` to control execution pacing inside `issue_driven`.

Allowed values:

1. `manual`
2. `autonomous`

Execution-mode rules:

- `manual`: execution starts from an explicit execution session and may stop after one bounded routing wave;
- `autonomous`: once execution is active, the orchestrator keeps routing work until no eligible `Ready` or `In Progress` issues remain or a hard workflow stop is reached;
- execution mode does not replace `.ai-dev-template.workflow-state.json`; the workflow-state file still controls whether the current session is in `dialogue` or `execution`;
- execution mode does not permit bypassing blockers, missing dependencies, review gates, or owner-contour rules.

## Git Delivery Rule

Before starting task work, sync Git state and confirm the current working branch is based on the latest remote state of its parent branch.

After creating a commit, sync again and confirm the branch still grows from the latest working branch state before further changes, handoff, or PR creation.

Every completed task handoff must have repository-persisted evidence and verified operational side effects:

- commit all repository changes required for the completed task output;
- push the commit before considering the task handoff complete;
- before any PR creation, merge, or other delivery action governed by `.ai-dev-template.config.json`, read the repository's committed config, decide the effective delivery policy for this repository, and record that decision in telemetry;
- if the effective config cannot be read, is ambiguous, or contradicts the intended delivery action, fail closed and stop that delivery action until the policy is clarified;
- if `pull_requests.enabled = true`, follow the configured PR policy after pushing;
- if `pull_requests.enabled = false`, push directly to the assigned working branch;
- verify the push and any required GitHub side effects before reporting completion;
- keep completed task outputs in the repository worktree as committed, pushed evidence;
- pair GitHub-side changes with corresponding canonical repository document updates, commits, and pushes.

If the branch is behind, diverged, or based on an outdated parent, reconcile branch history first and only then continue the workflow task.

The repository's committed `.ai-dev-template.config.json` is the effective workflow policy for that repository. Template updates do not retroactively change repositories that were already created from an older template state.

GitHub transport messages shown after `git push`, including links to create a PR, are informational only. They do not override repository policy.

## Text Encoding Rule

Workflow text exchanged through repository files or external delivery tools must use explicit UTF-8 encoding.

Rules:

- use UTF-8 for markdown, templates, issue bodies, PR bodies, commit-message files, and other workflow text artifacts;
- on Windows or in PowerShell, use explicit UTF-8 encoding when a file may contain non-ASCII text;
- when writing temporary files for `gh`, `git`, or related tools, encode them explicitly as UTF-8, preferably without BOM;
- if a GitHub-side artifact or repository text shows mojibake or replacement characters, rewrite the source file in explicit UTF-8 and repeat the operation with corrected text.

## Observability And Local Telemetry

Execution sessions and spawned subagents must write local telemetry for workflow analysis to `.agent-work/telemetry/`.

Rules:

- use append-only UTF-8 JSONL for runtime traces;
- keep the telemetry folder outside version control and treat it as disposable runtime evidence;
- include correlation fields such as `trace_id`, `span_id`, `parent_span_id`, `agent_role`, `task_type`, and `issue_id` when available;
- record observed events for `session_started`, `task_selected`, `subagent_spawned`, `subagent_finished`, `tool_called`, `tool_finished`, `attempt_started`, `attempt_finished`, `attempt_failed`, `decision_recorded`, `retry_scheduled`, `blocker_detected`, `workaround_applied`, `handoff_written`, and `session_finished`;
- log what was attempted, what failed, what was retried, and why the agent changed course;
- record a short structured decision summary instead of attempting to preserve hidden internal reasoning;
- redact secrets, tokens, and other sensitive payloads from telemetry;
- if a blocker or workaround occurs, log it before continuing so later analysis can reconstruct the path that failed or diverged;
- when delivery policy matters, emit a `decision_recorded` event before the governed action with the effective config inputs and the allowed or denied action;
- if a spawned worker has no observable completion signal, log that visibility gap, attempt one explicit fallback path, and record the eligible issues that still remain after the failed attempt.

See `docs/12-observability.md` for the schema and operational conventions.

## Task Types

All post-setup work must be represented by GitHub Issues with one of these task types:

| Task type | Primary owner contour | Purpose |
| --- | --- | --- |
| `initiative` | `business-analyst` or `system-analyst` | top-level business outcome and decomposition anchor |
| `business_analysis` | `business-analyst` | clarify problem, users, scope, constraints, success expectations, and workflow vocabulary |
| `system_analysis` | `system-analyst` | produce the canonical specification package for one bounded analysis slice, plus the related block-level decomposition and child implementation plan |
| `block_delivery` | `system-analyst` or delivery owner defined by repository policy | parent issue for one integrated deliverable that waits for all required child implementation tasks and later block-level validation |
| `implementation` | one of `frontend`, `backend`, `devops`, `qa-e2e` | execute one contour-owned child task within a block-level deliverable |
| `deploy` | `devops` | roll validated build outputs into the target environment |
| `e2e` | `qa-e2e` | validate the integrated system against scenarios and acceptance criteria |

## Mandatory Task Attributes

Each operational issue must carry these attributes through issue fields, labels, or body sections:

- `task_type`
- `owner_contour`
- `parent_initiative`
- `parent_block_task` for child implementation issues
- `depends_on`
- `definition_of_ready`
- `definition_of_done`
- `canonical_inputs`
- `project_status`

Attribute rules:

- `owner_contour` must contain exactly one contour;
- `depends_on` must list all blocking tasks explicitly or say `none`;
- `definition_of_ready` must state the preconditions for starting;
- `definition_of_done` must state the evidence needed for closure;
- `canonical_inputs` must point to repository artifacts or prerequisite tasks;
- `project_status` must match the GitHub Project item state.

Hierarchy rules:

- only one `business_analysis` issue should initiate a new delivery stream after setup;
- `business_analysis` hands off to one or more bounded `system_analysis` issues for the same initiative or version stream;
- each `system_analysis` issue must declare a bounded scope before creating downstream work;
- `system_analysis` creates one or more `block_delivery` parent issues only for the slice it fully specifies;
- each `block_delivery` issue owns all required child implementation issues for that integrated outcome;
- `qa-e2e` validates the `block_delivery` issue after all required child implementation issues are done;
- if implementation is blocked by missing specification, create a linked follow-up `system_analysis` issue that defines the missing requirements explicitly.

## System Analysis Decomposition

`system_analysis` is canonical by scope, not by issue size.

Approved decomposition patterns:

- version slice: one issue covers one release increment, milestone, or rollout slice;
- capability slice: one issue covers one bounded business or technical capability;
- follow-up clarification slice: one issue closes a specific specification gap discovered after downstream work starts.

Decomposition rules:

- each `system_analysis` issue must state its bounded scope in the issue body and canonical docs;
- a bounded scope must be small enough to review without requiring the full initiative context in one session;
- downstream `block_delivery`, `implementation`, `deploy`, and `e2e` tasks may be created only for the slice whose specifications are implementation-ready;
- unresolved work outside that slice must remain in another planned or follow-up `system_analysis` issue, not hidden inside the current one;
- multiple `system_analysis` issues may exist for the same initiative when their boundaries and dependencies are explicit;
- no `block_delivery` issue may depend on unspecified behavior that belongs to another undeclared analysis slice.

## GitHub Project Model

GitHub Project is the canonical execution-status board for post-setup work.

Minimum required fields:

- `Status`
- `Task Type`
- `Owner Contour`
- `Priority`

Minimum required statuses:

- `Inbox`
- `Ready`
- `In Progress`
- `Blocked`
- `Waiting for Testing`
- `Testing`
- `Waiting for Fix`
- `In Review`
- `Done`

Status semantics:

- `Inbox`: created but not yet decomposed or triaged.
- `Ready`: owner contour may claim the task because dependencies are closed and inputs are sufficient.
- `In Progress`: the owning contour has claimed the task and is actively executing it.
- `Blocked`: work pauses while a dependency, access issue, or missing specification is being resolved.
- `Waiting for Testing`: a block-level delivery task has all required child implementation tasks done and is ready for integrated validation.
- `Testing`: `qa-e2e` is actively validating the integrated block-level result.
- `Waiting for Fix`: integrated validation found defects and the block-level task is waiting for child implementation follow-up.
- `In Review`: implementation is complete and the configured review or verification step is pending.
- `Done`: all done conditions are satisfied and the issue may be closed.

Status classes:

- Universal claimable: only `Ready` may be claimed as a new task from backlog.
- Active execution: `In Progress` means the task is already claimed and currently being worked.
- Handoff/control states: `Inbox`, `Blocked`, `Waiting for Testing`, `Testing`, `Waiting for Fix`, and `In Review` are not universal claimable statuses.
- A handoff/control state may still require the next role-specific workflow step when a task-type-specific rule explicitly says so.

## Active Execution Signal

The canonical signal for active task execution is GitHub Project status `In Progress`.

Rules:

- any open issue with the required workflow metadata, closed dependencies, and status `In Progress` is active execution work;
- multiple open issues may be active at the same time when their ownership and dependencies are explicit;
- `Ready` is the only universal claimable status for starting a new task from backlog;
- an agent may continue an issue already in `In Progress`;
- an agent may start a `Ready` issue only by first moving it to `In Progress`, then re-reading the issue and project state before continuing;
- if the post-claim re-read shows the issue is no longer safe to start, the agent must stop and treat it as unavailable instead of proceeding optimistically;
- non-terminal statuses other than `Ready` and `In Progress` do not become claimable by default; use them only through explicit task-type-specific continuation rules;
- a blocked issue stops only that issue path; it does not justify a global stop while another eligible `Ready` or `In Progress` issue still exists.

Task-type-specific continuation:

- `block_delivery` in `Waiting for Testing` is a handoff state for `qa-e2e`, not a general backlog pickup state;
- when `qa-e2e` starts integrated validation from `Waiting for Testing`, move the task to `Testing` before continuing;
- `Waiting for Fix` does not open the parent `block_delivery` task for general pickup; instead, create or reopen follow-up implementation issues and claim those through the normal `Ready` -> `In Progress` rule.

Eligibility and tie-breaking:

1. consider only open issues that have the required workflow metadata and whose declared dependencies are done;
2. treat eligible issues with GitHub Project status `In Progress` as already active work;
3. if a new task must be started, consider eligible issues with status `Ready`;
4. within the chosen status bucket, rank by `priority: high`, then `priority: medium`, then `priority: low`, then no priority label;
5. if multiple eligible issues still remain, choose the lowest issue number.

## Routing Algorithm

Every session must follow this sequence:

1. Start with `AGENTS.md`.
2. Read `.ai-dev-template.workflow-state.json`.
3. If `current_stage = "setup"`, execute setup instructions only.
4. If `current_stage = "issue_driven"`, select one or more eligible GitHub Issues using the general `Ready` / `In Progress` rules plus any explicit task-type-specific continuation rules.
5. For each selected issue, read the task metadata and determine `task_type`, `owner_contour`, dependencies, and `project_status`.
6. Stop on any selected issue unless the owner contour matches the session role and all dependencies are closed.
7. Read only the canonical artifacts and instructions allowed for that task type and contour.
8. If the task is `implementation`, rely on task-linked inputs first and stop if they are insufficient.
9. If the task is `block_delivery` in `Waiting for Testing`, treat that as a `qa-e2e` handoff, move it to `Testing`, and then validate the integrated result against its acceptance expectations.
10. If the task is `block_delivery` already in `Testing`, continue the integrated validation flow.
11. Produce only the output owned by that task.

Autonomous-mode continuation:

- after one selected issue finishes, re-evaluate the backlog before reporting a session-level stop;
- do not report a project-wide stop while any eligible `Ready` or `In Progress` issue remains;
- if a selected path becomes `Blocked`, continue with other eligible paths when they exist;
- report a session-level stop only when every remaining open path is either ineligible or blocked by a hard dependency, missing access, or required human gate.

After the session role is identified and its role file is read, the agent must adopt that file's `Execution Profile` section as the active role prompt for the remainder of the task.

## Setup Exit Conditions

Goal:
prepare the repository, workflow, and GitHub operating model.

Setup can complete in either of two modes:

- normal mode: GitHub-side bootstrap is available and the repository is fully connected to Issues/Project before stage transition;
- degraded mode: GitHub-side bootstrap is temporarily unavailable, setup records deferred GitHub reconciliation, and the local bootstrap path still completes so the repository can advance instead of stalling.

Setup completion requires:

- `.ai-dev-template.config.json` has been read and applied to the repository workflow assets and instructions;
- if `.ai-dev-template.config.json` was modified before or during setup and its contents were used, that file is committed and pushed as part of the setup evidence when GitHub access is available, or its deferred push is recorded when it is not;
- setup-side changes to instructions, docs, labels, project structure, or repository workflow assets are verified and recorded before setup exit;
- the repository has a top-level initiating Epic template or documented creation path;
- local bootstrap evidence is recorded so later agents can resume the configured workflow;
- when GitHub bootstrap is available, the repository is connected to GitHub Issues;
- when `project_tracking = github_project` and GitHub bootstrap is available, the repository is connected to a GitHub Project linked to the current repository;
- when GitHub bootstrap is available, setup creates or verifies the required labels, project fields, board view, and seeded backlog;
- when GitHub bootstrap is unavailable, setup records deferred GitHub reconciliation for the missing Issues/Project state instead of treating that absence as a stage blocker.

Blocker handling during setup:

- transient GitHub, gh, or project-access problems do not freeze setup;
- record the problem in telemetry, continue the local bootstrap path, and defer GitHub reconciliation until access returns;
- use a local-first degraded path instead of writing replacement bootstrap tooling unless the user explicitly requests that tooling.

Bootstrap transition:
update `current_stage` from `setup` to `issue_driven` when the local bootstrap path is complete; if GitHub reconciliation is deferred, record that debt in telemetry and canonical docs rather than keeping the repository stuck in `setup`.

## Task Readiness And Completion Rules

### Initiative

Ready when:

- setup is complete;
- the triggering request exists;
- no higher-level initiative already covers the same outcome.

Done when:

- child tasks for business analysis, system analysis, block delivery, implementation, deploy, and e2e are created or explicitly ruled out;
- dependency links between those tasks are recorded;
- the GitHub Project reflects the planned execution chain.

### Business Analysis

Ready when:

- an initiative exists;
- the request, requester, and expected business outcome are identifiable.

Done when:

- users, scenarios, scope, constraints, and success expectations are documented;
- unresolved business questions are recorded explicitly;
- workflow terminology and operating states are normalized for the initiative;
- exactly one downstream `system_analysis` task has sufficient intake context to start.

### System Analysis

Ready when:

- `business_analysis` outputs are complete or the initiative already has equivalent business context recorded;
- business blockers are closed.

Done when:

- the bounded analysis slice has an implementation-ready canonical analysis package;
- contour decomposition exists in `docs/delivery/contour-task-matrix.md`;
- each required `block_delivery` task for that slice exists and records ready and done rules plus canonical inputs;
- each required child implementation, deploy, and e2e task for that slice exists as its own issue;
- dependencies between those tasks are explicit in GitHub;
- any remaining unspecified scope is represented by another planned or linked follow-up `system_analysis` issue with explicit boundaries.

### Block Delivery

Ready when:

- the relevant `system_analysis` task is done;
- the integrated deliverable boundary is explicit;
- all required child implementation issues exist and are linked;
- ready and done rules for integrated validation are recorded.

Done when:

- all required child implementation issues are done;
- integrated validation passes for the block-level outcome;
- follow-up implementation issues are closed or explicitly moved to another block;
- the block task status is `Done`.

### Implementation

Ready when:

- system-analysis outputs are complete for the task's contour;
- the task belongs to exactly one `block_delivery` parent issue;
- all declared dependencies are done;
- the task status is `Ready` or `In Progress`.

Done when:

- the contour-owned change is implemented;
- required repository docs are updated;
- tests or verification owned by that contour are complete;
- downstream dependent tasks can start without guessing;
- the issue is ready for its block parent to move toward `Waiting for Testing` once sibling child issues are also done.

### Deploy

Ready when:

- all implementation tasks needed for the release slice are done;
- deployment prerequisites and runtime requirements are documented.

Done when:

- rollout succeeds in the target environment;
- deployment evidence and environment notes are recorded;
- the e2e task is unblocked.

### E2E

Ready when:

- the target `block_delivery` result is in `Waiting for Testing` or the deployed release slice is ready for integrated validation;
- user scenarios and acceptance criteria are still current.

Done when:

- critical scenarios pass end to end;
- defects are routed back into the affected `block_delivery` task and required child implementation issues when found;
- release recommendation or rejection is recorded.

## Blocking Rules

Stop and mark a task `Blocked` when any of the following is true:

- the task metadata or owner contour is missing or ambiguous;
- the task depends on unfinished work;
- a role would need to read sibling implementation code just to infer behavior;
- canonical inputs are insufficient for the task type;
- the task improperly mixes multiple owner contours;
- required access to GitHub, environments, or external systems is missing.

Hard-stop rule for autonomous routing:

- if no eligible `Ready` or `In Progress` issue remains, record that state explicitly and end the routing wave;
- before ending an autonomous routing wave, re-read the latest GitHub Issue and Project state after the most recent task update and confirm that no eligible path remains;
- if a selected issue becomes blocked because direct implementation inputs are missing but analysis-grade design context still exists in Figma Make, route that gap into `system_analysis` and continue with any other eligible path instead of treating the whole initiative as globally stopped;
- if a spawned subagent has no observable completion signal, treat that as a blocker for the current execution attempt, record the gap in telemetry, and retry with a documented fallback instead of silently dropping the path.

Blocker routing rules:

- missing business context -> create or reopen a `business_analysis` task;
- missing specifications, contracts, or decomposition -> block the current implementation issue and create or reopen a linked `system_analysis` follow-up task;
- missing UX behavior, screen states, or design assets -> create or reopen a `system_analysis` task;
- failed rollout prerequisites -> block `deploy` and create follow-up tasks in the owning contour;
- failed integrated validation -> move the relevant `block_delivery` task to `Waiting for Fix`, record defects, and create or reopen follow-up implementation issues for the owning contour of each defect.

## Target Task Flow

Canonical post-setup chain:

1. `business_analysis`
2. one or more bounded `system_analysis` issues
3. `block_delivery`
4. child `implementation` issues by contour
5. block-level validation by `qa-e2e`
6. `deploy` when rollout is required
7. initiative closure after all required blocks are done

## Documentation Update Rules

- Business problem or goals change: update `docs/01-product-vision.md` and `docs/02-business-requirements.md`.
- Scope or acceptance changes: update `docs/03-scope-and-boundaries.md` and `docs/analysis/version-scope-and-acceptance.md`.
- UX behavior changes: update `docs/analysis/ui-specification.md`.
- System design changes: update the relevant files in `docs/analysis/`.
- Repository structure or runtime placement changes: update `docs/05-architecture.md`.
- Workflow, routing, task metadata, or role rules change: update `AGENTS.md`, `.ai-dev-template.workflow-state.json`, issue templates, `instructions/`, and this file together.
- Material decisions change: update `docs/06-decision-log.md`.

## Configuration And PR Policy

The repository still uses `.ai-dev-template.config.json` for approvals and PR/review policy.

Those settings control delivery mechanics while task ownership, dependencies, GitHub Project state, and the workflow-state file remain the routing inputs.
