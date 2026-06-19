# Build card - stage_lifted_spinor_shell_n5_v0

Status: builder packet, not an audit verdict.

Ceiling: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Inputs

- Template lineage: committed `system_v6/sims/stage_lifted_spinor_shell_n4_v0/` source/results and `audit_verdict.md` hardening addendum.
- Spec receipts:
  - `system_v6/receipts/lifted_ladder_spec_20260610.md`
  - `system_v6/receipts/geometry_sim_program_canonical_20260610.md`
- S5/S6 leakage lineage:
  - `system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json`
  - `system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json`

## Built Artifacts

- `stage_lifted_spinor_shell_n5_v0_julia.jl`
- `stage_lifted_spinor_shell_n5_v0_jax.py`
- `stage_lifted_spinor_shell_n5_v0_pytorch.py`
- `stage_lifted_spinor_shell_n5_v0_envelope.py`
- `results/stage_lifted_spinor_shell_n5_v0_julia_results.json`
- `results/stage_lifted_spinor_shell_n5_v0_jax_results.json`
- `results/stage_lifted_spinor_shell_n5_v0_pytorch_results.json`
- `results/stage_lifted_spinor_shell_n5_v0_envelope_results.json`

## Builder Facts

- Five-site shell support was constructed as a real support object with 5 nodes, 7 tensor/path edges, and 3 filled shell faces.
- Density quotient row uses the `d=32` carrier and a 1024-effect finite IC frame; all three legs report `frame_rank=1024`.
- Entropy rows are computed in natural-log units. GHZ5 reports `S(A)=ln(2)` across proper bipartitions; W5 single-site entropy reports `0.500402423538`.
- Nesting rows are computed, not asserted: `Tr_one(GHZ5)` is a rank-2 classical mixture, while `Tr_one(W5)` matches `4/5 |W4><W4| + 1/5 |0000><0000|`.
- Separable and permuted-weight W controls are emitted as failing controls in all three legs.
- Cl(10) anchor row constructs an 11-element anticommuting family on `C^32` and records chirality split `16+16`.
- The Cl(10) maximality receipt is stored under `rows.P6_order_gaps.Cl10_anchor.maximality_receipt`. Direct 1023-vertex branch-and-bound was infeasible for the build turn, so the packet stores an exact finite symplectic-rank certificate: the 11-element Jordan-Wigner witness is explicit, and `rank(K_12)=12 > 2n=10` excludes a 12-element family. JAX and PyTorch record z3/cvc5 rank-bound checks as `unsat`; Julia records the same exact theorem witness and points to the Python solver mirrors.
- Shell leakage derives `z_dot=e_z^T(A*r_eta+b)` from exported S5 `A,b` rows and records S6 class taxonomy with lineage path/hash/pin fields.
- Mutation controls are full rerun-style controls in the packet rows: shell-only, no-face, duplicate-eta, collapsed-shell, density-only collapse, wrong shell coordinate, hardcoded-zero leakage, carrier mismatch, matrix-associator overclaim, GHZ nesting, W nesting, separable W, and permuted-weight W controls.
- G1, G2, G3, G6, and G8 machinery from n=4 hardening is baked in from the start.

## Carried Open Checks

- G4 remains open: no separately named static network-level shell coordinate is closed here.
- G5 remains open: raw-object bracketing SMT belongs to separate `geo_bracketing_smt_lifted_v0`; this packet keeps bracketing numeric/symbolic only.
- G7 remains open: GHZ/W density and entropy rows remain named carrier-state rows with shell-placement receipts, not coordinate-parameterized state families.

## Fresh Commands

```text
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n5_v0/stage_lifted_spinor_shell_n5_v0_jax.py
```

Result: `all_pass=true`.

```text
env GEOMSTATS_BACKEND=pytorch NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n5_v0/stage_lifted_spinor_shell_n5_v0_pytorch.py
```

Result: `all_pass=true`.

```text
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/stage_lifted_spinor_shell_n5_v0/stage_lifted_spinor_shell_n5_v0_julia.jl
```

Result: `all_pass=true`.

```text
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n5_v0/stage_lifted_spinor_shell_n5_v0_envelope.py
```

Result: `all_pass=true`, `max_divergence=0.0`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n5_v0/stage_lifted_spinor_shell_n5_v0_jax.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n5_v0/stage_lifted_spinor_shell_n5_v0_pytorch.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n5_v0/stage_lifted_spinor_shell_n5_v0_julia.jl
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/stage_lifted_spinor_shell_n5_v0/results/stage_lifted_spinor_shell_n5_v0_envelope_results.json
```

Result: `{"ok": true}`.

## Scalar Agreement

The three leg results agree exactly on:

- `support_node_count=5`
- `support_edge_count=7`
- `support_face_count=3`
- `GHZ_A_B_I=1.38629436112`
- `GHZ_A_B_conditional=-0.69314718056`
- `order_gap_TO=2.0`
- `bracketing_path_gap=0.894427191`
- `matrix_associator_norm=0.0`
- `aggregate_leakage=-0.02436752262`
- `ghz_non_nesting_distance=0.707106781187`

## Boundary

This packet is a scratch diagnostic build receipt only. It is not an audit verdict, stage closure, canonical geometry, formal admission, bridge/axis admission, physics claim, or trend claim across the ladder.
