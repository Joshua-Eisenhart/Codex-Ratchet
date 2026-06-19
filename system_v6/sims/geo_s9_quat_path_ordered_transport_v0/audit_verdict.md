# Fresh Audit Verdict: geo_s9_quat_path_ordered_transport_v0

Audit date: 2026-06-10
Audit mode: read-only except this `audit_verdict.md`
Calibrated bar: `system_v6/receipts/audit_bar_calibration_20260610.md`
Packet: `system_v6/sims/geo_s9_quat_path_ordered_transport_v0/`
Parent: committed `geo_s9_quaternionic_hopf_stack_v0`

## Verdict

VERDICT: GENUINE-WITH-CAVEATS.

This packet earns the narrow closure it was built for: the parent's G2 caveat is closed for the two named quaternionic Hopf/BPST comparison loops because the same parent planes now have path-ordered transport ODE holonomies, and the transported commutator gap recomputes to the committed algebraic gap `1.5` to roundoff.

Ceiling restated: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. This is fibration-level, loop-family-local transport evidence. It is not formal geometry admission, not continuum/global holonomy admission, not full nonabelian Stokes, not bridge/axis/physics evidence, and not evidence for untested loop families.

Named caveats:

- G1: The ODE integrators use endpoint unit renormalization, not a Lie-group integrator. This is honestly declared and the raw drift is recorded; the finest raw drift is at roundoff, and the deliberately coarse control has visible drift.
- G2: The U(1) contrast is numerically consistent with the committed S2 holonomy row, but not byte-identical to the committed symbolic row. Example: committed S2 stores `eta=pi/6`, `lifted_holonomy="-pi"`; this packet stores float target/result values near `-pi` with error about `9e-15`.
- G3: The small-loop row is leading-order only. The packet explicitly does not prove full surface-ordered nonabelian Stokes.
- G4: Closure is only for the two named loops `(x0,x1)->i` and `(x0,x2)->j`, calibrated to `theta=pi/3`. Other loop families remain open.

## Commands And Checks

Read-only validator:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/geo_s9_quat_path_ordered_transport_v0/results/geo_s9_quat_path_ordered_transport_v0_envelope_results.json --require-source-backed
-> {"ok": true, "result_json": "system_v6/sims/geo_s9_quat_path_ordered_transport_v0/results/geo_s9_quat_path_ordered_transport_v0_envelope_results.json"}
```

Independent stored-output recomputation:

```text
Julia gap recomputed = 1.5000000000000009
JAX gap recomputed   = 1.4999999999999976
Parent algebraic gap = 1.4999999999999998
Julia gap-parent diff = 1.1102230246251565e-15
JAX gap-parent diff   = 2.220446049250313e-15
Envelope gate failures = []
```

Current source hashes recomputed:

```text
geo_s9_quat_path_ordered_transport_v0_julia.jl    e5fd02f8dca03ec7ad596323e125db53563ca79f9a64a7a8714726503fe74e7b
geo_s9_quat_path_ordered_transport_v0_jax.py      7bf111a3eca152b912ce7031e40660068d65952a535c6e1f2073849eec4ba673
geo_s9_quat_path_ordered_transport_v0_envelope.py b6e678831e9e4a8eb04812ab4f4eb0a31265812056ddcb1bb108e3c78fbfddee
```

## Q1 - Real Transport

Adjudication: PASS WITH G1.

Source quotes:

- Julia connection: `return [0.0, prod[2], prod[3], prod[4]] ./ (1.0 + dot(x, x))` for `bpst_a_t` (`geo_s9_quat_path_ordered_transport_v0_julia.jl:134-139`).
- Julia ODE: `du[:] = qmul(-at, collect(u))`, then `solve(prob, Vern9(); reltol=1.0e-11, abstol=1.0e-13, dtmax=1.0 / n_per_segment, save_everystep=false)` (`geo_s9_quat_path_ordered_transport_v0_julia.jl:147-154`).
- Julia unit handling: `max_raw_norm_drift = ... abs(norm(q) - 1.0)` and `q = qnormalize(q)` with method text `segment endpoint unit renormalization with raw drift recorded` (`geo_s9_quat_path_ordered_transport_v0_julia.jl:156-165`).
- JAX/Python ODE: `return qmul_jnp(-a_t, y)` with `diffrax.Dopri8()` and `diffrax.ConstantStepSize()` (`geo_s9_quat_path_ordered_transport_v0_jax.py:202-219`).
- JAX/Python unit handling: raw drift recorded before `q = qnormalize(q)` and method text `diffrax.Dopri8 constant step dt=1/N, segment endpoint unit renormalization with raw drift recorded` (`geo_s9_quat_path_ordered_transport_v0_jax.py:221-230`).

Convergence is real in stored rows. Julia loop 1 angles at `n=32,64,128,256` are `1.047197551196597`, `1.0471975511965976`, `1.0471975511965972`, `1.0471975511965983`; recomputed Richardson with order 9 gives limit `1.0471975511965983`, error bar `0.0`, last delta `1.1102230246251565e-15`. JAX loop 1 gives limit `1.0471975511965963`, error bar `0.0`, last delta `1.5543122344752192e-15`.

The `0.0` error bar is a roundoff artifact from the last stored value equaling the extrapolated float. The honest convergence evidence is the step sequence plus the last-step delta, not the literal zero as a rigorous bound.

## Q2 - Comparison Row

Adjudication: PASS.

Source quotes:

- The source pin names the parent and loop planes: `parent=geo_s9_quaternionic_hopf_stack_v0 read_only` and `loops=(x0,x1)->i,(x0,x2)->j` (`geo_s9_quat_path_ordered_transport_v0_julia.jl:30`, `geo_s9_quat_path_ordered_transport_v0_jax.py:35-42`).
- Julia receipt says `same parent planes: rectangle in (x0,x1) gives i holonomy; rectangle in (x0,x2) gives j holonomy` (`geo_s9_quat_path_ordered_transport_v0_julia.jl:227-228`).
- Parent algebraic row stores `noncommuting_product_difference_norm: 1.4999999999999998` and the loop model `curvature-generated small rectangle loops at the BPST chart basepoint: (x0,x1) -> i and (x0,x2) -> j` (`geo_s9_quaternionic_hopf_stack_v0` envelope result).

Hand recomputation from stored transported holonomies:

```text
Julia h1 = [0.4999999999999995, 0.8660254037844389, 0.0, 0.0]
Julia h2 = [0.4999999999999995, 0.0, 0.8660254037844389, 0.0]
h1*h2 = [0.2499999999999995, 0.433012701892219, 0.433012701892219, 0.7500000000000004]
h2*h1 = [0.2499999999999995, 0.433012701892219, 0.433012701892219, -0.7500000000000004]
||h1*h2 - h2*h1|| = 1.5000000000000009
```

JAX recomputes the same row to `1.4999999999999976`. The packet does not smooth the row to `1.5`; the envelope records both engine values and their cross-engine difference `3.3306690738754696e-15`.

## Q3 - Small-Loop Limit

Adjudication: PASS WITH G3.

Source quotes:

- The check uses stored transport against `qexp(1, 2.0 * side^2)` (`geo_s9_quat_path_ordered_transport_v0_julia.jl:267-280`).
- The boundary is explicit: `leading-order nonabelian Stokes only; no surface-ordered full nonabelian Stokes theorem is proved` (`geo_s9_quat_path_ordered_transport_v0_julia.jl:282-285`).

Recomputation from stored rows:

```text
side=0.12 distance=0.0005420430921481302 distance/side^4=2.6140195416094247
side=0.08 distance=0.00010825710956351156 distance/side^4=2.642995838952919
side=0.04 distance=0.000006811410796308934 distance/side^4=2.6607073423081773
side=0.02 distance=0.00000042642787368171806 distance/side^4=2.6651742105107377
```

Distance shrinks under loop-size reduction, and the scaled distance is stable at the expected leading-order error scale. This supports `transport -> exp(curvature area)` at leading order only.

## Q4 - Abelian Contrast

Adjudication: NUMERIC PASS, BYTE-CONSISTENCY FAIL WITH G2.

Source quotes:

- The U(1) transport ODE is `du[1] = -cos(2.0 * eta) * (2.0 * pi)` and the target is `-2.0 * pi * cos(2.0 * eta)` (`geo_s9_quat_path_ordered_transport_v0_julia.jl:291-299`).
- The receipt source string names `geo_s2_connection_flux_foliation_v0: lifted_holonomy=-2*pi*cos(2*eta), rows eta=pi/12,pi/6,pi/4,pi/3,5pi/12` (`geo_s9_quat_path_ordered_transport_v0_julia.jl:310-314`).
- The committed S2 envelope stores `eta: "pi/6"` and `lifted_holonomy: "-pi"` (`geo_s2_connection_flux_foliation_v0_envelope_results.json:1313-1316`).

Stored row check for `eta=pi/6`:

```text
Committed S2 symbolic row: -pi
Julia target float:        -3.141592653589794
Julia transported result:  -3.141592653589785
Julia abs_error:           8.881784197001252e-15
JAX transported result:    -3.1415926535897847
JAX abs_error:             9.325873406851315e-15
```

So the abelian machinery reproduces the committed value numerically within diagnostic-float tolerance, and U(1) commutator gap is zero, but it is not byte-consistent with the committed symbolic row.

## Q5 - Controls

Adjudication: PASS.

Controls recomputed from stored envelope:

```text
zero-curvature identity distance: Julia 0.0, JAX 0.0
reverse loop inverse distance:   Julia 0.0, JAX 0.0
coarse raw norm drift:           Julia 0.07188834341880224, JAX 0.07188834341880224
cross-engine commutator diff:    3.3306690738754696e-15
```

The deliberately coarse Euler control fires visibly. The refined transport rows converge to roundoff. The SMT erased-flip polarity also fires: z3 positive identity is `unsat`, z3 erased flip is `sat`; JAX/Python also records cvc5 positive identity `unsat` and cvc5 erased flip `sat`.

## Q6 - Standard

Adjudication: PASS WITH G1/G2.

What checked:

- Parent lineage hashes are recorded for parent envelope/source/JAX/Julia paths, with `read_only: true`.
- Julia leg is real: `DifferentialEquations` is load-bearing for `Vern9` transport and `Z3` is load-bearing for the erased-flip identity check.
- Python/JAX leg is real: `diffrax` is load-bearing for `Dopri8` transport, and `z3`/`cvc5` are load-bearing for erased-flip identity checks.
- Mode is honest: `julia_differentialequations_plus_python_high_order_diagnostic`; PyTorch is excluded because no graph/network/autograd claim path is scoped.
- Tool calls are one-to-one for claim-path tools; the envelope gate passes.
- No `fixture`, `mock`, `stub`, `dummy`, or `fabricated` wording was found in the packet.
- Versions/capabilities are present: Julia `1.12.6`, active project `system_v5/julia_carrier/Project.toml`, `diffrax 0.7.2`, `jax 0.10.1`, `cvc5 1.3.3`, `numpy 2.3.4`; z3 Python version is recorded as `unknown` but the tool call and verdict are present.
- Seeds: no RNG; deterministic explicit loops, ODE tolerances, and finite SMT constants.
- Ceilings are exact: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

The main standard caveat is not missing machinery; it is claim hygiene. The packet's strongest safe wording is "transport-backed diagnostic for the two specified loops," not global holonomy or formal nonabelian-Stokes evidence.

## Q7 - Closure

Adjudication: CLOSES THE PARENT G2 CAVEAT FOR THE SPECIFIED ROW ONLY.

The parent caveat was that its G2/nonabelian row was algebraic curvature-generated, not path-ordered transport. This packet closes that caveat for the same two comparison loops: it integrates the parallel-transport ODE in Julia and Python/JAX, recomputes the same noncommutative product gap, passes reverse/flat/coarse controls, and keeps the claim ceiling explicit.

What stays open:

- full surface-ordered nonabelian Stokes;
- continuum/global holonomy admission;
- other loop families and non-rectangular paths;
- stronger bridge/axis/physics claims;
- formal/admitted geometry status.

Final allowed citation: `geo_s9_quat_path_ordered_transport_v0` is a genuine scratch diagnostic upgrading the parent's fibration-level noncommutation row from algebraic-only to transport-backed for the two named loops, with caveats G1-G4 preserved.

No git add or git commit was performed by this audit.
