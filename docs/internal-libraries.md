# Internal Libraries

## Project Shared Modules

<!-- Fill this section when shared modules, packages, or reusable abstractions exist in the project.
     For each module record: what it exports, how to initialize, contracts and types to rely on. -->

_Not yet filled. Complete when shared modules are introduced._

---

## Rules

- Do not assume internal library API from naming alone.
- Check this file first.
- Then inspect real usage in the codebase.
- Treat existing working consumers as stronger evidence than guesswork.
- If the API contract is still unclear, mark uncertainty and avoid risky changes.

## Required Verification

Before changing code that depends on a shared module, verify:

- exported types;
- public signatures;
- required initialization or provider pattern;
- supported props, options, or config shape;
- version or package boundary constraints.

## Source Of Truth

Use one of the following:

- the Project Shared Modules section above;
- the library source code and its exported types;
- an existing working example in the codebase.

## Missing Confirmation Rule

If the internal contract is not confirmed:

- do not invent API;
- do not use unconfirmed exports;
- leave a note about the missing source of truth;
- prefer the safest minimal change if possible.

## Maintenance Rule

When a new shared module is created or an existing one changes its public contract — update the Project Shared Modules section above before closing the task.
