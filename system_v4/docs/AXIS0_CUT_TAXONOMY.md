# Axis 0 Cut Taxonomy

**Date:** 2026-03-29  
**Epistemic status:** Strict working owner packet for exact `Axis 0` cut candidates. This file is about the cut \(A|B\), not the bridge \(\Xi\). The `Axis 0` kernel family is source-backed. The exact doctrine-level cut is still open.

---

## 1. Scope And Status

This file answers:

- what counts as a legitimate `Axis 0` cut?
- which cut candidates are strongest now?
- which cuts are controls only?
- which cuts are killed or still unresolved?

It does **not** answer the separate bridge question by itself.

This file owns the history-window cut family, not the strict history bridge construction; bridge strictness stays in the `Xi_hist` owner packet.

Bridge owner packet:

- [AXIS0_MANIFOLD_BRIDGE_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md)
- [AXIS0_XI_HIST_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_XI_HIST_STRICT_OPTIONS.md)
- [AXIS0_ACTIVE_PACKET_INDEX.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_ACTIVE_PACKET_INDEX.md)

Upstream separation packet:

- [CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md)

---

## 2. Cut Contract

The minimum legitimate cut object is:

\[
\rho_{AB}\in \mathcal D(\mathcal H_A\otimes\mathcal H_B)
\]

with an explicit partition

\[
A|B
\]

on which the `Axis 0` kernel is evaluated.

### 2.1 Required conditions

| Requirement | Meaning |
|---|---|
| bipartite legitimacy | the cut must produce a real bipartite state \(\rho_{AB}\) |
| explicit partition | the two subsystems must be typed as \(A|B\) |
| kernel compatibility | the same cut must support \(S(A|B)\), \(I_c(A\rangle B)\), and/or \(I(A:B)\) |
| bridge realizability | at least one admissible bridge family must be able to land in that cut |
| notation safety | the cut naming should not collide with existing runtime meanings |

### 2.2 Minimal QIT core

\[
S(A|B)_\rho = S(\rho_{AB}) - S(\rho_B)
\]

\[
I_c(A\rangle B)_\rho = -S(A|B)_\rho
\]

\[
I(A:B)_\rho = S(\rho_A) + S(\rho_B) - S(\rho_{AB})
\]

So a cut is legitimate for `Axis 0` only if those quantities make sense on the same \(\rho_{AB}\).

---

## 3. Cut Family Table

| Cut family | Pure math shape | Current status | Why it matters |
|---|---|---|---|
| generic bipartite cut | \(A|B\) on \(\rho_{AB}\) | admitted abstract minimum | minimum QIT legitimacy |
| shell/interior-boundary cut | \(I_r|B_r\) or shell boundary/interior family | strongest doctrine-facing geometric-QIT family, still open | best match to shell-cut coherent-information family without forcing one exact shell algebra yet |
| history-window cut | \(A_t|B_t\) or \(cut\in C\) along \(\rho_h(t)\) | strongest live executable family | best fit to surviving `Xi_hist` behavior |
| point-reference cut | \(A_{\mathrm{ref}}|B_x\) or label/state cut induced by reference-vs-current pairing | open doctrine family, strongest live pointwise discriminator | best fit to surviving point-reference bridge |
| raw `L|R` cut | \(L|R\) on \(\rho_L\otimes\rho_R\) | control only | honest guardrail, but too weak alone |

---

## 4. Bridge Compatibility Matrix

| Cut family | `Xi_shell_strict` | `Xi_hist` | `Xi_ref` | raw `Xi_LR` |
|---|---|---|---|---|
| generic \(A|B\) | yes, abstractly | yes, abstractly | yes, abstractly | yes, abstractly |
| shell/interior-boundary | strongest intended fit | possible if history tracks shell cuts | weak fit | poor fit |
| history-window | weak fit unless shell histories are explicit | strongest fit | weak fit | poor fit |
| point-reference | weak fit | weak fit | strongest fit | poor fit |
| raw `L|R` | not intended | not intended | not intended | exact fit, but trivial as sufficient |

Interpretation:

- compatibility does not mean doctrine
- a family can fit a bridge abstractly while still failing executable tests

---

## 5. Admission Tests

| Test | Desired outcome | Kill condition |
|---|---|---|
| bipartite legitimacy | valid \(\rho_{AB}\) exists | no real bipartite state |
| nontriviality | cut can support nonzero \(I(A:B)\) under a live bridge family | identically trivial on its only intended bridge |
| signed-kernel fit | works naturally with \(-S(A|B)\) / \(I_c\) | only meaningful for unsigned diagnostics |
| geometry sensitivity | if it claims geometric meaning, it must respond to real geometry differences | geometry-blind |
| history sensitivity | if it claims history meaning, it must differ across real history windows | history-blind |
| notation safety | no symbol collision with runtime repo objects | overloaded names like `rho_LR` in conflicting roles |
| bridge naturalness | cut matches one surviving bridge family without extra ontology imports | only works after inventing extra ungrounded machinery |
| least arbitrariness | cut has a natural interpretation that buys real evidential gain over a simpler live family | survives only by a bookkeeping split with no added explanatory power |

### 5.1 Practical kill reads

- Kill any doctrine claim that equates the final cut with raw local `L|R`.
- Kill any cut family that only re-labels geometry coordinates as if they were bipartite subsystems.
- Kill any cut family that cannot pair naturally with `Xi_hist`, `Xi_ref`, or a future strict shell bridge.
- Kill any cut family that makes coherent information impossible in principle.

---

## 6. Current Candidate Ranking

| Rank | Cut candidate | Status | Reason |
|---|---|---|---|
| 1 | shell/interior-boundary cut | strongest doctrine-facing family, still open | best match to shell-cut coherent-information family and bookkeeping language, but not yet one exact executable cut or current carrier winner |
| 2 | history-window cut | strongest live executable cut family | best aligned with surviving `Xi_hist` behavior |
| 3 | generic \(A|B\) | safest abstract fallback | always legitimate, but too abstract to finish doctrine |
| 4 | point-reference cut | point-reference currently ranks as secondary open cut family, strongest live pointwise discriminator | useful executable separator, but not yet doctrine |
| 5 | raw `L|R` cut | control only | real and simple, but too weak as the final `Axis 0` cut |

### 6.1 Current strict-cut read

- shell/interior-boundary remains the strongest doctrine-facing cut family, but that does not mean shell is the strongest executable or constructive bridge winner on the current carrier
- history-window remains the strongest live executable cut family
- point-reference remains the strongest live pointwise discriminator
- the strongest exploratory constructive bridge family is cross-temporal chiral with Weyl/chirality weighting, which pressures bridge construction but does not close the doctrine-level cut
- the fixed-marginal preserving lane is certified near-zero on the current carrier, so raw bridge wins cannot be overread as earned cut closure

### 6.2 Strict shell/interior-boundary read

The strongest doctrine-facing shell read is still not one finished executable formula. It is a family shape.

| Shell object | Current read | Status |
|---|---|---|
| shell band / shell index \(r\) | radial or shell-like partition label used in the global cut family | live family symbol, exact algebra still open |
| boundary/interior split \(I_r|B_r\) | interior vs boundary cut attached to shell \(r\) | strongest doctrine-facing cut family |
| shell-cut weighted family | \(\Phi_0(\rho)=\sum_r w_r\, I_c(A_r\rangle B_r)_\rho\) | strongest screenshot-backed global form |
| ring / shell gradient language | geometric-overlay language for how the shell family is visualized | overlay only, not the cut by itself |
| shell-strata pointwise shortcut | old pointwise shell implementation | killed as strict pointwise solution |

So the clean shell read is:

\[
\text{shell doctrine} \approx \{(r,w_r,A_r|B_r)\}_r
\]

with global evaluation

\[
\Phi_0(\rho)=\sum_r w_r\, I_c(A_r\rangle B_r)_\rho
\]

but without yet claiming one final microscopic shell algebra for \(A_r|B_r\).

### 6.3 What a strict shell cut must satisfy

| Requirement | Why it matters | Kill read |
|---|---|---|
| real bipartite cut per shell | each shell contribution must still be a legitimate cut-state term | shell label without a real \(A_r|B_r\) split |
| shell sensitivity | changing shell structure should matter | shell-blind constant readout |
| nontriviality beyond raw local `L|R` | shell language must buy something real over the guardrail control | collapses back to trivial `L|R` |
| compatibility with coherent information | shell doctrine is strongest precisely because it matches \(I_c\) language | only supports unsigned diagnostics |
| distinction from pointwise shortcut | global shell family must not be confused with the killed shell-strata pointwise bridge | old pointwise shell code rebranded as doctrine |
| bridge compatibility | a future strict `Xi_shell` must be able to land in it naturally | requires extra ungrounded bookkeeping to make the cut exist |

### 6.4 Current shell verdict

| Item | Verdict |
|---|---|
| shell/interior-boundary as a cut family | `KEEP` |
| shell-cut coherent-information sum as the strongest global shell form | `KEEP` |
| exact shell algebra for \(A_r|B_r\) | `OPEN` |
| old shell-strata pointwise implementation | `KILL` as strict shell solution |
| shell imagery by itself | `KILL` as kernel math |

Strict shell bridge replacement packet:

- [AXIS0_XI_SHELL_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_XI_SHELL_STRICT_OPTIONS.md)

Strict history bridge packet:

- [AXIS0_XI_HIST_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_XI_HIST_STRICT_OPTIONS.md)

Typed history-window cut contract:

- [AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md)

Typed shell cut contract:

- [AXIS0_TYPED_SHELL_CUT_CONTRACT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_TYPED_SHELL_CUT_CONTRACT.md)

Shell algebra option-space owner:

- [AXIS0_SHELL_ALGEBRA_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_SHELL_ALGEBRA_STRICT_OPTIONS.md)

Boundary/interior micro option-space owner:

- [AXIS0_SHELL_BOUNDARY_INTERIOR_MICRO_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_SHELL_BOUNDARY_INTERIOR_MICRO_OPTIONS.md)

Strict point-reference packet:

- [AXIS0_XI_REF_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_XI_REF_STRICT_OPTIONS.md)

Point-reference owner handoff:

- owner packet for point-reference cut-role tightening: [AXIS0_XI_REF_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_XI_REF_STRICT_OPTIONS.md)

Bridge relation packet:

- [AXIS0_BRIDGE_RELATION_PACKET.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_BRIDGE_RELATION_PACKET.md)

---

## 7. Killed Or Demoted Cuts

| Candidate | Verdict | Why |
|---|---|---|
| single-spinor “cut” | killed | not bipartite |
| single reduced density \(\rho(\psi)\) | killed | not bipartite |
| raw \(\eta\)-only split | killed as cut | coordinate only, not a cut-state |
| uncoupled pure product \(L|R\) as final doctrine cut | demoted to control | guardrail shows it stays correlation-trivial by itself |
| old shell-strata pointwise cut | killed as strict pointwise shell solution | strict bakeoff shows it is loop-blind / geometry-blind in the required sense |

---

## 8. Runtime Collision Warnings

| Object | Why dangerous |
|---|---|
| `rho_LR` | already used in repo probes for an inter-chirality coherence block; do not reuse as the generic final `Axis 0` cut-state symbol |
| runtime `GA0` | proxy readout, not the same thing as an exact cut definition |
| shell-label register constructions | can be useful bridge scaffolds, but they are not automatically the final shell/interior cut doctrine |

---

## 9. Current Verdict

The strongest current doctrine-facing cut candidate is:

\[
I_r|B_r
\]

as a shell/interior-boundary family.

The strongest live executable cut family is:

\[
\text{history-window cut}
\]

because it aligns best with surviving `Xi_hist`.

The safest abstract fallback is:

\[
A|B
\]

until one doctrine-level cut wins.

The clean control is:

\[
L|R
\]

but only as a guardrail, not as the final answer.

Short read:

- `L|R` is too weak, but still required as the guardrail.
- history-window is the strongest live executable family.
- shell/interior-boundary is the strongest doctrine-facing family, but still needs an exact strict realization.
- point-reference is valuable because it survives the fiber/base discriminator, but that still does not make it the final cut.

---

## 10. Open Items

| Open item | Why it remains open |
|---|---|
| exact doctrine-level cut | shell/interior-boundary is strongest, but not yet fully closed |
| exact shell algebra | still needed before shell/interior-boundary becomes fully executable |
| history-window cut formalization | strongest live executable family; typed target contract now exists, but exact family \(C\) and exact \(\rho_c(t)\) construction remain open |
| relation between point-reference and doctrine cut | good discriminator, unclear doctrinal role |
| bridge-to-cut locking | surviving bridge families still need to be tied to one exact cut cleanly |
| exact strict shell-cut replacement | still needed after the old shell-strata pointwise failure |

---

## 11. Do Not Smooth

- Do not confuse the bridge \(\Xi\) with the cut \(A|B\).
- Do not confuse shell-label scaffolds with a finished shell/interior-boundary doctrine cut.
- Do not promote raw `L|R` from control to final answer.
- Do not reuse `rho_LR` as if it were already the generic `Axis 0` cut-state symbol.
- Do not confuse point-reference discrimination with the final cut taxonomy.
