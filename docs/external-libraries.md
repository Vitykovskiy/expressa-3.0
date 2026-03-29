# External Libraries

## Project Dependencies

<!-- Fill this section during Phase 2 tech stack definition and update when dependencies change.
     For each library record:
     - Official best practices URL
     - Key rules most commonly violated (based on known best practices for this library)
     - Size and decomposition limits where applicable
     - Project conventions that differ from library defaults
-->

_Not yet filled. Complete during Phase 2 tech stack definition._

<!--
Example entry:

## Vue 3
Official best practices: https://vuejs.org/guide/best-practices/performance.html
- Use Composition API, not Options API
- Max component size: 300 lines — extract logic to composables, split UI to child components
- One component = one responsibility
- No direct API calls from components — use composables for data fetching

## Pinia
Official best practices: https://pinia.vuejs.org/cookbook/
- Split stores by domain, not one global store
- Business logic in actions, not in components or templates
- Do not mutate state outside of actions
-->

---

## Rules

- Do not rely on memory, guesses, or "typical API".
- Check this file first.
- Check real usage examples in the codebase next.
- Check official documentation after that.
- If confirmation is missing, mark uncertainty explicitly.
- Do not invent API.
- Do not use unconfirmed methods, parameters, or options.
- Do not apply version-sensitive patterns without checking the current version.

## Required Verification

Before changing code, verify:

- signatures;
- types;
- method names;
- supported options;
- lifecycle or initialization rules;
- version limitations.

## Allowed Sources Of Truth

Use one of the following:

- the Project Dependencies section above;
- official documentation available to the agent;
- an existing working example in the codebase.

## Missing Documentation Rule

If no confirmed source of truth is available:

- do not make risky blind changes;
- leave a note about the missing confirmation;
- prefer the safest minimal change if possible.

## Maintenance Rule

When a new external dependency is added or an existing one is upgraded — update the Project Dependencies section above before closing the task.
