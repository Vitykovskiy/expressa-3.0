# E2E Validation Runbook

## Environment

- Environment contract owner: DevOps
- Test environment URL: `<published live URL from DevOps-managed contract>`
- Login: `<documented access detail from DevOps-managed contract>`
- Password source: `<documented access detail or secret source from DevOps-managed contract>`
- Environment owner: `<team or role>`
- Access prerequisites: `<accounts, VPN, seed data>`

## Scope

- Primary scenarios: `<scenario ids>`
- Acceptance source: `<artifact paths>`
- Out-of-scope scenarios: `<scenarios or none>`

## Validation Flow

1. Confirm the DevOps-published environment contract exists and the live URL/access details are populated or mapped from the target secret source.
2. `<execute scenario set>`
3. `<collect evidence>`
4. `<record defects or sign-off>`

## Evidence

- Reports location: `<path or link>`
- Screenshots or videos: `<path or link>`
- Logs or traces: `<path or link>`

## Defect Routing

- Defect tracker or issue path: `<where failures are recorded>`
- Severity rule: `<how to classify failures>`
- Escalation owner: `<team or role>`

## Exit Criteria

- Required pass threshold: `<threshold>`
- Blocking defect rule: `<rule>`
- Sign-off evidence: `<artifact>`
