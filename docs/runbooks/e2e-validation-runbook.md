# E2E Validation Runbook

## Environment

- Environment contract owner: DevOps
- Test environment URL: `http://216.57.105.133:8080`
- Login: `n/a for Stage 0 bootstrap`
- Password source: `n/a for Stage 0 bootstrap`
- Environment owner: `devops`
- Access prerequisites: public HTTP reachability to port `8080`

## Scope

- Primary scenarios:
  - Stage 0 infra landing page availability
  - proxied backend health contract
  - metadata contract with `DISABLE_TG_AUTH=true`
- Acceptance source:
  - `docs/analysis/cross-cutting-concerns.md`
  - `docs/analysis/version-scope-and-acceptance.md`
  - `scripts/infra/smoke.sh`
  - `scripts/infra/e2e.sh`
- Out-of-scope scenarios: customer ordering and backoffice operations feature flows; they belong to issues `#7-#12`

## Validation Flow

1. Confirm the DevOps-published environment contract exists and the live URL/access details are populated or mapped from the target secret source.
2. Run `bash scripts/infra/e2e.sh http://216.57.105.133:8080`.
3. If deeper diagnostics are needed, SSH to the VPS and run `bash scripts/infra/smoke.sh http://127.0.0.1:8080 http://127.0.0.1:8081`.
4. Collect the GitHub Actions run link, the target URL response, and any `docker compose ps/logs` evidence.
5. Record defects into the active infrastructure or deploy issue if the baseline environment is unavailable.

## Evidence

- Reports location: GitHub Actions logs for `Stage 0 CI` and `Deploy Staging`
- Screenshots or videos: optional, only if a public target check fails
- Logs or traces: `.agent-work/telemetry/20260329-225342.jsonl`, `docker compose logs`

## Defect Routing

- Defect tracker or issue path: issue `#4` until infrastructure closes, then issue `#13` for rollout defects, then relevant implementation issues for feature regressions
- Severity rule:
  - environment unreachable or compose unhealthy -> blocking
  - metadata mismatch in Stage 0 bootstrap -> blocking
  - cosmetic landing-page mismatch -> non-blocking for infrastructure
- Escalation owner: `devops`

## Exit Criteria

- Required pass threshold: all scripted Stage 0 checks pass
- Blocking defect rule: any failure in `/health`, `/api/health`, or `/api/meta` blocks the infrastructure handoff
- Sign-off evidence: successful CI run, successful deploy run, and successful public `scripts/infra/e2e.sh` output
