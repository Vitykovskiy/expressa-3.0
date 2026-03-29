# Integrations

## GitHub Project

- URL: `https://github.com/users/Vitykovskiy/projects/24`
- Board type: `Kanban`
- Required statuses present: `yes`
- Required fields present: `Status`, `Task Type`, `Owner Contour`, `Priority`
- Project item creation verified: `yes`
- Setup validation status: `complete`
- Notes: Project 24 is linked to `Vitykovskiy/expressa-3.0`. `Status` options were updated to `Inbox`, `Ready`, `In Progress`, `Blocked`, `Waiting for Testing`, `Testing`, `Waiting for Fix`, `In Review`, and `Done`.

## GitHub Issues

- Initiative issue creation verified: `yes`
- Initial seeded `business_analysis` issue verified: `yes`
- Operational issue templates verified: `yes`
- Required task metadata captured by forms: `yes`
- Ready -> In Progress claim/start flow verified: `yes`
- Labels prepared for workflow use: `yes`
- Notes: Seeded issues are `#1` (`initiative`, `Inbox`) and `#2` (`business_analysis`, `Ready`). Workflow labels created: `priority: high`, `priority: medium`, `priority: low`.

## Effective Workflow Policy

- Effective `.ai-dev-template.config.json` committed and pushed: `yes`
- Notes: Repo-local `.ai-dev-template.config.json` is authoritative for this repository. `pull_requests.enabled = false`, so delivery uses commit + direct push.

## Bootstrap Access Variables

These variables describe the raw VPS access that DevOps receives at Stage 0. They are inputs, not published app credentials.

| Variable | Required | Purpose | Stage first needed | Status |
| --- | --- | --- | --- | --- |
| `VPS_HOST` | yes | Raw VPS host or IP for Stage 0 bootstrap | `setup` | configured locally in `.env` |
| `VPS_USER` | yes | Raw VPS login user for Stage 0 bootstrap | `setup` | configured locally in `.env` |
| `VPS_PORT` | no | SSH port for Stage 0 bootstrap | `setup` | 22 |
| `VPS_PASSWORD` | one of | Password auth for Stage 0 bootstrap | `setup` | configured locally in `.env` |
| `VPS_SSH_PRIVATE_KEY_PATH` | one of | Local path to SSH private key for Stage 0 bootstrap | `setup` | empty in `.env` |
| `VPS_SSH_PRIVATE_KEY` | one of | Secret-backed SSH key material for Stage 0 bootstrap | `setup` | empty in `.env` |

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

- GitHub repository access: `yes`
- GitHub Project access: `yes`
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
