# Build card - stage_lifted_spinor_shell_n4_v0

Status: builder packet, not an audit verdict.

Ceiling: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Inputs

- Template lineage: committed `system_v6/sims/stage_lifted_spinor_shell_n3_v0/` source/results and `audit_verdict.md` hardening addendum.
- Spec receipts:
  - `system_v6/receipts/lifted_ladder_spec_20260610.md`
  - `system_v6/receipts/geometry_sim_program_canonical_20260610.md`
- S5/S6 leakage lineage:
  - `system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json`
  - `system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json`

## Built Artifacts

- `stage_lifted_spinor_shell_n4_v0_julia.jl`
- `stage_lifted_spinor_shell_n4_v0_jax.py`
- `stage_lifted_spinor_shell_n4_v0_pytorch.py`
- `stage_lifted_spinor_shell_n4_v0_envelope.py`
- `results/stage_lifted_spinor_shell_n4_v0_julia_results.json`
- `results/stage_lifted_spinor_shell_n4_v0_jax_results.json`
- `results/stage_lifted_spinor_shell_n4_v0_pytorch_results.json`
- `results/stage_lifted_spinor_shell_n4_v0_envelope_results.json`

## Builder Facts

- Four-site shell support was constructed as a real support object with 4 nodes, 5 tensor/path edges, and 2 filled shell faces.
- Density quotient row uses the `d=16` carrier and a 256-effect finite IC frame; all three legs report `frame_rank=256`.
- Entropy rows are computed in natural-log units. GHZ4 reports `S(A)=ln(2)` across proper bipartitions; W4 single-site entropy reports `0.562335144619`.
- Nesting rows are computed, not asserted: `Tr_one(GHZ4)` is a rank-2 classical mixture, while `Tr_one(W4)` matches `3/4 |W3><W3| + 1/4 |000><000|`.
- Cl(8) anchor row constructs a 9-element anticommuting family on `C^16` and records chirality split `8+8`.
- Shell leakage derives `z_dot=e_z^T(A*r_eta+b)` from exported S5 `A,b` rows and records the S6 class taxonomy.
- Mutation controls are full rerun-style controls in the packet rows: shell-only, no-face, duplicate-eta, collapsed-shell, density-only collapse, wrong shell coordinate, hardcoded-zero leakage, carrier mismatch, matrix-associator overclaim, and GHZ/W nesting tripwires.

## Fresh Commands

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
```

Result: `ok=True install_state=stable_observed`.

```text
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_jax.py
```

Result: `all_pass=true`.

```text
env GEOMSTATS_BACKEND=pytorch NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_pytorch.py
```

Result: `all_pass=true`.

```text
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_julia.jl
```

Result: `all_pass=true`.

```text
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_envelope.py
```

Result: `all_pass=true`, `max_divergence=0.0`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_envelope_results.json
```

Result: `{"ok": true}`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_envelope_results.json
```

Result: `{"ok": true}`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_jax.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_pytorch.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_julia.jl
```

Result: no violations.

## Scalar Agreement

The envelope reports `max_divergence=0.0` across Julia, JAX, and PyTorch for:

- `support_node_count=4`
- `support_edge_count=5`
- `support_face_count=2`
- `GHZ_A_B_I=1.38629436112`
- `GHZ_A_B_conditional=-0.69314718056`
- `order_gap_TO=2.0`
- `bracketing_path_gap=1.0`
- `matrix_associator_norm=0.0`
- `aggregate_leakage=-0.007193697444`
- `ghz_non_nesting_distance=0.707106781187`

## Boundary

This packet is a scratch diagnostic build receipt only. It is not an audit verdict, stage closure, canonical geometry, formal admission, bridge/axis admission, physics claim, or trend claim across the ladder.
