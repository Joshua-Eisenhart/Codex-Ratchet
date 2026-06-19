# Fresh Audit Verdict: geo_s1_two_qubit_boundary_exact_v0

Audit date: 2026-06-10
Audit mode: read-only except this `audit_verdict.md`
Inputs: sim folder sources/results, `build_card.md`, `directive_addendum.md`, `/tmp/claude_s1_qubit_ladder_corrected_message_20260610.md`
Prior-pattern focus: predeclared equality, CAS echo, hardcoded signs, float-boxed intervals, missing pins

## Verdict

VERDICT: EARNED.

The packet earns the requested 2Q boundary/control scratch diagnostic: exact 2Q positives are present, exact 2Q negatives are present, root noncommutation is not collapsed into anticommutation, matrix associativity is handled honestly, and no claim-bearing float-tolerance row was found.

Ceiling restated: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. This does not admit carrier, final `M(C)`, QIT-engine, physics, or bridge claims.

## Commands And Checks

Read-only validator checks:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/geo_s1_two_qubit_boundary_exact_v0/results/geo_s1_two_qubit_boundary_exact_v0_envelope_results.json
-> {"ok": true, ...}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_two_qubit_boundary_exact_v0/results/geo_s1_two_qubit_boundary_exact_v0_envelope_results.json
-> {"ok": true, ...}
```

Exactness scans:

```text
JSON float_value_count = 0 for envelope, jax, julia, pytorch result JSONs.
Tolerance/token scan found no claim-path tolerance gate; only the directive's forbidden-list text and integer conversion code matched.
```

Independent recomputation:

```text
O3 A=X, B=X+Z:
AB-BA = [[0,-2],[2,0]]
AB+BA = [[2,0],[0,2]]
so AB != BA and AB+BA != 0.

Tensor-lift O3 on C4:
commutator nonzero = True
anticommutator nonzero = True

Representative associator:
(AB)C - A(BC) = 0 exactly.

Bell concurrence:
a=d=1/sqrt(2), b=c=0, C=2|ad-bc|=1.

Bell Schmidt:
rho_A = [[1/2,0],[0,1/2]]
eigenvalues = {1/2: multiplicity 2}
Schmidt coefficients = sqrt(2)/2, sqrt(2)/2.

Max-family bound:
m=5 minimal dimension 2^floor(5/2)=4 <= 4.
m=6 minimal dimension 2^floor(6/2)=8 > 4.
m=7 minimal dimension 2^floor(7/2)=8 > 4.

Finite Pauli-string exhaustive check:
max clique size = 5
example = (IX, IY, XZ, YZ, ZZ)
size-6 clique exists = False
```

## Per-Check Adjudication

### A1 - F01 Finitude Receipt

Source requirement: directive says not to infer finitude from arrays and requires `hilbert_dim`, basis count, operator count, `S^(...)`, `CP^(...)`, density real dimension, named finite bounds, and finite proof objects (`directive_addendum.md:92-110`). Build card requires C4/S7/CP3/D(C4) dimension 15 separation (`build_card.md:11-18`, `build_card.md:22-27`).

Source evidence: the JAX exact leg computes `n = 2`, then emits `hilbert_dim: 2**n`, `computational_basis_count: 2**n`, `operator_basis_count: 4**n`, `pure_sphere: "S^7 subset C^4"`, `phase_quotient: "CP^3"`, `mixed_density_real_dim: 4**n - 1`, finite Pauli/basis/enumeration bounds, and finite proof objects (`geo_s1_two_qubit_boundary_exact_v0_jax.py:163-188`). The envelope gate checks the scalar requirements directly (`geo_s1_two_qubit_boundary_exact_v0_envelope.py:159-166`).

Adjudication: PASS. Recomputed for n=2: Hilbert dim 4, computational basis 4, operator basis 16, pure sphere S7, phase quotient CP3, mixed density real dimension 15. The finite presentation is named through finite variables, matrix-entry constraints, and Pauli generator-relation objects.

### A2 - N01 O1-O6 Receipt And Nonconflation

Source requirement: the directive states "Do not collapse noncommutation into anticommutation" and requires O1-O6, including O3 `AB != BA and AB+BA != 0`, while O4 is the separate Clifford anticommutation row (`directive_addendum.md:112-154`).

Source evidence: JAX computes O1-O6 in exact matrices and SMT polarity checks. O3 uses `A = X tensor I`, `B = (X + Z) tensor I`, and records both `AB_minus_BA_nonzero` and `AB_plus_BA_nonzero`; O4 separately records `AB_plus_BA_zero`; O6 names the Clifford capacity row as separate from O2/O3 root-order rows (`geo_s1_two_qubit_boundary_exact_v0_jax.py:249-319`). Julia independently mirrors the same O3/O4/O6 structure (`geo_s1_two_qubit_boundary_exact_v0_julia.jl:205-232`).

Recomputation: for A=X and B=X+Z, `AB-BA = [[0,-2],[2,0]]` and `AB+BA = [[2,0],[0,2]]`; both nonzero where required. The tensor-lifted C4 witness is also nonzero for both commutator and anticommutator.

Adjudication: PASS. No anticommutation-as-root conflation found.

### A3 - T01 Associator Boundary

Source requirement: qubit matrix algebras must show `(AB)C-A(BC)=0` and must not fake algebra-level nonassociativity (`directive_addendum.md:156-186`).

Source evidence: JAX enumerates all 4096 ordered Pauli-string triples and increments failures only on nonzero associators. It records representative `X tensor I`, `Z tensor I`, `I tensor X`, `failures: 0`, schedule associator `not_scoped`, and an octonion/nonassociative extension boundary (`geo_s1_two_qubit_boundary_exact_v0_jax.py:331-361`). Julia mirrors exhaustive associator checking and records the associative boundary (`geo_s1_two_qubit_boundary_exact_v0_julia.jl:252-267`).

Recomputation: representative `(AB)C - A(BC)` equals zero exactly.

Adjudication: PASS. Boundary statement is honest; no fake nonassociativity.

### A4 - 2Q Can/Cannot Boundary

Source requirement: the 2Q rung must prove positives `Cl4`, Bell/concurrence, two-slot entanglement, chirality split `2+2`, and negatives `Cl6 no`, `7 anticommuting family no`, `GHZ/W/3-tangle no`, `three-slot floor no` (`directive_addendum.md:246-286`). The build card requires max family 5 by upper bound and failed 6-member extension (`build_card.md:41-55`).

Positive evidence:

- Bell/Schmidt/concurrence are computed symbolically: Bell reduced densities `I/2`, entropy `log(2)`, generic Schmidt eigenvalues, concurrence formula `C = 2|ad-bc|`, Bell `1`, product `0`, and solver controls (`geo_s1_two_qubit_boundary_exact_v0_jax.py:395-499`).
- Cl4 is exact over Pauli strings, all 16 anticommutator pairs are checked, gamma5 is `-gamma_1 ... gamma_4 = Z tensor Z`, gamma5 squared identity, trace zero, and split `2+2` (`geo_s1_two_qubit_boundary_exact_v0_jax.py:502-583`).
- Max family 5 is both constructed and exhaustively checked over nonidentity two-qubit Pauli strings; source checks `max_clique_size == 5` and `size_6_clique_exists is False` (`geo_s1_two_qubit_boundary_exact_v0_jax.py:590-663`).

Negative evidence:

- The source uses the representation bound `2^floor(m/2) <= carrier_dim` via z3/cvc5; m=6 gives unsat at carrier dim 4, while m=5 is sat (`geo_s1_two_qubit_boundary_exact_v0_jax.py:616-650`).
- Cl6 and seven-family impossibility rows are emitted with representation-theorem reasons, not just assertions (`geo_s1_two_qubit_boundary_exact_v0_jax.py:666-679`).
- GHZ, W, and three-tangle are emitted as `not_defined_by_arity`; the three-site schedule floor is `not_available` because 2Q has two tensor slots (`geo_s1_two_qubit_boundary_exact_v0_jax.py:680-699`).

Recomputation: Bell concurrence is 1; Bell Schmidt coefficients are `sqrt(2)/2, sqrt(2)/2`; m=5 is dimension-admissible and m=6/m=7 are not in C4; finite Pauli clique max is 5 with no size-6 clique.

Adjudication: PASS. The no-Cl6/no-7-family receipt uses the required representation argument and finite Pauli-string control. The 3-slot absence is not misencoded as numeric zero.

### A5 - CP3 Versus Quaternionic Hopf Nonconflation

Source requirement: build card says not to collapse C4 pure sphere S7, 2Q quotient `S7/S1 = CP3`, mixed domain D(C4) dim 15, and quaternionic Hopf `S3 -> S7 -> S4` (`build_card.md:7-18`). Directive separately requires `S7/S1 = CP3` from quaternionic Hopf `S3 -> S7 -> S4` (`directive_addendum.md:276-286`).

Source evidence: Y1 emits separate fields for normalized states, global phase quotient, rank-1 density quotient, mixed-state domain, and non-conflation fields. It explicitly sets `CP3_equals_S4: False` and `S7_over_S1_equals_S7_over_S3: False` (`geo_s1_two_qubit_boundary_exact_v0_jax.py:365-392`). Julia mirrors the separation (`geo_s1_two_qubit_boundary_exact_v0_julia.jl:269-286`).

Adjudication: PASS. The quaternionic Hopf field is present only as a non-conflation/control field; quotient computations use the CP3 phase-erasure route.

### A6 - Strength Classification And Forbidden List

Source requirement: claim rows must use only listed exact strength classes; forbidden claim-bearing rows include `bare_float_tolerance`, `sample_only`, `max_deviation_only`, `abs_error_only`, visual agreement, and validator-green-only (`directive_addendum.md:382-407`).

Source evidence: JAX builds the classification table row-by-row for F01, N01.O1-O6, T01, Y1-Y6, P1-P3, marks all claim-bearing rows as exact/symbolic/theorem/finite-enumeration, and sets `bare_float_claim: False`; it then fails if any claim-bearing bare-float row is present (`geo_s1_two_qubit_boundary_exact_v0_jax.py:703-745`). The envelope requires all three engines to report `zero_claim_bearing_bare_float_rows` and no invalid strengths (`geo_s1_two_qubit_boundary_exact_v0_envelope.py:236-244`).

Independent scan: all four result JSON files contain zero JSON float values. Token scan found no tolerance gate in source or results, apart from the directive's own forbidden-list text.

Adjudication: PASS. No float tolerance finding.

### A7 - Standard: Two-CAS, Controls, SMT, PyTorch, Ceilings

Source evidence:

- Two-CAS independence: JAX and PyTorch legs use both z3 and cvc5 for load-bearing polarity checks (`geo_s1_two_qubit_boundary_exact_v0_jax.py:203-246`, `geo_s1_two_qubit_boundary_exact_v0_pytorch.py:169-224`). Envelope records z3 and cvc5 as load-bearing crossover proofs (`geo_s1_two_qubit_boundary_exact_v0_envelope.py:326-355`).
- Computed signs and hardcoded-sign guard: gamma5 convention is pinned, computed as `-product`, and a corrupted gamma sign control must return sat (`geo_s1_two_qubit_boundary_exact_v0_jax.py:512-583`). The build card requires gamma5 pinned sign/factor (`build_card.md:41-45`).
- Can-fail controls: corrupted gamma, wrong Bell/product labels, 5-boundary sat, no-6 unsat, CP3/S4 controls all feed envelope gates (`geo_s1_two_qubit_boundary_exact_v0_envelope.py:220-235`, `geo_s1_two_qubit_boundary_exact_v0_envelope.py:326-355`).
- Exact SMT: z3/cvc5 use integer matrix/value constraints; no approximate numeric tolerance gate was found (`geo_s1_two_qubit_boundary_exact_v0_jax.py:203-246`).
- PyTorch honest role: PyTorch represents complex Gaussian-integer matrices as integer real/imag tensor pairs with `torch.int64`, exact multiplication, exact kron, and integer extraction (`geo_s1_two_qubit_boundary_exact_v0_pytorch.py:84-148`).
- Ceilings: build card ceiling is scratch-only (`build_card.md:5`), source constants preserve `scratch_diagnostic`, no promotion, and no formal admission (`geo_s1_two_qubit_boundary_exact_v0_julia.jl:21-24`), and envelope records forbidden stronger claims (`geo_s1_two_qubit_boundary_exact_v0_envelope.py:296-307`).

Adjudication: PASS. The standard is met for this scratch diagnostic boundary packet.

## Pattern-Catalog Audit

- Predeclared equality: not a finding. Critical rows are computed in source and independently recomputed above.
- CAS echo: not a finding. z3/cvc5 are both used on Python/PyTorch exact integer routes; Julia Z3 is present as canon-side SMT, while packet-level two-CAS independence is supplied by the Python/PyTorch lanes.
- Hardcoded signs: not a finding. gamma5 sign is pinned and has a corrupted-sign can-fail control.
- Float-boxed intervals: not a finding. No JSON floats and no tolerance gates on claim-bearing rows.
- Missing pins: not a finding. `pin_identical` is an envelope gate and strict-source-backed validation passed.

## Named Gaps

No blocking mathematical or exactness gaps found for the requested 2Q boundary/control ceiling.

Residual limits:

- This is still a scratch diagnostic, not formal admission.
- The schedule/channel associator row is explicitly `not_scoped`; that is acceptable for this algebraic carrier/control packet but cannot be cited as a channel-bracketing result.
- The folder is currently untracked in git; this audit does not stage or commit it.

## 2026-06-10 Tooling Remediation Steps 5-6

Step 5: Clifford claims now route through Julia `CliffordAlgebras` as load-bearing for Cl4. The Julia receipt constructs `CliffordAlgebra(4,0)` and records package dimension `16` plus generator-square evidence; the hand Jordan-Wigner gamma table is retained as a mirror.

Step 6: max-family scan now routes through an exact `rustworkx.PyGraph` anticommutation graph in the JAX and PyTorch lanes. The previous exact matrix/tensor scan is retained as mirror evidence.

Byte-stability pins: max family `5`, gamma5 split `2+2`, Cl4 algebra dimension `16`, and existing 2Q scalar pins remained unchanged.

Fresh checks: JAX, Julia, PyTorch, and envelope reruns returned `ok:true`; `validate_three_engine_sim_result.py --require-pytorch --strict-source-backed` returned `ok:true`; relevant capability gates for `rustworkx` and `CliffordAlgebras` returned passing receipts.
