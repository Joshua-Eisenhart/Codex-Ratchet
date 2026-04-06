# Axis Math Branches Map

**Date:** 2026-03-29
**Status:** SUPERSEDED for current routing use. Retained as an older broader extraction surface; do not use as the preferred branch-routing packet.
**Superseded by:** [AXIS_MATH_BRANCH_MAP.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_MATH_BRANCH_MAP.md)
**Scope:** Compact branch extraction from these four owner surfaces only:
- `core_docs/a1_refined_Ratchet Fuel/AXES_MASTER_SPEC_v0.2.md`
- `core_docs/a1_refined_Ratchet Fuel/AXIS_FOUNDATION_COMPANION_v1.4.md`
- `system_v4/docs/AXIS_0_1_2_QIT_MATH.md`
- `system_v4/docs/PROTO_RATCHET_FOUR_SURFACES.md`

**Purpose:** Map the math branches feeding `Ax0..Ax6` and the main cross-product structures without smoothing canon, working, and overlay layers together.

---

## 1. Upstream Branch Roots

Constraints are not yet geometry.

The handoff from roots is first to admissibility, then to allowed math, then to realization.

\[
\text{constraints} \to C \to M(C) \to \text{admissible mathematics} \to \text{favored realizations} \to \text{axes}
\]

Axes are discovered, not primitive.

Axes are slices
\[
A_i : M(C) \to V_i
\]
not primitive carriers.

| Root branch | Pure math | Status | Feeds |
|---|---|---|---|
| constraint branch | `F01_FINITUDE`, `N01_NONCOMMUTATION`, admissibility rules, `M(C)` | canon | all later axis slices |
| allowed-math branch | finite witnesses, finite operators, probes, relations, refinement/order structures, finite Hilbert spaces, density matrices, CPTP maps, Pauli basis, noncommutative algebra | working / proto-ratchet | `Ax0`, `Ax1`, `Ax2`, `Ax4`, `Ax5`, `Ax6` |
| realized geometry branch | `C^2 -> S^3 -> S^2 -> T_eta -> gamma_fiber/gamma_base`, plus Weyl working layer | working | geometry-backed slices and bridge candidates |
| entropy/correlation branch | `S(rho)`, `S(A|B)`, `I_c(A>B)`, `I(A:B)` | working | `Ax0` |
| operator/channel branch | unitary channels, proper CPTP channels, conjugated representations, composition order | canon + working | `Ax1`, `Ax2`, `Ax4`, `Ax6` |
| texture/calculus branch | partition vs mixing, gradient / delta vs Laplacian / Fourier | canon | `Ax5` |

**Load-bearing rule:** `constraints -> M(C) -> geometry on M(C) -> axis slices`.

Thin canon currently stops at the root pair, `C`, `M(C)`, induced geometry on `M(C)`, and axis slices.

Do not collapse the handoff into the favored QIT realization.

Do not smooth this into "canon geometry is already S^3/Hopf/Weyl".

---

## 2. Axis Branch Map

| Axis | Primary branch | Pure math branch | Status | Immediate outputs |
|---|---|---|---|---|
| `Ax0` | cut-state entropy/correlation branch | `Phi_0(rho_AB)` after `Xi : geometry/history -> rho_AB` | canon role + working kernel family | two-class slice on `M(C)` after a bridge |
| `Ax1` | openness / channel-class branch | unitary `*-automorphism` vs proper CPTP | source-locked working split | one factor of `Topology4` |
| `Ax2` | representation / frame-class branch | direct representation vs unitarily conjugated representation | source-locked working split | second factor of `Topology4` |
| `Ax3` | engine-family branch | Type-1 vs Type-2 | canon semantic split only | engine-family fork |
| `Ax4` | operator-family / optimization branch | `DEDUCTIVE (FeTi)` vs `INDUCTIVE (TeFi)` | canon | loop/operator family fork |
| `Ax5` | texture / generator-algebra branch | `Line (Partition)` vs `Wave (Mixing)` | canon | calculus toolhead fork |
| `Ax6` | precedence / composition branch | `UP` vs `DOWN` | canon | sidedness / operator-channel order |

---

## 3. Axis 0 Branches

| Ax0 sub-branch | Pure math | Status | Read |
|---|---|---|---|
| role on manifold | `A_0 : M(C) -> V_0` | canon | two-class slice on the constraint manifold |
| bridge branch | `Xi : geometry/history -> rho_AB` | open | geometry alone is not yet an Ax0 object |
| generic kernel family | `Phi_0(rho_AB)` | source-backed family | admissible cut-state functional |
| single-state entropy branch | `S(rho) = -Tr(rho log rho)` | admitted, not enough alone | mixedness only |
| total-correlation branch | `I(A:B)` | live companion diagnostic | correlation magnitude, never negative |
| signed correlation branch | `-S(A|B) = I_c(A>B)` | strongest simple working candidate | negative-entropy / coherent-information branch |
| shell/global branch | `sum_r w_r I_c(A_r > B_r)` | strongest screenshot-backed global form | shell-cut family |
| discrete projection branch | `{Ne,Ni}` vs `{Se,Si}` | working projection | white/black, N/S projection only |

**Ax0 branch read:** `Ax0` is downstream of constraints, allowed math, geometry, and a bridge. It is not the geometry itself.

`Xi : geometry/history -> rho_AB` is an unresolved bridge object.

Current live bridge read:

- real geometry + `(L|R cut)` => trivial `Ax0`
- raw local `L|R` is killed as sufficient
- `Xi_hist` is the strongest live bridge family
- point-reference is the strongest live pointwise discriminator
- shell-strata pointwise is killed as a pointwise bridge
- runtime `GA0` is proxy only

---

## 4. Axis 1 and Axis 2 Branches

### `Ax1`

| Branch | Pure math | Status | Notes |
|---|---|---|---|
| semantic split | unitary `*-automorphism` vs proper CPTP | source-locked working split | kernel class split |
| working realization | `Phi(rho) = U rho U^dagger` vs `Phi(rho) = sum_k K_k rho K_k^dagger` | working | concrete QIT realization |
| reduced topology projection | `{Se,Ni}` vs `{Ne,Si}` | working reduced join surface | do not confuse with full terrain-law ledger |

### `Ax2`

| Branch | Pure math | Status | Notes |
|---|---|---|---|
| semantic split | direct vs unitarily conjugated representation | source-locked working split | frame-class split |
| direct branch | `dot rho = L(rho)` | source-locked | ambient / fixed-frame description |
| conjugated branch | `tilde rho = V^dagger rho V`, `dot tilde rho = V^dagger L(V tilde rho V^dagger)V - i[-K, tilde rho]` | source-locked | transported / co-moving description |
| unitary special case | `dot rho = -i[H,rho]`, `dot tilde rho = -i[tilde H - K, tilde rho]` | working | same split in the unitary subclass |

---

## 5. Axis 3 through Axis 6 Branches

| Axis | Branch | Pure math | Status | Nonconflation note |
|---|---|---|---|---|
| `Ax3` | engine-family branch | Type-1 vs Type-2 | canon | Weyl / chirality / flux is overlay, not canon `Ax3` |
| `Ax4` | optimization / operator-family branch | `DEDUCTIVE (FeTi)` vs `INDUCTIVE (TeFi)` | canon | do not collapse into loop order; loop order is a derived probe |
| `Ax5` | texture / generator-algebra branch | `Line (Partition)` vs `Wave (Mixing)` | canon | do not collapse into Jung labels |
| `Ax6` | precedence / sidedness branch | `UP` vs `DOWN` | canon | `Ax6 != Ax4` |

Nonconflation rule:

- `Ax3` canon is engine-family only
- `Ax4`, `Ax5`, and `Ax6` are distinct branches
- do not confuse point-reference discrimination with a finished bridge theorem
- do not confuse broad-spectrum ranking with strict bridge-quality proof

### `Ax4` operator-family details from the master spec

| Side | Pure math branch | Read |
|---|---|---|
| deductive | `S -> 0`, `Ti` projector/coarse-graining, `Fe` Lindbladian synchronization | constraint-first family |
| inductive | `Delta W -> max`, `Te` Hamiltonian / gradient drive, `Fi` spectral / Fourier projection | drive/exploration-first family |

### `Ax5` texture details from the master spec

| Side | Pure math branch | Read |
|---|---|---|
| line / partition | `rho -> sum_x P_x rho P_x`, gradient, Dirac-delta projector | cutting / isolating branch |
| wave / mixing | `rho -> sum_k W_k rho W_k^dagger`, Laplacian, Fourier transform | binding / smoothing / correlating branch |

---

## 6. Cross-Products and Derived Structures

| Structure | Pure math | Status | Read |
|---|---|---|---|
| `Ax1 x Ax2` | `Topology4` | canon + working | four base regimes |
| `Topology4` regimes | `open_system_eulerian`, `open_system_lagrangian`, `closed_system_eulerian`, `closed_system_lagrangian` | overlay-companion kernel-safe naming | math-first names for the four regimes |
| reduced `Ax1 x Ax2` table | `Se = CPTP + direct`, `Ni = CPTP + conjugated`, `Ne = unitary + direct`, `Si = unitary + conjugated` | source-locked working packet | current reduced terrain join |
| graph edges on Topology4 | adjacency between bases | derived only | not `Ax1` or `Ax2` themselves |
| `Topology4 x Flux2` | `Terrain8` | overlay only | same topology, different flow sign |
| `Stage8` | `(outer/inner) x Topology4` | overlay only | engine schematic, not canon axis math |

**Cross-product lock:** the only source-clean cross-product directly locked in this extraction is `Ax1 x Ax2 -> Topology4`. `Terrain8` and `Stage8` are overlay pipelines from the companion, not canon kernel theorems.

---

## 7. Kernel vs Overlay

| Axis | Kernel branch | Overlay branch |
|---|---|---|
| `Ax0` | cut-state entropy/correlation functional | white/black, N/S labels |
| `Ax1` | unitary vs proper CPTP | open/closed naming |
| `Ax2` | direct vs conjugated representation | Eulerian/Lagrangian, teardrop/dot naming |
| `Ax3` | engine-family split | Weyl chirality / flux sign |
| `Ax4` | deductive vs inductive operator family | loop-order heuristics |
| `Ax5` | line/partition vs wave/mixing | Jung / texture labels |
| `Ax6` | precedence / sidedness | token-order mnemonics |

---

## 8. Compact Read

| Level | Branch result |
|---|---|
| constraints | admit `M(C)` and order-sensitive admissibility |
| allowed math | admits finite witnesses, finite operators, probes, relations, refinement/order structures, then finite QIT objects, density matrices, channels, probes, Pauli basis |
| geometry | current favored realization is `S^3 -> Hopf -> T_eta -> fiber/base`, with a Weyl working layer |
| `Ax0` | entropy/correlation branch on cut states after a bridge |
| `Ax1`, `Ax2` | the two math splits whose product gives `Topology4` |
| `Ax3` | engine-family split only |
| `Ax4` | operator-family / optimization split |
| `Ax5` | texture / calculus split |
| `Ax6` | precedence / composition-order split |

**Do not smooth:**
- constraints are not yet geometry
- noncommutative algebra is admitted before geometry
- refinement/order structure is admitted before coordinates
- finite Hilbert spaces are working admissible, not primitive handoff
- density matrices and probes belong to allowed math, not geometry proper
- Pauli basis is a working realization witness of `N01`, not a root primitive
- Hopf-like and `S^3`-like structures are candidates, not assumptions
- `S^3` / Hopf / Weyl are favored realizations, not the primitive root layer
- nested Hopf-like structure is a stable attractor under the constraints, not the only possible endpoint
- `Ax0` is not the geometry.
- `Ax1 x Ax2` is the base-regime product, not the graph edges.
- `Ax3` canon is engine-family only.
- `Terrain8` is an overlay pipeline, not a canon primitive.
