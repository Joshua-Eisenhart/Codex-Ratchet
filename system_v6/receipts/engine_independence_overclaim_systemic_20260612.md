# SYSTEMIC — "cross-engine consensus / independence" is structurally guaranteed on ~43 packets (2026-06-12)

```yaml
receipt_kind: systemic_overclaim_finding
severity: HIGH (framing, not math) — affects the engine-independence CLAIM across the estate, not the core results
method: Opus-orchestrated workflow (Opus orchestrators spawned codex1/codex2 + gemini via Bash) + a structural discriminator over all packets + controller route-truth
status: finding recorded; the FIX is a framing relabel at a single point, NOT a math change and NOT a mass-regenerate
```

## The smoking gun (controller-confirmed at source)

`gcm_constraint_carve_v1` (and the other diseased packets) ship in their envelope:
`"engine_consensus": {"independent": true}` and `"max_divergence": 0.0`.
`max_divergence ~ 0` is **guaranteed by construction**: JAX and PyTorch both call the shared Python
`common.build_packet()` (or an equivalent core-compute fn) and then only VERIFY properties of that one
payload — so their "agreement" on the core counts cannot diverge. Only an engine that INDEPENDENTLY
recomputes (Julia, in some packets) is a real second opinion.

## Quantified spread (structural discriminator: does each lane call a shared core-compute fn vs only consume constants + recompute natively?)

- **~43 CORE-SHARED (OVERCLAIM/MIXED):** JAX **and** PyTorch both call shared `common` core-compute -> mutual consensus is structural. Includes all `gcm_constraint_carve_*`, all `gcm_geometry_attach_*`, `gcm_2q_freeze_and_cut_v0`, `gcm_nesting_tower_le3q_v0`, `gcm_nested_geometry_delta_3q/4q_v0`, `gcm_runtime_flux_3q_v0/v1`, `gcm_connection_flux_attach_v0`, `manifold_dynamic_chart_*`, `ring_checkerboard_*`, and others.
- **~41 GENUINE:** shared `common` is scaffold/IO/constants only; each lane recomputes the core natively (`jnp`/`vmap`/own Julia). Confirmed GENUINE_INDEPENDENT on `gcm_nesting_tower_le2q_v0` (JAX own `compatibility_counts` via jnp, PyTorch via vmap, Julia own `tower_counts`; none call build_packet; counts flip under in-memory registry corruption).
- **Out of scope:** single-engine (e.g. `gcm_3q_freeze_and_cuts_v0` is numpy-only -> makes NO multi-engine claim -> not an overclaim).

## Per-packet nuances (do not collapse)

- `gcm_2q_freeze_and_cut_v0`: STRUCTURAL; Julia recomputes densities/metrics but copies 2 count fields from the Python packet.
- `gcm_runtime_flux_3q_v1`: STRUCTURAL + a DECORATIVE JAX/PyTorch L/R-opposition observable (passes on corrupted J_cut because `all_pass` never gates it).
- `gcm_geometry_attach_2q_v1`: MIXED — Julia IS independent (recomputes Bloch/Schmidt/negativity from upstream JSON); JAX/PyTorch verify; a decorative PyTorch `sympy_guard` (checks product+entangled==544, never `survivor_count==544` directly).
- z3/cvc5 proofs across these DO flip (real->UNSAT / erased->SAT) — genuine, NOT decorative — but they are **count-consistency vs hardcoded `EXPECTED_*` literals + partition identity**: genuine-but-narrow, not independent structural derivation.

## What STANDS vs what is FALSE

- STANDS: the core RESULTS (survivor/class counts, cut counts, geometry values) — mostly fine; recomputed where checked.
- FALSE / OVERCLAIMED: the **independence/consensus framing** shipped verbatim as `engine_consensus.independent=true` + `max_divergence=0.0` on the ~43 core-shared packets. "Three independent engines agree" is, on those packets, "one Python carve, cross-engine VERIFIED; only the independent lane (often Julia) is a second opinion."

## The fix (framing relabel, single point — NOT a mass-regenerate)

- The shared envelope builder `scripts/build_three_engine_envelope.py` is the single relabel point.
  Relabel honestly: `engine_consensus` -> distinguish INDEPENDENT-RECOMPUTE lanes from VERIFY-PAYLOAD lanes;
  `max_divergence` over verify-payload lanes is a tautological 0 and must be labeled "structural (shared payload), not an independence signal."
- Do NOT mass-regenerate the 43 committed envelopes (sha cascade, per the registry-drift lesson). Fix the
  builder going forward + this receipt documents the affected set; affected packets get the honest framing on next rebuild.
- Demote `gcm_substrate_check`/TOOL_INTEGRATION_DEPTH lines that imply 3 independent engines on the diseased packets.

## Relation to the rest of the campaign

Same disease family as the probe-relativity overclaim ([[probe_relativity_overclaim_correction_20260612]] — definition-sensitive readout sold as structure) and the decorative-z3 (geom-delta, demoted). The Wizard v4.3 verdict frames all of it: these are PROXY/ADAPTER artifacts, and the object's first-class fields remain un-instantiated (see `v43_object_card_current_run.json`). The blind cross-model lane (grok/gemini, no narrative investment) caught what 5 invested audits missed.
