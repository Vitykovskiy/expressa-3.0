# Decision Log

Use ADR-lite entries. Add new decisions to the top.

## 2026-03-29 - Treat repo-local config as authoritative after template creation

- Decision: A repository created from the template keeps its own committed `.ai-dev-template.config.json` as the workflow policy source of truth after setup.
- Reason: Template defaults can evolve over time, but previously created repositories must remain governed by their committed local policy unless a user explicitly changes it.
- Consequences: Setup and later sessions must not infer PR or pacing policy from the current template repository when the target repository already has its own committed config.

## 2026-03-29 - Allow local-first setup fallback when GitHub bootstrap is temporarily unavailable

- Decision: Setup may continue in local-first fallback mode when GitHub-side bootstrap is temporarily unavailable, provided the agent records deferred GitHub reconciliation and the local bootstrap state remains internally consistent.
- Reason: GitHub auth, project wiring, or network availability should not stop the repository from progressing through setup and preparing the local operating model.
- Consequences: Setup instructions, workflow docs, and telemetry must distinguish between normal GitHub-backed bootstrap and deferred GitHub reconciliation so later sessions can resume the remote side without guessing.

## 2026-03-29 - Require Make-aware system analysis before declaring UI-source absence

- Decision: System analysis must use Figma Make context when available to extract UI/UX contracts, and direct Figma frames are optional rather than mandatory.
- Reason: Make can provide real screen-level design context and the implementation flow should be able to continue from a usable contract even when no exact frame link exists.
- Consequences: Analysis docs may be enriched from Make or other references, and frontend implementation continues from the approved UI/UX contract unless the contract itself is insufficient.

## 2026-03-13 - Establish template operating model

- Decision: Use repository docs as the source of truth for project context and GitHub Issues plus GitHub Project as the source of truth for delivery state.
- Reason: New agent sessions must be able to resume work predictably without relying on transient context.
- Consequences: Documentation and issue hygiene become mandatory parts of task completion.

## 2026-03-16 - Add configurable workflow policy

- Decision: Introduce `.ai-dev-template.config.json` as the workflow policy file for language, approval checkpoints, PR policy, and artifact persistence.
- Reason: The template must support different collaboration models without hardcoding one fixed operating mode.
- Consequences: Agent behavior, docs, and setup scripts must honor the configuration before project execution starts.
