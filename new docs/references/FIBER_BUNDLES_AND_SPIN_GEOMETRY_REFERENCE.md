# Fiber Bundles and Spin Geometry: Formal Reference

Date: 2026-04-05
Status: Reference doc — the actual mathematics, not the system's application

---

## Fiber Bundles

A fiber bundle is (E, B, π, F): total space E, base space B, fiber F,
projection π: E → B. Locally trivial: each point in B has a neighborhood
U with homeomorphism φ: π⁻¹(U) → U × F commuting with projection.

Transition functions t_ij: U_i ∩ U_j → G satisfy the cocycle condition.
Structure group G acts on fiber F.

**Principal bundle:** fiber F = G, group acts freely and transitively on
each fiber. B = P/G.

**Associated bundle:** given principal G-bundle P → B and representation
ρ: G → Aut(V), the associated bundle E = P ×_G V.

---

## Connections on Fiber Bundles

**Vertical subspace:** V_e = ker(dπ_e), tangent to the fiber.

**Ehresmann connection:** smooth choice of horizontal subspace H_e at each
e ∈ E such that T_eE = H_e ⊕ V_e, smooth in e.

**Parallel transport:** given curve γ(t) in B, the horizontal lift γ̃(t)
in E satisfies π(γ̃) = γ and γ̃'(t) ∈ H_{γ̃(t)}.

**Holonomy:** for closed loop γ in B, parallel transport gives a map from
fiber to itself. Set of all such maps = holonomy group Hol(∇).

**Curvature:** R(X,Y) = [X_H, Y_H]_V — vertical component of Lie bracket
of horizontal lifts. Measures failure of H to be integrable.
Bianchi identity: [Φ, R] = 0.

**Principal connection:** G-equivariant Ehresmann connection.
Connection 1-form ω is a g-valued 1-form on P.

---

## The Hopf Fibration

S¹ → S³ → S² with fiber S¹. Simplest nontrivial principal U(1)-bundle.

**Explicit map:** S³ = {(z₀,z₁) ∈ C² : |z₀|² + |z₁|² = 1}

h(z₀, z₁) = (2Re(z₀z₁*), 2Im(z₀z₁*), |z₀|² - |z₁|²)

Equivalently: h(z₀,z₁) = [z₀:z₁] in CP¹. Fiber over each point is
{(e^{iφ}z₀, e^{iφ}z₁)} — a circle.

**Quaternionic:** identify S³ with unit quaternions. h(q) = qkq*.

**Why it matters:** generator of π₃(S²) = Z. Simplest bundle that is not
a product. Topology forces global non-triviality.

**Quantum mechanics:** state space of qubit is S³. Quotienting by global
phase U(1) gives Bloch sphere S². The Hopf map IS this quotient. Fiber
S¹ = unobservable global phase.

**Berry phase:** natural connection on this U(1)-bundle has curvature ∝
area form on S². Holonomy around closed loop on Bloch sphere = Berry
phase: γ = -(1/2)Ω, where Ω = solid angle subtended.

---

## Berry Phase / Geometric Phase (Berry, 1984)

Hamiltonian H(R) depending on parameters R. Eigenstate |n(R)⟩ evolves
adiabatically around closed loop C in parameter space.

**Berry connection:** A_n = i⟨n(R)|∇_R|n(R)⟩

**Berry phase:** γ_n[C] = ∮_C A_n · dR

Gauge-invariant. Depends only on geometry, not speed of traversal.

**Berry curvature:** F_μν = ∂_μA_ν - ∂_νA_μ = -2Im(⟨∂_μn|∂_νn⟩)
By Stokes: γ_n = ∫_S F dS.

**Fiber bundle interpretation (Simon, 1983):** eigenspaces form U(1) line
bundle over parameter space. Berry connection = connection on this bundle.
Berry phase = holonomy. Berry curvature = bundle curvature. Non-trivial
Chern number → no smooth global gauge.

**Wilczek-Zee (1984):** k-fold degenerate → non-abelian su(k)-valued
connection. Holonomy is a unitary matrix, not just a phase.

---

## Spinors and Spin Geometry

**Clifford algebra:** Cl(V,g) = T(V) / {v⊗v + g(v,v)·1}.
Generators satisfy: e_ie_j + e_je_i = -2g(e_i,e_j).

**Spin group:** Spin(n) = double cover of SO(n), subgroup of Cl(n).
Covering map ρ: Spin(n) → SO(n), ker(ρ) = {+1,-1}.

**Spin representations:** for n = 2k, spinor space Δ has dimension 2^k,
decomposes into half-spin (Weyl) representations Δ = Δ₊ ⊕ Δ₋.

**How spinors differ from vectors:** 2π rotation gives factor -1.
Only 4π rotation returns to original. The covering is 2-to-1.

**SU(2) = Spin(3):** double cover of SO(3). Rotation by angle θ about
axis n̂ implemented by U = cos(θ/2)I - i sin(θ/2)(n̂·σ).

**Relation to Hopf:** SU(2) ≅ S³. U(1) acting on SU(2) gives
S³ → S³/U(1) = S², which IS the Hopf fibration.

---

## Weyl Spinors

Dirac spinor decomposes in Weyl basis: ψ = (ψ_L, ψ_R)ᵀ

**Chirality:** γ⁵ = iγ⁰γ¹γ²γ³, (γ⁵)² = I, {γ⁵,γ^μ} = 0.
P_L = (1-γ⁵)/2 extracts left. P_R = (1+γ⁵)/2 extracts right.

**Weyl equations (massless spin-1/2):**
Right: σ^μ ∂_μ ψ_R = 0, σ^μ = (I, σ_x, σ_y, σ_z)
Left: σ̄^μ ∂_μ ψ_L = 0, σ̄^μ = (I, -σ_x, -σ_y, -σ_z)

Mass terms couple ψ_L and ψ_R.

**Parity:** P swaps L ↔ R. Weak interaction couples only to left-handed →
violates parity (Wu, 1957).

**Helicity vs chirality:** for massless, they coincide. For massive,
chirality is Lorentz-invariant, helicity is frame-dependent.

---

## Nested Tori in S³

**Hopf torus foliation:**
(z₁,z₂) = (cos η · e^{iξ₁}, sin η · e^{iξ₂})

η ∈ [0,π/2], ξ₁,ξ₂ ∈ [0,2π). Fixed η → flat torus
T_η = S¹(cos η) × S¹(sin η) in S³.

**Boundaries:** η=0 → circle (z₂=0). η=π/2 → circle (z₁=0).
These are Hopf fibers over north/south poles of S².

**Clifford torus:** η = π/4, cos η = sin η = 1/√2.
- Unique torus dividing S³ into two congruent solid tori (Heegaard splitting)
- Flat (zero Gaussian curvature) embedded in S³
- Minimal surface in S³

**Nesting:** as η increases 0 → π/2, tori inflate from one boundary circle,
reach max symmetry at Clifford torus, deflate to other boundary circle.

**Fibers on tori:** Hopf fibers restricted to T_η are (1,1)-curves,
wrapping once around each circle factor.

---

## Curvature

**Riemann tensor:**
R(X,Y)Z = ∇_X∇_YZ - ∇_Y∇_XZ - ∇_{[X,Y]}Z

Measures noncommutativity of covariant derivatives.

**Ricci tensor:** R_μν = R^λ_μλν (trace of Riemann).
**Scalar curvature:** R = g^μν R_μν (full trace).

**Bundle curvature:** for connection ω on principal G-bundle,
Ω = dω + (1/2)[ω,ω] (structure equation). g-valued 2-form.

**Chern classes (Chern-Weil):**
det(I + (it/2π)Ω) = Σ_k c_k(E) t^k

c_k ∈ H^{2k}(M;Z). Topological invariants independent of connection choice.
c₁ of a line bundle = curvature class. Top Chern class = Euler class.

---

## Gauge Theory

| Physics | Geometry |
|---|---|
| Gauge field A_μ | Connection 1-form ω |
| Field strength F_μν | Curvature 2-form Ω |
| Gauge transformation | Change of local section |
| Gauge symmetry group | Structure group G |
| Matter field | Section of associated vector bundle |
| Covariant derivative D_μ | Connection on associated bundle |

Standard Model: SU(3)×SU(2)×U(1).
- U(1): electromagnetism
- SU(2): weak isospin (non-abelian → self-interacting bosons)
- SU(3): color/QCD (8 gluons from 8-dim Lie algebra)

Yang-Mills: D*F = J. Action: S = ∫ tr(F ∧ *F).

Bundle topology constrains physics: instantons, monopoles, theta-vacua.
Chern number of SU(2) instanton on S⁴ = instanton number.

---

## Topological Invariants

**Chern numbers:** ∫_M c_{i₁} ∧ ... ∧ c_{i_k} ∈ Z on closed 2n-manifold.
First Chern number classifies U(1) bundles over closed surfaces completely.

**Winding number:** deg(f: S^n → S^n) ∈ π_n(S^n) = Z. The Hopf fibration
= generator of π₃(S²) = Z, Hopf invariant 1.

**Euler characteristic:** χ(M) = ∫_M e(TM) (Gauss-Bonnet-Chern).
Surfaces: χ = 2-2g. Nowhere-vanishing vector field exists iff χ = 0.

**Classification:** complex line bundles over M classified by H²(M;Z) via c₁.
Principal G-bundles over S^n classified by π_{n-1}(G).

---

## Sources

Steenrod (1951) Topology of Fibre Bundles. Milnor & Stasheff (1974)
Characteristic Classes. Berry (1984) Proc. R. Soc. Lond. Simon (1983)
geometric interpretation. Wilczek & Zee (1984). Hopf (1931).
Lawson & Michelsohn (1989) Spin Geometry. Nakahara (2003) Geometry,
Topology and Physics. Frankel (2011) Geometry of Physics.
