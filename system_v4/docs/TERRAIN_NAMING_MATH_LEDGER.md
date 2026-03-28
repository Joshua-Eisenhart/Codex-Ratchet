# TERRAIN NAMING AND MATH LEDGER

**Date:** 2026-03-27
**Status:** Source-grounded. Not a proposal — pulled from constraint ladder math.

**Source:** [Axis 1 2 topology math](file:///Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Axis%201%202%20topology%20math%CE%93%C3%87%C2%BF%CE%93%C3%87%C2%BF%CE%93%C3%87%C2%BFGood%20%CE%93%C3%87%C3%B6%20this%20is%20the%20right%20point%20to%20ask%20that%CE%93%C3%87%C2%AA.md) (constraint ladder)

---

## 4 base topologies — math-grounded

| Topology | Expansion / Compression | Ax1 class | Flow geometry | Generator form |
|---|---|---|---|---|
| **Se** | Expansion | Isothermal | Radial expansion (divergence > 0) | Dissipative Lindblad, entropy ↑ |
| **Ne** | Expansion | Adiabatic | Tangential circulation (div = 0) | Pure Hamiltonian `-i[H,ρ]`, entropy constant |
| **Ni** | Compression | Isothermal | Radial contraction (divergence < 0) | Dissipative Lindblad, entropy ↓ locally |
| **Si** | Compression | Adiabatic | Stratified retention (invariant strata) | Commuting `[H, P_i] = 0`, nested invariant subspaces |

---

## Feature matrix (from source, line 191)

| Feature | Se | Ne | Ni | Si |
|---|---|---|---|---|
| Lindblad dissipator | ✔ | ✗ | ✔ | ✗ |
| Hamiltonian flow | ✗ | ✔ | ✗ | ✔ |
| Divergence ≠ 0 | ✔ | ✗ | ✔ | ✗ |
| Attractors exist | ✗ | ✗ | ✔ | ✗ |
| Circulation | ✗ | ✔ | ✗ | ✗ |
| Invariant strata | ✗ | ✗ | ✗ | ✔ |
| Exists on S³ | ✔ | ✔ | ✔ | ✔ |

---

## Canonical 8 terrain names

**Source:** [axes math. apple notes dump.txt:8452](file:///Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a2_feed_high%20entropy%20doc/axes%20math.%20apple%20notes%20dump.txt) + constraint ladder line 19-23

| Topology | Constraint ladder name | T1 terrain (IN) | T2 terrain (OUT) | QIT effect |
|---|---|---|---|---|
| **Se** | Funnel / Cannon | **Inward funnel** | **Outward cannon** | Boundary-driven flow reversed |
| **Ne** | Vortex / Spiral | **Spiral-in** (vortex) | **Spiral-out** (vortex) | Phase correlation inverted |
| **Ni** | Pit / Source | **Pit** (collapse) | **Source** (emergence) | Predictive entropy inverted |
| **Si** | Hill / Citadel | **Hill** (accumulation) | **Basin** (release) | Entropy gradient reversed |

---

## Alias / conflict registry

| Topology | Canonical pair | Aliases in Apple Notes | Aliases in other docs | Notes |
|---|---|---|---|---|
| Se | funnel / cannon | gradient descent, damping, gradient funnel, inward funnel (mirrored swirl) | — | Cleanest pair. 5+ confirmations. |
| Ne | spiral / spiral | spiral mixing, spiral attractor, spiral-in vortex, spiral-out vortex, expanding spiral | vortex in constraint ladder | "Vortex" is used as modifier, not standalone name |
| Ni | pit / source | singular collapse, singular pit, deep vortex, twist/pit, source well, expansion pole, tight inner vortex | — | "Vortex" also used here (9840). Pit and vortex both appear. |
| Si | hill / basin | archive, stable basin, sink, archive pit, basin stabilization, fixed-point damping | **citadel** (constraint ladder only) | Most conflicted. "Basin" is canonical T2 name (8456) but user remembers "citadel" from constraint ladder. |

---

## What T1 vs T2 actually changes (math level)

**Source:** [axes math. apple notes dump.txt:9749-9849](file:///Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a2_feed_high%20entropy%20doc/axes%20math.%20apple%20notes%20dump.txt)

| Component | Same or different? |
|---|---|
| Lindblad operators (L_k) | **Same** — Se=σ_z, Si=σ_-, Ne=σ_x, Ni=σ_y |
| Hamiltonian | **Sign-flipped** — T1=+n·σ, T2=−n·σ |
| Dissipation | Same |
| Entropy production | Same |
| Lindblad spectrum | Same |
| Flow orientation | **Opposite** |

**Lock sentence** (line 9849): *"Type-1 and Type-2 terrains are identical Lindblad dissipative structures distinguished solely by opposite Weyl chirality of the Hamiltonian, resulting in mirrored unitary flow on the same four terrain geometries."*

---

## IGT gradient table (user-grounded)

The user's original insight: on closed terrains (Si/Ni), Te carries gradient ascent/descent and the casing (WIN/LOSE/win/lose) carries objective polarity.

| Token | Terrain | Motion | Outcome read |
|---|---|---|---|
| TeSi | Si hill | ascent (climb hierarchy) | WIN maximization |
| SiTe | Si hill | descent (enforce positions) | win minimization |
| TeNi | Ni pit | ascent (climb out) | lose minimization |
| NiTe | Ni pit | descent (map full space) | LOSE maximization |

**Rule:** geometric direction ≠ outcome polarity. They are different axes of meaning.

---

## Open naming questions

1. **Si-out**: "Basin" is the Apple Notes canonical name (line 8456). "Citadel" is the constraint ladder name. Which is authoritative?
2. **Ne vs Ni on "vortex"**: Both use "vortex" as a modifier in different blocks. The distinction is: Ne = tangential circulation (no attractor), Ni = radial collapse (has attractor). The vortex-like quality differs geometrically.
3. **Se-out "cannon"**: Only 2 confirmations. Solid but less anchored than "funnel" (5+).
