# Canonical State Schema (System Spec Pack v2)
Status: DRAFT / NONCANON
Date: 2026-02-20

## Canonical State (B-Owned)
Minimum structural fields:

- `axioms`
  - admitted `AXIOM_HYP` ids + raw lines

- `specs`
  - admitted `SPEC_HYP` ids, kinds, deps, raw lines
  - evidence tokens attached to specs (from SIM_EVIDENCE)
  - statuses (e.g., ACTIVE / PENDING_EVIDENCE / FAILED_SIM)

- `terms` (TERM_REGISTRY)
  - key: term literal
  - fields:
    - `spec_id` (TERM_DEF id)
    - `binds` (math def anchor)
    - `state` (permission state)
    - `required_evidence` (token required to transition to CANONICAL_ALLOWED)

- `survivor_order`
  - ordered admission history (noncommutation makes order meaningful)

- `graveyard`
  - rejected item records:
    - `id`
    - `reason`
    - `raw_lines`

- `parked`
  - parked item records (id + reason)

- `evidence_pending`
  - map: `spec_id -> {token}` required by that spec

## Term States (minimal intended)
- `TERM_PERMITTED`
  - admitted by TERM_DEF but does not unlock protected operations/glyphs

- `CANONICAL_ALLOWED`
  - term is allowed to authorize protected operations/glyphs
  - transition intended via:
    - `CANON_PERMIT` sets REQUIRED_EVIDENCE for a term
    - SIM_EVIDENCE delivers that evidence token

