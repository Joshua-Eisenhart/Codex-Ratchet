# Build card - stage_lifted_spinor_shell_n7_v0

Status: builder packet, not an audit verdict.

Ceiling: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Inputs

- Template lineage: committed `system_v6/sims/stage_lifted_spinor_shell_n6_v0/` source/results plus `build_card.md` and `audit_verdict.md`, including the hardening addendum that closed n=6 G10/G11.
- Spec receipts:
  - `system_v6/receipts/lifted_ladder_spec_20260610.md`
  - `system_v6/receipts/geometry_sim_program_canonical_20260610.md`
- S5/S6 leakage lineage:
  - `system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json`
  - `system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json`

## Built Artifacts

- `stage_lifted_spinor_shell_n7_v0_julia.jl`
- `stage_lifted_spinor_shell_n7_v0_jax.py`
- `stage_lifted_spinor_shell_n7_v0_pytorch.py`
- `stage_lifted_spinor_shell_n7_v0_envelope.py`
- `results/stage_lifted_spinor_shell_n7_v0_julia_results.json`
- `results/stage_lifted_spinor_shell_n7_v0_jax_results.json`
- `results/stage_lifted_spinor_shell_n7_v0_pytorch_results.json`
- `results/stage_lifted_spinor_shell_n7_v0_envelope_results.json`

## Builder Facts

- Seven-site shell support was constructed as a real support object with 7 nodes, 14 tensor/path edges, and 5 filled shell faces: `f012`, `f123`, `f234`, `f345`, and `f456`.
- Density quotient row uses the `d=128` carrier and a finite IC frame with `d^2=16384` effects and `frame_rank=16384`.
- The full `16384 x 16384` Gram/rank matrix was not materialized. The packet stores the exact certified Hermitian matrix-unit rank argument: 128 diagonal projectors plus 8128 real-symmetric and 8128 imaginary-antisymmetric off-diagonal pair effects, totaling 16384 linearly independent Hermitian directions.
- Entropy rows are computed in natural-log units. GHZ7 stores all 126 nonempty proper bipartition cuts exhaustively, with every `S(A)=ln(2)`.
- W7 single-site entropy is computed as `-(6/7)ln(6/7)-(1/7)ln(1/7)=0.410116318288`.
- `S(A|B)`, `I(A:B)`, and `I_c` rows are recomputed on the 7-qubit carrier for the representative named cuts, while the GHZ all-cut table stores the full 126-cut `S(A)` anchor.
- Nesting rows are computed, not asserted: `Tr_one(GHZ7)` is a rank-2 classical mixture, while `Tr_one(W7)` matches `6/7 |W6><W6| + 1/7 |000000><000000|`.
- Separable and permuted-weight W controls are emitted as failing controls in all three legs.
- Cl(14) anchor row constructs a 15-element anticommuting family on `C^128` and records chirality split `64+64`.
- The Cl(14) maximality receipt is stored under `rows.P6_order_gaps.Cl14_anchor.maximality_receipt`. It uses the finite symplectic-rank certificate pattern: explicit 15-Pauli witness, all 105 pairs verified, `rank(K_15)=14` admissible in `F_2^14`, and `rank(K_16)=16>14` excludes a 16-element family. JAX and PyTorch record z3/cvc5 rank-bound checks as `unsat`; Julia records the same exact theorem witness and points to the Python solver mirrors.
- Shell leakage derives `z_dot=e_z^T(A*r_eta+b)` from exported S5 `A,b` rows and records S6 class taxonomy with lineage path/hash/pin fields.
- Mutation controls are full-rerun-style controls in the packet rows: shell-only, no-face, duplicate-eta, collapsed-shell, density-only collapse, wrong shell coordinate, hardcoded-zero leakage, carrier mismatch, matrix-associator overclaim, GHZ nesting, W nesting, separable W, and permuted-weight W controls.
- G1, G2, G3, G6-pattern, G8 one-to-one function-level `tool_calls`, G10 exhaustive cuts, and G11 prose-matches-computed-objects are carried forward from the start.

## Carried Open Checks

- G4-at-n7 remains open and is noted, not closed.
- G5-at-n7 remains open: raw-object SMT bracketing belongs to the separate `geo_bracketing_smt_lifted_v0` packet; this packet keeps the bracketing row numeric.
- G7-lifted remains open: GHZ/W density and entropy rows remain named carrier-state rows with shell-placement receipts, not coordinate-parameterized lifted state families.

## Fresh Commands

```text
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier -e 'include("system_v6/sims/stage_lifted_spinor_shell_n7_v0/stage_lifted_spinor_shell_n7_v0_julia.jl"); println("julia_parse_ok")'
```

Result: wrote `stage_lifted_spinor_shell_n7_v0_julia_results.json`, `all_pass=true`.

```text
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n7_v0/stage_lifted_spinor_shell_n7_v0_jax.py
```

Result: `all_pass=true`.

```text
env GEOMSTATS_BACKEND=pytorch NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n7_v0/stage_lifted_spinor_shell_n7_v0_pytorch.py
```

Result: `all_pass=true`.

```text
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n7_v0/stage_lifted_spinor_shell_n7_v0_envelope.py
```

Result: `all_pass=true`, `max_divergence=0.0`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n7_v0/stage_lifted_spinor_shell_n7_v0_jax.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n7_v0/stage_lifted_spinor_shell_n7_v0_pytorch.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n7_v0/stage_lifted_spinor_shell_n7_v0_julia.jl
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/stage_lifted_spinor_shell_n7_v0/results/stage_lifted_spinor_shell_n7_v0_envelope_results.json
```

Result: `{"ok": true}`.

## Scalar Agreement

The three leg results agree exactly on:

- `support_node_count=7`
- `support_edge_count=14`
- `support_face_count=5`
- `GHZ_A_B_I=1.38629436112`
- `GHZ_A_B_conditional=-0.69314718056`
- `order_gap_TO=2.0`
- `bracketing_path_gap=0.755928946018`
- `matrix_associator_norm=0.0`
- `aggregate_leakage=-0.042748922622`
- `ghz_non_nesting_distance=0.707106781187`

## Boundary

This packet is a scratch diagnostic build receipt only. It is not an audit verdict, stage closure, canonical geometry, formal admission, bridge/axis admission, physics claim, or trend claim across the ladder.
