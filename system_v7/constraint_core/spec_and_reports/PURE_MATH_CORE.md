---
title: Constraint-Core — Pure-Math Core (this session's earned results, de-jargoned)
date: 2026-07-01
discipline: mathematics first; ALL labels (project jargon AND physics jargon) live in §C.
claim tiers: [exact] provable identity, machine-confirmed · [numeric] machine-verified,
model-dependent · [open] not earned
status: scratch_diagnostic; promotion_allowed=false
---

# A. Objects (no labels)

- **A1.** State space: density matrices on ℂ², ρ = ½(I + xσx + yσy + zσz),
  (x,y,z) ∈ closed unit ball.
- **A2.** Generator class: L(ρ) = −iεg[H₀,ρ] + Σγₖ D[Lₖ]ρ, where
  D[L]ρ = LρL† − ½{L†L, ρ}, ε ∈ {+1,−1}, g > 0, and the dissipator is one of
  three families: **F₁** = D[σ₊] or D[σ₋] (rank-one, pole-seeking);
  **F₂** = ½(D[σx]+D[σy]) (planar); **F₃** = D[σz] (axial). Eight instances:
  indices t0…t7 = (ε, family, pole) per the table in the sims.
- **A3.** Four channel generators:
  **Pz** = pinching onto span{I,σz} (conditional expectation, Kraus
  {√(1−q)I, √q Π₊, √q Π₋} in the σz eigenbasis); **Px** = same for σx;
  **Rx(θ)**, **Rz(θ)** = inner automorphisms ρ ↦ e^{−iθσ/2}ρe^{iθσ/2}.
- **A4.** Three maps on the model: the involution **W** = (σx+σz)/√2
  (W = W†, W² = I); the one-parameter conjugations **V_s** = e^{−iH₀s};
  the antiunitary **K** = entrywise complex conjugation in the σz basis.
- **A5.** The loop functional: for a trajectory γ(t) with Bloch coordinates
  (x(t), y(t)), A[γ] = ½∮(x dy − y dx) (signed swept area in the xy-plane).

# B. Propositions

**P1 — pair conjugacy. [exact]**
W σz W = σx and W σx W = σz, hence as channels
  Ad_W ∘ Pz ∘ Ad_W = Px  and  Ad_W ∘ Rx(θ) ∘ Ad_W = Rz(θ)  for all θ.
The two channel pairs {Pz, Rx} and {Px, Rz} are one pair up to conjugation by
the single involution W. Machine: ≤ 4×10⁻¹⁶.
Moreover W ∉ {V_s} for either choice of H₀ used in the sims: rotations about
σz cannot move the pinching axis at all, and rotations about (1,1,1)/√3 map
Pz → Px only at ±2π/3, where they simultaneously map Rx → Ry ≠ Rz. No element
of the V-group maps the pair to the pair; W does, exactly.

**P2 — conjugation degeneracy of the coherent semigroup. [exact]**
[V_s, e^{−iH₀t}] = 0, therefore Ad_{V_s} ∘ U_t ∘ Ad_{V_s}† = U_t where
U_t = Ad_{e^{−iH₀t}}. A bit defined as "conjugated by V_s or not" is
unobservable on the purely coherent semigroup: the two channels are identical.
Machine: 2×10⁻¹⁶.

**P3 — spectral blindness. [exact, one line]**
spec(VρV†) = spec(ρ) for any unitary V, so every functional of the spectrum
(entropy, purity, any tr f(ρ), and their bipartite combinations) is invariant
under conjugation. Observables split into an eigenvalue sector and an
eigenvector sector; conjugation data lives entirely in the second.

**P4 — parity non-readability. [exact]**
Let a₁ be a bit readable by spectral functionals and a₂ a bit carried only by
the eigenvector sector (P3). Then p = a₁ ⊕ a₂ is computed by no single
spectral functional; and no affine expression sign(αa₁ + βa₂ + γ) equals ⊕.
Any realization of p requires one reading from each sector, combined
multiplicatively.

**P5 — first-order symmetry breaking (the corrected form). [exact + numeric]**
(i) For the one-step family Λ_δ = (1−δ/2)id + (δ/2)Ad_Z, any linear readout
satisfies split(δ) = (δ/2)|c_{Z₁} − c_{Z₀}| — exactly linear because the
family is affine in δ. This is an identity of the parametrization, not a law.
(ii) For the semigroup e^{t(−i[H,·] + δD)}, split(δ) = k₁δ + O(δ²) with
strictly decreasing split/δ (measured 0.297 → 0.064 over δ ∈ [0.05, 3.2]).
The earned content is the coefficient k₁ and the exact zero at δ = 0 (P2).

**P6 — unitality dichotomy: the "surplus" is non-unitality. [exact + numeric]**
All four channel generators of A3 are unital: O(I) = 0 (machine: 0 exactly).
Any linear combination of unital generators is unital. The F₁ generators are
non-unital: L(I) = ±(σ₊σ₋ − σ₋σ₊) ≠ 0, ‖L(I)‖ = √2. Therefore a non-unital
generator has an irreducible component outside the span of the four channel
generators — no frame change removes it. Measured containment residuals:
{0.000, 0.115} for the unital generators (F₂, F₃) vs {0.666, 0.705} for the
non-unital ones (F₁), tracking 𝟙[L(I) ≠ 0] exactly. The 8/8 partition used in
three spec sections is this one bit.

**P7 — the conjugation mirror and the sign of A. [exact for half; numeric for rest]**
Every Lindblad operator in A2–A3 is either real (σx, σz, σ±) or appears in the
K-invariant combination D[σx]+D[σy]; hence K commutes with all dissipators and
flips the sign of every coherent term −i[H,·] with real H. Consequently
ρ̄(t) solves the equation with ε → −ε (and with any coherent drive sign
flipped), and Bloch-wise (x,y,z) → (x,−y,z), so A → −A.
Corollary (exact): for the 8 stages whose channel drive is a pinching (Pz/Px,
K-invariant), ε → −ε negates A identically. Machine: sign-antisymmetric to all
printed digits.
For the 8 rotation-driven stages the drive breaks the mirror: under an
ε-neutral probe, sign(A) tracks ε in 6 of 8; the two failures are
(F₃ generator, Rz) — the fixed rotation rate 0.5 exceeds the signed rate
g = 0.35. Including the ε-signed term ±H₀ in the loop definition restores
16/16. So: exact theorem on the pinching half; a definition-dependent
dynamical statement on the rotation half, failing first exactly at the
weakest-coherence generator (F₃), consistent with the fingerprint bottleneck.

**P8 — fixed points and −ln ρ∞. [numeric, model-dependent]**
For each generator, ρ∞ = ½(I + r∞·σ) and −ln ρ∞ has traceless part along r∞.
Alignment |cos(r∞, coherent axis)| = 1.000 exactly for the isotropic-dissipator
instances and ≈ 1/√3 for the rest (the angle between the fixed axis and the
(1,1,1)/√3 coherent axis). Self-adjointness of L in the ρ∞-weighted inner
product ⟨A,B⟩ = tr(ρ∞^{1/2}A†ρ∞^{1/2}B) fails for all eight (relative
asymmetry 0.42–1.88). The statement "the generator is determined by its own
fixed state" holds in the reconstruction sense (GNS) everywhere, and in the
dynamical sense only where [H_eff, ρ∞] = 0 — currently the isotropic instances.

**P9 — the selection problem. [open, with the candidate mechanism identified]**
No tested functional of a generator (fixed-point displacement, commutation
gap, algebra containment, order gap) selects a preferred channel pair from
{Pz,Rx} vs {Px,Rz}. P1 supplies the only exact pair-level mapping found (the
involution W), and P1 also shows W is not in the V-group. Decidable fork:
either the model's conjugation element is (or contains) W — then the pair
assignment is a covariance theorem — or the assignment remains an external
labelling. This is a lookup in the source operator table, not a new sim.

**P10 — the phase-sector meter and the layer of a2. [earned as sector meter; a2 resolved as a layer statement; spec §7v–§7w]**
An open-path functional χ₂ (Bargmann/Pancharatnam phase of the top eigenvector
against fixed references, on a non-closed segment) is an earned eigenvector-sector
meter: nonzero open / zero closed, gauge-invariant under rephasing, tracks
eigenvectors at fixed spectrum while entropy tracks the spectrum. It is NOT
a2-specific — it responds to all three binary frame operations (a2: V-vs-I; ε:
V-vs-V†; K: V-vs-V*); the §7v demonstration read the K-mirror pair. The
terrain-level a2 readout does not exist and cannot: the ε-even quotient of χ₂ reads
the a1 dynamics bit, not a2 (finite check over the 8 generators), and W conjugates
the four operators into their a2-partners exactly (9×10⁻¹⁶) but does NOT conjugate
the terrain generators (residual ≈2.05). a2 is therefore an OPERATOR-layer label
(P9/§7t), one level above the terrain generators; the parity P4 reads end-to-end at
the operator layer and is carried, not measured, at the terrain layer.

# C. The rosetta layer (labels; NONE load-bearing; several overlays per object)

| Pure object (§A/§B) | index | overlay: QIT names | overlay: Jungian | overlay: physics vocabulary | tier |
|---|---|---|---|---|---|
| ε ∈ {±1} | eps | Left/Right engine | I/E chirality, Type-1/2 | Weyl sheet, chirality | earned (P7) |
| 𝟙[L(I) ≠ 0] | a1 | dissipative/unitary terrain split | {Se,Ni} vs {Ne,Si} | entropy charge, Axis-1 | earned (P6) |
| conjugation by V_s | a2 | direct/conjugated frame | {Se,Ne} vs {Ni,Si} | gauge charge, Axis-2 | earned (P2,P3) |
| a1 ⊕ a2 | p | perceiving split | N vs S | Axis-0 parity | earned as identity (P4); operator-layer readout earned (P10/§7t); terrain-layer readout a no-go (§7w) |
| generator instances t0–t7 | t0..t7 | Funnel, Vortex, Pit, Hill, Cannon, Spiral, Source, Citadel | Se/Ne/Ni/Si ×2 | terrains, basins | earned (fingerprints) |
| Pz, Px, Rx, Rz | Ti, Te, Fi, Fe | judging operators | Ti/Te/Fi/Fe | pinchings, rotations | earned (A3) |
| pair map W | — | native-operator law mechanism | I/E judging alternation | "Hadamard" | candidate (P9) |
| A[γ] sign | — | engine handedness | — | geometric phase | earned (P7, two-tier) |
| −ln ρ∞ | — | "surface is the operator" (strong form) | — | modular Hamiltonian | partial (P8) |
| δ-breaking coefficient k₁ | — | co-ratchet gate | — | gauge-breaking | earned as first-order only (P5) |
| Carnot/Szilard, I-Ching, taijitu, gradient descent = (F₃, Px) order | — | various | various | various | witness/candidate only |

The same column-1 object supports every overlay to its right simultaneously;
none of them constrains the math. Physics vocabulary is an overlay too:
"gauge" is conjugation by V_s, "geometric phase" is A[γ], "modular
Hamiltonian" is −ln ρ∞, "Weyl chirality" is ε, "detailed balance" is
self-adjointness in a weighted inner product. The audits, including this
auditor's previous three reports, used those labels as if primary; this
document is the correction.

# D. Standing corrections to the spec, in pure form

1. §7o: replace "linear law, R² = 1.0" with P5 as stated.
2. §7n: reclassify sector blindness as the one-line theorem P3.
3. §7q: replace "irreducible surplus geometry" with P6 (non-unitality) — the
   claim strengthens: irreducibility is now proved, not measured.
4. §7s: replace "structural theorem 16/16" with the two-tier P7.
5. §7q/§7r native-operator law: resolve P9's fork against the source table.
6. Open queue: P10 is resolved (χ₂ earned as sector meter; a2 realized at the
   operator layer, a no-go at the terrain layer — §7w). Remaining: the P9
   admissibility derivation (why exactly 2 operators per terrain, from C1–C3).
