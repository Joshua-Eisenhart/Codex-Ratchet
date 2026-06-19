# Fresh validator sweep — dated red-list receipt (2026-06-13)

```yaml
receipt_kind: fresh_red_list
method: ran every system_v6/sims/*/validate_*.py fresh this turn; captured ok=false + first error
why: the stored red count DRIFTED between snapshots (Codex-app saw 8; stored JSONs said 2). Do not trust stored validator JSONs or prose. This is the fresh ground truth.
caveat: a fresh validator run may write validator_results.json (byproducts reverted after capture). Some validators rebuild; some only read.
```

## Confirmed red (real error), grouped by class

**A — builder/audit-boundary gate ("builder packet must not contain/create/write/emit audit_verdict.md")** (~11):
axis_triple_consistency_b6_v0, axis_triple_consistency_b6_v1, axis0_contender_heavy_v0, discrete_axes12_pair_v0, discrete_axis4_composition_v0, discrete_axis5_family_partial_v0, discrete_axis6_precedence_v0, ecd01_order_programmable_computer_v0, ecd02_chiral_information_routing_v1, fiber_augmented_cover_v0, root_randomness_entropy_discriminator_v0.
→ Fix: G.2a boundary discipline — the audit verdict must live in a separate audit lane, not inside the builder packet. Gate-discipline, NOT a math failure.

**B — source-hash / source-lock drift** (~8):
ecd03_typed_coratchet_v0, ecd04_record_conditioned_navigation_v0, ecd05_instruction_machine_v0, ecd06_prediction_first_inference_v0/v1/v2, ecd07_associative_retrieval_v0 (all "ecd_supplement_1 source hash drift"); topology_parity_guard_v3 ("source_complex_lock drifted").
→ Fix: restore the committed supplement/source OR re-pin (metadata-class, same as the 1Q registry H1). Owner-decision if it touches committed identity.

**C — packet-drift-against-source-rebuild (helper-output schema growth)** (~4):
gcm_5q_freeze_and_cuts_v0, gcm_constraint_carve_3q_v0, gcm_geometry_attach_2q_v0, gcm_nesting_tower_le2q_v0.
→ Fix: the proven helper-output-exclusion in the rebuild-compare (already applied to the freeze validators); NO math change.

**D — all_pass / candidate-death** (~2):
entropy_type_ratchet_v1, ring_checkerboard_automaton_v0 ("all_pass must be true").
→ Likely GENUINE NEGATIVE results (candidate died) mislabeled; fix = honest negative classification, not a green.

**E — audit-header-not-fresh** (~3):
entropy_type_ratchet_v2, gcm_nested_geometry_delta_4q_v0, ring_checkerboard_qca_v1 ("audit_verdict.md header does not declare an independent/fresh audit").
→ Fix: the audit header must declare independent/fresh audit (the stale-audit-supersession discipline).

**F — substrate_enforcement payload drift** (~2):
gcm_ring_checkerboard_runner_v0, gcm_ring_checkerboard_runner_v1.

**G — forbidden wording in audit_verdict.md** (~1):
basin_generating_set_sweep_v0 (forbidden words: fixture/toy/mock/dummy).

## Sweep-parse INDETERMINATE (ok=false but EMPTY error — likely parse noise; these are committed-green / builder-green; re-check individually before trusting)
axis0_amendment_light_sweep_v1, render_layer_readout_v0/v1, retrocausal_possibility_field_v0/v1/v2_contraction/v2_info_gradient/v2_irreversibility/v3, rpf_dual_chiral_engines_v0, rpf_outward_record_memory_v0.
→ Do NOT count as red without an individual recheck (the sweep's one-line JSON parse is unreliable when a validator prints extra lines or a different shape).

## Honest scope
~30 confirmed-red + ~11 indeterminate. The reds are DOMINATED by drift / gate-discipline classes (A,B,C,E,F,G = metadata/source-hash/audit-boundary/wording), NOT math failures; only class D (~2) is a genuine candidate-death needing honest negative reclassification. This is accumulated CLOSURE DEBT (Hermes' diagnosis), not broken math. 2Q/3Q FREEZE were red earlier this turn and are GREEN after the result-JSON restore (note: 3Q-freeze conflicting reports — recheck before any identity migration).

## Closeout order (per converged Hermes/Codex-app instruction)
1. This receipt (done).
2. Fix the drift/gate classes systematically (A: boundary; B: restore/re-pin source; C: helper-output-exclusion; D: honest negative; E: audit-header; F/G: payload/wording) — codex2-gated, NO math change, NO new packets.
3. Classify every untracked root COMMIT_READY/VOID/DEFER (codex2).
4. Add trackedness + stale-audit + audit-header gates.
5. Only then build the integrated GCM/QIT artifact on the M(C) spine.
