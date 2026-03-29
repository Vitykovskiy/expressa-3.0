# AGENTS.md

Read this file first at the start of every new session.

## Agent Modes

### Dialogue session (default)

The agent answers questions, explains decisions, and helps the user think through the work. It does not pick up tasks, run subagents, or advance the workflow.

Dialogue session is active when:
- `mode` in `.ai-dev-template.workflow-state.json` is `"dialogue"` or the field is absent; **or**
- the user message contains no explicit execution command.

### Execution session

The agent picks up tasks from the backlog, runs subagents, and advances the workflow.

Execution session activates when **either** of the following is true:
- `mode` in `.ai-dev-template.workflow-state.json` is `"execution"`; **or**
- the user message contains an explicit execution command such as "run", "execute", "start workflow", "pick up next task".

The orchestrator itself never implements. It only launches subagents and tracks their results.

`workflow.execution_mode` in `.ai-dev-template.config.json` controls how aggressively the orchestrator keeps moving once execution is active:

- `manual`: execution starts from an explicit execution session and may end after one bounded routing wave;
- `autonomous`: execution still requires a valid execution session, but the orchestrator should keep claiming eligible work until no eligible `Ready` or `In Progress` issues remain or a hard workflow stop is reached.

## Router Goal

This repository uses a bootstrap stage plus a session mode:

1. `current_stage = "setup"` bootstraps the repository, workflow assets, labels, and GitHub operating model; if GitHub-side bootstrap is temporarily unavailable, setup continues in local-first fallback mode and records deferred reconciliation instead of stalling.
2. `current_stage = "issue_driven"` runs all post-setup work through GitHub Issues, task dependencies, owner contours, and GitHub Project state.
3. `mode = "dialogue"` or `mode = "execution"` controls session behavior for the current run.

After `setup`, the workflow proceeds through these stages:

```
Stage BA - Business analysis (business-analyst)
Stage 0  - Infrastructure   (devops)
Stage 1  - Design system    (system-analyst)
Stage 2  - Decomposition    (system-analyst)
Stage 3+ - Implementation   (frontend / backend / devops) -> repeat per block
Stage 4+ - QA per block     (qa-e2e) -> repeat per block
```

Infrastructure (Stage 0) must be complete before any implementation task is created or starts.

Setup must not transition to `issue_driven` until the repository has a seeded starting backlog containing at least one open `initiative` issue and exactly one open initial `business_analysis` issue.

## Canonical Document Roles

- `AGENTS.md` is the session router and task-selection guardrail.
- `docs/07-workflow.md` is the canonical workflow policy.
- `docs/11-workflow-configuration.md` explains which workflow parts are fixed and which are configurable.
- `README.md` is a human overview, not the canonical workflow policy.

## Bootstrap State Detection

Read `.ai-dev-template.workflow-state.json` and use `current_stage` and `mode` exactly as written.

`current_stage` allowed values:

1. `setup`
2. `issue_driven`

`mode` allowed values:

1. `dialogue` (default when absent)
2. `execution`

If the file is missing, malformed, or contains an unsupported value, stop and report a blocker.

`current_stage` acts as a bootstrap guardrail:

- `setup` means the repository is being prepared for operational work;
- `issue_driven` means setup is complete and routing comes from eligible GitHub Issues plus GitHub Project state.

## Git Delivery Rule

Before starting a task, sync Git state and confirm the working branch is based on the latest remote state of its parent branch.

After creating a commit, sync again and confirm the branch still grows from the latest working branch state before continuing, handing off, or opening a PR.

Every completed task handoff must have repository-persisted evidence and verified operational side effects:

- commit all repository changes required for the completed task output;
- push that commit before considering the task handoff complete;
- before any PR creation, merge, or other delivery action governed by `.ai-dev-template.config.json`, read the repository's committed config, decide the effective delivery policy for this repository, and record that decision in telemetry;
- if the effective config cannot be read, is ambiguous, or contradicts the current delivery action, fail closed: do not create or merge a PR until the policy is clarified;
- if `pull_requests.enabled = true`, follow the configured PR policy after pushing;
- if `pull_requests.enabled = false`, push directly to the assigned working branch;
- verify the push and any required GitHub side effects before reporting completion;
- keep completed task outputs in the repository worktree as committed, pushed evidence;
- pair GitHub-side changes with corresponding canonical repository document updates, commits, and pushes.

If the branch is behind, diverged, or based on an outdated parent, stop implementation work, reconcile the branch history, and then continue.

The repository's committed `.ai-dev-template.config.json` is the effective workflow policy for that repository. Template updates do not retroactively change repositories that were already created from an older template state.

Treat GitHub's post-push suggestion text such as `Create a pull request` as transport output, not as policy. Only the repository's committed config decides whether a PR should actually be opened.

## Text Encoding Rule

When creating or updating text files that will be consumed by Git, GitHub CLI, or other external tools, use explicit UTF-8 encoding.

- treat UTF-8 as the required default for markdown, issue bodies, PR bodies, commit-message files, templates, and other workflow text artifacts;
- on Windows or in PowerShell, use explicit UTF-8 encoding for files that may contain non-ASCII text;
- when creating temporary files for `gh` or related tooling, write them in UTF-8 explicitly, preferably UTF-8 without BOM;
- if text appears corrupted after a tool call, treat it as an encoding failure and rewrite the source file with explicit UTF-8 before retrying.

## Post-Setup Routing

When `current_stage = "issue_driven"`, route work from the eligible GitHub Issues.

Active execution signal:

- any open issue whose required task metadata is present, whose declared dependencies are complete, and whose GitHub Project status is `In Progress` is active execution work;
- multiple open issues may be active at the same time when their dependencies are resolved and their ownership is explicit;
- `Ready` is the only universal claimable status for starting a new task from backlog;
- `In Progress` means the issue has been claimed and is currently being executed;
- `Inbox`, `Blocked`, `Waiting for Testing`, `Testing`, `Waiting for Fix`, and `In Review` are workflow handoff or control states, not universal claimable statuses;
- one of those non-terminal statuses may still require role-specific continuation when a task-type-specific rule says so.

Eligible issue selection order:

1. consider only open issues with all required task metadata present and all declared dependencies already complete;
2. treat issues whose GitHub Project status is `In Progress` as already active work;
3. if a new task must be started, consider eligible issues with status `Ready`;
4. within the chosen status bucket, sort by priority label in this order: `priority: high`, `priority: medium`, `priority: low`, then unlabeled;
5. if more than one issue still matches and no stronger repository policy applies, choose the lowest issue number.

Claim/start rule:

- an agent may continue an eligible issue already in `In Progress`;
- an agent may start an eligible issue in `Ready` only by first moving it to `In Progress`;
- after moving a `Ready` issue to `In Progress`, re-read the issue and project state before continuing so the claim is verified against the latest metadata;
- if the issue can no longer be safely claimed after that re-read, stop and treat it as unavailable instead of proceeding optimistically.
- a blocked issue stops only that issue path; it does not justify a global stop while another eligible `Ready` or `In Progress` issue still exists.

Handoff/control-state rule:

- non-terminal statuses other than `Ready` and `In Progress` do not open a task for general backlog pickup by themselves;
- continue work from those statuses only when a task-type-specific rule explicitly instructs the owning contour to do so;
- `Waiting for Testing` is a `block_delivery` handoff state for `qa-e2e`, not a general backlog pickup state;
- when `qa-e2e` starts integrated validation from `Waiting for Testing`, move the task to `Testing` before continuing;
- `Waiting for Fix` requires follow-up implementation issues to be created or reopened and claimed through the normal `Ready` -> `In Progress` rule, rather than claiming the parent block task as new work.

Every operational task must have these required attributes, expressed through issue body fields, labels, or project fields:

- task type: one of `initiative`, `business_analysis`, `system_analysis`, `infrastructure`, `block_delivery`, `implementation`, `deploy`, `e2e`;
- owner contour: exactly one of `business-analyst`, `system-analyst`, `frontend`, `backend`, `devops`, `qa-e2e`;
- parent initiative: the top-level Epic or initiative issue;
- parent block task: required for implementation issues that contribute to an integrated delivery block;
- dependencies: explicit issue links or a `Blocked by` list;
- ready rule: why the task is allowed to start;
- done rule: what must be true to close the task;
- canonical inputs: the specific repository artifacts and linked issues the task may rely on;
- project status: one of `Inbox`, `Ready`, `In Progress`, `Blocked`, `Waiting for Testing`, `Testing`, `Waiting for Fix`, `In Review`, `Done`.

Required task chain after setup:

1. one `business_analysis` issue clarifies the request, users, scope, constraints, and workflow vocabulary;
2. one or more `system_analysis` issues produce the canonical specification package including `uiux_contract` for any UI work;
3. one `infrastructure` issue completes CI/CD and VPS setup (Stage 0); no implementation task may start until this is done;
4. each `system_analysis` issue decomposes its approved analysis slice into one or more parent `block_delivery` tasks;
5. each `block_delivery` task owns child implementation issues, one per responsible contour (`frontend`, `backend`, `devops`, `qa-e2e` when contour-owned test assets are required);
6. `qa-e2e` validates the integrated result at the `block_delivery` level after all required child implementation issues are done;
7. `deploy` remains separate when rollout is required for the validated slice.

## Task Selection Rules

An agent works on a task when all of the following are true:

- the task owner contour matches the agent's role for the session;
- all declared dependencies are already complete or explicitly marked as no longer blocking;
- the issue is either eligible for general pickup through `Ready` / `In Progress` or explicitly selectable through a task-type-specific handoff rule for its current status;
- if the current status is not `Ready` or `In Progress`, the agent has an explicit role-specific reason in the workflow rules to continue from that status;
- the canonical inputs named by the task exist and are sufficient;
- the task belongs to exactly one owner contour.

Execution stays within the assigned contour, resolved dependency set, and declared task boundary.

## Role Detection

Use the active task's `owner contour` field to determine the role for the current session:

- `business-analyst`
- `system-analyst`
- `frontend`
- `backend`
- `devops`
- `qa-e2e`

If the owner contour is missing or ambiguous, stop and report a blocker.

## Role Prompt Rule

After the session role is identified and the corresponding role file is read, adopt that role file's `Execution Profile` section as the active role prompt for the rest of the task.

Rules:

- treat the role profile as mandatory operating behavior;
- apply the role profile together with repository safety, routing, dependency, and blocking rules;
- if a role file says to verify, review, or avoid assumptions, perform that behavior explicitly before reporting completion;
- preserve the role's required rigor throughout the task.

## Execution Telemetry Rule

During every session, the agent and any spawned subagents must append structured local telemetry to `.agent-work/telemetry/` using the schema in `docs/12-observability.md`.

Telemetry must capture task selection, attempted actions, tool calls, failures, retries, blockers, workarounds, and handoffs.

If a spawned subagent has no observable completion path, treat that as a workflow blocker for the current attempt, record it in telemetry, and retry with a concrete fallback such as respawn, direct execution, or explicit handoff recovery. Do not silently end the orchestration wave after a spawn with no completion evidence.

When delivery policy matters, record a `decision_recorded` event before the governed action with enough metadata to reconstruct the choice, including whether `pull_requests.enabled` was true or false and which action was allowed or denied.

Telemetry is local runtime evidence, not durable repository state. Do not commit trace files unless the task explicitly asks for telemetry persistence.

## Allowed Reading By Mode And Task Type

Read only the files listed for the active mode and task type.

### setup

Read, in order:

1. `.ai-dev-template.workflow-state.json`
2. `instructions/setup/router.md`
3. `instructions/setup/technical-agent.md`

Setup must ensure the repository is configured according to `.ai-dev-template.config.json` before switching to `issue_driven`. Apply the configuration to workflow assets, instructions, issue templates, labels, project structure, and required repository-management infrastructure. When GitHub-side bootstrap is available, create or validate labels, GitHub Project structure, repository linkage, and other GitHub-side setup artifacts directly through `gh` or equivalent integrated tooling instead of relying on repository bootstrap scripts. If GitHub Project tracking is configured, treat only a project already linked to the current repository as an existing project for setup purposes. If no repository-linked project exists and GitHub access is available, create one, connect it to the repository, record it in the canonical docs, and advance the bootstrap state after that integration is validated. If GitHub-side bootstrap is temporarily unavailable, record deferred GitHub reconciliation, continue local bootstrap, and do not let the missing GitHub path block setup progress.
Setup must also seed the starting backlog before leaving `setup` when GitHub access is available. At minimum, create one open `initiative` issue plus one open `business_analysis` issue directly through GitHub and leave that `business_analysis` issue in `Ready` so it can be claimed by the first execution session. If GitHub access is temporarily unavailable, capture the intended backlog as deferred reconciliation and continue the local bootstrap path instead of stalling setup.
If GitHub-side setup is blocked by missing auth, permissions, CLI support, or other environment constraints, record the blocker in telemetry, continue the local bootstrap path, and defer GitHub reconciliation until access returns unless the user explicitly requests a replacement bootstrap workflow.
If setup consumed a user-updated `.ai-dev-template.config.json`, that file is part of the effective setup state and must be staged and committed; push it as part of the setup evidence when GitHub access is available, or record deferred push reconciliation when it is not.

### business_analysis

Read, in order:

1. `instructions/intake/router.md`
2. `instructions/intake/business-analyst.md`
3. `docs/00-project-overview.md`
4. `docs/07-workflow.md`
5. `docs/11-workflow-configuration.md`

Business analysis clarifies the bounded business slice and creates only the downstream analysis tasks needed for that slice. It must not create implementation tasks directly.

### system_analysis

Read, in order:

1. `instructions/analysis/router.md`
2. `instructions/analysis/system-analyst.md`
3. `docs/00-project-overview.md`
4. `docs/07-workflow.md`
5. `docs/09-integrations.md`
6. `docs/analysis/README.md`
7. the specific files in `docs/analysis/` required for the initiative

### infrastructure

Read, in order:

1. `instructions/delivery/router.md`
2. `instructions/delivery/roles/devops.md`
3. `docs/00-project-overview.md`
4. `docs/04-tech-stack.md`
5. `docs/09-integrations.md`

### implementation

Read, in order:

1. `instructions/delivery/router.md`
2. exactly one role file from `instructions/delivery/roles/`

Allowed role files:

- `instructions/delivery/roles/frontend.md`
- `instructions/delivery/roles/backend.md`
- `instructions/delivery/roles/devops.md`
- `instructions/delivery/roles/qa-e2e.md`

Minimum common context:

- `docs/00-project-overview.md`
- `docs/07-workflow.md`
- `docs/analysis/README.md`
- `docs/delivery/contour-task-matrix.md`

Read only the canonical artifacts for the assigned contour and the exact contracts it depends on.

### deploy

Read, in order:

1. `instructions/deploy/router.md`
2. `instructions/deploy/devops.md`
3. `docs/00-project-overview.md`
4. `docs/07-workflow.md`
5. `docs/analysis/cross-cutting-concerns.md`
6. `docs/delivery/contour-task-matrix.md`
7. `docs/runbooks/deployment-runbook.md`

### e2e

Read, in order:

1. `instructions/delivery/roles/qa-e2e.md`
2. `docs/00-project-overview.md`
3. `docs/analysis/user-scenarios.md`
4. `docs/analysis/version-scope-and-acceptance.md`
5. `docs/runbooks/e2e-validation-runbook.md`

## Blocking Rules

Stop and report a blocker when any of the following is true:

- `.ai-dev-template.workflow-state.json` is missing or invalid;
- setup is not complete but work tries to bypass `setup`;
- the task metadata or owner contour is missing or ambiguous;
- the task has unresolved dependencies;
- the active role is ambiguous;
- canonical analysis artifacts are insufficient for implementation, deployment, or testing;
- a task tries to combine multiple contours without explicit decomposition;
- a role would need to read unrelated instructions or sibling implementation code just to infer expected behavior;
- a frontend task is missing a usable `uiux_contract` or any other implementation-ready UI/UX contract;
- an infrastructure task is not yet done and an implementation task tries to start.

In `workflow.execution_mode = "autonomous"`, report a global stop only when:

- no eligible `Ready` issue remains;
- no eligible `In Progress` issue remains;
- every remaining open path is blocked by an unresolved hard dependency, missing access, or required human gate.
- the orchestrator has re-read the latest GitHub Issue and Project state after the most recent task completion, blocker update, or subagent retry decision and still finds no eligible path.

When blocked by missing specifications, contracts, decomposition details, or UX behavior, stop implementation, mark the implementation task `Blocked`, and create or request a linked `system_analysis` follow-up issue before any coding continues.

