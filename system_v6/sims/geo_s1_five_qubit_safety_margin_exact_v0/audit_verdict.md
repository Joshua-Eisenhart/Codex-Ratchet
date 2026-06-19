# Fresh Audit Verdict: geo_s1_five_qubit_safety_margin_exact_v0

Audit date: 2026-06-10
Audit mode: read-only except this `audit_verdict.md`
Inputs: this sim folder sources/results, `build_card.md`, `directive_addendum.md`, `/tmp/claude_s1_qubit_ladder_corrected_message_20260610.md`, prior H1-H7 catalog from `axis_independence_discriminators_036/audit_verdict.md`, and prior E1-E6 catalog from `geo_s1_exact_closure_v0/audit_verdict.md`.

## Verdict

VERDICT: EARNED.

The packet earns the requested 5Q safety-margin scratch diagnostic: F01/N01/T01 are present and computed; `C32`, `S63`, `CP31`, mixed dimension `1023`, `Cl10`, `gamma11` split `16+16`, and max family `11` are source-backed; max-family uses theorem-plus-constructive labeling from the directive; no arbitrary dense enumeration is used; and the no-new-minimum boundary is explicit.

Ceiling restated: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. This is an overbuild/safety-margin result only. It does not move the 3Q minimum floor and does not admit final carrier, final `M(C)`, QIT-engine, physics, bridge, or theorem-of-everything claims.

## Fresh Commands

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/geo_s1_five_qubit_safety_margin_exact_v0/results/geo_s1_five_qubit_safety_margin_exact_v0_envelope_results.json
-> {"ok": true, ...}
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_five_qubit_safety_margin_exact_v0/results/geo_s1_five_qubit_safety_margin_exact_v0_envelope_results.json
-> {"ok": true, ...}
```

JSON float scan:

```text
envelope: 3 floats, all runtime_seconds resource rows
jax: 2 floats, all runtime_seconds resource rows
julia: 0 floats
pytorch: 2 floats, all runtime_seconds resource rows
```

Adjudication: no claim-row float tolerance was found. The only JSON floats are diagnostic runtime/resource values, not equality, bound, entropy, gamma, theorem, or control rows.

## Per-Check Adjudication

### 1. F01/N01/T01

Verdict: PASS.

Quoted source:

- F01 emits exact counts: `hilbert_dim = DIM`, `computational_basis_count = DIM`, `operator_basis_count = 4**N`, `S^63 subset C^32`, `CP^31`, and `mixed_density_real_dim = 4**N - 1` (`geo_s1_five_qubit_safety_margin_exact_v0_jax.py:267-294`).
- F01 explicitly records `arbitrary_dense_clique_enumeration = "not_used"` (`geo_s1_five_qubit_safety_margin_exact_v0_jax.py:277-284`).
- N01 O3 computes `A = X tensor I tensor I tensor I tensor I` and `B = (X + Z) tensor I tensor I tensor I tensor I`, then proves both commutator and anticommutator nonzero with z3-backed finite integer deltas (`geo_s1_five_qubit_safety_margin_exact_v0_jax.py:297-365`).
- O6 separates the root noncommutation row from the Clifford capacity row and labels the capacity row `representation_theorem_with_constructive_receipt` (`geo_s1_five_qubit_safety_margin_exact_v0_jax.py:360-365`).
- T01 uses matrix associativity theorem plus six exact Pauli-string spot checks, marks schedule/channel associator `open_with_reason`, and states qubit matrix multiplication in `M32(C)` is associative (`geo_s1_five_qubit_safety_margin_exact_v0_jax.py:529-565`).

Recomputation:

```text
5Q F01:
hilbert_dim = 32
computational_basis_count = 32
operator_basis_count = 1024
pure sphere = S^63 subset C^32
phase quotient = CP^31
mixed density real dimension = 1023

O3 with A=XIIII, B=(X+Z)IIII:
AB-BA nonzero = true, 32 nonzero entries
AB+BA nonzero = true, 32 nonzero entries

One Clifford pair:
gamma_1 = XIIII, gamma_2 = YIIII
gamma_1 gamma_2 + gamma_2 gamma_1 = 0 exactly
```

Adjudication: O3 is genuine. Anticommutation remains a Clifford special case and does not replace root noncommutation. T01 is honest: no fake algebra-level nonassociativity is introduced.

### 2. Cl10, Gamma11, Max-Family 11

Verdict: PASS.

Quoted source:

- W2 checks all 100 Cl10 anticommutator pairs, records `gamma11 = (-i)^5 gamma_1...gamma_10 = ZZZZZ`, `gamma11_squared_identity`, trace `0`, split `16+16`, and `gamma11_equals_ZZZZZ` (`geo_s1_five_qubit_safety_margin_exact_v0_jax.py:446-484`).
- W3 constructs the family `gammas + [gamma11]`, verifies pairwise anticommutation, and labels the route `representation_theorem_with_constructive_receipt` (`geo_s1_five_qubit_safety_margin_exact_v0_jax.py:491-523`).
- The upper-bound theorem states that pairwise anticommuting Hermitian-unitaries give a `Cl_m(C)` representation, minimal complex dimension is `2^floor(m/2)`, and `2^floor(m/2) <= 32` implies `m <= 11` (`geo_s1_five_qubit_safety_margin_exact_v0_jax.py:508-512`).
- z3 and cvc5 both block the 12-member family and accept the 11-member boundary control (`geo_s1_five_qubit_safety_margin_exact_v0_jax.py:514-523`).

Recomputation:

```text
m = 11: 2^floor(11/2) = 32 <= 32, admissible.
m = 12: 2^floor(12/2) = 64 > 32, theorem-blocked.
```

Adjudication: exhaustive arbitrary clique search is not required at this size because the packet uses the admitted theorem-plus-constructive route and labels it with the current strength-list token. The constructed 11-family is exact.

### 3. 5Q-Specific Safety-Margin Rows

Verdict: PASS.

Quoted source:

- W4 records validator scaling at dense matrix dimension `32x32`, exact gamma pair checks `100`, max-family pair checks `55`, Pauli-string total `1024`, and `full_nonidentity_clique_enumeration = "not_run"` with reason `1023 vertices is arbitrary dense enumeration for this card` (`geo_s1_five_qubit_safety_margin_exact_v0_jax.py:568-582`).
- W5 constructs GHZ5, product, and Bell-pair-plus-spectator states exactly; it emits reduced densities and entropies and explicitly says full five-party entanglement classification is not scoped (`geo_s1_five_qubit_safety_margin_exact_v0_jax.py:585-635`).
- W6 states what 5Q adds and does not add, and rejects the overclaim `because 5Q exists, 3Q was not minimum` with z3/cvc5 `5 == 3` controls returning `unsat` (`geo_s1_five_qubit_safety_margin_exact_v0_jax.py:638-665`).

Recomputation:

```text
GHZ5 one-qubit reduction = diag(1/2, 1/2), entropy = log(2).
Bell-pair-plus-spectators q0q1 reduction is a pure Bell projector, entropy = 0.
Spectator q2 reduction is |0><0|, entropy = 0.
```

Adjudication: no arbitrary dense enumeration was used; routes are Pauli-string/stabilizer-exact and theorem-bound. The safety-margin framing is correct and does not make a new minimum claim.

### 4. Strength, Forbidden Rows, Tools, Ceilings

Verdict: PASS.

Quoted source:

- The classification table uses directive tokens including `exact_integer_combinatorial`, `representation_theorem_with_constructive_receipt`, `symbolic_identity`, `open_with_reason`, and `negative_control`; every claim-bearing row has `bare_float_claim = False` (`geo_s1_five_qubit_safety_margin_exact_v0_jax.py:668-709`).
- The build card accepts theorem/spot-check proof where full SMT over 32x32 matrices is too heavy, as long as `proof_scope` is clear (`build_card.md:67-73`).
- The envelope gates F01, N01, T01, W2, W3, W4, W5, W6, exact-strength rows, z3/cvc5 controls, and PyTorch exact integer mirror (`geo_s1_five_qubit_safety_margin_exact_v0_envelope.py:153-249`).
- The envelope keeps `.numpy`, `np.asarray`, CSV, pickle, and hidden host-copy bridges forbidden, and the PyTorch role is exact integer tensor mirror plus z3/cvc5/sympy controls (`geo_s1_five_qubit_safety_margin_exact_v0_envelope.py:292-295`).

Pattern-catalog audit:

- H1-H7 fixture/echo/control/derived-boolean/synthetic-boundary patterns: no matching fixture-isolation or label-template failure found. The packet uses shared exact Pauli/Jordan-Wigner objects, theorem rows, and named state controls rather than disjoint observable fixtures.
- E1-E6 exactness patterns: convention pins are explicit, signs are computed for `gamma11`, no formula-only CAS echo carries the max-family theorem, no hardcoded sign row is claim-bearing, runtime floats are diagnostic-only, and the classification table uses current directive labels.

Named gaps:

1. T01 schedule/channel associator remains `not_scoped`. This is honest and acceptable for this safety-margin carrier packet; it cannot be cited as a channel-bracketing result.
2. Runtime/resource rows contain floats. They are diagnostic and non-claim; do not reuse them as exact performance claims.
3. Full five-party entanglement classification is not scoped. Only the named controls are earned.

## Final Verdict

VERDICT: EARNED.

Use the packet as a 5Q overbuild/safety-margin scratch diagnostic for exact `C32/S63/CP31/D(C32)`, Cl10, `gamma11` split `16+16`, max family `11`, validator scaling, and named exact state controls. The ceiling remains scratch-only with no promotion or minimum-floor shift.

## 2026-06-10 Tooling Remediation Steps 5-6

Step 5: Clifford claims remain routed through Julia `CliffordAlgebras` as load-bearing for Cl10. The Julia receipt constructs `CliffordAlgebra(10,0)` and records package dimension `1024` plus generator-square evidence; the hand Jordan-Wigner gamma table is retained as a mirror.

Step 6: the constructed 11-member max-family receipt now includes an exact `rustworkx.PyGraph` complete-graph check in JAX and PyTorch. Full 1023-vertex arbitrary clique enumeration remains explicitly `not_run`; the theorem-bound plus constructed-family graph is the admitted route.

Byte-stability pins: max family `11`, gamma11 split `16+16`, Cl10 algebra dimension `1024`, `C32/S63/CP31/D(C32)=1023`, and no-minimum-shift controls remained unchanged.

Fresh checks: JAX, Julia, PyTorch, and envelope reruns returned `ok:true`; `validate_three_engine_sim_result.py --require-pytorch --strict-source-backed` returned `ok:true`; relevant capability gates for `rustworkx`, `sympy`, `torch`, and `CliffordAlgebras` returned passing receipts.
