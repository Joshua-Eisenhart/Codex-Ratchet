# Constraint on Distinguishability: Full Mathematical Treatment

Date: 2026-04-05
Status: Comprehensive math reference. Verified against sim results.
        Integrates: axiom, carrier, geometry, connection, chirality,
        topologies, operators, algebra, composition, entropy, entanglement.

No jargon. Pure mathematical structures and their measured properties.

---

## 0. The Primitive

A finite set S of states, a finite set M of measurements, and the
equivalence relation:

  s₁ ~_M s₂ ⟺ ∀m ∈ M : m(s₁) = m(s₂)

The quotient Q = S/~_M is the ontology at resolution M.

F01: |S| < ∞, |M| < ∞, dim(H) < ∞
N01: For A, B ∈ M: A∘B ≠ B∘A in general. ~_{A∘B} ≠ ~_{B∘A}.

M(C) = {s ∈ S : s satisfies F01, N01, and all derived constraints}

---

## 1. Carrier and State Space

H = C². States: D(C²) = {ρ ∈ B(C²) : ρ ≥ 0, Tr(ρ) = 1}

Bloch decomposition: ρ = ½(I + r_x σ_x + r_y σ_y + r_z σ_z)

Pauli matrices satisfy: σ_i σ_j = δ_{ij} I + i ε_{ijk} σ_k

Bloch vector r⃗ = (r_x, r_y, r_z), |r⃗| ≤ 1.
|r⃗| = 1: pure. |r⃗| < 1: mixed. |r⃗| = 0: maximally mixed I/2.

Trace distance (operational distinguishability):
T(ρ₁, ρ₂) = ½|r⃗₁ - r⃗₂|

Helstrom bound: p_guess = ½(1 + T)

---

## 2. Spinor Carrier and Hopf Structure

Pure states: S³ = {ψ ∈ C² : |ψ| = 1}

Hopf map π: S³ → S²:
  π(z₁, z₂) = (2Re(z₁z₂*), 2Im(z₁z₂*), |z₁|² - |z₂|²)

Fiber π⁻¹(p) = S¹ (global phase). States in the same fiber are
indistinguishable under any density-matrix measurement. The fiber
IS an equivalence class under ~_M where M = {all POVMs}.

Torus foliation of S³:

  T_η = {ψ(φ,χ;η) = (e^{i(φ+χ)}cosη, e^{i(φ-χ)}sinη)ᵀ : φ,χ ∈ [0,2π)}

η ∈ [0, π/2]. Radii: R_major = cosη, R_minor = sinη.

η = 0: degenerates to circle (north pole fiber)
η = π/4: Clifford torus (R_major = R_minor = 1/√2, minimal, flat)
η = π/2: degenerates to circle (south pole fiber)

---

## 3. Connection and Loop Geometry

Hopf connection: 𝒜 = -iψ†dψ = dφ + cos(2η)dχ

Fiber loop (vertical):
  γ_f(u) = ψ(φ₀+u, χ₀; η₀)
  γ̇_f = ∂_φ ψ = i(e^{i(φ+χ)}cosη, e^{i(φ-χ)}sinη)ᵀ
  ρ(γ_f(u)) = ρ(γ_f(0)) ∀u — DENSITY-STATIONARY

Proof: π depends on |z₁|², |z₂|², z₁z₂*. Along fiber loop all three
are constant in u. Zero new distinguishability created.

Base loop (horizontal):
  γ_b(u) = ψ(φ₀ - cos(2η₀)u, χ₀+u; η₀)
  Horizontal condition: 𝒜(γ̇_b) = -cos(2η) + cos(2η) = 0 ✓
  ρ(γ_b(u)) varies with u — DENSITY-TRAVERSING
  The off-diagonal phase rotates with u → new distinguishability.

Berry phase (holonomy):
  γ_Berry = -½Ω(C) where Ω = solid angle on S²

Sim result: Berry phase varies from ±0.92 (inner/outer) to ±π (Clifford).

---

## 4. Weyl Chirality

Two copies of carrier with opposite Hamiltonians:

  H_L = +H₀ = +(n_x σ_x + n_y σ_y + n_z σ_z) (left Weyl)
  H_R = -H₀ (right Weyl)

Joint state: ρ_AB ∈ D(C² ⊗ C²), 4×4 density matrix.
Marginals: ρ_L = Tr_R(ρ_AB), ρ_R = Tr_L(ρ_AB)
Init: ρ_AB = ρ_L ⊗ ρ_R (separable, C = 0)

In Cl(3,0): chirality IS the pseudoscalar e₁₂₃ (squares to -1).
The sign flip is the eigenvalue of e₁₂₃ on each sheet.

---

## 5. Four Perceiving Topologies

The four structurally distinct one-parameter CPTP semigroups on D(C²):

### Se (expansion — σ₊ Lindblad)

  ℒ_Se(ρ) = γ(σ₊ρσ₋ - ½{σ₋σ₊, ρ})
  σ₊ = |1⟩⟨0| = (σ_x + iσ_y)/2
  σ₋ = |0⟩⟨1| = (σ_x - iσ_y)/2

Bloch: ṙ_x = -γr_x/2, ṙ_y = -γr_y/2, ṙ_z = γ(1 - r_z)
Drives r_z → 1. Radial outward. State becomes MORE distinguishable
from maximally mixed. Open boundary.

### Ne (circulation — Hamiltonian commutator)

  ℒ_Ne(ρ) = -i[H₀, ρ], H₀ = ω n⃗·σ⃗
  Bloch: ṙ⃗ = 2ω(n⃗ × r⃗)

Tangential circulation. |r⃗| preserved (unitary). Angular position
changes, distance from center constant. Closed boundary.

### Ni (contraction — σ₋ Lindblad)

  ℒ_Ni(ρ) = γ(σ₋ρσ₊ - ½{σ₊σ₋, ρ})
  Bloch: ṙ_x = -γr_x/2, ṙ_y = -γr_y/2, ṙ_z = -γ(1 + r_z)

Radial inward. State becomes LESS distinguishable from maximally
mixed. Open boundary.

### Si (stratified — commuting Hamiltonian)

  ℒ_Si(ρ) = -i[H_comm, ρ] where [H_comm, {P_i}] = 0

Rotation within invariant subspaces. Populations preserved while
phases evolve. Closed boundary, stratified subspaces.

### Why exactly four

Pauli algebra on C² has 3 generators.
2 channel types: unitary (-i[H,ρ]) and dissipative (LρL† - ½{L†L,ρ}).
2 dissipative families: raising (σ₊ → Se) and lowering (σ₋ → Ni).
2 unitary families: generic rotation (Ne) and commuting/stratified (Si).
Total: 2 + 2 = 4. Forced by su(2) on D(C²).

---

## 6. Four Operators

### Ti (Z-dephasing)

  K₀ = √(1-q)I, K₁ = √q|0⟩⟨0|, K₂ = √q|1⟩⟨1|
  Trace-preserving: K₀†K₀ + K₁†K₁ + K₂†K₂ = I ✓
  ℒ_Ti(ρ) = (κ₁/2)(σ_zρσ_z - ρ)
  Output: [[0, -κ₁(u-iv)], [-κ₁(u+iv), 0]]
  Effect: kills off-diagonal (r_x, r_y → 0), preserves r_z.
  Entanglement: DESTROYS (mean ΔC = -0.011 Type 1)

### Te (X-dephasing)

  K₀ = √(1-q)I, K₁ = √q·½[[1,1],[1,1]], K₂ = √q·½[[1,-1],[-1,1]]
  Trace-preserving: ✓
  ℒ_Te(ρ) = (κ₂/2)(σ_xρσ_x - ρ) = (κ₂/2)[[d-a, 2iv], [-2iv, a-d]]
  Effect: kills X-basis coherence. Populations change (a↔d mix).
  Entanglement: STRONGEST DESTROYER (mean ΔC = -0.018 Type 1)

### Fi (X-rotation, unitary)

  U_x(θ) = e^{-iθσ_x/2} = [[cos(θ/2), -isin(θ/2)], [-isin(θ/2), cos(θ/2)]]
  ℒ_Fi(ρ) = -i[ω₃σ_x/2, ρ] = [[ω₃v, -iω₃(d-a)/2], [iω₃(d-a)/2, -ω₃v]]
  Effect: rotates Bloch around x. Preserves purity.
  Entanglement: ONLY BUILDER (mean ΔC = +0.039 Type 1, +0.024 Type 2)

### Fe (Z-rotation, unitary)

  U_z(φ) = e^{-iφσ_z/2} = [[e^{-iφ/2}, 0], [0, e^{iφ/2}]]
  ℒ_Fe(ρ) = -i[ω₄σ_z/2, ρ] = [[0, -iω₄(u-iv)], [iω₄(u+iv), 0]]
  Effect: rotates Bloch around z. Preserves purity.
  Entanglement: slight destroyer (mean ΔC = -0.007)

### Axis 5 split

F-kernel = {Fe, Fi}: purity-preserving. Fi creates correlations.
T-kernel = {Ti, Te}: entropy-increasing. Both destroy correlations.

Sim: T-kernel alone → C=0, S=0.56-0.59 (entropy without entanglement)
     F-kernel alone → C=0.0002-0.024, S=0.009-0.52 (entanglement without entropy)
     Full engine → C=0.035-0.059, S=0.38-0.41 (both)

F generates correlations (positive feedback on distinguishability).
T structures them (negative feedback). Both needed.

---

## 7. Operator Algebra

Generators σ_x, σ_z produce the full Pauli algebra. Commutation:

  [σ_x, σ_y] = 2iσ_z
  [σ_y, σ_z] = 2iσ_x
  [σ_z, σ_x] = 2iσ_y

Lie algebra: su(2), dimension 3. Verified exactly (sympy).
Jacobi identity: [[A,B],C] + [[B,C],A] + [[C,A],B] = 0 ✓
Casimir: C₂ = σ_x² + σ_y² + σ_z² = 3I (spin-½: j(j+1)=¾ × 4 = 3)

Chiral split adds U(1) from relative L/R phase.
Combined: su(2) × u(1) — electroweak subalgebra of Standard Model.

su(3) (color) would require dim(H) ≥ 3.

---

## 8. Composition and Loop Grammar

Eight terrains = 4 topologies × 2 loops (fiber/base).

Type 1 (H_L = +H₀):
  Outer (base, deductive): Se_b → Ne_b → Ni_b → Si_b
  Inner (fiber, inductive): Se_f → Si_f → Ni_f → Ne_f
  Outer=cooling, inner=heating.

Type 2 (H_R = -H₀):
  Outer (fiber, inductive): Se_f → Si_f → Ni_f → Ne_f
  Inner (base, deductive): Se_b → Ne_b → Ni_b → Si_b
  Outer=heating, inner=cooling.

Type 2 = complete inversion of Type 1 assignments. Same components,
opposite arrangement. Chirality determines arrangement, not content.

Operator-terrain assignment (STAGE_OPERATOR_LUT):
  Type 1 fiber: Se→Fi↓, Ne→Fi↑, Ni→Te↑, Si→Te↓
  Type 1 base:  Se→Ti↑, Ne→Ti↓, Ni→Fe↓, Si→Fe↑
  Type 2 = exact mirror (fiber↔base swapped).

16 placements = 4 topologies × 2 sheets × 2 loops.

---

## 9. N01: Composition Order Is Load-Bearing

Sim results (Type 1, 10 cycles, concurrence):

  Normal order:   C = 0.059
  Swapped (ind↔ded): C = 0.040 (0.67×)
  Reversed:       C = 0.021 (0.35×)
  Random (20 trials): C = 0.013 ± 0.018 (0.22×)

Destroying composition order destroys quantum correlations.
The specific ordering is where Fi's building outruns Te's destruction.

Goldilocks zone for operator strength (piston p):
  p = 0: C = 0 (no operators fire)
  p = 0.825: C = 0.162 (Type 1 optimum)
  p = 0.575: C = 0.039 (Type 2 optimum)
  p = 1.0: C = 0 (dissipative operators overwhelm Fi)

Resonance peak: creation-destruction balance is optimal.

---

## 10. Entropy Structure on M(C)

S(ρ) = -Tr(ρ log₂ ρ)

Across torus foliation (10 cycles):

  Inner  (η=0.39): S(L)=0.054, C=0.044 (Type 1)
  Clifford(η=0.79): S(L)=0.378, C=0.059
  Outer  (η=1.18): S(L)=0.054, C=0.043

Clifford torus = maximum entropy AND maximum entanglement.
Gradient symmetric: ΔS(inner→Cliff) = +0.324, ΔS(Cliff→outer) = -0.324.
Persists over 50+ cycles (slowly decreasing: 0.34 → 0.22).

Entanglement concentration: 5-85× stronger at Clifford than inner/outer.

---

## 11. Bipartite Correlation Measures

  I(A:B) = S(ρ_A) + S(ρ_B) - S(ρ_AB) ≥ 0 (total correlation)
  S(A|B) = S(ρ_AB) - S(ρ_B) (signed conditional entropy)
  I_c(A⟩B) = S(ρ_B) - S(ρ_AB) = -S(A|B) (coherent information)
  C(ρ_AB) via Wootters (concurrence, entanglement measure)

Sim: I_c < 0 everywhere with direct L|R cut.
Bell mixing threshold: p = 0.60 crossing I_c = 0.
Below 0.60 = classical. Above = quantum advantage.

Bridge layer (Ξ) is needed to convert geometric structure into
quantum correlations strong enough for I_c > 0.

---

## 12. Entanglement Dynamics

Type 1 (left, IN): C grows 0.038 → 0.112 over 50 cycles.
  ACCUMULATES inter-subsystem distinguishability.
  Positive feedback on bipartite correlations.

Type 2 (right, OUT): C peaks at 0.035, decays to 0 by 50 cycles.
  DISSIPATES inter-subsystem distinguishability.
  Negative feedback dominates.

Dual-stack (alternating T1+T2): T1 loses C (→0 by cycle 12).
  T2 maintains weak C (~0.027). Asymmetric coupling.

Neg/pos feedback at entanglement level:
  Type 1 = positive feedback (accumulates)
  Type 2 = negative feedback (dissipates)
  Ratchet = the interaction between them.

---

## 13. From Axiom to Everything

  a=a iff a~b (identity requires distinguishability)
  ↓
  Quotient S/~_M (ontology = equivalence classes)
  ↓
  H = C², ρ = ½(I + r⃗·σ⃗) (minimal carrier)
  ↓
  S³ → Hopf → S² with fiber S¹ (geometry of phase equivalence)
  ↓
  T_η foliation (nested tori parameterizing resolution)
  ↓
  𝒜 = dφ + cos(2η)dχ (connection separating fiber from base)
  ↓
  γ_f stationary / γ_b traversing (two loop families)
  ↓
  H_L = +H₀, H_R = -H₀ (Weyl chirality → bipartite space)
  ↓
  Se/Ne/Ni/Si (4 CPTP semigroups, forced by Pauli algebra)
  ↓
  Ti/Te/Fi/Fe (4 operators: 2 dissipative + 2 unitary)
  ↓
  su(2) × u(1) (operator algebra, electroweak)
  ↓
  Loop grammar (composition order determines accumulation)
  ↓
  Entropy peak at Clifford (constraint surface has structure)
  ↓
  Type 1 accumulates / Type 2 dissipates (feedback coupling)
  ↓
  Ratchet = their interaction producing sustained structure

Every layer is a structure in S/~_M under F01 and N01.
The constraint on distinguishability generates them all.

---

## Sources

Engine code: system_v4/probes/engine_core.py
Operators: system_v4/probes/geometric_operators.py
Geometry: system_v4/probes/hopf_manifold.py
Clifford bridge: system_v4/probes/clifford_engine_bridge.py
TopoNetX bridge: system_v4/probes/toponetx_torus_bridge.py
PyG bridge: system_v4/probes/pyg_engine_bridge.py

Sim results (this session):
  gauge_group_correspondence_results.json
  viability_vs_attractor_results.json
  metric_uniqueness_results.json
  feedback_loop_coupling_results.json
  chirality_mirror_symmetry_results.json
  per_stage_entanglement_dynamics_results.json
  ax5_entanglement_split_results.json
  loop_order_sensitivity_results.json
  geometric_ablation_battery_results.json
  strength_resonance_sweep_results.json
  engine_earned_entanglement_results.json
  bridge_family_live_test_results.json
  entanglement_structure_survey_results.json
  full_preaxis_geometry_survey_results.json
  simultaneous_preaxis_surface_probe_results.json
