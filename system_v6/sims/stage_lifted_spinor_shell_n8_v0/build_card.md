# Build card - stage_lifted_spinor_shell_n8_v0

Status: builder packet, not an audit verdict.

Ceiling: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Inputs

- Template lineage: committed `system_v6/sims/stage_lifted_spinor_shell_n7_v0/` source/results plus `build_card.md` and `audit_verdict.md`, including carried G1/G2/G3/G6/G8/G10/G11 patterns and the n=7 G13 wording rule.
- Spec receipts:
  - `system_v6/receipts/lifted_ladder_spec_20260610.md`
  - `system_v6/receipts/geometry_sim_program_canonical_20260610.md`
- S5/S6 leakage lineage:
  - `system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json`
  - `system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json`

## Built Artifacts

- `stage_lifted_spinor_shell_n8_v0_julia.jl`
- `stage_lifted_spinor_shell_n8_v0_jax.py`
- `stage_lifted_spinor_shell_n8_v0_pytorch.py`
- `stage_lifted_spinor_shell_n8_v0_envelope.py`
- `results/stage_lifted_spinor_shell_n8_v0_julia_results.json`
- `results/stage_lifted_spinor_shell_n8_v0_jax_results.json`
- `results/stage_lifted_spinor_shell_n8_v0_pytorch_results.json`
- `results/stage_lifted_spinor_shell_n8_v0_envelope_results.json`

## Builder Facts

- Eight-site shell support was constructed as a real support object with 8 nodes, 16 tensor/path edges, and 6 filled shell faces: `f012`, `f123`, `f234`, `f345`, `f456`, and `f567`.
- Density quotient row uses the `d=256` carrier and a finite IC frame with `d^2=65536` effects and `frame_rank=65536`.
- The full `65536 x 65536` Gram/rank matrix was not materialized. The packet stores the exact certified Hermitian matrix-unit rank argument: 256 diagonal projectors plus 32640 real-symmetric and 32640 imaginary-antisymmetric off-diagonal pair effects, totaling 65536 linearly independent Hermitian directions.
- Entropy rows are computed in natural-log units. GHZ8 stores all 254 nonempty proper bipartition cuts exhaustively, with every `S(A)=ln(2)`.
- W8 single-site entropy is computed as `-(7/8)ln(7/8)-(1/8)ln(1/8)=0.376770161256`.
- `S(A|B)`, `I(A:B)`, and `I_c` rows are recomputed on the 8-qubit carrier for the representative named cuts, while the GHZ all-cut table stores the full 254-cut `S(A)` anchor.
- Nesting rows are computed, not asserted: `Tr_one(GHZ8)` is a rank-2 classical mixture, while `Tr_one(W8)` matches `7/8 |W7><W7| + 1/8 |0000000><0000000|`.
- Separable and permuted-weight W controls are emitted as failing controls in all three legs.
- Cl(16) anchor row constructs a 17-element anticommuting family on `C^256` and records chirality split `128+128`.
- The Cl(16) maximality receipt is stored under `rows.P6_order_gaps.Cl16_anchor.maximality_receipt`. It uses the finite symplectic-rank certificate pattern: explicit 17-Pauli witness, all 136 pairs verified, `rank(K_17)=16` admissible in `F_2^16`, and `rank(K_18)=18>16` excludes an 18-element family. JAX and PyTorch record z3/cvc5 rank-bound checks as `unsat`; Julia records the same exact theorem witness and points to the Python solver mirrors.
- Julia does not claim a materialized `CliffordAlgebras.CliffordAlgebra(16,0)` package object. A fresh materialization attempt was terminated after about 7m14s at roughly 1.3GB RSS while inside that constructor, so the Julia leg labels this as a certificate route; JAX/PyTorch still materialize the explicit 256x256 Jordan-Wigner gamma/chirality rows.
- Boundary-stress rows record wall-clock and max RSS telemetry for support, density/IC, exhaustive GHZ8 cuts, Cl(16)/order/bracketing, S5/S6 leakage, and nesting boundary rows. Certificate-only rows are labeled rather than silently downgraded.
- Shell leakage derives `z_dot=e_z^T(A*r_eta+b)` from exported S5 `A,b` rows and records S6 class taxonomy with lineage path/hash/pin fields.
- Mutation controls are full-rerun-style controls in the packet rows: shell-only, no-face, duplicate-eta, collapsed-shell, density-only collapse, wrong shell coordinate, hardcoded-zero leakage, carrier mismatch, matrix-associator overclaim, GHZ nesting, W nesting, separable W, and permuted-weight W controls.
- G1, G2, G3, G6-pattern, G8 one-to-one function-level `tool_calls`, G10 exhaustive cuts, and G11 prose-matches-computed-objects are carried forward from the start.

## Carried Open Checks

- G4-at-n8 remains open and is noted, not closed.
- G5-at-n8 remains open: raw-object SMT bracketing belongs to the separate `geo_bracketing_smt_lifted_v0` packet; this packet keeps the bracketing row numeric.
- G7-lifted remains open: GHZ/W density and entropy rows remain named carrier-state rows with shell-placement receipts, not coordinate-parameterized lifted state families.
- G13-wording-rule is enforced: load-bearing `tool_calls` descriptions avoid the banned n=7 wording and describe computed mathematical objects.

## Fresh Commands

```text
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier -e 'include("system_v6/sims/stage_lifted_spinor_shell_n8_v0/stage_lifted_spinor_shell_n8_v0_julia.jl"); println("julia_parse_ok")'
```

Result: wrote `stage_lifted_spinor_shell_n8_v0_julia_results.json`, `all_pass=true`.

Boundary note: a prior Julia `CliffordAlgebras.CliffordAlgebra(16,0)` package-object materialization attempt was terminated after about 7m14s and is not claimed as materialized. The final Julia run uses the explicit Pauli/GF(2) certificate route and records that boundary.

```text
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n8_v0/stage_lifted_spinor_shell_n8_v0_jax.py
```

Result: `all_pass=true`.

```text
env GEOMSTATS_BACKEND=pytorch NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n8_v0/stage_lifted_spinor_shell_n8_v0_pytorch.py
```

Result: `all_pass=true`.

```text
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n8_v0/stage_lifted_spinor_shell_n8_v0_envelope.py
```

Result: `all_pass=true`, `max_divergence=0.0`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n8_v0/stage_lifted_spinor_shell_n8_v0_jax.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n8_v0/stage_lifted_spinor_shell_n8_v0_pytorch.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n8_v0/stage_lifted_spinor_shell_n8_v0_julia.jl
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/stage_lifted_spinor_shell_n8_v0/results/stage_lifted_spinor_shell_n8_v0_envelope_results.json
```

Result: `{"ok": true}`.

## Scalar Agreement

The three leg results agree exactly on:

- `support_node_count=8`
- `support_edge_count=16`
- `support_face_count=6`
- `GHZ_A_B_I=1.38629436112`
- `GHZ_A_B_conditional=-0.69314718056`
- `order_gap_TO=2.0`
- `bracketing_path_gap=0.707106781187`
- `matrix_associator_norm=0.0`
- `aggregate_leakage=-0.048510637939`
- `ghz_non_nesting_distance=0.707106781187`

## Boundary Stress Highlights

- JAX: exhaustive GHZ8 cuts `0.604745209217s`; Cl(16)/order/bracketing `1.875389959197s`; S5/S6 leakage `9.109981291927s`.
- PyTorch: exhaustive GHZ8 cuts `70.162239000201s`; Cl(16)/order/bracketing `0.955930375028s`; S5/S6 leakage `9.473084582947s`.
- Julia final certificate-route run: support object `32.863127334s`; exhaustive GHZ8 cuts `4.842109375s`; density/IC `6.461164875s`; Cl(16)/order/bracketing `10.779114542s`; S5/S6 leakage `6.404932542s`.
- Julia package-object boundary: `CliffordAlgebras.CliffordAlgebra(16,0)` was attempted separately, then terminated at about `7m14s` and roughly `1.3GB` RSS; no package Cl(16,0) object is claimed.

## Boundary

This packet is a scratch diagnostic build receipt only. It is not an audit verdict, stage closure, canonical geometry, formal admission, bridge/axis admission, physics claim, or trend claim across the ladder.
