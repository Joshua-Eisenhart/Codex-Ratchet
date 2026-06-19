Claude — corrected S1 qubit-ladder directive / audit addendum.

Do not start S2 runtime yet.

The previous ladder message was directionally right but incomplete in three important ways:

1. It over-weighted anticommutation. The root condition is noncommutation, not anticommutation.
2. It assumed finitude because the code uses finite arrays. Finitude has to be explicitly receipted.
3. It under-specified ternary/bracketing/nonassociativity. That boundary must be tested too, without faking nonassociativity inside associative matrix algebras.

This is the corrected S1 target.

---

## 0. Status / sequencing

Keep the current 1Q and 3Q builder lanes running if they are still live. Do not interrupt them just to apply this message.

When they land, fold this addendum into hardening and fresh audit before any commit.

S2 runtime remains blocked until the S1 qubit ladder is closed to the selected target depth.

Recommended target now:

```text
S1 engine-ready closure through 8Q,
with 6Q–8Q as scaling/stress/boundary packets, not new minimum claims.
```

Minimum stop if owner later narrows scope:

```text
1Q exact closure + 2Q boundary + 3Q minimum + 4Q support
```

Safety stop:

```text
through 5Q
```

Engine-ready / robust stop:

```text
through 8Q
```

Do not climb past 8Q unless a specific downstream claim fails, changes, or demands more. 8Q is the finite overbuild ceiling for now, not an invitation to infinite escalation.

---

## 1. Flux distinction

Do not confuse two meanings of flux.

### Hopf curvature flux

This exists already at the 1Q/S2 geometry level:

```math
A=d\phi+\cos(2\eta)d\chi
```

```math
F=dA=-2\sin(2\eta)d\eta\wedge d\chi
```

```math
\int F=-4\pi
```

This does not require 3Q.

### QIT-engine / chirality / memory / runtime flux

That is later. For that, 3Q is a plausible minimum floor because it gives the Cl(6)/C8/three-slot structure. 4Q–8Q are support/scaling/stress rungs for later work.

So:

```text
1Q is enough for geometric curvature flux.
3Q is minimum for the QIT-engine floor / three-slot / Cl(6)-style structure.
8Q is robustness and later-work support, not the minimum.
```

---

## 2. Root constraints that every rung must receipt

Every nQ packet must have three explicit root/structure sections.

### F01 — finitude receipt

Do not assume finitude just because arrays are finite. Emit a machine-readable receipt:

```text
F01_finitude_receipt:
  hilbert_dim = 2^n
  computational_basis_count = 2^n
  operator_basis_count = 4^n
  pure_sphere = S^(2^(n+1)-1) subset C^(2^n)
  phase_quotient = CP^(2^n - 1)
  mixed_density_real_dim = 4^n - 1
  active_probe_family_count = finite / named
  quotient_or_relation_table = finite where claimed
  finite_enumeration_bounds = named
  proof_objects = finite variables + finite constraints + finite polynomial identities / finite generator-relation set
```

A symbolic “for all states” proof is allowed only because the carrier has a finite presentation: finite variables, finite constraints, finite generator set, finite relation set.

### N01 — noncommutation receipt

Do not collapse noncommutation into anticommutation.

Root binary order pressure:

```math
[A,B]=AB-BA\neq0
```

or operationally:

```math
A(Bx)\not\sim_{\mathcal M}B(Ax)
```

Each rung must include:

```text
N01_noncommutation_receipt:
  O1 commuting control: AB=BA, order gap = 0
  O2 general noncommuting witness: AB != BA
  O3 noncommuting-but-not-anticommuting witness: AB != BA and AB+BA != 0
  O4 anticommuting Clifford witness: AB+BA=0 and AB != 0
  O5 order-gap receipt on states/probes
  O6 Clifford-family capacity row kept separate from root-order row
```

Example for O3:

```text
A = X
B = X + Z
AB != BA but AB + BA != 0
```

Example for O4:

```text
X and Z anticommute: XZ + ZX = 0 and XZ != 0
```

Anticommutation is a sharpened Clifford special case. It is not the root.

### T01 — ternary/bracketing/nonassociativity receipt

Yes, nonassociativity/bracketing must be tested. But do not fake it.

For qubit matrix algebras:

```math
(AB)C-A(BC)=0
```

always. This must be a control.

Each rung must include:

```text
T01_bracketing_receipt:
  matrix_associator_control: (AB)C - A(BC) = 0 in M_{2^n}(C)
  schedule_or_channel_associator_test if scoped: (A∘B)∘C vs A∘(B∘C)
  explicit statement: algebra-level nonassociativity is not present in qubit matrix multiplication
  boundary: true algebra-level nonassociativity belongs to octonion/nonassociative extension lane
  octonion path: [a,b,c]=(ab)c-a(bc) can be nonzero, associator is alternating / alternativity
  anti-associativity: negative-control/exotic branch only unless separately defined
```

Safe interpretation:

```text
qubit matrix reps are associative;
qubit/channel/measurement/quotient schedules may have bracketing effects;
true algebra-level nonassociativity enters through later octonion/nonassociative extension.
```

---

## 3. General n-qubit theorem spine

For n qubits:

```text
Hilbert carrier: (C^2)^⊗n ~= C^(2^n)
Pure normalized sphere: S^(2^(n+1)-1) subset C^(2^n)
Global phase quotient: S^(2^(n+1)-1)/S^1 = CP^(2^n-1)
Full mixed density space: D(C^(2^n)), real affine dimension 4^n - 1
Clifford floor: Cl_(2n)(C) represented on C^(2^n)
Gamma count: 2n generators plus chirality gamma_(2n+1)
Chirality split for Cl_(2n): 2^(n-1) + 2^(n-1)
Max pairwise anticommuting Hermitian-unitary family in M_(2^n)(C): 2n + 1
```

Max-family upper bound must be proven, not just constructed:

```text
m pairwise anticommuting generators imply a Cl_m(C) representation.
minimal complex representation dimension is 2^floor(m/2).
therefore 2^floor(m/2) <= 2^n.
therefore m <= 2n+1.
```

But keep this row separate from the more general noncommuting row. The max anticommuting family is a Clifford capacity result, not the whole of N01.

---

## 4. Qubit ladder roles

### 1Q — exact Hopf foundation

```text
C2
S3
S3/S1 = CP1 = S2
D(C2) = Bloch ball/channel domain
Hopf map
fiber/phase erasure
linking
SU(2) double cover
Hopf curvature prerequisites
```

Packet already launched:

```text
geo_s1_exact_closure_v0
```

Must close every original S1 G1–G7 leaf claim with zero claim-bearing bare-float rows.

### 2Q — boundary/control rung

```text
C4
S7
CP3
D(C4), real dim 15
Bell/concurrence
Schmidt decomposition
Cl4
gamma5 split 2+2
max anticommuting family 5
```

Main job: prove what 2Q can and cannot do.

Positive:

```text
Cl4 yes
Bell/concurrence yes
2-slot entanglement yes
chirality split 2+2 yes
```

Negative:

```text
Cl6 no
7 anticommuting family no
GHZ/W/3-tangle no
three-slot floor no
```

Also separate:

```text
S7/S1 = CP3
```

from quaternionic Hopf:

```text
S3 -> S7 -> S4
```

### 3Q — minimum Cl6 / C8 / three-slot floor

Packet already launched:

```text
geo_s1_three_qubit_floor_exact_v0
```

Correct wording:

```text
2Q already has Cl4 chirality.
3Q gives the Cl6/C8 floor with six gammas, 4+4 split, 7-generator capacity, and three sites/slots.
```

Do not say 3Q is where chirality first exists in every possible sense.

Required:

```text
C8
S15
CP7
D(C8), real dim 63
Cl6(C) ~= M8(C)
gamma7 split 4+4
max anticommuting family 7
GHZ/W/product exact reduced densities
3-tangle exact values
three-slot schedule boundary
```

Non-conflation:

```text
S15/S1 = CP7 is the 3Q global phase quotient.
S15 -> S8 is the octonionic fibration.
They are not the same structure.
```

### 4Q — later-work support rung

```text
C16
S31
CP15
D(C16), real dim 255
Cl8(C) ~= M16(C)
gamma9 split 8+8
max anticommuting family 9
Spin(8)/triality pressure
GHZ4 / cluster / product / biseparable controls
```

4Q supports later work. It does not prove 3Q minimality by itself.

### 5Q — safety margin / overbuild rung

```text
C32
S63
CP31
D(C32), real dim 1023
Cl10(C)
gamma11 split 16+16
max anticommuting family 11
```

Use it to show the exact machinery survives beyond the immediately needed rung. It is not a new minimum claim.

### 6Q–8Q — scaling / stress / boundary regime

These are not “minimum” rungs. They test whether the exact ladder, Clifford/stabilizer machinery, tensor-network strategy, and later QIT-engine support survive serious dimensional growth.

```text
6Q: C64, S127, CP63, D dim 4095, Cl12, max family 13, split 32+32
7Q: C128, S255, CP127, D dim 16383, Cl14, max family 15, split 64+64
8Q: C256, S511, CP255, D dim 65535, Cl16, max family 17, split 128+128
```

Do not brute-force arbitrary full dense-state enumeration everywhere at 6Q–8Q. Use:

```text
exact constructive families
Clifford/stabilizer subfamilies
named entangled states
finite exhaustive checks over Pauli strings where feasible
theorem receipts
resource-bound rows
sparse/tensor/stabilizer representations where needed
```

---

## 5. Completion standard per rung

Every claim row must be classified as one of:

```text
symbolic_identity
closed_form_integral
exact_integer_combinatorial
rigorous_interval_bound
measure_theorem
finite_exhaustive_enumeration
representation_theorem_with_constructive_receipt
statistical_redundant_by_exact_route
diagnostic_float_nonclaim
open_with_reason
```

Forbidden for claim-bearing rows:

```text
bare_float_tolerance
sample_only
max_deviation_only
abs_error_only
visual agreement
validator-green only
```

Every rung needs:

```text
1. F01_finitude_receipt
2. N01_noncommutation_receipt
3. T01_bracketing_receipt
4. exact convention pins
5. exact positive receipts
6. can-fail negative controls
7. raw-object SMT/proof checks where scoped
8. normal validator pass
9. source-backed validator pass
10. strict-source-backed pass or honest demotion
11. custom exact-strength validator pass
12. fresh blind/audit comparison
13. no-promotion ceiling preserved
```

---

## 6. Operational queue

1. Let current 1Q exact and 3Q builder lanes finish.
2. Harden/audit them against this corrected directive and the existing exact-closure addendum.
3. Add/build 2Q boundary-control exact packet.
4. Build 4Q support/triality/scaling packet.
5. Build 5Q safety-margin packet.
6. Build 6Q, 7Q, 8Q scaling/stress packets.
7. Only then reopen S2 runtime, unless owner explicitly narrows the target.

If 3Q lands before 2Q, status is:

```text
3Q artifact landed early;
sequence closure still blocked until 2Q boundary/control lands.
```

---

## 7. Commit/status language

Use:

```text
S1 qubit ladder strengthened through N qubits as committed scratch diagnostics.
```

Do not use:

```text
formal carrier admission
final M(C)
QIT-engine admission
physics admission
geometry complete
```

S1 ladder closure is stronger scratch evidence, not admission.

---

## 8. Existing controller files

Hermes already wrote these local controller files:

```text
/tmp/s1_deepening_completion_addendum_20260610.md
/tmp/s1_qubit_ladder_directive_20260610.md
/tmp/s1_2q_build_card_20260610.md
/tmp/s1_4q_build_card_20260610.md
/tmp/s1_5q_build_card_20260610.md
```

Ingest them before launching the next wave, but apply the corrections in this message too: F01 explicit, N01 noncommutation before anticommutation, and T01 bracketing/nonassociativity boundary tests.
