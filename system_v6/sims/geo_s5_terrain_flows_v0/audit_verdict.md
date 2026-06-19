# Fresh Audit Verdict: geo_s5_terrain_flows_v0

Audit date: 2026-06-10.

VERDICT: REJECT AS CLAIMED against the S5 blind exactness bar.

The packet is a useful executable three-engine `scratch_diagnostic`, and both local validators are green. That is not enough. The combined/JAX `bloch_generator_table` records the pure `Ne_Vortex_L` and `Ne_Spiral_R` generator matrices as all zeros while the same packet claims `r(t)=R_n(+/-2t)r0`, fixed axis `span(n)`, non-limit orbits, and Hamiltonian purity preservation. This is a load-bearing contradiction in the exact generator table, flow table, fixed/orbit table, and purity table.

Julia and PyTorch independently expose nonzero pure-Ne precession rows, so this is not a mathematical ambiguity. It is an envelope/JAX acceptance failure: the packet accepts inconsistent engine evidence and the validators do not check the Ne `A` matrix.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Do not use this packet as S5 terrain-flow completion, canonical terrain-family evidence, formal admission, Axis-level admission, runtime closure, physics evidence, S6 stacking evidence, or Matrix64 closure evidence.

## Inputs And Boundary

Inputs read:

- `system_v6/sims/geo_s5_terrain_flows_v0/`
- `/tmp/s5_blind_expected_20260610.md`
- `system_v6/receipts/s5_build_spec_20260610.md`
- pattern catalog: `system_v6/sims/axis_independence_discriminators_036/audit_verdict.md` H1-H7
- pattern catalog: `system_v6/sims/geo_s1_exact_closure_v0/audit_verdict.md` E1-E6
- pattern catalog: `system_v6/sims/geo_s4_operator_stage_v0/audit_verdict.md` v2 six closed conditions

I did not run the builder scripts because they overwrite result JSONs. I ran read-only validators, source imports without `main()`, source/result inspection, and independent SymPy recomputation. The only write is this `audit_verdict.md`.

Fresh checks:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json
=> {"ok": true, "result_json": "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s5_terrain_flows_v0/geo_s5_terrain_flows_v0_exact_strength_validator.py system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json
=> {"errors": [], "ok": true, "result_json": "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json"}

git status --short -- system_v6/sims/geo_s5_terrain_flows_v0 system_v6/receipts/s5_build_spec_20260610.md
=> ?? system_v6/sims/geo_s5_terrain_flows_v0/
```

The packet directory is untracked in this checkout.

## Pattern Binding Applied

Binding from H1-H7, E1-E6, and S4-v2:

- Validator green is shape/process evidence, not claim success.
- Source-derived math must be checked against the actual emitted rows.
- Sign/rate pins and order/sign correctness are separate from content correctness.
- Fixed points and basins require separate receipts.
- Controls must be actual can-fail mutation computations, not only rows saying `executed=true`.
- SMT may be accepted only at its honest scope; pinned-entry contradiction is not full symbolic flow proof.
- Engine roles must remain distinct; PyTorch pinned mirror evidence cannot repair a broken combined symbolic table.

## Quoted Source And Result Evidence

Blind expected pure Hamiltonian convention:

```text
rho' = -i[H,rho] gives r' = 2 h x r.
...
The antisymmetric Hamiltonian matrix is
C_s(epsilon) = [[0,-w,w],[w,0,-w],[-w,w,0]].
```

Cites: `/tmp/s5_blind_expected_20260610.md:14-38`.

Blind expected pure Ne row:

```text
Ne_L: A = C_+(epsilon_Ne_L), b = 0
Ne_R: A = C_-(epsilon_Ne_R), b = 0
...
r(t) = R_n(2 epsilon t) r0 for L
r(t) = R_n(-2 epsilon t) r0 for R
```

Cites: `/tmp/s5_blind_expected_20260610.md:56-74`.

JAX source claims to derive pure Ne from Hamiltonian density generators:

```python
"Ne_Vortex_L": {
    ...
    "generator": -sp.I * commutator(HL, rho),
}
...
"Ne_Spiral_R": {
    ...
    "generator": -sp.I * commutator(HR, rho),
}
```

Cites: `geo_s5_terrain_flows_v0_jax.py:323-335`.

But the emitted JAX result table has all-zero pure-Ne `A` rows:

```text
"Ne_Spiral_R" ... "symbolic": {"A": [["0","0","0"],["0","0","0"],["0","0","0"]], "b": ["0","0","0"]}
...
"Ne_Vortex_L" ... "symbolic": {"A": [["0","0","0"],["0","0","0"],["0","0","0"]], "b": ["0","0","0"]}
```

Cites: `geo_s5_terrain_flows_v0_jax_results.json:48-258`.

The same JAX flow receipts then claim nonzero Hamiltonian rotation:

```python
"formula": "r(t)=R_n(+2t) r0"
...
"formula": "r(t)=R_n(-2t) r0"
```

Cites: source construction at `geo_s5_terrain_flows_v0_jax.py:461-472`; result rows at `geo_s5_terrain_flows_v0_jax_results.json:1199,1292`.

The envelope still declares the exact generator and positive receipts green:

```text
"exact_generator_rows_eight": true
"required_positive_receipts_pass": true
"source_sha256_current": true
```

Cites: `geo_s5_terrain_flows_v0_envelope_results.json:887-912`.

The packet-local validator misses the failure because it checks only Ne `b`, not Ne `A`:

```python
require(rows["Ne_Vortex_L"]["symbolic"]["b"] == ["0", "0", "0"], "Ne Vortex b drift")
```

Cite: `geo_s5_terrain_flows_v0_exact_strength_validator.py:91-99`.

Julia and PyTorch show the expected nonzero pure-Ne rows:

- Julia `Ne_Vortex_L` has `A = [[0,-2/sqrt(3),2/sqrt(3)], [2/sqrt(3),0,-2/sqrt(3)], [-2/sqrt(3),2/sqrt(3),0]]` and `Ne_Spiral_R` has the sign mirror. Cites: `geo_s5_terrain_flows_v0_julia_results.json:127-229`.
- PyTorch pinned mirror has nonzero opposite signed pure-Ne `pinned_A_fractional` rows and classifies both as `nonlimit_orbit`. Cites: `geo_s5_terrain_flows_v0_pytorch_results.json:39-83,378-390`.

This engine split is a decisive packet-level failure because the combined envelope exports the JAX table as the packet `bloch_generator_table`.

## Hand Recomputation Packet

### Required minimum: sigma-minus ODE derivation

Using

```text
rho=(I+x*sigma_x+y*sigma_y+z*sigma_z)/2
sigma_-=[[0,0],[1,0]]
D[L]rho=L rho L^dagger - 1/2{L^dagger L,rho}
H_L=H0=(sigma_x+sigma_y+sigma_z)/sqrt(3)
```

I recompute

```text
A_sigma_minus =
[[-gamma/2, -2*sqrt(3)*eps/3,  2*sqrt(3)*eps/3],
 [ 2*sqrt(3)*eps/3, -gamma/2, -2*sqrt(3)*eps/3],
 [-2*sqrt(3)*eps/3,  2*sqrt(3)*eps/3, -gamma]]

b_sigma_minus = (0,0,-gamma)
```

So the blind `gamma/2` transverse and `gamma` longitudinal rate tripwire is satisfied by the Ni/Pit symbolic row. The Ni/Source row mirrors `b=(0,0,+gamma)` under the locked `sigma_+` convention. This part survives.

### Required minimum: one precession axis

For `H0=n.sigma`, `n=(1,1,1)/sqrt(3)`, direct expansion of `-i[H0,rho]` gives

```text
x' =  2/sqrt(3) * (z-y)
y' =  2/sqrt(3) * (x-z)
z' =  2/sqrt(3) * (y-x)

C_+ =
[[0, -2/sqrt(3),  2/sqrt(3)],
 [2/sqrt(3), 0, -2/sqrt(3)],
 [-2/sqrt(3), 2/sqrt(3), 0]]
```

`H_R=-H0` gives `C_-=-C_+`. This matches the blind sheet and the Julia/PyTorch legs, but not the JAX/envelope generator table.

### Required minimum: one basin limit

For the Si/Hill z-frame row with `delta=kappa>0` and `nu=2 omega`, the expected flow is

```text
x(t)=exp(-kappa*t)(x0*cos(2*omega*t)-y0*sin(2*omega*t))
y(t)=exp(-kappa*t)(x0*sin(2*omega*t)+y0*cos(2*omega*t))
z(t)=z0
```

Therefore

```text
lim_{t->infty} r(t) = (0,0,z0)
```

This matches the packet's Si/Hill limit row. The same structure gives Citadel x-slices. These rows survive.

### Required minimum: one purity proof step

For pure Hamiltonian precession:

```text
d/dt |r|^2 = 2 r . r' = 4 s eps r . (n x r)
```

The recomputed scalar term is

```text
x*(z-y) + y*(x-z) + z*(y-x) = 0
```

So the mathematical purity statement is true for the expected pure-Ne Hamiltonian rows. The packet's JAX purity receipt is still not earned from its own exported Ne `A`, because its exported Ne `A` is zero while its flow receipt says nonzero rotation.

## F1. Per-Generator Bloch ODEs, Rate Pin, Sheet Mirror

Verdict: FAIL AS PACKET, PARTIAL AS ENGINE EVIDENCE.

Survives:

- Ni amplitude damping rate convention is correct in the JAX row: transverse `-gamma/2`, longitudinal `-gamma`, and affine `b=(0,0, +/- gamma)`.
- Se source-isotropic rows carry `-4 lambda I + C_s(epsilon)`.
- Si Hill/Citadel use z/x retention frames with transverse damping `kappa` for paired projectors.
- The convention pin names the primary standard Bloch basis, `H_L=+H0`, `H_R=-H0`, and the S1 pinned-y conversion layer.

Fails:

- The per-generator table does not derive all eight rows correctly. Both pure-Ne rows are all-zero in the combined/JAX table.
- Sheet-sign mirror for pure-Ne `L/R` is not computed in the combined table because both sides are zero.
- The source import of `generator_rows()` reproduces the same JAX zero-Ne rows, so this is not just stale JSON.

Likely local cause: `affine_from_components()` extracts coefficients using `comp.coeff(var)` after simplification (`geo_s5_terrain_flows_v0_jax.py:277-284`). For the pure Hamiltonian expressions, explicit expansion/differentiation recovers the nonzero coefficients. The validator does not catch this.

## F2. Closed Forms, Fixed Sets, Basins, Limits

Verdict: FAIL AS PACKET.

Survives for some rows:

- Se closed forms and zero-limit rows match the blind isotropic source expectation when `lambda>0`.
- Ni affine solution form `r(t)=r_*+exp(tA)(r0-r_*)` and erased-H pole controls match the blind structure.
- Si z/x damped-spiral limit rows match recomputation.

Fails:

- Pure-Ne closed forms are incompatible with the exported JAX/envelope `A=0` rows. If `A=0`, the exact flow is `r(t)=r0`, not `R_n(+/-2t)r0`.
- Pure-Ne fixed-axis and nonlimit orbit receipts are also incompatible with `A=0`; an all-zero generator has the whole Bloch ball fixed.
- The envelope accepts the contradiction because it checks row counts and receipt booleans, not consistency between `A`, flow, fixed set, and basin/orbit receipts.

## F3. Purity Invariance And Non-Unitality

Verdict: PARTIAL.

Purity:

- The mathematical pure-Hamiltonian proof is correct: `r . (n x r)=0`, so `d/dt Tr(rho^2)=0`.
- Julia/PyTorch give nonzero skew pure-Ne rows, so they support that proof.
- The combined/JAX table does not earn the proof because pure-Ne `A=0` is inconsistent with the claimed rotation. The statement "purity preserved" remains true for the wrong reason if judged from the JAX table.

Non-unitality:

- Ni/Pit and Ni/Source witnesses survive at the infinitesimal level: `X(I)` has Bloch coefficients `(0,0,-gamma_Ni_L)` and `(0,0,+gamma_Ni_R)`.
- Erased-H finite-time witness recomputes as `b_t=(0,0,q(1-exp(-gamma*t)))`, nonzero for `gamma>0`, `t>0`.
- Non-Ni rows have `b=0` in the scoped tables.

## F4. CPTP, Trace, Positivity, Controls, Tools, SMT, Ceilings

Verdict: MIXED; not enough to accept.

Passes:

- The read-only strict source-backed validator passes.
- The packet-local exact-strength validator passes.
- The envelope preserves `scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`.
- Sampled Choi/trace/Hermiticity fixtures are present at `t in {0, 0.1, 0.2, 0.4, 1.0}` and pass within numeric tolerance.
- SMT is honestly scoped as pinned-entry contradiction for Ni non-unitality, not full symbolic flow proof.
- PyTorch is explicitly a pinned mirror, not a symbolic CAS.

Fails or remains weak:

- Validator pass is not claim pass; both validators miss the pure-Ne generator contradiction.
- Negative controls are still mostly declarative result rows. For example, `negative_controls()` returns dictionaries with `executed=true`, mutated observations, and `gate_passed_after_mutation=false` (`geo_s5_terrain_flows_v0_jax.py:720-827`), but I found no actual mutation rerun code for these controls. This repeats the H4/S4-v1 failure mode in softer form.
- The packet accepts inconsistent engine evidence: Julia/PyTorch nonzero Ne rows versus JAX/envelope zero Ne rows.
- `aligned_packages_load_bearing` for JAX omits `sympy` even though `TOOL_MANIFEST` says SymPy is load-bearing for exact symbolic derivation. This is a receipt hygiene gap, not the decisive math failure.

## Named Gaps

1. Fix the JAX/SymPy affine extraction so pure Hamiltonian Ne rows emit `C_+` and `C_-`, not zero matrices. Use expansion or differentiation, then add a validator assertion for both Ne `A` rows.
2. Add an envelope consistency gate: every claimed closed-form flow must differentiate back to its exported `A,b`.
3. Add fixed-set consistency gates: pure Ne `A=0` must not be allowed to coexist with `span(n)` fixed set and nonlimit orbit claims.
4. Add basin/orbit consistency gates tying limits and nonlimits to the actual exported generator, not only to row labels.
5. Turn negative controls into actual mutation computations or demote them from `executed_mutation_control`.
6. Make cross-engine disagreement fatal when the combined table differs from a supposedly independent engine derivation on a load-bearing row.
7. Strengthen `geo_s5_terrain_flows_v0_exact_strength_validator.py` so it checks Ne `A`, flow/ODE consistency, and the pure-Ne nonzero skew matrix, not only `b=0`.
8. Preserve the current ceiling; no canonical or formal-admission language is justified.

## Final Boundary

Accept as: executable scratch packet with useful S5 scaffolding, correct Ni amplitude-damping rates/signs in the JAX row, correct Si retained-axis limits, correct Se isotropic damping form, green local validators, non-unitality witnesses for Ni, sampled CPTP regression fixtures, and bounded ceiling language.

Reject as: exact S5 flow packet, per-generator Bloch ODE pass, pure-Ne flow proof, full fixed/basin proof, executed-control proof, or engine-consistent three-engine receipt.

VERDICT: REJECT AS CLAIMED. Keep `classification=scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`.

## V2 Re-Audit: Six v1 Fail Conditions

Audit date: 2026-06-10.

Boundary: I did not build this sim and did not run the builders because they write result JSON. I re-read the v2 sources/results, ran the fresh validators against the canonical envelope, and used read-only Python recomputation. The only repo write is this appended section.

Fresh checks:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json
=> {"ok": true, "result_json": "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s5_terrain_flows_v0/geo_s5_terrain_flows_v0_exact_strength_validator.py system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json
=> {"errors": [], "ok": true, "result_json": "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json"}
```

Note: `geo_s5_terrain_flows_v0_exact_strength_validator.py` currently ignores its CLI path argument and always reads the canonical result path. I therefore treat the canonical validator pass as evidence for the canonical v2 result only, not as a path-parametric mutation test.

### V1. Ne Affine Rows And Antisymmetric Precession A

Verdict: CLOSED.

The exported `Ne_Vortex_L` and `Ne_Spiral_R` symbolic rows now carry the nonzero antisymmetric Hamiltonian precession matrices:

```text
Ne_Vortex_L A =
[[0, -2*sqrt(3)/3,  2*sqrt(3)/3],
 [2*sqrt(3)/3, 0, -2*sqrt(3)/3],
 [-2*sqrt(3)/3, 2*sqrt(3)/3, 0]]
b = [0, 0, 0]

Ne_Spiral_R A = -Ne_Vortex_L A
b = [0, 0, 0]
```

Independent hand/SymPy recomputation from `rho=(I+xX+yY+zZ)/2`, `H0=(X+Y+Z)/sqrt(3)`, and `rho'=-i[H0,rho]` gave:

```text
components = [
  2*sqrt(3)*(-r_y + r_z)/3,
  2*sqrt(3)*(r_x - r_z)/3,
  2*sqrt(3)*(-r_x + r_y)/3
]

A = C_+ =
[[0, -2*sqrt(3)/3,  2*sqrt(3)/3],
 [2*sqrt(3)/3, 0, -2*sqrt(3)/3],
 [-2*sqrt(3)/3, 2*sqrt(3)/3, 0]]

b = [0, 0, 0]
diff_vs_blind_C_plus = zero matrix
```

This matches `/tmp/s5_blind_expected_20260610.md` for `C_s(epsilon)` with `s=+1`, `epsilon=1`; the local diff snippet exited `0`.

### V2. Round-Trip Differentiation Gate

Verdict: CLOSED.

`flow_round_trip_gates["all_pass"]` is `true`. Every row has `computed=true`, `pass=true`, and residual `[0,0,0]` after differentiating the claimed closed-form flow at `t=0` and comparing to exported `A*r+b`.

Spot checks:

```text
Ne_Vortex_L derived_A = C_+, residual = [0,0,0]
Ne_Spiral_R derived_A = C_-, residual = [0,0,0]
Ni_Pit_L derived_A has transverse -gamma_Ni_L/2, longitudinal -gamma_Ni_L, b=[0,0,-gamma_Ni_L]
Si_Hill_L derived_A = [[-kappa,-2*omega,0],[2*omega,-kappa,0],[0,0,0]]
```

The source route is no longer just a flow formula receipt: `flow_round_trip_receipts()` differentiates the formula and calls `affine_from_components()` on the derivative before setting pass/fail.

### V3. Fixed Sets From Exported A,b

Verdict: CLOSED.

`build_gates["fixed_set_consistency_from_exported_A_b"]` is `true`. Each fixed receipt says it was derived from exported symbolic `A,b` by solving `A*r+b=0` and taking `kernel(A)`.

Spot checks:

```text
Ne_Vortex_L fixed axis: span(n), kernel_basis=[[1,1,1]], pass=true
Ne_Spiral_R fixed axis: span(n), kernel_basis=[[1,1,1]], pass=true
Si_Hill_L fixed set: {(0,0,z) : -1 <= z <= 1}
Si_Citadel_R fixed set: {(x,0,0) : -1 <= x <= 1}
Ni_Pit_L fixed point: r_star=-A^-1*b
```

### V4. Basin/Limit Receipts Tied To The Generator

Verdict: CLOSED.

`build_gates["basin_orbit_consistency_from_exported_A_b"]` is `true`. Basin/orbit rows use `computed_from="exported A,b"` and pass.

Spot checks:

```text
Ne_Vortex_L: non-attracting invariant orbit classes off span(n), velocity_at_initial=[0, 2*sqrt(3)/3, -2*sqrt(3)/3], norm_derivative=0
Ne_Spiral_R: non-attracting invariant orbit classes off span(n), velocity_at_initial=[0, -2*sqrt(3)/3, 2*sqrt(3)/3], norm_derivative=0
Si_Hill_L: kappa>0 limit [0,0,z0], basin slices keep retained z
Si_Citadel_R: kappa>0 limit [x0,0,0], basin slices keep retained x
Ni_Pit_L/Ni_Source_R: whole Bloch ball converges to exported r_star because pinned A has negative real-part spectrum
```

This closes the v1 contradiction where a zero Ne `A` coexisted with non-limit orbit claims.

### V5. Controls As Executed Mutations

Verdict: CLOSED, with scope noted.

`negative_controls["all_executed_can_fail"]` is `true`, and C1 through C12 each carry `computed_mutation=true`, `executed=true`, `expected_failure_observed=true`, and `gate_passed_after_mutation=false`. The validator now explicitly enforces those four fields for every C1-C12 row.

The strongest controls are actual symbolic/numeric mutations: wrong right-sheet Hamiltonian sign, wrong Bloch convention without conversion, wrong Si frame, Ni jump swap, fake unital Ni, fake nonunital scoped unital row, Hamiltonian-as-attractor error, and weak-Ne purity promotion. C8-C10/C12 are evidence-surface deletion/conflation controls rather than solver reruns, but they do emit concrete mutated observations and can-fail gates instead of the old bare `executed=true` pattern.

### V6. Cross-Engine Fatality Wired

Verdict: CLOSED.

The envelope now computes cross-engine pinned `A,b` row agreement across Julia, JAX, and PyTorch, stores per-row diffs, and wires `cross_engine_load_bearing_rows_agree` into `all_pass`. The packet-local validator also has explicit checks for:

```text
build_gates.cross_engine_load_bearing_rows_agree is true
cross_engine_consistency.all_pass is true
all cross_engine_consistency.rows[*].pass are true
```

Fresh emitted result:

```text
cross_engine_consistency.all_pass = true
max_abs_diff = 2.271086585459159e-08
tolerance = 1e-06

Ne_Vortex_L max_abs_diff = 2.271086585459159e-08, pass=true
Ne_Spiral_R max_abs_diff = 2.271086585459159e-08, pass=true
Ni_Pit_L max_abs_diff = 1.14799610650973e-08, pass=true
```

## V2 Final Boundary

All six v1 fail conditions are closed against the v2 canonical sources/results I read. This earns the v2 repair of the rejected claim, but it does not raise the packet above its declared ceiling: `classification=scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false` remain binding.

FINAL: EARNED.

## 2026-06-10 Remediation Note - Tooling Step 4

Scope: audit queue item 4, flow-evolution claim-path remediation for `geo_s5_terrain_flows_v0`.

Route table:

```text
Julia canon leg: DifferentialEquations.ODEProblem + DifferentialEquations.solve(Tsit5) on pinned affine Bloch ODE r'=A*r+b.
JAX leg: diffrax.ODETerm + diffrax.diffeqsolve + diffrax.Tsit5 on pinned affine Bloch ODE r'=A*r+b.
Exact special-case checks: LinearAlgebra.exp / jax.scipy.linalg.expm on the augmented constant-coefficient affine generator, retained only as exact parity checks.
Carrier note: direct OrdinaryDiffEq is not declared in the strict Julia carrier project; Tsit5 is used through DifferentialEquations.
```

Byte-stability: claim values are unchanged against `HEAD` for `pin_spec`, `pin_sha256`, `convention_pin`, `bloch_generator_table`, `flow_solutions`, `flow_round_trip_gates`, `fixed_points_and_basins`, `generator_consistency_gates`, `gksl_all_t_proofs`, `sampled_choi_fixtures`, `purity_preservation`, `nonunitality_witnesses`, `cross_engine_consistency`, `strength_tokens`, `positive_ledger`, and `divergence.max_divergence`.

Fresh rerun and validators:

```text
geo_s5_terrain_flows_v0_julia.jl: all_pass=true
geo_s5_terrain_flows_v0_jax.py: all_pass=true
geo_s5_terrain_flows_v0_pytorch.py: all_pass=true
geo_s5_terrain_flows_v0_envelope.py: all_pass=true
geo_s5_terrain_flows_v0_exact_strength_validator.py: ok=true, errors=[]
scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed .../geo_s5_terrain_flows_v0_envelope_results.json: ok=true
```

Capability gate: changed-file gates returned no violations for `sim_diffrax_capability.py`, `sim_differentialequations_capability.py`, `sim_symbolics_capability.py`, `geo_s5_terrain_flows_v0_jax.py`, `geo_s5_terrain_flows_v0_julia.jl`, and `geo_s5_terrain_flows_v0_envelope.py`.
