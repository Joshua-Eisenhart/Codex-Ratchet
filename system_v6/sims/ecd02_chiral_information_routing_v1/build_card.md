# BUILD CARD - ecd02_chiral_information_routing_v1

## Boundary

Build in `system_v6/sims/ecd02_chiral_information_routing_v1/` only. No git add. No git commit. This packet is file-disjoint from `ecd02_chiral_information_routing_v0/`.

## Authority

- v0 death audit: `system_v6/sims/ecd02_chiral_information_routing_v0/audit_verdict.md`.
- ECD registry contract: `system_v6/receipts/engine_capability_differentiators_20260612.md`, `ECD.02`; Szilard baseline must fail computed and QIT candidate must pass computed, or the candidate dies.
- Alt-view receipt: `system_v6/receipts/altviews_capability_and_surface_miss_20260612.md`.
- Panel 9 blind alt-views: `system_v6/receipts/panel9_blind_altviews_wave_targets_20260612.md`.
- QCA v3 realized-unitary seed: `system_v6/sims/ring_checkerboard_qca_v3/`.

## Discovery Rule

The chirality witness must be discovered from computation over realized dynamics. It must not be declared from `signed_index`, `rule_id`, a chirality label, or endpoint-arrival proxy logic.

## Required Computed Rows

- Two-bit joint-state evolution with entropy reduction/increase comparison and final projective readout entropy.
- Equal-temperature direction-dependent information flux over the run.
- Real mutual-information rows: `I(source; left_readout)` and `I(source; right_readout)` from joint distributions over the dynamics.
- Strongest fair Szilard baseline search with the same alphabet and step budget, including unconstrained classical endpoint policies.
- Mirror control, scrambled-schedule control, and no-identity-leak check.
- Honest verdict either way: if strongest Szilard matches or exceeds the QIT separation, ECD.02 dies.

## Standard Contract

Emit `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, `claim_ceiling=capability_discriminator_only`, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, three engine lane results, envelope result, packet-local validator result, focused pytest coverage, and `builder_self_assessment.md`. The builder must not write `audit_verdict.md`.
