# QIT ENGINE MATH CONTRACT v1
# ============================
# Source: axes math. apple notes dump.txt (17,701 lines)
# Grounding: antigravity/brain HONEST_MATH_AUDIT.md
# Status: BINDING — engine must implement these or be considered broken
#
# This file is the required math spec. Any engine_core.py that does not
# implement these equations is a dominance table, not a real engine.

"""
ENGINE MATH CONTRACT — Required equations and structures
=========================================================

Every equation below has a source line in the canon dump.
Every equation must be implemented, computed, or measured in the engine.

Source: core_docs/a2_feed_high entropy doc/axes math. apple notes dump.txt
Grounding: antigravity/brain/351be0f2.../HONEST_MATH_AUDIT.md
"""

# ═══════════════════════════════════════════════════════════════════
# AXIS 3 — CHIRAL FLUX ORIENTATION
# Source: dump.txt:13080-13237
# ═══════════════════════════════════════════════════════════════════
#
# MATH:
#   ρ̇ = +G(ρ)     for Type-1 (Left Weyl / Inward Flux)
#   ρ̇ = −G(ρ)     for Type-2 (Right Weyl / Outward Flux)
#
# WHERE:
#   G is a SINGLE unified generator (Hamiltonian + Lindblad composed)
#   ± is orientation of circulation in state space, NOT time reversal
#   Type-1 = clockwise Hopf fiber, Type-2 = counter-clockwise
#
# IMPLEMENTATION REQUIREMENT:
#   The engine MUST have ONE generator G.
#   Type-1 applies +G. Type-2 applies −G.
#   Ad-hoc conjugation (separate L/R operator dispatch) is a hack.
#
# WHAT AXIS 3 IS NOT (dump.txt:13219-13231):
#   NOT induction/deduction, NOT operator order, NOT entropy sign,
#   NOT time direction, NOT loop order.

# ═══════════════════════════════════════════════════════════════════
# IMPEDANCE — Z
# Source: dump.txt:13166-13180, 14283-14338
# ═══════════════════════════════════════════════════════════════════
#
# MATH:
#   Z ∝ ||dρ/dt||⁻¹
#
# INVARIANT (dump.txt:14309):
#   Outer loop = LOW impedance (large radius, lower curvature)
#   Inner loop = HIGH impedance (tight confinement, higher curvature)
#   This is the SAME for both Type-1 and Type-2.
#   It does NOT flip by chirality.
#
# IMPLEMENTATION REQUIREMENT:
#   The engine MUST compute ||dρ/dt|| at each step.
#   Z must be a real computed variable, not a strength hack.

# ═══════════════════════════════════════════════════════════════════
# LOOP ASSIGNMENT
# Source: dump.txt:11054-11073
# ═══════════════════════════════════════════════════════════════════
#
# Engine A = Deductive = FeTi (constraint first, V↓ early)
# Engine B = Inductive = TeFi (release first, V↑ early)
#
# Type-1: A outer, B inner
# Type-2: B outer, A inner
#
# Deductive: V(T_i(ρ)) ↓ early — variance reduced before traversal
# Inductive: V(T_e(ρ)) ↑ early — variance expands before pruning
#
# THESE ARE SEPARATE OBJECTS:
#   - Type (chirality/identity) ≠ A/B (loop role) ≠ Deductive/Inductive (Axis 4)
#   - Type selects WHICH loop role goes to outer vs inner position.

# ═══════════════════════════════════════════════════════════════════
# AXIS 4 — VARIANCE DIRECTION / MATH CLASS
# Source: dump.txt:11020-11036
# ═══════════════════════════════════════════════════════════════════
#
# FOUR QUADRANTS (from axis3_orthogonality_sim.py):
#   Type 1 Deductive: Ti → Fe  (FeTi, constraint first)
#   Type 1 Inductive: Fe → Ti  (FeTi, release first)
#   Type 2 Deductive: Fi → Te  (TeFi, constraint first)
#   Type 2 Inductive: Te → Fi  (TeFi, release first)
#
# ORTHOGONALITY:
#   ΔAx3 = 0.5 * ((E_1D − E_2D) + (E_1I − E_2I))
#   ΔAx4 = 0.5 * ((E_1D − E_1I) + (E_2D − E_2I))
#   overlap = |Tr(ΔAx3† ΔAx4)| / (||ΔAx3|| ||ΔAx4||) ≈ 0

# ═══════════════════════════════════════════════════════════════════
# AXIS 5 — GENERATOR ALGEBRA CLASS
# Source: dump.txt:12897-12960
# ═══════════════════════════════════════════════════════════════════
#
# FGA (Finite Gradient Algebra):
#   Generator: Lindblad/GKSL
#   ρ̇ = Σ_k (L_k ρ L_k† − ½{L_k†L_k, ρ})
#   Entropy: non-conserving (monotone)
#   Geometry: convex cones, attractors
#   Operators: {Ti, Te}
#
# FSA (Finite Spectral Algebra):
#   Generator: Hamiltonian
#   ρ̇ = −i[H, ρ]
#   Entropy: conserved exactly
#   Geometry: group orbits, Hopf fibers
#   Operators: {Fi, Fe}
#
# IMPLEMENTATION REQUIREMENT:
#   Each operator must know its algebra class.
#   FGA operators are irreversible. FSA operators are unitary.

# ═══════════════════════════════════════════════════════════════════
# AXIS 6 — ACTION ORIENTATION
# Source: dump.txt:1-340
# ═══════════════════════════════════════════════════════════════════
#
# Left (pre-composition):  ρ → Aρ
# Right (post-composition): ρ → ρA
#
# These are algebraically distinct whenever [A, ρ] ≠ 0.
#
# WHAT AXIS 6 IS NOT:
#   NOT execution order, NOT temporal, NOT causal, NOT strategy.

# ═══════════════════════════════════════════════════════════════════
# AXIS 5 × AXIS 6 — FOUR PRIMITIVE SUPEROPERATORS
# Source: dump.txt:12928-12941
# ═══════════════════════════════════════════════════════════════════
#
# FGA-Left  (Gradient-Left):    Σ(L ρ L† − ½{L†L, ρ})     irreversible
# FGA-Right (Gradient-Right):   Σ(ρ L†L − ½{L†L, ρ})       irreversible
# FSA-Left  (Spectral-Left):    ρ̇ = −iHρ                    reversible
# FSA-Right (Spectral-Right):   ρ̇ = +iρH                    reversible
#
# These four are inequivalent under finitude.
# All engines must be built from these.
# No further primitive generator types exist.

# ═══════════════════════════════════════════════════════════════════
# FOUR TOPOLOGIES (as density matrix equivalence classes)
# Source: dump.txt:396-498
# ═══════════════════════════════════════════════════════════════════
#
# T₁ (Localized):   ρ ≈ |ψ⟩⟨ψ|, |r| ≈ 1   — projective, low entropy
# T₂ (Distributed): ρ ≈ I/2 + ε, |r| ≪ 1   — mixed, high entropy
# T₃ (Coherent):    strong off-diagonal      — phase transport
# T₄ (Partitioned): p|0⟩⟨0| + (1−p)|1⟩⟨1|   — bistable, classical mixture
#
# 8 terrains = 4 topologies × 2 orientations (Axis 3)

# ═══════════════════════════════════════════════════════════════════
# WHAT IS ALREADY CORRECTLY IMPLEMENTED
# ═══════════════════════════════════════════════════════════════════
#
# ✅ hopf_manifold.py: S³ → S² Hopf fibration, torus decomposition,
#    Berry phase, fiber action — all mathematically correct
#
# ✅ geometric_operators.py: Ti (Lüders), Fe (amplitude damping),
#    Te (unitary rotation), Fi (spectral filter) — all real CPTP/unitary
#
# ✅ engine_core.py: left/right Weyl spinor separation, conjugate
#    dynamics for ψ_R, torus transport on S³, fiber coarse-graining
#
# ✅ axis3_orthogonality_sim.py: 4-quadrant Axis 3 ⊥ Axis 4 test
#    with correct Hilbert-Schmidt inner product

# ═══════════════════════════════════════════════════════════════════
# WHAT IS MISSING (ordered by criticality)
# ═══════════════════════════════════════════════════════════════════
#
# 1. ±G(ρ) as the ACTUAL type differentiator (not ad-hoc conjugation)
# 2. Z = ||dρ/dt||⁻¹ computed at every step
# 3. Operator algebra typing (FGA vs FSA)
# 4. Action orientation (Left vs Right) on each operator
# 5. Variance measurement (V(ρ) before/after each loop)
# 6. Topology awareness (which of T₁–T₄ is current state in)
# 7. Geometry-derived strength (replace 1.0/0.3 and 1.2/0.8 hacks)
