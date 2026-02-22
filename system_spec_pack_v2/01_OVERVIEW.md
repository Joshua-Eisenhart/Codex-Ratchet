# Overview (System Spec Pack v2)
Status: DRAFT / NONCANON
Date: 2026-02-20

## What This System Is
- A **specification-driven staged constraint engine** with deterministic adjudication (B) and deterministic execution evidence (SIM).
- Not conventional code-first software: the primary objects are *artifacts*, *constraints*, *state exports*, and *evidence*.

## Purpose (structural)
- Ratchet a growing constraint surface while preserving:
  - finitude (`F01_FINITUDE`)
  - noncommutation (`N01_NONCOMMUTATION`)
- Make every admission auditable by:
  - explicit candidate artifacts
  - explicit rejections (graveyard)
  - explicit dynamic evidence (SIM_EVIDENCE)

## Non-Negotiables
- Root constraints must be present and never negotiated:
  - `F01_FINITUDE`
  - `N01_NONCOMMUTATION`

- "Ratcheted" is not "admitted as TERM_DEF".
  - Minimum intended bar for meaningful ratcheting:
    - alternatives exist (graveyard contains plausible failures)
    - positive sims exist and have run
    - negative sims exist and have run

- Doc surface must stay lean:
  - fixed file sets where possible
  - append + shard
  - avoid file-per-batch explosion
  - never modify `core_docs/`

