# Fresh Audit Verdict: geo_s1_exact_closure_v0

Scope: read-only audit of `system_v6/sims/geo_s1_exact_closure_v0/` against `/tmp/s1x_blind_expected_20260610.md`. I did not rerun the sim legs because they write result JSONs. I ran the read-only strict envelope validator and independent hand recomputations.

Validator check:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json
=> {"ok": true, "result_json": "system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json"}
```

This validator pass is a schema/source-backed pass. It does not clear the audit findings below.

## Hand recomputations

### r_y sign trap

Blind sheet source:

> With standard `sigma_y = [[0,-i],[i,0]]` and `r_i = Tr(rho sigma_i)`, `r_y = -2 Im(z1 conj(z2))`; the S1 Hopf convention is `+2 Im(z1 conj(z2))`; the builder must pin `Bloch basis = (sigma_x, -sigma_y, sigma_z)` or the equivalent expansion.

Cites: `/tmp/s1x_blind_expected_20260610.md:35-94`.

My recomputation with `z1=a+ib`, `z2=c+id`:

```text
ry_std = 2*a*d - 2*b*c
ry_hopf_basis = -2*a*d + 2*b*c
hopf_y = -2*a*d + 2*b*c
std_minus_hopf_y = 4*a*d - 4*b*c
hopf_basis_minus_hopf_y = 0
```

So the identity holds only with the `-sigma_y` basis / Hopf-y pin. Under standard sigma_y it is flipped.

### Closed-form integral step

Blind sheet source:

> `Vol(S^3) = (1/2)(4 pi^2)(1) = 2 pi^2`; `Area(T_eta) = (1/2)(4 pi^2 sin(2eta)) = 2 pi^2 sin(2eta)`.

Cites: `/tmp/s1x_blind_expected_20260610.md:140-175`.

My recomputation:

```text
volume_chart = 4*pi**2
volume = 2*pi**2
torus_chart = 4*pi**2*sin(2*eta)
torus = 2*pi**2*sin(2*eta)
```

This part matches the packet.

### Interval endpoint check

Packet source:

> Julia interval route uses `I_A = A/sqrt(1+A^2), tail_bound <= 1/(2A^2)` with `cutoff_A=100`, lower `0.9999500037496873`, tail `5e-05`, upper `1.0000000037496877`.

Cites: `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_julia_results.json:64-75`; source code at `geo_s1_exact_closure_v0_julia.jl:113-127`.

My recomputation of the same formula:

```text
A100_finite = 0.999950003749687527341289288065
A100_tail = 0.0000500000000000000000000000000000
A100_upper = 1.00000000374968752734128928807
contains_one_by_formula = True
```

The arithmetic matches the receipt, but this is a closed-form/tail box with float constants, not genuine interval propagation from the Gauss-integral inputs through the integrand.

## E1. Sign Pin

Verdict: FAIL.

The blind trap requires an explicit PIN field naming the sigma-y / `r_i` / Hopf-y convention and both CAS legs emitting expanded component differences under that pin, not just a zero result.

The packet has a shared `PIN_SPEC`, but it only says:

> `exact_strength=symbolic_closed_form_interval|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false`

Cites: `geo_s1_exact_closure_v0_julia.jl:26`, `geo_s1_exact_closure_v0_jax.py:37-41`, `geo_s1_exact_closure_v0_envelope.py:27-31`, envelope result `geo_s1_exact_closure_v0_envelope_results.json:1113-1116`.

That is not a convention pin. The sign is absorbed in the JAX/SymPy leg by using:

> `sy_hopf = sp.Matrix([[0, sp.I], [-sp.I, 0]])`

Cites: `geo_s1_exact_closure_v0_jax.py:139-150`.

That matrix is `-sigma_y` relative to the blind sheet's standard `sigma_y`. The Julia leg does not derive `Bloch(rho)` from `rho` and a Pauli basis; it directly sets:

> `y_bloch = 2b * c - 2a * d`; `y_hopf = 2b * c - 2a * d`

Cites: `geo_s1_exact_closure_v0_julia.jl:70-87`.

Both result files emit expanded zeros, but not under an explicit convention PIN:

> Julia `bloch_minus_hopf_expanded`: `["0","0","0"]`; JAX `bloch_minus_hopf_expanded`: `["0","0","0"]`.

Cites: `geo_s1_exact_closure_v0_julia_results.json:14-47`, `geo_s1_exact_closure_v0_jax_results.json:36-70`.

Finding: the identity passes because the JAX basis is silently flipped and the Julia leg predefines the Hopf-y convention into `y_bloch`. The required sign PIN is absent.

## E2. Two-CAS Independence

Verdict: FAIL.

The JAX/SymPy leg is a real density-matrix CAS derivation with a nonstandard `sy_hopf` basis:

> `rho = psi * psi.conjugate().T`; `bloch = sp.Matrix([sp.trace(rho * basis) for basis in (sx, sy_hopf, sz)])`.

Cites: `geo_s1_exact_closure_v0_jax.py:133-150`.

The Julia/Symbolics leg is not an independent density-matrix derivation. It defines Bloch components equal to Hopf components before expanding:

> `x_bloch = ...`; `y_bloch = ...`; `x_hopf = ...`; `y_hopf = ...`.

Cites: `geo_s1_exact_closure_v0_julia.jl:70-87`.

The solver P1 route also encodes the same component formulas directly rather than the density construction:

> `x_bloch = 2 * (a * c + b * d)`; `y_bloch = 2 * (b * c - a * d)`; `x_hopf = ...`; `y_hopf = ...`.

Cites: `geo_s1_exact_closure_v0_jax.py:338-348`.

Finding: this is one genuine CAS leg plus a formula echo. It is not two independent CAS derivations of `Bloch(psi psi^dagger)` under an explicit pin.

## E3. Linking Three Routes

Verdict: FAIL overall.

### E3a. Crossing count from exact points

Partial. The PyTorch leg uses exact SymPy points:

> `eps = sp.Rational(1, 2)`; `roots = [sp.pi / 3, 5 * sp.pi / 3]`; points include `1/2` and `sqrt(3)/2`.

Cites: `geo_s1_exact_closure_v0_pytorch.py:64-83`; result `geo_s1_exact_closure_v0_pytorch_results.json:40-89`.

But the crossing signs are hard-coded:

> `# Convention fixed to match the positive Gauss orientation...`; `sign = sp.Integer(1)`.

Cites: `geo_s1_exact_closure_v0_pytorch.py:74-75`.

The JAX crossing route is hard-coded receipt data:

> `crossing_records = [...]`; each record has `"sign": 1`.

Cites: `geo_s1_exact_closure_v0_jax.py:462-505`; result `geo_s1_exact_closure_v0_jax_results.json:513-559`.

The P2 SMT check proves only the already-assigned integer:

> `solver.add(value == signed_sum)` and `solver.add(value != 2)`.

Cites: `geo_s1_exact_closure_v0_jax.py:413-438`; envelope proofs `geo_s1_exact_closure_v0_envelope_results.json:853-877`.

Finding: exact point types are present in the PyTorch leg, but the crossing signs and signed sum are not derived from an exact crossing-orientation computation.

### E3b. Closed-form Gauss route

Partial. The packet derives a symbolic circle-line Gauss integral:

> `circle = (cos(t), sin(t), 0)`, `line = (0,0,u)`, numerator `1`, integrand `(u**2 + 1)**(-3/2)`, `gauss_value = 1`.

Cites: `geo_s1_exact_closure_v0_jax.py:232-263`; result `geo_s1_exact_closure_v0_envelope_results.json:240-249`.

The blind sheet asked for two explicit Hopf fibers and an orientation-flip control:

> `F_N(t)` and `F_E(s)` over distinct base points; reversing one fiber orientation should flip the sign.

Cites: `/tmp/s1x_blind_expected_20260610.md:190-223`.

I found no exact orientation-flip control for the Gauss route. The only sign control is the scrambled crossing control, not reversing one Gauss fiber orientation.

Finding: the closed-form integral is exact for the circle-line model, but the route does not show the requested orientation-flip prediction/control.

### E3c. Interval route

Fail. The blind sheet requires:

> genuine interval arithmetic from inputs through final bound.

Cite: `/tmp/s1x_blind_expected_20260610.md:231`.

The Julia route computes:

> `a = interval(cutoff, cutoff)`; `finite_part = a / sqrt(1 + a^2)`; `tail_bound = 1.0 / (2.0 * cutoff^2)`; `contains_exact_one` compares against `1.0`.

Cites: `geo_s1_exact_closure_v0_julia.jl:113-127`; receipt `geo_s1_exact_closure_v0_julia_results.json:64-87`.

Finding: this is float-tailed boxing of a closed-form expression. It is not interval arithmetic from exact Gauss-integral inputs through the bound. This is also the main place where a float tolerance/path hides inside a claimed rigorous-bound row despite `bare_float_rows: 0`.

## E4. Closed-form Integrals

Verdict: PASS for X3.

The build card requires symbolic metric/integral derivations and visible double-cover division:

> chart integral `4pi^2 sin2eta / 2`; volume, base area, torus area as exact symbolic integrals.

Cites: `build_card.md:10`, blind sheet `/tmp/s1x_blind_expected_20260610.md:96-188`.

The SymPy source constructs the Hopf chart, Jacobian metric, determinant, chart integrals, and divides by 2:

> `volume_chart_integral = ...`; `volume_s3 = volume_chart_integral / 2`; `torus_chart_integral = ...`; `torus_area = torus_chart_integral / 2`.

Cites: `geo_s1_exact_closure_v0_jax.py:180-229`; result `geo_s1_exact_closure_v0_jax_results.json:87-120`.

The envelope records:

> `volume_chart_integral_before_double_cover_division = 4*pi**2`, `volume_s3 = 2*pi**2`, `torus_chart_integral_before_double_cover_division = 4*pi**2*sin(2*eta)`, `torus_area_eta = 2*pi**2*sin(2*eta)`.

Cites: `geo_s1_exact_closure_v0_jax_results.json:87-120`.

## E5. X6 Haar Statistic

Verdict: PASS with honest statistical-redundant ceiling.

The source derives exact rotation-invariant expectations:

> sphere density `sin(theta)/(4*pi)`, moment matrix integrals, pairwise cosine density `1/2`, and pairwise second moment.

Cites: `geo_s1_exact_closure_v0_jax.py:280-325`; result `geo_s1_exact_closure_v0_jax_results.json:297-355`.

The non-Haar control fails the statistic as intended:

> `max_second_moment_deviation_from_one_third = 0.33331876518351217`; `must_fail_threshold >= 0.02`; `pass: true`.

Cites: `geo_s1_exact_closure_v0_jax_results.json:333-355`, envelope `geo_s1_exact_closure_v0_envelope_results.json:814-823`.

The table labels the sample row `statistical-redundant`, not symbolic:

> `achieved_strength: statistical-redundant`; reason says samples are diagnostics behind exact expected values.

Cites: `geo_s1_exact_closure_v0_envelope.py:128-151`, envelope result `geo_s1_exact_closure_v0_envelope_results.json:748-777`.

## E6. Classification Table

Verdict: FAIL.

Spot check 1, claimed-symbolic X1:

> Table says `Bloch density quotient equals the pinned Hopf map`, `achieved_strength: symbolic`.

Cites: `geo_s1_exact_closure_v0_envelope.py:89-96`.

Actual: the required convention PIN is absent and one leg is a component echo, so this row is overclaimed.

Spot check 2, X4:

> Table says `Hopf fibers have linking number 1`, `achieved_strength: closed-form+rigorous-bound`, with interval enclosure.

Cites: `geo_s1_exact_closure_v0_envelope.py:113-119`; envelope result `geo_s1_exact_closure_v0_envelope_results.json:235-335`.

Actual: crossing signs are hard-coded, the Gauss orientation-flip control is absent, and the interval route is float-tailed closed-form boxing rather than interval arithmetic through the integrand. This row is overclaimed.

Spot check 3, MC/statistical row:

> Table says prior Monte Carlo/convergence rows are `statistical-redundant`, retained only as diagnostics.

Cites: `geo_s1_exact_closure_v0_envelope.py:145-151`; envelope result `geo_s1_exact_closure_v0_envelope_results.json:768-777`.

Actual: this label matches the computation type.

Finding: the table's `bare_float_tolerance: false` entries do not catch the float-tailed X4 interval path. `bare_float_rows: 0` is not accepted as an audit conclusion.

## E7. Standard Checks

Verdict: MIXED.

Pass:

- Strict validator with `--require-pytorch --strict-source-backed` returned `ok: true`.
- Envelope ceiling is `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- Envelope lineage says `geo_s1_spinor_hopf_free_v0@013fb0fa1` and `modified_lineage_packet=false`.
- `git status --short -- system_v6/sims/geo_s1_spinor_hopf_free_v0 system_v6/sims/geo_s1_exact_closure_v0` showed the S1 lineage packet untouched and the exact-closure folder untracked: `?? system_v6/sims/geo_s1_exact_closure_v0/`.

Cites: envelope `geo_s1_exact_closure_v0_envelope_results.json:887-900`, `geo_s1_exact_closure_v0_envelope_results.json:1110-1125`.

Fail / caveat:

- P1 SMT inherits the unpinned sign convention because the polynomial identity is encoded directly in Hopf-y coordinates.
- P2 SMT proves the assigned integer `signed_sum == 2`, not the exact crossing-sign derivation from geometry.
- PyTorch is present, but its load-bearing claim is weakened because the signs are hard-coded before tensor summation.

Cites: `geo_s1_exact_closure_v0_jax.py:338-348`, `geo_s1_exact_closure_v0_jax.py:413-438`, `geo_s1_exact_closure_v0_pytorch.py:74-99`.

## Named Gaps

1. Missing explicit convention PIN: add a structured field naming `sigma_y_standard`, `Bloch basis`, `r_i = Tr(rho basis_i)`, and `Hopf_y = +2 Im(z1 conj(z2))`.
2. Julia X1 must derive from `rho = psi psi^dagger` and a pinned Pauli basis, not predeclared component equality.
3. Crossing signs must be computed from exact projected geometry/orientation, not assigned constants.
4. Gauss closed-form route needs an exact orientation-flip control that returns `-1`.
5. Interval route must propagate interval inputs through the Gauss integrand/bound, with no `1.0`/float-tailed comparison on the claim path.
6. Classification table must demote X1 and X4 until the above are fixed; `bare_float_rows: 0` is currently too strong.

## VERDICT

REJECT AS CLAIMED.

The packet is useful as a `scratch_diagnostic`, and the validator/schema result is green, but the audit target was stronger than schema validity. E1, E2, E3, and E6 fail. The exact closure claim is not accepted because the sign pin is not explicit, one CAS leg echoes formulas, the linking/crossing route hard-codes signs, and the claimed interval route contains float-tailed boxing rather than genuine interval arithmetic from inputs through bound.

Ceiling remains: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, no canonical/admitted status.

---

# Fresh Re-Audit Verdict v2: geo_s1_exact_closure_v0

Date: 2026-06-10T07:47:06Z.

Scope: read-only re-audit of v2 sources/results under `system_v6/sims/geo_s1_exact_closure_v0/`, except this append. I did not rerun the leg scripts because they overwrite result JSONs. I ran validators, source-hash checks, and independent recomputations against the current sources/results and `/tmp/s1x_blind_expected_20260610.md`.

Fresh validator:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json
=> {"ok": true, "result_json": "system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json"}
```

Runtime/env check:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py --skip-julia
=> ok=True install_state=stable_observed; no repo-local env pollution, missing expected modules, or active installers observed.
```

Source/result binding: recomputed SHA-256 for all four current sources and matched the result receipts exactly: Julia `f52dc997fb78fe06a615066dc3fd47e32044079a0a712bb2d3800dd31e422204`, JAX `25d15ea849e09857388362302d5dfe454288c238052181cc83fa5fb6367fa8d1`, PyTorch `90bbed33d4078283d67188cac561ea42da62e71b8cb05b0d71be4158654e5444`, envelope `bcaa2aae1861efe4d3dc4eaac77be623af7862641d0b0c101b2a0cd35efd715e`. The envelope also reports all V1-V6 gates true. Cites: `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json:1408-1450`.

## E1 / V1. Sign Pin

Verdict: CLOSED.

The old failure was missing explicit convention pin. v2 now carries the structured pin: standard `sigma_y`, pinned basis `(sigma_x, -sigma_y_standard, sigma_z)`, `r_i = Tr(rho * basis_i)`, Hopf-y `+2 Im(z1*conj(z2))`, and the derived standard-vs-pinned y story. Cites: `system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_julia.jl:27-40`, `system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_jax.py:37-58`, `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json:1097-1112`.

Receipt check: both CAS receipts emit `standard_sigma_y_trace_expanded = 2*a*d - 2*b*c`, `standard_sigma_y_trace_plus_hopf_y_expanded = 0`, and `bloch_minus_hopf_expanded = [0,0,0]` under the pinned basis. Cites: `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json:24-120`, `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json:130-224`.

Independent recomputation:

```text
std_minus_expected = [0,0,0] for standard Bloch compared to (x,-y,z)
pinned_minus_hopf = [0,0,0]
std_y_plus_hopf_y = 0
```

This matches the blind sheet's sign derivation.

## E2 / V2. Two-CAS Density Derivation

Verdict: CLOSED.

The old failure was Julia echoing predeclared component equalities. v2 Julia constructs `psi`, then `rho = reshape(psi,2,1) * reshape(conj.(psi),1,2)`, defines standard and pinned Pauli bases, and computes `bloch = tr(rho * basis)` before comparing to Hopf. Cites: `system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_julia.jl:84-104`. The v2 JAX/SymPy leg independently constructs `rho = psi * psi.conjugate().T` and traces the pinned basis. Cites: `system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_jax.py:150-170`.

Receipt check: both result paths include non-empty `rho_from_psi_psidagger`, pinned Pauli basis, expanded Bloch-from-trace components, and zero expanded differences. Cites: `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_julia_results.json:15-118`, `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json:24-224`.

The P1 z3/cvc5 formulas still encode component polynomials directly, but the V2 acceptance target was the two CAS derivations from `rho`; those now exist. Solver flips pass separately. Cites: `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json:1113-1136`.

## E3 / V3-V5. Linking Routes

Verdict: CLOSED for the v2 card's V3-V5 gates, with the interval route ceiling noted below.

V3 crossing signs: closed. The old failure was hardcoded crossing signs. v2 JAX computes each sign from exact roots, exact projected tangents, exact z-order, and `exact_sign(orientation_det)`. Cites: `system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_jax.py:501-556`. PyTorch independently mirrors the exact crossing computation and only tensors the computed signs after the exact records are built. Cites: `system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_pytorch.py:94-164`.

Receipt check: both crossings carry `orientation_determinant_ordered_over_under`, `z_delta_line_minus_circle`, and `computed_sign`; signed sum is `2`, linking number is `1`, and the scrambled control sum is `0`. Cites: `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json:339-380`, `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_pytorch_results.json:24-115`.

Independent recomputation:

```text
crossing_recs = [
  (pi/3, sqrt(3)/2, sqrt(3)/2, +1),
  (5*pi/3, -sqrt(3)/2, sqrt(3)/2, +1),
]
signed_sum = 2
signed_sum/2 = 1
```

V4 orientation flip: closed. v2 computes the compactified-line Gauss route and its reversed-fiber control. Cites: `system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_jax.py:263-309`. Independent recomputation returned:

```text
gauss_value = 1
reversed_gauss_value = -1
```

V5 interval propagation: closed for genuine interval propagation. The old failure was float-tailed boxing. v2 Julia now computes an interval Riemann sum over interval-valued subdomains through `f(u)=(1+u^2)^(-3/2)`, then adds an interval tail. Cites: `system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_julia.jl:144-179`, `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_julia_results.json:135-169`.

Independent Julia type/path recomputation under the recorded isolated project `@codex-ratchet-tensorkit-v1.12` returned:

```text
active_project=/Users/joshuaeisenhart/.julia/environments/codex-ratchet-tensorkit-v1.12/Project.toml
total_type=Interval{Float64}
tail_type=Interval{Rational{Int64}}
enclosure_type=Interval{Float64}
contains_one=true
tight_lower=0.9974500062481424
tight_upper=1.0025000012520549
tight_width=0.005049995003912455
coarse_contains_one=true
coarse_width=0.6616116523516821
```

Ceiling note: the strict carrier project does not currently import `IntervalArithmetic`; this interval receipt is valid as an isolated Julia interval route under the recorded `codex-ratchet-tensorkit-v1.12` project, not as strict-carrier package evidence. The envelope records that project in the foreign runtime manifest. Cites: `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json:1384-1396`.

## E6 / V6. Classification Table

Verdict: CLOSED.

The old failure was an overstated table and an unearned `bare_float_rows: 0`. v2 table rows now match the recomputed routes: X1 symbolic under the explicit sign pin, X4 `closed-form+rigorous-bound` backed by computed crossing signs, orientation-flip closed form, and interval propagation, X6 marked `statistical-redundant`, and prior Monte Carlo/convergence rows retained only as redundant diagnostics. Cites: `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json:796-893`.

Independent table recomputation from the current envelope table found zero rows with `bare_float_tolerance: true`, matching `bare_float_rows: {"count":0,"labels":[]}`. Cites: `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json:895-899`, `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json:1434-1442`.

## Verdict v2

E1, E2, E3, and E6 are CLOSED against the v2 sources/results and the v2 card's V1-V6 gates. The claim is EARNED at the stated packet ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. No canonical/admitted/formal-promotion status is implied.

## 2026-06-10 ott-Wasserstein Haar Addendum

Added an `ott` capability receipt to the S1 X6 Haar receipt as a new diagnostic row only. Exact rows are unchanged. The JAX leg now computes a Sinkhorn distance from the Hopf pushforward samples to a deterministic Fibonacci-sphere uniform proxy with `ott.geometry.pointcloud.PointCloud`, `ott.problems.linear.linear_problem.LinearProblem`, and `ott.solvers.linear.sinkhorn.Sinkhorn`.

Fresh receipt values:

```text
haar_reg_ot_cost = 0.23625525451293983
clustered_control_reg_ot_cost = 1.9302514046178747
calibrated_bar = haar < 0.35 and clustered > 1.0
```

The clustered north-pole control fails the uniformity bar as required. Fresh runs returned `ok:true` for the JAX, Julia, PyTorch, and envelope entrypoints. Fresh checks:

```text
validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json
=> {"ok": true}

audit_three_engine_source_claims.py --results-dir system_v6/sims/geo_s1_exact_closure_v0/results
=> source_backed_all_lanes, problems=[]
```
