# AI Dev Template

Template repository for an AI team that uses `setup` as a one-time bootstrap step and then runs all delivery through GitHub Issues, block-level delivery tasks, contour-owned child issues, and GitHub Project state.

## Operating Model

The template uses a bootstrap stage plus a session mode recorded in `.ai-dev-template.workflow-state.json`:

1. `current_stage = setup` - technical agent initializes the repository, issue templates, labels, project structure, and workflow rules.
2. `current_stage = issue_driven` - all post-setup work is routed by GitHub task metadata, dependencies, owner contours, and GitHub Project state.
3. `mode = dialogue` or `mode = execution` - session behavior for the current run.

After `setup`, GitHub Issues become the primary execution objects:

- an initiating Epic anchors the initiative;
- one `business_analysis` issue starts the initiative;
- one or more bounded `system_analysis` issues produce the canonical specification package slice by slice and decompose only the delivery they fully specify;
- each `block_delivery` task represents one integrated deliverable and owns child implementation issues;
- every implementation issue has one owner contour and explicit dependencies;
- multiple open issues may be `In Progress` at the same time when their dependencies are resolved and their ownership is explicit;
- agents execute only tasks owned by their contour and only when task-linked inputs are sufficient;
- GitHub Project holds the canonical execution state for those issues.

## Core Principles

- Implementation starts after the required business-analysis and system-analysis tasks are complete.
- `system_analysis` remains the single source of truth for implementation inputs and block decomposition, but analysis may be split into bounded slices.
- User scenarios, interfaces, contracts, and acceptance expectations exist before contour-owned implementation starts.
- Each task has exactly one owner contour.
- Cross-contour delivery is decomposed into linked tasks with explicit ownership.
- Missing specification routes work into a linked `system_analysis` follow-up task with explicit clarification scope.
- Large initiatives may split `system_analysis` by version slice, capability slice, or explicit follow-up clarification scope.
- `qa-e2e` validates integrated block-level outcomes.
- An initiative closes after required block-level validation, deploy work, and e2e tasks finish successfully.

## Repository Layout

- `AGENTS.md` - router that decides between `setup` and post-setup issue-driven routing.
- `.ai-dev-template.workflow-state.json` - bootstrap guardrail that records whether setup is still active.
- `instructions/` - setup instructions plus task-type and contour-specific instructions.
- `docs/analysis/` - canonical analysis package that gates implementation, deploy, and e2e work.
- `docs/delivery/` - block decomposition and contour handoff artifacts.
- `docs/runbooks/` - canonical deployment and integrated-validation instructions.
- `docs/12-observability.md` - local telemetry contract for agent attempts, failures, retries, blockers, and workarounds.
- `.agent-work/telemetry/` - gitignored runtime traces for local execution analysis.
- `templates/` - reusable templates for initiative, business-analysis, system-analysis, implementation, deploy, and e2e tasks.
- `tasks/` - local scratch space only; not a durable backlog.

## Canonical Document Roles

- `AGENTS.md` is the runtime router for the current session.
- `docs/07-workflow.md` is the canonical workflow policy.
- `docs/11-workflow-configuration.md` explains which parts of the operating model are fixed and which are configurable.
- `docs/12-observability.md` defines the local telemetry format used to analyze execution friction and workflow failures.
- `README.md` is an entrypoint overview for humans, not the canonical policy source.

## How A New Project Starts

1. Create a repository from this template and clone it locally.
2. Add `.ai-dev-template.config.json` to the root.
3. Keep `.ai-dev-template.workflow-state.json` in the root with `current_stage = "setup"`.
4. Connect the repository to GitHub Issues and a GitHub Project board when GitHub access is available. During `setup`, create or validate the required labels directly through `gh` or equivalent GitHub-integrated tooling, create and link the repository GitHub Project directly, and seed the initial initiative plus `business_analysis` backlog directly. If `project_tracking = github_project`, treat only a project already linked to this repository as an existing match. If no repository-linked project exists yet and GitHub access is available, create one and attach the repository before leaving `setup`. If the environment blocks GitHub-side setup, continue in local-first fallback mode and record deferred GitHub reconciliation instead of stopping.
5. Give the agent access to the repository and the business request.
6. Start with `AGENTS.md`; the router will either keep the repository in `setup` or switch to issue-driven routing after setup is validated.

When GitHub access is available, the repository must not leave `setup` until the starting backlog exists:

- at least one open `initiative` issue exists;
- exactly one open initial `business_analysis` issue exists;
- that `business_analysis` issue is in `Ready`.

## GitHub Workflow

GitHub Issues and GitHub Project are the operational backbone after setup.

Required GitHub Issue types:

- `initiative`
- `business_analysis`
- `system_analysis`
- `block_delivery`
- `implementation`
- `deploy`
- `e2e`

Required task attributes:

- task type
- owner contour
- parent initiative
- explicit dependencies
- definition of ready
- definition of done
- canonical inputs
- GitHub Project status

Canonical active execution signal:

- any eligible open issue with GitHub Project status `In Progress`
- multiple open issues may be `In Progress` at the same time
- an agent may start a `Ready` issue only by moving it to `In Progress` first and then re-reading the issue state before continuing

Required GitHub Project statuses:

- `Inbox`
- `Ready`
- `In Progress`
- `Blocked`
- `Waiting for Testing`
- `Testing`
- `Waiting for Fix`
- `In Review`
- `Done`

Required GitHub Project board fields:

- `Status`
- `Task Type`
- `Owner Contour`
- `Priority`

Required workflow labels:

- `priority: high`
- `priority: medium`
- `priority: low`

Completed task handoffs must have verified evidence. Repository changes must be committed and pushed, and required GitHub-side workflow actions must be verified before completion is reported when GitHub access is available. When GitHub access is temporarily unavailable, the agent records deferred reconciliation and continues the local bootstrap path. When pull requests are disabled, the agent pushes directly to the assigned working branch.

Workflow text artifacts should be written in UTF-8. On Windows and in PowerShell, files passed to `gh`, `git`, or similar tools must use explicit UTF-8 encoding to avoid corrupted non-ASCII text.

Local execution telemetry belongs in `.agent-work/telemetry/` and stays out of version control unless a task explicitly requires persistence.

## Bootstrap Guardrail

`.ai-dev-template.workflow-state.json` remains in the repository as a lightweight guardrail:

- `setup` keeps the repository in bootstrap preparation mode until the repository and GitHub operating model are ready;
- `issue_driven` activates post-setup routing through task metadata, dependencies, owner contours, and GitHub Project state.

The file records the active repository mode and the setup-to-operations transition.

## Configuration

Workflow policy is configured in `.ai-dev-template.config.json`.

The configuration governs execution pacing, language, approval checkpoints, and PR/review behavior. It does not replace task ownership, dependencies, or GitHub Project state.

It also governs optional repository conventions such as `architecture.use_fsd`, which tells the template whether frontend work should explicitly follow Feature-Sliced Design.

The effective policy is always the repository-local committed `.ai-dev-template.config.json`. Updating the template later does not retroactively rewrite repositories that were already created from it.

Human-facing repository artifacts may follow configured language settings, but agent-only control files such as `AGENTS.md`, `instructions/`, routers, and role prompts must remain in English.
