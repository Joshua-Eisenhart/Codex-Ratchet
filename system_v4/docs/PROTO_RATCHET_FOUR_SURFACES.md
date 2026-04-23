# Proto-Ratchet Four Surfaces

**Date:** 2026-03-29
**Purpose:** Compact proto-ratchet packet that keeps four surfaces separate before later full ratcheting:

1. Root Constraints
2. Geometry Build Order
3. Allowed Math Ledger
4. Ax0 Bridge Basin

**Discipline:** This file is intentionally compact. It keeps **canon**, **working**, and **proposal** layers explicit and does not collapse them into one unified doctrine.

**Global do-not-smooth rules:**

- thin canon currently stops at `F01_FINITUDE`, `N01_NONCOMMUTATION`, `C`, `M(C)`, induced geometry on `M(C)`, and `A_i : M(C) -> V_i`
- these are constraints; they are not yet geometry
- `constraints -> M(C) -> geometry on M(C) -> axis slices` is load-bearing and should not be collapsed
- do not smooth this into "canon geometry is already `S^3`/Hopf/Weyl"
- density matrices and probes belong to allowed math, not geometry proper
- `fiber/base` is universal geometry language; `inner/outer` is later engine-indexed overlay language
- `Axis 0` is not part of the geometry ladder
- without `Xi`, you only have geometry, spinors, densities, and loops; you do not yet have the bipartite cut-state that `Ax0` measures
- raw `L|R` cut is killed as sufficient

---

## 1. Root Constraints

| Object | Pure math or source-tight wording | Status | Why it belongs here |
|---|---|---|---|
| `F01_FINITUDE` | finite encodings, bounded distinguishability, no completed infinities, decidable admissibility | **Canon** from [TERRAIN_MATH_LEDGER_v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/TERRAIN_MATH_LEDGER_v1.md) | This is one of the two thin-canon root locks used by the live `M(C)` packet. It forces finite carriers, finite operator bases, and finite admissibility. |
| `N01_NONCOMMUTATION` | order-sensitive composition, no swap-by-default, sequence belongs to the object | **Canon** from [TERRAIN_MATH_LEDGER_v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/TERRAIN_MATH_LEDGER_v1.md) | This is the other thin-canon root lock. It directly admits order-sensitive composition, noncommuting operators, and loop holonomy. |
| entropic monism | there is only one kind of substance: constraint on distinguishability | **Proto foundation** from [Constraints.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Constraints.md) | This is deeper than the thin canon pair. It explains why information, geometry, and dynamics are secondary descriptions of constraint. |
| no primitive identity / equality | `CAS04 NO_PRIMITIVE_IDENTITY`, `CAS05 NO_PRIMITIVE_EQUALITY` | **Proto foundation** from [COSMOLOGICALLY_CONSTRAINT_ADMISSIBLE_STRUCTURES_v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/COSMOLOGICALLY_CONSTRAINT_ADMISSIBLE_STRUCTURES_v1.md) | This blocks smuggling sameness, substitution, and objecthood in before probes and finite discriminator families exist. |
| finite witness discipline | refinement claims require explicit finite witness tokens | **Proto foundation** from [REFINEMENT_CONTRACT_v1.1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/REFINEMENT_CONTRACT_v1.1.md) | This constrains admissibility before scalar grading, geometry, or finished semantics are admitted. |

**Root note:** The thin canon root pair is currently `F01_FINITUDE + N01_NONCOMMUTATION`. The broader constraint-ladder material is stronger and shapes proto-ratcheting, but it should not be silently relabeled as the same executable layer.

---

## 2. Geometry Build Order

| Step | Pure math | Status | Why it belongs in the build order |
|---|---|---|---|
| constraints to manifold | `C = {F01, N01, admissible probe rules, admissible composition rules}`, `M(C) = {x : x admissible under C}` | **Canon** from [CANON_GEOMETRY_CONSTRAINT_MANIFOLD_SPEC_v1.1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/CANON_GEOMETRY_CONSTRAINT_MANIFOLD_SPEC_v1.1.md) and [TERRAIN_MATH_LEDGER_v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/TERRAIN_MATH_LEDGER_v1.md) | Geometry is explicitly a constraint manifold emerging from constraints. |
| manifold to coordinate-free geometry | geometry = compatibility structure induced by `C` on `M(C)` | **Canon** | This keeps geometry after constraints and before axes. |
| live finite-QIT realization | `H = C^2`, `D(C^2)`, probes `p_O(rho) = Tr(O rho)` | **Working** from [TERRAIN_MATH_LEDGER_v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/TERRAIN_MATH_LEDGER_v1.md) and [CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md) | This is the current favored executable basin, not the primitive root itself. |
| spinor carrier | `S^3 = {psi in C^2 : ||psi|| = 1}`, `pi(psi) = psi^dagger sigma_vec psi in S^2` | **Working** | This is the first concrete geometry ladder used by the live packet. |
| torus realization | `T_eta subset S^3`, with `T_{pi/4}` the Clifford torus | **Working** | This is the nested Hopf torus layer; it is derived geometry, not primitive substrate. |
| loop families | `gamma_fiber^s`, `gamma_base^s`, `A = -i psi^dagger d psi` | **Canon-working realization** from [TERRAIN_MATH_LEDGER_v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/TERRAIN_MATH_LEDGER_v1.md) | This is the strongest source-tight loop geometry layer now. |
| Weyl working layer | `psi_L`, `psi_R`, `rho_L = psi_L psi_L^dagger`, `rho_R = psi_R psi_R^dagger`, `H_L = +H_0`, `H_R = -H_0` | **Working** | This is the live left/right sheet layer on top of the direct carrier geometry. |
| axes as slices | `A_i : M(C) -> V_i` | **Canon** | Axes come after the manifold and after the geometry buildup. |

**Build-order note:** The compact geometry ladder is:

`constraints -> M(C) -> finite QIT realization -> S^3 -> S^2 -> T_eta -> gamma_fiber/base -> (psi_L, psi_R, rho_L, rho_R)`

This is geometry buildup. It is not yet `Ax0`.

**Build-order anti-smoothing notes:**

- root constraints are upstream admissibility, not carrier geometry
- the live finite-QIT packet is the current favored realization, not the primitive substrate
- Weyl is useful, but not the most minimal canon rung
- axes come after the manifold and after the geometry buildup

---

## 3. Allowed Math Ledger

| Category | Admitted mathematical kinds | Status | Why this category belongs here |
|---|---|---|---|
| early-allowed | finite registries, domain-scoped relations, order-sensitive composition, noncommutative algebra, partial ordering / refinement structure | **Proto foundation** from [Constraints.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Constraints.md), [COSMOLOGICALLY_CONSTRAINT_ADMISSIBLE_STRUCTURES_v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/COSMOLOGICALLY_CONSTRAINT_ADMISSIBLE_STRUCTURES_v1.md), [REFINEMENT_CONTRACT_v1.1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/REFINEMENT_CONTRACT_v1.1.md) | These are the earliest admissible mathematical kinds because they respect finitude, witness discipline, and noncommutation without assuming geometry or scalar closure first. |
| early-allowed live realization | finite Hilbert spaces, density matrices, CPTP maps, Pauli basis, finite probes | **Working** from [MATH_NOMINALISM_SYNTHESIS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/MATH_NOMINALISM_SYNTHESIS.md) and [TERRAIN_MATH_LEDGER_v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/TERRAIN_MATH_LEDGER_v1.md) | This is the current executable QIT basin favored by the corpus. |
| late-derived | scalar-valued functionals, information geometry, metrics, `S^3` / Hopf / Clifford / nested tori, manifold geometry, axes as slices | **Canon + working + proto foundation** | These are admissible only after earlier prerequisites are earned. They are not primitive just because they are now live. |
| banned-as-primitive | completed infinities, unrestricted reals, global coordinates, absolute metrics, free equality, unrestricted substitution, primitive identity, free closure, overlay-smuggled kernel math | **Proto foundation** from [Constraints.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Constraints.md) and [Rosetta contract v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Rosetta%20contract%20v1.md) | These are explicitly blocked at primitive admission because they would smuggle finished structure into the system too early. |

**Ledger note:** "Allowed" here means admissible in the proto-ratchet build, not globally primitive. The live QIT packet is the current best working basin, but it remains a realization of the constraint program, not a license to skip the buildup order.

**Ledger anti-smoothing notes:**

- some banned-as-primitive objects may return later in restricted, derived form
- the strongest ban in practice is not just "no infinity"; it is also "no free structure"
- overlay labels are a ratchet hazard and must stay overlay-only unless re-admitted explicitly

---

## 4. Ax0 Bridge Basin

| Object | Pure math | Status | Why it belongs in the `Ax0` basin |
|---|---|---|---|
| `Ax0` role | `varphi_0 = Phi_0 o Xi` | **Working lock** from [AXIS0_MANIFOLD_BRIDGE_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md) | This is the cleanest compact statement: `Ax0` is not the geometry itself; it is a functional after a bridge into a cut state. |
| `Ax0` domain | `Phi_0 : D(H_A tensor H_B) -> R` or shell-cut/history generalization | **Source-backed family** | `Ax0` acts on cut states, not on a single isolated spinor. |
| best simple kernel | `Phi_0(rho_AB) = -S(A|B)_rho = I_c(A>B)_rho` | **Working strongest candidate** | This is the strongest simple signed primitive currently surviving the live packet. |
| strongest global form | `Phi_0(rho) = sum_r w_r I_c(A_r > B_r)_rho` | **Working/source-backed** | This is the strongest shell-cut global form now. |
| companion diagnostic | `Phi_0(rho_AB) = I(A:B)_rho` | **Working diagnostic only** | Mutual information is useful for guardrails and correlation checks, but it is not enough alone because it cannot go negative. |
| bridge family | `Xi : geometry/history -> rho_AB` | **Open** | This is still the missing construction. It is the main unresolved part of `Ax0`. |
| live bridge shapes | pointwise pullback, shell-cut pointwise pullback, history functional | **Working/proposal boundary** | These are the current basin shapes; none is yet the final doctrine-level bridge. |
| guardrail result | raw local Hopf/Weyl geometry + raw `L|R` cut => trivial `Ax0` | **Working executable result** from the live repo probes summarized in [AXIS0_MANIFOLD_BRIDGE_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md) | This is the key basin constraint: geometry alone does not finish `Ax0`. |

**Basin note:** The compact `Ax0` read is:

`geometry != Ax0`

`Ax0 = Phi_0(rho_AB) after a bridge Xi`

The best current basin is:

- real geometry is already executable
- the strongest simple kernel is `-S(A|B) = I_c`
- the exact bridge `Xi` is still open
- raw uncoupled `L|R` is not enough

**Ax0 anti-smoothing notes:**

- geometry is not `Ax0`
- mutual information is a companion diagnostic, not the full signed primitive
- the bridge family is still open even though the kernel basin has a current leader
- shell-cut and history shapes may both survive; neither should be declared final too early

---

## 5. Working Read Order

For the compact basin, the safest read order is:

1. [PROTO_RATCHET_ROOT_TO_ALLOWED_MATH_HANDOFF.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_ROOT_TO_ALLOWED_MATH_HANDOFF.md)
2. [PROTO_RATCHET_GEOMETRY_HANDOFF_CARD.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_GEOMETRY_HANDOFF_CARD.md) once present, as the hinge from admitted math into realized geometry
3. [CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md)
4. [PROTO_RATCHET_CONSTRAINT_GEOMETRY_BASIN.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_CONSTRAINT_GEOMETRY_BASIN.md)
5. [AXIS0_STRICT_BRIDGE_BASIN.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_STRICT_BRIDGE_BASIN.md)
6. [AXIS0_CUT_TAXONOMY.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_CUT_TAXONOMY.md)

Short read:

- root handoff earns admissible carriers and order-sensitive algebra, not finished geometry
- geometry handoff should sit between allowed math and realized geometry
- `Ax0` stays downstream of geometry and still depends on a bridge
- after the bridge question, the exact cut question is still separate and now has its own owner packet
