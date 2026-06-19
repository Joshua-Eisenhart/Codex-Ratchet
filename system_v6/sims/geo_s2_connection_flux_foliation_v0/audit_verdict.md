# Fresh Audit Verdict: geo_s2_connection_flux_foliation_v0

Date: 2026-06-10

Mode: read-only audit except this file. I did not rebuild the packet entrypoints because they rewrite result JSON timestamps; validation and recomputation below read existing sources/results only.

Inputs checked:

- Sim folder: `system_v6/sims/geo_s2_connection_flux_foliation_v0/`
- Blind sheet: `/tmp/s2_blind_expected_20260610.md`
- Build spec: `system_v6/receipts/s2_build_spec_20260610.md`
- Canonical program receipt: `system_v6/receipts/geometry_sim_program_canonical_20260610.md`
- Pattern catalog: H1-H7 from `system_v6/sims/axis_independence_discriminators_036/audit_verdict.md`; E1-E6 from `system_v6/sims/geo_s1_exact_closure_v0/audit_verdict.md`

## Verdict

VERDICT: EARNED.

Ceiling: this earns only the S2 positive connection/flux/foliation scratch diagnostic at `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. It supports the pinned Hopf connection, curvature, lifted-cycle horizontal holonomy, Berry convention map, Stokes/Chern receipts, torus double-cover area/grid accounting, and scoped exact/tool receipts. It does not admit formal/canonical status, bridge/axis/physics claims, or any higher-stage geometric coupling claim.

## Validator Commands

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s2_connection_flux_foliation_v0/results/geo_s2_connection_flux_foliation_v0_envelope_results.json
```

Result: `{"ok": true, "result_json": "system_v6/sims/geo_s2_connection_flux_foliation_v0/results/geo_s2_connection_flux_foliation_v0_envelope_results.json"}`

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s2_connection_flux_foliation_v0/geo_s2_connection_flux_foliation_v0_exact_strength_validator.py
```

Result: `{"errors": [], "ok": true, "result_json": "system_v6/sims/geo_s2_connection_flux_foliation_v0/results/geo_s2_connection_flux_foliation_v0_envelope_results.json"}`

## P1. Holonomy And Convention Map

Status: PASS.

Quoted source:

```python
"holonomy_quantity=primary:accumulated_phi;separate:endpoint_global_spinor_phase,Berry_phase|"
"berry_formula=one_base_loop:-Omega/2=-pi*(1-cos(2*eta));lifted_cycle_twice:-2*pi*(1-cos(2*eta))|"
"phase_domain=lifted_real_with_mod_2pi_reconciliation|"
"base_loop_count=lifted_torus_chart_cycle chi:0->2pi traverses base twice; one_base_loop chi:0->pi|"
```

Cites: `geo_s2_connection_flux_foliation_v0_jax.py:37-43`; same structured pin in PyTorch `:32-39` and Julia `:24-49`.

Genuine numerical horizontal transport is present. JAX computes `dchi_dt`, then sums `-cos(2*eta) * dchi_dt / n`, and compares to the closed form after the solve (`geo_s2_connection_flux_foliation_v0_jax.py:236-270`). PyTorch does the same in `euler_delta_phi` and `torch.func.vmap` (`geo_s2_connection_flux_foliation_v0_pytorch.py:106-121`). Julia uses `DifferentialEquations.ODEProblem` with `du[1] = -cos(2eta) * (2pi + 0.1 * (1 - 2t))` (`geo_s2_connection_flux_foliation_v0_julia.jl:102-129`).

Hand recompute, one transport step route:

```text
eta = pi/6, steps = 15
dphi sum = sum_k[-cos(2eta) * (2*pi + 0.1*(1-2*k/15))/15]
          = -3.1449259869231274
target    = -2*pi*cos(pi/3) = -3.141592653589794
residual  = -0.0033333333333334103
receipt residual = -0.0033333333333329662
```

The Berry route is not compared directly to lifted-cycle accumulated phi. The JAX symbolic receipt records one-base-loop Berry `-pi*(1 - cos(2*eta))`, lifted/twice-loop Berry `-2*pi*(1 - cos(2*eta))`, one-base-loop accumulated phi `-pi*cos(2*eta)`, and lifted accumulated phi `-2*pi*cos(2*eta)` (`geo_s2_connection_flux_foliation_v0_jax.py:202-210`, `:511`). This closes the blind sheet's central convention-mixing tripwire.

## P2. Curvature, Stokes, Chern

Status: PASS.

Quoted source:

```python
coeff = -sp.I * sum(sp.conjugate(spinor[i]) * sp.diff(spinor[i], var) for i in range(2))
f_eta_chi = sp.trigsimp(sp.simplify(sp.diff(a_chi, eta) - sp.diff(a_eta, chi)))
```

Cites: `geo_s2_connection_flux_foliation_v0_jax.py:150-162`.

The source derives the connection from the pinned spinor, then derives `F = dA`. The result reports `d_eta=0`, `d_phi=1`, `d_chi=cos(2*eta)`, `curvature_eta_chi=-2*sin(2*eta)`, and a wrong-sign control that fails.

Stokes is computed as separate horizontal and flux routes. The source independently integrates the strip and computes `h_delta` for multiple pairs (`geo_s2_connection_flux_foliation_v0_jax.py:275-306`). The Chern receipt integrates the chart and records the physical/base normalization (`geo_s2_connection_flux_foliation_v0_jax.py:217-222`).

Hand recompute, Stokes pair:

```text
eta_i = pi/6, eta_j = pi/4, L = 2*pi
int_strip_F = 2*pi*(cos(pi/2) - cos(pi/3)) = -pi
h_delta = -2*pi*cos(pi/2) - (-2*pi*cos(pi/3)) = pi
h_delta + int_strip_F = 4.440892098500626e-16 numeric roundoff; exact receipt = 0
```

Receipt row: `int_strip_F="-pi"`, `h_delta="pi"`, `h_delta_plus_strip="0"`.

Hand recompute, Chern:

```text
int_chart F = int_0^(pi/2) int_0^(2pi) -2*sin(2eta) dchi deta
            = 2*pi * [cos(2eta)]_0^(pi/2)
            = -4*pi
int_physical_base F = -2*pi
c1 = -int_physical_base F / (2*pi) = 1
```

## P3. Torus Area, Double Cover, Grid, Foliation

Status: PASS.

Quoted source:

```python
torus_metric = sp.trigsimp(sp.simplify(torus_jac.T * torus_jac))
torus_det = sp.trigsimp(sp.simplify(torus_metric.det()))
chart_area = sp.simplify((2 * sp.pi) * (2 * sp.pi) * sp.sin(2 * eta))
physical_area = sp.simplify(chart_area / 2)
```

Cites: `geo_s2_connection_flux_foliation_v0_jax.py:172-176`.

The result records `chart_area=4*pi**2*sin(2*eta)`, `physical_area=2*pi**2*sin(2*eta)`, and `double_cover_reason=(phi, chi) ~ (phi + pi, chi + pi)`.

Hand recompute, cover factor:

```text
eta = pi/5
chart_area = 4*pi^2*sin(2*pi/5) = 37.54620631564544
physical_area = chart_area / 2 = 18.77310315782272
cover_factor = 2
```

The grid route enumerates chart pairs and quotient classes for even `N` (`geo_s2_connection_flux_foliation_v0_jax.py:309-335`); PyTorch independently forms tensor meshgrid classes (`geo_s2_connection_flux_foliation_v0_pytorch.py:152-175`). For `N=8`, `chart_points=64`, `physical_points=32 = N^2/2`.

Foliation/leaf receipts are present: source emits non-endpoint shells `pi/12, pi/6, pi/4, pi/3, 5*pi/12`, physical area, lifted holonomy, adjacency, and flux deltas (`geo_s2_connection_flux_foliation_v0_jax.py:338-361`). Endpoint singular shells are not treated as ordinary torus rows.

## P4. Strength, Pins, Controls, Tools, Ceiling

Status: PASS.

The envelope build gates are all true: identical structured convention pins, current source hashes, literal strength tokens, two-to-one double cover handled, exact SMT can-fail controls, no peer-result reads, and ceilings preserved (`geo_s2_connection_flux_foliation_v0_envelope.py:119-151`; result `build_gates` all true).

Strength tokens are literal and scoped. `S2.H1` is deliberately `diagnostic_float_nonclaim`; exact claims sit on symbolic/closed-form/integer/SMT rows. The interval row is a genuine monotonic endpoint enclosure, not float-tail boxing: `eta_interval=[pi/6, pi/4]`, `cos_2eta_interval=[0, 1/2]`, `h_scaled_by_2pi_interval=[-1/2, 0]`, method `exact endpoint enclosure from monotonicity` (`geo_s2_connection_flux_foliation_v0_jax.py:364-375`).

SMT/proof controls bind raw values, not precomputed booleans. Z3/CVC5 assert the scaled Stokes equality and wrong-sign failure from explicit raw fractions (`geo_s2_connection_flux_foliation_v0_jax.py:378-470`). PyTorch Z3/CVC5 bind torch-derived `N` and `physical_points` for `2*physical_points == N*N` and fail the naive control (`geo_s2_connection_flux_foliation_v0_pytorch.py:178-239`).

Two-CAS-or-honest-split: this is not two full CAS derivations of every row. It is an honest split: SymPy is the load-bearing symbolic/CAS derivation; Julia is ODE/Z3 carrier-side receipt; PyTorch is tensor ODE/grid/SMT. The envelope names those roles explicitly (`geo_s2_connection_flux_foliation_v0_envelope.py:188-195`) and does not let PyTorch arbitrate symbolic connection/curvature.

PyTorch role is real enough for its scoped claim. It uses `torch.func.vmap` over ODE endpoint deltas and exact grid cardinality proof, and its demotion condition is explicit (`geo_s2_connection_flux_foliation_v0_pytorch.py:264-297`). It is not listed as the symbolic arbiter.

## H/E Pattern Catalog

H1-H7: no blocking H-pattern found. The packet is not a field-isolated independence matrix; it does not echo axis labels; its controls are value-changing wrong-sign/grid controls; solver checks bind raw fractions/integers rather than movement booleans; `torch.func` is applied to ODE/grid work, not a synthetic diagonal sensitivity; no Axis-4/6 boundary is asserted.

E1-E6: no blocking E-pattern found. The five-item sign/convention pin is explicit; the packet uses an honest CAS/ODE/tensor split; signs/factors are computed and have can-fail controls; closed-form integrals and double-cover divisions match the blind sheet; no Haar/statistical claim is in scope; classification/strength labels are exact enough for the stated ceiling.

## Named Gaps

No blocking gap found for the requested P1-P4 audit. Residual limits are ceiling limits, not open gaps: `S2.H1` remains diagnostic numerical evidence behind exact routes, the interval row is only the monotonic endpoint enclosure it says it is, and the packet remains non-promoting scratch evidence.

## 2026-06-10 Toolset-Coverage Addendum

Manifolds.jl is now load-bearing for the Julia S2/S3 metric/geodesic side of this connection/flux packet. The Julia leg adds `S2.M` with `Manifolds.distance`, `Manifolds.shortest_geodesic`, `Manifolds.log`/`exp`, and `Manifolds.manifold_volume` on `Sphere(2)` and `Sphere(3)`.

Closed-form torus/grid rows remain intact; the package-native Manifolds receipt gates the metric side and does not promote the packet beyond `scratch_diagnostic`.

Fresh checks: `sim_manifolds_capability.py` wrote `manifolds_capability_results.json` with `summary.all_pass=true`; the Julia leg and envelope reran with `ok:true`; `validate_three_engine_sim_result.py --strict-source-backed` and `geo_s2_connection_flux_foliation_v0_exact_strength_validator.py` returned `ok:true`; the per-file load-bearing capability gate returned no violations for `DifferentialEquations`, `Manifolds`, and `Z3`.

## 2026-06-10 Grassmann Exterior-Calculus Addendum

Added an independent Julia mirror receipt `S2.FG` for the curvature claim. The existing SymPy `S2.F` route remains intact; `S2.FG` is a labeled mirror that uses `Grassmann.wedge(v1, v2)` under `@basis S"++"` to represent `deta wedge dchi`, checks wedge antisymmetry, checks `deta wedge deta = 0`, and records:

```text
dA = d(cos(2*eta)) wedge dchi
d(cos(2*eta)) = -2*sin(2*eta) d eta
F = -2*sin(2*eta) d eta wedge d chi
```

Fresh receipt status: `S2.FG.pass=true`, `api=Grassmann.wedge(v1, v2)`, and the envelope gate `grassmann_exterior_curvature_mirror=true`.

Fresh checks:

```text
validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s2_connection_flux_foliation_v0/results/geo_s2_connection_flux_foliation_v0_envelope_results.json
=> {"ok": true}

geo_s2_connection_flux_foliation_v0_exact_strength_validator.py
=> {"errors": [], "ok": true}

audit_three_engine_source_claims.py --results-dir system_v6/sims/geo_s2_connection_flux_foliation_v0/results
=> source_backed_all_lanes, problems=[]
```
