# BUILD CARD: geo_s1_four_qubit_scaling_triality_exact_v0 — 4Q support rung

One object, one claim, one card. CLAIM UNDER TEST: the four-qubit carrier `(C^2)^{⊗4} ~= C^16` is the next-rung support packet for later work: Cl(8), larger chirality split, Spin(8)/triality pressure, and exact scaling controls beyond the 3Q minimum. It supports later layers; it does not prove 3Q minimality by itself.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. No final carrier, final `M(C)`, QIT engine, physics, or bridge admission.

## Required non-conflation

```text
C16 pure-state sphere: S31 subset C16
4Q global phase quotient: S31/S1 = CP15
4Q mixed-state domain: D(C16), real affine dimension 255
Cl8 / Spin8 representation pressure: separate from pure-state quotient
Spin8 triality: representation-structure pressure, not automatic from qubit count alone
```

## Exact computations

Z1. CARRIER / QUOTIENT
- basis dictionary for 16 computational states;
- normalized pure-state sphere `S31`;
- global phase quotient `CP15`;
- rank-1 density phase-erasure identity;
- full mixed-state dimension `255`.

Z2. EXACT ENTANGLEMENT CONTROLS
Use exact named states, not random samples:

```text
GHZ4 = (|0000>+|1111>)/sqrt2
product = |0000>
Bell-pair product = (|00>+|11>)/sqrt2 on AB tensor same on CD
4-qubit cluster state or pinned graph state
```

Emit exact reduced densities and entropies for named bipartitions. At minimum:

```text
GHZ4 one-qubit reduction: I/2, S=ln2
product all reductions: entropy 0
Bell-pair product: AB/CD partition behavior separated from one-qubit reductions
cluster/graph state: exact stabilizer or reduced-density receipt, if scoped
```

Z3. Cl(8) EXACT FLOOR
- construct eight gamma generators as exact Pauli/Jordan-Wigner strings on `C16`;
- verify all 64 anticommutators exactly;
- construct chirality `gamma9` with convention pin;
- prove `gamma9^2=I`, `tr(gamma9)=0`, split `8+8`.

Z4. MAX ANTICOMMUTING FAMILY = 9
- construct nine-member pairwise anticommuting family;
- prove upper bound using Clifford representation dimension bound;
- attempted 10-member extension negative/control fails.

Z5. SPIN(8) / TRIALITY PRESSURE
Do not overclaim full triality unless implemented. Minimum acceptable pressure:

```text
construct Cl8 gamma representation;
separate vector-like 8, positive spinor 8, negative spinor 8 representation labels where mathematically supported;
verify invariant dimensions and a pinned triality-relevant symmetry relation if feasible;
otherwise label `triality_pressure_open` with exact missing condition.
```

If a full triality automorphism is claimed, require an explicit map that permutes `8v,8s,8c` while preserving the relevant bilinear/quadratic form. No prose-only triality.

Z6. 4Q SUPPORTS LATER WORK, NOT MINIMUM
- exact comparison row to 3Q: 3Q has Cl6/7-family; 4Q has Cl8/9-family;
- 4Q is scaling/support, not a replacement for proving 3Q minimum;
- no S2/S3 terrain/operator/engine runtime claims.

Z7. CLASSIFICATION TABLE
Every row classified as symbolic / exact-integer / closed-form / representation-theorem / finite-exhaustive / negative-control / open-with-reason. Zero claim-bearing bare-float rows.

## Proofs

P1. z3 + cvc5 anticommutation table over exact matrix entries; corrupted gamma -> SAT.

P2. maximal 9-family upper-bound theorem receipt plus exact construction; attempted 10-family negative.

P3. exact named-state entropy/eigenvalue rows; corrupted state-label controls fail.

## Controls

```text
corrupted gamma sign
10-anticommuting-family impossible control
product mislabeled as GHZ4
Bell-pair product mislabeled as global GHZ4
triality prose-only overclaim control
CP15 vs Spin8/triality conflation control
```

## Engines

Julia = canon: Symbolics/exact matrices/Z3.jl.  
JAX/Python = sympy + z3/cvc5 exact mirror.  
PyTorch = exact integer tensor anticommutation/stabilizer mirror where honest.  
No NumPy on claim path except baseline/control/io-only.

## Files

```text
system_v6/sims/geo_s1_four_qubit_scaling_triality_exact_v0/
  build_card.md
  *_julia.jl / *_jax.py / *_pytorch.py / *_envelope.py
  results/*.json
```

## Acceptance

Fresh leg/envelope reruns; validator `--require-pytorch --require-source-backed` passes; strict source-backed passes or thin claims demoted; exact classification table has zero claim-bearing bare-float rows; blind audit confirms exact values; no-promotion ceiling exact.
