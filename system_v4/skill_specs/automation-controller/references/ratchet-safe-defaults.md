# Ratchet-Safe Defaults

## Hard defaults

- archive-first, not delete-first
- quarantine-first for unattended `Pro` returns
- no direct unattended writes into active `A2` / `A1`
- one bounded loop per automation
- explicit stop rule required
- emit a user-visible summary or inbox item
- fail closed on ambiguity

## Strong default deny zones

- `system_v3/specs/`
- `system_v3/a2_state/`
- `system_v3/a1_state/`
- `system_v3/tools/`
- `system_v3/runtime/`
- live ZIP template/dropin paths

## Preferred unattended work

- return audits
- queue checks
- monitoring
- safe maintenance
- packet prep
- controller summaries

## Poor automation fits

- destructive cleanup
- broad unfenced refinery
- direct doctrine promotion
- direct active-memory mutation
- vague open-ended “keep going” loops

