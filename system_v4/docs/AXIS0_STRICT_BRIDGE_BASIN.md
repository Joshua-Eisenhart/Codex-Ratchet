# Axis 0 Strict Bridge Basin

**Date:** 2026-03-29  
**Status:** SUPERSEDED. Older bridge-basin summary retained for audit context only. Do not cite as an active owner surface.  
**Superseded by:** [AXIS0_MANIFOLD_BRIDGE_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md), [AXIS0_BRIDGE_RELATION_PACKET.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_BRIDGE_RELATION_PACKET.md), and [AXIS0_BRIDGE_CLOSEOUT_CARD.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_BRIDGE_CLOSEOUT_CARD.md).  
**Purpose:** Keep a strict `Axis 0` bridge packet that only uses the strongest current surfaces and explicit `keep / kill / open` status.  
**Scope discipline:** This is not a geometry packet. It assumes the Hopf/Weyl geometry packet already exists and asks only what survives once `Axis 0` is treated as a cut-state functional.

---

## 1. Precedence Rule

- [AXIS0_ACTIVE_PACKET_INDEX.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_ACTIVE_PACKET_INDEX.md) is the compact entrypoint for the current active `Axis 0` packet stack; use it before reading this superseded basin note.

Use these surfaces first:

1. [axis0_full_constraint_manifold_guardrail_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_full_constraint_manifold_guardrail_sim.py)
2. [axis0_xi_strict_bakeoff_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_xi_strict_bakeoff_sim.py)
3. [AXIS_0_1_2_QIT_MATH.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_0_1_2_QIT_MATH.md)

Use these only as lower-authority working basin support:

1. [AXIS0_MANIFOLD_BRIDGE_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md)
2. [axis0_full_spectrum_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_full_spectrum_sim.py)

---

## 2. Kernel Basin

| Status | Candidate | Current read |
|---|---|---|
| `KEEP` | \(\Phi_0(\rho_{AB})=-S(A|B)_\rho=I_c(A\rangle B)_\rho\) | strongest simple signed kernel |
| `KEEP` | \(\Phi_0(\rho)=\sum_r w_r I_c(A_r\rangle B_r)_\rho\) | strongest global shell-cut family |
| `KEEP` | \(I(A:B)_\rho\) | companion diagnostic only |
| `KILL` | `I(A:B)` by itself as the full `Axis 0` primitive | unsigned, so not enough alone |
| `OPEN` | final ranking between pointwise, shell-cut, and history-shaped `Axis 0` forms | not yet unified |

Compact kernel read:

\[
\Phi_0 \approx -S(A|B)=I_c(A\rangle B)
\]

with

\[
I(A:B)
\]

as the main guardrail diagnostic.

---

## 3. Bridge Basin

| Status | Bridge object | Current read |
|---|---|---|
| `KEEP` | \(\Xi:\text{geometry/history}\to \rho_{AB}\) | bridge is required; geometry alone is not an `Axis 0` object |
| `KEEP` | `Xi_hist` family | strongest live history-family bridge |
| `KEEP` | point-reference pointwise bridge | strongest live pointwise discriminator |
| `KILL` | raw uncoupled `L|R` as a sufficient bridge | guardrail kill |
| `KILL` | shell-strata pointwise bridge | strict bakeoff kill |
| `KILL` | “geometry alone spontaneously creates nontrivial Axis 0” | guardrail kill |
| `OPEN` | strict shell-cut bridge that survives the stricter bakeoff | still missing |
| `OPEN` | final cut \(A|B\) | still unresolved |
| `OPEN` | final bridge factorization / codomain | still unresolved |

Core bridge law:

\[
\text{geometry} \neq \text{Axis 0}
\]

\[
\text{Axis 0} = \Phi_0(\rho_{AB}) \text{ after a bridge } \Xi
\]

Without `Xi`, you only have geometry, spinors, densities, and loops. You do not yet have the cut-state that `Axis 0` measures.

---

## 4. Strongest Strict Evidence

| Status | Surface | What it earns |
|---|---|---|
| `KEEP` | [axis0_full_constraint_manifold_guardrail_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_full_constraint_manifold_guardrail_sim.py) | real left/right Weyl geometry on nested Hopf tori with raw `L|R` readout stays trivial |
| `KEEP` | [axis0_xi_strict_bakeoff_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_xi_strict_bakeoff_sim.py) | direct `L|R` trivial, shell-strata killed, point-reference survives as pointwise discriminator, history stays live |
| `KEEP` | [AXIS_0_1_2_QIT_MATH.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_0_1_2_QIT_MATH.md) | strongest compact working lock for the `Axis 0` kernel family and bridge placeholder |
| `WORKING` | [AXIS0_MANIFOLD_BRIDGE_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md) | useful basin doc, but too optimistic in places relative to the strict bakeoff |

Strict result worth preserving:

\[
\text{real geometry} + \text{raw }L|R \Rightarrow \text{trivial Axis 0}
\]

\[
\text{real geometry} + \text{explicit }Xi \Rightarrow \text{working Axis 0-like candidates}
\]

---

## 5. Killed Closures

| Killed closure | Why it is killed |
|---|---|
| `Axis 0 = raw L:R mutual information on the live Hopf/Weyl engine` | raw `L|R` stays trivial on the strict surfaces |
| `Axis 0 = geometry by itself` | bridge remains required |
| `one naive shell pointwise bridge closes the problem` | shell-strata pointwise candidate dies in the strict bakeoff |
| `mutual information alone is the Axis 0 primitive` | unsigned and too weak by itself |
| `the bridge is already finished` | strict surfaces still leave `Xi`, the cut, and the factorization open |

---

## 6. Current Basin

| Layer | Best current read |
|---|---|
| geometry | already real and executable on the strong Hopf/Weyl surfaces |
| kernel | `-S(A|B)` strongest simple signed candidate |
| bridge | `Xi_hist` strongest live history family |
| pointwise discrimination | point-reference strongest live pointwise discriminator |
| unresolved | final `Xi`, final cut `A|B`, strict shell-cut family |

Shortest read:

- real geometry is already there
- raw uncoupled `L|R` is not enough
- `Axis 0` remains a bridge problem
- the bridge basin is narrowed, but not closed
