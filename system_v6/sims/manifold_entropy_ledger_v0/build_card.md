# BUILD CARD: manifold_entropy_ledger_v0

Object: `manifold_entropy_ledger_v0`

Claim under test: compute a like-for-like entropy ledger across the committed Hopf/manifold layers, with entropy notions typed explicitly instead of merging differential, von Neumann, and counting entropies.

Ceiling: `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Mode: `julia_canon_plus_jax_diagnostic`. Julia is the independent symbolic/Manifolds/Z3 leg. The `jax` slot is a Python exact sidecar using `sympy`, `z3`, and `cvc5`. PyTorch is not scoped because this packet has no graph, network, or autograd claim path.

Write scope:

- `system_v6/sims/manifold_entropy_ledger_v0/`
- `system_v6/sims/manifold_entropy_ledger_v0/results/`

No `audit_verdict.md` is part of this build.

Parents cited as committed/hash-bound inputs:

- `geo_disintegration_machinery_v0`
- `geo_nested_disintegration_v0`
- `geo_union_rule_k_leaves_v0`
- `geo_s2_connection_flux_foliation_v0`
- `geo_s6_s7_mode_sweep_v0`
- `geo_s7_discrete_refinement_v0`
- `ratchet_s1_single_shell_pilot_v0`
- `ratchet_s2_three_shell_chain_v0`
- `ratchet_s6_terrain_operator_shell_v0`
- `compression_flow_radiated_record_v0`
- `stage_lifted_spinor_shell_n3_v0` through `stage_lifted_spinor_shell_n8_v0`
- `geo_s1_scaling_stress_678q_exact_v0`

Required ledger rows:

1. Measure-level differential entropy, base `e`:
   - `h(S^3)=log(2*pi^2)` under round Riemannian volume.
   - `h(eta)=1-log(2)` for density `sin(2eta)` on `[0,pi/2]`.
   - `h(T_eta)=log(2*pi^2*sin(2eta))` under induced physical area measure.
   - Chain rule: `h(S^3)=h(eta)+E[h(T_eta)]`.
   - Finite k-leaf union mixture entropy: `H(weights)+sum_i w_i h(T_eta_i)`.

2. Conditioning deltas:
   - Free `S^3` to a fixed leaf is singular. State the honest infinite differential drop; compute the symmetric band-limit row and its `epsilon -> 0` behavior.
   - Lens quotient drop is `log(|G|)`.
   - Terrain restriction uses the committed S6/S7 mode sweep row counts as counting entropy: `log(40)-log(16)=log(5/2)`.

3. Carrier-level anchors:
   - Cite committed vN entropy rows from lifted-ladder rungs `n=3..8`.
   - Do not recompute those carrier values in this packet.
   - State the entropy type table: differential vs vN vs lattice/counting.

4. Cross-layer meeting point:
   - At a conditioned leaf, compute the differential leaf entropy and cite the carrier vN row placed there.
   - Keep the types separate; if a product bookkeeping convention is used, the combined value is explicitly `h_leaf + S_vN`.

Controls:

- Natural-log vs bit-log mismatch is detected.
- Chain rule fails with a wrong flat eta marginal.
- Lens quotient drop fails when the wrong group order is used.
- `z3` and `cvc5` prove the chain coefficient identity and reject the erased conditional term.

Acceptance:

- Fresh Python leg exits 0 and writes `results/manifold_entropy_ledger_v0_jax_results.json`.
- Fresh Julia leg exits 0 and writes `results/manifold_entropy_ledger_v0_julia_results.json`.
- Fresh envelope exits 0 and writes `results/manifold_entropy_ledger_v0_envelope_results.json`.
- `scripts/validate_three_engine_sim_result.py` returns `ok:true` for the declared mode.
- Packet validator returns `ok:true`.
- `tool_calls` are one-to-one with `claim_path_tools`.
