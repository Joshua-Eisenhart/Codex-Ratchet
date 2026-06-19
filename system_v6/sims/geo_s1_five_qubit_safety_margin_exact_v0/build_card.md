# BUILD CARD: geo_s1_five_qubit_safety_margin_exact_v0 — 5Q safety / boundary stress rung

One object, one claim, one card. CLAIM UNDER TEST: the five-qubit carrier `(C^2)^{⊗5} ~= C^32` is a finite overbuild margin beyond the immediate 4Q support rung. It stress-tests the ladder pattern, exact validators, and scaling behavior without turning the project into an unbounded qubit escalation.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. This is safety margin / boundary stress only; no final carrier, final `M(C)`, QIT engine, physics, bridge, or theorem-of-everything claim.

## Binding Directive

This packet is built under the binding overrides copied into `directive_addendum.md` from `/tmp/claude_s1_qubit_ladder_corrected_message_20260610.md`: F01 finitude must be receipted explicitly; N01 noncommutation must not collapse into anticommutation; T01 bracketing/nonassociativity boundary must be tested without faking nonassociativity inside qubit matrix algebras; max family is 11 by theorem receipt plus constructive family; no arbitrary dense enumeration.

## Why 5Q exists

5Q is not required to prove the 3Q minimum and not required for the first 4Q support rung. It is useful because it checks that the exact machinery survives beyond the needed rung:

```text
1Q exact Hopf foundation
2Q boundary/control
3Q minimum Cl6/C8 floor
4Q Cl8/Spin8 support
5Q overbuild margin: Cl10/C32, 11-family, validator scaling, no-new-minimum check
```

## Exact computations

W1. CARRIER / QUOTIENT
- basis dictionary for 32 computational states;
- normalized pure-state sphere `S63 subset C32`;
- global phase quotient `CP31`;
- rank-1 density phase-erasure identity;
- full mixed-state dimension `1023`.

W2. Cl(10) EXACT FLOOR
- construct ten gamma generators as exact Pauli/Jordan-Wigner strings on `C32`;
- verify all 100 anticommutators exactly;
- construct chirality `gamma11` with sign/factor convention pin;
- prove `gamma11^2=I`, `tr(gamma11)=0`, split `16+16`.

W3. MAX ANTICOMMUTING FAMILY = 11
- construct eleven-member pairwise anticommuting family;
- prove upper bound using Clifford representation dimension bound;
- attempted 12-member extension negative/control fails or is theorem-blocked.

W4. SCALING OF EXACT VALIDATORS
- demonstrate the same exact-classification validator works at dimension 32;
- record performance/resource rows honestly;
- if some exhaustive checks are infeasible, switch to representation-theorem proof with exact spot-checks and state the reason.

W5. EXACT NAMED-STATE CONTROLS
Use simple exact states, not random samples:

```text
GHZ5 = (|00000>+|11111>)/sqrt2
product = |00000>
Bell-pair-plus-spectator controls
```

Emit exact selected reduced densities and entropies. Do not attempt a full classification of 5-party entanglement unless scoped separately.

W6. NO-NEW-MINIMUM / BOUNDARY FINDING
- state exactly what 5Q adds: larger Cl(10), 11-family, 16+16 chirality split, scaling margin;
- state exactly what it does not add: it does not move the minimum Cl6/three-slot floor from 3Q;
- include a negative control against “because 5Q exists, 3Q was not minimum.”

W7. CLASSIFICATION TABLE
Every row classified as symbolic / exact-integer / closed-form / representation-theorem / finite-exhaustive / negative-control / open-with-reason. Zero claim-bearing bare-float rows.

## Proofs

P1. z3 + cvc5 anticommutation rows where feasible; if full SMT over 32x32 matrices is too heavy, use exact matrix generation plus theorem receipt and solver spot-checks with clear `proof_scope`.

P2. max-family upper bound by Clifford representation dimension bound; attempted 12-family blocked.

P3. selected named-state entropy/eigenvalue rows exact; corrupted controls fail.

## Controls

```text
corrupted gamma sign
12-family impossible control
product/GHZ5 label swap
5Q-minimum-overclaim control
validator-scaling resource bound row
```

## Engines

Julia = canon exact matrices / symbolic / Z3.jl where scoped.
JAX/Python = sympy + z3/cvc5 exact mirror.
PyTorch = exact integer tensor mirror only if honest and resource-safe; otherwise demote to scoped support.
No NumPy on claim path except baseline/control/io-only.

## Files

```text
system_v6/sims/geo_s1_five_qubit_safety_margin_exact_v0/
  build_card.md
  *_julia.jl / *_jax.py / *_pytorch.py / *_envelope.py
  results/*.json
```

## Acceptance

Fresh leg/envelope reruns; validator `--require-pytorch --require-source-backed` passes if PyTorch scoped, otherwise envelope honestly marks PyTorch demoted/not-scoped; strict source-backed passes or thin claims demoted; exact classification table has zero claim-bearing bare-float rows; blind audit confirms exact rows; no-promotion ceiling exact.
