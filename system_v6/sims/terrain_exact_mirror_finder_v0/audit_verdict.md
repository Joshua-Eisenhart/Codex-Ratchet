# Audit Verdict: terrain_exact_mirror_finder_v0

Audit date: 2026-06-11  
Auditor: codex1 cross-backend auditor  
Scope: read-only audit of codex2-built `terrain_exact_mirror_finder_v0`, except this `audit_verdict.md`.  
Wizard route truth: PARTIAL controller/tool audit only. Native Codex `spawn_agent` receipts were not available in this runtime, so no FULL Max Assembly parent/child topology is claimed.

## Executive Verdict

VERDICT: PARTIAL ACCEPT WITH NAMED CAVEATS.

The core mathematical finding survives hard audit:

- There is no single exact common affine mirror `M` for all four committed S5 L/R terrain families.
- The solve space is correctly over `O(3)`, not restricted to `SO(3)`. Both determinant branches are present in the result packet.
- `Se` and `Ne` each have the same one-parameter continuum of exact mirrors.
- `Si` also has a one-parameter continuum, but it is a different `z`-frame to `x`-frame continuum.
- `Ni` is zero-dimensional after the linear constraints and becomes a single affine solution after the `b` condition.
- The three-family exact matrix is exact for `Se/Ne/Ni`, not `Se/Ne/Si`. The prompt's `Se/Ne/Si` wording is a label drift; `Se/Ne/Si` is impossible by an inner-product obstruction.

Ceiling: `scratch_diagnostic` only. `promotion_allowed=false`; `formal_admission_allowed=false`. This verdict supports the local exact-mirror diagnostic, not a canonical geometry, bridge, physics, or admission claim.

## Fresh Commands And Result Signals

Read/validation commands run in this audit:

- Read authority: `AGENTS.md`, `CODEX.md`, `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`, `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`, `system_v5/docs/LEGO_SIM_CONTRACT.md`, and `system_v6/receipts/audit_bar_calibration_20260610.md`.
- Read Wizard v4.2 packet/manifest and compact MMM from `~/wiki/wizard/packet-v4-2-current/`.
- Read builder sources/results under `system_v6/sims/terrain_exact_mirror_finder_v0/`.
- Scratch recomputation with Makefile interpreter: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ...`.
- Generic envelope validator: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/terrain_exact_mirror_finder_v0/results/terrain_exact_mirror_finder_v0_envelope_results.json` returned `{"ok": true, ...}`.
- Source-backed envelope validator: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/terrain_exact_mirror_finder_v0/results/terrain_exact_mirror_finder_v0_envelope_results.json` returned `{"ok": true, ...}`.

I did not rerun the builder entrypoints or packet-local validator after writing this audit because those entrypoints write result files, and the packet-local validator currently asserts that `audit_verdict.md` does not exist.

## Parent Lineage

Accepted lineage from result reads:

- `geo_s5_terrain_flows_v0` committed S5 parent: `system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json`, sha256 `8c5474786973f067e55c0200392c1a27cbe8bf5d71cfd632b507d066b6cc9b1e`.
- `terrain_weyl_spinor_lr_v0` sigma_y refutation parent: commit `a706208c4`, source `system_v6/sims/terrain_weyl_spinor_lr_v0/terrain_weyl_spinor_lr_v0.py`, result `system_v6/sims/terrain_weyl_spinor_lr_v0/results/terrain_weyl_spinor_lr_v0_python_results.json`, result sha256 `a26e8c5734dcbcc0b6e88096069d5957e97a9c0811630db19d58b583c2be5312`.

The committed S5 generator table contains the eight expected rows: `Se_Funnel_L`, `Se_Cannon_R`, `Ne_Vortex_L`, `Ne_Spiral_R`, `Ni_Pit_L`, `Ni_Source_R`, `Si_Hill_L`, `Si_Citadel_R`.

## Q1: No Common Mirror

Verdict: ACCEPT, with solver-scope caveat.

The solve space is not over-restricted to `SO(3)`. The result explicitly parameterizes `O(3)`:

- `Se` and `Ne`: `{M in O(3): det(M) * M * h0 = -h0, h0=(1,1,1)/sqrt(3)}`.
- `Se` and `Ne` determinant branches:
  - proper branch: pi rotations `R(n)=2*n*n^T-I` with `n.h0=0`, `n.n=1`;
  - improper branch: Householder reflections `I-2*n*n^T` with `n.h0=0`, equivalently `det(M)=-1` and `M*h0=h0`.
- `Si`: `{M in O(3): M*e_z = det(M)*e_x}`, again with proper and improper branches.
- `Ni`: the packet records a unique affine matrix, and scratch recomputation shows the underlying linear stage has two determinant branches before affine filtering.

Scratch recomputation over the committed matrices confirms the four-way empty intersection:

- `M_Ni = [[0,-1,0],[-1,0,0],[0,0,-1]]` is exact for `Se`, `Ne`, and `Ni`.
- The same `M_Ni` fails `Si` with `max_abs_residual=0.4`.
- The `Si` canonical exact matrix `[[0,0,1],[0,1,0],[-1,0,0]]` fails `Se`, `Ne`, and `Ni`.

Solver encodings:

- Python/SymPy provides the solve-space reduction and residual coefficient extraction.
- Python/z3 and Python/cvc5 encode integer-scaled residual coefficients in basis `rational_plus_rational_times_sqrt3`.
- The all-four nonzero row is `all_four_M_Ni_erased_Si_flip_control_nonzero`: `expected=nonzero`, `nonzero_count=6`, `z3_any=sat`, `cvc5_any=sat`, `z3_zero=unsat`, `cvc5_zero=unsat`.
- The solved first-three row is `solve_space_identity_Se_Ne_Ni_M_Ni_zero`: `expected=zero`, `nonzero_count=0`, `z3_any=unsat`, `cvc5_any=unsat`, `z3_zero=sat`, `cvc5_zero=sat`.
- Julia/Z3 independently records `M_Ni_first_three_zero` with `any_nonzero_status=unsat`, `forced_zero_status=sat`, and `Si_erased_flip_control_nonzero` with `any_nonzero_status=sat`, `forced_zero_status=unsat`.

Named caveat: the SMT rows are not raw quantified SMT over arbitrary symbolic `O(3)` matrix variables. They certify the coefficient rows after the symbolic `O(3)` solve-space reduction. That is acceptable here because the reduction was separately checked, but it must not be described as three independent raw O(3) solvers.

## Q2: Per-Family Structure

Verdict: ACCEPT, with one corrected wording detail.

`Se` recomputation:

- I parameterized `n = c*(1,-1,0)/sqrt(2) + s*(1,1,-2)/sqrt(6)` with `c^2+s^2=1`.
- For both `R(n)=2*n*n^T-I` and `H(n)=I-2*n*n^T`, every `Se` affine residual reduces to a multiple of `c^2+s^2-1`.
- This is a one-parameter circle in the plane perpendicular to `h0`. Geometrically: an axis family in `h0^perp`, with a proper pi-rotation branch and an improper Householder branch.

`Ne` has the same `O(3)` rule and same one-parameter continuum as `Se`.

`Si` has a one-parameter continuum, but not the `h0^perp` continuum. Its rule is `M*e_z = det(M)*e_x`, i.e. a frame-axis family mapping the `z` terrain frame to the `x` terrain frame.

`Ni` is zero-dimensional in the affine solve: one matrix,

```text
M_Ni = [[0,-1,0],
        [-1,0,0],
        [0,0,-1]]
```

It is discrete and nonempty, not empty.

## Q3: Ni Mechanism

Verdict: ACCEPT WITH SHARPENED MECHANISM.

The builder's high-level statement that `Ni` is special because it is the only family with nonzero affine shift is directionally right, but the precise mechanism is:

1. The `Ni` linear part already collapses the continuum to two discrete O(3) mirrors.
2. The affine condition kills one of those two mirrors and selects the unique proper branch.

Scratch recomputation:

- Linear-only branch:
  - `M = [[0,1,0],[1,0,0],[0,0,1]]`
  - `det=-1`
  - `A_exact=true`
  - `affine_exact=false`
  - `b` residual is `[0,0,1]`
  - max affine residual is `1.0`
- Affine surviving branch:
  - `M = [[0,-1,0],[-1,0,0],[0,0,-1]]`
  - `det=1`
  - `A_exact=true`
  - `affine_exact=true`
  - `b` residual is `[0,0,0]`

So the affine shift does not kill all linear mirrors. It kills the improper `z`-fixed linear mirror and leaves the proper pi rotation.

## Q4: Three-Of-Four M

Verdict: ACCEPT, correcting the family label.

The exact three-family map exists for `Se/Ne/Ni`, not for `Se/Ne/Si`.

Explicit matrix:

```text
M_Ni = [[0,-1,0],
        [-1,0,0],
        [0,0,-1]]
```

Geometry:

- `det(M_Ni)=1`.
- Axis/angle: pi rotation about `(1,-1,0)/sqrt(2)`.
- It sends the engine axis `h0=(1,1,1)/sqrt(3)` to `-h0`.

Fresh residuals:

- `Se`: exact, max residual `0.0`.
- `Ne`: exact, max residual `0.0`.
- `Ni`: exact, max residual `0.0`.
- `Si`: not exact, max residual `0.4`.

Correction to the prompt's `Se/Ne/Si` phrase: there is no `Se/Ne/Si` common exact mirror. Reason: `Se/Ne` require `M h0 = -det(M) h0`, while `Si` requires `M e_z = det(M) e_x`. Orthogonality would preserve `<h0,e_z>=1/sqrt(3)`, but the two rules send it to `<-det(M)h0, det(M)e_x> = -1/sqrt(3)`. I checked this dot-obstruction as an integer contradiction (`1=-1`) in z3 and cvc5; both returned `unsat`.

## Q5: Controls

Verdict: ACCEPT.

Sigma_y anchor:

- `sigma_y = diag(-1,1,-1)` fails all four families.
- Fresh residuals match the committed `terrain_weyl_spinor_lr_v0` refutation:
  - `Se`: `0.4618802153517006`
  - `Ne`: `2.309401076758503`
  - `Ni`: `0.4618802153517006`
  - `Si`: `0.4`

Positive control:

- `Hxz=(sigma_x+sigma_z)/sqrt(2)` recovers `sigma_y` exactly as a valid boundary-case member.
- Residual is exactly zero, and z3/cvc5 zero rows have `any_nonzero=unsat`, `force_zero=sat`.

Negative controls:

- Identity fails all four: max residuals `Se=0.4618802153517006`, `Ne=2.309401076758503`, `Ni=1.0`, `Si=0.4`.
- Deterministic random orthogonal fails all four: max residuals `Se=0.6158402871356008`, `Ne=3.079201435678004`, `Ni=0.6713958426911564`, `Si=0.35555555555555557`.

## Q6: Standard Schema, Tools, Receipts

Verdict: MOSTLY ACCEPT, WITH TOOLING CAVEATS.

Accepted:

- `schema_version = three_engine_sim_result_v1`.
- `classification = scratch_diagnostic`.
- `promotion_allowed = false`.
- `formal_admission_allowed = false`.
- `engine_contract.mode = FIELD`.
- Generic envelope validator passed.
- Generic envelope validator with `--require-source-backed` passed.
- Parent hashes are present.
- Python versions recorded: `sympy 1.14.0`, `z3-solver 4.16.0.0`, `cvc5 1.3.3`, `scipy 1.17.1`, `numpy 2.3.4`.
- Julia versions recorded: `julia 1.12.6`, `Symbolics 6.58.0`, `Z3 1.0.4`.
- Seed recorded: `20260610`.
- Standard schema note says `fixture_wording=none`; grep found no live fixture/toy/mock/dummy wording except that note.
- Load-bearing tool calls are present for Python `sympy`, `z3`, `cvc5` and Julia `Symbolics`, `Z3.jl`.
- Supportive tools are declared as supportive: Python `numpy`, `scipy`; Julia `JSON`.
- PyTorch omission is explicitly scoped: no graph, network, autograd, torch_geometric, or PyTorch-specific claim path in this packet.

Named caveats:

- The envelope calls the Python lane `jax` for standard validator compatibility, but it also says no native `jax` package is claimed. This is tolerable under the FIELD/exact-symbolic scope, but should not be marketed as a native JAX run.
- `scripts/verify_load_bearing_has_capability_probe.py --sim ...terrain_exact_mirror_finder_v0.py` and the Julia variant returned `error: no_tool_integration_depth`. The result JSONs contain `TOOL_INTEGRATION_DEPTH`, but this source-level helper does not recognize the packet shape. Treat the generic validator pass as the schema gate and this helper as a tooling-fit caveat.
- Tool calls are one-to-one for load-bearing claim-path tools, not for every supportive manifest entry. If the local standard requires one tool call for every supportive serializer/array package too, this packet needs a metadata repair.

## Q7: Closure And Honest Narrative

Verdict: ACCEPT WITH PRECISE CEILING.

The owner L/R chirality reading is neither globally killed nor globally proven as a single mirror law.

Precise statement:

- The committed `sigma_y` mirror law from the earlier expectation is refuted for these four committed S5 L/R generator pairs.
- The rotational parts of `Se` and `Ne` are mirror-related by a one-parameter `O(3)` family.
- `Ni` shares the `Se/Ne` mirror relation only after collapsing to the unique affine-compatible pi rotation about `(1,-1,0)/sqrt(2)`.
- `Si` is mirror-related by a different `z`-frame to `x`-frame `O(3)` family.
- There is no uniform affine mirror for all four families.
- The surviving L/R structure is the signed/time-direction chirality separation from `terrain_weyl_spinor_lr_v0` plus the exact `Se/Ne/Ni` three-family mirror, not a universal sigma_y or universal all-four mirror.

This is a strong local exact-mirror diagnostic. It is not closure of L/R chirality, not a bridge claim, and not admission beyond `scratch_diagnostic`.

## Named Caveats

1. `Se/Ne/Si` prompt label drift: the exact three-of-four matrix is for `Se/Ne/Ni`; `Se/Ne/Si` is impossible.
2. SMT scope caveat: z3/cvc5 certify coefficient-reduced residual rows, not raw quantified `O(3)` solve-space search.
3. Source-level capability-helper caveat: `verify_load_bearing_has_capability_probe.py` cannot recognize this packet's source shape, even though the result JSONs carry tool depth and capability receipts.
4. JAX-label caveat: the envelope's `jax` lane is an exact Python/SymPy/z3/cvc5 lane, not native JAX.
5. Result-estate mutation caveat: I did not rerun builder entrypoints because the user requested read-only except this verdict.

## Final Ceiling

Accepted status label: `passes local rerun` for the existing result packet based on read validator results plus independent scratch recomputation; public scientific ceiling remains `scratch_diagnostic`.

Blocked consumers:

- canonical sim admission;
- all-four mirror law;
- universal sigma_y mirror reading;
- bridge/axis/physics claims;
- any claim that the packet ran a native JAX or PyTorch claim path.

Next unblocked step:

- Metadata repair only if desired: rename the envelope lane from `jax` to `python_exact_symbolic` or add an explicit compatibility alias, and add source-level capability-probe patterns so the helper recognizes load-bearing tool depth. Do not change the mathematical verdict unless a new raw O(3) solver packet is built.
