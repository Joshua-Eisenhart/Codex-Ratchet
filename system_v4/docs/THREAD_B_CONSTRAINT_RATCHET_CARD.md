# Thread B Constraint Ratchet Card

**Date:** 2026-03-29
**Status:** Proto-ratchet owner surface for a B-thread-facing rebuild from root constraints. This is not a canon claim and not a Thread B submission. It is a constraint-first admission map that keeps boot fences, allowed math, favored geometry, entropy branches, and axis-math branches separate.

---

## 1. Thread B Admission Fences

These constraints come from the Thread B boot surfaces and bound what a B-thread-safe ratchet can mean.

| Fence | Source | Effect on this ratchet |
|---|---|---|
| Thread B is a kernel | [BOOTPACK_THREAD_B_v3.9.13.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/upgrade%20docs/BOOTPACK_THREAD_B_v3.9.13.md), [17_BOOTPACK_THREAD_B_v3.9.13_ENFORCEABLE_CONTRACT_EXTRACT_FOR_IMPLEMENTATION_v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/specs/17_BOOTPACK_THREAD_B_v3.9.13_ENFORCEABLE_CONTRACT_EXTRACT_FOR_IMPLEMENTATION_v1.md) | no freeform prose can be treated as accepted B-state; B only accepts command/artifact containers |
| Thread B never runs simulations | same | any probe-backed ratchet claim must be carried by `SIM_EVIDENCE v1`, not by narrative summary |
| domain/metaphor words are not primitive | same | geometry/entropy/axis language must enter through term discipline, not as raw kernel assumptions |
| term pipeline controls admission | same | terms and labels become legal only through `TERM_DEF`, `CANON_PERMIT`, evidence binding, and dependency discipline |
| A2 boot is source-bound and no-smoothing | [28_A2_THREAD_BOOT__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md) | this surface can prepare bounded B-thread fuel, but it cannot self-authorize canon or smooth tensions away |

Thread-B-safe reading rule:

- separate root-earned structure from favored realizations
- separate admitted math from geometry
- separate entropy families from ontology claims
- separate axis branch maps from doctrine-level acceptance

---

## 2. Root-Earned Core

The current thin-canon root pair remains:

| Root | Immediate earning | Status |
|---|---|---|
| `F01_FINITUDE` | finite carriers, finite witnesses, finite codomains, no completed infinities | thin canon |
| `N01_NONCOMMUTATION` | order-sensitive composition, noncommuting algebra, guarded precedence | thin canon |

Direct handoff:

\[
F01 + N01 \to C \to M(C) \to \text{induced geometry on } M(C) \to A_i : M(C) \to V_i
\]

What the roots directly earn:

- finite admissible carriers
- finite witness discipline
- precedence-sensitive composition
- noncommutative operator language
- refinement / partial-order structure

What the roots do **not** directly earn:

- `C^2` as the unique carrier
- density-matrix ontology as primitive
- `S^3` / Hopf / Weyl as primitive geometry
- a finished scalar or entropy kernel
- a finished `Ax0` bridge or cut

---

## 3. Admitted Math Branches

These are the main math branches that can be carried forward constraint-first without pretending they are all equally primitive.

| Branch | Best current objects | Surface class | B-thread-safe read |
|---|---|---|---|
| admissible core | finite registries, relations, partial orders, noncommutative operator algebra | root-earned / proto foundation | earliest legal math |
| favored live QIT basin | finite Hilbert carriers, density matrices, probes, CPTP maps, Pauli basis | admitted working math | strongest live executable basin, not root doctrine |
| favored live geometry basin | `S^3`, Hopf reduction to `S^2`, `T_eta`, Clifford / nested tori, fiber/base loops | realized geometry | favored realization, not directly earned by the root pair |
| working Weyl layer | `psi_L`, `psi_R`, `rho_L`, `rho_R`, `H_L=+H_0`, `H_R=-H_0` | working layer | useful compiled realization above direct geometry |
| entropy branch | `S(rho)`, `I(A:B)`, `S(A|B)`, `I_c(A>B)`, shell-cut sums, relative entropy | late-derived / working / proxy | operational family after math admission, not primitive ontology |
| axis branch | axis-local math families for Ax0-Ax6 | mixed: primitive, derived, open | use owner packets; do not let one axis branch rewrite the whole substrate |

---

## 4. Geometry And Entropy Boundaries

The core separation to preserve is:

\[
\text{constraints} \to \text{admitted math} \to \text{realized geometry} \to \text{entropy / axis functionals}
\]

Current B-thread-safe read:

- geometry is downstream of the root handoff
- entropy is downstream of admitted math and explicit domain declarations
- entropy does not define admissibility
- geometry does not by itself finish `Ax0`

### Entropy branch ranking

| Family | Status | Role |
|---|---|---|
| `I_c(A>B) = -S(A|B)` | strongest working candidate | signed cut-based primitive for `Ax0` |
| `sum_r w_r I_c(A_r>B_r)` | working/source-backed | strongest shell-cut global form |
| `I(A:B)` | diagnostic | total-correlation guardrail |
| `S(rho)` | diagnostic / late-derived | one-state mixedness only |
| `D(rho||sigma)` | working / late-derived | shell or reference comparison |
| refinement entropy / path entropy | proto-foundational branch | ordering / path-cost branch before full geometry |

Thread-B-safe entropy rule:

- scalar families stay descriptive unless later contracts admit more
- no entropy family can define admissibility at base
- multiple non-equivalent scalar families may coexist

---

## 5. Axis-Math Branches

The current axis branch map is:

| Axis family | Main math branch | Status | Owner surface |
|---|---|---|---|
| `Ax0` | cut-state entropy / coherent-information branch plus bridge/cut branch | source-backed family, bridge/cut still open | [AXIS_0_1_2_QIT_MATH.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_0_1_2_QIT_MATH.md), [AXIS0_MANIFOLD_BRIDGE_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md), [AXIS0_CUT_TAXONOMY.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_CUT_TAXONOMY.md) |
| `Ax1` / `Ax2` | topology / representation branch | source-locked semantic split; reduced product surface is locked | [AXIS_0_1_2_QIT_MATH.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_0_1_2_QIT_MATH.md) |
| `Ax3` | geometry branch: fiber vs base-lift loops | derivable from geometry spine | [AXIS_3_4_5_6_QIT_MATH.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_3_4_5_6_QIT_MATH.md) |
| `Ax4` | CPTP ordering branch: unitary vs non-unitary loop ordering | derivable from constraint-ladder source and loop assignments | [AXIS_3_4_5_6_QIT_MATH.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_3_4_5_6_QIT_MATH.md) |
| `Ax5` | operator branch: dephasing vs rotation | directly derivable from operator math | [AXIS_3_4_5_6_QIT_MATH.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_3_4_5_6_QIT_MATH.md) |
| `Ax6` | precedence branch: operator vs terrain order | derived from `Ax0 ⊕ Ax3` | [AXIS_3_4_5_6_QIT_MATH.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_3_4_5_6_QIT_MATH.md) |

Detailed branch map:

- [AXIS_MATH_BRANCH_MAP.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_MATH_BRANCH_MAP.md)

---

## 6. Do Not Smooth

- Do not let B-thread-safe admission talk masquerade as accepted Thread B state.
- Do not let `F01 + N01` be rewritten as if they already imply Hopf/Weyl uniquely.
- Do not let the favored QIT basin erase alternative admissible branches.
- Do not let entropy families define ontology, time, heat, or admissibility at base.
- Do not let one axis packet silently become the substrate for all the others.
- Do not let proxy/runtime language outrank boot fences and explicit term admission.

Key phrases to preserve:

- `These are constraints. They are not yet geometry.`
- `constraints -> admitted math -> realized geometry -> entropy / axis functionals`
- `Thread B consumes SIM_EVIDENCE v1 only`
- `terms enter through the term pipeline, not by prose`
- `multiple non-equivalent scalar functionals may coexist`

---

## 7. Owner Stack

Use this stack for the B-thread root-first ratchet:

1. [PROTO_RATCHET_ROOT_TO_ALLOWED_MATH_HANDOFF.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_ROOT_TO_ALLOWED_MATH_HANDOFF.md)
2. [PROTO_RATCHET_GEOMETRY_HANDOFF_CARD.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_GEOMETRY_HANDOFF_CARD.md)
3. [PROTO_RATCHET_ENTROPY_ALIGNMENT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_ENTROPY_ALIGNMENT.md)
4. [THREAD_B_CONSTRAINT_RATCHET_CARD.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_CONSTRAINT_RATCHET_CARD.md)
5. [AXIS_MATH_BRANCH_MAP.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_MATH_BRANCH_MAP.md)
6. [AXIS0_MANIFOLD_BRIDGE_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md)
7. [AXIS0_CUT_TAXONOMY.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_CUT_TAXONOMY.md)

Short read:

- roots earn admissibility and order-sensitive algebra
- allowed math comes next
- favored geometry is later and still non-unique
- entropy families are late-derived operational branches
- axis math should be handled as a branch map, not as one blended doctrine
