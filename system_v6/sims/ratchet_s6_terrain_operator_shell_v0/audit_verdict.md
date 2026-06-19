# Fresh audit verdict: ratchet_s6_terrain_operator_shell_v0

Scope: read-only fresh audit of `system_v6/sims/ratchet_s6_terrain_operator_shell_v0/`, except this `audit_verdict.md`. I did not build this packet. I did not run any command that writes packet results, and I did not `git add` or commit anything.

Wizard route truth: partial Max Assembly only. Three Codex parent audit lanes were spawned; two returned before synthesis and the third returned during close. No child subsubagent layer or full council topology completed. Counts are therefore advisory audit receipts plus local tool recomputation, not a FULL Wizard proof.

## Verdict

VERDICT: PASS WITH NAMED CAVEATS at `scratch_diagnostic` ceiling.

The packet earns a bounded single-shell terrain/operator ratchet diagnostic: conditioning to one `T_pi/6` shell, consuming the committed `Se_Funnel_L` generator by hash, computing the induced conditioned-leaf flow/fixed-point exclusion, and proving a genuine nonzero `Se_Funnel_L` then `Fi_R_x` order gap with a computed zero `D_z`/`R_z` commuting control.

It does not earn two-shell terrain, a full 8-terrain sweep, basin theorem, Matrix64/all-64 S6 overlay, `M(C,t)`, formal admission, canonical geometry, axis-level admission, bridge claim, or finite-time terrain-flow theorem beyond the generator row.

## Named caveats

- `CAVEAT_WORKTREE_STATE`: the target packet directory is untracked at audit time: `?? system_v6/sims/ratchet_s6_terrain_operator_shell_v0/`. This verdict audits the working-tree packet contents over committed parent receipts, not a committed S6 object.
- `CAVEAT_PACKET_VALIDATOR_NOT_RERUN`: `validate_ratchet_s6_terrain_operator_shell_v0.py` writes `results/ratchet_s6_terrain_operator_shell_v0_validator_results.json` (`validate_ratchet_s6_terrain_operator_shell_v0.py:176`), so I did not rerun it under the read-only-except-verdict constraint. Existing validator result is green.
- `CAVEAT_JAX_NAME`: the envelope `engines.jax.scope` says "Python exact/SMT workhorse lane for this packet; no JAX array claim is made" (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:718-733`). This is honest lane prose, but it is not an actual JAX runtime lane.
- `CAVEAT_JULIA_QUOTE_GATE`: the Julia leg is real and Z3.jl is load-bearing, but the Julia result carries source path/hash and solver rows rather than full source quote gates. Treat this as sufficient for the bounded diagnostic, not a stronger source-lock standard.
- `CAVEAT_JULIA_SHALLOW_SOLVER_ROW`: Julia Z3.jl proves a pre-derived scaled row, `15*Delta_z = -2*sqrt3_squared with sqrt3_squared=3`, rather than reconstructing the full matrix gap inside the solver. Python z3/cvc5 do reconstruct the matrix gap.

## Q1 conditioning and lineage

PASS.

Source rule quoted: the committed disintegration rule pins `conditional_on_T_eta=normalized_flat_torus_measure_in_phi_chi_chart`, `chart_double_cover=(phi,chi)~(phi+pi,chi+pi)`, and `conditional_chart_density=1/(4*pi^2)` (`geo_disintegration_machinery_v0_common.py:40-42`). The S6 packet cites that parent as the `single_leaf_rule` and says only the five named parent packets are cited (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:793-800`). The conditioned step says: `conditioned_object = T_pi/6`, rule = "use committed disintegration machinery; do not use naive 0/0 singleton conditioning", and state family has `z = 1/2`, `xy_radius = sqrt(3)/2` (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:869-900`).

Fresh recomputation:

```text
s1_envelope_sha256 = 65ad62f37fe1119cd2984f7ce7a58d4e1e3657a27a76d715193ef4794974b555
recorded_s1_envelope_sha256 = 65ad62f37fe1119cd2984f7ce7a58d4e1e3657a27a76d715193ef4794974b555
```

This matches the recorded `ratchet_s1_single_shell_pilot_v0` parent lineage row (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:848-858`). A parent-lane recomputed all five lineage rows from `git show HEAD:<path>` and matched their `committed_tree`, `envelope_sha256`, and `top_source_sha256`.

Naive conditioning control was re-fired: denominator mass `0`, numerator mass `0`, `naive_quotient = nan`, `pass = true` (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:151-158`). This mirrors the committed parent control (`geo_disintegration_machinery_v0_envelope_results.json#/controls/naive_singleton_conditioning`), which records the same `0/0 -> nan` failure.

## Q2 terrain step

PASS.

The S6 source consumes committed S5 and S4 rows from `git show HEAD:<path>` via `selected_committed_rows()` (`ratchet_s6_terrain_operator_shell_v0.py:200-228`). The selected S5 row is `s5["bloch_generator_table"]["Se_Funnel_L"]["pinned"]` (`ratchet_s6_terrain_operator_shell_v0.py:207`).

Fresh recomputation from committed S5/S4 parent results:

```text
terrain_ab_sha256 = 25f78fc755e37729771e46eef26f6d80358dbcee06891917e2ebe82dcee5128a
rx_sha256 = c9b672bf2f456447639c0623577a865d3ef081bf5de2a3a0672f67234fa225e8
dz_sha256 = 3e9f91bc0026bccd728a4b4991e50494f35c8bca4689c35c95f0734522138a65
rz_sha256 = 45270cfa2241cf25bbdcce2a6129fcaffc55ea7d558ca94ead1fe4e41b8f3841
```

The emitted terrain row carries the same `ab_sha256`, `A`, `b`, and `id = Se_Funnel_L` (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:920-950`).

Fresh recomputation of the conditioned-leaf flow:

```text
field = [
  -sin(theta)/5 - 2*sqrt(3)*cos(theta)/5 + sqrt(3)/15,
  -2*sqrt(3)*sin(theta)/5 + cos(theta)/5 - sqrt(3)/15,
  -sqrt(2)*cos(theta + pi/4)/5 - 2/5
]
z_dot = -sqrt(2)*cos(theta + pi/4)/5 - 2/5
theta_dot = -2*sqrt(2)*sin(theta + pi/4)/15 + 2*sqrt(3)/15
purity_dot = -8/5
average_z_dot = -2/5
wrong_leaf_average_z_dot_at_eta_pi_over_4 = 0
```

These match the envelope field, leakage, projected drift, and wrong-leaf control (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:944-961`, `151-163`). The leakage class names are used correctly for this row: `leakage_class = cross_shell`, `pure_foliation_status = leave_foliation`, and `s6_class_name_applied = cross_shell_with_leave_foliation` (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:951-956`).

Fresh fixed-point recomputation:

```text
unconstrained_fixed_point = [0, 0, 0]
fixed_survives_T_pi_over_6 = False
induced_leaf_fixed_points = []
```

The packet's exclusion language is correct: `r=0` has `z=0` and Bloch radius `0`, while the conditioned object has `z=1/2` and pure radius `1` (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:903-918`).

## Q3 order gap and commuting control

PASS.

The source computes the order gap as `a_terrain * (rx * r) + b_terrain - rx * (a_terrain * r + b_terrain)` (`ratchet_s6_terrain_operator_shell_v0.py:255-258`). Fresh recomputation:

```text
Delta(theta) = [2*sin(theta)/5, 0, -2*cos(theta)/5]
||Delta(theta)||^2 = 4/25
Delta(0) = [0, 0, -2/5]
Delta(pi/2) = [2/5, 0, 0]
```

This matches the emitted N01/path-specific order row (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:978-999`, `1064-1085`). The gap is genuinely nonzero and is the path-specificity row: terrain-then-operator differs from operator-then-terrain on the conditioned object for `Se_Funnel_L` and `Fi_R_x`.

The commuting control is computed, not merely asserted. The source computes `dz * (rz * r) - rz * (dz * r)` and its norm (`ratchet_s6_terrain_operator_shell_v0.py:260-261`). Fresh recomputation:

```text
D_z/R_z control_delta = [0, 0, 0]
D_z/R_z control_norm2 = 0
```

SMT recomputation:

```text
z3_gap_zero_assertion = unsat
z3_erased_gap_zero_assertion = sat
z3_dz_rz_nonzero_assertion = unsat
cvc5_gap_zero_assertion = unsat
cvc5_erased_gap_zero_assertion = sat
cvc5_dz_rz_nonzero_assertion = unsat
```

The zero control therefore survives the calibrated bar: the nonzero assertion for the commuting pair is UNSAT in both solvers, while the erased-skew control flips the noncommuting row to SAT (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:146-150`, `1134-1190`).

Julia Z3.jl corroborates the bounded row: `verdict = unsat`, `erased_flip_verdict = sat`, and `julia_z3_commuting_control.verdict = unsat` (`ratchet_s6_terrain_operator_shell_v0_julia_results.json:62-99`). Caveat: see `CAVEAT_JULIA_SHALLOW_SOLVER_ROW`.

## Q4 ratchet signatures

PASS.

Narrowing is exact and names the objects:

- Step 0: Bloch ball / density state space, dimension `3`.
- Step 1: `T_pi/6` leaf state family, dimension `1`, `z = 1/2`.
- Step 2: terrain-constrained fixed/basin survivor set on conditioned shell, `survivor_count = 0`.

These rows are emitted at `ratchet_s6_terrain_operator_shell_v0_envelope_results.json:1019-1041`.

Alteration is computed: before conditioning the unconstrained fixed point count is `1` with fixed point `[0,0,0]`; after conditioning the induced fixed point set is empty and `projected_leaf_drift_has_no_zero = true` (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:1003-1017`).

Path-specificity is the order-gap row: `Delta(theta)` has norm squared `4/25`, while the `D_z/R_z` commuting control has norm squared `0` and solver rows `z3 = unsat`, `cvc5 = unsat` for the relevant zero/nonzero assertions (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:1043-1085`).

## Q5 standard checks

PASS WITH CAVEATS.

Schema and mode: `schema_version = three_engine_sim_result_v1`, `mode = RATCHETED`, `classification = scratch_diagnostic`, `promotion_allowed = false`, and `formal_admission_allowed = false` (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:102-124`, `1088-1097`).

Tool manifest and depth are present with non-empty reasons. Claim-path tools are one-to-one: `sympy`, `z3`, `cvc5`, `Z3` (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:1-53`, `117-123`, `1117-1225`). Capability receipts exist for Python, SymPy, z3, and cvc5 with versions (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:84-100`).

Julia leg: existing Julia result has `packages_used = ["JSON3","SHA","Dates","Z3"]`, `aligned_packages_load_bearing = ["Z3"]`, `reads_peer_result = false`, `all_pass = true`, and `classification = scratch_diagnostic` (`ratchet_s6_terrain_operator_shell_v0_julia_results.json:1-24`). The Julia source constructs real Z3.jl solver rows for the scaled nonzero gap and commuting-control zero row (`ratchet_s6_terrain_operator_shell_v0_julia.jl:38-90`). I did not rerun the Julia script because it writes its fixed repo result path. The existing source/result hashes match the envelope (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:735-753`).

Validator checks run fresh:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/ratchet_s6_terrain_operator_shell_v0/results/ratchet_s6_terrain_operator_shell_v0_envelope_results.json
=> {"ok": true, "result_json": ".../ratchet_s6_terrain_operator_shell_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/ratchet_s6_terrain_operator_shell_v0/results/ratchet_s6_terrain_operator_shell_v0_envelope_results.json
=> {"ok": true, "result_json": ".../ratchet_s6_terrain_operator_shell_v0_envelope_results.json"}
```

Packet-local validator existing receipt is green: `ok = true`, `errors = []`, `validated_mode = RATCHETED` in `results/ratchet_s6_terrain_operator_shell_v0_validator_results.json`. I did not rerun it because it writes that file.

No banned fixture wording was found in the packet sources/results, excluding this verdict file, by `rg -n "\b(fixture|mock|toy|demo)\b" system_v6/sims/ratchet_s6_terrain_operator_shell_v0 -g "!audit_verdict.md"`. Seed ledger is deterministic exact-row/no-RNG with `symbolic_seed = 2026061106`, `smt_seed = 2026061106`, `terrain = Se_Funnel_L`, and `operator = Fi_R_x` (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:1098-1105`).

Honest lane naming: the envelope does not claim real JAX arrays; it says the `jax` key is a "Python exact/SMT workhorse lane" (`ratchet_s6_terrain_operator_shell_v0_envelope_results.json:718-733`). This is accepted only with `CAVEAT_JAX_NAME`.

## Q6 closure

Earned:

- one conditioned shell: `T_pi/6`;
- one committed terrain row consumed by hash: `Se_Funnel_L`;
- one conditioned-leaf induced-flow/leakage/fixed-point exclusion row;
- one genuine noncommuting `Se_Funnel_L`/`Fi_R_x` order-gap row with norm squared `4/25`;
- one computed killing control: `D_z`/`R_z` gap norm squared `0`;
- z3/cvc5 erased-skew flip: noncommuting zero assertion `unsat`, erased zero assertion `sat`;
- Julia Z3.jl corroboration of the bounded scaled row.

Not earned:

- no two-shell terrain;
- no full eight-terrain sweep;
- no basin theorem;
- no full Matrix64 or all-64 S6 overlay;
- no `M(C,t)`;
- no formal admission;
- no canonical geometry;
- no axis, bridge, physics, or finite-time terrain-flow theorem.

## Hygiene

No `git add` and no commit were run. Fresh `git status --short -- system_v6/sims/ratchet_s6_terrain_operator_shell_v0` showed the target packet as untracked before this verdict; after this verdict, that remains the expected packet-level untracked state with this audit file added inside it.
