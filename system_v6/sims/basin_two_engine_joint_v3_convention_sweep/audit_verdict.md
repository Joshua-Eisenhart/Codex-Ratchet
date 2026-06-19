# Fresh Cross-Backend Audit Verdict - basin_two_engine_joint_v3_convention_sweep

Auditor: independent Codex audit of codex2 builder packet.
Scope: read-only audit except this verdict file. No `git add` or commit.
Wizard route truth: PARTIAL Max Assembly audit, with 3 Codex native parent lanes completed (`provenance`, `order/proof`, `backend/schema/anti-by-construction`) and no child subsubagents. Controller synthesis and file write remained serial.
Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

## Bottom Line

VERDICT: GENUINE-WITH-CAVEATS / CONVENTION-ROW-RELATIVE NEGATIVE.

The packet genuinely finds `primary_64_level_found=false` for all six realized rows and `source_valid_primary_64_level_count=0` across the rows it admits as B-sensitive. The decisive mechanical result is real: A and `D_matrix64_b_order_overlay` survive the B order-shuffle control and still do not produce 64; the C rows, `D_matrix64_direction_as_loop`, and `v2_cyclic_wrap_contrast` are order-blind in this packet and are correctly excluded from source-valid 64 evidence.

The hard caveat is provenance/family completeness. The mining receipt says A, C, and D underdetermine transition-law details. The builder enumerated some minimal subvariants, but not all quote-admissible possibilities. Therefore the strict re-registration exclusion clause fires only for the actually realized, B-tested admitted-row packet, not for every possible faithful convention-family subvariant.

Prediction-adjudication sentence:

`The pre-registered 64 = 2 engines x 2 loops x 4 stages x 4 substages prediction is unconfirmed and negatively adjudicated under the basin_two_engine_joint_v3_convention_sweep realized convention rows: no source-valid B-sensitive primary terminal/SCC row realizes 64; however, because the source quotes still underdetermine unenumerated B-sensitive A/C/D transition subvariants, this is convention-row-relative negative evidence, not a canonical disproof of the whole owner prediction family.`

Future-citation rule:

`Cite basin_two_engine_joint_v3_convention_sweep as scratch-diagnostic, convention-row-relative negative evidence: A_readout_transition_dwell and D_matrix64_b_order_overlay are B-sensitive source-valid realized rows with no primary 64; C_composition_outer_inner, C_composition_inner_outer, D_matrix64_direction_as_loop, and v2_cyclic_wrap_contrast are excluded as order-blind or contrast-only in this realization. Do not cite "C is source-invalid" or "D is source-invalid" at family level; cite "this C/D realization is order-blind under the B control." Do not cite the packet as a canonical disproof unless a later receipt proves the minimal A/C/D subvariant space is exhausted.`

## Adjudication

1. Provenance fidelity

- `A_readout_transition_dwell`: fair as one A realization, not exhaustive. The quote pins stage words, active-loop component readout, and readout periodicity; it does not pin the dwell law. The builder says so in `under_determined_detail`, but silently picked one dwell rule instead of enumerating the minimal A subfamily.
- `C_composition_outer_inner` and `C_composition_inner_outer`: fair thin renderings of the composition-first quote, and the explicit outer/inner versus reverse ambiguity was enumerated. They are not strawmen, but they are state-machine choices over a quote that mainly pins composition discipline, not a unique transition law.
- `D_matrix64_direction_as_loop` and `D_matrix64_b_order_overlay`: fair mapping attempts over a quote that explicitly leaves the Matrix64-to-owner-product mapping open. The overlay row is the stronger B-constrained D realization; the direction-as-loop row is a plausible but order-blind mapping, not an inherent D-family failure.
- `v2_cyclic_wrap_contrast`: fair contrast row only. It is not source-admitted and is properly fenced.

2. Order-blind exclusions

The order-shuffle control permutes the two B-pinned directed loop orders (`Se->Ne->Ni->Si` and `Se->Si->Ni->Ne`) to shuffled orders and recomputes the row terminal structure. The control has teeth: A changes under shuffle, and `D_matrix64_b_order_overlay` changes under shuffle. Rows that ignore the directed order stay unchanged and are excluded.

This proves:

- A and `D_matrix64_b_order_overlay` are real B-sensitive negative rows for 64.
- The two C rows, `D_matrix64_direction_as_loop`, and v2-cyclic are order-blind as implemented.

It does not prove:

- all faithful C realizations are inherently order-blind;
- all faithful D realizations are inherently order-blind;
- all possible A dwell/readout-transition variants have been exhausted.

3. Family-level finding

The realized admitted family contains no source-valid primary 64 row. The exact packet-level sentence is:

`Within the realized v3 convention sweep rows that pass the B order-sensitivity control, the 64 prediction is excluded: A_readout_transition_dwell has primary terminal counts {sync:28, l_only:32, r_only:32, async_lr_union:1, all_interleavings:1}; D_matrix64_b_order_overlay has {sync:24, l_only:32, r_only:32, async_lr_union:1, all_interleavings:1}; no source-valid primary row has terminal/SCC count 64.`

The sharper positive statement is per-engine, not joint-subsubbasin: the single-engine rows repeatedly expose 32 terminal classes under L-only and R-only modes, matching the per-engine carrier size `2 loops x 4 stages x 4 substages`. That is a real row-relative per-engine cycle/carrier structure with absent-exit proofs in the graph partition rows. It is not the owner's joint 64 product `2 engines x 2 loops x 4 stages x 4 substages`, and it is not a discovered 64-subsubbasin level.

Both readings must be carried forward:

- packet-negative reading: excluded across the actually realized B-sensitive rows;
- open-family reading: still open through unenumerated source-faithful, B-sensitive subvariants.

4. Anti-by-construction

The packet does not repeat the v0 state-identity error. The primary 64-relevant counts are terminal/SCC counts over generated transition graphs, not state addresses, marginal intersections, or imposed projections. The result has `all_observed_primary_64_levels=[]`.

The v1 replication row is fenced as `by_construction_baseline`, with `coarse_8x8_intersection_count=64` and `accepted_as_primary_evidence=false`. Dissipative merge controls produce 64 for variants but are fenced as added reset/glue controls and `accepted_as_primary_evidence=false`.

Caveat: the label-permutation control is weak. It records a label rename but recomputes the same graph rather than applying a genuinely permuted readout/transition mapping. This does not create the primary no-64 result, but future citations should not lean heavily on the label-freeness pass.

5. SMT, cross-engine, validators, schema

SMT is load-bearing for computed count identity at the packet level: z3 and cvc5 bind the measured primary terminal-count map, return UNSAT for the negated mismatch, and flip to SAT when one expected count is incremented. Julia/Z3 mirrors the count proof. Caveat: `erased_flip_verdict` is the same flipped expected-count control, not a separate erased-input proof; later audit prose should not overdescribe it.

Cross-engine agreement is real for the reported primary terminal counts and `source_valid_primary_64_level_count=0`. Independence scope is narrower than full lattice independence: Julia independently recomputes every convention-row terminal count with Graphs.jl/Z3.jl; JAX/PyTorch share the Python payload for full quotient/may-must lattice contents and add package-backed checks around graph/tensor/proof surfaces. This is enough for `GENUINE-WITH-CAVEATS`, not for a stronger three-independent-implementation claim.

Fresh validators run in this audit:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/basin_two_engine_joint_v3_convention_sweep/validate_basin_two_engine_joint_v3_convention_sweep.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/basin_two_engine_joint_v3_convention_sweep/results/basin_two_engine_joint_v3_convention_sweep_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/basin_two_engine_joint_v3_convention_sweep/results/basin_two_engine_joint_v3_convention_sweep_envelope_results.json
```

All returned `ok:true`. The envelope remains `schema_version=three_engine_sim_result_v1`; mode is a field, not a schema fork.

## Named Caveats

- C1 underenumerated A: A is a fair realization but not an exhausted minimal subvariant family.
- C2 C-family remains open: the implemented C rows are order-blind, but the C quote does not inherently require order-blindness.
- C3 D-family mapping remains open: `D_matrix64_b_order_overlay` is B-sensitive and negative for 64, while `D_matrix64_direction_as_loop` is order-blind; neither exhausts all possible D-to-owner-product mappings.
- C4 label-permutation control weak: label-freeness is not the load-bearing negative result.
- C5 proof wording: SMT flips are computed-count expected-value flips, not a separate erased-input proof.
- C6 backend independence: Julia is independently count-bearing; Python/JAX/PyTorch share the full lattice payload scope.

Accepted status label: `passes local rerun` for the validator/envelope checks above, with internal result ceiling `scratch_diagnostic`.
