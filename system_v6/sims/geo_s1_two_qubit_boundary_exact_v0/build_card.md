# BUILD CARD: geo_s1_two_qubit_boundary_exact_v0 - 2Q boundary/control rung

One object, one claim, one card. CLAIM UNDER TEST: the two-qubit carrier `(C^2)^{⊗2} ~= C^4` is the exact boundary/control rung between the single-qubit Hopf foundation and the three-qubit Cl(6)/three-slot floor. It must establish exactly what 2Q supports and exactly what it cannot support.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. This packet does not admit carrier, final `M(C)`, QIT engine, physics, or bridge claims.

## Required non-conflation

Do not collapse these structures:

```text
C4 pure-state sphere: S7 subset C4
2Q global phase quotient: S7/S1 = CP3
2Q mixed-state domain: D(C4), real affine dimension 15
quaternionic Hopf fibration: S3 -> S7 -> S4, a different quotient/fibration structure than CP3
```

Emit explicit fields for each.

## Exact computations

Y1. CARRIER / QUOTIENT
- basis dictionary for `|00>, |01>, |10>, |11>`;
- normalized states `S7 subset C4`;
- global phase quotient `S7/S1=CP3`;
- rank-1 density quotient `rho=psi psi^dagger` phase erasure symbolic proof;
- full mixed state dimension `15` and trace/positivity constraints stated separately.

Y2. SCHMIDT / BELL / PRODUCT EXACT STATES
- exact Schmidt decomposition for generic two-qubit coefficient matrix where feasible;
- Bell state `(|00>+|11>)/sqrt2`: reduced densities `I/2`, entropy `ln 2`;
- product state `|00>`: reduced entropy `0`;
- biseparable does not apply at 2Q; label correctly.

Y3. CONCURRENCE / 2Q ENTANGLEMENT
- concurrence formula `C=2|ad-bc|` for state coefficients `(a,b,c,d)`;
- Bell concurrence `1`, product concurrence `0`;
- exact symbolic route in Julia/Symbolics and Python/sympy;
- solver proof/control: Bell not zero UNSAT, product nonzero UNSAT, corrupted label SAT.

Y4. Cl(4) EXACT FLOOR
- construct four gamma generators as exact Pauli strings on `C4`;
- verify all 16 anticommutators `{gamma_i,gamma_j}=2 delta_ij I` exactly over Gaussian-integer matrices;
- construct chirality `gamma5` with pinned sign/factor;
- prove `gamma5^2=I`, `tr(gamma5)=0`, split `2+2`.

Y5. MAX ANTICOMMUTING FAMILY = 5
- construct a five-member pairwise anticommuting Hermitian-unitary family;
- prove upper bound using the Clifford representation dimension bound;
- include an attempted 6-member extension negative/control that fails.

Y6. 2Q FAILS THE 3Q MINIMUM CLAIMS
- exact negative rows showing 2Q cannot carry Cl(6) / 7 anticommuting family in `M4(C)`;
- no GHZ/W/3-tangle object exists at 2Q; label `not_defined_by_arity`, not numeric zero;
- no three-site bracket/schedule floor; only two slots.

Y7. CLASSIFICATION TABLE
- every claim row has strength label: symbolic / exact-integer / closed-form / representation-theorem / finite-exhaustive / negative-control;
- zero claim-bearing bare-float rows.

## Proofs

P1. z3 + cvc5: exact anticommutation table over bound matrix entries; assert any anticommutator differs -> UNSAT; corrupted gamma -> SAT.

P2. z3 + cvc5: max-family upper-bound / no 6-member family in `M4(C)` encoded or, if full encoding is too heavy, proof-theorem receipt plus finite Pauli-string exhaustive enumeration; corrupted control must fail.

P3. concurrence exact values: Bell/product controls flip.

## Controls

```text
wrong Bell label control
product mislabeled entangled control
corrupted gamma sign control
6-anticommuting-family impossible control
CP3 vs S4 conflation control
S7/S1 vs quaternionic S7/S3 quotient non-conflation field
```

## Engines

Julia = canon: Symbolics.jl + exact Gaussian-integer matrices + Z3.jl where scoped.
JAX/Python = sympy + z3/cvc5 + exact rational/integer mirror.
PyTorch = exact integer tensor anticommutation mirror where honest; otherwise scoped/demoted.
No NumPy on claim path except baseline/control/io-only.

## Files

```text
system_v6/sims/geo_s1_two_qubit_boundary_exact_v0/
  build_card.md
  geo_s1_two_qubit_boundary_exact_v0_julia.jl
  geo_s1_two_qubit_boundary_exact_v0_jax.py
  geo_s1_two_qubit_boundary_exact_v0_pytorch.py
  geo_s1_two_qubit_boundary_exact_v0_envelope.py
  results/*.json
```

## Acceptance

Legs rerun fresh; envelope reruns fresh; `validate_three_engine_sim_result.py --require-pytorch --require-source-backed` passes; strict source-backed either passes or thin claims are demoted; custom exact-strength table has zero claim-bearing bare-float rows; blind audit agrees on expected exact values; ceiling exact.
