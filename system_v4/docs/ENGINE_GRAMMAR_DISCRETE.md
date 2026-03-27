# [Controller-safe] Engine Grammar: Discrete Owned Slices

**Date:** 2026-03-27
**Status:** Extracted from canonical source docs. No synthesis across slices. Each slice is a separate, owned piece.
**Source:** `EM_BOOTPACK_v8_0_02_BUNDLE2_ROSETTA_ENGINES.md` (Rosetta Stone + Engines Spec v0.8 + Axis-1/Axis-2 Dual-Stack Szilard)

> **Anti-collapse rule:** Do not merge these slices. They are distinct grammar layers. A probe that conflates any two slices is already off-manifold.

---

## SLICE A: Spinor Carrier

**Primary state carrier:** Weyl spinor pair (ψ_L, ψ_R) on S³/SU(2) — Level 2–3 in the ratchet chain.

**Constraint manifold:** S³ / SU(2) carrier. Root constraints: F01_FINITUDE, N01_NONCOMMUTATION.

**Projection loss (what is destroyed at each step):**

| Projection | What is lost |
|---|---|
| Spinor → ρ_L (density) | U(1) phase: completely destroyed. SU(2)_R: invisible in ρ_L block. |
| Density → Bloch S² | SU(2)_L rotations: attenuated from 0.53 → 0.007 |
| Bloch → scalar | Parity survives (minimal loss) |

**Constraint-first rule:** Probes must inhabit the local chart. Test processes (loop integrals, path history, spinor-path). Do NOT use global static comparisons on ρ.

**Forbidden claims from density-level probes:**
- Cannot verify Ax3 (chirality/phase) — density erases phase
- Cannot claim Ax0 is a structural displacement (dephasing, partial trace, eigentruncation)
- Cannot claim geometric volume or U(1) phase properties

---

## SLICE B: Loop / Stage Grammar

**Loops per engine type:** 2 (outer/major + inner/minor). Outer/inner is NOT an axis — it is derived casing.

**Axis-4 governs:** Macro topology order ONLY (Deduction vs Induction). Not sign, not CW/CCW.

**Topology orders:**
- Deduction: `Ne → Si → Se → Ni`
- Induction: `Ne → Ni → Se → Si`

**Which loop runs which order:**

| Engine | Loop | Axis-4 stroke | Token sequence |
|---|---|---|---|
| Type-1 | Outer (major) | Deduction | `NeTi → FeSi → TiSe → NiFe` |
| Type-1 | Inner (minor) | Induction | `SeFi → SiTe → FiNe → TeNi` |
| Type-2 | Outer (major) | Induction | `FiSe → TeSi → NeFi → NiTe` |
| Type-2 | Inner (minor) | Deduction | `TiNe → SiFe → SeTi → FeNi` |

**Stages per loop:** 4 (macro-4)
**Stages per engine:** 8 macro (expandable to 32 micro via Ax6 substages)
**Heating/cooling:** Se = hot mixing ("heating leg"), Ni = cold reset ("cooling leg"). Each loop touches both Se and Ni.

---

## SLICE C: Terrain Ownership and Directional Flow

**4 base topologies and their QIT map classes:**

| Topology | QIT class | Thermodynamic role |
|---|---|---|
| Ne | Unitary transport (entropy-preserving) | Expansion / explore |
| Si | Pinching / dephasing | Stabilize / cooperate |
| Se | Hot mixing → τ_hot | Heating leg / heat-in-contact |
| Ni | Cold reset → τ_cold | Cooling leg / erasure-leg |

**8 terrains = 4 topologies × 2 flow directions:**

| Terrain | Base topology | Flow direction |
|---|---|---|
| Ne1 | Ne | U(θ) |
| Ne2 | Ne | U(−θ) — sign flip |
| Si1 | Si | Pinch in Z basis (or B₁) |
| Si2 | Si | Pinch in rotated basis B₂ (exploration marker) |
| Se1 | Se | Toward τ_hot^(1) |
| Se2 | Se | Toward τ_hot^(2) (exploration marker) |
| Ni1 | Ni | Toward τ_cold^(1) |
| Ni2 | Ni | Toward τ_cold^(2) (exploration marker) |

**Flux direction (allowed range, not pinned exactness):**
- Type-1 = sink-like (inward flux direction)
- Type-2 = source-like (outward flux direction)
- Ne1 vs Ne2 is pinned (sign flip). Si2/Se2/Ni2 variants are exploration markers for next pass.
- Do NOT pin the flux direction to a single exact formalization — explore the correlated range.

**Terrain ownership by loop** (from 16-macro-token table):
Every terrain appears in exactly one slot per engine — each loop visits all 4 base topologies, with flow direction set by engine chirality.

---

## SLICE D: Operator / Sign Grammar

**4 base operator families (QIT CPTP maps):**

| Operator | QIT map | Non-commutation |
|---|---|---|
| Ti | Z-pinching: (1−q)ρ + q·Π_Z(ρ) | Non-commutes with Te |
| Te | X-pinching: (1−q)ρ + q·Π_X(ρ) | Non-commutes with Ti |
| Fi | Unitary rotation about X: U_Fi·ρ·U_Fi† | — |
| Fe | Unitary rotation about Z: U_Fe·ρ·U_Fe† | — |

**Axis-6 governs:** Precedence (token composition order) ONLY.
- DOWN (Topo→Op): ρ' = (J ∘ P)(ρ) — topology applied first
- UP (Op→Topo): ρ' = (P ∘ J)(ρ) — operator applied first

**Token string encoding:**
- TopoOp → DOWN: `NeTi` = apply Ne then Ti
- OpTopo → UP: `TiNe` = apply Ti then Ne

**8 operator modes:** Ti↓, Ti↑, Te↓, Te↑, Fi↓, Fi↑, Fe↓, Fe↑
These are NOT intrinsic properties of the operator families — they are Axis-6 composition labels.

**Sign effects:** Axis-6 precedence CAN induce sign-flips in DERIVED witnesses (commutators, holonomy). Axis-6 itself is not ±.

**FORBIDDEN Axis-6 interpretations:**
- NOT induction/deduction (that is Axis-4)
- NOT CW/CCW (that is flow direction / terrain)
- NOT a direct ± toggle
- NOT implemented as negative channels

---

## SLICE E: 64-State Combinatorics

**Formation:** 8 terrains × 8 operator modes = 64 micro-configurations

**Ownership:**

| Unit | Owns | Shared? |
|---|---|---|
| Each engine type | 32 micro-configurations | No — disjoint |
| Each stage (base topology) | 16 micro-configurations | No — disjoint |
| Each macro-4 token | 1 micro-configuration per precedence | No |

**The 8×8 grid IS:** A lookup table — a dictionary of all possible (terrain, operator-mode) pairs.

**The 8×8 grid IS NOT:**
- The engine schedule (the schedule is a PATH through grid cells)
- A claim that the engine visits all 64 states equally
- A physics proof
- A closed canon

**Non-sharing constraint:** Microstates are disjoint across engine types and across stages by definition.

---

## SLICE F: Metaphor-to-Math Handles

**Jungian labels (Ti/Te/Fi/Fe, Ne/Si/Se/Ni) are:** Named handles for QIT map classes. "We keep Jung labels as names, but the math stays clean."

**Topology metaphors (pinned):**
- Ne = expansion/explore (WinLose)
- Si = stabilize/cooperate (WinWin)
- Se = tradeoff/exploit (LoseWin) — heating leg
- Ni = minimax survival (LoseLose) — cooling leg

**Carnot/Szilard:** The dual-stacked Szilard is a necessity claim (Type-1 + Type-2 as conjugate orientations bounding each other's winding). Exact thermodynamic accounting (which stroke maps to which Carnot cylinder) is explicitly OPEN until a full accounting layer is added. **Carnot/Szilard is inspiration and structural candidate, not canon equation.**

**Flux direction for terrains:** Ne1 vs Ne2 is pinned as a unitary sign flip. Si2/Se2/Ni2 variants are exploration ranges. Do NOT collapse all terrain-direction variation to one exact formalization.

**Taijitu / yin-yang:** Mnemonic and search-map only. Not a proof surface. Not primary mathematical ontology.

**EXPLICIT WARNINGS from docs:**
- "Do not drift into personality typing."
- "Keep metaphor layers downstream from the math rather than using them as proof surfaces."
- Picking single proxies for axes was "premature narrative smoothing."
- No axis currently has a locked canonical mathematical formulation.

---

## Minimal Stable Grammar (Cross-Slice Invariants)

These must be preserved by ANY future probe, doc, or sim:

1. **Spinors are first-class** — ψ_L / ψ_R on S³ are the engine's geometry. Density is a shadow.
2. **2 loops per engine type** — not 1. Outer = major, Inner = minor. Not an axis.
3. **4 stages per loop** — ordered. The 4-token sequences above are the macro-4 canon.
4. **Loop order inverts across types** — Type-1 outer = deduction, Type-2 outer = induction.
5. **8 terrains = 4 topologies × 2 flow directions** — flow direction differs by engine chirality.
6. **8 operator modes = 4 families × 2 Axis-6 precedences** — not intrinsic to operators.
7. **64 = 8 × 8, each engine owns 32, no sharing** — the grid is a lookup, not a schedule.
8. **Ax6 = precedence only** — sign effects are derived, never direct.
9. **Ax4 = topology order only** — deduction vs induction.
10. **All metaphor labels are handles, not proofs** — Carnot/Szilard is a candidate family, not canon.
