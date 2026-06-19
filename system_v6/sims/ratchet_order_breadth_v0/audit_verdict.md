# Audit verdict: ratchet_order_breadth_v0

Auditor: codex1 cross-backend audit
Date: 2026-06-11
Scope: read-only audit of `system_v6/sims/ratchet_order_breadth_v0/` except this `audit_verdict.md`
Calibration: `system_v6/receipts/audit_bar_calibration_20260610.md`
Verdict: REJECT headline equivalence-class / k claim; KEEP enumeration and mortality evidence as bounded scratch diagnostics.

## Source quotes and artifact basis

- Builder ceiling: `ratchet_order_breadth_v0.py:2-5` says this is an "Exhaustive ratchet-order breadth diagnostic" and "Builder-only packet. Ceiling: scratch_diagnostic; promotion_allowed=false."
- Enumeration source: `ratchet_order_breadth_v0.py:303-305` constructs rows with `itertools.permutations(CONSTRAINTS)`.
- Claimed invariant object: `ratchet_order_breadth_v0.py:261-270` includes `class_id`, `effective_denominator`, `final_chart_volume`, `holonomy_spectrum`, `entropy_ledger`, `survival_sets`, and terrain gaps in `invariant_signature`.
- Classification source: `ratchet_order_breadth_v0.py:309-311` groups live rows by `row["class_id"]`, not by `class_signature_sha256` or the full invariant object.
- Validator gap: `validate_ratchet_order_breadth_v0.py:78-84` checks expected class labels/order lists/counts, but does not check that rows within one claimed class have identical committed invariants.
- The result itself states the risky premise at `results/ratchet_order_breadth_v0_envelope_results.json:1256`: `LZWT and ZLWT same class...`.
- Parent mortality source: `ratchet_deep_chain_v0_envelope_results.json` records the raw window mortality as quotient well-definedness/equivariance failure, with nonconstant Z4 membership and the condition that an extra section is not supplied by the committed quotient rule.

Repository state caveat: `git status --short` showed `?? system_v6/sims/ratchet_order_breadth_v0/` and `?? system_v6/sims/geo_s9_alternative_connections_v0/`. This packet is present on disk but not committed in this checkout at audit time.

## Q1 - Enumeration exhaustive

Status: PASS for on-disk enumeration.

Fresh recomputation, without writing result files:

```text
perm_count 24 row_count 24 unique_rows 24
missing []
extra []
summary {"distinct_live_outcomes": 2, "distinct_mortality_classes": 3, "live_orderings": 5, "mortality_orderings": 19, "orderings_total": 24, "total_equivalence_classes_including_mortality": 5}
```

The rows are all computed before table summarization: `order_table()` evaluates every `itertools.permutations(CONSTRAINTS)` member. I found no skipped or deduplicated ordering before computation.

## Q2 - Equivalence classes by committed invariants

Status: FAIL.

The advertised class grouping is by `class_id`; the committed invariant object includes the ordered `entropy_ledger`. Recomputing live row signatures gives five singleton live signatures, not two live invariant classes:

```text
live_by_full_signature_count 5
43ebe143...: ["LZWT"]
505afe3a...: ["LZTW"]
26e3a2c2...: ["LTZW"]
c846a96d...: ["ZLWT"]
0d01a6df...: ["ZLTW"]
```

Different claimed classes do differ as expected:

```text
("LZWT","LZTW") same_class_id False same_full_signature False
```

But same claimed classes are not identical under the packet's own full invariant object:

```text
("LZWT","ZLWT") same_class_id True same_full_signature False
("LZTW","LTZW") same_class_id True same_full_signature False
```

Concrete evidence:

- `LZWT` has class signature `43ebe143...` and an entropy ledger with `L` at step 1, `Z` at step 2, `W` at step 3, `T` at step 4.
- `ZLWT` has class signature `c846a96d...` and an entropy ledger with `Z` at step 1, `L` at step 2, `W` at step 3, `T` at step 4.
- `LZTW` has class signature `505afe3a...`; `LTZW` has `26e3a2c2...`; `ZLTW` has `0d01a6df...`.

Mortality point check passed for one named mortality class:

```text
LWZT -> M3_raw_window_then_Z4
mortality_point 3
mortality_constraint Z4_phase_lens
committed_class quotient_well_definedness_equivariance_failure
reason raw representative phase-window membership is not constant on the Z4 orbit
```

## Q3 - Anchors recovered

Status: MIXED.

Pass: the projection check for the four-step committed order is byte-exact:

```text
committed_order LZWT
ours_projected_sha256 32cbf26c68953ec144c3667e10073da262767ff996a93c49c19aa2f6a651ad81
parent_projected_sha256 32cbf26c68953ec144c3667e10073da262767ff996a93c49c19aa2f6a651ad81
byte_exact true
```

Named caveat: this is projection-only. The deep parent's full final denominator is 16 after the second Z2 row, while this four-constraint packet's final denominator is 8. The result labels the scope as `ratchet_deep_chain_v0 steps L,Z,W,T only; second Z2/operator/saturation rows intentionally erased`.

Pass with caveat: the known noncommuting pair recovers mortality:

```text
alive ordering LZWT -> O1_window_before_terrain
mortality ordering LWZT -> M3_raw_window_then_Z4
```

Fail under Q2 bar: the known commuting `L/Z` pair is same `class_id`, but not same full invariant object:

```text
LZWT signature 43ebe143...
ZLWT signature c846a96d...
same_full_signature False
```

If the intended equivalence relation deliberately quotients out zero-entropy leaf/Z step-order positions, that normalization is not encoded in the committed invariant classifier, validator, or result table.

## Q4 - Headline k and path-dependence reading

Status: FAIL for the published `k=2` class-count headline under the stated invariant bar.

The table traces the claimed counts:

```text
orderings_total 24
live_orderings 5
mortality_orderings 19
distinct_live_outcomes 2
distinct_mortality_classes 3
total_equivalence_classes_including_mortality 5
```

But when final objects are classified by the packet's committed invariant signature, the live count is 5 and total classes including mortality are 8:

```text
live full-invariant classes 5
mortality classes 3
total full-invariant classes including mortality 8
```

Independent SMT check on corrected full-invariant counts:

```text
z3_corrected_negated_claim_status sat
cvc5_corrected_negated_claim_status sat
```

That means the negated claim `live_classes + mortality_classes != 5` is satisfiable when bound to the recomputed full-invariant class count. The current z3/cvc5/Z3.jl proofs are load-bearing only for the internally asserted `live_classes=2` abstraction, not for the committed invariant classifier named in the audit question.

Honest structural reading after audit: the artifact proves exhaustive 24-order breadth for one fixed four-constraint multiset/alphabet, with 19 mortality orderings in three committed mortality modes. It does not prove two live final-object equivalence classes unless a new, explicit normalization removes entropy-ledger order from the invariant definition.

## Q5 - Standard schema and tool/process checks

Status: MIXED.

Pass:

- `mode` is `RATCHETED`.
- `schema_version` is `three_engine_sim_result_v1`.
- `classification` is `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.
- Parent lineage is present for the four requested parents and includes committed hashes.
- `TOOL_MANIFEST` and `TOOL_INTEGRATION_DEPTH` exist with non-empty reasons/depths.
- Top-level `tool_calls` are one-to-one for `sympy`, `z3`, `cvc5`, and `Z3`.
- No fixture wording found by `rg -n "fixture|fixtures" system_v6/sims/ratchet_order_breadth_v0`.
- Capability versions are present: Python 3.13.6, sympy 1.14.0, z3 4.16.0, cvc5 1.3.3, Julia 1.12.6, Z3.jl 1.0.4.
- Real Julia/Z3 environment smoke check passed:

```text
julia_z3_unsat=unsat
active_project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml
```

Fail/caveat:

- The packet calls the Python lane `jax`, but `engines.jax.packages_used` is `["sympy", "z3", "cvc5", "json", "hashlib", "subprocess"]`; no actual JAX package or JAX array computation is present. This may be consistent with prior "JAX as workhorse label" convention only if accepted as naming drift, not as a real JAX backend.
- No `seed_ledger` or seed field exists in the target envelope. The computation is exact/deterministic, but the requested "seeds" standard is not literally satisfied.
- The scoped validator returns no errors, but it misses the decisive within-class full-invariant mismatch.

## Named caveats

1. CAVEAT_UNTRACKED_PACKET: the audited packet is untracked in this checkout; audit status is on-disk, not committed-current.
2. CAVEAT_CLASS_ID_NOT_INVARIANT: live equivalence classes are grouped by `class_id`, not by denominator + holonomy spectrum + entropy ledger + survival sets.
3. CAVEAT_ENTROPY_LEDGER_ORDER: if entropy-ledger ordering is meant to be normalized away, the normalization is absent from the builder, validator, and result schema.
4. CAVEAT_PROJECTION_ONLY_PARENT: the deep-chain anchor is byte-exact only after erasing second Z2/operator/saturation rows.
5. CAVEAT_JAX_LABEL: the `jax` engine label is not backed by JAX package execution in this packet.
6. CAVEAT_NO_SEED_LEDGER: deterministic exact rows are present, but no target seed ledger is present.

## Verdict

REJECT as a claim that `ratchet_order_breadth_v0` closes the exhaustive-ordering uniqueness gap with `k=2` live final-object classes.

Acceptable retained ceiling: `scratch_diagnostic` enumeration/mortality scout. It supports: "all 24 orderings of the fixed `L,Z,W,T` multiset were evaluated; 19 die in three committed mortality classes; the five live orderings separate by full invariant signature unless a future explicit normalization quotients out entropy-ledger order."

Blocked promotion: final uniqueness/`k=2`, committed equivalence-class table, and any downstream claim that depends on the live rows collapsing to two final objects.

## Builder-fix addendum - 2026-06-11

Status: builder correction applied; this does not overturn the audit verdict. The verdict remains `REJECT` until a fresh re-audit accepts the corrected packet.

Correction named: `CAVEAT_CLASS_ID_NOT_INVARIANT` was fixed by grouping live survivors under the packet's full declared invariant signature rather than under coarse `class_id`. The load-bearing class count now recomputes as:

```text
summary {"distinct_live_outcomes": 5, "distinct_mortality_classes": 3, "live_orderings": 5, "mortality_orderings": 19, "orderings_total": 24, "total_equivalence_classes_including_mortality": 8}
```

Corrected structural reading:

```text
19/24 orderings die in three committed/scope mortality classes.
The five live orderings are pairwise distinct under the full declared invariant signature.
For this fixed L/Z/W/T multiset, the surviving paths are full-invariant path-unique.
```

SMT/proof rebinding:

```text
z3 identity: live_classes + mortality_classes = 8 with full-invariant table counts bound as context
z3 verdict: unsat
z3 erased_flip_verdict: sat
cvc5 identity: live_classes + mortality_classes = 8 with full-invariant table counts bound as context
cvc5 verdict: unsat
cvc5 erased_flip_verdict: sat
Julia Z3 verdict: unsat
Julia Z3 erased_flip_verdict: sat
```

Anchor status after correction:

```text
committed_chain_projection_byte_exact true
commuting_pair_anchor_recovered true
commuting_pair_full_invariant_same false
known_noncommuting_anchor_recovered true
live_full_invariant_pairwise_distinct true
```

Fresh reruns and validators:

```text
/opt/homebrew/bin/julia --project=system_v5/julia_carrier --startup-file=no --check-bounds=yes -e 'include("system_v6/sims/ratchet_order_breadth_v0/ratchet_order_breadth_v0_julia.jl")'
{"ok":true,"result_path":"system_v6/sims/ratchet_order_breadth_v0/results/ratchet_order_breadth_v0_julia_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ratchet_order_breadth_v0/ratchet_order_breadth_v0.py
{"ok": true, "result_path": "system_v6/sims/ratchet_order_breadth_v0/results/ratchet_order_breadth_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ratchet_order_breadth_v0/validate_ratchet_order_breadth_v0.py system_v6/sims/ratchet_order_breadth_v0/results/ratchet_order_breadth_v0_envelope_results.json
{"ok": true, "errors": []}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/ratchet_order_breadth_v0/results/ratchet_order_breadth_v0_envelope_results.json
{"ok": true}
```

Byte-stability check across a second envelope rerun:

```text
stable true
all_orderings_sha256 de1aadd347be4843668a10cd3fa2276ed32cd07f0f9802a8a2108b9a2398d78b
live_rows_sha256 c3ae5c9beb06323662825def35af5434c95b29eb44693b9817b53d0af7ae9248
mortality_rows_sha256 200e850d9c7f6e4dfd8ab9605749fda9345512bae9461a56e99853ce312e8113
```

## Re-audit addendum - 2026-06-11

Mode: focused read-only re-audit of the corrected packet, except appending this addendum. I did not build this packet. I did not run the packet builders because they write result files. I did not `git add` or commit anything. This packet remains untracked in this checkout (`git status --short -- system_v6/sims/ratchet_order_breadth_v0` reports `?? system_v6/sims/ratchet_order_breadth_v0/`), so this verdict is on-disk, not committed-current.

The prior `REJECT` headline / `KEEP` enumeration verdict remains history. The corrected packet now fixes the rejected bar. Source inspection shows `live_object()` hashes the full declared invariant object, including `effective_denominator`, `holonomy_spectrum`, `entropy_ledger`, and `survival_sets`, into `class_signature_sha256` (`ratchet_order_breadth_v0.py:271-287`), and `order_table()` now groups live rows by that full signature (`ratchet_order_breadth_v0.py:313-358`), not by coarse `class_id`.

Fresh scratch recomputation with the Makefile interpreter (`/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`) imported the source without invoking `main()` and recomputed:

```text
summary {"distinct_live_outcomes": 5, "distinct_mortality_classes": 3, "live_orderings": 5, "mortality_orderings": 19, "orderings_total": 24, "total_equivalence_classes_including_mortality": 8}
relation full_declared_invariant_signature_sha256
```

Two concrete class memberships under the full signature:

```text
LZWT -> 43ebe1439c1c318c2d0fd3fff87a95a45d556fc904dc4e11542a67652d578437, singleton ["LZWT"], coarse O1_window_before_terrain
ZLWT -> c846a96dd6ef826e476b7df8379a17e03c7753616c2fb633f973609238cec1bb, singleton ["ZLWT"], coarse O1_window_before_terrain
```

This verifies the old coarse commuting anchor remains visible while the full invariant bar keeps the two survivor paths distinct. The five live singleton classes are `LZWT`, `LZTW`, `LTZW`, `ZLWT`, and `ZLTW`.

Corrected structural reading: `19/24` orderings die in three committed/scope mortality classes; the five survivors are pairwise distinct under the full declared invariant signature; for this fixed `L/Z/W/T` multiset, survivor paths are full-invariant path-unique. This does not generalize beyond the one fixed four-constraint multiset.

Fresh SMT rebound:

```text
z3 negated corrected identity status: unsat
z3 erased-live-class control status: sat
cvc5 negated corrected identity status: unsat
cvc5 erased-live-class control status: sat
Julia Z3 positive_negation_status=unsat
Julia Z3 erased_flip_status=sat
```

The solver identity is the corrected one: `live_classes + mortality_classes = 8` with full-invariant table counts bound as context. The erased control binds `live_classes=4`, making the negated identity satisfiable as expected.

Anchors re-verified under the corrected classification:

```text
committed_chain_projection_byte_exact true
commuting_pair_anchor_recovered true
commuting_pair_full_invariant_same false
known_noncommuting_anchor_recovered true
terrain_gap_anchor_recovered true
live_full_invariant_pairwise_distinct true
```

Validators checked without rewriting the packet-local validator result: importing `validate_ratchet_order_breadth_v0.validate(payload)` returned `[]`, and `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/ratchet_order_breadth_v0/results/ratchet_order_breadth_v0_envelope_results.json` returned `{"ok": true, "result_json": "system_v6/sims/ratchet_order_breadth_v0/results/ratchet_order_breadth_v0_envelope_results.json"}`.

Enumeration/mortality rows are byte-stable against the kept-row hashes quoted in the builder-fix addendum:

```text
all_orderings_sha256 de1aadd347be4843668a10cd3fa2276ed32cd07f0f9802a8a2108b9a2398d78b
live_rows_sha256 c3ae5c9beb06323662825def35af5434c95b29eb44693b9817b53d0af7ae9248
mortality_rows_sha256 200e850d9c7f6e4dfd8ab9605749fda9345512bae9461a56e99853ce312e8113
historical_hash_match true/true/true
```

Final verdict line: the corrected packet EARNED the bounded scratch diagnostic; final `k` statement is `k=5` live full-invariant survivor classes, plus `3` mortality classes, for `8` total classes across the exhaustive 24 orderings of this one fixed `L/Z/W/T` multiset; ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, with no global order theorem, admission, bridge, axis, physics, or cross-multiset claim earned.

## Builder-fix-2 addendum - 2026-06-11

Status: builder correction applied after live falsifier-agent receipt on 2026-06-11. The prior re-audit `EARNED` line is superseded on the distinctness component only; enumeration, mortality, ceilings, and the M3 witness remain retained pending fresh rerun evidence below.

Circularity named: the previous `k=5` live-survivor headline was an order echo. The signature included `entropy_ledger` rows with per-step constraint names and step indices, so the classifier could decode the path order. The packet's own L/Z commuting anchor pair (`LZWT` vs `ZLWT`, `gap=0`) differed only through that ledger echo. The falsifier's echo-stripped recount gave the live split `{LZWT,ZLWT}` vs `{LZTW,LTZW,ZLTW}`.

Correction required and applied: live classes are now grouped by an order-blind object signature only: final denominator, holonomy spectrum, final survival sets, and entropy deltas canonicalized by constraint with step order dropped. The terrain split is carried by the computed object support set, not by `class_id` or a terrain-scope label. The terrain order gap row is recomputed inside `ratchet_order_breadth_v0.py` from the symbolic `Delta(theta)=T(O r)-O(T r)` expression instead of copied as a constant.

Corrected structural target:

```text
orderings_total 24
live_orderings 5
mortality_orderings 19
distinct_live_outcomes k=2
distinct_mortality_classes 3
total_equivalence_classes_including_mortality 5
L/Z anchor: LZWT and ZLWT same order-blind class
T/W precedence split: {LZWT,ZLWT} vs {LZTW,LTZW,ZLTW}
```

SMT rebinding target:

```text
z3/cvc5/Julia Z3 identity: live_classes + mortality_classes = 5 with order-blind table counts bound as context
erased flip: bind live_classes=1, making the negated identity SAT
```

The original mortality half is intentionally unchanged: `19/24` orderings die in `M1_phase_without_leaf`, `M2_terrain_without_leaf`, and `M3_raw_window_then_Z4`; the `M3_raw_window_then_Z4` witness remains the raw phase-window then Z4 equivariance failure.

Fresh reruns after builder-fix-2:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
ok=True install_state=stable_observed
No repo-local env pollution, missing expected modules, or active installers observed.

/opt/homebrew/bin/julia --project=system_v5/julia_carrier --startup-file=no --check-bounds=yes -e 'include("system_v6/sims/ratchet_order_breadth_v0/ratchet_order_breadth_v0_julia.jl")'
{"ok":true,"result_path":"system_v6/sims/ratchet_order_breadth_v0/results/ratchet_order_breadth_v0_julia_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ratchet_order_breadth_v0/ratchet_order_breadth_v0.py
{"ok": true, "result_path": "system_v6/sims/ratchet_order_breadth_v0/results/ratchet_order_breadth_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ratchet_order_breadth_v0/validate_ratchet_order_breadth_v0.py system_v6/sims/ratchet_order_breadth_v0/results/ratchet_order_breadth_v0_envelope_results.json
{"ok": true, "errors": []}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/ratchet_order_breadth_v0/results/ratchet_order_breadth_v0_envelope_results.json
{"ok": true, "result_json": "system_v6/sims/ratchet_order_breadth_v0/results/ratchet_order_breadth_v0_envelope_results.json"}
```

Fresh result slice:

```text
summary {"distinct_live_outcomes": 2, "distinct_mortality_classes": 3, "live_orderings": 5, "mortality_orderings": 19, "orderings_total": 24, "total_equivalence_classes_including_mortality": 5}
live classes ["LZTW","LTZW","ZLTW"] and ["LZWT","ZLWT"]
LZWT/ZLWT order_blind_same true
terrain_order_gap_norm_squared 4/25
commuting_control_gap_norm_squared 0
z3/cvc5/Julia Z3 bound live_classes 2, mortality_classes 3, table_rows 24
mortality_rows_sha256 200e850d9c7f6e4dfd8ab9605749fda9345512bae9461a56e99853ce312e8113
```

## Final fix-2 re-audit addendum - 2026-06-11

Mode: focused read-only re-audit of builder-fix-2, except appending this one addendum. I did not build or fix the packet. I did not rerun packet builders because they rewrite result files. I did not `git add` or commit anything.

Premortem guard / pinned convention: accepted only under the order-blind signature convention declared by the fix-2 packet: "live classes are now grouped by an order-blind object signature only: final denominator, holonomy spectrum, final survival sets, and entropy deltas canonicalized by constraint with step order dropped." The concrete pinned basis in the result is `effective_denominator`, `holonomy_spectrum`, `entropy_deltas_by_constraint`, and `survival_sets`, with relation `order_blind_object_signature_sha256`. `k` is therefore not absolute; it is `k=2` relative to this pinned order-blind signature convention for this fixed `L/Z/W/T` multiset.

Order-echo falsifier rerun: no live `order_blind_signature` contains `step`, `ordered`, `ordering`, or a literal live ordering string. Component partitions were: `effective_denominator`, `holonomy_spectrum`, and `entropy_deltas_by_constraint` each collapse all five live rows together; `survival_sets` splits exactly into `{LZWT,ZLWT}` and `{LZTW,LTZW,ZLTW}`. The ordering cannot be recovered from any signature component; only the intended T/W support-set split remains.

Fresh scratch recomputation from imported source, without invoking `main()`:

```text
summary {"distinct_live_outcomes": 2, "distinct_mortality_classes": 3, "live_orderings": 5, "mortality_orderings": 19, "orderings_total": 24, "total_equivalence_classes_including_mortality": 5}
relation order_blind_object_signature_sha256
basis ["effective_denominator","holonomy_spectrum","entropy_deltas_by_constraint","survival_sets"]
live classes ["LZWT","ZLWT"] and ["LZTW","LTZW","ZLTW"]
LZWT/ZLWT same signature e9e17eba36180e6aefcaf446083df4d8904c5117d7ba3ac05cf2ff9c92bdaceb
```

Terrain gap check: `terrain_gap_row()` recomputes `Delta(theta)=T(O r(theta))-O(T r(theta))` locally. Fresh scratch output was `delta = [2*sin(theta)/5, 0, -2*cos(theta)/5]`, `terrain_gap_norm_squared = 4/25`, and commuting control `D_z/R_z = 0`. The value is constant across live rows because the local symbolic expression simplifies to that constant norm, not because a parent value was echoed.

Mortality and SMT checks:

```text
mortality 19/24, classes {"M1_phase_without_leaf":8,"M2_terrain_without_leaf":8,"M3_raw_window_then_Z4":3}
mortality_rows_sha256 200e850d9c7f6e4dfd8ab9605749fda9345512bae9461a56e99853ce312e8113
z3 bound live_classes=2 mortality_classes=3 table_rows=24 -> negated identity unsat; erased live_classes=1 -> sat
cvc5 bound live_classes=2 mortality_classes=3 table_rows=24 -> negated identity unsat; erased live_classes=1 -> sat
current Julia Z3 result binds live_classes=2 mortality_classes=3 table_rows=24 -> unsat; erased flip -> sat
validator import returned []
validate_three_engine_sim_result.py returned ok true
```

Final verdict line: fix-2 EARNED, under the pinned order-blind signature convention only. Final honest headline: `ratchet_order_breadth_v0` is a bounded scratch diagnostic showing all 24 orderings of the fixed `L/Z/W/T` multiset were evaluated; 19 die in three mortality classes; the five survivors collapse to `k=2` order-blind live classes relative to the pinned signature, with `LZWT/ZLWT` now same-class and the surviving split carried by terrain support after Z4. Ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`; no global order theorem, admission, bridge, axis, physics, or cross-multiset claim is earned.
