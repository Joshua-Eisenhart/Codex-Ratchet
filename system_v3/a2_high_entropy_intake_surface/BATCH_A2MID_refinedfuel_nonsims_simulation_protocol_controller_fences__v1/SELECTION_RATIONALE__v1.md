# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_refinedfuel_nonsims_simulation_protocol_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why This Parent
- `BATCH_refinedfuel_nonsims_simulation_protocol_math_class__v1` was the strongest next refined-fuel controller follow-on on the action board after the thin state-language packet
- its value is sharply controller-facing:
  - admit simulation/protocol artifacts only as explicit replay bookkeeping
  - block kernel gating, hidden runtime state, silent repair, correctness verdict drift, and summary-over-tape authority
  - keep manifest, lineage, tape, diagnostics, cache, and export vocabulary subordinate to replay evidence instead of letting those vocabularies harden into doctrine

## Why This Reduction Goal
- bounded goal:
  - isolate controller-usable fences for anti-gating handling, explicit input and lineage handling, finite declared replay structure, non-binding failure/diagnostic handling, and loss-aware tape-grounded cache/summary/export control
- excluded for now:
  - promoting protocol status into kernel truth, validation, or admissibility gates
  - treating summaries, diagnostics, exports, or caches as substitutes for explicit tape-grounded replay

## Deferred Alternatives
- `BATCH_refinedfuel_nonsims_topology_contract_math_class__v1`
  - next refined-fuel follow-on after the simulation-protocol packet is now reduced
- `BATCH_sims_ultra3_full_geometry_stage16_axis0_orphan_family__v1`
  - strongest current sims follow-on still sitting in the immediate reduction tranche
