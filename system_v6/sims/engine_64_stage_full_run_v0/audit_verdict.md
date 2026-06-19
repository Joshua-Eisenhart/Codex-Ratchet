Independent audit verdict - fresh audit, read-only except this file.

Bottom line: VERDICT: GENUINE-WITH-CAVEATS.

The packet genuinely executes a realization-relative finite 64-slot schedule trajectory and the envelope completion preserves the original result values. The earned claim is narrow: `scratch_diagnostic` / `promotion_allowed=false` / `formal_admission_allowed=false`; realization-relative schedule trajectory only. It is not source admission for the substage convention, not slot-semantics admission for axis5, not an I Ching or hexagram match, not a basin/subbasin/64-subsubbasin result, not axis/QIT/bridge/physics evidence, and not canonical admission.

Freshness tier: `TIER-2` under `system_v6/receipts/audit_standards_codex_v1.md`: result JSONs and source were available, no prior `audit_verdict.md` existed or was read, and the decisive values below were recomputed from source before writing this verdict.

## Commands Rerun Fresh

To preserve the live repo read-only boundary, the full declared command sequence was rerun in a scratch clone under `/tmp/engine64_fullrerun.ZcV6hC/Codex-Ratchet`:

```bash
/opt/homebrew/bin/julia --startup-file=no system_v6/sims/engine_64_stage_full_run_v0/engine_64_stage_full_run_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_64_stage_full_run_v0/engine_64_stage_full_run_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_64_stage_full_run_v0/engine_64_stage_full_run_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_64_stage_full_run_v0/engine_64_stage_full_run_v0_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/engine_64_stage_full_run_v0/results/engine_64_stage_full_run_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_64_stage_full_run_v0/validate_engine_64_stage_full_run_v0.py
```

All six commands returned `ok:true`; the packet validator returned `errors: []`.

Important post-audit caveat: the packet-local validator still contains a builder-era hard absence check for `audit_verdict.md` in `validate_required_files`. The validator was therefore rerun in scratch before this legitimate independent audit file existed. The shared boundary helper is post-audit-idempotent when the header declares independent/fresh audit status, but this packet-local absence check should be repaired in a later validator-maintenance change.

## Recomputed Load-Bearing Values

Source used for recomputation:

- `system_v6/sims/engine_64_stage_full_run_v0/engine_64_stage_full_run_v0_common.py`
- `system_v6/sims/engine_64_stage_full_run_v0/results/engine_64_stage_full_run_v0_results.json`
- `system_v6/sims/engine_64_stage_full_run_v0/results/engine_64_stage_full_run_v0_envelope_results.json`

Fresh recomputation from source, not from builder prose:

| Check | Recomputed value | Live result value | Verdict |
|---|---:|---:|---|
| total schedule slots | 64 | 64 | pass |
| Type1-L slots | 32 | 32 | pass |
| Type2-R slots | 32 | 32 | pass |
| unique coordinate rows | 64 | 64 | pass |
| bad coordinate rows | 0 | 0 | pass |
| full trajectory rows with `state_before`, `state_mid`, `state_after` | 64 | 64 trajectory rows | pass |
| L-vs-R final_state_l2 | 0.1856033825938027 | 0.185603382593803 | pass |

The L-vs-R recomputation used the same pinned initial state and independently ran each half-schedule from that same state. Recomputed final states:

- Type1-L: `[0.065236827231741, 0.051497326527878, 0.048944562774595]`
- Type2-R: `[0.031491298648636, -0.088771147068158, -0.067822771039047]`

The "64 slots" earned here is 64 total schedule slots, split 32 Type1-L and 32 Type2-R. Do not cite this as 64 slots per family.

## Slot-Coordinate Consistency

Fresh recomputation found 64 coordinate-consistency rows and 0 bad rows. Sample rows were recomputed directly:

| Slot | Axis bits | Expected/actual operator | Expected/actual stage | Expected/actual terrain | Expected/actual precedence | Verdict |
|---:|---|---|---|---|---|---|
| 0 | `(0,0,0,0,0,0)` | `Ti` / `Ti` | `Se` / `Se` | `Se/Funnel` / `Se/Funnel` | `operator_first` / `operator_first` | pass |
| 17 | `(0,0,0,1,0,1)` | `Ti` / `Ti` | `Si` / `Si` | `Si/Hill` / `Si/Hill` | `terrain_first` / `terrain_first` | pass |
| 42 | `(1,0,1,0,1,0)` | `Fi` / `Fi` | `Ni` / `Ni` | `Ni/Source` / `Ni/Source` | `operator_first` / `operator_first` | pass |
| 63 | `(1,1,1,1,1,1)` | `Fe` / `Fe` | `Se` / `Se` | `Se/Cannon` / `Se/Cannon` | `terrain_first` / `terrain_first` | pass |

This consistency check is an internal realization-coordinate check. It does not admit source semantics for axis5 or the unpinned substage convention.

## Controls And Solver Flips

The controls fire for real computed reasons:

| Control | Fresh recompute | Why it fires |
|---|---:|---|
| shuffled schedule | final_state_l2_vs_full `0.0772917840835821`; same matrix-index multiset true; order identical false; signature equal false | same slots in a different order give a different trajectory/final state, so the maps are order-sensitive under this realization |
| truncated-32 boundary | slot_count `32`; axis3 values `[0]`; final_state_l2_vs_full `0.1853587271703458` | the one-family Type1-L 32-slot boundary is not the full 64-slot trajectory |
| bit-coordinate erasure | unique coordinates collapse to 2; final_state_l2_vs_full `0.04841443683042904`; signature equal false | erasing axis1/axis2/axis4/axis5/axis6 leaves only axis3 and changes the realized trajectory |

The SMT crossover fields are also can-fail in the required polarity:

- `z3`: negated full-run gate `unsat`; erased-coordinate control `sat`.
- `cvc5`: negated full-run gate `unsat`; erased-coordinate control `sat`.

## Envelope Completion

The envelope is a schema/envelope completion, not a result rewrite. Fresh comparison of envelope subtrees against the original result JSON found unchanged values for:

- `allowed_claims`
- `disallowed_claims`
- `coordinate_consistency`
- `type1_l_vs_type2_r_comparison`
- `controls`
- `gate_values`
- `crossover_proofs`

`result_values_unchanged=true` is supported by that direct subtree equality check. The envelope `base_result_sha256` also matches the live original result JSON.

The envelope honestly declares `mode=julia_canon_plus_jax_diagnostic_pytorch_omitted`. Julia and JAX lanes execute and validate; PyTorch is omitted with an explicit boundary because this packet makes no tensor/autograd/graph PyTorch claim path. Do not cite it as a full three-backend PyTorch-bearing sim.

## Hash Pins

Hash-pin checks passed for the live estate:

- runner source hash matches `engine_64_stage_full_run_v0.py`;
- common source hash matches `engine_64_stage_full_run_v0_common.py`;
- envelope source hash matches `engine_64_stage_full_run_v0_envelope.py`;
- envelope `base_result_sha256` matches `engine_64_stage_full_run_v0_results.json`;
- envelope stability pairs match the live base, Julia-lane, and JAX-lane result JSONs;
- parent source locks exist and hash-match for `matrix64_mine`, `two_engine_readout_automaton`, `substage_transition_convention_mining`, `eng_64_julia_source`, and `eng_64_julia_result`.

## Circularity Species Check

| Species | Finding |
|---|---|
| frozen-factor echo | Not found as a claim-bearing defect. The packet does not cite frozen complementary-factor counts as moving subbasins and explicitly disallows 64-subsubbasin/basin claims. |
| definitional circularity | Present only as bounded schedule-completeness structure: 64 coordinate slots are built by the declared finite schedule. This is acceptable only because the claim is schedule execution, while state evolution, L/R distance, controls, and solver flips are computed and can fail. |
| rule-table readback | Not found for the state-evolution/control claims. Coordinate rows read the declared realization map, so cite them only as internal coordinate consistency, not as external invariant/source semantics. |
| post-hoc statistic | Not found. No statistical target set or significance row is used. |
| shift-relabeling | Not found. Type1-L and Type2-R are distinct schedule realizations with different final states; calibration/control rows are not relabeled as target evidence. |
| structure-by-symmetry | Not found as a promoted structure claim. The packet does not elevate symmetry/product/orbit structure into basin/subbasin evidence; those consumers are explicitly blocked. |

## What This Earns

This is a disciplined path item 2 milestone candidate in the narrow sense: a complete, hash-pinned, realization-relative Type1-L then Type2-R Matrix64 schedule run exists, executes real state evolution across 64 total slots, emits per-slot coordinate/state ledger rows, computes an L-vs-R chirality-sensitive final-state difference, and carries firing controls plus green scratch rerun validators.

Accepted status label: `passes local rerun` in scratch for the declared command sequence, with classification still `scratch_diagnostic`.

## What This Does Not Earn

It does not earn:

- source admission of the v2/v3 cyclic substage convention;
- axis5 or slot-semantics doctrine claims;
- I Ching, hexagram, or match-lane claims;
- basin, subbasin, 64-subsubbasin, attractor, or terminal-core claims;
- canonical Matrix64 admission;
- QIT, bridge, axis, physics, or manifold admission;
- PyTorch-bearing three-engine evidence;
- downstream claim promotion beyond the stated scratch diagnostic ceiling.

## Citation Rule

Cite this packet only as:

> `engine_64_stage_full_run_v0`: GENUINE-WITH-CAVEATS, `scratch_diagnostic`, realization-relative finite Matrix64 schedule trajectory; 64 total slots = 32 Type1-L + 32 Type2-R; L-vs-R final_state_l2 `0.185603382593803`; controls fire; envelope values unchanged; no source-admitted substage convention, no axis5 slot-semantics claim, no match-lane claim, no basin/subbasin/64-subsubbasin claim, no axis/QIT/bridge/physics/manifold admission.

