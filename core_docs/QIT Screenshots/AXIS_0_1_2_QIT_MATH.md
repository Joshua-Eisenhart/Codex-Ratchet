# Axis 0–1–2 QIT Math Packet

**Date:** 2026-03-29
**Epistemic status:** Axis 1 and Axis 2 are source-locked at the semantic class-split level. The reduced Axis 1 × Axis 2 terrain join is source-locked. Axis 0 has a source-backed candidate family, but its exact kernel and exact bridge from geometry to cut state are still open. Any local sign encoding, color/symbol overlay, and the closure `χ₀ = χ₁χ₂` are compiled conventions, not source-locked theorems.
**Status:** Working lock — tightened to the screenshot packet and corrected by multi-lane audit.

---

## Shared Objects

| Object | Pure Math | QIT Label |
|---|---|---|
| state space | D(C²) = {ρ ∈ B(C²) : ρ ≥ 0, Tr ρ = 1} | qubit density states |
| cut-state space | D(H_A ⊗ H_B) | two-part state for correlation functionals |
| topology set | T = {Se, Ne, Ni, Si} | four terrain addresses |
| Pauli triple | σ⃗ = (σ_x, σ_y, σ_z) | algebraic basis for density, Hamiltonians, operators |
| entropy | S(ρ) = -Tr(ρ log ρ) | von Neumann entropy |
| conditional entropy | S(A\|B)_ρ = S(ρ_AB) - S(ρ_B) | bipartite conditional entropy |
| mutual information | I(A:B)_ρ = S(ρ_A) + S(ρ_B) - S(ρ_AB) | total correlation |

---

## Pauli Basis

| Role | Pure Math | Status |
|---|---|---|
| density coordinates | ρ = ½(I + r⃗·σ⃗) | direct |
| Hamiltonian coordinates | H₀ = n_x σ_x + n_y σ_y + n_z σ_z | direct |
| projector/operator coordinates | P_±^Z = ½(I ± σ_z), Q_±^X = ½(I ± σ_x) | direct |
| generator ingredients | σ_±, σ_j | schematic reminder only |

---

## Geometry Spine

### Direct geometry

| Layer | Pure Math | Meaning |
|---|---|---|
| carrier | S³ = {ψ ∈ C² : \|ψ\| = 1} | normalized spinor carrier |
| torus stratum | T_η = {(e^{iα} cos η, e^{iβ} sin η) : α,β ∈ S¹} ⊂ S³ | one nested Hopf torus |
| loop family | γ_fiber, γ_base ⊂ T_η | the two loop families on the Hopf carrier |
| density reduction | ρ(ψ) = \lvert\psi\rangle\langle\psi\rvert = ½(I + r⃗·σ⃗) | Bloch reduction of a spinor |

`inner/outer` is not used as a universal geometry label here. The source-tight carrier geometry is `fiber/base`; any `inner/outer` naming has to be attached later and engine-indexed.

### Compiled working layer on top of the geometry

| Layer | Pure Math | Meaning |
|---|---|---|
| sheet | s ∈ {L, R}, H_s = ±H₀ | compiled left/right sheet variable |
| terrain | X_{τ,s} | local flow law on the chosen sheet |
| operator | J_o | local map family |
| precedence | Ψ↑, Ψ↓ | later composition layer; not part of the direct geometry |

### Weyl-sheet working layer

| Object | Pure Math |
|---|---|
| left spinor | ψ_L ∈ S³ ⊂ C² |
| right spinor | ψ_R ∈ S³ ⊂ C² |
| left density | ρ_L = ψ_L ψ_L† |
| right density | ρ_R = ψ_R ψ_R† |
| left Hamiltonian | H_L = +H₀ |
| right Hamiltonian | H_R = -H₀ |

This Weyl-sheet block is a compiled working layer from screenshot math plus probe support. It is useful, but it is not a source-quoted theorem about live branch semantics.

---

## Required Ax0 Bridge

Axis 0 cannot be evaluated on a single isolated spinor. It needs a cut state.

| Object | Pure Math | Status |
|---|---|---|
| bridge placeholder | Ξ : (geometry sample or history window) → ρ_AB ∈ D(H_A ⊗ H_B) | compiled placeholder for the still-missing bridge |
| Ax0 evaluation | Φ₀(ρ_AB) | source-backed: Ax0 acts on cut/bipartition states |
| open choice | choice of cut `A\|B` and construction of ρ_AB | not locked |

`ρ_LR` is not used here, because current repo usage already gives `ρ_LR` a different meaning as an inter-chirality coherence block.

---

## Axis 0

### Candidate family

| Role | Pure Math | Status |
|---|---|---|
| candidate family | Φ₀(ρ_AB) | source-backed family, not one locked final formula |
| current preferred candidate | Φ₀(ρ_AB) = -S(A\|B)_ρ | strongest current working candidate |
| companion diagnostic | I(A:B)_ρ | source-backed companion quantity |
| saved shell-cut candidate | Φ₀(ρ) = Σ_r w_r I_c(A_r⟩B_r)_ρ | saved shell/cut form, not final closure |
| required input | ρ_AB or a higher-partite reduction | not a single isolated spinor |

### Discrete projection

| Topology | Projection |
|---|---|
| Ne | N / white |
| Ni | N / white |
| Se | S / black |
| Si | S / black |

### What is solid

| Layer | Math | Meaning |
|---|---|---|
| continuous Axis 0 | Φ₀(ρ_AB) after a chosen bridge Ξ | primitive continuous correlation family |
| discrete Axis 0 projection | {Ne, Ni} vs {Se, Si} | N/S or white/black projection |

---

## Axis 1

### Source-locked semantic split

| Class | Pure Math | QIT Label |
|---|---|---|
| unitary branch | Φ(ρ) = UρU† | unitary *-automorphism dynamics |
| proper CPTP branch | Φ(ρ) = Σ_k K_k ρ K_k†, Σ_k K_k†K_k = I | proper CPTP dynamics |
| Markovian working realization | ρ̇ = -i[H,ρ] + Σ_j (L_jρL_j† - ½L_j†L_jρ - ½ρL_j†L_j) | concrete GKLS subclass, not the whole definition |

### Reduced topology projection used by the screenshot packet

| Side | Topologies |
|---|---|
| proper CPTP side | Se, Ni |
| unitary side | Ne, Si |

This is the reduced kernel-regime split used by the screenshot packet. It should not be confused with the richer full terrain-law packet.

---

## Axis 2

### Source-locked semantic split

| Class | Pure Math | QIT Label |
|---|---|---|
| direct representation | ρ̇ = L(ρ) | direct representation |
| unitarily conjugated representation | ρ̃ = V†ρV, K = iV†V̇, ρ̃̇ = V†L(Vρ̃V†)V - i[-K, ρ̃] | conjugated representation |

### Unitary special case

| Class | Pure Math |
|---|---|
| direct unitary form | ρ̇ = -i[H,ρ] |
| conjugated unitary form | H̃ = V†HV, ρ̃̇ = -i[H̃ - K, ρ̃] |

### Label layers

| Layer | Meaning | Status |
|---|---|---|
| kernel | direct vs unitarily conjugated representation | source-locked |
| readable overlay | Eulerian vs Lagrangian | overlay only |
| note overlay | teardrops vs dots | informal note layer only |
| weak metaphor | expansion/compression | do not use as the kernel |

The grouping `Se/Ne` on the direct side and `Ni/Si` on the conjugated side belongs to the reduced `Axis 1 × Axis 2` product surface, not to the primitive Axis 2 kernel by itself.

---

## Axis 1 × Axis 2

### Source-locked reduced terrain join

| Axis 1 class | Axis 2 class | Topology | Reduced product equation |
|---|---|---|---|
| proper CPTP | direct representation | Se | ρ̇ = L(ρ) |
| proper CPTP | unitarily conjugated representation | Ni | ρ̃̇ = V†L(Vρ̃V†)V - i[-K, ρ̃] |
| unitary | direct representation | Ne | ρ̇ = -i[H,ρ] |
| unitary | unitarily conjugated representation | Si | ρ̃̇ = -i[H̃ - K, ρ̃] |

This is the reduced kernel-regime table from the screenshot packet. It is not the full terrain-law table.

---

## Local Sign Encoding

The source packet locks the semantic partitions and the four-way join. It does **not** lock a canonical `±1` polarity. The encoding below is a local bookkeeping convention only.

| Encoding | Definition | Status |
|---|---|---|
| χ₁ | χ₁(Se) = χ₁(Ni) = +1, χ₁(Ne) = χ₁(Si) = -1 | local sign coding of the Axis 1 partition |
| χ₂ | χ₂(Se) = χ₂(Ne) = -1, χ₂(Ni) = χ₂(Si) = +1 | local sign coding of the Axis 2 partition |
| χ₀ | χ₀(Ne) = χ₀(Ni) = +1, χ₀(Se) = χ₀(Si) = -1 | local sign coding of the Axis 0 projection |

### Compatible derived closure inside that sign convention

| Topology | χ₁χ₂ | χ₀ |
|---|---|---|
| Se | (+1)(-1) = -1 | -1 |
| Ne | (-1)(-1) = +1 | +1 |
| Ni | (+1)(+1) = +1 | +1 |
| Si | (-1)(+1) = -1 | -1 |

\[
\chi_0 = \chi_1 \chi_2
\]

This closure is compatible and useful, but it is derived from the local sign convention above. It is not a source-locked theorem.

---

## Informal Symbol Overlay

This table is preserved because it is useful, but it stays at the note/overlay layer.

| Topology | Informal symbol | Status |
|---|---|---|
| Se | black teardrop | note-layer overlay |
| Ne | white teardrop | note-layer overlay |
| Ni | white dot | note-layer overlay |
| Si | black dot | note-layer overlay |

The note source itself says one of the symbol-axis orientations could be inverted, so this overlay is not promoted to kernel status.

---

## Open Points

| Missing | Why it still matters |
|---|---|
| explicit bridge Ξ | Ax0 still needs a concrete map from geometry/history data to a chosen cut state |
| exact cut `A\|B` for Ax0 | needed before the Ax0 kernel can be evaluated concretely |
| explicit V(t) tied to geometry | Ax2 has clean representation math, but not yet a geometry-locked transport law |
| η not assigned to any axis | torus latitude is real geometry with no settled axis role yet |
| full terrain laws vs reduced product equations | the reduced `Ax1 × Ax2` packet is solid, but it is not yet the full terrain law ledger |
| symbol orientation caveat | the note-layer symbol projection is still not fully closed |

### Epistemic status summary

| Item | Status |
|---|---|
| Axis 1 semantic split | source-locked |
| Axis 2 semantic split | source-locked |
| reduced Axis 1 × Axis 2 terrain join | source-locked |
| Axis 0 candidate family | source-backed, not final |
| local sign encoding `χ₀, χ₁, χ₂` | compiled convention |
| `χ₀ = χ₁χ₂` | compatible derived closure |
| symbol/color overlay | note-layer only |
| explicit bridge Ξ | missing |
