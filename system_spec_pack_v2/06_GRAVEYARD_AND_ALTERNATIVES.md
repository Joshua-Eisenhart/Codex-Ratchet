# Graveyard + Alternatives (System Spec Pack v2)
Status: DRAFT / NONCANON
Date: 2026-02-20

## Graveyard Role
- The graveyard is an audit surface:
  - what was tried
  - what failed
  - why it failed
- It is also a mining surface for future attempts (resurrection/reformulation).

## Minimum Graveyard Record
Every rejected item must carry:
- `id`
- `reason` (bootpack tag or kernel tag)
- `raw_lines` (verbatim item lines for replay)

## Alternatives Requirement (intent)
For a survivor to be considered "ratcheted" in a meaningful sense, there should exist:
- at least one plausible competing alternative that failed (in graveyard)
- the failure reason should be structurally informative (derived-only, undefined-term, schema fail, etc.)

## Graveyard vs Negative SIM (non-equivalence)
- Graveyard alternative:
  - explicit candidate/spec that was rejected/parked and recorded with reason + raw lines
- Negative sim:
  - adversarial execution artifact testing target failure modes or alternative invalidity

Both are required:
- graveyard alone is insufficient (no dynamic evidence)
- negative sim alone is insufficient (no explicit rejected alternative record)
