# Screenshots Index

**Source folder:** `system_v5/READ ONLY Reference Docs/Screenshots/` (READ ONLY)

**Built by:** iter_141–iter_148 session, 2026-05-20

**Claim ceiling:** `side_quest_only`. This doc summarizes content extracted from screenshot images for use by the grok_sim axis-math iters. Not a formal-side artifact. Does not modify any READ ONLY file.

**Inventory:** 25 files in source folder. All readable as PNGs (validated via `file`). Some required retries through the Read tool.

---

## 0. Screenshot-extracted candidate spec — across all readable screenshots

This section is the consolidated spec. Per-file extractions follow in §1–§25.

### Carrier

```
ψ_L, ψ_R ∈ C²,  ‖ψ‖ = 1
S³ = {ψ ∈ C² : ‖ψ‖ = 1}
ρ_s = ψ_s ψ_s† = (1/2)(I + r_s · σ),  s ∈ {L, R}
π(ψ) = ψ† σ ψ ∈ S²    (Hopf projection)

Hopf coordinates:
  ψ_s(φ, χ; η) = ( e^{i(φ+χ)} cos η ,  e^{i(φ-χ)} sin η )
```

### Pauli data

```
σ_x = [[0, 1],[1, 0]]
σ_y = [[0, -i],[i, 0]]
σ_z = [[1, 0],[0, -1]]
σ_- = [[0, 0],[1, 0]]
σ_+ = [[0, 1],[0, 0]]
σ_± = (1/2)(σ_x ± i σ_y)
```

### Hamiltonians

```
H_0 = n_x σ_x + n_y σ_y + n_z σ_z         (base)
H_L = +H_0                                 (Type 1, left Weyl)
H_R = -H_0                                 (Type 2, right Weyl)

Bloch laws:
  ṙ_L = +2 n̂ × r_L     (left, Type 1)
  ṙ_R = -2 n̂ × r_R     (right, Type 2)

Weyl/Pauli covariance:
  σ^μ = (I, σ_x, σ_y, σ_z)
  σ̄^μ = (I, -σ_x, -σ_y, -σ_z)
```

### Nested Hopf-torus family

```
T_η = { (e^{iα} cos η, e^{iβ} sin η) : α, β ∈ S¹ } ⊂ S³

inner loop = Hopf fiber loop
outer loop = lifted base loop
```

### Loop geometry (explicit carriers)

```
torus family       T_η  = { ψ_s(φ, χ; η) : φ, χ ∈ [0, 2π) } ⊂ S³
left  fiber loop   Γ^L_f(η, χ_0) = { ψ_L(φ, χ_0; η)                : φ ∈ [0, 2π) }
left  base-lift    Γ^L_b(η, φ_0) = { ψ_L(φ_0 - cos(2η) χ, χ; η)    : χ ∈ [0, 2π) }
right fiber loop   Γ^R_f(η, χ_0) = { ψ_R(φ, χ_0; η)                : φ ∈ [0, 2π) }
right base-lift    Γ^R_b(η, φ_0) = { ψ_R(φ_0 - cos(2η) χ, χ; η)    : χ ∈ [0, 2π) }

Probe:
  observable probe O = O†
  probe readout    p_O(ρ) = Tr(O ρ)
```

### Common dissipator + channels

```
D[L](ρ) = L ρ L† - (1/2)(L† L ρ + ρ L† L)        (Lindblad dissipator)
Π_P(ρ) = Σ_k P_k ρ P_k                            (projection class)
F_Q(ρ) = F ρ F† / Tr(F ρ F†)                      (filter/measurement)
D_-(ρ) = σ_- ρ σ_+ - (1/2){σ_+ σ_-, ρ}
D_+(ρ) = σ_+ ρ σ_- - (1/2){σ_- σ_+, ρ}
D_P(ρ) = Σ_j ( P_j ρ P_j - (1/2)(P_j ρ + ρ P_j) ) (dephasing class)
```

### Dissipative-operator algebra per terrain

Each L is built from the Pauli generators with terrain-specific scalar coefficients:

```
L^{F,L}_k = a^{F,L,k}_0 I + a^{F,L,k}_x σ_x + a^{F,L,k}_y σ_y + a^{F,L,k}_z σ_z   (Funnel left, k indexes channel)
L^{C,R}_k = a^{C,R,k}_0 I + ...                                                    (Cannon right)
M^{V,L}_k = b^{V,L,k}_x σ_x + b^{V,L,k}_y σ_y + b^{V,L,k}_z σ_z                   (Vortex left)
M^{S,R}_k = b^{S,R,k}_x σ_x + ...                                                  (Spiral right)

Pit/Source dissipators (pure):
  Pit:    γ_{Pi,L} D[σ_-](ρ_L)
  Source: γ_{So,R} D[σ_+](ρ_R)

Hill/Citadel projectors:
  P^{H,L}_j = (1/2)(I + m̂^{H,L}_j · σ),  [K_L, P^{H,L}_j] = 0
  P^{C,LR}_j = (1/2)(I + m̂^{C,LR}_j · σ)
```

### Eight terrain laws (full forms)

**Left sheet / Type 1 laws** (Inward terrains, on ρ_L with H_L = +H_0):

| Terrain | Jung | Density law |
|---|---|---|
| Funnel | Se-IN | ρ̇_L = Σ_k D[L^{F,L}_k](ρ_L) − i ε_{F,L} [H_L, ρ_L] |
| Vortex | Ne-IN | ρ̇_L = −i [H_L, ρ_L] + ε_{V,L} Σ_k D[M^{V,L}_k](ρ_L) |
| Pit    | Ni-IN | ρ̇_L = γ_{P,L} D[σ_-](ρ_L) − i ε_{P,L} [H_L, ρ_L] |
| Hill   | Si-IN | ρ̇_L = −i [K_L, ρ_L] + Σ_j κ_{H,L,j} ( P^{H,L}_j ρ_L P^{H,L}_j − (1/2)(P^{H,L}_j ρ_L + ρ_L P^{H,L}_j) ) |

**Right sheet / Type 2 laws** (Outward terrains, on ρ_R with H_R = −H_0):

| Terrain | Jung | Density law |
|---|---|---|
| Cannon  | Se-OUT | ρ̇_R = Σ_k D[L^{C,R}_k](ρ_R) − i ε_{C,R} [H_R, ρ_R] |
| Spiral  | Ne-OUT | ρ̇_R = −i [H_R, ρ_R] + ε_{S,R} Σ_k D[M^{S,R}_k](ρ_R) |
| Source  | Ni-OUT | ρ̇_R = γ_{So,R} D[σ_+](ρ_R) − i ε_{So,R} [H_R, ρ_R] |
| Citadel | Si-OUT | ρ̇_R = −i [K_R, ρ_R] + Σ_j κ_{C,L,j} ( P^{C,LR}_j ρ_R P^{C,LR}_j − (1/2)(P^{C,LR}_j ρ_R + ρ_R P^{C,LR}_j) ) |

### Exact terrain-pair separation

| Pair | Mathematical difference |
|---|---|
| Funnel / Cannon | projector class vs Fourier class, plus commutator sign flips |
| Vortex / Spiral | Hamiltonian sign flips, projector correction direction reversed |
| Pit / Source | σ_− damping vs σ_+ excitation; commutator sign flips |
| Hill / Citadel | same strata algebra, opposite orientation sign |

### Four loops

```
Type 1 inner loop : (ρ_L, Γ^L_f)     Type 1 outer loop : (ρ_L, Γ^L_b)
Type 2 inner loop : (ρ_R, Γ^R_f)     Type 2 outer loop : (ρ_R, Γ^R_b)

These four are NOT the same because:
  Γ^L_f ≠ Γ^L_b ,  Γ^R_f ≠ Γ^R_b ,  H_L ≠ H_R
```

### Full 16 placements

Each placement is a pair (X, Γ) where X is the density-law generator and Γ is the carrier:

| # | Label | (X, Γ) |
|---|---|---|
| 1 | Se / Funnel on Type 1 inner | (X^L_F, Γ^L_f) |
| 2 | Ne / Vortex on Type 1 inner | (X^L_V, Γ^L_f) |
| 3 | Ni / Pit on Type 1 inner | (X^L_P, Γ^L_f) |
| 4 | Si / Hill on Type 1 inner | (X^L_H, Γ^L_f) |
| 5 | Se / Funnel on Type 1 outer | (X^L_F, Γ^L_b) |
| 6 | Ne / Vortex on Type 1 outer | (X^L_V, Γ^L_b) |
| 7 | Ni / Pit on Type 1 outer | (X^L_P, Γ^L_b) |
| 8 | Si / Hill on Type 1 outer | (X^L_H, Γ^L_b) |
| 9 | Se / Cannon on Type 2 inner | (X^R_C, Γ^R_f) |
| 10 | Ne / Spiral on Type 2 inner | (X^R_S, Γ^R_f) |
| 11 | Ni / Source on Type 2 inner | (X^R_{So}, Γ^R_f) |
| 12 | Si / Citadel on Type 2 inner | (X^R_{Ci}, Γ^R_f) |
| 13 | Se / Cannon on Type 2 outer | (X^R_C, Γ^R_b) |
| 14 | Ne / Spiral on Type 2 outer | (X^R_S, Γ^R_b) |
| 15 | Ni / Source on Type 2 outer | (X^R_{So}, Γ^R_b) |
| 16 | Si / Citadel on Type 2 outer | (X^R_{Ci}, Γ^R_b) |

### Counts

| Object | Count | Formula |
|---|---|---|
| topology families | 4 | Se, Ne, Ni, Si |
| terrains per engine | 4 | Type 1: Funnel, Vortex, Pit, Hill; Type 2: Cannon, Spiral, Source, Citadel |
| loop families per engine | 2 | inner, outer |
| stage placements per engine | 8 | 4 × 2 |
| stage placements across both engines | 16 | 4 × 2 × 2 |

### Sim shape (composition hierarchy)

```
Φ_substage                                                                  (single sub-operator application)
Φ_stage    = Φ_substage,4 ∘ Φ_substage,3 ∘ Φ_substage,2 ∘ Φ_substage,1     (4 substages → 1 stage)
Φ_loop     = Φ_stage,4 ∘ Φ_stage,3 ∘ Φ_stage,2 ∘ Φ_stage,1                 (4 stages → 1 loop)
Φ_engine   = Φ_outer_loop ∘ Φ_inner_loop                                   (or reverse, per schedule)
Φ_schedule = Φ_engine,N ∘ ... ∘ Φ_engine,1                                 (N engines)
```

### Direct mapping stack

| Level | Mathematical object |
|---|---|
| Pauli layer | I, σ_x, σ_y, σ_z |
| spinor layer | ψ ∈ S³ ⊂ C² |
| density layer | ρ = (1/2)(I + r·σ) |
| Weyl layer | H_L = +H_0, H_R = −H_0 |
| terrain layer | one of the 8 terrain laws above |
| loop layer | inner Hopf fiber or outer lifted-base placement |

### Where the axes sit (pure-math role of each)

| Axis | Pure math role |
|---|---|
| A_0 | external scalar field on M (constraint manifold) |
| A_1 | unitary vs proper CPTP dynamics |
| A_2 | direct vs unitarily conjugated representation |
| A_3 | outer-loop family vs inner-loop family |
| A_4 | UEUE vs EUEU composite order |
| A_5 | dissipative generator algebra vs coherent spectral generator algebra |
| A_6 | left action A·ρ vs right action ρ·A |

### Axis 6 sign meaning

| Sign | Meaning |
|---|---|
| UP | operator first |
| DOWN | terrain first |

### Global locks (Type-1 vs Type-2)

| Layer | Type-1 | Type-2 |
|---|---|---|
| Flux | IN | OUT |
| Major / Outer casing | WIN / LOSE | WIN / LOSE |
| Minor / Inner casing | win / lose | win / lose |
| Outer loop family | Deductive (FeTi-family token mix) | Inductive (TeFi) |
| Inner loop family | Inductive (TeFi) | Deductive (FeTi) |

### Loop orders + edge walks

| A_4 family | Terrain order | Edge-walk (Ax0 vs Ax2) |
|---|---|---|
| Inductive | Se → Si → Ni → Ne | Ax0 → Ax2 → Ax0 → Ax2 |
| Deductive | Se → Ne → Ni → Si | Ax2 → Ax0 → Ax2 → Ax0 |

### Terrain graph (K_{2,2})

```
Ax0 edges (yin-yang opposite pairs):  Se–Si,  Ne–Ni
Ax2 edges (within-frame pairs):       Se–Ne,  Si–Ni
```

### Type-1 full chart (Topology screenshot)

| Step | Topology | Terrain | Loop | Order family | Stage token | Axis 6 | Signed op | Result | Pattern |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Se | Se-in | Outer / Major | Deductive | TiSe | UP   | Ti↑ | LOSE | LOSEwin |
| 2 | Ne | Ne-in | Outer / Major | Deductive | NeTi | DOWN | Ti↑ | WIN  | WINlose |
| 3 | Ni | Ni-in | Outer / Major | Deductive | NiFe | DOWN | Fe↑ | LOSE | loseLOSE |
| 4 | Si | Si-in | Outer / Major | Deductive | FeSi | UP   | Fe↑ | WIN  | winWIN |
| 1 | Se | Se-in | Inner / Minor | Inductive | SeFi | DOWN | Fi↑ | win  | LOSEwin |
| 2 | Si | Si-in | Inner / Minor | Inductive | SiTe | DOWN | Te↑ | win  | winWIN |
| 3 | Ni | Ni-in | Inner / Minor | Inductive | TeNi | UP   | Te↑ | lose | loseLOSE |
| 4 | Ne | Ne-in | Inner / Minor | Inductive | FiNe | UP   | Fi↑ | lose | WINlose |

### Type-2 full chart

| Step | Topology | Terrain | Loop | Order family | Stage token | Axis 6 | Signed op | Result | Pattern |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Se | Se-out | Outer / Major | Inductive | FiSe | UP   | Fi↑ | WIN  | loseWIN |
| 2 | Si | Si-out | Outer / Major | Inductive | TeSi | UP   | Te↑ | WIN  | WINwin |
| 3 | Ni | Ni-out | Outer / Major | Inductive | NiTe | DOWN | Te↑ | LOSE | LOSElose |
| 4 | Ne | Ne-out | Outer / Major | Inductive | NeFi | DOWN | Fi↑ | LOSE | winLOSE |
| 1 | Se | Se-out | Inner / Minor | Deductive | SeTi | DOWN | Ti↑ | lose | loseWIN |
| 2 | Ne | Ne-out | Inner / Minor | Deductive | TiNe | UP   | Ti↑ | win  | winLOSE |
| 3 | Ni | Ni-out | Inner / Minor | Deductive | FeNi | UP   | Fe↑ | win  | LOSElose |
| 4 | Si | Si-out | Inner / Minor | Deductive | SiFe | DOWN | Fe↑ | lose | WINwin |

### Invariants per engine (count of WIN/LOSE/win/lose stages)

| Engine | WIN | LOSE | win | lose |
|---|---|---|---|---|
| Type-1 | 2 | 2 | 2 | 2 |
| Type-2 | 2 | 2 | 2 | 2 |

### "Actual candidate math" simple-form 8-terrain table

This is the simpler single-matrix realization of each terrain (one L per terrain instead of a linear-combo family):

| Terrain | Jung | Type | L matrix | Hamiltonian | Equation |
|---|---|---|---|---|---|
| Funnel | Se | 1 | σ_z = [[1,0],[0,-1]] | +n·σ | ρ̇ = −i(Hρ − ρH) + LρL† − (1/2)(L†Lρ + ρL†L) |
| Cannon | Se | 2 | σ_z | −n·σ | same |
| Vortex | Ne | 1 | σ_x = [[0,1],[1,0]] | +n·σ | same |
| Spiral | Ne | 2 | σ_x | −n·σ | same |
| Pit    | Ni | 1 | σ_y = [[0,-i],[i,0]] | +n·σ | same |
| Source | Ni | 2 | σ_y | −n·σ | same |
| Hill   | Si | 1 | σ_- = [[0,0],[1,0]] | +n·σ | same |
| Citadel| Si | 2 | σ_- | −n·σ | same |

> Note: this "simple" table differs from the formal "Eight Terrain Laws" spec in two places: Pit/Source use σ_y here vs σ_-/σ_+ in the formal laws; Hill/Citadel use σ_- here vs projector dephasing in the formal laws. Both forms are self-consistent under the axis algebra within iter_148 sidequest encoding (C6: R1∧R2∧R3 holds in either encoding). This is not formal terrain-law admission.

### Inward vs Outward terrains — native distinctions

**Inward terrains (Type 1, left Weyl sheet):**

| Terrain | Family | Exact working law | Native distinction |
|---|---|---|---|
| Funnel | Se-IN | ρ̇ = η_F (Π_P(ρ) − ρ) − iε_F[H_0, ρ] | projector-led inward boundary carving |
| Vortex | Ne-IN | ρ̇ = −i[H_0, ρ] + η_V (F_Q(ρ) − ρ) | negative Hamiltonian orientation with inward spectral correction |
| Pit    | Ni-IN | ρ̇ = γ_P D_−(ρ) − iε_P[H_0, ρ] | damping-to-attractor inward sink |
| Hill   | Si-IN | ρ̇ = −i[H_0, ρ] + κ_H D_P(ρ);  [H_0, P] = 0 | commuting inward retention on invariant strata |

**Outward terrains (Type 2, right Weyl sheet):**

| Terrain | Family | Exact working law | Native distinction |
|---|---|---|---|
| Cannon  | Se-OUT | ρ̇ = η_C (F_Q(ρ) − ρ) + iε_C[H_0, ρ]  | Fourier-led outward signal release |
| Spiral  | Ne-OUT | ρ̇ = +i[H_0, ρ] + η_S (Π_P(ρ) − ρ)    | positive Hamiltonian orientation with outward projector correction |
| Source  | Ni-OUT | ρ̇ = γ_S D_+(ρ) − iε_S[H_0, ρ]         | excitation-from-source outward emission |
| Citadel | Si-OUT | ρ̇ = +i[H_0, ρ] + κ_C D_P(ρ);  [H_0, P] = 0 | commuting outward retention with opposite orientation |

### Exact inward-vs-outward pairing

| Pair | Inward law | Outward law | Difference |
|---|---|---|---|
| Funnel / Cannon | η_F(Π_P − ρ) − iε_F[H_0, ρ] | η_C(F_Q − ρ) + iε_C[H_0, ρ] | projector term vs Fourier term, and commutator sign flips |
| Vortex / Spiral | −i[H_0, ρ] + η_V(F_Q − ρ) | +i[H_0, ρ] + η_S(Π_P − ρ) | Hamiltonian sign flips, and correction channel swaps |
| Pit / Source | γ_P D_− − iε_P[H_0, ρ] | γ_S D_+ − iε_S[H_0, ρ] | σ_− damping vs σ_+ excitation, and commutator sign flips |
| Hill / Citadel | −i[H_0, ρ] + κ_H D_P | +i[H_0, ρ] + κ_C D_P | same strata algebra, opposite orientation sign |

### Two senses in which axes can operate on Weyl spinors

**1. Geometry-side** — directly on Weyl sectors as spinor dynamics. Example: chirality-side Hamiltonians can be written as `H_L = +n̂·σ`, `H_R = −n̂·σ`. Or covariantly as `σ^μ = (I, σ_x, σ_y, σ_z)` and `σ̄^μ = (I, −σ_x, −σ_y, −σ_z)`. That is the **Weyl/Pauli** alignment.

**2. QIT-side** — most of the axis math acts more cleanly on density operators and channels:

```
ρ ↦ U ρ U† ,    ρ ↦ Φ(ρ) ,    ρ̇ = −i[H, ρ] ,    ρ̇ = L(ρ)
```

So for kernel work, the best move is usually:

```
Weyl spinor geometry  →  density operator layer  →  axis algebra
```

### Axis 0 caveats ("it Hand oft" screenshot)

```
φ_0(x) = Φ_0(ρ(x))
Φ_0(ρ) = Σ_r w_r I_c(A_r > B_r)_ρ = − Σ_r w_r S(A_r | B_r)_ρ
```

- Axis 0 acts on the manifold through the state attached to each point.
- It is NOT an engine operator.
- It grades trajectories on the nested Hopf/Weyl geometry.
- A single isolated Weyl spinor is **not enough for conditional entropy**. Conditional entropy needs a bipartite state ρ_AB. So for Axis 0 you usually need:
  - a coupled left/right state ρ_LR, or
  - a shell-cut bipartition ρ_{A_r, B_r}, or
  - a reduced multipartite state derived from the manifold point.
- Strict pipeline:  `x ∈ M ↦ (ψ_L(x), ψ_R(x)) ↦ ρ_LR(x) or ρ_{A,B}(x) ↦ Φ_0(ρ(x))`

---

## Per-file inventory

### 1. `0. - (o, tio,).png` — 2044×1326

**Topics:** Inward Terrains, Outward Terrains, Exact Inward-vs-Outward Pairing.

**Content extracted:** Inward Terrains table (Funnel/Vortex/Pit/Hill — Type 1) with Family, Exact working law, Native distinction columns. Outward Terrains table (Cannon/Spiral/Source/Citadel — Type 2) with same columns. Exact Inward vs Outward Pairing table showing all 4 pair comparisons. Also includes the σ_± = (1/2)(σ_x ± i σ_y) definition at the top.

**Consumed by:** iter_148 (terrain-pair separations).

### 2. `1(0) -1021 - 3(1 +7-0).png` — 1990×1488

**Topics:** Carrier (S³, π, ρ), Nested Hopf-torus family, Weyl sectors.

**Content extracted:**
- S³ = {ψ ∈ C² : ‖ψ‖ = 1}
- π(ψ) = ψ†σψ ∈ S²
- ρ(ψ) = (1/2)(I + r·σ)
- σ = (σ_x, σ_y, σ_z)
- T_η = { (e^{iα} cos η, e^{iβ} sin η) : α, β ∈ S¹ } ⊂ S³
- inner loop = Hopf fiber loop; outer loop = lifted base loop
- ρ_L = (1/2)(I + r_L·σ), ρ_R = (1/2)(I + r_R·σ)
- H_0 = n_x σ_x + n_y σ_y + n_z σ_z
- H_L = +H_0, H_R = −H_0

**Consumed by:** iter_148.

### 3. `Can it operate directly on leftjright Weyt spinors.png` — 2076×1670

**Topics:** Two senses of axis action; Where the axes sit (pure-math role table).

**Content extracted:** see §0 "Two senses…" and "Where the axes sit" tables.

**Consumed by:** iter_148 (informed C2, C3 design).

### 4. `Common Operators.png` — 1774×1124

**Topics:** Density matrix, base Hamiltonian, projection class, filter class, Lindblad terms for σ_±, dephasing class.

**Content extracted:**
- ρ ∈ D(H), ρ = (1/2)(I + r·σ)
- H_0 = (1/2)(n_x σ_x + n_y σ_y + n_z σ_z)  (note: 1/2 prefactor differs from other screenshots)
- Π_P(ρ) = Σ_k P_k ρ P_k
- F_Q(ρ) = F ρ F† / Tr(F ρ F†)
- D_-(ρ) = σ_- ρ σ_+ − (1/2){σ_+ σ_-, ρ}
- D_+(ρ) = σ_+ ρ σ_- − (1/2){σ_- σ_+, ρ}
- D_P(ρ) = Σ_j ( P_j ρ P_j − (1/2)(P_j ρ + ρ P_j) )
- σ_± = (1/2)(σ_x ± i σ_y)

**Consumed by:** iter_148.

### 5. `Image.png` — 238×169

**Topics:** Six yin-yang visual variants (no math content).

**Consumed by:** none (visual reference only).

### 6. `Minor  Inner casing.png` — 2006×1382 (note: double space in filename)

**Topics:** Global locks (Type-1 vs Type-2), Loop orders, Terrain graph edges, Edge walks.

**Content extracted:**
- Global locks (Flux, Major/Outer casing, Minor/Inner casing, Outer loop family, Inner loop family) — see §0.
- Loop orders:
  - Inductive: Se → Si → Ni → Ne
  - Deductive: Se → Ne → Ni → Si
- Terrain graph edges:
  - Ax0 edges: Se-Si, Ne-Ni
  - Ax2 edges: Se-Ne, Si-Ni
- Loop edge walks:
  - Inductive: Ax0 → Ax2 → Ax0 → Ax2
  - Deductive: Se → Ne → Ni → Si  with walk Ax2 → Ax0 → Ax2 → Ax0

**Consumed by:** iter_147 (S3, S4 tests).

### 7. `NeTX.png` — 2094×1546

**Topics:** Axis 6 sign meaning; Type-1 full chart with all 8 stages; Type-1 loop view; Type-2 full chart.

**Content extracted:**
- Axis 6 sign: UP = operator first, DOWN = terrain first.
- Type-1 full chart (8 rows) with Topology, Terrain, Outer/Major pair, Ax6, Signed op, Outer result, Inner/Minor pair, Ax6, Signed op, Inner result, Pattern columns.
- Type-1 loop view (Outer Major Deductive, Inner Minor Inductive with per-step Stage 1–4 entries).
- Type-2 full chart (8 rows, mirror).

**Consumed by:** iter_147 (S2 Axis-6 prediction test sources this data).

### 8. `Outer  Malor.png` — 2106×1452 (note: double space)

**Topics:** Type-2 loop view; Topology-aligned comparison; Invariants per engine; Engine ↑/↓ stage counts.

**Content extracted:**
- Type-2 loop view (Outer Major Inductive, Inner Minor Deductive per-stage entries).
- Topology-aligned comparison table: for each Topology (Se/Ne/Ni/Si), shows Type-1 terrain | Type-1 major | Type-1 minor | Type-2 terrain | Type-2 major | Type-2 minor.
- Invariants: each Engine has 2 WIN, 2 LOSE, 2 win, 2 lose stages.
- Engine ↑ stages | ↓ stages:
  - Type-1: Ti↑, Fe↑, Fi↑, Te↑ | Ti↓, Fe↓, Fi↓, Te↓
  - Type-2: same balance

**Consumed by:** iter_147.

### 9. `Pasted Graphic 1.png` — 2092×606

**Topics:** outer = deductive / inner = inductive; 4-step traversal with Outer pair, Ax6, Outer result, Inner pair, Ax6, Inner result columns.

**Content extracted:** Per-stage 4-row table showing Step | Outer deductive terrain | Outer pair | Ax6 | Outer result | Inner inductive terrain | Inner pair | Ax6 | Inner result. Plus a "Layer | Meaning" table where "Engine type | chooses `in` vs `out` terrain family".

**Consumed by:** iter_147.

### 10. `Screenshot 2026-03-28 at 1.25.58 PM.png` — 2174×1168

**Topics:** Carrier definitions; Pauli Matrices table.

**Content extracted:**
- spinor carrier ψ ∈ C², ‖ψ‖ = 1
- pure-state manifold S³
- Hopf projection π(ψ) = ψ†σψ ∈ S²
- density matrix ρ(ψ) = (1/2)(I + r·σ)
- Pauli basis σ = (σ_x, σ_y, σ_z)
- Standard 2×2 matrices for I, σ_x, σ_y, σ_z, σ_-, σ_+ (see §0).

**Consumed by:** iter_148.

### 11. `Screenshot 2026-03-28 at 1.26.46 PM.png` — 2068×1182

**Topics:** Nested Hopf Tori; Weyl Sheets; Weyl Rotation Laws; Dissipator.

**Content extracted:**
- T_η = { (e^{iα} cos η, e^{iβ} sin η) : α, β ∈ S¹ } ⊂ S³
- Γ_inner = Hopf fiber loop; Γ_outer = lifted base loop
- Type-1 engine: left Weyl sheet, ρ_L = (1/2)(I + r_L·σ), H_L = +H_0
- Type-2 engine: right Weyl sheet, ρ_R = (1/2)(I + r_R·σ), H_R = −H_0
- Base Hamiltonian H_0 = n_x σ_x + n_y σ_y + n_z σ_z
- Weyl rotation laws:
  - Type-1: ρ̇_L = −i[H_L, ρ_L], ṙ_L = +2 n̂ × r_L
  - Type-2: ρ̇_R = −i[H_R, ρ_R], ṙ_R = −2 n̂ × r_R
- Lindblad dissipator D[L](ρ) = LρL† − (1/2)(L†Lρ + ρL†L)

**Consumed by:** iter_148 (C2, C3 tests).

### 12. `Screenshot 2026-03-28 at 1.27.22 PM.png` — 2172×1570

**Topics:** Eight Terrain Laws (Type 1 + Type 2); Exact Terrain Pair Separation; Loop Placement By Engine; Count Table.

**Content extracted:**
- Eight terrain laws split into Type-1 (left sheet) and Type-2 (right sheet) — see §0 "Eight terrain laws" tables.
- Exact terrain pair separation:
  - Funnel/Cannon: opposite Weyl sign and distinct dissipative family
  - Vortex/Spiral: opposite Hopf chirality handedness
  - Pit/Source: sink vs source
  - Hill/Citadel: distinct retained strata on opposite sheets
- Loop placement by engine (4 rows): Type-1 inner: vector field along Hopf fiber direction; Type-1 outer: along lifted-base direction; Type-2 mirror.
- Each row "What stays the same": same Type-1 (or Type-2) terrain law.

**Consumed by:** iter_148.

### 13. `Screenshot 2026-03-28 at 1.27.50 PM.png` — 2264×1536

**Topics:** Loop Placement By Engine; Count Table; Direct Mapping Stack.

**Content extracted:**
- Loop Placement By Engine table (same as §12 above).
- Count Table (4 rows): topology families 4, terrains per engine 4, loop families per engine 2 (inner, outer), stage placements per engine 8 (4×2), stage placements across both engines 16 (4×2×2).
- Direct Mapping Stack (6 rows): Pauli layer (I, σ_x, σ_y, σ_z); spinor layer (ψ ∈ S³ ⊂ C²); density layer (ρ = (1/2)(I + r·σ)); Weyl layer (H_L = +H_0, H_R = −H_0); terrain layer (one of 8 laws); loop layer (inner Hopf fiber or outer lifted base).

**Consumed by:** iter_148.

### 14. `Screenshot 2026-03-28 at 2.14.07 PM.png` — 1976×1518

**Topics:** Definitions: Carrier + Pauli Data (cleaner version of #10).

**Content extracted:** ψ_L, ψ_R ∈ C² with ‖ψ‖ = 1; S³ carrier; ρ_L, ρ_R = ψ ψ† = (1/2)(I + r·σ); Hopf coords ψ_s(φ, χ; η) = (e^{i(φ+χ)} cos η, e^{i(φ−χ)} sin η); π(ψ) = ψ†σψ. Pauli matrices I, σ_x, σ_y, σ_z, σ_-, σ_+ explicitly.

**Consumed by:** iter_148.

### 15. `Screenshot 2026-03-28 at 2.14.19 PM.png` — 1982×1266

**Topics:** Hamiltonians; Dissipative Objects.

**Content extracted:**
- base Hamiltonian H_0 = n_x σ_x + n_y σ_y + n_z σ_z
- left Hamiltonian H_L = +H_0
- right Hamiltonian H_R = −H_0
- left Bloch law ṙ_L = +2 n̂ × r_L
- right Bloch law ṙ_R = −2 n̂ × r_R
- dissipator D[L](ρ) = LρL† − (1/2)(L†Lρ + ρL†L)
- L^{F,L}_k, L^{C,R}_k, M^{V,L}_k, M^{S,R}_k as σ-coefficient linear combos
- left Si projectors P^{H,L}_j = (1/2)(I + m̂_j^{H,L}·σ), [K_L, P^{H,L}_j] = 0
- right Si projectors P^{C,LR}_j similarly

**Consumed by:** iter_148.

### 16. `Screenshot 2026-03-28 at 2.14.37 PM.png` — 2132×1420

**Topics:** Loop Geometry (explicit carriers Γ); Probe; Eight Terrain Laws (left sheet beginning).

**Content extracted:**
- torus family T_η = {ψ_s(φ,χ;η) : φ,χ ∈ [0, 2π)} ⊂ S³
- left fiber loop Γ^L_f(η, χ_0) = {ψ_L(φ_0, χ; η) : φ ∈ [0, 2π)}
- left base-lift Γ^L_b(η, φ_0) = {ψ_L(φ_0 − cos(2η)χ, χ; η) : χ ∈ [0, 2π)}
- right fiber loop Γ^R_f
- right base-lift Γ^R_b
- probe: observable O = O†, readout p_O(ρ) = Tr(Oρ)
- Eight terrain laws (left sheet / Type 1 laws header + Se/Funnel, Ne/Vortex, Ni/Pit, Si/Hill density laws)

**Consumed by:** iter_148.

### 17. `Screenshot 2026-03-28 at 2.14.49 PM.png` — 2044×1184

**Topics:** Eight Terrain Laws (both sheets) — cleanest form.

**Content extracted:** Left sheet / Type 1 laws (Se/Funnel, Ne/Vortex, Ni/Pit, Si/Hill); Right sheet / Type 2 laws (Se/Cannon, Ne/Spiral, Ni/Source, Si/Citadel). See §0 "Eight terrain laws" tables. Plus "The Four Loops" header.

**Consumed by:** iter_148.

### 18. `Screenshot 2026-03-28 at 2.15.05 PM.png` — 2088×1490

**Topics:** The Four Loops; Type 1 Inner Loop; Type 1 Outer Loop.

**Content extracted:**
- The Four Loops: Type-1 inner (ρ_L, Γ^L_f), Type-1 outer (ρ_L, Γ^L_b), Type-2 inner (ρ_R, Γ^R_f), Type-2 outer (ρ_R, Γ^R_b).
- "These four are not the same because: Γ^L_f ≠ Γ^L_b, Γ^R_f ≠ Γ^R_b, H_L ≠ H_R."
- Type-1 Inner Loop (4 stages): Se/Funnel, Ne/Vortex, Ni/Pit, Si/Hill with carrier constraint ψ_L(t) ∈ Γ^L_f and density law ρ̇_L = X^L_F, X^L_V, X^L_P, X^L_H respectively.
- Type-1 Outer Loop (4 stages): same labels but ψ_L(t) ∈ Γ^L_b.

**Consumed by:** iter_148.

### 19. `Screenshot 2026-03-28 at 2.15.21 PM.png` — 2080×1380

**Topics:** Type-1 Outer Loop (continued); Type-2 Inner Loop; Type-2 Outer Loop.

**Content extracted:**
- Type-1 Outer Loop end of table.
- Type-2 Inner Loop (4 stages): Se/Cannon, Ne/Spiral, Ni/Source, Si/Citadel with carrier ψ_R(t) ∈ Γ^R_f and density law ρ̇_R = X^R_C, X^R_S, X^R_{So}, X^R_{Ci}.
- Type-2 Outer Loop (4 stages): same labels, carrier Γ^R_b.

**Consumed by:** iter_148.

### 20. `Screenshot 2026-03-28 at 2.15.31 PM.png` — 2102×1572

**Topics:** Full 16 Placements; Count.

**Content extracted:** 16-row table listing each of the 16 placements with explicit (X, Γ) pair — see §0 "Full 16 placements". Plus Count table: loops 4, stages per loop 4, placements 16.

**Consumed by:** iter_148.

### 21. `Sim shape.png` — 1782×668

**Topics:** Composition hierarchy Φ_substage → Φ_stage → Φ_loop → Φ_engine → Φ_schedule.

**Content extracted:**
- Φ_stage = Φ_substage,4 ∘ Φ_substage,3 ∘ Φ_substage,2 ∘ Φ_substage,1
- Φ_loop = Φ_stage,4 ∘ Φ_stage,3 ∘ Φ_stage,2 ∘ Φ_stage,1
- Φ_engine = Φ_outer_loop ∘ Φ_inner_loop (or reverse)
- Φ_schedule = Φ_engine,N ∘ … ∘ Φ_engine,1
- "The sim must be tiered."

**Consumed by:** iter_148 (informed placement structure).

### 22. `Terrain.png` — 2048×886

**Topics:** Type-1 + Type-2 terrain tables with Topology, Terrain, Major/Outer Axis 6, Minor/Inner Axis 6, Pattern columns.

**Content extracted:**

Type-1 (rows: Ne, Si, Se, Ni):
- Ne / Ne-in : outer Ax6 = DOWN (Ti↑/WIN), inner Ax6 = UP (Fi↑/lose), Pattern = WINlose
- Si / Si-in : outer Ax6 = UP (Fe↑/WIN), inner Ax6 = DOWN (Te↑/win), Pattern = winWIN
- Se / Se-in : outer Ax6 = UP (Ti↑/LOSE), inner Ax6 = DOWN (Fi↓/win), Pattern = LOSEwin
- Ni / Ni-in : outer Ax6 = DOWN (Fe↑/LOSE), inner Ax6 = UP (Te↑/lose), Pattern = loseLOSE

Type-2 (rows: Ne, Si, Se, Ni):
- Ne / Ne-out: outer Ax6 = UP, inner Ax6 = UP, …
- (entries hard to OCR — see source image)

**Consumed by:** iter_147 (S2 test sources this).

### 23. `The actuel candidene math we've been ceeling la lunt thit, once, in one table.png` — 2048×812

**Topics:** Single-table "candidate math" — 8 terrains with L matrix + Hamiltonian matrix + single Lindblad equation.

**Content extracted:** See §0 "Actual candidate math simple-form 8-terrain table".

**Consumed by:** iter_147 (Ne σ_+ → σ_x correction noted).

### 24. `Topology.png` — 2050×1408

**Topics:** Type-1 + Type-2 Full Chart with Step, Topology, Terrain, Loop, Order family, Stage token, Axis 6, Signed operator, Result, Pattern columns.

**Content extracted:** See §0 "Type-1 full chart" and "Type-2 full chart" tables. Each is 8 rows (4 outer + 4 inner) with all columns filled in.

**Consumed by:** iter_147 (consistency check against my axis math).

### 25. `Yin and yang.png` — 640×503

**Topics:** Philosophical background (Wikipedia-style blurb) + nested torus diagram showing "Information flux on the Topology of the Torus" (Gravity / Dark Energy at top/bottom, Spiral Information Trajectory, Event Horizon, Inner Core; Negentropic Converging Halve vs Entropic Diversion Halve labels; Entropic information generation / compression / unfolding at the bottom).

**Content extracted:** Visual diagram of nested torus structure aligning with the inner/outer Hopf-loop split. Information flux distinction: convergent (neg-entropic) and divergent (entropic) halves. Wikipedia-style yin-yang summary text.

**Consumed by:** iter_148 (informed the geometric reading of fiber/base loops).

---

## Inter-screenshot inconsistencies

1. **Ne Lindblad operator**: "Actual candidate math" table says σ_x. The formal terrain-laws screenshot (2.14.49) describes Ne as Hamiltonian-led circulation with generic M^{V,L}_k linear combo (no single σ specified). My iter_141 had σ_+. iter_147 logged the σ_+ → σ_x correction.

2. **Pit/Source Lindblad operator**: "Actual candidate math" table says σ_y for both Pit and Source. The formal terrain-laws screenshot (2.14.49) says σ_- for Pit and σ_+ for Source (sink vs source). The two encodings give different dynamics; iter_148 C4 used the σ_-/σ_+ form and confirmed sink-to-|1⟩ / source-to-|0⟩.

3. **Hill/Citadel Lindblad form**: "Actual candidate math" table says σ_-. The formal terrain-laws screenshot (2.14.49) says projector dephasing D_P with [K, P] = 0. The two are not the same channel — σ_- decays toward a polar pure state; projector dephasing preserves diagonal entries in the projector basis.

4. **H_0 prefactor**: "Common Operators" screenshot uses H_0 = (1/2)(n_x σ_x + n_y σ_y + n_z σ_z). The 2.14.19 and 1.26.46 screenshots use H_0 = n_x σ_x + n_y σ_y + n_z σ_z (no 1/2). My iters used the no-prefactor convention.

5. **iter_141 chart-A_0 misread**: iter_141 fed measured Bloch r_z into A_0, but the atlas specifies CHART-η on the torus latitude. iter_142 corrected this within the sidequest encoding and matched atlas L482 8/8; formal Axis0 closure remains open.

6. **Atlas A_5 "active" label vs found derivation**: Atlas L180 calls A_5 "active" (primitive); iter_144's exhaustive sweep found A_5 = A_2·A_3·A_4 holding 16/16. The screenshot terrain tables imply this derivation through the WIN/LOSE/win/lose × ↑/↓ × Type structure but do not state it as a relation. iter_145 documents this as a new finding.

---

## Empty / unreadable files

None on the file-system level. All 25 PNGs are valid per `file`. Six required Read-tool retries before returning content: `0. - (o, tio,).png`, `Can it operate directly on leftjright Weyt spinors.png`, `NeTX.png`, `Topology.png`, `Screenshot 2026-03-28 at 1.27.50 PM.png`, `Screenshot 2026-03-28 at 2.14.37 PM.png`. After retry, all six returned content; logged in §1, §3, §7, §13, §16, §24.

---

## Cross-reference: iter → screenshots consumed

| Iter | Screenshots consumed |
|---|---|
| iter_141 | (none — pre-screenshot pass; used master atlas L1-758) |
| iter_142 | (none directly; resolved iter_141's A_0 misread via atlas L221-233 + L671 reread) |
| iter_143 | (none; atlas L405 + L692-703 only) |
| iter_144 | (none; iter_143 table only) |
| iter_145 | (none; iter_144 sweep only) |
| iter_146 | (none; iter_143 table only) |
| iter_147 | §6 Minor Inner casing, §7 NeTX, §8 Outer Malor, §9 Pasted Graphic 1, §22 Terrain, §23 actual candidate math |
| iter_148 | §1 Inward/Outward terrains, §2 Hopf carrier, §3 axis roles, §4 common operators, §10–§20 formal spec screenshots, §21 Sim shape, §25 Yin-yang topology |
