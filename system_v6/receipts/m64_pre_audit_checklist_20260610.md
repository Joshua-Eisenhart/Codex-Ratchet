# Adversarial pre-audit checklist: terrain_operator_precedence_64_matrix

Status: outcome-blind checklist authored before reading any `terrain_operator_precedence_64_matrix/results/*.json`.

Scope: audit the future `system_v6/sims/terrain_operator_precedence_64_matrix/` build against `/tmp/m64_build_card_20260610.md` and cited source surfaces. The checklist is not an outcome, not a verdict, and not evidence that the matrix ran.

Hard read rule: audit may read build cards, source files, source-locked packet code, validators, and non-result receipts. Do not read `terrain_operator_precedence_64_matrix/results/*.json` while authoring or modifying this checklist.

Standing ceiling: `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`. The 64 lattice remains a structural scaffold/proposal unless later diagnostic evidence supports a narrower claim. No "decoded", canonical, admitted, axis-level, runtime-64, engine-closure, IGT, or physics claim may pass from this packet.

## Sources locked for this checklist

- `/tmp/m64_build_card_20260610.md`: build target, G1-G8, controls, engines, ceiling.
- `system_v6/receipts/matrix64_mine_20260610.md`: four parallel 64 constructions, D1 matrix target, D2 fingerprint ladder, boundary against `eng_64_hexagram`.
- `system_v6/receipts/terrain_operator_map_20260609.md`: operator/terrain source map, Axis-6 precedence definition, sparse existing status, Axis4/Axis6 separation.
- `system_v5/READ ONLY Reference Docs/operator math explicit.md`: four intrinsic operator families only; `UP/DOWN` only composition order after a terrain map is chosen.
- `system_v5/READ ONLY Reference Docs/terrain math.md`: eight terrain generators and 16 placements.
- `system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md`: 16-placement structural lock.
- `system_v6/sims/source_locked_operator_base_packet/source_locked_operator_base_packet_jax.py`: source-locked operator implementation, pins, citations, solver shape.
- `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py`: source-locked terrain implementation, line hashes, pins, terrain channel definitions.
- `system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md` and `system_v6/receipts/mct_blind_expected_20260610.md`: control and scale-anchor pattern for order-gap expectations.
- `system_v5/READ ONLY Reference Docs/TAIJITU_PROBE_RECONCILIATION_CARD copy.md:16`: 64-slot scaffold fence.

## Minimum manual recomputation packet

The future audit must include these four recomputations before accepting any emitted verdict.

1. Commuting cell, distinct operations: recompute one `Hill` terrain with `Ti` operator row from source-locked forms, not from labels. In the current terrain packet, `Hill` is a Z-axis channel: Z Hamiltonian plus Z projective dephasing. `Ti` is Z-basis dephasing with Bloch action `(x,y,z) -> ((1-q1)x,(1-q1)y,z)`. A finite Z channel has transverse action `(x,y,z) -> (a x - b y, b x + a y, z)` for source-pinned `a,b`. Since scalar transverse contraction commutes with Z rotation/dephasing, both orders must match for all pinned states: `Phi_Hill(Ti(rho)) == Ti(Phi_Hill(rho))` within `FP_TOL`. This is a valid commuting control only if `Hill` and `Ti` are distinct operations and both source lineages are cited.
2. Noncommuting cell, distinct operations: recompute one `Hill` terrain with `Fi` operator row. `Fi` at the source pin is X rotation with Bloch action `(x,y,z) -> (x, -z, y)` for `theta=pi/2`. With the same Z terrain channel `(x,y,z) -> (a x - b y, b x + a y, z)`, the two orders give:
   - `Phi_Hill(Fi(r)) = (a*x + b*z, b*x - a*z, y)`
   - `Fi(Phi_Hill(r)) = (a*x - b*y, -z, b*x + a*y)`
   - `Delta = (b*(z+y), b*x + z*(1-a), y - b*x - a*y)`.
   For a pinned nondegenerate state not on an invariant axis, this must be nonzero. If the chosen pinned state or parameters make it zero, the audit must require a generic-state sweep row that separates it or mark the control underinstrumented.
3. Ladder rung class count: recompute `F0_address` as enumeration only: `8 terrain_id * 8 signed_operator_id = 64` address classes. This count cannot be used as behavior distinctness. Any `n_distinct=64` statement that relies on `F0_address` fails.
4. SMT flip: recompute one solver check from computed entries. For the noncommuting cell above, z3 and cvc5 must receive values derived from the computed `Delta` entries and prove `Delta = 0` is UNSAT under the real row. The symmetrized/erased-precedence control must flip to SAT. If either solver uses hardcoded literals, copies the same encoding without an independent build path, or lacks the SAT flip, SMT is decorative and fails.

## Checklist format

Each item must be filled as:

```text
open:
recompute:
fail-condition:
evidence-field:
source-citation:
```

`open` names the risk. `recompute` names the direct check the auditor performs. `fail-condition` is the kill criterion. `evidence-field` is the exact future result field or source field that must carry the value. `source-citation` must cite the source or code line range used.

## 1. Label matrix attack

open: The 64 rows may be label products, with behavior columns copied from `(terrain_id, signed_operator_id)` rather than computed channel applications.

recompute: Count exactly 64 chart rows and verify each row has both ordered outputs, `Delta_{T,O}` matrix, norms, entropy/purity deltas, and observables computed from source-locked `Phi_T(O(rho))` and `O(Phi_T(rho))`. Perform the two manual cell recomputations above: one commuting (`Hill`, `Ti`) and one noncommuting (`Hill`, `Fi`) unless the build declares a better source-justified distinct pair.

fail-condition: Any row lacks computed ordered outputs; behavior columns are derivable from address labels alone; the commuting row is a self-pair; the noncommuting row has no generic-state rescue when the pinned state is degenerate; or the manual recomputation disagrees without a named source/pin change.

evidence-field: `rows[*].ordered_outputs`, `rows[*].delta_matrix`, `rows[*].delta_norms`, `controls.commuting_pair_zero`, `controls.noncommuting_pair_nonzero`, `pin_spec`.

source-citation: `/tmp/m64_build_card_20260610.md` G1/G3; `matrix64_mine_20260610.md` D1; `terrain_operator_map_20260609.md:36-39,108-140`; operator and terrain source-locked packet code.

## 2. Chart/runtime conflation attack

open: The result may imply this chart matrix settles the existing `eng_64_hexagram` `n_distinct=16` question or achieves 64 runtime states.

recompute: Inspect boundary fields and prose for four separate 64 constructions: chart matrix, runtime hexagram/channel-fingerprint 64, live runtime 64, and two-engine constrained-placement 64. Confirm the result says the chart object is related but different from the existing `eng_64_hexagram` runtime object.

fail-condition: Any field says or implies "achieves 64 runtime states", "settles `eng_64_hexagram`", "runtime decoded", "n_distinct=64" without `under named Fk`, or collapses the four-construction table into one object.

evidence-field: `boundary_statement`, `related_prior_evidence`, `four_construction_boundary`, `claim_ceiling`.

source-citation: `/tmp/m64_build_card_20260610.md` G7; `matrix64_mine_20260610.md` A5/B; `TAIJITU_PROBE_RECONCILIATION_CARD copy.md:16`.

## 3. Fingerprint theater attack

open: The fingerprint ladder may be decorative, with rungs that co-classify identically, a tolerance chosen to manufacture/hide distinctness, or `F0_address` leaking into behavior claims.

recompute: For every `F0` through `F8`, recompute `n_distinct(Fk)`, class map, largest class, differing in-class fields, `recovered_over_16`, and `invariant_collapse_under_all_F`. Compare `F2_order_pair` against `F3_delta`; if they always co-classify, require explanation because `F3` should be a derived witness, not a new independent signal. Run tolerance sweep around `FP_TOL` and compare cliff scale to blind order-gap anchors: commuting same-axis controls near zero, noncommuting pairs above tolerance by a stable margin.

fail-condition: `F0_address` appears in behavior distinctness; `FP_TOL` cliff alone creates the advertised distinctness; `F2` and `F3` are treated as independent despite exact co-classification; `n_distinct` changes by tolerance gaming without a physical/numerical scale reason; or missing sweep rows are backfilled by prose.

evidence-field: `fingerprint_ladder`, `fp_tol`, `tolerance_sweep`, `controls.trivial_fingerprint`, `controls.label_shuffle`, `controls.commuting_pair_zero`.

source-citation: `/tmp/m64_build_card_20260610.md` G8/Controls; `matrix64_mine_20260610.md` D2; `mct_blind_expected_20260610.md` order-gap predictions.

## 4. Classification gaming attack

open: Collapse verdicts may be assigned without the named computed evidence, with `intended_degeneracy_candidate` used as a dumping ground.

recompute: For each collapsed class, require a row-by-row ledger: which `Fk` collapsed it, which stronger `Fk` split it if any, which controls survived, and which computed fields justify the class. Test every `intended_degeneracy_candidate` against all admitted `Fk` plus commuting, erased-precedence, label-shuffle, tolerance-sweep, spinor/sheet/loop, trajectory, and Axis4/Axis6 controls.

fail-condition: A verdict lacks a cited computed field; `probe_coarseness` is assigned without a stronger `Fk` split; `commuting_degeneracy` lacks distinct-operation commute evidence; `definition_alias` hides an address/spec collision without source lock; `intended_degeneracy_candidate` has not survived all admitted `Fk` and controls; or `bug_or_underinstrumented` is softened into a positive result.

evidence-field: `collapse_classifications`, `class_map`, `intra_class_differing_fields`, `invariant_collapse_under_all_F`, `controls`.

source-citation: `/tmp/m64_build_card_20260610.md` G2/G8; `matrix64_mine_20260610.md` C/D2; `lego-sim-classifier` ceiling discipline.

## 5. Control circularity attack

open: The commuting control may be a self-pair, and the erased-precedence control may only drop a label without recomputing anything.

recompute: Confirm the commuting control uses two distinct operations with independent source formulas. Confirm erased-precedence recomputes a one-order/symmetrized object and shows signed pairs merge under `F2/F3` because the precedence computation was removed, not because labels were hidden.

fail-condition: Commuting control compares an operation to itself; identity parameters make all rows commute; erased-precedence removes `+/-` labels while keeping both ordered outputs; or signed-pair merge is asserted without recomputed class maps.

evidence-field: `controls.commuting_pair_zero`, `controls.erased_precedence_merge`, `erased_precedence_class_map`, `control_pin_spec`.

source-citation: `/tmp/m64_build_card_20260610.md` G3/G4; `terrain_operator_map_20260609.md` D; operator exact-lock source.

## 6. Decorative SMT attack

open: Solver rows may be hardcoded, reuse a single encoding across z3/cvc5, or omit the required SAT flip.

recompute: Trace z3 and cvc5 inputs back to computed matrix entries or symbolic expressions derived from source-locked row computations. Confirm z3 and cvc5 are constructed separately enough to catch encoding drift. Run the noncommuting UNSAT and symmetrized/erased SAT flip.

fail-condition: Delta entries are literals typed into SMT code; z3 and cvc5 share one serialized formula without independent construction; only one solver runs; the noncommuting row lacks UNSAT for `Delta=0`; the erased/symmetrized control lacks SAT; or solver output is only schema decoration.

evidence-field: `smt.z3`, `smt.cvc5`, `smt.inputs_from_computed_delta`, `smt.symmetrized_control`, `tool_manifest`, `tool_integration_depth`.

source-citation: `/tmp/m64_build_card_20260610.md` G6; source-locked operator/terrain packets' z3/cvc5 patterns.

## 7. Reuse honesty attack

open: Terrain/operator forms may be re-derived ad hoc, with only source-looking labels or stale hashes; carrier rows may not come from the committed M(C,t) table.

recompute: Verify imports, shared functions, or byte/lineage hashes for the terrain generator packet and source-locked operator base packet. Verify `pin_block_sha256` and carrier row references against `mct_dynamic_admissibility_packet_v0` without promoting to nested/rung maps. Reject any new hand-written substitute unless it is explicitly a quoted copy with hash equivalence.

fail-condition: Missing lineage hash; source citations present but implementation differs; terrain/operator formulas are reimplemented without source-lock freshness checks; carrier support is invented or only label-sampled; or the result promotes carrier reuse into rung/nested geometry claims.

evidence-field: `source_lineage`, `operator_lineage`, `terrain_lineage`, `pin_block_sha256`, `carrier_rows`, `reads_peer_result`.

source-citation: `/tmp/m64_build_card_20260610.md` read-first item 5/6; `terrain_generator_sheet_packet_jax.py` source-lock hashes; `source_locked_operator_base_packet_jax.py` source citations; `mct_dynamic_admissibility_packet_v0/build_card.md`.

## 8. Axis conflation attack

open: `F8_axis_orthogonality` may merge Axis-4 loop order and Axis-6 precedence because both use "order" language.

recompute: Require two independent variations: vary Axis-4 loop-order class with Axis-6 precedence fixed, then vary Axis-6 precedence with Axis-4 fixed. Confirm each moves its own observable without silently changing the other. Verify no field equates loop-order, clockwise/counterclockwise, pair-order, and terrain/operator precedence.

fail-condition: `F8` has only one variation; Axis-4 and Axis-6 are implemented as one label bit; loop-order language is used as precedence evidence; or the result says Axis-6 is earned from an Axis-4 loop-order split.

evidence-field: `fingerprint_ladder.F8_axis_orthogonality`, `axis4_fixed_axis6_varied`, `axis6_fixed_axis4_varied`, `axis_boundary`.

source-citation: `/tmp/m64_build_card_20260610.md` G5; `matrix64_mine_20260610.md` C/D2; `terrain_operator_map_20260609.md` addendum on three distinct polarities.

## 9. Standard checks

open: The envelope may pass by copy, NumPy may carry claim-bearing logic, or ceiling language may drift upward.

recompute: Check independent leg implementations for cross-leg parity-by-copy. Search for peer-result reads before local computation. Confirm NumPy is only control/baseline, not claim-bearing. Confirm `classification`, `promotion_allowed`, and `formal_admission_allowed` exactly match the build card in every leg and envelope. Search result prose and fields for `candidate`, `scaffold`, `proposal`, `decoded`, `canonical`, `admitted`, `runtime states`, and `64 achieved`.

fail-condition: JAX/PyTorch/Julia share copied result tables instead of independent computation; any leg reads peer JSON before computing; NumPy carries a nonclassical or QIT claim; ceiling fields are missing/drifted; "decoded" appears without diagnostic verdicts supporting the exact decoded object; or "64 achieved" is not qualified by a named fingerprint family.

evidence-field: `reads_peer_result`, `tool_manifest`, `tool_integration_depth`, `classification`, `promotion_allowed`, `formal_admission_allowed`, `claim_boundary`, `engine_parity`.

source-citation: `/tmp/m64_build_card_20260610.md` ceiling/Engines/Acceptance; `system_v6/README.md` evidence ladder; `TAIJITU_PROBE_RECONCILIATION_CARD copy.md:16`.

## Audit verdict rules

- `pass`: Only if all required fields exist, manual recomputations match, controls fire, solver flips are load-bearing, and ceiling language stays exact.
- `fail`: Any hard fail-condition above.
- `blocked`: Required evidence path is absent, source lineage cannot be verified, or a source/pin ambiguity prevents the manual recomputation.
- `underinstrumented`: The matrix runs but lacks the observables or controls needed to classify a collapse.

No single positive row can promote the object above `scratch_diagnostic`.
