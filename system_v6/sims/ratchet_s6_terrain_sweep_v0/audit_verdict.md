# audit_verdict.md -- ratchet_s6_terrain_sweep_v0

Auditor: codex1 cross-backend audit
Date: 2026-06-11
Scope: fresh read-only audit of `ratchet_s6_terrain_sweep_v0`, except this verdict file.
Route truth: partial local audit. Wizard v4.2 Max Assembly was required by repo contract, but native subagent spawning was blocked by the active tool contract for this turn. No worker/council receipts are claimed here.

## Claim And Ceiling

Claim under audit: the builder packet computes an 8-terrain matrix on one conditioned `T_pi/6` shell, anchored to the committed `Se_Funnel_L` single-terrain packet.

Accepted public status label: passes local rerun, for the claim-bearing result surfaces checked below.

Accepted ceiling: scratch diagnostic on one conditioned shell only. This earns an 8-terrain leakage/survival/order-gap matrix on `T_pi/6`, not multi-shell terrain behavior, not a basin theorem, not a terrain ranking, not `M(C,t)`, not a bridge/axis claim, and not formal admission.

Verdict: ACCEPT WITH NAMED CAVEATS.

## Fresh Checks Run

- `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ...`: independent SymPy/hash recomputation from committed parent JSONs, including all 8 terrain hashes, four fixed-point conditioning checks, leakage/purity rows, anchor field comparison, and anti-collapse pair columns.
- `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ...`: imported `validate_ratchet_s6_terrain_sweep_v0.validate(payload)` without invoking its write-producing CLI; result `validator_errors: []`.
- `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ...`: imported `ratchet_s6_terrain_sweep_v0.build_result()` without invoking `main`; claim-bearing subtrees matched the committed result payload.
- `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/ratchet_s6_terrain_sweep_v0/results/ratchet_s6_terrain_sweep_v0_envelope_results.json`: returned `{"ok": true, "result_json": "system_v6/sims/ratchet_s6_terrain_sweep_v0/results/ratchet_s6_terrain_sweep_v0_envelope_results.json"}`.

The packet CLI validator was not run directly because it writes `results/ratchet_s6_terrain_sweep_v0_validator_results.json`, outside the user's one-file write allowance.

## Per-Check Verdicts

### Q1 -- All 8 Generators Consumed By Committed Hash

Verdict: PASS.

The sweep result contains all 8 terrain rows in the declared order. Independent recomputation from `git show HEAD:system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json` reproduced the terrain-row stable JSON hashes:

- `Ne_Spiral_R`: `890ac6990ff4158d0f2f7bf9c786aac832837bd9b84530219b763576e18214b4`
- `Ne_Vortex_L`: `f7a01b371cb290c49e911ac477a244e29d9ae489ef0aec3c17c935c2f0c66218`
- `Ni_Pit_L`: `6eff3605086c785fa80db6f2c56f258685a500249bb41d34cc8bdc048ebfa13e`
- `Ni_Source_R`: `53103e38a21a630ef160a17355a2b55bedbc1faff74918bf1d8c8b47a08cc086`
- `Se_Cannon_R`: `82eaa9e60bea7754402e70442c041a467b3546199fae3af0ddd013a2a5763433`
- `Se_Funnel_L`: `25f78fc755e37729771e46eef26f6d80358dbcee06891917e2ebe82dcee5128a`
- `Si_Citadel_R`: `059b6cbfe868456e2478a802252ed543c3bd046d4e2cd4f4d3d79a4cbf50c4be`
- `Si_Hill_L`: `63c4862cc0414923ac5f4918f32a9c704f0050cb8d7e48830560b7b06b841676`

Spot recomputation included `Si_Hill_L`, yielding the same `63c486...1676` hash. The sweep's `terrain_ab_sha256` fields match the committed S5 pinned `A,b` rows.

### Q2 -- Fixed Survivors On T_pi/6: Zero

Verdict: PASS, no cross-packet conflict found.

The sweep's `fixed_point_survival_table` has 8 rows and all `survives_conditioning: false`. Independent fixed-point conditioning checks reproduced the exclusion logic for four rows:

- `Ne_Spiral_R`: fixed kernel line; at `z=1/2`, `alpha=1/2`, `radius_squared_at_z=3/4`; excluded.
- `Ni_Source_R`: fixed point `[64/203 - 40*sqrt(3)/203, 64/203 + 40*sqrt(3)/203, 139/203]`; `z=139/203`, `radius_squared=37113/41209`; excluded.
- `Se_Funnel_L`: fixed point `[0, 0, 0]`; `z=0`, `radius_squared=0`; excluded.
- `Si_Hill_L`: fixed kernel line along z; at `z=1/2`, `alpha=1/2`, `radius_squared_at_z=1/4`; excluded.

Cross-packet adjudication: the committed single-terrain packet `ratchet_s6_terrain_operator_shell_v0` does not contain a surviving conditioned fixed point for `Se_Funnel_L`. It records unconstrained fixed point `[0, 0, 0]`, `survives_conditioning: false`, empty `survivor_set_on_conditioned_object`, and exclusion language that `r=0` has `z=0` and Bloch radius `0` while the conditioned object requires `z=1/2` and pure radius `1`. Therefore the sweep's zero-survivor result is consistent with the committed packet's exclusion table, not a contradiction.

### Q3 -- Pure-Shell Compatible Terrains: None; Si_Hill_L Nuance

Verdict: PASS.

The computed table, not just labels, supports `pure_shell_compatible: []`. Independent recomputation showed:

- `Si_Hill_L` has `z_dot = 0`, so it preserves the density z-leaf.
- `Si_Hill_L` has `purity_derivative = -3/5`, so it breaks the pure shell.
- `Si_Hill_L` has `shell_compatibility = density_z_leaf_preserved_but_pure_shell_breaking`, `density_z_leaf_compatible: true`, and `pure_T_pi_over_6_compatible: false`.

The other seven rows have nonzero `z_dot` or nonzero shell movement and are classified as `shell_breaking`. Thus "none compatible" is computed from leakage/purity rows and not merely asserted.

### Q4 -- Anchor: Se_Funnel_L Gap 4/25 Byte-Exact Vs Committed Packet

Verdict: PASS.

The sweep's `template_anchor_reproduction.byte_exact` is true. Independent field comparison found exact equality for:

- terrain: `Se_Funnel_L`
- operator: `Fi_R_x`
- `terrain_ab_sha256`: `25f78fc755e37729771e46eef26f6d80358dbcee06891917e2ebe82dcee5128a`
- `order_gap_norm_squared`: `4/25`
- `order_gap_delta`: `["2*sin(theta)/5", "0", "-2*cos(theta)/5"]`
- `order_gap_witness_theta0`: `["0", "0", "-2/5"]`

### Q5 -- Anti-Collapse Findings

Verdict: PASS WITH OPEN PROBE CAVEAT.

The anti-collapse pairs are reported as findings and are not silently merged:

- `Ne_Spiral_R` / `Ne_Vortex_L`
- `Se_Cannon_R` / `Se_Funnel_L`

Independent comparison on the declared like-for-like matrix columns reproduced indistinguishability for both pairs across:

- `leakage_class`
- `survives_conditioning`
- `order_gap_norm_squared`
- `order_gap_zero_for_all_theta`
- `s6_class_name_applied`

For `Ne_Spiral_R` / `Ne_Vortex_L`, the common row is `cross_shell`, `survives_conditioning=false`, `order_gap_norm_squared=4`, `order_gap_zero_for_all_theta=false`, `s6_class_name_applied=cross_shell`.

For `Se_Cannon_R` / `Se_Funnel_L`, the common row is `cross_shell`, `survives_conditioning=false`, `order_gap_norm_squared=4/25`, `order_gap_zero_for_all_theta=false`, `s6_class_name_applied=leave_foliation`.

Open finer probe: the signed/vector-valued row could separate them. For example, `Ne_Spiral_R` and `Ne_Vortex_L` have opposite signed gap deltas (`[-2*sin(theta), 0, 2*cos(theta)]` vs `[2*sin(theta), 0, -2*cos(theta)]`), and `Se_Cannon_R`/`Se_Funnel_L` have opposite signed gap deltas at the same norm. A finer signed-flow, orientation, or time-directed probe is open and not resolved by this packet.

### Q6 -- Controls

Verdict: PASS.

Observed controls:

- Nothing-excluded control is byte-exact: before and after hashes match.
- Naive-conditioning failure re-fired: denominator mass `0`, numerator mass `0`, naive quotient `nan`, `pass: true`.
- Permuted-generator control fires: swapping the first two rows of committed `Se_Funnel_L` `A` breaks anchor reproduction; `anchor_reproduction_broken: true`.
- Erased-skew SMT flip fires: Python z3 and cvc5 erased rows return `sat` while the positive zero-gap assertion returns `unsat`.
- Julia Z3.jl leg also reports anchor `unsat`, erased flip `sat`, committed `D_z/R_z` control `unsat`, and eight sweep-row checks passing.

### Q7 -- Standard Schema, Tooling, Lineage, And Language

Verdict: PASS WITH ROUTE CAVEAT.

The envelope has `schema_version: three_engine_sim_result_v1`, `mode: RATCHETED`, `classification: scratch_diagnostic`, `promotion_allowed: false`, and `formal_admission_allowed: false`.

The packet has parent lineage for the committed parents, including:

- `ratchet_s6_terrain_operator_shell_v0`
- `ratchet_s1_single_shell_pilot_v0`
- `geo_disintegration_machinery_v0`
- `geo_s5_terrain_flows_v0`
- `geo_s4_operator_stage_v0`
- `geo_s2_s5_mode_sweep_v0`

The tool manifest and one-to-one `tool_calls` are present for `sympy`, `z3`, `cvc5`, and Julia `Z3`; all four are marked load-bearing for claim-path work. Capability receipts list Python `3.13.6`, SymPy `1.14.0`, z3 `4.16.0`, and cvc5 `1.3.3`. The Julia leg records `packages_used: ["JSON3", "SHA", "Dates", "Z3"]`, `aligned_packages_load_bearing: ["Z3"]`, `reads_peer_result: false`, and one load-bearing `Z3` tool call.

The exclusion language is present and avoids "best terrain" ranking language. The sweep's own ceiling and scope fences reject terrain ranking, nested multi-shell conditioning, promotion, and formal admission.

Route caveat: this audit did not run a real Wizard v4.2 multi-subagent/council topology. It is a local controller + shell/tool recomputation audit. Therefore no Max Assembly worker-count claims are made.

### Q8 -- Closure

Verdict: PASS.

Earned:

- 8 committed S5 terrain generator rows consumed by hash.
- Computed 8-row matrix on the single conditioned `T_pi/6` shell.
- Fixed-point survival exclusion on `T_pi/6`: zero survivors.
- Pure-shell compatibility exclusion: none; `Si_Hill_L` preserves density z-leaf but breaks pure shell.
- `Se_Funnel_L`/`Fi_R_x` anchor reproduced byte-exact from the committed single-terrain packet.
- Declared anti-collapse pairs retained as findings rather than merged.
- Controls fire, including permutation, naive-conditioning, nothing-excluded, and erased-skew SMT flips.

Not earned:

- No multi-shell terrain conclusion.
- No basin theorem.
- No terrain ranking or "best terrain" conclusion.
- No `M(C,t)`.
- No formal admission.
- No bridge/axis-level claim.
- No all-64 S6 overlay claim.

## Named Caveats

1. Untracked packet caveat: `system_v6/sims/ratchet_s6_terrain_sweep_v0/` is untracked in the working tree at audit time. The packet can pass local checks but is not itself committed repo truth.
2. Wizard route caveat: no native Codex subagent/council receipts were produced; route status is partial local audit.
3. Validator-write caveat: the packet validator was imported and run in memory to respect the one-file write constraint; its CLI write path was deliberately not invoked.
4. Anti-collapse caveat: indistinguishability is only on the declared leakage/survival/gap probe family. Signed/vector-valued orientation probes remain open.
5. Julia caveat: the Julia leg is real result evidence with Z3.jl load-bearing rows, but this audit did not rerun the Julia script because its `main()` writes the Julia result JSON. The existing Julia source and result were inspected, and the Python envelope's in-memory recomputation matched the Julia result values in the result payload.

## Block K

Gates cited: AGENTS.md sim-mode Max Assembly contract; `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`; `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`; `system_v5/docs/LEGO_SIM_CONTRACT.md`; `system_v6/receipts/audit_bar_calibration_20260610.md`; packet validator; source-backed three-engine result validator.

Admission decisions: local audit accepts the packet at `passes local rerun` / `scratch_diagnostic` ceiling; formal admission blocked; multi-shell/basin/ranking/bridge/axis claims blocked.

Narrative substitutions intercepted: "zero survivors" was checked against the committed single-terrain fixed-point exclusion instead of accepted as headline prose; "none compatible" was checked from computed `z_dot` and purity rows; anti-collapse was kept to the declared probe columns.

Worker claims verified: builder claims Q1-Q8 checked against result files, committed parents, in-memory validator, in-memory builder recomputation, independent SymPy/hash recomputation, and source-backed repo validator.

Worker claims not verified: no independent Julia rerun due one-file write constraint; no Wizard Max Assembly subagent topology.

Status label changes to registry: none.

Blocked actions: no git add, no commit, no result rewrite, no validator-result rewrite, no promotion/admission wording.
