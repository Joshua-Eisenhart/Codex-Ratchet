# Fresh Audit Verdict: mct_dynamic_admissibility_packet_v0

Bottom line: VERDICT = GENUINE-WITH-CAVEATS. The packet contains real computed support, quotient, b0, sidecar, SMT, relation-readout, and cross-engine agreement evidence. It is not merely decorative or broken. It does have named semantic hardening gaps: the active sheet quotient uses a label-derived `P_chirality` row, the commuting control is a self-pair, G8 presentations are summary IDs rather than full tables, and some source/variant diff receipts required by the card are not emitted.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Per-Check Results

1. PASS - G1 support and spinor-density table: all three legs emit `support_size=384`; hand sample `L:eta0:phi0:chi1` recomputes norm 1.0 and rho `[[0.853553390593, 0+0.353553390593i], [0-0.353553390593i, 0.146446609407]]`, matching emitted rows. Evidence: `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:107`, `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json:901`.

2. FAIL - G1 PIN/source lock is present, but the explicit chart agreement/divergence receipt is not emitted as a named field. Evidence: build card requires agreement/divergence at `system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md:24`; PIN/ceiling are emitted at `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json:865`, but no chart-agreement field was found.

3. PASS - G2 two-sheet separation is computed somewhere, but the active `P_chirality` key itself is label-derived. Matched L/R rows have identical support numerics but all 192 matched L/R pairs differ in emitted `order_gap_noncommuting`; example Julia `L:eta0:phi0:chi0=0.09118202808462852` versus `R:eta0:phi0:chi0=0.10120073823301562`. Evidence: `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:137`, `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:203`.

4. PASS - G2/G3 b0 readout is present and non-promotional: hand recompute gives `b0=-1,0,+1` with 128 rows each across the packet and 64 rows each per sheet. Evidence: `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json:70`, `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json:822`.

5. PASS - G3 phi-blindness and phase split are real. Hand slice `sheet=L, eta=0, chi=0` collapses eight phi rows to one quotient class without `P_phase` and splits to eight classes with `P_phase`; all legs emit `q_without_phase=24`, `q_with_phase=192`. Evidence: `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:254`, `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json:897`.

6. PASS - Probe-family rows are emitted for all 384 support rows; `P_density`, `P_shell`, `P_phase`, `P_loop`, `P_order`, and `P_chirality` are present. Caveat: `P_chirality` is label-derived, adjudicated below. Evidence: `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:169`, `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:202`.

7. PASS - G7 SMT checks use computed rows and show the expected unsat/sat flips for density separation, phase injection, and row scrambling. Evidence: `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:290`, `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json:364`.

8. FAIL - G4 dynamics has a real nonzero order gap, but the commuting-control zero row is a self-pair and does not test a distinct commuting operator pair. Evidence: Julia `terrain_si_commuting = dephase_z` and `dephase_z` is compared with itself at `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:143`; same pattern appears in JAX and PyTorch at `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_jax.py:195` and `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_pytorch.py:262`.

9. PASS - G5 operation/readout sidecars are present: graph warping/reindexing/folding fields and the self-loop policy sidecar are emitted. Hand recompute of the `E3` sidecar gives erase policy `|E3|=4` and retain policy `|E3|=8`. Evidence: `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:398`, `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json:899`.

10. PASS - G6 relation-dependent readout is present and field-wide: full relation gives one weak component; ablated/product/local/null controls give 384 components. Evidence: `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_pytorch.py:565`, `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_julia_results.json:169`.

11. FAIL - G8 presentations are not realized as full flat/spherical/nested tables. The packet emits presentation IDs and common-value summaries only, so row-location equivalence across three concrete presentation tables is not demonstrated. Evidence: `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:457`, `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_julia_results.json:405`.

12. PASS - Engine independence and envelope agreement are present: legs report `reads_peer_result=false`, support hashes match, and common scalar divergence is at floating tolerance only. Recomputed max scalar divergence is `6.938893903907228e-17` on `max_order_gap_noncommuting`. Evidence: `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_envelope.py:66`, `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json:412`.

13. PASS - No NumPy-only claim path was found. The JAX leg uses `jax.numpy`, the PyTorch leg uses tensor operations and only converts to `.numpy()` for JSON serialization. Evidence: no `import numpy` hit in the packet sources; serialization conversion at `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_pytorch.py:156`.

14. FAIL - Control circularity is present for the commuting-control row: `dephase_z o dephase_z` is compared with itself, so that zero gap cannot fail. Other controls fire, but this named control is weak. Evidence: `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl:145`, `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_jax.py:203`, `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_pytorch.py:270`.

15. PASS - Status ceilings are correct and promotion language is fenced. The result states `classification=scratch_diagnostic`, `formal_admission_allowed=false`, and `promotion_allowed=false`; search hits for canonical/admitted-style terms are negative or ceiling text. Evidence: `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json:70`, `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json:822`, `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json:873`.

16. PASS - Envelope validator passes under the Makefile Python interpreter path recorded by preflight. Fresh command returned `{"ok": true, "result_json": "system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json"}`. Evidence: `/tmp/mct_preflight_20260610.md:5`, `scripts/validate_three_engine_sim_result.py` fresh run.

17. FAIL - Source provenance is mostly present, but the packet does not emit the build-card-required `literal_table_diff` and `non_isomorphic_diff` fields, and no explicit `Var_t`/variant ledger was found in result JSON. Evidence: requirement at `system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md:41`; no matching emitted fields found in `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/`.

## Adjudications

F1 - P_chirality label echo: sustained, but not fatal to the whole packet. All three legs set `P_chirality` directly from the sheet sign or chirality label, so the active 2x sheet factor in the quotient is label-derived. However, the Weyl sign also enters the dynamics, and every matched L/R row differs in emitted `order_gap_noncommuting`; therefore the sheet realization is not purely decorative. The named gap is narrower: the packet lacks a computed, binned, sheet-sensitive probe row to replace or corroborate the label-derived `P_chirality` quotient factor.

F2 - Blind P2 arithmetic error: the blind sheet is superseded by the crosscheck. Direct computation gives exactly four distinct values of `exp(2i chi_j)` on the 8-point grid, so exact density quotient is `3 shells x 4 off-diagonal phases = 12`. The build's decomposition is `q_without_phase=24 = 12 exact density classes x 2 P_chirality sheet rows`; `q_with_phase=192 = 12 exact density classes x 2 sheet rows x 8 P_phase bins`. Binning coarsens nothing for the emitted active keys. Phi-blindness itself is confirmed: rho is independent of phi, and the eight-row phi slice collapses/splits exactly as claimed.

F3 - Trivial commuting control: sustained. Julia, JAX, and PyTorch all compare a dephasing operation with itself for the zero-gap commuting control. No other emitted zero-gap row already constitutes a genuine distinct-pair commuting control. This is a named gap, not a reason to discard the nonzero noncommuting gap.

## Hand-Recomputed Values

- Phi-slice quotient: for `sheet=L, eta=0, chi=0`, eight phi rows collapse to one class without `P_phase`; the same eight rows split into eight classes with `P_phase=0..7`.
- Density quotient: `exp(2i chi_j)` has period 4, so exact density classes are `3 x 4 = 12`.
- Active quotient: `q_without_phase=24 = 12 exact density classes x 2 P_chirality rows`; `q_with_phase=192 = 12 x 2 x 8`.
- b0 row count: across 384 rows, `b0=-1` has 128 rows, `b0=0` has 128 rows, and `b0=+1` has 128 rows; per sheet, each has 64 rows.
- Sidecar `E3`: erase self-loops gives `|E3|=4`; retain self-loops gives `|E3|=8`.
- Cross-engine scalar tolerance: max recomputed divergence on common scalars is `6.938893903907228e-17`.

## Named Gaps

- Add a computed sheet-sensitive probe row. Keep current claim values byte-stable; add a new field that bins or records the sheet-sensitive dynamic difference already present in `order_gap_noncommuting`.
- Replace the self-pair commuting control with a distinct-pair commuting control, for example a source-locked `T_z` with `R_z` row, while preserving the existing control value as a legacy diagnostic if needed.
- Emit full G8 presentation tables or row-location receipts for flat, spherical, and nested presentations, not only presentation IDs and common-value summaries.
- Emit the build-card-required `literal_table_diff` and `non_isomorphic_diff` receipts as additive fields.
- Emit an explicit source/variant conflict ledger for `Var_t` and the ring-checkerboard source conflict, keeping the current PIN note intact.
- Add a validator rule that detects self-pair commuting controls and missing presentation/diff receipts; current validator shape does not catch these semantic gaps.

## Verdict

VERDICT: GENUINE-WITH-CAVEATS.

This packet is genuine as a `scratch_diagnostic`: it computes the support, quotient behavior, phi-blindness, b0 readout, sidecar policy split, relation-dependent readout, SMT checks, and cross-engine envelope agreement. The caveats are hardening gaps, not permission to change the existing claim values: `P_chirality` is label-derived, the commuting control is self-pair, presentations are not fully realized, and some source/diff receipts are missing.

Promotion remains blocked: `promotion_allowed=false`, `formal_admission_allowed=false`.

## Post-Hardening Re-Audit Addendum - 2026-06-10

Scope: focused re-audit of the five named hardening gaps only. I did not re-run the original 17-check audit. Ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`; this packet is only a first finite geometric support/probe/quotient packet.

### Gap Closure Verdicts

1. Original FAIL 2 / chart agreement: CLOSED. `chart_agreement_receipt` is now emitted in all three legs and summarized in the envelope. I checked the pinned chart against `Formal constraints and geometry.md:78-88`: both use `psi_s(phi,chi;eta)=(exp(i(phi+chi))*cos(eta), exp(i(phi-chi))*sin(eta))`, with `s in {L,R}`. Lines 157-166 define left and right torus charts with the same chart formula, so the receipt's note that sheet dynamics are carried separately by the Weyl-sign choice is truthful rather than a silent chart substitution.

2. Original FAIL 8 / computed sheet-sensitive row: CLOSED. The new computed row is `P_weyl_gap`, sourced from `order_gap_noncommuting`, and `q_without_phase_computed_sheet=24` recomputes from the key `P_density/P_shell/P_loop/P_order/P_weyl_gap`, not from `P_chirality`. Hand recompute for the pair `L:eta0:phi0:chi0` / `R:eta0:phi0:chi0` gives gaps `0.09118202808462847` and `0.10120073823301565`, delta `0.010018710148387178`; result rows report `0.09118202808462852` and `0.10120073823301562`. All 192 matched L/R pairs have a distinct dynamic gap.

3. Original FAIL 14 / commuting control circularity: CLOSED. The self-pair remains only as `legacy_self_pair_diagnostic`; the active distinct commuting control is `T_z_dephasing` with `R_z_z_rotation`. Hand recompute on `L:eta0:phi0:chi0` gives Frobenius gap `4.3885418357208765e-17`, matching the Julia row and within zero tolerance. The noncommuting flip partner remains nonzero (`max_gap` about `0.1135167896453421`), so the control can fail.

4. Original FAIL 11 / G8 presentations: CLOSED. Each leg now emits full row-location tables for `flat`, `spherical_shell`, and `nested_ring`, each with 384 rows. Agreement receipts cover support count, adjacency edge count, axis0 rows, quotient class count, and phi-blindness. Disagreement controls genuinely break agreement: shell nesting erasure collapses `[-1,0,1]` to `[0]`; flat erasure changes adjacency edges `1664 -> 1152`; fiber/ring erasure drops phase separations `1152 -> 0`.

5. Original FAIL 17 / source diffs and variant ledger: CLOSED. `literal_table_diff` and `non_isomorphic_diff` are computed in all three legs and surfaced in the envelope. The literal diff reports `left_class_count=24`, `right_class_count=192`, and `literal_keyset_diff_count=192`; the non-isomorphic diff reports class-count signatures `24` vs `192`, with `non_isomorphic_by_class_count=true`. `variant_ledger.Var_t` is present in all legs, with `nested_hopf_tori_finite_support` active and the 64-cell, engine-stage board, and pre-geometric grid lanes marked `inactive_out_of_scope`, not erased.

### Dispositions And Provenance

Disposition status is coherent. `pass_condition=non_isomorphic_diff` and `self_loop_policy_default=retain` both carry `disposition_status="derived_default_under_current_doctrine"` in the extended PIN and the superseding owner-pending receipt blocks. The provenance strings say `derived_default_under_current_doctrine` and explicitly say "Disposition, not owner lock"; I found no "doctrine forces" wording.

The N01 wording is the load-bearing-where-probes-preserve form: the self-loop provenance says "N01 makes order/history load-bearing where probes preserve it." The self-loop provenance cites `system_v6/receipts/mct_reconciled_spec_20260609.md`, which preserves fold/aggregation killed-information ledger discipline and reports the retain-side pushforward value `|E_3|=8`; it also cites `system_v6/receipts/shell_flow_radiated_information_mine_20260610.md`, which supports the owner correction as doctrine-level radiated-record/no-destruction framing while explicitly saying exact conservation/reconstruction math is not on file and not yet built. That provenance is honest.

### Lineage And Stale Surface

The base PIN remains byte-stable across Julia, JAX, and PyTorch: all three report `pin_block_sha256=f64f2c3624658fb522c8e5363ae2bb1a38b2a626d9da5e283ef05025a0e13161`, and recomputing the SHA256 from `pin_block_canonical_json` gives the same hash. `PIN_SPEC_EXTENDED.pin_extended_from.sha256` points back to that base hash with the lineage note "additive instrumentation plus derived defaults only; previous PIN retained as pin_block_sha256." The old `owner_pending` choice-point block is preserved as the frozen base PIN, while active extended/current fields carry the derived dispositions; the `owner_pending` receipt block is marked `superseded_by_choice_point_dispositions`.

I searched the sim folder for stale undecided-choice surfaces. Remaining `owner_pending` hits are in the frozen base PIN, build-card historical requirement text, replacement code that constructs the extended PIN, and superseded receipt blocks. The build card now carries the `DISPOSITIONS - 2026-06-10` addendum, so no active surface I found still implies the current choice points are undecided.

### Byte Stability And Validator

The audited claim values remain unchanged in the envelope: support `384`; `q_without_phase=24`; `q_with_phase=192`; sidecar `E3=4/8`; `max_order_gap_commuting=0.0`; `max_order_gap_noncommuting=0.10120073823301576`; solver flags `z3_density_unsat=1.0`, `cvc5_density_unsat=1.0`; relation components `full=1.0`, `ablated=384.0`. I directly recomputed the b0 distribution from the current probe rows as `-1:128, 0:128, +1:128`, and recomputed the computed-sheet quotient as 24 classes directly from the row table.

Fresh validator command:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json --require-pytorch
```

Result:

```json
{"ok": true, "result_json": "system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json"}
```

### Final Verdict

POST-HARDENING VERDICT: GENUINE-WITH-CAVEATS sustained with the five named hardening gaps closed. No upgrade beyond the original ceiling is granted. Remaining caveat: this is still a `scratch_diagnostic` first finite geometric support/probe/quotient packet, with `promotion_allowed=false` and `formal_admission_allowed=false`; it is not canonical, not formal admission, and not a manifold/axis/bridge/physics result.
