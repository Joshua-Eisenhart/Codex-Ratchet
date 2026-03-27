# [Controller-safe] Engine Grammar: Discrete Owned Slices

**Date:** 2026-03-27 (corrections added 2026-03-27)
**Status:** Extracted from canonical source docs + owner corrections. No synthesis across slices.
**Source:** `EM_BOOTPACK_v8_0_02_BUNDLE2_ROSETTA_ENGINES.md` + owner verbal corrections.

> **Anti-collapse rule:** Do not merge these slices. They are distinct grammar layers. A probe that conflates any two slices is already off-manifold.

---

## AXIS OWNER CORRECTIONS (take precedence over extracted spec)

### Ax0 — Correlation Entropy (not VN polarity)
**Owner definition:** Ax0 is **correlation entropy** — it can be **negative**. This is distinct from VN entropy and from the signed orientation framing in `ENGINES_SPEC.md` (which says N/S polarity of Φ(ρ)). Negative correlation entropy is a real and structurally meaningful state in a QIT engine. The `AXIS_STRUCTURE_EMPIRICAL_AUDIT.md` characterization ("fine/coarse-graining") is a density-layer probe result, not the owner definition.

### Ax5 — Actual Entropy Amount in the System (hot/cold)
**Owner definition:** Ax5 is the **actual amount of entropy** in the engine system at a given state — the "temperature" in a loose QIT sense, hot vs cold. This bends what was described as the yin-yang curvature line, which may correspond to a real QIT engine property (e.g., mixing parameter, bath temperature, or non-unitality depth). Ax5 is NOT dormant by default — prior probes showing it as dormant were running on insufficient drive amplitude. The `AXIS_STRUCTURE_EMPIRICAL_AUDIT.md` which merged Ax5 with Ax1 was doing density-layer probes; on the spinor constraint manifold these are likely distinct.

### Topology Repetition per Engine
**Owner definition:** Each loop visits ALL 4 perceiving topologies. Topologies appear **twice per engine** (outer + inner loop), differentiated by terrain flow-direction variant. This overrides any interpretation that the 4 topologies split 2/2 between the two loops.

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

**Topology orders — ⚠️ DISPUTED:**

> The order from `ENGINES_SPEC.md` is preserved below, but is flagged as likely thermodynamically incorrect.
> The user-proposed Carnot-grounded order is listed alongside as the probe candidate.
> Loop order should be verified by sim — since it is a cycle, starting position does not matter, only the traversal order does.

| | Spec (ENGINES_SPEC.md) | Proposed (Carnot-grounded, to sim) |
|---|---|---|
| Induction | `Ne → Ni → Se → Si` | `Se → Si → Ni → Ne` |
| Deduction | `Ne → Si → Se → Ni` | `Se → Ne → Ni → Si` |

**Proposed order rationale (QIT-native):** The hypothesis is that the structural sequence of QIT map classes matters — specifically: mixing channel (Se, non-unital toward τ_hot) → dephasing channel (Si, basis-stabilizing) → reset channel (Ni, non-unital toward τ_cold) → unitary transport (Ne, entropy-preserving) places the two non-unital channels (Se, Ni) in structurally opposed positions rather than adjacent, which may be required for the dual-stack to produce bounded winding. This is a probe candidate, not a thermodynamic claim. Carnot/thermodynamics is a search-direction metaphor only — these are QIT engines.

**Which loop runs which order (token sequences use ENGINES_SPEC order — subject to correction pending sim):**

| Engine | Loop | Axis-4 stroke | Token sequence |
|---|---|---|---|
| Type-1 | Outer (major) | Deduction | `NeTi → FeSi → TiSe → NiFe` |
| Type-1 | Inner (minor) | Induction | `SeFi → SiTe → FiNe → TeNi` |
| Type-2 | Outer (major) | Induction | `FiSe → TeSi → NeFi → NiTe` |
| Type-2 | Inner (minor) | Deduction | `TiNe → SiFe → SeTi → FeNi` |

**Stages per loop:** 4 (macro-4)
**Stages per engine:** 8 macro (expandable to 32 micro via Ax6 substages)
**Heating/cooling:** Se = hot mixing, Ni = cold reset. Each loop touches both Se and Ni.

**Topology repetition (owner correction):** Each loop visits ALL 4 perceiving topologies (Ne, Si, Se, Ni). The 4 base topologies therefore appear TWICE per engine — once in the outer loop, once in the inner loop. The two visits are distinguished by flow direction (terrain variant 1 vs 2). This means the 8 terrains split as: outer loop = {Ne1, Si1, Se1, Ni1} (or 2-variants), inner loop = {Ne2, Si2, Se2, Ni2} (or 1-variants), with assignment by engine chirality. NOT a 4/4 split by topology family.

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

**Terrain ownership by loop (corrected):**
- Each loop visits all 4 base topologies — Ne, Si, Se, Ni — in order
- The same 4 topology types appear in BOTH the outer and inner loop of each engine
- The two visits are distinguished by terrain flow-direction variant (1 vs 2)
- Outer loop gets one variant set, inner loop gets the other
- Assignment of which variant goes to which loop is set by engine chirality (Ax3)

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
3. **4 stages per loop** — ordered. Token sequences are recorded but topology traversal ORDER is disputed: the ENGINES_SPEC order may be thermodynamically incorrect. Correct order is a probe target (Carnot-grounded proposal: induction = Se→Si→Ni→Ne, deduction = Se→Ne→Ni→Si).
4. **Loop order inverts across types** — Type-1 outer = deduction, Type-2 outer = induction.
5. **8 terrains = 4 topologies × 2 flow directions** — flow direction differs by engine chirality.
6. **8 operator modes = 4 families × 2 Axis-6 precedences** — not intrinsic to operators.
7. **64 = 8 × 8, each engine owns 32, no sharing** — the grid is a lookup, not a schedule.
8. **Ax6 = precedence only** — sign effects are derived, never direct.
9. **Ax4 = topology order only** — deduction vs induction.
10. **All metaphor labels are handles, not proofs** — Carnot/Szilard is a candidate family, not canon.
