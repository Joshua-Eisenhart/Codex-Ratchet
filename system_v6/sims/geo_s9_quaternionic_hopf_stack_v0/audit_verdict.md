# Fresh Audit Verdict: geo_s9_quaternionic_hopf_stack_v0

Audit date: 2026-06-10
Audit mode: read-only except this `audit_verdict.md`
Calibrated bar: `system_v6/receipts/audit_bar_calibration_20260610.md`
Packet: `system_v6/sims/geo_s9_quaternionic_hopf_stack_v0/`

## Verdict

VERDICT: GENUINE-WITH-CAVEATS.

The depth-frontier packet earns the requested scratch-diagnostic treatment of the quaternionic Hopf stack: the map is implemented with the pinned `C^4 ~= H^2` convention, the right `Sp(1)` fiber action recomputes, the `c2=1` normalization recomputes, the concurrence identity is symbolic before QuTiP float checks, the foliation/marginal row is self-contained, and the Adams/sedenion boundary is fenced as theorem-backed boundary only.

Ceiling restated: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. This packet does not admit canonical geometry, bridge/axis, physics, Standard Model, spacetime, octonionic-build, fifth-fibration, or formal-admission claims.

Named caveats:

- G1: The holonomy row is fibration-level noncommutation evidence, but the packet does not literally label it `N01`. It is labeled as `nonabelian_holonomy_boundary` / "nonabelian holonomy contrast"; the audit accepts the computation and flags the missing row label.
- G2: The holonomy computation is algebraic curvature-generated stored holonomy data, not a full path-ordered BPST transport integration. It is valid for the packet's scratch diagnostic fibration contrast, not for a stronger continuum holonomy claim.
- G3: Capability receipts are adequate but thin for version provenance. QuTiP and Quaternions/project receipts are explicit; z3/cvc5/SymPy are source-backed by tool calls and passing validator gates, but their package versions are not separately recorded.

## Commands And Checks

Read-only checks run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/geo_s9_quaternionic_hopf_stack_v0/results/geo_s9_quaternionic_hopf_stack_v0_envelope_results.json --require-source-backed
-> {"ok": true, "result_json": "...geo_s9_quaternionic_hopf_stack_v0_envelope_results.json"}
```

Source/result hash binding checked:

```text
geo_s9_quaternionic_hopf_stack_v0_jax.py      297f0c8a4f9e31711114a658db72de8da563c1d9df37ef446ad7846ffeee11c0
geo_s9_quaternionic_hopf_stack_v0_julia.jl    bede8645bc9becc6d20400d6727da300bddb4111af72ed230fb32c5165df62ec
geo_s9_quaternionic_hopf_stack_v0_envelope.py f1facd18e9da938d70a41ca26619861e9323f4d41cf0d90062e03dda3bdd9c6f
```

The stored result JSONs record the same source hashes.

Independent recomputation summary:

```text
Q1 right Sp(1) random deviations = [1.6653345369377348e-16, 2.220446049250313e-16, 1.1102230246251565e-16]
Q1 left-action control deviations = [0.36834209622666925, 1.3177680870140902, 0.6099995498540719]
Q2 radial integral = 1/12; full integral = 8*pi**2; c2 = 1; wrong orientation = -1
Q3 product concurrence = 0; Bell concurrence = 0.9999999999999998
Q3 theta=pi/8 interior concurrence = sqrt(2)/2 = target sin(2theta)
Q4 stored holonomy commutator gap = 1.4999999999999998; U(1) contrast gap = 0.0
Q5 eta integral = 1/12; Vol(S7) = pi**4/3; beta norm = 1; beta mean = 1/2
Q7 envelope validator = ok; gate failures = []
```

## Q1 - The Map Genuine

Adjudication: PASS.

Source quotes:

- Pin/source convention: `psi=(a,b,c,d) in C4 normalized=S7 2Q state|q1=a+b*j,q2=c+d*j` and `Hopf_H=(2*q1*conj(q2),abs2(q1)-abs2(q2))` (`geo_s9_quaternionic_hopf_stack_v0_julia.jl:26`, `geo_s9_quaternionic_hopf_stack_v0_jax.py:36-42`).
- Implementation: `qfrom_complex_pair(z[1], z[2]), qfrom_complex_pair(z[3], z[4])`, then `w = 2.0 * (q1 * conj(q2))` (`geo_s9_quaternionic_hopf_stack_v0_julia.jl:100-113`).
- Fiber side: `right_sp1_action` computes `state_from_qpair(q1 * u, q2 * u)` (`geo_s9_quaternionic_hopf_stack_v0_julia.jl:124-127`).
- Receipt statement: `(q1,q2)->(q1*u,q2*u) leaves H fixed` (`geo_s9_quaternionic_hopf_stack_v0_julia.jl:223`).

Recomputation: for one normalized `C^4` point and three deterministic random unit quaternions, right multiplication fixed the Hopf image to max deviation `2.220446049250313e-16`. The same test with left multiplication moved the image by `0.368`, `1.318`, and `0.610`, pinning the side convention. Stored Julia receipt reports `right_sp1_orbit_invariance_max_deviation = 4.440892098500626e-16` and constructive fiber residual `7.043575467574348e-16`.

The packet explicitly identifies `S^7 = normalized C^4 = 2Q state` in the pin and states the quaternion-to-`C^2` convention `q1=a+b*j, q2=c+d*j`.

## Q2 - c2 = 1

Adjudication: PASS.

Source quotes:

- Python exact leg computes `radial = integrate(r**3/(1+r**2)**4, 0..oo)`, `integral = 48 * 2*pi**2 * radial`, then `c2 = integral/(8*pi**2)` (`geo_s9_quaternionic_hopf_stack_v0_jax.py:293-298`).
- Pinned convention: `normalization: c2 = (1/(8*pi^2))*int tr(F wedge F)` (`geo_s9_quaternionic_hopf_stack_v0_jax.py:312`).
- Trace/orientation pins: `tr_sp1(e_a e_b)=-2*delta_ab` and `dvol_S4 = -dx0^dx1^dx2^dx3` (`geo_s9_quaternionic_hopf_stack_v0_jax.py:307-309`).
- Julia mirror states `1/(8*pi^2) * int tr(F^F) = 1` and wrong orientation `-1` (`geo_s9_quaternionic_hopf_stack_v0_julia.jl:312-323`).

Recomputation: `int_0^infty r^3/(1+r^2)^4 dr = 1/12`; multiplying by `48 * Vol(S3) = 48 * 2*pi^2` gives `8*pi^2`; dividing by `8*pi^2` gives `c2=1`. The wrong-orientation control flips to `-1`, matching both stored receipts.

Hand normalization: with the packet's trace pin and orientation pin, the stated density integrates to `8*pi^2`; the stated `1/(8*pi^2)` convention therefore gives exactly `+1`.

## Q3 - Concurrence Identity

Adjudication: PASS.

Source quotes:

- Symbolic route defines real/imag determinant parts and proves `concurrence_squared - jk_block_squared == 0` (`geo_s9_quaternionic_hopf_stack_v0_jax.py:171-183`).
- Basis pin: `psi=(a,b,c,d) in |00>,|01>,|10>,|11>; q1=a+b*j, q2=c+d*j` (`geo_s9_quaternionic_hopf_stack_v0_jax.py:184`).
- Exact identity: `C=sqrt(J^2+K^2)=2|a*d-b*c|` (`geo_s9_quaternionic_hopf_stack_v0_jax.py:195`).
- Product-state control: product determinant simplifies to `0` (`geo_s9_quaternionic_hopf_stack_v0_jax.py:180-197`).
- QuTiP is a side/cross-check, not the source of the identity: it uses `qutip.Qobj/qutip.concurrence` after the symbolic row (`geo_s9_quaternionic_hopf_stack_v0_jax.py:149-151`, `geo_s9_quaternionic_hopf_stack_v0_jax.py:238-255`).

Recomputation:

- Product state `|00>` maps to coordinates `[0,0,0,0,1]`; concurrence `0`.
- Bell state `(|00>+|11>)/sqrt(2)` maps to `[0,0,-1,0,0]` up to float roundoff; concurrence `0.9999999999999998`.
- Interior family point `theta=pi/8`, `cos(theta)|00> + sin(theta)|11>` has exact concurrence `sqrt(2)/2`, matching `sin(2theta)` and `sqrt(J^2+K^2)`.

The stored QuTiP max gap is `1.1780402431327275e-08`. Because the symbolic identity is present and exact before the QuTiP row, this is float/library noise, not the load-bearing evidence.

The committed `geo_s1_two_qubit_boundary_exact_v0` anchor is git-tracked and records `product_concurrence_squared=0`, `bell_concurrence_squared=1`; S9 binds those values by name in the Julia and Python receipts (`geo_s9_quaternionic_hopf_stack_v0_julia.jl:276-279`, `geo_s9_quaternionic_hopf_stack_v0_jax.py:284-288`).

## Q4 - Nonabelian Holonomy

Adjudication: PASS WITH G1/G2.

Source quotes:

- Stored loop model: `curvature-generated small rectangle loops at the BPST chart basepoint: (x0,x1) -> i and (x0,x2) -> j` (`geo_s9_quaternionic_hopf_stack_v0_jax.py:353-355`).
- Formula: `||exp(theta*i)exp(theta*j)-exp(theta*j)exp(theta*i)|| = 2*sin(theta)^2` (`geo_s9_quaternionic_hopf_stack_v0_jax.py:359-360`).
- U(1) contrast: `U(1) phase holonomies commute for the complex Hopf row` (`geo_s9_quaternionic_hopf_stack_v0_jax.py:362-363`).
- Boundary/contrast gate: envelope has `nonabelian_holonomy_boundary` and the claim says `nonabelian holonomy contrast` (`geo_s9_quaternionic_hopf_stack_v0_envelope.py:184-190`, `geo_s9_quaternionic_hopf_stack_v0_envelope.py:218`).

Stored-data recomputation:

```text
h1 = (0.5, 0.8660254, 0, 0)
h2 = (0.5, 0, 0.8660254, 0)
h1*h2 = (0.25, 0.4330127, 0.4330127, 0.75)
h2*h1 = (0.25, 0.4330127, 0.4330127, -0.75)
||h1*h2 - h2*h1|| = 1.4999999999999998
U(1) contrast gap = 0.0
```

This is real noncommutativity at the fibration/fiber level. It is not overclaimed into physics or spacetime. Caveat G1 remains because the packet does not literally label this row `N01`; caveat G2 remains because this is an algebraic curvature-generated holonomy row, not path-ordered continuum transport.

## Q5 - Foliation And Marginal

Adjudication: PASS.

Source quotes:

- Python exact row integrates `cos(eta)^3*sin(eta)^3`, computes `s7_volume`, and computes the `6*r*(1-r)` marginal norm and mean (`geo_s9_quaternionic_hopf_stack_v0_jax.py:319-338`).
- Leaf statement: `S3_{cos eta} x S3_{sin eta}` and `4*pi^4*cos(eta)^3*sin(eta)^3` (`geo_s9_quaternionic_hopf_stack_v0_jax.py:328-330`).
- Julia independently states the metric, leaf geometry, total volume integral, eta density, and beta marginal (`geo_s9_quaternionic_hopf_stack_v0_julia.jl:329-347`).

Recomputation:

```text
int_0^{pi/2} cos^3(eta) sin^3(eta) d eta = 1/12
4*pi^4 * 1/12 = pi^4/3 = Vol(S7)
int_0^1 6*r*(1-r) dr = 1
int_0^1 r*6*r*(1-r) dr = 1/2
```

This row is self-contained. It does not depend on the disintegration lane. Any consistency with the committed `S^3` disintegration packet is bonus context, not load-bearing here.

## Q6 - Boundary Rows

Adjudication: PASS.

Source quotes:

- Ladder: `S0 -> S1 -> S1`, `S1 -> S3 -> S2`, `S3 -> S7 -> S4`, `S7 -> S15 -> S8` (`geo_s9_quaternionic_hopf_stack_v0_jax.py:371-375`, `geo_s9_quaternionic_hopf_stack_v0_julia.jl:361-365`).
- Adams boundary: theorem-backed allowed base dimensions `[1,2,4,8]` and no fifth sphere Hopf fibration (`geo_s9_quaternionic_hopf_stack_v0_jax.py:377-381`).
- Julia says `boundary row only` and blocks a sedenion-style continuation (`geo_s9_quaternionic_hopf_stack_v0_julia.jl:368-370`).

The packet states the four-fibration ladder and treats Adams/sedenion/no-further as boundary only. It does not claim the octonionic rung is built, and the envelope forbids both `octonionic S7->S15->S8 built` and `fifth Hopf fibration` claims (`geo_s9_quaternionic_hopf_stack_v0_envelope.py:264-270`).

## Q7 - Standard Controls, Tools, Seeds, Ceilings

Adjudication: PASS WITH G3.

Source/result evidence:

- Controls fired: separable-locus, shuffled/permuted-state, wrong-convention c2, degenerate foliation, erased SMT flip, and U(1) contrast all fired in the envelope controls.
- SMT polarity: Julia Z3 and Python z3/cvc5 prove the positive finite identity unsat and erased flip sat (`geo_s9_quaternionic_hopf_stack_v0_envelope.py:191-199`).
- One-to-one tool calls: envelope gate `tool_calls_one_to_one` passed (`geo_s9_quaternionic_hopf_stack_v0_envelope.py:206-209`).
- Claim tools: `Quaternions`, `Z3`, `z3`, `cvc5`, `qutip`, `sympy`.
- Capability receipts: QuTiP version `5.2.3`; Quaternions constructor and Julia active project recorded; z3/cvc5/SymPy have function-level tool-call receipts and passing source-backed validator, but no separate version strings.
- Seeds: envelope says `rng: none` and deterministic rows are Julia trigonometric grid, Python symbolic rows, finite integer SMT domain, and named QIT states.
- Mode: `julia_canon_plus_jax_diagnostic`; PyTorch is explicitly excluded because no graph/network/autograd claim path is scoped (`geo_s9_quaternionic_hopf_stack_v0_envelope.py:230-237`).
- Ceilings: envelope and legs all record `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- Fixture wording: scan found no `fixture`, `mock`, or `dummy` wording in the S9 packet.
- Physics/SM/spacetime scan: no physics, Standard Model, or spacetime claims found. Envelope fences block bridge/axis-level and stronger geometry claims.

The committed `geo_s1_two_qubit_boundary_exact_v0` anchor is tracked by git and its source-backed result passes; S9 uses only the product/Bell concurrence pins from that anchor, while deriving the S4/concurrence identity locally and symbolically.

## Final Ceiling

Use this packet as a genuine scratch diagnostic for:

- quaternionic Hopf map/fiber convention for `S3 -> S7 -> S4`;
- `c2=1` under the pinned trace/orientation/normalization convention;
- exact two-qubit concurrence detection as the `J,K` block norm on the S4 base;
- algebraic nonabelian `Sp(1)` holonomy contrast against abelian U(1);
- self-contained `S3 x S3` foliation and beta marginal row;
- theorem-backed Adams/four-rung boundary placement.

Do not cite it as formal admission, canonical geometry, full path-ordered gauge transport, octonionic construction, fifth-fibration evidence, physics/SM/spacetime evidence, or bridge/axis-level evidence.

No git add or git commit was performed by this audit.
