# Fresh audit verdict: ratchet_deep_chain_v0

Scope: read-only fresh audit of `system_v6/sims/ratchet_deep_chain_v0/`, except this `audit_verdict.md`. I did not build this packet. I did not run the packet builder, Julia sidecar, or packet-local validator because each writes fixed result files under the target directory. I did run read-only source/result inspection, parent hash recomputation, independent symbolic/SMT spot checks, and the repo-level three-engine validator.

Calibration used: `system_v6/receipts/audit_bar_calibration_20260610.md`. Exact/symbolic/integer rows are held strict; route genuineness, erasure honesty, scratch ceilings, capability gates, and source-backed claim paths remain binding.

VERDICT: GENUINE-WITH-CAVEATS as a bounded exact denominator/entropy/mortality diagnostic. The stronger `Z4 x Z2` group-isomorphism wording is not earned by the packet as written.

The earned core is: parent-lineage hashes resolve, the seven-row exact volume/entropy ledger recomputes, the raw phase-window mortality witness is real, the saturation row is scoped to cited committed constraints, the terrain order row cites a committed `4/25` gap, and z3/cvc5/Z3.jl denominator-erasure checks are present.

It does not earn: a proved composite action isomorphic to `Z4 x Z2`, a distinction from `Z8` or a quotient-collapse model, a full per-step induced-geometry object past the volume/denominator rows, a global saturation theorem, formal admission, canonical geometry, bridge/axis/manifold-level claims, or any claim beyond `scratch_diagnostic`.

## Named Caveats

- `G1_COMPOSITE_GROUP_NOT_EARNED`: the final denominator and volume survive recomputation, but the packet does not compute a second-action orbit table. `Z4 x Z2` is asserted via bound integers and prose, not adjudicated against `Z8` or collapse models.
- `G2_SECOND_Z2_ACTION_UNSPECIFIED`: the packet records `Z2_order = 2` and proves `4 * 2 * 2 = 16`, but it does not define the second `Z2` action on representatives, quotient classes, or an independent coordinate.
- `G3_INDUCED_GEOMETRY_THIN_AFTER_STEP2`: step 1/2 geometry can be recomputed from committed/pilot rows, but steps 3/4 mainly carry volume, denominator, and entropy rows. They do not carry a full induced metric/connection/orbit object.
- `G4_MEASURE_ZERO_CONVENTION_NOT_BAND_LIMITED`: the packet states a chart-uniform disintegration convention and avoids naive singleton conditioning, but it does not literally state a band-limit convention for the measure-zero conditioning step.
- `G5_PYTHON_LANE_NAMED_JAX`: the envelope key is `engines.jax`, but the lane is pure Python `sympy`/`z3`/`cvc5`; the envelope does say "no JAX array claim is made" (`ratchet_deep_chain_v0_envelope_results.json:300-304`). Treat it as a Python exact/SMT lane, not a JAX runtime lane.
- `G6_TOOL_RECEIPTS_THIN`: one-to-one tool rows exist, but the `sympy` row records only the final denominator object and lacks the richer positive/negative/boundary/demotion fields expected for load-bearing tool-call receipts.
- `G7_VERSION_RECEIPTS_PARTIAL`: Python capability receipt records Python version and package names, but not exact `sympy`/`z3`/`cvc5` package versions (`ratchet_deep_chain_v0.py:569-571`).
- `G8_TARGET_PACKET_UNCOMMITTED`: `git log -- system_v6/sims/ratchet_deep_chain_v0` returned no commits and `git status --short` showed `?? system_v6/sims/ratchet_deep_chain_v0/`. This audit covers the working-tree packet over committed parent receipts, not a committed target packet.

## Q1 Chain Genuineness

Decision: PASS WITH CAVEATS `G3` and `G8`.

Quoted source: the packet declares committed parents and allowed uses in `PARENTS` (`ratchet_deep_chain_v0.py:40-104`), then computes parent lineage through `git show HEAD:<path>`, `git rev-parse`, and `git log -n 1` (`ratchet_deep_chain_v0.py:184-203`).

Fresh recomputation of all parent lineage rows found no mismatches:

```text
parent_lineage_bad []
```

This covers the five RATCHETED parent packets plus the disintegration, union-rule, finite-lens, and compression/entropy framing parents recorded by the packet.

Induced geometry recomputation at two non-adjacent steps:

```text
step1 metric_phi_chi = [[1, 1/2], [1/2, 1]]
step1 determinant = 3/4
step1 double-cover chart area = 2*sqrt(3)*pi**2
step2 Z4 chart volume = pi**2
step4 final chart volume from double-cover convention = pi**2/4
step4 final chart volume from physical 2*pi**2 / 8 convention = pi**2/4
```

The source ledger computes the chain from symbolic volumes, not carried labels: `base_chart_volume = 4*pi**2`, `z4_volume = base/4`, `window_volume = z4/2`, and `z4xz2_volume = window/2` (`ratchet_deep_chain_v0.py:219-225`). The source then writes the per-step rows with citations and exclusions (`ratchet_deep_chain_v0.py:244-313`).

The caveat is that the recomputed induced object after step 2 is mostly a scalar volume/denominator/entropy object. There is no full induced metric, connection, representative action, or orbit object for steps 3/4.

## Q2 Composite Quotient

Decision: FAIL AS GROUP THEORY; PASS ONLY FOR EFFECTIVE DENOMINATOR/VOLUME.

The packet records:

```text
step 4 alteration: after = "Z4 x Z2, order 8 on independent quotient residue"
effective_denominator = 16
```

This is visible in the result (`ratchet_deep_chain_v0_envelope_results.json:623-643`) and produced in source (`ratchet_deep_chain_v0.py:274-282`). The SMT rows prove only:

```text
effective_denominator = Z4_order * phase_window_denominator * Z2_order
```

with `Z4_order = 4`, `phase_window_denominator = 2`, and `Z2_order = 2` (`ratchet_deep_chain_v0.py:374-420`; Julia mirror at `ratchet_deep_chain_v0_julia.jl:38-58`). Fresh solver recomputation:

```text
z3_positive unsat
z3_erased sat
cvc5_positive unsat
cvc5_erased sat
```

That proves the integer denominator identity and erased-control flip. It does not prove that the second action is independent from the first action, nor that the generated group is `Z4 x Z2` rather than `Z8` or a quotient/collapse.

Hard group-theory adjudication:

- `Z4 x Z2` requires an explicitly independent involution commuting with the `Z4` action and not generated by the `Z4` action.
- `Z8` is also compatible with an order-8 orbit denominator if the supposed second action is a square/root relation in one cyclic phase coordinate.
- Collapse is compatible if the second `Z2` acts inside an already identified quotient class, or is effectively identity on the surviving residue.

The packet does not define the second action on representatives, does not emit orbit sizes/counts for the composite action, and does not compute a quotient-of-quotient class table. The only orbit-style target rows found in the target packet are the mortality witness rows (`ratchet_deep_chain_v0_envelope_results.json:463-490`, `504-541`), not a composite quotient orbit table.

Reconciliation of `16` vs `8`:

```text
source convention: 4*pi**2 / 16 = pi**2/4
physical chart convention: 2*pi**2 / 8 = pi**2/4
```

The `16` is relative to the source's double-cover `dphi dchi` chart (`ratchet_deep_chain_v0.py:222-225`, `ratchet_deep_chain_v0_envelope_results.json:553-557`). The `8` is relative to the physical `2*pi x pi = 2*pi**2` chart. They are the same final volume under two chart conventions, not two different final objects. This reconciles the arithmetic, but it does not repair the missing group-action proof.

## Q3 Mortality Exhibit

Decision: PASS.

The mortality exhibit is the raw representative-level phase window before quotienting. Source:

```text
witness = [pi/4, 3*pi/4, 5*pi/4, 7*pi/4]
membership_z4 = [True, True, False, False]
membership_z2_after_window = [True, False]
```

This is computed in `ratchet_deep_chain_v0.py:324-340` and emitted at `ratchet_deep_chain_v0_envelope_results.json:463-490`.

Fresh recomputation:

```text
mortality_z4_membership [True, True, False, False]
equivariant False
mortality_z2_pair [True, False]
```

The failed step is the step 2/3 adjacent-swap branch: applying the raw phase window after quotienting is not well-defined because membership depends on the representative of the quotient orbit. The result correctly classifies this as `quotient_well_definedness_equivariance_failure`, not as a numeric order gap (`ratchet_deep_chain_v0_envelope_results.json:504-541`).

This matches the committed pilot's standard: the pilot records the non-Z4-saturated window witness and says the quotient-first branch kills the raw window as a coherent quotient constraint (`ratchet_s1_single_shell_pilot_v0.py:393-415`).

## Q4 Saturation Scoped

Decision: PASS.

The packet makes the saturation scope explicit:

```text
status = saturated_for_available_committed_constraint_set
available_repeats_checked = [T_pi/6, Z4, Z2, Se_Funnel_L basin exclusion, Se_Funnel_L/R_x order row]
proof_scope = scoped to the committed constraint types cited in parent_lineage; not a global theorem
```

This is emitted at `ratchet_deep_chain_v0_envelope_results.json:711-721` and constructed at `ratchet_deep_chain_v0.py:541-546`.

Fresh recomputation of the fixed point:

```text
before effective_denominator = 16
after effective_denominator = 16
before volume = pi**2/4
after volume = pi**2/4
```

No broader saturation claim was found in the target packet. The caveat is that this is a finite, cited-constraint fixed point only. It does not exclude future constraints, alternative lens actions, or broader manifold/axis-level constraints.

## Q5 Entropy Deltas

Decision: PASS WITH CAVEAT `G4`.

Panel-6 pre-registration says a free order-`N` quotient has entropy change exactly `-ln N`, and the disintegration chain rule is exact (`cross_model_anchor_recompute_panel6_20260611.md:7-10`).

Fresh recomputation of target rows:

```text
step 1: h = log(4*pi**2), delta = None
step 2: h = 2*log(pi), delta = -log(4)
step 3: h = log(pi**2/2), delta = -log(2)
step 4: h = log(pi**2/4), delta = -log(2)
steps 5-7: delta = 0
chain_rule_drop_1_to_4 = -log(16)
sum_deltas_2_to_4 = -log(16)
```

The stored result matches these values (`ratchet_deep_chain_v0_envelope_results.json:590-707`). The lens-step deltas match the pre-registered exact values: `-ln 4` for the `Z4` quotient and `-ln 2` for the second quotient row. The phase-window row is also `-ln 2`, but it is a survivor-fraction cut, not a quotient-group order by itself.

The packet states its convention as chart-uniform differential entropy on the current fundamental domain and says terrain fixed-point rows are not new absolutely continuous measure cuts (`ratchet_deep_chain_v0_envelope_results.json:553-557`). It also preserves the naive singleton conditioning failure (`ratchet_deep_chain_v0_envelope_results.json:556-560`). It does not literally state a band-limit convention for the measure-zero conditioning step; it uses disintegration/chart conditioning instead.

## Q6 Order Rows

Decision: PASS FOR RECORDED ADJACENT ROWS; NO FULL REORDERED-CHAIN CONTROL.

The step 1/2 adjacent swap is honestly commuting:

```text
condition_then_Z4_sha256 == Z4_then_condition_sha256
gap = 0
reason = Z4 global phase preserves eta
```

This is emitted at `ratchet_deep_chain_v0_envelope_results.json:493-502`.

The step 2/3 adjacent swap is a mortality row, not a numeric gap:

```text
gap_kind = undefinability_not_numeric_gap
honest_commutation = false
```

This is emitted at `ratchet_deep_chain_v0_envelope_results.json:504-541`.

The terrain order row cites the committed S6 terrain/operator packet:

```text
Se_then_Rx_gap_norm_squared = 4/25
commuting_control_Dz_Rz_gap_norm_squared = 0
```

The committed audit recomputed the same `4/25` row and the zero commuting control (`ratchet_s6_terrain_operator_shell_v0/audit_verdict.md:88-119`). The target records the citation at `ratchet_deep_chain_v0_envelope_results.json:543-551`.

The caveat is that there is no full reordered-chain control over all seven steps. The packet has adjacent rows plus one raw-window mortality branch.

## Q7 Standard Schema And Tooling

Decision: PASS WITH CAVEATS `G5`, `G6`, and `G7`.

Schema and ceiling:

- `schema_version = three_engine_sim_result_v1`
- `mode = RATCHETED`
- `classification = scratch_diagnostic`
- `promotion_allowed = false`
- `formal_admission_allowed = false`

These appear in the source (`ratchet_deep_chain_v0.py:35-38`, `489-498`) and result (`ratchet_deep_chain_v0_envelope_results.json:326-329`, `725-731`).

Julia leg:

- Source imports `Z3` (`ratchet_deep_chain_v0_julia.jl:3-7`).
- Source constructs a real `Z3.Solver` with `Z3.IntVar`, binds `z4`, `window`, `z2`, and `denom`, and checks `Not(denom == 16)` (`ratchet_deep_chain_v0_julia.jl:38-58`).
- Existing Julia result records `all_pass = true`, `reads_peer_result = false`, `packages_used = ["JSON3","Pkg","SHA","Dates","Z3"]`, and `aligned_packages_load_bearing = ["Z3"]` (`ratchet_deep_chain_v0_julia_results.json:1-24`).

Python z3/cvc5 rows:

- Source constructs the same denominator identity in z3 and cvc5 (`ratchet_deep_chain_v0.py:374-420`).
- Fresh recomputation gave `unsat` for the positive identity-negation check and `sat` for the erased second-`Z2` control.

Validators:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json --require-source-backed
=> {"ok": true, ...}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json --strict-source-backed
=> {"ok": true, ...}
```

I did not rerun `validate_ratchet_deep_chain_v0.py` because it writes `results/ratchet_deep_chain_v0_validator_results.json`. The existing receipt is green: `ok = true`, `errors = []`, `validated_mode = RATCHETED`.

Tool rows and capability receipts:

- One-to-one tool rows exist for `sympy`, `z3`, `cvc5`, and `Z3` (`ratchet_deep_chain_v0_envelope_results.json:735-760` and following rows).
- No banned `fixture`, `mock`, `toy`, or `demo` wording was found in target sources/results excluding this verdict.
- No trend/manifold-level promotion language was found in target sources/results.
- Seeds are deterministic exact-row/SMT/Julia seeds (`ratchet_deep_chain_v0_envelope_results.json:726-730`).

The caveats are that the Python lane is named `jax` without actual JAX execution, the `sympy` tool-call row is thin, Python package versions are partial, and the z3/cvc5 proof is a composite denominator proof rather than a per-step proof of every induced object.

## Final Ceiling

Ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Accepted statement:

`ratchet_deep_chain_v0` is a bounded working-tree diagnostic that recomputes a seven-row exact chart-volume/entropy chain over committed parent receipts, exhibits a genuine quotient-well-definedness mortality witness, and records scoped saturation for the cited committed constraint set.

Required demotion:

The phrase `Z4 x Z2` must not be treated as adjudicated group theory. Until a future packet defines the second action and emits composite orbit/class tables, the safe claim is only: effective denominator/volume arithmetic survives (`4*pi**2/16 = 2*pi**2/8 = pi**2/4`) with a named, unproved composite-action caveat.

No `git add` and no commit were run.

## Re-audit addendum: G1-G6 hardening closures

Scope: focused read-only re-audit of the hardening closures only. I did not build this packet. I did not run any writer entrypoint. I appended only this addendum.

Verdict update: the GENUINE-WITH-CAVEATS earned core stands, and the G1/G2, G3, G4, and G6 hardening closures are earned in the current working-tree packet. Residual caveats outside this closure scope remain: the target packet is still working-tree/untracked, and the `engines.jax` lane is still honestly a Python exact/SMT lane rather than a JAX array lane.

G1/G2 decisive closure:

```text
COMPOSITE_RECOMPUTE orbit_size= 8 orders= [('a^0 b^0', (0, 0), 1), ('a^0 b^1', (0, 1), 2), ('a^1 b^0', (1, 0), 4), ('a^1 b^1', (1, 1), 4), ('a^2 b^0', (2, 0), 2), ('a^2 b^1', (2, 1), 2), ('a^3 b^0', (3, 0), 4), ('a^3 b^1', (3, 1), 4)] max_order= 4 has_order8= False
```

I recomputed from the pinned actions `a:(q,r)->(q+1 mod 4,r)` and `b:(q,r)->(q,r+1 mod 2)`. The orbit from `q0r0` has eight representatives, every product has order at most 4, and there is no order-8 element. That earns the finite-action structure `Z4 x Z2` for the pinned representative model, excludes `Z8`, and excludes the quotient-collapse model where `b=a^2`.

SMT check:

```text
SMT_RECOMPUTE z3_positive= unsat z3_erased= sat cvc5_positive= unsat cvc5_erased= sat
```

The SMT rows bind the computed integer order/denominator identity `effective_denominator = Z4_order * phase_window_denominator * Z2_order`, with erased control `Z2_order=1`. The finite group discriminator itself is the explicit orbit/product-order table above, not an SMT proof of group isomorphism.

G3 closure:

```text
STEP3_HOLONOMY_RECOMPUTE inherited_Z4_holonomy= pi/2 stored= pi/2 connection_coefficient_dchi= 1/2
```

Steps 3 and 4 now carry `induced_geometry` objects with connection coefficient, metric data, holonomy data, and orbit/action objects. The step-3 inherited holonomy recomputes to `pi/2`.

G4 closure:

```text
BAND_LIMIT_QUOTE Band-limit convention: measure-zero fixed-eta conditioning is defined as the committed disintegration limit from positive eta-bands. Committed text pin: conditional_on_T_eta=normalized_flat_torus_measure_in_phi_chi_chart|chart_double_cover=(phi,chi)~(phi+pi,chi+pi)|conditional_chart_density=1/(4*pi^2)|finite_grid_physical_points=N^2/2|controls=naive_zero_denominator,positive_eta_band,flat_marginal_wrong,null_set_modification. Naive ambient singleton conditioning remains zero-denominator and is not used.
COMMITTED_FRAGMENT_QUOTE conditional_on_T_eta=normalized_flat_torus_measure_in_phi_chi_chart|chart_double_cover=(phi,chi)~(phi+pi,chi+pi)|conditional_chart_density=1/(4*pi^2)|finite_grid_physical_points=N^2/2|controls=naive_zero_denominator,positive_eta_band,flat_marginal_wrong,null_set_modification
```

The band-limit convention is now text-pinned and includes the committed disintegration fragment literally.

G6 closure:

```text
SYMPY_RECEIPT_KEYS ['boundary_case', 'demotion_condition', 'input_object', 'load_bearing', 'negative/erased_control', 'output_object', 'positive_case', 'qualified_api/function']
```

The SymPy receipt now has full shape: positive case, negative/erased control, boundary case, demotion condition, qualified API/function, input object, output object, and load-bearing flag.

Previously audited row stability:

```text
STABILITY_SLICE_SHA256 f022207ead8f0bc5907f9589e5835e5dfa7c12b9851b11cfc69b5c3fc2bacca8
POST_VALIDATOR_STABILITY_SLICE_SHA256 f022207ead8f0bc5907f9589e5835e5dfa7c12b9851b11cfc69b5c3fc2bacca8
STABILITY_SLICE_QUOTE final_denominator= 16 final_volume= pi**2/4 entropy_deltas= [(1, None), (2, '-log(4)'), (3, '-log(2)'), (4, '-log(2)'), (5, '0'), (6, '0'), (7, '0')] mortality_Z4= [True, True, False, False] mortality_Z2= [True, False]
```

The denominator, volume, entropy-delta, and mortality-witness slice stayed byte-stable across the read-only validator pass.

Validators:

```text
packet-local validate() => {"errors": [], "ok": true, "validated_mode": "RATCHETED", "validator": "system_v6/sims/ratchet_deep_chain_v0/validate_ratchet_deep_chain_v0.py::validate"}
scripts/validate_three_engine_sim_result.py ... --require-source-backed => {"ok": true, "result_json": "system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json"}
scripts/validate_three_engine_sim_result.py ... --strict-source-backed => {"ok": true, "result_json": "system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json"}
```

Closure line: closures earned; the precise composite finding is `Z4 x Z2` for the pinned finite action on `(q mod 4, r mod 2)` with no order-8 element, excluding `Z8` and quotient-collapse; ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
