# Axis and Entropy Architecture: Reference

Date: 2026-04-05
Status: Extracted verbatim from v5 docs. Not paraphrased.
Source: AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS, Axis 0 rough
        and drifty, Contraint on Admisibility ENTROPY tables,
        ENGINE_64_SCHEDULE_ATLAS

---

## Scope and Boundary

This doc is the reference surface for:
- the axis taxonomy
- the terrain/operator/token schedule layer
- the entropy-layer split
- imported owner-side Axis 0 formalization that still remains open

This doc is not the main surface for:
- live repo truth about which claims are currently earned
- current sim promotion status
- operator derivations in full detail

Read order:
1. `CONSTRAINT_SURFACE_AND_PROCESS.md`
2. `ENGINE_MATH_REFERENCE.md`
3. this file
4. `TIER_STATUS.md` and `LLM_CONTROLLER_CONTRACT.md` for current live-state reporting

Short rule:
- use this doc to understand the axis vocabulary and placement structure
- use `TIER_STATUS.md` to report what is actually open/survived now

## Honesty Boundary

- 7 active axes (0-6). Axes 7-12 are planned later mirror layer.
- Jung, IGT, trigram, hexagram, yin-yang, I-Ching labels are
  CORRELATION LAYERS, not primary mathematics.
- Axis 0 is still open at bridge-and-cut level.

---

## Global Axis Table (7 Axes)

| Axis | Math role | Exact math | Status |
|---|---|---|---|
| 0 | entropy drive, cut-state functional | torus seat + Φ₀(ρ_AB) family | active, open |
| 1 | derived terrain branch split | Se/Ni vs Ne/Si | active, derived |
| 2 | direct vs conjugated frame | ρ̃=ρ vs ρ̃=V†ρV | active |
| 3 | fiber vs lifted-base loop | density-stationary vs density-traversing | active |
| 4 | loop-order family | UEUE vs EUEU | active, derived |
| 5 | operator family | dephasing vs rotation | active |
| 6 | precedence order | operator-first vs terrain-first | active, derived |

### Axis 0: What's Earned vs Open

| Layer | Status |
|---|---|
| earned | geometry seat exists; I_c is strongest simple signed candidate |
| open | final bridge Ξ, final cut A|B, exact shell/hist unification |
| killed | raw local L|R as final doctrine cut; runtime ga0 as doctrine object |

---

## Axis Grounding Status

| Axis | Grounding |
|---|---|
| 0 | chart-level candidate only |
| 1 | source-grounded factor, local binding not closed |
| 2 | source-grounded factor, under reconstruction |
| 3 | UNRESOLVED — chirality/flux vs outer/inner (do not close) |
| 4 | strongest source-grounded operator axis |
| 5 | chart/IGT correlation only |
| 6 | partially source-grounded; chart clearer than source closure |

---

## Eight Terrain Table

| Terrain | Topology | Loop | Path math | Density law | Frame |
|---|---|---|---|---|---|
| Se_f | Se | fiber | γ_fiber | ρ_f(u) = ρ_f(0) | direct |
| Si_f | Si | fiber | γ_fiber | ρ_f(u) = ρ_f(0) | conjugated |
| Ne_f | Ne | fiber | γ_fiber | ρ_f(u) = ρ_f(0) | direct |
| Ni_f | Ni | fiber | γ_fiber | ρ_f(u) = ρ_f(0) | conjugated |
| Se_b | Se | base | γ_base | ρ_b(u) = |γ_b(u)⟩⟨γ_b(u)| | direct |
| Si_b | Si | base | γ_base | ρ_b(u) = |γ_b(u)⟩⟨γ_b(u)| | conjugated |
| Ne_b | Ne | base | γ_base | ρ_b(u) = |γ_b(u)⟩⟨γ_b(u)| | direct |
| Ni_b | Ni | base | γ_base | ρ_b(u) = |γ_b(u)⟩⟨γ_b(u)| | conjugated |

---

## Eight Signed Judging Variants

| Variant | Operator | Order | Tokens |
|---|---|---|---|
| Ti↑ | Z-dephasing | operator first | TiSe, TiNe |
| Ti↓ | Z-dephasing | terrain first | SeTi, NeTi |
| Fe↑ | Z-rotation | operator first | FeSi, FeNi |
| Fe↓ | Z-rotation | terrain first | SiFe, NiFe |
| Te↑ | X-dephasing | operator first | TeNi, TeSi |
| Te↓ | X-dephasing | terrain first | NiTe, SiTe |
| Fi↑ | X-rotation | operator first | FiNe, FiSe |
| Fi↓ | X-rotation | terrain first | NeFi, SeFi |

---

## Token Partition (Axes 3 and 6)

| Loop side | Direction | Type 1 tokens | Type 2 tokens |
|---|---|---|---|
| inner white | up | TeNi, FiNe | TiNe, FeNi |
| inner black | down | SiTe, SeFi | SeTi, SiFe |
| outer white | down | NeTi, NiFe | NiTe, NeFi |
| outer black | up | TiSe, FeSi | TeSi, FiSe |

---

## Loop Order Rules (Axis 4)

| Family | Order | Edge walk |
|---|---|---|
| Inductive | Se → Si → Ni → Ne | Ax0 → Ax2 → Ax0 → Ax2 |
| Deductive | Se → Ne → Ni → Si | Ax2 → Ax0 → Ax2 → Ax0 |

---

## 64-Schedule Grid (8×8)

Rows = terrains, cols = signed operators. 16 starred (*) cells =
chart-locked macro-stages. 48 unstarred = non-locked.

(Full 8×8 grid in ENGINE_64_SCHEDULE_ATLAS.md)

---

## Invariants

| Invariant | Value |
|---|---|
| Terrains per engine | 4 (visited by both loops = 8 terrain-visits) |
| Macro-stages per engine | 8 |
| Microsteps per engine | 32 |
| Total microsteps | 64 |
| WIN/LOSE/win/lose per engine | 2 each |
| Signed operators per engine | 8 |
| Chart-locked macro-stages | 16 |
| Terrain families shared | 4 (Se,Ne,Ni,Si) |
| Chart terrain IDs shared | 0 |

---

## Three-Layer Entropy Architecture

Three separate entropy layers:

| Layer | Object | Role |
|---|---|---|
| Runtime engine | S(ρ_L), S(ρ_R) | per-sheet entropy during operation |
| Torus seat | torus latitude η → entropy of torus embedding | geometry-level entropy |
| Bipartite Ax0 | S(A|B), I(A:B), I_c(A⟩B) on ρ_AB | the actual Axis 0 family |

### Sign Structure

| Quantity | Sign | Role |
|---|---|---|
| S(ρ) | ≥ 0 | unsigned entropy |
| I(A:B) | ≥ 0 | unsigned correlation |
| S(A|B) | can be < 0 | SIGNED cut entropy |
| I_c(A⟩B) | can be < 0 | SIGNED primitive correlation |

---

## Axis 0 Formalization (8 Sections — NOT CANON)

From "Axis 0 rough and drifty." Owner's working formalization.

Use this section as:
- a bounded import of the owner-candidate formalization
- a record of the open shape of Axis 0 reasoning in the v5 source

Do not use this section as:
- proof that Axis 0 is closed
- a substitute for bridge/cut evidence
- the final live status surface

### 1. Primitive Theses

- Entropic monism: reality = constraint on distinguishability
- Identity not primitive: a=a iff a~b
- Time not primitive: time = monotone shell ordering
- Causality not primitive
- Predictive compression deeper than causal story
- Expansion/gravity/entanglement/time/entropy = one family
- Positive and negative entropy modes both exist

### 2. Constraint-First Basis

- Constraint set C = {F01, N01, probe rules, composition rules}
- M(C) = admissible domain
- Axis 0 field type: φ: M(C) → ℝ (scalar on admissible domain)

### 3. Shell/Boundary Bookkeeping

- H_total = H_{I_r} ⊗ H_{B_r} ⊗ H_{O_r}
- Admissible interior: A(r) = {ρ_{I_r B_r} : Tr_{I_r}(ρ) = ρ_{B_r} and constraints hold}
- Shell difference: Δ_r f = f(r+1) - f(r)
- Boundary constrains admissible interior

### 4. j/k Fuzz as Admissible Future

- Ω_r = admissible refinement index set
- N(r) = |Ω_r| (cardinality)
- H_Ω(r) = Shannon entropy on admissible refinements
- ρ_present = C({ρ_ω}_{ω∈Ω_r}) (compression of future possibilities)

### 5. Feynman-Like Path Form

- One-step: Φ(ρ) = Σ_α K_α ρ K_α† (CPTP)
- Multi-step branch: ρ̃_{α₁...αₙ} = K_αₙ...K_α₁ ρ K_α₁†...K_αₙ†
- Branch weight: P(α₁...αₙ) = Tr(ρ̃)
- Path entropy: H_path = -Σ P log P
- Depth parameter n = refinement depth (non-temporal)

### 6. Entanglement Tensor-Network Shell

- Shell-indexed tensor-network family T = {(V_r, E_r, {T_v}, {χ_e})}_r
- Bond dimension χ_e ∈ ℕ (local entanglement capacity)
- Shell contraction Z_r = Contract(T_r)

### 7. Ring Checkerboard as Finite Support

- Finite vertex set V = {v₁,...,vₙ}
- Checkerboard coloring κ: V → {0,1}
- Ring split V = V_inner ⊔ V_outer
- Ordered adjacency E ⊆ V × V (directed)
- Discrete Axis 0 field: φ: V → ℝ
- Directed gradient: Δ_{vi→vj} φ = φ(vj) - φ(vi)

### 8. Entropy Field and i-Scalar

- Shell order parameter: i(r) = G(ρ_{B_r})
- Entropy: S(ρ) = -Tr(ρ log ρ)
- Mutual information across shell: I(I_r:B_r)
- Conditional entropy: S(I_r|B_r)
- Coherent information: I_c(I_r→B_r)
- Shell-weighted field: φ(x) = Σ_r w_r (S(ρ_{B_r}(x)) - S(ρ_{I_r B_r}(x)))
- Path-order parameter: i = H_path

---

## Entropic Monism Doctrine Clarification

Entropic monism = doctrine name
Constraint on distinguishability = actual primitive claim
Entropy = a later admissible measure of distinguishability under constraint

entropic monism ≠ "entropy is primitive"

---

## Source

Extracted verbatim from:
- system_v5/READ ONLY Reference Docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md
- system_v5/READ ONLY Reference Docs/Axis 0 rough and drifty. NOT CANON.md
- system_v5/READ ONLY Reference Docs/Contraint on Admisibility, ENTROPY tables, Entropic Monism.md
- system_v5/READ ONLY Reference Docs/ENGINE_64_SCHEDULE_ATLAS.md
