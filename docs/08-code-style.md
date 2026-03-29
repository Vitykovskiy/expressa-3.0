# Code Style

This file defines code style rules for the project. It is created during Phase 1 based on the chosen tech stack and updated as new conventions are established.

The agent reads this file at the start of every session and enforces all rules before closing any task.

---

## Size Limits

| Unit | Max size | Action when exceeded |
|---|---|---|
| File | — | Decompose into modules |
| Component / class | — | Split by responsibility |
| Function / method | — | Extract to a named helper |

> Fill in limits based on the tech stack during Phase 1. Examples: Vue 3 component ≤ 300 lines, composable ≤ 150 lines; React component ≤ 250 lines, custom hook ≤ 100 lines; Go function ≤ 60 lines.

---

## Decomposition Rules

- Extract to a separate module/component when it has a distinct, nameable responsibility.
- A unit that is reused in more than one place must be extracted.
- Avoid files that mix unrelated concerns (e.g. data fetching + rendering + business logic in one component).

---

## Naming

- _Fill in project naming conventions here._

---

## Accepted Patterns

- If `.ai-dev-template.config.json` contains `architecture.use_fsd: true`, frontend code follows FSD layers and import boundaries.
- _List patterns explicitly approved for this project._

---

## Forbidden Patterns

- If `.ai-dev-template.config.json` contains `architecture.use_fsd: true`, keep FSD boundaries explicit with layer-aligned imports and responsibilities.
- _List patterns explicitly banned for this project._

---

## Notes

- If `architecture.use_fsd` is `false`, document and enforce the alternative frontend structure chosen by the team.
- _Any project-specific style notes that do not fit the categories above._
