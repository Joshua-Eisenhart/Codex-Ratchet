# Axis Math Branch Map

**Date:** 2026-03-29
**Status:** Compact branch map for the math families feeding the current axis packet. This is a proto-ratchet routing surface, not a final ontology. It separates primitive, derived, geometry-backed, operator-backed, entropy-backed, and open families.

---

## 1. Upstream Math Families

| Family | What it contributes |
|---|---|
| admissible core | finite carriers, witness discipline, noncommutative algebra, refinement/order structure |
| geometry branch | `S^3`, Hopf projection, `S^2`, `T_eta`, fiber/base loops, Weyl working layer |
| entropy branch | `S(rho)`, `I(A:B)`, `S(A|B)`, `I_c(A>B)`, shell-cut sums, relative entropy |
| operator branch | unitary channels, non-unitary CPTP channels, dephasing, rotations, precedence order |
| derived closure branch | `Ax1 = f(Ax0,Ax2)`, `Ax4 = f(Ax3, engine type)`, `Ax6 = Ax0 xor Ax3` |

---

## 2. Axis-By-Axis Map

| Axis | Main math family | Branch class | Status | Open items |
|---|---|---|---|---|
| `Ax0` | cut-state entropy branch on \(\rho_{AB}\): \(I_c(A>B)=-S(A|B)\), shell-cut sums, diagnostics \(I(A:B)\) | entropy-backed + bridge/cut dependent | source-backed candidate family; bridge and cut still open | exact bridge `Xi`, exact cut `A|B`, pointwise/history unification, shell strict replacement |
| `Ax1` | topology / terrain-class split; reduced product with `Ax2` | derived from `Ax0 × Ax2` in current packet, source-locked semantic split | source-locked semantic split | full terrain laws beyond reduced product equations |
| `Ax2` | direct vs unitarily conjugated representation | primitive constraint-manifold slice with representation law | source-locked | explicit geometry-tied transport law `V(t)` |
| `Ax3` | geometry branch: Hopf fiber loop vs lifted base loop / base-lift loop | geometry-backed primitive | derivable from geometry spine | no major kernel open item; naming must stay geometry-tight |
| `Ax4` | CPTP ordering branch: \(\mathcal U\mathcal E\mathcal U\mathcal E\) vs \(\mathcal E\mathcal U\mathcal E\mathcal U\) | operator-backed derived axis | derivable from loop-order assignments | exact sub-operator sequencing inside one stage |
| `Ax5` | operator branch: dephasing vs rotation; Ti/Te vs Fi/Fe | operator-backed primitive | directly derivable from operator math | none major beyond broader terrain-law integration |
| `Ax6` | precedence branch: operator-after-terrain vs terrain-after-operator | derived closure | directly derivable from `Ax0 ⊕ Ax3` | depends operationally on unresolved `Ax0` concretization |

---

## 3. Primitive vs Derived Read

| Axis | Primitive / derived in current packet | Why |
|---|---|---|
| `Ax0` | primitive slice statement, but concretization still open | lives as `A0 : M(C) -> V0`, yet its concrete kernel needs bridge/cut completion |
| `Ax1` | derived | current packet treats it as the cross-diagonal / reduced product branch of `Ax0 × Ax2` |
| `Ax2` | primitive | direct vs conjugated representation split is source-locked |
| `Ax3` | primitive | tied to geometry spine: density-stationary fiber vs density-traversing base-lift |
| `Ax4` | derived | loop ordering of unitary vs non-unitary maps depends on loop/engine assignment |
| `Ax5` | primitive | directly carried by subcycle operator type |
| `Ax6` | derived | entailed by `Ax0` and `Ax3` in the current packet |

---

## 4. Geometry-Backed Branches

These axes depend primarily on the favored geometry realization.

| Axis | Geometry objects | Read |
|---|---|---|
| `Ax3` | `S^3`, Hopf map, fiber/base loops, horizontal condition | strongest geometry-backed axis |
| `Ax0` | geometry is upstream only; needs bridge into cut state | not geometry itself, but geometry constrains its bridge options |
| `Ax6` | depends partly on `Ax3` geometry split | geometry enters indirectly through `Ax3` |

Geometry warning:

- do not let geometry-backed mean geometry-identical
- `Ax0` still needs `Xi` and `A|B`

---

## 5. Operator-Backed Branches

These axes depend primarily on operator/channel math.

| Axis | Operator math | Read |
|---|---|---|
| `Ax4` | unitary vs non-unitary CPTP ordering | loop-order branch |
| `Ax5` | dephasing vs rotation operators | subcycle operator branch |
| `Ax6` | precedence composition order | operator/terrain ordering branch |

Operator warning:

- do not conflate operator-backed branches with the geometry substrate
- `Ax4` and `Ax5` both use QIT channel math, but on different objects and at different layers

---

## 6. Entropy-Backed Branches

Only `Ax0` is directly entropy-backed in the current stack.

| Axis | Entropy family | Current read |
|---|---|---|
| `Ax0` | `I_c(A>B)`, `S(A|B)`, `I(A:B)`, shell-cut sums, relative-entropy-style comparisons | strongest entropy-backed branch; still bridge/cut open |

Entropy warning:

- `S(rho)` alone is too weak for `Ax0`
- `I(A:B)` is a companion diagnostic, not the full signed primitive
- entropy branches are late-derived and cannot define admissibility by themselves

---

## 7. Open Branches

| Open branch | Why it remains open |
|---|---|
| exact `Ax0` bridge branch | `Xi_hist` leads, but exact doctrine-level bridge is unfinished |
| exact `Ax0` cut branch | shell/interior-boundary leads doctrine-facingly; history-window leads executably |
| geometry-tied transport law for `Ax2` | representation law is clean, but full geometry locking is incomplete |
| full terrain laws beyond reduced products | current reduced equations do not yet close the whole terrain ledger |
| sub-operator-level sequencing for `Ax4` | terrain-level loop ordering is stronger than the operator-pair detail so far |

---

## 8. Do Not Smooth

- Do not let `Ax0` entropy math overwrite the rest of the axis substrate.
- Do not let `Ax3` geometry math get promoted into the root constraints.
- Do not conflate `Ax4` loop ordering with `Ax5` operator family.
- Do not let derived closures (`Ax1`, `Ax4`, `Ax6`) masquerade as primitive roots.
- Do not let older primitive/derived tables outrank the newer owner packets when they conflict.

Short read:

- the axis packet is fed by multiple math branches, not one
- `Ax0` is entropy-backed but still bridge/cut open
- `Ax3` is geometry-backed
- `Ax4` and `Ax5` are operator-backed
- `Ax1`, `Ax4`, and `Ax6` are the main derived closures in the current packet
