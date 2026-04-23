# Root To Axis 0 Entropy Handoff

**Date:** 2026-03-29  
**Status:** Strict handoff packet between root refinement/path entropy and the later cut-state `Ax0` kernel family.

---

## 1. Purpose

This file answers one question:

**How does the root negative-entropy story relate to the later `Ax0` story without collapsing them into the same object?**

The answer is:

- they are aligned
- they are not identical
- the later `Ax0` kernel is a retooling, not the primitive root form

---

## 2. Root Entropy Object

The root entropy packet is:

| Object | Pure math | Role |
|---|---|---|
| refinement multiplicity | \(\mu([x]) = |\mathcal R([x])|\) | admissible next-step count |
| path entropy | \(S(\gamma)=\sum_k \log \mu([x_k])\) | first legal entropy |
| derived state entropy | \(S([x])=\sup_{\gamma \text{ from } [x]} S(\gamma)\) | future possibility |
| entropy decrease under refinement | \([x]\preceq[y]\Rightarrow S([y])\le S([x])\) | root negative-entropy claim |
| entropy gradient | \(\Delta S\) | direction without time |
| i-scalar | \(i([x])=S([x])\) | global ordering functional |

This is:

- pre-geometry
- pre-probability
- pre-time
- pre-density-matrix

---

## 3. Late Axis 0 Kernel Object

The late `Ax0` packet is:

| Object | Pure math | Role |
|---|---|---|
| single-state entropy | \(S(\rho)=-\operatorname{Tr}(\rho\log\rho)\) | mixedness only |
| mutual information | \(I(A:B)\) | unsigned companion diagnostic |
| conditional entropy | \(S(A|B)\) | signed cut entropy |
| coherent information | \(I_c(A\rangle B)=-S(A|B)\) | strongest simple `Ax0` kernel |
| shell-cut coherent information | \(\sum_r w_r I_c(A_r\rangle B_r)\) | strongest current global `Ax0` family |

This is:

- cut-state based
- bridge dependent
- late-QIT

---

## 4. Alignment

These two layers align in a real way.

| Root layer | Late `Ax0` layer | Shared idea |
|---|---|---|
| refinement entropy | cut-state entropy/correlation | constrained distinguishability bookkeeping |
| entropy decrease under refinement | negative conditional entropy / coherent information | signed negative-entropy-like structure |
| path-dependent ordering | bridge-dependent cut-state evaluation | no free global scalar without structure |
| i-scalar ordering | `Ax0` field on chosen cut-state domain | ordering/gradient witness |

So your original intuition was right in spirit:

\[
\text{Axis 0 wants a negative-entropy-like object}
\]

But the mature QIT retool is:

\[
I_c(A\rangle B) = -S(A|B)
\]

not plain `S(\rho)` by itself.

---

## 5. Non-Identity

These are still not the same object.

| Root entropy | Late `Ax0` |
|---|---|
| defined on refinement classes and paths | defined on cut states \(\rho_{AB}\) |
| no density matrices required | density matrices required |
| no bridge required | bridge `Xi` required |
| no explicit bipartite cut required | cut `A|B` required |
| upstream of geometry | downstream of geometry and realization |

So:

\[
\text{root entropy} \neq Ax0
\]

even though root entropy is the strongest philosophical and mathematical ancestor of `Ax0`.

---

## 6. Retooling Rule

The safe retargeting rule is:

| Move | Allowed? | Read |
|---|---|---|
| root refinement entropy -> general negative-entropy intuition | yes | source-safe |
| root refinement entropy -> plain VN entropy as final answer | no | too collapsed |
| root refinement entropy -> coherent information as late QIT retool | yes | strongest current retool |
| root refinement entropy -> mutual information alone as final answer | no | unsigned only |
| root refinement entropy -> shell-cut coherent-information family | yes | strongest current global retool |

---

## 7. Current Best Read

The clean current handoff is:

1. Root negative entropy is first earned as refinement entropy decrease and path-entropy ordering.
2. That root story does not yet give `Ax0`.
3. The later finite-QIT realization retools that intuition into signed cut-state structure.
4. The strongest simple retool is:

\[
I_c(A\rangle B)=-S(A|B)
\]

5. The strongest global retool is:

\[
\sum_r w_r I_c(A_r\rangle B_r)
\]

6. Mutual information stays as the companion guardrail, not the lead kernel.

---

## 8. Do Not Smooth

- Do not say root entropy “already is” `Ax0`.
- Do not say `Ax0` is just von Neumann entropy.
- Do not let cut-state QIT language leak backward into the primitive root layer.
- Do not let root path/refinement entropy get erased just because the later kernel is cleaner operationally.
- Do not confuse alignment with identity.
