# Analysis Package

`docs/analysis/` is the canonical implementation-ready specification package.

Implementation, deploy, and e2e tasks work from these artifacts as their canonical behavior source.

## Required Files

- `problem-context.md`
- `user-scenarios.md`
- `version-scope-and-acceptance.md`
- `system-modules.md`
- `domain-model.md`
- `integration-contracts.md`
- `ui-specification.md`
- `cross-cutting-concerns.md`

## Source Of Truth By Role

- business analyst: intake-facing product docs plus scenario context
- system analyst: all analysis files in this folder
- frontend: `user-scenarios.md`, `ui-specification.md`, consumed portions of `integration-contracts.md`, `version-scope-and-acceptance.md`
- backend: `system-modules.md`, `domain-model.md`, produced and consumed portions of `integration-contracts.md`, `cross-cutting-concerns.md`, `version-scope-and-acceptance.md`
- devops: `cross-cutting-concerns.md`, runtime-related module and integration details, rollout constraints
- qa-e2e: `user-scenarios.md`, `ui-specification.md`, `version-scope-and-acceptance.md`, deployed environment notes

## Rule

If any role cannot execute from the artifacts it owns for the active delivery slice, that slice is not ready and must return to the relevant `system_analysis` issue through GitHub task routing.
