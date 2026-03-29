# Integrations

## GitHub Project

- URL: `<paste GitHub Project URL here>`
- Board type: `Kanban`
- Required statuses present: `yes/no`
- Required fields present: `Status`, `Task Type`, `Owner Contour`, `Priority`
- Project item creation verified: `yes/no`
- Setup validation status: `Unknown`
- Notes: If `project_tracking = github_project`, prefer a repository-linked project for normal setup. If GitHub-side bootstrap is temporarily unavailable, record deferred reconciliation and continue local bootstrap instead of blocking the stage.

## GitHub Issues

- Initiative issue creation verified: `yes/no`
- Initial seeded `business_analysis` issue verified: `yes/no`
- Operational issue templates verified: `yes/no`
- Required task metadata captured by forms: `yes/no`
- Ready -> In Progress claim/start flow verified: `yes/no`
- Labels prepared for workflow use: `yes/no`
- Notes: Record the identifiers or URLs needed to prove that workflow-required issue records exist.

## Effective Workflow Policy

- Effective `.ai-dev-template.config.json` committed and pushed: `yes/no`
- Notes: If setup used a modified configuration file, record the commit or push evidence here.

## Bootstrap Access Variables

These variables describe the raw VPS access that DevOps receives at Stage 0. They are inputs, not published app credentials.

| Variable | Required | Purpose | Stage first needed | Status |
| --- | --- | --- | --- | --- |
| `VPS_HOST` | yes | Raw VPS host or IP for Stage 0 bootstrap | `setup` | Unknown |
| `VPS_USER` | yes | Raw VPS login user for Stage 0 bootstrap | `setup` | Unknown |
| `VPS_PORT` | no | SSH port for Stage 0 bootstrap | `setup` | 22 |
| `VPS_PASSWORD` | one of | Password auth for Stage 0 bootstrap | `setup` | Unknown |
| `VPS_SSH_PRIVATE_KEY_PATH` | one of | Local path to SSH private key for Stage 0 bootstrap | `setup` | Unknown |
| `VPS_SSH_PRIVATE_KEY` | one of | Secret-backed SSH key material for Stage 0 bootstrap | `setup` | Unknown |

## Published Runtime And Validation Contract

These variables are produced or published by DevOps after Stage 0. They are not required for setup.

| Variable | Required | Purpose | Stage first needed | Status |
| --- | --- | --- | --- | --- |
| `TARGET_URL` | no | Published target environment URL | `deploy/e2e` | Unknown |
| `TARGET_LOGIN` | no | Authenticated access for validation or operations | `deploy/e2e` | Unknown |
| `TARGET_PASSWORD` | no | Authenticated access for validation or operations | `deploy/e2e` | Unknown |

## Tokens And Secrets

| Secret | Where It Lives | Purpose | Stage first needed | Status |
| --- | --- | --- | --- | --- |
| `gh` auth token | GitHub CLI auth store | Issues and Project automation | `setup` | Unknown |

## GitHub Token Scope Baseline

Required scopes:

- `repo`
- `project`

Recommended scopes:

- `read:org`
- `workflow`

Validation note:

- token scopes are necessary but not sufficient;
- repository membership, project write access, and branch protection rules must still be validated separately;
- record actual validation results in this file during `setup`;
- report setup or later GitHub-side workflow steps complete after the corresponding side effects are verified.

## Runtime And External Integrations

Document every external system that matters to development, deploy, or e2e validation.

| Integration | Purpose | Stage first needed | Status | Notes |
| --- | --- | --- | --- | --- |
| `<integration>` | `<purpose>` | `<setup/business_analysis/system_analysis/implementation/deploy/e2e>` | `<status>` | `<notes>` |

## Integration Status

- GitHub repository access: `Unknown`
- GitHub Project access: `Unknown`
- Deployment environment access: `Unknown`
- E2E environment readiness: `Unknown`

## Runbook References

- Deployment runbook: `docs/runbooks/deployment-runbook.md`
- E2E validation runbook: `docs/runbooks/e2e-validation-runbook.md`

## Setup Notes

- Update this file as integrations are connected or changed.
- During `setup`, validate GitHub Issues access and GitHub Project access, and record the actual result here.
- Record verification evidence for the GitHub operating model prepared in `setup`, including project readiness, issue creation ability, and required labels or project fields.
- Keep the runbook documents in `docs/runbooks/` aligned with the actual deployment and test environments.
- Do not store production secrets in committed files.
- If the project uses a separate secret manager, document the reference location here.
