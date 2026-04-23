# Proto-Ratchet Geometry Handoff Card

**Date:** 2026-03-29  
**Status:** Compact proto-ratchet handoff surface. Canon, working, and proto foundation remain separate. This card only covers the middle hinge:

`earned by constraints -> admitted as math -> realized as geometry -> kept as working layer`

---

## Earned By Constraints

| Object | Pure math or source-tight wording | Status | Immediate consequence |
|---|---|---|---|
| `F01_FINITUDE` | finite encodings, bounded distinguishability, no completed infinities, decidable admissibility | **Canon** | finite carriers, finite operator bases, finite Kraus families, finite codomains |
| `N01_NONCOMMUTATION` | order-sensitive composition, no swap-by-default, sequence belongs to the object | **Canon** | noncommuting operator algebra, guarded precedence, loop holonomy |
| `C` | `C = {F01, N01, admissible probe rules, admissible composition rules}` | **Canon** | admissibility charter |
| `M(C)` | `M(C) = {x : x admissible under C}` | **Canon** | admissible configuration space |
| induced geometry on `M(C)` | coordinate-free compatibility structure induced by `C` on `M(C)` | **Canon** | geometry comes after constraints |
| axes as slices | `A_i : M(C) -> V_i` | **Canon** | axes are bookkeeping slices, not primitives |

Thin-canon stop rule:

- thin canon currently stops at the root pair, `C`, `M(C)`, induced geometry on `M(C)`, and axis slices
- thin canon does not yet include `S^3`, Hopf, Weyl sheets, Clifford torus, or a finished `Ax0` bridge

Proto-foundational pressure that must remain visible:

- entropic monism
- no primitive identity
- no primitive equality
- finite witness discipline
- axes are discovered, not primitive

---

## Admitted As Math

| Mathematical kind | Status | Why it belongs here |
|---|---|---|
| finite registries and finite relation vocabularies | **Proto foundation** | minimal admissible carriers before richer realization |
| domain-scoped relations and operators | **Proto foundation** | allowed before scalar closure |
| precedence-sensitive operator composition | **Proto foundation** | direct consequence of `N01` |
| noncommutative algebra | **Proto foundation** | direct witness of order sensitivity |
| partial ordering / refinement structure | **Proto foundation** | distinguishability and refinement come before coordinates |
| finite Hilbert spaces | **Working realization** | current favored live QIT carrier basin |
| density matrices | **Working realization** | operational state language that respects finitude |
| finite probes / observables | **Working realization** | operational witnesses before scalar closure |
| CPTP maps / channels | **Working realization** | admissible transformation layer |
| Pauli basis | **Working realization** | finite noncommuting operator basis witnessing `N01` |

Handoff rule:

`F01 + N01` earns finite admissible carriers and order-sensitive algebra.

It does **not** yet directly earn:

- `C^2`
- `S^3`
- Hopf
- Weyl
- `Xi`
- `Phi_0`

---

## Realized As Geometry

| Layer | Pure math | Status | Read |
|---|---|---|---|
| finite QIT realization | `H = C^2`, `D(C^2)`, `O = O^dagger`, `p_O(rho) = Tr(O rho)` | **Working** | admissible math, not geometry yet |
| spinor carrier | `S^3 = {psi in C^2 : ||psi|| = 1}` | **Working geometry** | first concrete carrier-geometry rung |
| Hopf / Bloch reduction | `pi(psi) = psi^dagger sigma_vec psi in S^2`, `rho(psi) = |psi><psi|` | **Working geometry** | `S^3 -> S^2` plus density reduction |
| Hopf chart | `psi_s(phi,chi;eta)` | **Working geometry** | local torus and loop chart |
| torus foliation | `T_eta subset S^3`, `T_(pi/4)` the Clifford torus | **Working geometry** | derived geometry, not primitive substrate |
| loop families | `gamma_fiber^s`, `gamma_base^s`, `A = -i psi^dagger d psi` | **Canon-working realization** | strongest source-tight loop geometry layer |

Geometry ladder:

`constraints -> M(C) -> finite QIT realization -> S^3 -> S^2 -> T_eta -> gamma_fiber/base`

This is geometry buildup. It is not yet `Ax0`.

Geometry anti-smoothing notes:

- geometry is not the root constraint
- density matrices and probes belong to allowed math, not geometry proper
- `fiber/base` is universal geometry language
- `inner/outer` is later engine-indexed overlay language
- `S^3` / Hopf / Weyl are favored realizations, not the primitive root layer
- current executable success favors the Hopf/Weyl basin, but does not yet prove uniqueness

What is currently favored vs still open:

| Geometry read | Status |
|---|---|
| finite-QIT realization -> `S^3` / Hopf / `T_eta` / fiber-base / Weyl | favored live realization |
| Hopf/Weyl as one stable attractor basin | strongest open meta-read |
| Hopf/Weyl as uniquely forced by the roots | not earned |
| non-Hopf compatible manifolds | still open, but weak and underdeveloped |

---

## Kept As Working Layer

| Layer | Pure math | Status | Read |
|---|---|---|---|
| sheeting | `S_s^3`, `s in {L,R}` | **Thin-canon realization** | concrete carrier-sheet realization inside `M(C)` |
| Weyl working layer | `psi_L`, `psi_R`, `rho_L = psi_L psi_L^dagger`, `rho_R = psi_R psi_R^dagger`, `H_L = +H_0`, `H_R = -H_0` | **Working** | useful live realization above direct geometry |
| direct geometry | `S^3`, `S^2`, `T_eta`, fiber/base loops | **Direct geometry** | still not `Ax0` |
| `Ax0` role | `varphi_0 = Phi_0 o Xi` | **Working lock** | later functional after a bridge into a cut state |
| `Ax0` kernel | `Phi_0(rho_AB) = -S(A|B)_rho = I_c(A > B)_rho` | **Working strongest candidate** | strongest simple signed primitive currently surviving the live packet |
| global shell-cut form | `Phi_0(rho) = sum_r w_r I_c(A_r > B_r)_rho` | **Working/source-backed** | strongest global shell-cut form |
| bridge family | `Xi : geometry/history -> rho_AB` | **Open** | still the missing construction |

Working-layer rule:

- Weyl is useful, but not the most minimal canon rung
- `Axis 0` is not part of this ladder
- without `Xi`, you only have geometry, spinors, densities, and loops; you do not yet have the bipartite cut-state that `Ax0` measures

---

## Do Not Smooth

- Do not collapse the root pair into the deeper proto foundation.
- Do not collapse `F01 + N01` straight into `S^3` / Hopf / Weyl.
- Do not let the finite-QIT realization masquerade as primitive geometry.
- Do not let `S^3` / Hopf / Weyl overwrite `C -> M(C)` as the real admissions order.
- Do not treat the working Weyl layer as thin canon.
- Do not let `Ax0` leak backward into the geometry handoff.
- Do not treat the current strongest working realization as final canon closure.

Key phrases to preserve:

- `These are constraints. They are not yet geometry.`
- `constraints -> M(C) -> geometry on M(C) -> axis slices`
- `Do not smooth this into "canon geometry is already S^3/Hopf/Weyl".`
- `density matrices and probes belong to allowed math, not geometry proper`
- `fiber/base is universal geometry language`
- `inner/outer is later engine-indexed overlay language`
- `Axis 0 is not part of this ladder`
- `Without Xi, you only have geometry, spinors, densities, and loops. But you do not yet have the bipartite cut-state that Ax0 measures.`

---

## Working Read Order

1. [PROTO_RATCHET_ROOT_TO_ALLOWED_MATH_HANDOFF.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_ROOT_TO_ALLOWED_MATH_HANDOFF.md)
2. [PROTO_RATCHET_FOUR_SURFACES.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_FOUR_SURFACES.md)
3. [PROTO_RATCHET_ALLOWED_MATH_CHART.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_ALLOWED_MATH_CHART.md)
4. [CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md)
5. [PROTO_RATCHET_CONSTRAINT_GEOMETRY_BASIN.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_CONSTRAINT_GEOMETRY_BASIN.md)
6. [AXIS0_STRICT_BRIDGE_BASIN.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_STRICT_BRIDGE_BASIN.md)

Short read:

- root constraints earn the admissibility charter and `M(C)`
- allowed math is finite, witness-disciplined, and noncommutative before geometry
- geometry is still downstream of the root handoff
- the Weyl layer is kept as working realization, not canon closure
- `Ax0` is still a later bridge into a cut state, not a root-layer object
