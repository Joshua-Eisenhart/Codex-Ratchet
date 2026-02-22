# INTERACTION_DENSITY v1

Purpose: define doctrine for interaction-backed admissibility pressure in semantic ratcheting.

This document is doctrine-only.
It does NOT alter `SIM_EVIDENCE_v1` structure.
It does NOT alter promotion implementation.
It does NOT modify kernel behavior.

## Doctrine

- Every new `SPEC_HYP` must participate in at least one non-trivial SIM interaction.
- Graveyard entries must correspond to SIM falsification, not narrative-only rejection.
- Promotion review should consider interaction density as a required evidence quality dimension.

## Non-Modification Clause

- No new SIM primitives are introduced.
- No new ZIP types or container types are introduced.
- Existing transport and enforcement schemas remain unchanged.
