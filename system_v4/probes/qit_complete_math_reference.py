# QIT COMPLETE MATH REFERENCE
# ===========================
# All math must satisfy TWO constraints:
#   F01_FINITUDE:      dim(H) < ∞, discrete spectra
#   N01_NONCOMMUTATION: [A, ρ] ≠ 0 in general
#
# NO classical math. Everything is QIT (quantum information theory).
# Jungian labels are METAPHOR LABELS for real math, not definitions.
#
# Source: axes math. apple notes dump.txt (17,701 lines)
# Geometry: hopf_manifold.py, geometric_operators.py, engine_core.py
# Grounding: antigravity/brain HONEST_MATH_AUDIT.md

"""
╔══════════════════════════════════════════════════════════════════╗
║              QIT COMPLETE MATH REFERENCE v1                     ║
║              All Axes · All Geometry · All Operators             ║
║              Consistent with F01 + N01 only                      ║
╚══════════════════════════════════════════════════════════════════╝
"""

# ═══════════════════════════════════════════════════════════════════
# PART 0: BASE CONSTRAINTS (everything derives from these)
# ═══════════════════════════════════════════════════════════════════
#
# F01_FINITUDE
# ────────────
#   H ≅ ℂ^d,   d < ∞   (finite-dimensional Hilbert space)
#   Spectra are discrete: {λ₁, ..., λ_d}
#   No continuous Fourier duals
#   No infinite series
#   Consequences:
#     - All operators are bounded
#     - All channels are CPTP or unitary
#     - All states are density matrices
#     - All entropies are bounded: 0 ≤ S(ρ) ≤ log₂(d)
#
# N01_NONCOMMUTATION
# ──────────────────
#   ∃ A, ρ such that Aρ ≠ ρA
#   Consequences:
#     - Measurement back-action exists
#     - Operator ordering matters
#     - Left/right algebraic actions are distinct
#     - Uncertainty relations exist
#     - Berry phase is nontrivial
#
# Together, F01 + N01 force:
#   - Finite quantum mechanics (not classical probability)
#   - Non-commutative operator algebra on finite spaces
#   - All axes, geometry, and dynamics below

# ═══════════════════════════════════════════════════════════════════
# PART 1: STATE SPACE (density matrices)
# ═══════════════════════════════════════════════════════════════════
#
# DENSITY MATRIX ρ
# ────────────────
#   ρ ∈ D(H) = { ρ ∈ B(H) : ρ ≥ 0, Tr(ρ) = 1, ρ = ρ† }
#
#   For d=2 (minimal nontrivial case):
#     ρ = ½(I + r⃗ · σ⃗)
#     where r⃗ = (r_x, r_y, r_z) ∈ ℝ³, |r⃗| ≤ 1
#     σ⃗ = (σ_x, σ_y, σ_z) Pauli matrices
#
#   Pure states:  |r⃗| = 1   (surface of Bloch ball = S²)
#   Mixed states: |r⃗| < 1   (interior of Bloch ball)
#   Maximally mixed: r⃗ = 0   (I/2)
#
# BLOCH BALL ↔ S² ↔ S³ CONNECTION
# ────────────────────────────────
#   S² = { p ∈ ℝ³ : |p| = 1 }     ← pure states on Bloch sphere
#   S³ = { q ∈ ℝ⁴ : |q| = 1 }     ← unit quaternions = SU(2)
#   Hopf map π: S³ → S²             ← projects spinor → pure state direction
#
#   Pure density matrix from spinor:
#     |ψ⟩ = (z₁, z₂)ᵀ ∈ ℂ² with |z₁|² + |z₂|² = 1
#     ρ = |ψ⟩⟨ψ|
#
#   Bloch vector from ρ:
#     r⃗ = (Tr(ρσ_x), Tr(ρσ_y), Tr(ρσ_z))
#
# VON NEUMANN ENTROPY
# ───────────────────
#   S(ρ) = −Tr(ρ log₂ ρ)
#   For d=2:  S(ρ) = h(½(1 + |r⃗|))  where h is binary entropy
#   Pure: S = 0.  Maximally mixed: S = 1 bit.
#
# NEGENTROPY (used in engine)
# ──────────────────────────
#   Φ(ρ) = log₂(d) − S(ρ)
#   Measures distance from maximally mixed state
#   Φ = 0 at max entropy, Φ = log₂(d) for pure states

# ═══════════════════════════════════════════════════════════════════
# PART 2: GEOMETRY (S³, Hopf, nested tori, Clifford, Weyl)
# ═══════════════════════════════════════════════════════════════════
#
# S³ HOPF FIBRATION
# ─────────────────
#   π: S³ → S²
#   π(z₁, z₂) = (2Re(z̄₁z₂), 2Im(z̄₁z₂), |z₁|² − |z₂|²)
#
#   Fiber: π⁻¹(p) ≅ S¹ for each p ∈ S²
#   Total space: S³ (3-sphere)
#   Base: S² (Bloch sphere of pure states)
#   Fiber: S¹ (global phase of spinor)
#
#   This is the ONLY nontrivial principal U(1) bundle over S².
#
# U(1) FIBER ACTION
# ─────────────────
#   q → e^{iθ} · q
#   In components: (z₁, z₂) → (e^{iθ}z₁, e^{iθ}z₂)
#   Preserves base point: π(e^{iθ}q) = π(q)
#   This is the "vertical" direction on S³
#
# TORUS DECOMPOSITION OF S³
# ─────────────────────────
#   q = (cos(η)·e^{iθ₁}, sin(η)·e^{iθ₂})
#   η ∈ [0, π/2],  θ₁, θ₂ ∈ [0, 2π)
#
#   Each fixed η gives a flat torus T²(η)
#   S³ is foliated by this family of tori
#
#   Special values:
#     η = 0:     degenerate circle (z₂ = 0)
#     η = π/8:   INNER torus (small, tight)
#     η = π/4:   CLIFFORD torus (maximal flat, symmetric)
#     η = 3π/8:  OUTER torus (large)
#     η = π/2:   degenerate circle (z₁ = 0)
#
#   Torus radii:
#     R_major(η) = cos(η)   (radius of z₁ circle)
#     R_minor(η) = sin(η)   (radius of z₂ circle)
#     At Clifford: R_major = R_minor = 1/√2
#
# NESTED HOPF TORI (3 levels in engine)
# ─────────────────────────────────────
#   INNER:    η = π/8   → R_major ≈ 0.924, R_minor ≈ 0.383
#   CLIFFORD: η = π/4   → R_major = R_minor ≈ 0.707
#   OUTER:    η = 3π/8  → R_major ≈ 0.383, R_minor ≈ 0.924
#
#   Inter-torus transport:
#     Preserves angles (θ₁, θ₂), changes η
#     Smooth deformation, not a jump
#     Partial transport: S³ interpolation with renormalization
#
# CLIFFORD TORUS
# ──────────────
#   The unique flat, minimal torus in S³
#   Divides S³ into two congruent solid tori
#   η = π/4: maximal symmetry between the two S¹ circles
#   This is the "equator" of the torus foliation
#
# LEFT WEYL SPINOR ψ_L
# ────────────────────
#   ψ_L = (z₁, z₂)ᵀ ∈ ℂ²
#   Fundamental SU(2) representation
#   Under SU(2) rotation U:     ψ_L → U · ψ_L
#   Under fiber action e^{iθ}: ψ_L → e^{+iθ} ψ_L  (positive phase)
#   Density: ρ_L = |ψ_L⟩⟨ψ_L|
#   Metaphor label: INWARD FLUX (source: ORT_0_3_FIX_NOTES.md:23)
#
# RIGHT WEYL SPINOR ψ_R
# ─────────────────────
#   ψ_R = (z̄₂, −z̄₁)ᵀ ∈ ℂ²
#   Conjugate SU(2) representation: ψ_R = iσ₂ · ψ_L*
#   Under SU(2) rotation U:     ψ_R → U* · ψ_R  (conjugate)
#   Under fiber action e^{iθ}: ψ_R → e^{−iθ} ψ_R  (negative phase)
#   Density: ρ_R = |ψ_R⟩⟨ψ_R|
#   Metaphor label: OUTWARD FLUX
#
# BERRY PHASE
# ──────────
#   For a closed loop γ on S³:
#     φ_Berry = arg(∏_i ⟨ψ_i|ψ_{i+1}⟩)   (Pancharatnam connection)
#   For a closed loop on S² enclosing solid angle Ω:
#     φ_Berry = −Ω/2
#   This is a REAL geometric invariant (not a label).
#   Exists because of the nontrivial U(1) bundle structure.

# ═══════════════════════════════════════════════════════════════════
# PART 3: AXES 0–6 (complete math)
# ═══════════════════════════════════════════════════════════════════
#
# ┌────────────────────────────────────────────────────────────────┐
# │  AXIS 0 — ENTROPIC GRADIENT / COARSE-GRAINING                 │
# │  Source: engine_core.py, rosetta:6                             │
# │  Required axiom: F01                                           │
# └────────────────────────────────────────────────────────────────┘
#
#  MATH:
#    Coarse-graining over Hopf fibers:
#      ρ_coarse(q, n) = (1/n) Σᵢ ρ(fiber_action(q, 2πi/n))
#
#    n = 1: pure state (no coarse-graining)
#    n → ∞: maximally fiber-averaged (most mixed fiber contribution)
#
#    GA0 level ∈ [0, 1] controls n:
#      GA0 = 0: n = 1 (pure)
#      GA0 = 1: n = n_max (coarse-grained)
#
#  GEOMETRIC MEANING:
#    Axis 0 averages over the U(1) fiber of the Hopf bundle
#    This is real coarse-graining: destroys phase coherence along the fiber
#    Produces mixed states from pure states
#
#  ALT FORMULATIONS TO TEST:
#    (A) Fiber average as above (current implementation)
#    (B) Partial trace over environment system (standard QIT decoherence)
#    (C) Twirling channel: ρ → ∫ U(θ)ρU†(θ) dθ/2π
#    (D) Amplitude-dependent: GA0 = f(|r⃗|)
#
#  WHAT AXIS 0 IS NOT:
#    - Not an engine parameter
#    - Not a strategy
#    - It evaluates, it does not drive dynamics
#
# ┌────────────────────────────────────────────────────────────────┐
# │  AXIS 1 — COUPLING / BATH LEGALITY                            │
# │  Source: dump.txt:5763–5805                                    │
# │  Required axiom: F01                                           │
# └────────────────────────────────────────────────────────────────┘
#
#  MATH:
#    Axis 1 selects which CLASS of quantum channels is admissible.
#
#    ISOTHERMAL (metaphor: Se/Si terrains):
#      ρ → E(ρ),   E is general CPTP (Lindblad allowed)
#      Open system, heat exchange permitted
#      Entropy can increase or decrease
#
#    ADIABATIC (metaphor: Ne/Ni terrains):
#      ρ → UρU†,   U ∈ SU(d)
#      Closed system, no heat exchange
#      Entropy exactly conserved
#
#  GEOMETRIC MEANING:
#    Isothermal: trajectories cut across Berry-curvature flux
#    Adiabatic: trajectories slide along Berry-curvature fibers
#    Same chirality (Axis 3), different admissible motion
#
#  ALT FORMULATIONS TO TEST:
#    (A) Binary: CPTP vs unitary (source canon)
#    (B) Continuous: interpolation parameter γ ∈ [0,1]
#        ρ → (1−γ)UρU† + γ·E_Lindblad(ρ)
#    (C) Temperature-like: β parameter controlling Lindblad rates
#
# ┌────────────────────────────────────────────────────────────────┐
# │  AXIS 2 — REPRESENTATION / BOUNDARY                           │
# │  Source: dump.txt:5807–5863                                    │
# │  Required axiom: F01                                           │
# └────────────────────────────────────────────────────────────────┘
#
#  MATH:
#    Axis 2 selects the coordinate frame on the density matrix evolution.
#
#    EULERIAN / OPEN (metaphor: Se/Ne, "e" suffix):
#      Field-based density evolution:
#        ∂_t ρ(x,t) = L[ρ]
#      Boundary allows probability current:
#        ∮_∂V J · dS ≠ 0
#      Tracks flux THROUGH boundaries
#
#    LAGRANGIAN / CLOSED (metaphor: Si/Ni, "i" suffix):
#      Trajectory-based state tracking:
#        ρ(t) = U(t)ρ(0)U†(t)    or path-dependent channel composition
#      Boundary is conserved:
#        ∮_∂V J · dS = 0
#      Tracks state ALONG paths
#
#  GEOMETRIC MEANING:
#    Eulerian: flow ACROSS Hopf fibers
#    Lagrangian: motion ALONG Hopf fibers
#    Same chirality (Axis 3), different tracking frame
#
#  ALT FORMULATIONS TO TEST:
#    (A) Binary: open vs closed boundary (source canon)
#    (B) Leaky boundary: ε parameter, ∮ J·dS = ε·J_max
#    (C) Trace-preserving vs trace-decreasing channels
#
# ┌────────────────────────────────────────────────────────────────┐
# │  AXES 1×2 — THE 4 BASE TOPOLOGIES                             │
# │  Source: dump.txt:5865–5940, 3252–3270                         │
# └────────────────────────────────────────────────────────────────┘
#
#  AXIS 1 × AXIS 2 gives 4 real, inequivalent QIT evolution classes:
#
#  ┌────────────┬──────────────────────┬──────────────────────┐
#  │            │ Axis 2: Eulerian     │ Axis 2: Lagrangian   │
#  ├────────────┼──────────────────────┼──────────────────────┤
#  │ Axis 1:    │ Se (metaphor)        │ Si (metaphor)        │
#  │ Isothermal │ ∂_t ρ = −i[H,ρ]     │ ρ(t) = Σᵢ pᵢ(t)    │
#  │ (CPTP)     │   + Σ γ_k(LρL†−½{}) │   |ψᵢ(t)⟩⟨ψᵢ(t)|   │
#  │            │ Open Lindblad field  │ Thermalized path     │
#  ├────────────┼──────────────────────┼──────────────────────┤
#  │ Axis 1:    │ Ne (metaphor)        │ Ni (metaphor)        │
#  │ Adiabatic  │ ∂_t ρ = −i[H,ρ]     │ ρ(t) = Uρ(0)U†      │
#  │ (Unitary)  │ open boundary        │ closed unitary orbit │
#  │            │ Unitary field flow   │ Pure holonomy loop   │
#  └────────────┴──────────────────────┴──────────────────────┘
#
#  Density matrix forms (d=2, from dump.txt:3256–3270):
#    Se: ρ = [[0, c], [c, 0]]       (off-diagonal only, open CPTP)
#    Si: ρ = [[a, 0], [0, b]]       (diagonal, closed thermalized)
#    Ne: ρ = [[a, b], [b, a]]       (symmetric, open unitary)
#    Ni: ρ = [[d, 0], [0, -d]]      (antisymmetric diagonal, closed unitary)
#
#  These are forced by F01 + N01. No other 2×2 forms satisfy all constraints.
#
# ┌────────────────────────────────────────────────────────────────┐
# │  AXIS 3 — CHIRAL FLUX ORIENTATION                             │
# │  Source: dump.txt:13080–13237, 14196–14338                     │
# │  Required axioms: F01 + N01 (both)                             │
# └────────────────────────────────────────────────────────────────┘
#
#  DEFINITION:
#    Axis 3 selects the sign of the generator acting on density-matrix
#    flow within the same topology.
#
#  MATH:
#    ρ̇ = ±G(ρ)
#    where G is a fixed generator (Hamiltonian, Lindblad, or composed)
#    ± is ORIENTATION of circulation in state space, NOT time reversal
#
#    Type-1 (Left Weyl / Inward Flux):    ρ̇ = +G(ρ)
#    Type-2 (Right Weyl / Outward Flux):  ρ̇ = −G(ρ)
#
#  WEYL SPINOR GROUNDING:
#    Dirac: Ψ = (ψ_L, ψ_R)ᵀ
#    G_L = +σ^μ ∂_μ   (left Weyl)
#    G_R = −σ̄^μ ∂_μ   (right Weyl)
#
#  HOPF FIBER ORIENTATION:
#    Type-1: clockwise Hopf fiber
#    Type-2: counter-clockwise Hopf fiber
#    Same base S², same topology, opposite circulation
#
#  8 TERRAINS = 4 topologies × 2 orientations:
#    Type-1: Se-in, Si-in, Ne-in, Ni-in  (inward flux)
#    Type-2: Se-out, Si-out, Ne-out, Ni-out (outward flux)
#
#  IMPEDANCE (dump.txt:13166–13180, 14283–14338):
#    Z ∝ ||dρ/dt||⁻¹
#    Outer loop: LOW impedance (large radius, lower curvature)
#    Inner loop: HIGH impedance (tight confinement)
#    *** SAME for both Type-1 and Type-2 ***
#    *** Does NOT flip by chirality (dump.txt:14309) ***
#
#  LOOP ASSIGNMENT (dump.txt:11054–11073):
#    Engine A = FeTi (metaphor: deductive, constraint-first)
#    Engine B = TeFi (metaphor: inductive, release-first)
#    Type-1: A outer, B inner
#    Type-2: B outer, A inner
#
#  WHAT AXIS 3 IS NOT:
#    NOT induction/deduction, NOT operator order, NOT entropy sign,
#    NOT time direction, NOT loop order, NOT Axis 6, NOT strategy
#
#  ALT FORMULATIONS TO TEST:
#    (A) ±G sign flip on unified generator (source canon)
#    (B) Conjugate representation: U vs U* (current engine_core.py approach)
#    (C) Hopf fiber orientation via Berry phase sign
#    (D) σ^μ vs σ̄^μ Weyl generator structure
#
# ┌────────────────────────────────────────────────────────────────┐
# │  AXIS 4 — VARIANCE DIRECTION / MATH CLASS                     │
# │  Source: dump.txt:11020–11073, 5999–6086                       │
# │  Required axiom: N01                                           │
# └────────────────────────────────────────────────────────────────┘
#
#  DEFINITION:
#    Axis 4 selects the ORDER of channel composition,
#    producing different variance trajectories.
#
#  MATH:
#    Let A, B be admissible maps from Axis 1.
#
#    DEDUCTIVE (metaphor label):
#      ρ_{n+1} = B ∘ A(ρ_n)    — constraint FIRST
#      V(T_i(ρ)) ↓ early       — variance reduced before traversal
#      Low-impedance outer loop
#
#    INDUCTIVE (metaphor label):
#      ρ_{n+1} = A ∘ B(ρ_n)    — release FIRST
#      V(T_e(ρ)) ↑ early       — variance expands before pruning
#      High-impedance inner loop
#
#  FOUR QUADRANTS (from axis3_orthogonality_sim.py):
#    Type 1 Deductive: C_Ti then C_Fe  (FeTi terrain, constraint first)
#    Type 1 Inductive: C_Fe then C_Ti  (FeTi terrain, release first)
#    Type 2 Deductive: C_Fi then C_Te  (TeFi terrain, constraint first)
#    Type 2 Inductive: C_Te then C_Fi  (TeFi terrain, release first)
#
#  ORTHOGONALITY TEST:
#    ΔAx3 = 0.5 * ((E_1D − E_2D) + (E_1I − E_2I))
#    ΔAx4 = 0.5 * ((E_1D − E_1I) + (E_2D − E_2I))
#    overlap = |Tr(ΔAx3† ΔAx4)| / (||ΔAx3|| · ||ΔAx4||) ≈ 0
#
#  WHAT AXIS 4 DOES:
#    - Reverses composition order
#    - Changes loop thermodynamic direction
#
#  WHAT AXIS 4 DOES NOT:
#    - Introduce operators
#    - Change Axis 1 admissibility
#    - Change Axis 2 topology
#    - Affect chirality (Axis 3)
#
#  ALT FORMULATIONS TO TEST:
#    (A) Binary composition order (source canon)
#    (B) Continuous interpolation: δ ∈ [0,1]
#        ρ → (1−δ)·(B∘A)(ρ) + δ·(A∘B)(ρ)
#    (C) Variance functional: V(ρ) = Tr(ρ²) or V(ρ) = S(ρ)
#    (D) Measure V before and after each sub-step to verify ↓ vs ↑
#
# ┌────────────────────────────────────────────────────────────────┐
# │  AXIS 5 — GENERATOR ALGEBRA CLASS                             │
# │  Source: dump.txt:12897–12960, 580–750                         │
# │  Required axioms: F01 + N01                                    │
# └────────────────────────────────────────────────────────────────┘
#
#  DEFINITION:
#    Axis 5 separates two inequivalent generator classes for
#    quantum state evolution.
#
#  MATH:
#    FGA — Finite Gradient Algebra (dissipative/variational/Lindblad):
#      ρ̇ = Σ_k (L_k ρ L_k† − ½{L_k†L_k, ρ})     (GKSL generator)
#      Properties:
#        - Non-unitary, irreversible
#        - Entropy: non-conserving (monotone ↑ or ↓)
#        - Norm: contractive (semigroup)
#        - Defines attractors, fixed points
#        - Lives on convex cones
#      Operator metaphor labels: {Ti, Te}
#
#    FSA — Finite Spectral Algebra (coherent/Hamiltonian/unitary):
#      ρ̇ = −i[H, ρ]     (Hamiltonian generator)
#      ρ(t) = U(t)ρ(0)U†(t)
#      Properties:
#        - Unitary, reversible
#        - Entropy: conserved exactly
#        - Norm: preserved (group)
#        - No attractors, group orbits only
#        - Lives on Hopf fibers, representation spaces
#      Operator metaphor labels: {Fi, Fe}
#
#  HARD INVARIANTS:
#    FGA ≠ FSA
#    Semigroup ≠ Group
#    These cannot collapse under finitude
#
#  NOTE ON OPERATOR-ALGEBRA ASSIGNMENT:
#    Source canon says: FGA = {Ti, Te}, FSA = {Fi, Fe}
#    BUT actual math type of operators:
#      Ti = Lüders dephasing → irreversible (FGA ✓)
#      Te = unitary rotation → reversible (math type: FSA)
#      Fe = amplitude damping → irreversible (math type: FGA)
#      Fi = spectral filter → quasi-measurement (ambiguous)
#
#    This tension is REAL and needs to be tested:
#    The assignment may reflect ROLE in the engine, not mathematical type.
#
#  ALT FORMULATIONS TO TEST:
#    (A) Source canon: FGA = {Ti, Te}, FSA = {Fi, Fe}
#    (B) Math-type: FGA = {Ti, Fe}, FSA = {Te, Fi}
#    (C) Role-based: the assignment captures how operators ACT in
#        the engine loop, not their standalone mathematical type
#    (D) Mixed: operators have BOTH algebra components depending on
#        strength parameter γ
#
# ┌────────────────────────────────────────────────────────────────┐
# │  AXIS 6 — ACTION ORIENTATION                                  │
# │  Source: dump.txt:1–340                                        │
# │  Required axiom: N01 (essential)                               │
# └────────────────────────────────────────────────────────────────┘
#
#  DEFINITION:
#    Axis 6 distinguishes how an operator acts on a quantum state:
#    by pre-composition or post-composition, under non-commutation.
#
#  MATH:
#    Let A ∈ B(H), ρ ∈ D(H), [A, ρ] ≠ 0
#
#    LEFT (pre-composition):   ρ → Aρ
#    RIGHT (post-composition): ρ → ρA
#
#    Aρ ≠ ρA whenever [A, ρ] ≠ 0  (this is WHY Axis 6 exists)
#
#  IN GENERATORS:
#    Before symmetrization in Lindblad form, there are two primitives:
#      Lρ  (Left action)
#      ρL  (Right action)
#    Standard QIT hides Axis 6 by collapsing to symmetric forms.
#    This system REFUSES that collapse.
#
#  WHAT AXIS 6 IS NOT:
#    NOT execution order, NOT first/second strategy, NOT priority,
#    NOT temporal before/after, NOT causal direction, NOT control flow
#
#  ALT FORMULATIONS TO TEST:
#    (A) Binary: Aρ vs ρA (source canon)
#    (B) Commutator decomposition:
#        [A,ρ] = Aρ − ρA  (Left − Right)
#        {A,ρ} = Aρ + ρA  (Left + Right)
#    (C) Operator–terrain precedence:
#        UP:   E(ρ) = Π_terrain(O(ρ))   (operator before terrain)
#        DOWN: E(ρ) = O(Π_terrain(ρ))   (terrain before operator)
#    (D) Left/right regular representation on operator algebra

# ═══════════════════════════════════════════════════════════════════
# PART 4: AXIS 5 × AXIS 6 — FOUR PRIMITIVE SUPEROPERATORS
# ═══════════════════════════════════════════════════════════════════
#
#  Source: dump.txt:12928–12941
#  These four are inequivalent under finitude.
#  ALL engines must be built from these.
#  No further primitive generator types exist.
#
#  ┌──────┬───────┬──────────────────┬──────────────────────────────────────┬─────────────┐
#  │ Ax5  │ Ax6   │ Class            │ Equation                             │ Invertible  │
#  ├──────┼───────┼──────────────────┼──────────────────────────────────────┼─────────────┤
#  │ FGA  │ Left  │ Gradient-Left    │ Σ(L ρ L† − ½{L†L, ρ})              │ ❌          │
#  │ FGA  │ Right │ Gradient-Right   │ Σ(ρ L†L − ½{L†L, ρ})               │ ❌          │
#  │ FSA  │ Left  │ Spectral-Left    │ ρ̇ = −iHρ                           │ ✅          │
#  │ FSA  │ Right │ Spectral-Right   │ ρ̇ = +iρH                           │ ✅          │
#  └──────┴───────┴──────────────────┴──────────────────────────────────────┴─────────────┘

# ═══════════════════════════════════════════════════════════════════
# PART 5: OPERATOR ROSETTA (metaphor labels → math candidates)
# ═══════════════════════════════════════════════════════════════════
#
# These are Jungian labels. They are metaphor names for real math
# operations that are NOT fully pinned down. Each has multiple
# candidate implementations that need to be tested in sims.
#
# Ti — "Thinking Introverted" / "Quantization Projector"
# ──────────────────────────────────────────────────────
#   Math candidates:
#     (A) Lüders dephasing:  ρ → Σ_k P_k ρ P_k   (current impl)
#     (B) Pinching channel:  ρ → Σ_k |k⟩⟨k|ρ|k⟩⟨k|
#     (C) Conditional expectation onto subalgebra
#     (D) Partial measurement (weak measurement limit)
#   Source canon: FGA algebra
#   Polarity: absorptive (−)
#   Effect: constraint, carving, variance reduction
#
# Fe — "Feeling Extroverted" / "Laplacian Diffuse"
# ────────────────────────────────────────────────
#   Math candidates:
#     (A) Amplitude damping: K₀=diag(1,√(1−γ)), K₁=[[0,√γ],[0,0]] (current)
#     (B) Depolarizing channel: ρ → (1−p)ρ + p·I/d
#     (C) Random unitary channel: ρ → Σ_k p_k U_k ρ U_k†
#     (D) Heat bath Lindbladian with directed jump operators
#   Source canon: FSA algebra (but math type is FGA — tension!)
#   Polarity: emissive (+)
#   Effect: coupling, diffusion, entropy broadcast
#
# Te — "Thinking Extroverted" / "Gradient Push"
# ─────────────────────────────────────────────
#   Math candidates:
#     (A) Unitary rotation: ρ → exp(−iHdt) ρ exp(+iHdt) (current)
#     (B) Gradient flow on Bloch sphere: ρ̇ = −∇F(ρ)
#     (C) Hamiltonian kick with angle from geometry
#     (D) Phase-dependent rotation: U(θ₁ − θ₂)
#   Source canon: FGA algebra (but math type is FSA — tension!)
#   Polarity: emissive (+)
#   Effect: optimization, push, directed transport
#
# Fi — "Feeling Introverted" / "Fourier Filter"
# ─────────────────────────────────────────────
#   Math candidates:
#     (A) Spectral filter: ρ → FρF†/Tr(FρF†), F=diag(1,r) (current)
#     (B) Amplitude amplification: selective basis amplification
#     (C) Matched filter: correlate with template state
#     (D) Eigenvalue-dependent scaling
#   Source canon: FSA algebra
#   Polarity: absorptive (−)
#   Effect: filtering, absorption, selective amplification
#
# STAGE / TERRAIN LABELS (Se, Si, Ne, Ni)
# ───────────────────────────────────────
#   These are metaphor labels for the 4 base topologies:
#     Se = Isothermal + Eulerian (open Lindblad)
#     Si = Isothermal + Lagrangian (thermalized path)
#     Ne = Adiabatic + Eulerian (unitary field flow)
#     Ni = Adiabatic + Lagrangian (closed unitary orbit)
#
#   Each stage uses ALL FOUR operators, not just one.
#   "Native operator" is emphasis, not exclusion.
#   All four fire at each stage with same Axis-6 orientation.

# ═══════════════════════════════════════════════════════════════════
# PART 6: ENGINE STRUCTURE (how it all composes)
# ═══════════════════════════════════════════════════════════════════
#
# ENGINE STATE
# ────────────
#   state = (ρ_L, ρ_R, η, θ₁, θ₂, GA0)
#   where:
#     ρ_L: left Weyl density matrix (2×2)
#     ρ_R: right Weyl density matrix (2×2)
#     η: torus latitude ∈ [0, π/2]
#     θ₁, θ₂: torus angles ∈ [0, 2π)
#     GA0: coarse-graining level ∈ [0, 1]
#
# ONE MACRO-STAGE (from dump.txt:6150–6170)
# ──────────────────────────────────────────
#   E_stage = E_Fe ∘ E_Fi ∘ E_Te ∘ E_Ti
#   with same Axis-6 orientation applied to every E_O
#   All 4 operators present, none excluded
#
# ONE ENGINE CYCLE (8 stages)
# ──────────────────────────
#   Type-1 outer (deductive): Se-in → Si-in → Ne-in → Ni-in
#   Type-1 inner (inductive): Ni-in → Ne-in → Si-in → Se-in
#   (Type-2: swap FeTi/TeFi dominance, reverse flux orientation)
#
# MEASURABLE QUANTITIES AFTER EACH STEP
# ─────────────────────────────────────
#   S(ρ_L), S(ρ_R)              von Neumann entropy
#   Φ(ρ) = 1 − S(ρ)             negentropy
#   ||dρ/dt|| = ||ρ_new − ρ_old|| Frobenius norm of change
#   Z = 1/||dρ/dt||             impedance
#   V(ρ) = Tr(ρ²)               purity (variance proxy)
#   d_trace(ρ_L, ρ_R)           trace distance L↔R
#   Berry phase along loop       geometric phase

# ═══════════════════════════════════════════════════════════════════
# PART 7: WHAT NEEDS TO BE TESTED IN SIMS
# ═══════════════════════════════════════════════════════════════════
#
# SIM 1: ±G TYPE SPLIT
#   Build ONE generator G from operator composition
#   Run Type-1 with +G, Type-2 with −G
#   Measure: do they converge to different attractors?
#   Compare: current ad-hoc conjugation vs true ±G
#
# SIM 2: IMPEDANCE Z
#   Compute Z = ||dρ/dt||⁻¹ at every step
#   Verify: outer loop Z < inner loop Z (for both types)
#   Test: does Z flip by chirality? (source says NO)
#
# SIM 3: FGA vs FSA OPERATOR ASSIGNMENT
#   Test (A): source canon FGA={Ti,Te}, FSA={Fi,Fe}
#   Test (B): math-type FGA={Ti,Fe}, FSA={Te,Fi}
#   Measure: orthogonality, convergence, entropy trajectories
#   Which assignment produces cleaner axis separation?
#
# SIM 4: AXIS 6 LEFT/RIGHT ACTION
#   For each operator O and state ρ:
#     Compare: O(ρ) as Lüders/Lindblad/unitary
#     vs: Oρ (left multiply), ρO (right multiply)
#   Measure: does the non-symmetric part create meaningful dynamics?
#
# SIM 5: 4 TOPOLOGY DENSITY FORMS
#   Verify that Se, Si, Ne, Ni produce the canonical d=2 density forms
#   Check that Axis 3 orientation does not change the topology class
#   Measure: do the 4 topologies remain stable under admissible operators?
#
# SIM 6: VARIANCE DIRECTION (AXIS 4)
#   Compute V(ρ) = Tr(ρ²) before and after each sub-step
#   Deductive: V should decrease early
#   Inductive: V should increase early
#   Test with all 4 quadrants (Type1×Ded, Type1×Ind, Type2×Ded, Type2×Ind)
#
# SIM 7: FULL AXIS ORTHOGONALITY MATRIX
#   Compute pairwise overlap for all axis pairs (0-6)
#   Use Hilbert-Schmidt inner product on displacement matrices
#   Should be ≈ 0 for all pairs if axes are truly orthogonal
#
# SIM 8: BERRY PHASE PER ENGINE TYPE
#   Run full engine cycle for Type-1 and Type-2
#   Compute Berry phase accumulated along the loop on S³
#   Type-1 should have opposite sign from Type-2
"""

# This file is documentation, not executable code.
# The math above is the binding spec for all QIT sims.
# All alternative formulations (A/B/C/D) should be tested.
