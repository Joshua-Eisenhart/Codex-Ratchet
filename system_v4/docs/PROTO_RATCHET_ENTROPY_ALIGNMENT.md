# Proto-Ratchet Entropy Alignment

**Date:** 2026-03-29  
**Status:** Compact proto-ratchet alignment surface. Canon, working, and proxy distinctions stay explicit. This file only answers one question:

**Which entropy families align with the constraint-first ratchet, which can be retooled, which stay diagnostic, and which meanings stay forbidden at base?**

---

## 1. Root Semantic Guardrails

Entropic monism is not "everything is entropy."

The root claim is:

- there is only one primitive substance: constraint on distinguishability
- information is constraint bookkeeping
- geometry is constraint compatibility
- identity is emergent equivalence under constraint
- equality must be ratcheted, not assumed

So:

- entropy is allowed only as a measure of distinguishability under constraint
- most mathematics is illegal as a starting point if it assumes identity, infinity, or free structure
- entropy as heat is forbidden at base
- entropy as time is forbidden at base
- entropy as substance is forbidden at base
- entropy as optimization objective is forbidden at base

The first admissible entropy-like meanings are therefore:

| Base meaning | Status | Why it survives |
|---|---|---|
| count of admissible refinements | proto-foundational | earliest witness of constrained possibility |
| bookkeeping of equivalence classes | proto-foundational | compatible with emergent identity rather than primitive sameness |
| measure of correlation constraint | late-admitted | requires cut-state math first |
| conditional entropy, including negative values | late-admitted | strongest simple signed QIT retool once cut states exist |
| relative entropy between admissible states | late-admitted | valid comparison family after state space and references are admitted |

The entropy family is downstream of the bridge and the cut.

`Ax0` is not a root-layer entropy claim.

Without `Xi`, you do not yet have the bipartite cut-state that `Ax0` measures.

---

## 2. Entropy Families In Play

| Family | Pure math | Status | Best current use |
|---|---|---|---|
| refinement multiplicity | \(\mu([x]) = |\mathcal R([x])|\) | **Proto foundation** | smallest legal entropy-like seed before geometry or probability |
| path entropy | \(S(\gamma)=\sum_k \log \mu([x_k])\) | **Proto foundation** | first path-sensitive entropy over admissible refinement chains |
| derived state entropy | \(S([x])=\sup_{\gamma \text{ from } [x]} S(\gamma)\) | **Proto foundation** | future-refinement capacity / downstream possibility |
| refinement entropy gradient | \(\Delta S = S([x_{k+1}]) - S([x_k])\) | **Proto foundation** | root source of negative-entropy-gradient language |
| i-scalar ordering functional | \(i([x]) = S([x])\) | **Proto foundation** | early ordering scalar in the constraint ladder, not the late QIT `Ax0` kernel |
| von Neumann entropy | \(S(\rho) = -\mathrm{Tr}(\rho \log \rho)\) | **Working / late-derived** | single-state mixedness, not a signed Axis-0 primitive by itself |
| mutual information | \(I(A:B)_\rho = S(\rho_A) + S(\rho_B) - S(\rho_{AB})\) | **Working diagnostic** | total-correlation guardrail, companion quantity |
| conditional entropy | \(S(A|B)_\rho = S(\rho_{AB}) - S(\rho_B)\) | **Working / late-derived** | signed cut entropy, can go negative |
| coherent information | \(I_c(A\rangle B)_\rho = -S(A|B)_\rho = S(\rho_B) - S(\rho_{AB})\) | **Working strongest candidate** | strongest simple signed entropy primitive for `Ax0` |
| relative entropy | \(D(\rho\|\sigma)\) | **Working / late-derived** | comparison between admissible states or shells |
| refinement entropy / path entropy | entropy-like count over admissible refinements | **Proto foundation** | constraint-first ordering and path cost, before geometry |
| MI-distribution entropy | entropy of the pairwise MI weight distribution | **Working / proxy** | spread-vs-localization diagnostic |
| boundary bookkeeping deltas | \(\Delta I\), \(\Delta S\), reconstruction error | **Proxy** | useful for shell/boundary tests, not final kernel by itself |

Short read:

- the root program admits entropy only after constraints and admissible math exist
- von Neumann entropy is derived, not root semantics
- mutual information is contextual, not root semantics
- coherent information is contextual, not root semantics
- mutual information or coherent information as root semantics is not admitted
- the strongest signed candidate is still `-S(A|B) = I_c`
- mutual information stays important, but only as a companion diagnostic

---

## 3. Constraint-Safe Ranking

This is the current ratchet-safe ranking for entropy families.

| Rank | Family | Status | Why it ranks here |
|---|---|---|---|
| 1 | \(I_c(A\rangle B) = -S(A|B)\) | **Working strongest candidate** | signed, cut-based, can go negative, and matches the current `Ax0` basin |
| 2 | \(\sum_r w_r I_c(A_r\rangle B_r)\) | **Working/source-backed** | strongest shell-cut global form, aligns with the bridge family story |
| 3 | \(I(A:B)\) | **Working diagnostic** | good guardrail and correlation checker, but unsigned |
| 4 | \(S(\rho)\) | **Working / late-derived** | useful single-state mixedness, but too weak to stand alone for `Ax0` |
| 5 | \(D(\rho\|\sigma)\) | **Working / late-derived** | good comparison functional, but depends on a chosen reference family |
| 6 | entropy of MI distribution | **Proxy** | helps distinguish spread vs concentration, but is secondary |

Constraint-safe rule:

- if the family cannot go negative where the live probes need sign, it is not the primary `Ax0` kernel
- if the family only measures one-state mixedness, it is diagnostic, not the bridge
- if the family requires a chosen reference or coarse-graining, it is a proxy until the bridge is fixed

---

## 4. What Can Be Retooled

These families can be retooled into the proto-ratchet without pretending they are already final doctrine.

| Family | Retool target | Notes |
|---|---|---|
| mutual information | companion guardrail for cut-state families | keep it as the total-correlation check around the signed kernel |
| conditional entropy | signed cut functional | this is already close to the current strong candidate |
| coherent information | primary signed kernel | best simple retooling target for `Ax0` |
| relative entropy | shell comparison / reference sensitivity | useful for strict shell or boundary alignment |
| MI distribution entropy | localization/spread selector | useful for allostatic vs homeostatic response tests |
| boundary bookkeeping deltas | shell vs reconstruction proxy | useful for strict bridge tests, not the kernel itself |
| refinement entropy / path entropy | ordering cost over admissible refinements | root entropy object; can be retooled into path-based admission logic before full geometry |

Retooling rule:

- retool toward cut-state sensitivity, not toward generic “more entropy” language
- retool toward signed response, not just magnitude
- retool toward admissible refinement structure, not unbounded continuum metaphors
- do not let density language masquerade as the primitive root output

---

## 5. What Stays Diagnostic

These should remain diagnostic or proxy-only unless later ratcheting earns them more.

| Family | Status | Why it stays diagnostic |
|---|---|---|
| von Neumann entropy on a single state | **Diagnostic** | measures mixedness, but not correlation sign by itself |
| mutual information alone | **Diagnostic** | unsigned and not sufficient as the primary signed `Ax0` primitive |
| boundary bookkeeping deltas | **Proxy** | good for reconstruction tests, not a final ontology |
| MI distribution entropy | **Proxy** | helpful for spread-vs-localization, but secondary |
| runtime entropy proxies | **Proxy** | useful executable signals, but not doctrine |

Diagnostic rule:

- diagnostic means useful for discrimination and kill tests
- diagnostic does not mean final kernel
- proxy does not mean false; it means not yet source-closed as doctrine

---

## 6. Forbidden Base Meanings

These meanings stay forbidden at base admission.

| Forbidden meaning | Why it stays forbidden |
|---|---|
| entropy as heat | smuggles thermodynamic interpretation too early |
| entropy as time | smuggles chronology into the kernel layer |
| entropy as substance | violates constraint-first framing |
| entropy as optimization objective | turns a witness functional into a teleology |
| entropy as primitive geometry | geometry is downstream of constraints, not the root meaning |
| entropy as “everything is entropy” | the deeper claim is constraint on distinguishability, not generic entropy monism |

Base meaning rule:

- entropy is an operational quantity first
- entropy may later become a geometry or flow witness
- entropy is not allowed to define the whole ontology at the root layer

---

## 7. Working Read Order

Use this order if you need to continue the entropy ratchet from here:

1. [PROTO_RATCHET_ROOT_TO_ALLOWED_MATH_HANDOFF.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_ROOT_TO_ALLOWED_MATH_HANDOFF.md)
2. [PROTO_RATCHET_GEOMETRY_HANDOFF_CARD.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_GEOMETRY_HANDOFF_CARD.md)
3. [PROTO_RATCHET_FOUR_SURFACES.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_FOUR_SURFACES.md)
4. [CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md)
5. [AXIS0_STRICT_BRIDGE_BASIN.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_STRICT_BRIDGE_BASIN.md)
6. [AXIS0_MANIFOLD_BRIDGE_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md)

Short read:

- root constraints admit a narrow operational entropy vocabulary
- root negative-entropy language lives first in refinement/path entropy, not in late QIT cut-state kernels
- `I_c = -S(A|B)` is the strongest simple signed candidate
- mutual information stays as a companion diagnostic
- heat/time/substance/optimization meanings stay forbidden at base
