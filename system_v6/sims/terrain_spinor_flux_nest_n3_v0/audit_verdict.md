# Fresh Audit Verdict: terrain_spinor_flux_nest_n3_v0

Auditor: codex2 cross-backend audit
Date: 2026-06-11
Scope: read-only audit of `terrain_spinor_flux_nest_n3_v0`; this file is the only written artifact.
Calibration: `system_v6/receipts/audit_bar_calibration_20260610.md`.

## Verdict

VERDICT: GENUINE-WITH-CAVEATS.

The n=3 integration packet is a real scratch-diagnostic integration artifact: it combines the committed C^8 three-qubit carrier, terrain-dependent z-row edge couplings, flux/current rows, finite k-leaf conditioning, and three-runtime recomputation into one packet. It is not just a label join.

The ceiling remains:

- `classification: scratch_diagnostic`
- `promotion_allowed: false`
- `formal_admission_allowed: false`
- n=3 one-rung integration only
- no universal mirror law, no n>3 rung, no bridge/axis/whole-manifold claim

Named caveats:

- G1: The Z3/cvc5/Julia-Z3 continuity proofs are overclaimed as load-bearing derivations. They check equality over integer-scaled row values after `network_population_flow_scaled` is overwritten to the identity target. The computed continuity row is real, but the solver layer is a row-consistency/erased-flip wrapper, not an in-solver derivation from edge-current formulas.
- G2: The `decoupling_edges_recovers_rung2_per_site` control verifies exact `z_dot` agreement, but `byte_consistent_on_parent_exact_rows: true` is stronger than the check. The parent rows and computed rows have different schemas and different row hashes.
- G3: The `dropping_terrain_recovers_bare_network` control checks carrier/support counts and asserts `terrain_A_zero`, `terrain_b_zero`, and `couplings_zero`; it does not recompute a terrain-zero edge-current network and compare a committed bare-network current row.
- G4: The child packet reconstructs the C^8 carrier from committed site spinors. That is admissible here, but it is not a copied parent state-vector row. The parent does contain density/entropy/order-gap network evidence.

## Audit Commands And Fresh Checks

Fresh checks run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/terrain_spinor_flux_nest_n3_v0/results/terrain_spinor_flux_nest_n3_v0_envelope_results.json
```

Result: `{"ok": true, "result_json": "system_v6/sims/terrain_spinor_flux_nest_n3_v0/results/terrain_spinor_flux_nest_n3_v0_envelope_results.json"}`.

I did not rerun `validate_terrain_spinor_flux_nest_n3_v0.py` because it writes `terrain_spinor_flux_nest_n3_v0_validator_results.json`, outside the allowed write scope. The committed validator result already present is green: `ok: true`, `errors: []`, generated `2026-06-11T07:55:32Z`.

The packet directory is currently untracked in this worktree:

```text
?? system_v6/sims/terrain_spinor_flux_nest_n3_v0/
```

That does not invalidate the audit of the artifact contents, but it blocks any claim that this packet itself is already a committed artifact.

## Q1 - Carrier Real

Status: GENUINE-WITH-CAVEAT G4.

Source:

- `terrain_spinor_flux_nest_n3_v0_common.py:146-165` builds an 8-entry state vector from the three committed site spinors and marks `not_support_graph_only: True`.
- `terrain_spinor_flux_nest_n3_v0_common.py:628-633` loads `stage_lifted_spinor_shell_n3_v0_jax`, consumes `rows.P2_support_object.sites`, and builds the carrier from those sites.
- The parent `stage_lifted_spinor_shell_n3_v0_jax_results.json` contains `P3_density_quotient`, `P5_entropy`, `P6_order_gaps`, `mps_mirror`, and support topology rows.

Recomputation:

- carrier dimension: `8`
- carrier norm: `1.0`
- state row sha over reconstructed `state_vector_re_im`: `74ee8ad09564848f19e89be7ca16427cb06c8bf66c431bb0fb07d5a9a702f23b`
- probabilities sha: `41c28819fd301599c0dab8ea4048dd27655caf5b5d2e517894adc94f90987a90`

Parent lineage hash check: all seven parent hashes match the envelope, and all seven commit hints exist as Git commits:

```text
stage_lifted_spinor_shell_n3_v0 OK 8ae7744db3336104166e882b79159d51c94cfadf44e8261a17a9866c87eeebdc
terrain_spinor_shell_nest_v0 OK 46245b96ec8af6787886c0c322c0c00cbbef87e1e75f1c3aac72c286bbc7b46d
geo_s5_terrain_flows_v0 OK 8c5474786973f067e55c0200392c1a27cbe8bf5d71cfd632b507d066b6cc9b1e
ratchet_s2_two_shell_flux_v0 OK 1c37955b266d7245efb3dd23e50fd650c131823b300a6ed3a80dd6fa2e6eb9dd
geo_disintegration_machinery_v0 OK ef95598ac9f7117107cb160826c50ebe8111eec0af60bcbe2b9f8e24d24aa1b6
geo_union_rule_k_leaves_v0 OK 5f76eca08e321825ad046529c3188cfafe91e06a4b2345a8932167f876df073f
terrain_exact_mirror_finder_v0 OK 8f39bfd83253e0d847d95c268da9bb7f5d86ffb0953ede963c185bc3ee449b06
```

## Q2 - Terrain-Dependent Edge Couplings

Status: GENUINE.

Source quote:

- `PIN_SPEC` pins `edge_coupling=g_ij=abs((zdot_i+zdot_j)/2)+0.25*(abs(A_zx)+abs(A_zy)+abs(A_zz))+abs(b_z)` and names `A[2][0],A[2][1],A[2][2],b[2]` at `terrain_spinor_flux_nest_n3_v0_common.py:33-40`.
- `coupling_strength` reads `terrain_row["A"][2][0]`, `[2][1]`, `[2][2]`, and `terrain_row["b"][2]` at `terrain_spinor_flux_nest_n3_v0_common.py:240-246`.
- `network_rows` gates current and flux with `strength`: `current = strength * (p_src - p_dst)` at `terrain_spinor_flux_nest_n3_v0_common.py:266-289`.

Recomputed first edge `e01`:

- `A_zx=-2*sqrt(3)/15`, `A_zy=2*sqrt(3)/15`, `A_zz=-4/5`, `b_z=0`
- manual `g_e01 = 0.722227397487`
- packet `g_e01 = 0.722227397487`
- manual current `-0.255345945161`
- packet current `-0.255345945161`
- manual flux `-0.180556849372`
- packet flux `-0.180556849372`

Not a label join: changing the edge strengths changes computed rows. The `shuffled_couplings` control rotates strengths and changes total signed flux from `-0.692808577381` to `-0.975462198315`.

## Q3 - Flux And Continuity Row

Status: COMPUTED ROW GENUINE; SOLVER PROOF OVERCLAIMED, G1.

Source:

- Edge currents and divergences are computed at `terrain_spinor_flux_nest_n3_v0_common.py:272-305`.
- The stated identity is `network_population_flow - local_population_flow + edge_divergence_out_minus_in == 0` at `terrain_spinor_flux_nest_n3_v0_common.py:333-338`.
- The solver wrappers bind `network` and `target` from `proof_row`, then assert `network != target` at `terrain_spinor_flux_nest_n3_v0_jax.py:139-149` and `terrain_spinor_flux_nest_n3_v0_jax.py:152-167`.
- The Julia wrapper does the same at `terrain_spinor_flux_nest_n3_v0_julia.jl:199-210`.

Recomputed q0 continuity:

- local population flow: `0.364492370567`
- edge divergence out-minus-in: `-0.499549446032`
- network population flow: `0.864041816599`
- residual: `0.0`
- scaled proof row: `local=364492370567`, `edge=-499549446032`, `target=864041816599`, `network=864041816599`

Solver result:

- z3: `unsat`, erased flip: `sat`
- cvc5: `unsat`, erased flip: `sat`
- Julia-Z3: `unsat`, erased flip: `sat`

Problem: the proof row construction sets `network_population_flow_scaled` equal to `identity_target_scaled` at `terrain_spinor_flux_nest_n3_v0_common.py:314-317`. Therefore the solvers prove equality of two already-bound integers, with an erased off-by-one flip. That is not a full in-solver derivation from `g_ij`, populations, currents, and divergences. The continuity row itself is recomputed and exact within the packet's decimal scale; the solver proof should be described with the narrower claim.

## Q4 - RATCHETED Rows

Status: GENUINE.

Source:

- Conditioning rule is `w_i=sin(2*eta_i)/sum_j sin(2*eta_j)` at `terrain_spinor_flux_nest_n3_v0_common.py:225-237`.
- Conditioned edge strengths multiply by `sqrt(weights[src] * weights[dst])` at `terrain_spinor_flux_nest_n3_v0_common.py:268-269`.
- Surviving, altered, and excluded observables are named at `terrain_spinor_flux_nest_n3_v0_common.py:655-676`.

Recomputed conditioning:

- weights: `[0.292893218814, 0.414213562373, 0.292893218813]`
- weight sum: `1.0`
- e01 conditioning factor: `0.348310699749`
- e01 conditioned coupling: `0.251559530197`
- e01 conditioned current: `-0.088939724837`
- bare total absolute current: `0.735575785391`
- conditioned total absolute current: `0.242675773674`

Survive:

- `carrier_dimension_8`
- `support_edge_count_3`
- `continuity_identity`
- `density_quotient_row`

Altered:

- `edge_current_distribution`
- `total_abs_current`
- `total_signed_transport_flux`

Excluded:

- `universal_all-family_mirror`
- `naive_ambient_conditioning`
- `support_graph_only_carrier`
- `unweighted_shell_average`

## Q5 - Collapse Controls

Status: MIXED.

Control a, coupling to zero recovers rung-2 per-site terrain rows:

- Result: GENUINE for `z_dot` equality; caveat G2 for byte-consistency language.
- The code compares parent and computed `z_dot` values over required terrains at `terrain_spinor_flux_nest_n3_v0_common.py:392-404`.
- Recomputed max absolute `z_dot` error: `0.0`.
- Can fail if any recomputed terrain local `z_dot` differs from the parent row by more than `TOL`.
- Caveat: `byte_consistent_on_parent_exact_rows` is a literal true field, while parent and computed row hashes differ because schemas differ.

Control b, density quotient recovers committed n=3 ladder:

- Result: ACCEPTED AS A WEAK CONTROL.
- It checks `carrier.dimension == 8` and `carrier.norm == 1.0`, records parent density/support row hashes, and recovers support counts at `terrain_spinor_flux_nest_n3_v0_common.py:429-436`.
- Can fail if carrier dimension/norm or support counts diverge.
- It does not recompute the full parent density quotient row byte-for-byte inside the child packet.

Control c, dropping terrain recovers bare-network values:

- Result: WEAK/DECORATIVE, G3.
- The code compares `bare_values` and `stage_values` for carrier/support counts at `terrain_spinor_flux_nest_n3_v0_common.py:405-444`.
- `terrain_A_zero`, `terrain_b_zero`, and `couplings_zero` are asserted literals, not recomputed terrain-zero rows.
- Can fail only if carrier/support counts change; it would not catch a wrong zero-terrain edge-current calculation.

Additional controls:

- `permuted_etas`: flux changes from `-0.692808577381` to `-0.596215994752`.
- `shuffled_couplings`: flux changes from `-0.692808577381` to `-0.975462198315`.
- `naive_conditioning_fails`: carries the disintegration singleton failure and k-leaf equal-weight control.

## Q6 - Standard And Three-Engine Evidence

Status: GENUINE-WITH-CAVEATS G1-G3.

Schema and mode:

- `schema_version: three_engine_sim_result_v1`
- top-level `mode: RATCHETED`
- `engine_contract.mode: RATCHETED`
- `engine_contract.mode_is_field: true`
- `standard_schema_mode: FIELD`

Three-engine like-for-like divergence:

- metric: `conditioned_total_abs_current`
- Julia: `0.242675773674`
- JAX: `0.242675773674`
- PyTorch: `0.242675773674`
- max divergence: `0.0`

Julia leg:

- claim path tools: `QuantumOptics`, `ITensors`, `ITensorMPS`, `Z3`
- versions: `QuantumOptics 1.2.6`, `ITensors 0.9.30`, `ITensorMPS 0.4.1`, `Z3 1.0.4`
- `QuantumOptics.NLevelBasis/Ket/tensor/dm` returns `density_trace: 1`, `pass: true`
- `ITensors.Index/ITensor and ITensorMPS.siteinds/MPS` returns `site_count: 3`, `maxlinkdim: 1`, `pass: true`

JAX leg:

- claim path tools: `jraph`, `z3`, `cvc5`, `sympy`
- versions: `jax 0.10.1`, `jraph 0.0.6.dev0`, `z3 4.16.0`, `cvc5 1.3.3`, `sympy 1.14.0`
- `jraph.GraphsTuple nodes=3 edges=3`
- SymPy coupling receipt passes for first edge.

PyTorch leg:

- claim path tools: `torch_geometric`, `torch.func`, `sympy`
- versions: `torch 2.11.0`, `torch_geometric available`, `sympy 1.14.0`
- `torch_geometric.Data nodes=3 edges=3`
- `torch.func` Jacobian for e01: `[0.722227397487, -0.722227397487, -0.353553390593]`
- SymPy k-leaf receipt has symbolic sum defect `0`.

Other standard checks:

- one-to-one capability receipt IDs match tool call IDs.
- `pin_identical_across_legs: true`.
- seed: `2026061103`.
- no forbidden `fixture` wording found by direct `rg` scan.
- generic source-backed validator passes.

## Q7 - Closure

THE INTEGRATION ARTIFACT is earned at n=3 as a scratch-diagnostic component-marriage artifact, with caveats.

Precisely integrated:

- committed n=3 C^8 carrier from stage-lifted shell sites;
- parent terrain A,b z-row data into edge couplings;
- edge current and transport flux rows over the n=3 network;
- finite k-leaf conditioning into conditioned network observables;
- Julia/JAX/PyTorch recomputation of the same named scalar `conditioned_total_abs_current`;
- parent lineage for the k-leaf rule and family-local mirror boundary;
- can-fail shuffled-coupling and permuted-eta controls.

Still separate or overclaimed:

- full solver derivation of continuity from edge-current formulas is not integrated; current solvers check a constructed scaled row.
- zero-terrain/bare-network recovery is not a full recomputation of zero-terrain edge-current rows.
- density quotient recovery is a carrier/count/hash check, not a full child-side density quotient reproduction.
- n=4+ remains trail-by-one next work; no higher-rung or whole-manifold claim is earned.

Final classification: GENUINE-WITH-CAVEATS, ceiling `scratch_diagnostic`, promotion blocked.

## Re-Audit Addendum - Hardening Closures

Auditor: codex2 focused re-audit
Date: 2026-06-11
Scope: read-only hardening re-audit; this appended section is the only repo write.

Verdict on closures: G1 and G2 are earned; G3 is partially closed and explicitly carried; G4 is carried by name. The original earned core stands: this remains a real n=3 integration artifact, not a label join.

G1 decisive check:

- The continuity proof is now an in-solver finite-row derivation, not the earlier pre-overwritten target check. Encoding inspected in `terrain_spinor_flux_nest_n3_v0_jax.py:139-170` and `:186-226`: the solver binds `current`, `coupling`, `population_delta`, and `residual`, asserts `current * SCALE == coupling * population_delta + residual`, derives site divergence as `Sum(outgoing) - Sum(incoming)`, asserts `divergence == derived`, then proves the negated balance `network != local - divergence` is `unsat`.
- The finite values are in the proof receipt: for q0, `e01=-255345945161`, `e02=-244203500871`, outgoing sum `-499549446032`, incoming sum `0`, local `364492370567`, network `864041816599`, and `network - (local - derived)=0`.
- Independent recompute from the current envelope, using the stored finite edge-current rows rather than `identity_target_scaled`, gave `derived_divergence_scaled=-499549446032`, `rhs_local_minus_derived=864041816599`, `residual_scaled=0`, and all edge formula residuals `0`.
- Erased flip fires in all three proof routes: `z3=unsat/sat`, `cvc5=unsat/sat`, `julia_z3=unsat/sat`.

G2 check:

- The decoupling control now matches the claim exactly: exact same-schema `site_id,z_dot` agreement only. The overbroad full-row byte-consistency flag was corrected, not made genuine like-for-like: `byte_consistent_on_parent_exact_rows=false`, `full_schema_byte_comparison_claimed=false`, `parent_child_row_schema_identical=false`, while `z_dot_rows_same_schema_sha256_match=true` for all required terrains and `max_abs_z_dot_error=0.0`.

Remaining caveats:

- G3: partially closed and carried. The zero-terrain network is now mechanically recomputed with zero couplings, zero currents, zero transport flux, and continuity pass. The remaining caveat is still real and named: no committed bare-current parent row was found/compared, so this is not a parent current-row byte comparison.
- G4: carried. The C^8 carrier is reconstructed from committed parent site spinors and records reconstruction hashes; it is not a copied parent state-vector row.
- Density quotient recovery remains the earlier weak control: carrier/count/hash recovery, not a full child-side density quotient reproduction.

Byte-stability:

- Direct byte-stability against a committed pre-hardening baseline is not provable from this worktree because the packet directory is untracked. The exact non-proof values recorded by the original audit still match the current envelope: state hash `74ee8ad09564848f19e89be7ca16427cb06c8bf66c431bb0fb07d5a9a702f23b`, probability hash `41c28819fd301599c0dab8ea4048dd27655caf5b5d2e517894adc94f90987a90`, total signed transport flux `-0.692808577381`, conditioned total abs current `0.242675773674`, permuted flux `-0.596215994752`, and shuffled flux `-0.975462198315`. The hardening addendum does not itself report a full audited-row byte-stability table; it reports G1 proof-receipt changes plus caveat dispositions.

Validators:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/terrain_spinor_flux_nest_n3_v0/results/terrain_spinor_flux_nest_n3_v0_envelope_results.json
```

Result:

```text
{"ok": true, "result_json": "system_v6/sims/terrain_spinor_flux_nest_n3_v0/results/terrain_spinor_flux_nest_n3_v0_envelope_results.json"}
```

Packet-local validator was run with its result redirected to `/tmp` to preserve this read-only scope:

```text
validate_terrain_spinor_flux_nest_n3_v0.py --phase post_audit
```

Result:

```text
{"ok": true, "errors": [], "phase": "post_audit", "validator_sha256": "733002312600f0961f7d6c25a336c75d39f8a785b118d1e85ca2e553a3205a71"}
```

One-line conclusion: closures earned for G1+G2; THE INTEGRATION ARTIFACT is precisely an n=3 scratch-diagnostic integration of committed C^8 carrier/site-spinor reconstruction, terrain z-row edge couplings, flux/current continuity rows, k-leaf conditioning, and Julia/JAX/PyTorch agreement on `conditioned_total_abs_current`; still separate are copied parent state-vector provenance, committed bare-current parent-row comparison, full density-quotient reproduction, and any 4Q+/trail-by-one extension; ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, no bridge/axis/manifold/n>3 claim.
