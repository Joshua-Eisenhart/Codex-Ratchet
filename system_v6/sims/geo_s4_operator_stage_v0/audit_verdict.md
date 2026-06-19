# Fresh Audit Verdict: geo_s4_operator_stage_v0

Audit date: 2026-06-10.

VERDICT: REJECT AS CLAIMED against the blind exactness bar.

The packet is a useful executable `scratch_diagnostic`, and the repo validators are green, but the audit target was stricter than self-consistency. The packet's dephasing affine rows, unitality, ellipsoid shape classes, fixed axes, quotient boundary, and ceiling mostly hold. The rotation rows are sign-flipped relative to `/tmp/s4_blind_expected_20260610.md`, and that propagates into the signed commutator table and SMT witnesses. Basin rows are also prose classifications, not explicit iterated-limit receipts.

There are two live readings:

1. Under the blind/source-locked right-handed active Bloch convention, `R_x` and `R_z` must have the blind signs. The packet fails that match.
2. Under the packet's pinned `-sigma_y_standard` coordinate convention, the packet's signs derive from the same unitary source forms. That makes the packet internally coherent, but it does not satisfy the blind instruction to match the expected matrices or explicitly adjudicate the sign flip as a convention fork.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Do not use this as canonical operator-family completion, Axis-level admission, formal admission, terrain-generator closure, engine/runtime closure, or physics evidence.

## Inputs And Pattern Binding

Inputs read:

- `system_v6/sims/geo_s4_operator_stage_v0/`
- `/tmp/s4_blind_expected_20260610.md`
- `system_v6/receipts/s4_build_spec_20260610.md`
- pattern catalog binding: `system_v6/sims/axis_independence_discriminators_036/audit_verdict.md` H1-H7
- pattern catalog binding: `system_v6/sims/geo_s1_exact_closure_v0/audit_verdict.md` E1-E6 and v2 closure notes

Binding applied from the pattern catalogs: validator success is not claim success; source-derived math must be separated from fixture/string echo; sign pins and two-CAS/honest-split claims must be checked substantively; can-fail controls must actually be capable of failure, not just `pass: true` declarations.

I did not rerun the leg or envelope builders because they write result JSONs. I ran only read-only validators and independent recomputations.

Fresh checks:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json
=> {"ok": true, "result_json": "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s4_operator_stage_v0/geo_s4_operator_stage_v0_exact_strength_validator.py system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json
=> {"errors": [], "ok": true, "result_json": "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json"}

## Remediation note - 2026-06-10

Tooling remediation step 3 rebuilt the S4 operator-channel route so the Julia canon leg now routes pinned density/channel mechanics through `QuantumOptics` superoperator objects, and the Python leg now routes pinned channel matrices, ellipsoid rows, and commutator rows through `qutip` Qobj/superoperator APIs. The prior hand Pauli/Bloch and PyTorch tensor rows remain only as controls/mirrors. Scientific claims and values are unchanged; the route is now load-bearing through the quantum-object APIs.

git status --short -- system_v6/sims/geo_s4_operator_stage_v0 system_v6/receipts/s4_build_spec_20260610.md
=> ?? system_v6/sims/geo_s4_operator_stage_v0/
```

The packet directory is untracked in this checkout.

## Quoted Source

Blind expected rotation convention:

```text
Right-handed active rotation convention used for expected matrices:
R_x(theta_x) = [[1,0,0],[0,C,-S],[0,S,C]]
R_z(phi_z) = [[U,-V,0],[V,U,0],[0,0,1]]
```

Cites: `/tmp/s4_blind_expected_20260610.md:32-44`.

Blind tripwire:

```text
if a builder uses passive rotations, row-vector action, or the opposite sigma_y sign, the S and V signs can flip
```

Cite: `/tmp/s4_blind_expected_20260610.md:53`.

Packet source derives affine rows from Kraus/unitary action, then compares to its own expected matrix table:

```python
channel_rhos = {"D_z": ..., "D_x": ..., "R_x": ux * rho * ux.conjugate().T, "R_z": uz * rho * uz.conjugate().T}
...
"matches_expected_formula": zero_matrix(diff) and all(sp.simplify(item) == 0 for item in c_vec)
```

Cites: `geo_s4_operator_stage_v0_jax.py:267-288`.

Packet expected rotation rows:

```python
"R_x": Matrix([[1,0,0],[0,cos(theta),sin(theta)],[0,-sin(theta),cos(theta)]])
"R_z": Matrix([[cos(phi),sin(phi),0],[-sin(phi),cos(phi),0],[0,0,1]])
```

Cites: `geo_s4_operator_stage_v0_jax.py:292-300`.

Source-locked older Bloch channel rows use the blind signs with standard `SY`:

```python
Fi: (rx, ry*cos(theta) - rz*sin(theta), rz*cos(theta) + ry*sin(theta))
Fe: (rx*cos(phi) - ry*sin(phi), rx*sin(phi) + ry*cos(phi), rz)
```

Cites: `source_locked_operator_base_packet_jax.py:200-221`.

## Hand Recomputation Packet

I recomputed the required minimum independently with SymPy: one `(M,c)` derivation, one fixed-point proof, one basin limit, and one commutator. I also recomputed the source-unitary rows under both standard and pinned-y bases to isolate the convention fork.

Affine rows:

```text
D_z recompute:
M = diag(1-q_z, 1-q_z, 1), c = (0,0,0)

R_x blind/right-handed:
[[1,0,0],[0,cos(theta_x),-sin(theta_x)],[0,sin(theta_x),cos(theta_x)]]
pinned theta=pi/2: [[1,0,0],[0,0,-1],[0,1,0]]

R_x packet/pinned-y:
[[1,0,0],[0,cos(theta_x),sin(theta_x)],[0,-sin(theta_x),cos(theta_x)]]
pinned theta=pi/2: [[1,0,0],[0,0,1],[0,-1,0]]

R_z blind/right-handed:
[[cos(phi_z),-sin(phi_z),0],[sin(phi_z),cos(phi_z),0],[0,0,1]]
pinned phi=pi/2: [[0,-1,0],[1,0,0],[0,0,1]]

R_z packet/pinned-y:
[[cos(phi_z),sin(phi_z),0],[-sin(phi_z),cos(phi_z),0],[0,0,1]]
pinned phi=pi/2: [[0,1,0],[-1,0,0],[0,0,1]]
```

Unitary derivation fork:

```text
U_x with standard sigma_y basis -> blind R_x signs.
U_x with pinned -sigma_y basis -> packet R_x signs.
U_z with standard sigma_y basis -> blind R_z signs.
U_z with pinned -sigma_y basis -> packet R_z signs.
```

Fixed-point proof recompute for `D_z`:

```text
(D_z - I) r = (-q_z*x, -q_z*y, 0)
For 0 < q_z <= 1, x = y = 0 and z is free.
Fixed set inside Bloch ball: {(0,0,z): |z| <= 1}.
```

Basin limit recompute for `D_z`:

```text
D_z^n(x,y,z) = ((1-q_z)^n x, (1-q_z)^n y, z).
For 0 < q_z < 1, limit_n D_z^n(x,y,z) = (0,0,z).
For q_z = 1, the projection is reached in one step.
```

Commutator recompute:

```text
[D_z,R_x]_blind =
[[0,0,0],[0,0,q_z*sin(theta_x)],[0,q_z*sin(theta_x),0]]
pinned q_z=3/10, theta=pi/2:
[[0,0,0],[0,0,3/10],[0,3/10,0]]

[D_z,R_x]_packet =
[[0,0,0],[0,0,-q_z*sin(theta_x)],[0,-q_z*sin(theta_x),0]]
pinned q_z=3/10, theta=pi/2:
[[0,0,0],[0,0,-3/10],[0,-3/10,0]]
```

The packet's commutator sign is internally consistent with its sign-flipped `R_x`, but it does not match the blind commutator table.

## Per-Check Adjudication

### O1. Ellipsoid `(M,c)` Per Channel Derived

Verdict: FAIL AS BLIND MATCH; PASS ONLY UNDER PACKET PINNED-Y CONVENTION.

`D_z` and `D_x` match the blind sheet exactly: symbolic diagonals, pinned `7/10` rows, and `c=0`. The source derives `c` by evaluating the channel at `r=0`, not by only writing a predeclared zero: `c_vec = ... item.subs({var: 0 for var in r_vars})` at `geo_s4_operator_stage_v0_jax.py:277-285`.

`R_x` and `R_z` do not match `/tmp/s4_blind_expected_20260610.md:89-124`. The packet emits the opposite `S` and `V` signs in both symbolic and pinned rows. The envelope records `R_x` pinned as `[[1,0,0],[0,0,1],[0,-1,0]]` and `R_z` pinned as `[[0,1,0],[-1,0,0],[0,0,1]]`; blind expects `[[1,0,0],[0,0,-1],[0,1,0]]` and `[[0,-1,0],[1,0,0],[0,0,1]]`.

Ellipsoid shape classifications still survive because sign-flipped rotations preserve singular values, rank, determinant, and sphere image. The handedness-sensitive affine rows do not survive the blind match.

### O2. Fixed-Point Sets And Basins

Verdict: FIXED SETS MATHEMATICALLY SURVIVE; BASIN RECEIPTS FAIL FORM.

Fixed sets match the blind set-level classifications for all four channels. The rotation sign flip does not change the fixed axes because the transverse determinant remains `2(1-cos angle)`.

Packet fixed-set source is static case data:

```python
"D_z": {"equations": ["-q_z*r_x=0", "-q_z*r_y=0", "0=0"], ...}
"R_x": {"equations": ["0=0", "(cos(theta_x)-1)*r_y + sin(theta_x)*r_z=0", ...], ...}
```

Cites: `geo_s4_operator_stage_v0_jax.py:362-394`.

The math is right under the packet convention, and the blind set-level answer is right, but the packet does not emit a solver trace or determinant derivation object for the fixed sets. I accept the fixed sets as source-plus-recompute facts, not as independently proven by the packet's result format alone.

Basins fail the blind tripwire as receipt form. The blind file says basin claims require iterated-limit receipts, not just fixed-point equations (`/tmp/s4_blind_expected_20260610.md:353-360`). The packet emits prose rows:

```python
"0<q_z<1": "all Bloch points converge to z-axis projection (0,0,r_z)"
"0<q_x<1": "all Bloch points converge to x-axis projection (r_x,0,0)"
```

Cites: `geo_s4_operator_stage_v0_jax.py:397-429`.

Those statements match my recomputed limits, but the packet does not carry explicit `D_z^n`, `D_x^n`, `a^n -> 0`, `b^n -> 0`, or trajectory-limit receipts. This is a named gap.

### O3. Symbolic Commutators And Fixed-Axis Proofs

Verdict: SYMBOLIC TABLE EXISTS; SIGNED TABLE FAILS BLIND.

The packet has all 16 ordered pairs and affine shift commutators are zero. The always-zero and structural-zero classifications match the blind sheet:

- `[D_z,D_x]=0`
- `[D_z,R_z]=0`
- `[D_x,R_x]=0`
- self-pairs commute

The nonzero signed rows are flipped wherever they depend on the rotation handedness. Example: blind pinned `[D_z,R_x]` is `+3/10` in the two off-diagonal entries; packet pinned `[D_z,R_x]` is `-3/10`. Packet pinned `[D_x,R_z]` is `+3/10`; blind expects `-3/10`. Packet pinned `[R_x,R_z]` is `[[0,1,-1],[1,0,1],[1,1,0]]`; blind expects `[[0,-1,-1],[-1,0,-1],[1,-1,0]]`.

Fixed-axis proofs survive at set level, but the rotation equations are sign-flipped relative to blind:

```text
Blind R_x equations: (C-1)y - S z = 0; S y + (C-1)z = 0.
Packet R_x equations: (C-1)y + S z = 0; -S y + (C-1)z = 0.
```

The determinant is the same, so the axis conclusion is the same. The signed route is not the blind route.

### O4. Unitality, Strength Tokens, Controls, SMT, CAS Split, PyTorch, Ceiling

Verdict: MIXED.

Unitality: PASS for the four scoped channels. The JAX derivation computes `c_vec`; every result row has `c=["0","0","0"]`; the envelope gate `affine_shifts_all_zero` is true.

Non-unitality: PASS as not scoped. The blind optional amplitude-damping row is not merged into the four base channels, and no nonzero shift is claimed for them.

Strength tokens: PASS for literal token discipline. The envelope receipts use `exact_symbolic_matrix_table`, `exact_case_classification`, `exact_integer_rational_pin`, `smt_can_fail_control`, `lineage_citation_only`, and `quotient_boundary_statement`.

Can-fail controls: FAIL IN SUBSTANCE except the narrow SMT controls. The packet's C1-C8 control rows are mostly declarative booleans such as `detected: true`, `selectivity_pass: true`, or `..._fails: true`. I found no mutation execution receipt showing the wrong-basis, fake-shift, rotation-as-contraction, dephase-as-rotation, numeric-only, or terrain-leakage controls actually reran and failed. This repeats the pattern-catalog failure mode from H4 in `axis_independence_discriminators_036/audit_verdict.md`.

Exact SMT where scoped: PASS NARROWLY, FAIL AS GENERAL SYMBOLIC PROOF. z3, cvc5, Julia Z3, and PyTorch z3/cvc5 all check a raw scaled pinned entry by asserting `entry == -3` and `entry == 0`, with a wrong-control SAT path. That is a real can-fail check for one pinned packet-side sign. It does not prove the symbolic table, and because the sign is the packet sign, it does not rescue the blind mismatch.

Two-CAS-or-honest-split: PASS ONLY AS HONEST SPLIT, NOT AS TWO-CAS DERIVATION. JAX/SymPy is the real source-form derivation from Kraus/unitary action. Julia/Symbolics emits formula rows over symbolic parameters, not a second independent derivation from the Kraus/unitary density action. PyTorch is explicitly declared as a pinned tensor mirror, not a symbolic CAS. That split is honest if kept at this ceiling.

PyTorch role: PASS WITH NARROW SCOPE. PyTorch uses hardcoded pinned matrices and `torch.func.vmap` over 16 ordered pairs. It is useful as a pinned mirror, not as symbolic or source-form evidence.

Ceiling: PASS. The envelope preserves `scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`.

## Full Diff Against Blind Expectations

### Affine `(M,c)` Rows

| Channel | Blind expectation | Packet result | Decision |
|---|---|---|---|
| `D_z` | `diag(1-q_z,1-q_z,1)`, `c=0`; pinned `diag(7/10,7/10,1)` | Same | PASS |
| `D_x` | `diag(1,1-q_x,1-q_x)`, `c=0`; pinned `diag(1,7/10,7/10)` | Same | PASS |
| `R_x` | `[[1,0,0],[0,C,-S],[0,S,C]]`, `c=0`; pinned `[[1,0,0],[0,0,-1],[0,1,0]]` | `[[1,0,0],[0,C,S],[0,-S,C]]`, `c=0`; pinned `[[1,0,0],[0,0,1],[0,-1,0]]` | FAIL blind sign |
| `R_z` | `[[U,-V,0],[V,U,0],[0,0,1]]`, `c=0`; pinned `[[0,-1,0],[1,0,0],[0,0,1]]` | `[[U,V,0],[-V,U,0],[0,0,1]]`, `c=0`; pinned `[[0,1,0],[-1,0,0],[0,0,1]]` | FAIL blind sign |

### Fixed Sets

| Channel | Blind expectation | Packet result | Decision |
|---|---|---|---|
| `D_z` | `q_z=0` full ball; `0<q_z<=1` z-axis | Same | PASS |
| `D_x` | `q_x=0` full ball; `0<q_x<=1` x-axis | Same | PASS |
| `R_x` | identity if `theta=0 mod 2pi`; otherwise x-axis | Same set; sign-flipped transverse equations | PASS set, FAIL blind equation sign |
| `R_z` | identity if `phi=0 mod 2pi`; otherwise z-axis | Same set; sign-flipped transverse equations | PASS set, FAIL blind equation sign |

### Basin / Orbit Rows

| Channel | Blind expectation | Packet result | Decision |
|---|---|---|---|
| `D_z` | explicit limit to `(0,0,z)` for `0<q_z<1`; one-step projection for `q_z=1` | Prose classification only | FAIL receipt form; content matches recompute |
| `D_x` | explicit limit to `(x,0,0)` for `0<q_x<1`; one-step projection for `q_x=1` | Prose classification only | FAIL receipt form; content matches recompute |
| `R_x` | `R_x^n=R_x(n theta)`, rational periodic, irrational dense, no attraction | Prose classification only | PARTIAL; content right under packet convention, no explicit orbit formula receipt |
| `R_z` | `R_z^n=R_z(n phi)`, rational periodic, irrational dense, no attraction | Prose classification only | PARTIAL; content right under packet convention, no explicit orbit formula receipt |

## Named Gaps

1. Rotation convention fork unresolved: the packet should either match the blind/source-locked right-handed active rows or explicitly declare a convention conversion layer and report both standard-basis and pinned-y-basis matrices.
2. Signed commutator table is packet-consistent but blind-mismatched for handedness-sensitive rows.
3. Basin receipts need explicit iterated formulas and limits, not prose classifications.
4. Most negative controls are declarative booleans, not executed can-fail mutation receipts.
5. Julia is not a second independent Kraus/Bloch CAS derivation; keep this as an honest split, or add a real Julia derivation from density/channel forms.
6. SMT checks are narrow pinned-entry contradiction checks; they should not be described as proving the full symbolic commutator table.
7. PyTorch is a pinned mirror over hardcoded matrices; useful, but not source-form or symbolic evidence.

## Final Boundary

Accept as: executable three-engine scratch packet with green local validators, exact dephasing rows, exact unitality for the four scoped base channels, correct set-level fixed axes, correct ellipsoid shape classes, symbolic commutator machinery under the packet's chosen convention, and bounded ceiling.

Reject as: blind-matching S4 audit pass, right-handed active rotation table, signed commutator table matching `/tmp/s4_blind_expected_20260610.md`, basin-limit receipt, broad can-fail control suite, or two-CAS proof.

VERDICT: REJECT AS CLAIMED. Keep the packet at `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## V2 Fresh Re-Audit After REJECT AS CLAIMED

Audit date: 2026-06-10.

Scope: re-executed the six v1 fail conditions against the current v2 sources and result JSONs. I did not run the builder scripts because they overwrite result JSONs; this pass used read-only validators, source/result inspection, and independent inline recomputations. The only write was this appended verdict section.

Fresh read-only checks:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json
=> {"ok": true, "result_json": "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s4_operator_stage_v0/geo_s4_operator_stage_v0_exact_strength_validator.py system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json
=> {"errors": [], "ok": true, "result_json": "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json"}
```

### V1. Convention Coherence

Status: CLOSED.

Independent recomputation under the declared source-locked standard Bloch basis gives the blind/right-handed row:

```text
R_x(pi/2) =
[[1,0,0],
 [0,0,-1],
 [0,1,0]]

[D_z,R_x] at q_z=3/10, theta_x=pi/2 =
[[0,0,0],
 [0,0,3/10],
 [0,3/10,0]]
```

Those match `/tmp/s4_blind_expected_20260610.md` and the v2 envelope commutator row. The v2 result also keeps the sign-flipped S1 pinned-y basis as an explicit `J * M_source_locked_standard * J` conversion layer instead of silently absorbing it.

### V2. Basin Iterated Formulas And Computed Limits

Status: CLOSED.

The v2 envelope now carries explicit iteration formulas and computed pin-limit receipts. Independent recomputation for `D_z`, with `q_z=3/10` and `r_0=(1/5,-2/5,1/3)`, gives:

```text
D_z^n r_0 = ((7/10)^n/5, -2*(7/10)^n/5, 1/3)
r_1 = (7/50, -7/25, 1/3)
r_2 = (49/500, -49/250, 1/3)
r_5 = (16807/500000, -16807/250000, 1/3)
limit = (0,0,1/3)
```

These match the v2 `basin_classes.D_z.computed_pin_limit_receipt`. The rotation rows also now carry power/orbit receipts and nonlimit/period checks.

### V3. Controls Are Executed Mutations With Failing Values

Status: CLOSED.

The v2 `negative_controls` rows now record `executed=true`, observed mutated values, `gate_passed_after_mutation=false`, and `expected_failure_observed=true` for C1-C8. I reran C1 independently:

```text
mutation: use the S1 pinned-y matrix as if it were source-locked standard R_x
mutated R_x(pi/2) = [[1,0,0],[0,0,1],[0,-1,0]]
expected R_x(pi/2) = [[1,0,0],[0,0,-1],[0,1,0]]
gate_passed_after_mutation = false
```

That is a real failing value, not just a declarative boolean.

### V4. Julia Derivation

Status: CLOSED.

The current Julia leg contains a real density/channel derivation: it builds `rho_from_bloch`, applies projector/Kraus dephasing and unitary half-angle channels, extracts components, reduces the half-angle rows, and records `density_channel_derivation.all_pass=true`. The v2 Julia `R_x` and `R_z` rows match the blind standard-basis signs:

```text
R_x = [[1,0,0],[0,cos(theta_x),-sin(theta_x)],[0,sin(theta_x),cos(theta_x)]]
R_z = [[cos(phi_z),-sin(phi_z),0],[sin(phi_z),cos(phi_z),0],[0,0,1]]
```

This closes the v1 "honest split only" gap for the affine channel derivation. Julia SMT remains narrower, as described below.

### V5. SMT Description Honesty

Status: CLOSED.

The v2 SMT descriptions are honest about scope. The envelope labels every solver proof as `pinned_entry_contradiction_not_full_symbolic_table`; z3, cvc5, Julia Z3, PyTorch z3, and PyTorch cvc5 all report `verdict=unsat` with `wrong_control_can_fail=true`. This is now correctly described as pinned-entry contradiction evidence, not as a full symbolic commutator-table proof.

### V6. Strength Tokens And Ceilings

Status: CLOSED.

The v2 envelope keeps:

```text
classification = scratch_diagnostic
promotion_allowed = false
formal_admission_allowed = false
```

Observed strength tokens are bounded to:

```text
exact_symbolic_matrix_table
exact_case_classification
exact_integer_rational_pin
lineage_citation_only
quotient_boundary_statement
```

No result inspected in this pass promotes canonical operator-family completion, Axis-level admission, formal admission, terrain-generator closure, engine/runtime closure, or physics evidence.

Final line: EARNED, for the v1 six-fail-condition re-audit only. Ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
