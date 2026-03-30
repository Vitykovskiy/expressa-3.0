# Project Overview

## Purpose

This file is the high-signal entry point for a new agent session.

Use it to identify:

- the current repository mode;
- the active initiative;
- the currently active execution work;
- which canonical artifacts exist;
- where each role must read next.

## Workflow Summary

The repository follows a fixed 2-mode workflow tracked in `.ai-dev-template.workflow-state.json`:

1. `setup`
2. `issue_driven`

Mode semantics:

- `setup`: the technical agent prepares workflow assets, GitHub operating infrastructure, and the seeded starting backlog;
- `issue_driven`: all post-setup work routes through eligible GitHub Issues, their task metadata, their owner contour, their dependencies, and GitHub Project state.

See `AGENTS.md` for routing and `docs/07-workflow.md` for the canonical workflow rules.
If you need to diagnose execution friction, consult `docs/12-observability.md` for the local telemetry contract.

## Current Status

- Workflow state file: `.ai-dev-template.workflow-state.json`
- Current stage: `issue_driven`
- Session mode: `execution`
- Active initiative: `#1`
- Active execution issues: `none`
- Current owner role: `none`
- Delivery status: `waiting_for_testing_handoff`

## Canonical Artifact Map

### Intake And Product Context

- `docs/01-product-vision.md`
- `docs/02-business-requirements.md`
- `docs/03-scope-and-boundaries.md`

### Analysis Package

- `docs/analysis/problem-context.md`
- `docs/analysis/user-scenarios.md`
- `docs/analysis/version-scope-and-acceptance.md`
- `docs/analysis/system-modules.md`
- `docs/analysis/domain-model.md`
- `docs/analysis/integration-contracts.md`
- `docs/analysis/ui-specification.md`
- `docs/analysis/cross-cutting-concerns.md`

### Development Handoff

- `docs/delivery/contour-task-matrix.md`

### Operating Documents

- `docs/05-architecture.md`
- `docs/06-decision-log.md`
- `docs/07-workflow.md`
- `docs/09-integrations.md`
- `docs/11-workflow-configuration.md`
- `docs/12-observability.md`

## Reading Policy

- Start with `AGENTS.md`.
- Read `.ai-dev-template.workflow-state.json`.
- Read only the branch selected by the router.
- Load only the canonical artifacts required for the current mode, task type, and role.
- If no eligible issue can be safely continued or claimed under the documented `Ready` -> `In Progress` rules, treat that as a blocker.
- If an implementation, deploy, or e2e role needs to infer behavior from unrelated code or documents, treat that as a blocker and route the gap back into `system_analysis` through the issue workflow.

## GitHub Backbone

- Initiative and task tracking: GitHub Issues
- Delivery status: GitHub Project
- Integration metadata: `docs/09-integrations.md`
- Linked GitHub Project: `https://github.com/users/Vitykovskiy/projects/24`
- Seeded backlog: `#1` initiative, `#2` initial `business_analysis`, `#3` initial `system_analysis`
- Downstream planning chain: `#4` infrastructure, `#5` customer block, `#6` backoffice block, `#7-#13` implementation/e2e/deploy issues

## Notes

Keep this file concise. It should orient a new session without duplicating the detailed stage artifacts.
Stage 0 infrastructure is complete and staging baseline is live at `http://216.57.105.133:8080`.
The current QA-eligible issues are `#9` and `#12` after their parent blocks move to `Waiting for Testing` and their dependencies remain closed.

