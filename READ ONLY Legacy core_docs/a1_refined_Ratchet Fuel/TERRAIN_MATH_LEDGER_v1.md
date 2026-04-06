# TERRAIN MATH LEDGER v1

DATE_UTC: 2026-03-28T00:00:00Z
AUTHORITY: CANON (exact math packet; overlay labels in IGT/Jungian columns only)

GLOBAL LOCKS
- Fe/Ti/Te/Fi are OPERATORS. NOT terrains, NOT topologies.
- Terrain name: (topology × engine_type). Loop selects carrier curve only.
  Type-1: Se→Funnel, Ne→Vortex, Ni→Pit, Si→Hill
  Type-2: Se→Cannon, Ne→Spiral, Ni→Source, Si→Citadel
- Stage order within each loop is INDUCTIVE or DEDUCTIVE — not the same for all loops.
  O_ded = (Se, Ne, Ni, Si)   O_ind = (Se, Si, Ni, Ne)
  Type-1 inner = IND,  Type-1 outer = DED
  Type-2 inner = DED,  Type-2 outer = IND
- Axis-3 physical overlays (Weyl/chirality) remain noncanon — see AXIS3_HYPOTHESES.md.

---

## 1. Root Constraints

| Label | Exact statement | Immediate mathematical consequence |
|---|---|---|
| F01_FINITUDE | finite encodings, bounded distinguishability, no completed infinities, decidable admissibility | finite-dimensional Hilbert spaces, finite operator bases, finite Kraus families, finite axis codomains |
| N01_NONCOMMUTATION | order-sensitive composition, no swap-by-default, sequence belongs to the object | [A,B] ≠ 0 in general; Aρ ≠ ρA; Φ_{UEUE} ≠ Φ_{EUEU}; loop holonomy |

Pauli noncommutation (immediate from N01):
[σ_x, σ_y] = 2i σ_z,   [σ_y, σ_z] = 2i σ_x,   [σ_z, σ_x] = 2i σ_y

---

## 2. Constraint Manifold — Thin Canon Form

| Label | Exact math |
|---|---|
| constraint set | C = {F01, N01, admissible probe rules, admissible composition rules} |
| constraint manifold | M(C) = {x : x is admissible under C} |
| geometry | coordinate-free compatibility structure induced by C on M(C) |
| axis slice | A_i : M(C) → V_i,   i ∈ {0,1,2,3,4,5,6} |

### Concrete Geometric Realization

| Label | Exact math |
|---|---|
| Hilbert space | H = C² |
| carrier sheet | S_s³ = {ψ_s ∈ C² : ‖ψ_s‖ = 1},  s ∈ {L,R} |
| paired carrier-density | M̂_geom = ⊔_{s∈{L,R}} Ŝ_s,   Ŝ_s = {(ψ_s,ρ_s) ∈ S_s³ × D(H) : ρ_s = ψ_s ψ_s†} |
| realization map | ι : M̂_geom ↪ M(C) |
| Hopf chart | ψ_s(φ,χ;η) = ( e^{i(φ+χ)} cos η,  e^{i(φ−χ)} sin η ) |
| torus foliation | T_η^s = {ψ_s(φ,χ;η) : φ,χ ∈ [0,2π)} ⊂ S_s³ |
| Hopf projection | π(ψ) = ψ† σ⃗ ψ = (r_x, r_y, r_z) ∈ S² |
| density reduction | ρ_s = ψ_s ψ_s† = ½(I + r⃗_s · σ⃗) |
| fiber blindness | ρ_s(φ+θ, χ; η) = ρ_s(φ, χ; η) |

---

## 3. QIT Objects

### Pauli Basis

| Label | Exact math |
|---|---|
| I | [[1,0],[0,1]] |
| σ_x | [[0,1],[1,0]] |
| σ_y | [[0,−i],[i,0]] |
| σ_z | [[1,0],[0,−1]] |
| σ_- | [[0,0],[1,0]] |
| σ_+ | [[0,1],[0,0]] |

### Hamiltonians and Probes

| Label | Exact math |
|---|---|
| H₀ | n_x σ_x + n_y σ_y + n_z σ_z |
| H_L | +H₀ |
| H_R | −H₀ |
| ṙ_L | +2 n⃗ × r⃗_L |
| ṙ_R | −2 n⃗ × r⃗_R |
| probe | O = O†,   p_O(ρ) = Tr(O ρ) |

### Loop Geometry

| Label | Exact math |
|---|---|
| Hopf connection | A = −i ψ† dψ = dφ + cos(2η) dχ |
| Type-1 inner loop | γ_f^L(u) = ψ_L(φ₀+u, χ₀; η₀) |
| Type-1 outer loop | γ_b^L(u) = ψ_L(φ₀ − cos(2η₀)u, χ₀+u; η₀) |
| Type-2 inner loop | γ_f^R(u) = ψ_R(φ₀+u, χ₀; η₀) |
| Type-2 outer loop | γ_b^R(u) = ψ_R(φ₀ − cos(2η₀)u, χ₀+u; η₀) |
| horizontal condition | A(γ̇_b^s) = 0 |
| inner density path | ρ_f^s(u) = |γ_f^s(u)⟩⟨γ_f^s(u)| = ρ_f^s(0)  [constant — fiber is phase-only] |
| outer density path | ρ_b^s(u) = |γ_b^s(u)⟩⟨γ_b^s(u)| = ½(I + r⃗(χ₀+u, η₀)·σ⃗) |

---

## 4. Terrain Generators

Dissipator: D[L](ρ) = L ρ L† − ½(L†L ρ + ρ L†L)

### Type-1 Generator Set

| Label | Exact math |
|---|---|
| Se / Funnel | X_F^L(ρ) = Σ_k D[L_k^{F,L}](ρ) |
| Ne / Vortex | X_V^L(ρ) = −i [H_L, ρ] |
| Ni / Pit | X_P^L(ρ) = γ_{P,L} D[σ_-](ρ) |
| Si / Hill | X_H^L(ρ) = −i [K_L, ρ],   [K_L, P_j^{H,L}] = 0,   P_j^{H,L} = ½(I + m̂_j^{H,L}·σ⃗) |

### Type-2 Generator Set

| Label | Exact math |
|---|---|
| Se / Cannon | X_C^R(ρ) = Σ_k D[L_k^{C,R}](ρ) |
| Ne / Spiral | X_S^R(ρ) = −i [H_R, ρ] |
| Ni / Source | X_{So}^R(ρ) = γ_{So,R} D[σ_+](ρ) |
| Si / Citadel | X_{Ci}^R(ρ) = −i [K_R, ρ],   [K_R, P_j^{Ci,R}] = 0,   P_j^{Ci,R} = ½(I + m̂_j^{Ci,R}·σ⃗) |

### Stage Channels

Φ_F^L(t) = e^{t X_F^L},  Φ_V^L(t) = e^{t X_V^L},  Φ_P^L(t) = e^{t X_P^L},  Φ_H^L(t) = e^{t X_H^L}
Φ_C^R(t) = e^{t X_C^R},  Φ_S^R(t) = e^{t X_S^R},  Φ_{So}^R(t) = e^{t X_{So}^R},  Φ_{Ci}^R(t) = e^{t X_{Ci}^R}

---

## 5. Axes 0–7

| Axis | Codomain | Exact math | Note |
|---|---|---|---|
| 0 | scalar + two-class | φ₀[h] = (1/T)∫₀ᵀ Σ_{cut} w_cut I_c(cut;ρ_h(t)) dt;  A₀[h] = class(φ₀[h]) | external history functional; not inside-engine |
| 1 | {U, NU} | A₁(X)=U ⟺ X=−i[K,·];  A₁(X)=NU ⟺ X=Σ_k D[L_k](·) | unitary vs proper CPTP/nonunitary |
| 2 | {EXP, COMP} | A₂(Se)=A₂(Ne)=EXP;  A₂(Ni)=A₂(Si)=COMP | topology-sign slice |
| 3 | {Type1, Type2} | A₃(x̂)=Type1 ⟺ x̂∈Ŝ_L;  A₃(x̂)=Type2 ⟺ x̂∈Ŝ_R | canon core = engine-family split |
| 4 | {IND, DED} | A₄(L,f)=IND, A₄(L,b)=DED, A₄(R,f)=DED, A₄(R,b)=IND | loop-order class |
| 5 | {Line, Wave} | A₅(Ti)=A₅(Te)=Line;  A₅(Fi)=A₅(Fe)=Wave | generator/calculus family (from realized Jungian operator) |
| 6 | {UP, DOWN} | UP_A(ρ)=Aρ;  DOWN_A(ρ)=ρA | precedence / sidedness |

---

## 6. Loop Order Definitions

O_ded = (Se, Ne, Ni, Si)
O_ind = (Se, Si, Ni, Ne)

| Loop object | Carrier | Order | A4 |
|---|---|---|---|
| L_{T1,inner} = (γ_f^L, O_ind) | γ_f^L | Se → Si → Ni → Ne | IND |
| L_{T1,outer} = (γ_b^L, O_ded) | γ_b^L | Se → Ne → Ni → Si | DED |
| L_{T2,inner} = (γ_f^R, O_ded) | γ_f^R | Se → Ne → Ni → Si | DED |
| L_{T2,outer} = (γ_b^R, O_ind) | γ_b^R | Se → Si → Ni → Ne | IND |

Channel order by loop:

| Loop label | Exact channel order |
|---|---|
| Type-1 Engine Inductive Inner Loop | (Φ_F^L, Φ_H^L, Φ_P^L, Φ_V^L) |
| Type-1 Engine Deductive Outer Loop | (Φ_F^L, Φ_V^L, Φ_P^L, Φ_H^L) |
| Type-2 Engine Deductive Inner Loop | (Φ_C^R, Φ_S^R, Φ_{So}^R, Φ_{Ci}^R) |
| Type-2 Engine Inductive Outer Loop | (Φ_C^R, Φ_{Ci}^R, Φ_{So}^R, Φ_S^R) |

---

## 7. IGT Token Tables

### Type-1

| IGT label | Outer word | Outer pair | Inner word | Inner pair |
|---|---|---|---|---|
| `WINlose` | `WIN` | NeTi | `lose` | FiNe |
| `winWIN` | `WIN` | FeSi | `win` | SiTe |
| `LOSEwin` | `LOSE` | TiSe | `win` | SeFi |
| `loseLOSE` | `LOSE` | NiFe | `lose` | TeNi |

### Type-2

| IGT label | Outer word | Outer pair | Inner word | Inner pair |
|---|---|---|---|---|
| `winLOSE` | `LOSE` | NeFi | `win` | TiNe |
| `WINwin` | `WIN` | TeSi | `win` | SiFe |
| `loseWIN` | `WIN` | FiSe | `lose` | SeTi |
| `LOSElose` | `LOSE` | NiTe | `lose` | FeNi |

IGT parse: UPPERCASE = outer loop word, lowercase = inner loop word.
Precedence: UP_A(ρ) = Aρ, DOWN_A(ρ) = ρA.

---

## 8. Four Loop Tables with Axis 0–6

### Type-1 Engine Inductive Inner Loop
L_{T1,inner} = (γ_f^L, O_ind)

| Stage | Topology | Terrain | Generator | IGT | Word | Pair | A1 | A2 | A3 | A4 | A5 | A6 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Se | Funnel | X_F^L | `LOSEwin` | win | SeFi | NU | EXP | Type1 | IND | Wave/Fi | DOWN |
| 2 | Si | Hill | X_H^L | `winWIN` | win | SiTe | U | COMP | Type1 | IND | Line/Te | DOWN |
| 3 | Ni | Pit | X_P^L | `loseLOSE` | lose | TeNi | NU | COMP | Type1 | IND | Line/Te | UP |
| 4 | Ne | Vortex | X_V^L | `WINlose` | lose | FiNe | U | EXP | Type1 | IND | Wave/Fi | UP |

### Type-1 Engine Deductive Outer Loop
L_{T1,outer} = (γ_b^L, O_ded)

| Stage | Topology | Terrain | Generator | IGT | Word | Pair | A1 | A2 | A3 | A4 | A5 | A6 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Se | Funnel | X_F^L | `LOSEwin` | LOSE | TiSe | NU | EXP | Type1 | DED | Line/Ti | UP |
| 2 | Ne | Vortex | X_V^L | `WINlose` | WIN | NeTi | U | EXP | Type1 | DED | Line/Ti | DOWN |
| 3 | Ni | Pit | X_P^L | `loseLOSE` | LOSE | NiFe | NU | COMP | Type1 | DED | Wave/Fe | DOWN |
| 4 | Si | Hill | X_H^L | `winWIN` | WIN | FeSi | U | COMP | Type1 | DED | Wave/Fe | UP |

### Type-2 Engine Deductive Inner Loop
L_{T2,inner} = (γ_f^R, O_ded)

| Stage | Topology | Terrain | Generator | IGT | Word | Pair | A1 | A2 | A3 | A4 | A5 | A6 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Se | Cannon | X_C^R | `loseWIN` | lose | SeTi | NU | EXP | Type2 | DED | Line/Ti | DOWN |
| 2 | Ne | Spiral | X_S^R | `winLOSE` | win | TiNe | U | EXP | Type2 | DED | Line/Ti | UP |
| 3 | Ni | Source | X_{So}^R | `LOSElose` | lose | FeNi | NU | COMP | Type2 | DED | Wave/Fe | UP |
| 4 | Si | Citadel | X_{Ci}^R | `WINwin` | win | SiFe | U | COMP | Type2 | DED | Wave/Fe | DOWN |

### Type-2 Engine Inductive Outer Loop
L_{T2,outer} = (γ_b^R, O_ind)

| Stage | Topology | Terrain | Generator | IGT | Word | Pair | A1 | A2 | A3 | A4 | A5 | A6 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Se | Cannon | X_C^R | `loseWIN` | WIN | FiSe | NU | EXP | Type2 | IND | Wave/Fi | UP |
| 2 | Si | Citadel | X_{Ci}^R | `WINwin` | WIN | TeSi | U | COMP | Type2 | IND | Line/Te | UP |
| 3 | Ni | Source | X_{So}^R | `LOSElose` | LOSE | NiTe | NU | COMP | Type2 | IND | Line/Te | DOWN |
| 4 | Ne | Spiral | X_S^R | `winLOSE` | LOSE | NeFi | U | EXP | Type2 | IND | Wave/Fi | DOWN |

---

## 9. 16 Placements in Correct Stage Order

| # | Loop | Stage | Exact placement |
|---|---|---|---|
| 1 | Type-1 Engine Inductive Inner Loop | 1 | (γ_f^L, Φ_F^L) |
| 2 | Type-1 Engine Inductive Inner Loop | 2 | (γ_f^L, Φ_H^L) |
| 3 | Type-1 Engine Inductive Inner Loop | 3 | (γ_f^L, Φ_P^L) |
| 4 | Type-1 Engine Inductive Inner Loop | 4 | (γ_f^L, Φ_V^L) |
| 5 | Type-1 Engine Deductive Outer Loop | 1 | (γ_b^L, Φ_F^L) |
| 6 | Type-1 Engine Deductive Outer Loop | 2 | (γ_b^L, Φ_V^L) |
| 7 | Type-1 Engine Deductive Outer Loop | 3 | (γ_b^L, Φ_P^L) |
| 8 | Type-1 Engine Deductive Outer Loop | 4 | (γ_b^L, Φ_H^L) |
| 9 | Type-2 Engine Deductive Inner Loop | 1 | (γ_f^R, Φ_C^R) |
| 10 | Type-2 Engine Deductive Inner Loop | 2 | (γ_f^R, Φ_S^R) |
| 11 | Type-2 Engine Deductive Inner Loop | 3 | (γ_f^R, Φ_{So}^R) |
| 12 | Type-2 Engine Deductive Inner Loop | 4 | (γ_f^R, Φ_{Ci}^R) |
| 13 | Type-2 Engine Inductive Outer Loop | 1 | (γ_b^R, Φ_C^R) |
| 14 | Type-2 Engine Inductive Outer Loop | 2 | (γ_b^R, Φ_{Ci}^R) |
| 15 | Type-2 Engine Inductive Outer Loop | 3 | (γ_b^R, Φ_{So}^R) |
| 16 | Type-2 Engine Inductive Outer Loop | 4 | (γ_b^R, Φ_S^R) |

---

## 10. Structural Lock

{4 loops} = {γ_f^L, γ_b^L, γ_f^R, γ_b^R}
{8 generators} = {X_F^L, X_V^L, X_P^L, X_H^L, X_C^R, X_S^R, X_{So}^R, X_{Ci}^R}
{16 placements} = {(γ_ℓ^s, Φ_τ^s) : s∈{L,R}, ℓ∈{f,b}, τ∈{Se,Ne,Ni,Si}}

Order lock:
  Type-1 Engine Inductive Inner Loop = Se, Si, Ni, Ne
  Type-1 Engine Deductive Outer Loop = Se, Ne, Ni, Si
  Type-2 Engine Deductive Inner Loop = Se, Ne, Ni, Si
  Type-2 Engine Inductive Outer Loop = Se, Si, Ni, Ne

Root-constraint alignment = finite carrier + noncommuting operator algebra + probe-resolved admissibility
