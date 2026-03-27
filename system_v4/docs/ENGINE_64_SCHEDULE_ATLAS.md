# ENGINE 64-SCHEDULE ATLAS

**Date:** 2026-03-27
**Status:** Chart surface. No prose. No smoothing.
**Grammar layers:** IGT (stage grammar) · Jung (operator grammar) · I Ching (schedule index)

> **Rule:** IGT gives the stage grammar. Jung gives the operator grammar. I Ching gives the 64-schedule grammar. They do not overlap. They do not redefine each other.

---

## 1. TERRAINS (8)

| # | Terrain | Topology | Flux | Engine family | Loop assignment |
|---|---|---|---|---|---|
| T1 | `Se-in` | Se | IN | Type-1 | both (outer + inner) |
| T2 | `Ne-in` | Ne | IN | Type-1 | both |
| T3 | `Ni-in` | Ni | IN | Type-1 | both |
| T4 | `Si-in` | Si | IN | Type-1 | both |
| T5 | `Se-out` | Se | OUT | Type-2 | both |
| T6 | `Ne-out` | Ne | OUT | Type-2 | both |
| T7 | `Ni-out` | Ni | OUT | Type-2 | both |
| T8 | `Si-out` | Si | OUT | Type-2 | both |

### Terrain graph edges

```
Ne ──Ax2── Se
│          │
Ax0        Ax0
│          │
Ni ──Ax2── Si
```

| Edge family | Edges |
|---|---|
| Ax0 | Se↔Si, Ne↔Ni |
| Ax2 | Se↔Ne, Si↔Ni |

---

## 2. SIGNED OPERATORS (8)

Each operator × Ax6 sign = distinct physical object (non-commuting composition order).

| # | Signed op | Base op | Ax6 | QIT meaning | Composition |
|---|---|---|---|---|---|
| O1 | `Ti↑` | Ti | UP | Projector before terrain | `Φ_T(U_Ti · ρ · U_Ti†)` |
| O2 | `Ti↓` | Ti | DOWN | Terrain before projector | `U_Ti · Φ_T(ρ) · U_Ti†` |
| O3 | `Fe↑` | Fe | UP | Diffuser before terrain | `Φ_T(L_Fe[ρ])` |
| O4 | `Fe↓` | Fe | DOWN | Terrain before diffuser | `L_Fe[Φ_T(ρ)]` |
| O5 | `Te↑` | Te | UP | Gradient before terrain | `Φ_T(-i[H,ρ])` |
| O6 | `Te↓` | Te | DOWN | Terrain before gradient | `-i[H, Φ_T(ρ)]` |
| O7 | `Fi↑` | Fi | UP | Filter before terrain | `Φ_T(F_Fi[ρ])` |
| O8 | `Fi↓` | Fi | DOWN | Terrain before filter | `F_Fi[Φ_T(ρ)]` |

---

## 3. SIXTEEN MACRO-STAGE ATLAS

### IGT layer (stage grammar)

| IGT quadrant | Topology | T-strategy | F-strategy |
|---|---|---|---|
| WinLose | Ne | NeTi | FiNe |
| WinWin | Si | SiTe | FeSi |
| LoseWin | Se | TiSe | SeFi |
| LoseLose | Ni | TeNi | NiFe |

### Type-1 (IN flux)

| Row | Engine | Loop | Step | Terrain | Jung token | Ax6 | Signed op | IGT result | Pattern |
|---|---|---|---|---|---|---|---|---|---|
| M01 | T1 | outer | 1 | Se-in | TiSe | UP | Ti↑ | LOSE | LOSEwin |
| M02 | T1 | outer | 2 | Ne-in | NeTi | DOWN | Ti↓ | WIN | WINlose |
| M03 | T1 | outer | 3 | Ni-in | NiFe | DOWN | Fe↓ | LOSE | loseLOSE |
| M04 | T1 | outer | 4 | Si-in | FeSi | UP | Fe↑ | WIN | winWIN |
| M05 | T1 | inner | 1 | Se-in | SeFi | DOWN | Fi↓ | win | LOSEwin |
| M06 | T1 | inner | 2 | Si-in | SiTe | DOWN | Te↓ | win | winWIN |
| M07 | T1 | inner | 3 | Ni-in | TeNi | UP | Te↑ | lose | loseLOSE |
| M08 | T1 | inner | 4 | Ne-in | FiNe | UP | Fi↑ | lose | WINlose |

### Type-2 (OUT flux)

| Row | Engine | Loop | Step | Terrain | Jung token | Ax6 | Signed op | IGT result | Pattern |
|---|---|---|---|---|---|---|---|---|---|
| M09 | T2 | outer | 1 | Se-out | FiSe | UP | Fi↑ | WIN | loseWIN |
| M10 | T2 | outer | 2 | Si-out | TeSi | UP | Te↑ | WIN | WINwin |
| M11 | T2 | outer | 3 | Ni-out | NiTe | DOWN | Te↓ | LOSE | LOSElose |
| M12 | T2 | outer | 4 | Ne-out | NeFi | DOWN | Fi↓ | LOSE | winLOSE |
| M13 | T2 | inner | 1 | Se-out | SeTi | DOWN | Ti↓ | lose | loseWIN |
| M14 | T2 | inner | 2 | Ne-out | TiNe | UP | Ti↑ | win | winLOSE |
| M15 | T2 | inner | 3 | Ni-out | FeNi | UP | Fe↑ | lose | LOSElose |
| M16 | T2 | inner | 4 | Si-out | SiFe | DOWN | Fe↓ | win | WINwin |

### Loop view (each loop in its own traversal order)

| Engine | Loop | Axis-4 | Order | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|---|---|---|---|---|---|---|---|
| T1 | outer | Deductive | Se→Ne→Ni→Si | `TiSe/Ti↑/LOSE` | `NeTi/Ti↓/WIN` | `NiFe/Fe↓/LOSE` | `FeSi/Fe↑/WIN` |
| T1 | inner | Inductive | Se→Si→Ni→Ne | `SeFi/Fi↓/win` | `SiTe/Te↓/win` | `TeNi/Te↑/lose` | `FiNe/Fi↑/lose` |
| T2 | outer | Inductive | Se→Si→Ni→Ne | `FiSe/Fi↑/WIN` | `TeSi/Te↑/WIN` | `NiTe/Te↓/LOSE` | `NeFi/Fi↓/LOSE` |
| T2 | inner | Deductive | Se→Ne→Ni→Si | `SeTi/Ti↓/lose` | `TiNe/Ti↑/win` | `FeNi/Fe↑/lose` | `SiFe/Fe↓/win` |

---

## 4. SIXTY-FOUR MICROSTEP SCHEDULE

Each macro-stage (M01–M16) runs 4 internal operator substeps in fixed order: Ti → Fe → Te → Fi.

`schedule_id = (macro_row - 1) × 4 + operator_position`

| Macro | Terrain | Token | Sub 1 (Ti) | Sub 2 (Fe) | Sub 3 (Te) | Sub 4 (Fi) |
|---|---|---|---|---|---|---|
| M01 | Se-in | TiSe/Ti↑ | S01: Ti | S02: Fe | S03: Te | S04: Fi |
| M02 | Ne-in | NeTi/Ti↓ | S05: Ti | S06: Fe | S07: Te | S08: Fi |
| M03 | Ni-in | NiFe/Fe↓ | S09: Ti | S10: Fe | S11: Te | S12: Fi |
| M04 | Si-in | FeSi/Fe↑ | S13: Ti | S14: Fe | S15: Te | S16: Fi |
| M05 | Se-in | SeFi/Fi↓ | S17: Ti | S18: Fe | S19: Te | S20: Fi |
| M06 | Si-in | SiTe/Te↓ | S21: Ti | S22: Fe | S23: Te | S24: Fi |
| M07 | Ni-in | TeNi/Te↑ | S25: Ti | S26: Fe | S27: Te | S28: Fi |
| M08 | Ne-in | FiNe/Fi↑ | S29: Ti | S30: Fe | S31: Te | S32: Fi |
| M09 | Se-out | FiSe/Fi↑ | S33: Ti | S34: Fe | S35: Te | S36: Fi |
| M10 | Si-out | TeSi/Te↑ | S37: Ti | S38: Fe | S39: Te | S40: Fi |
| M11 | Ni-out | NiTe/Te↓ | S41: Ti | S42: Fe | S43: Te | S44: Fi |
| M12 | Ne-out | NeFi/Fi↓ | S45: Ti | S46: Fe | S47: Te | S48: Fi |
| M13 | Se-out | SeTi/Ti↓ | S49: Ti | S50: Fe | S51: Te | S52: Fi |
| M14 | Ne-out | TiNe/Ti↑ | S53: Ti | S54: Fe | S55: Te | S56: Fi |
| M15 | Ni-out | FeNi/Fe↑ | S57: Ti | S58: Fe | S59: Te | S60: Fi |
| M16 | Si-out | SiFe/Fe↓ | S61: Ti | S62: Fe | S63: Te | S64: Fi |

**I Ching layer:** Each S01–S64 is one hexagram slot. The hexagram is the schedule index — it labels a unique executable microstep, not an ontological claim. Mapping of hexagram numbers to schedule IDs is a separate indexing task.

---

## 5. TOPOLOGY-ALIGNED COMPARISON

| Topology | T1 terrain | T1 outer token | T1 outer result | T1 inner token | T1 inner result | T2 terrain | T2 outer token | T2 outer result | T2 inner token | T2 inner result |
|---|---|---|---|---|---|---|---|---|---|---|
| Se | Se-in | TiSe/Ti↑ | LOSE | SeFi/Fi↓ | win | Se-out | FiSe/Fi↑ | WIN | SeTi/Ti↓ | lose |
| Ne | Ne-in | NeTi/Ti↓ | WIN | FiNe/Fi↑ | lose | Ne-out | NeFi/Fi↓ | LOSE | TiNe/Ti↑ | win |
| Ni | Ni-in | NiFe/Fe↓ | LOSE | TeNi/Te↑ | lose | Ni-out | NiTe/Te↓ | LOSE | FeNi/Fe↑ | lose |
| Si | Si-in | FeSi/Fe↑ | WIN | SiTe/Te↓ | win | Si-out | TeSi/Te↑ | WIN | SiFe/Fe↓ | win |

---

## 6. AXIS OVERLAY

| Axis | Grammar layer | What it governs | Partitions |
|---|---|---|---|
| Ax0 | Graph edge | Ne/Ni vs Se/Si | Terrain graph edge family |
| Ax1 | Graph edge (cross) | Se/Ni vs Ne/Si | Diagonal cross-pairs |
| Ax2 | Graph edge | Se/Ne vs Si/Ni | Terrain graph edge family |
| Ax3 | IGT | IN flux vs OUT flux | Engine type (T1 vs T2) |
| Ax4 | Jung | FeTi (deductive) vs TeFi (inductive) | Loop operator family assignment |
| Ax5 | IGT | First strategy (Te/Ti) vs second strategy (Fe/Fi) | T vs F kernel in IGT |
| Ax6 | Jung | UP (operator first) vs DOWN (terrain first) | Token composition order / signed op |

---

## 7. INVARIANTS

| Invariant | Value |
|---|---|
| Terrains per engine | 4 (all visited by both loops = 8 terrain-visits) |
| Macro-stages per engine | 8 (4 outer + 4 inner) |
| Microsteps per engine | 32 (8 × 4 operators) |
| Total microsteps | 64 (2 engines × 32) |
| WIN per engine | 2 |
| LOSE per engine | 2 |
| win per engine | 2 |
| lose per engine | 2 |
| Signed operators per engine | 8 (4 ops × 2 signs, one per macro-stage) |
| Terrains overlap between engines | 0 (IN set ∩ OUT set = ∅) |

---

## 8. QUARANTINE TABLE

| Tempting collapse | Why it's wrong |
|---|---|
| type = flow | Ax3 (flux direction) ≠ Ax4 (loop family). Both types have WIN/LOSE outer. |
| flow = chirality | Chirality is Left/Right Weyl. Flux IN/OUT is terrain-level. Different objects. |
| chirality = precedence | Precedence is Ax6 (UP/DOWN token order). Chirality is Ax3. Not interchangeable. |
| outer/inner = Ax3 | Both engines have outer (caps) and inner (lower). Ax3 is flux direction, not casing. |
| IGT labels = Jung pairings | IGT gives WIN/LOSE result. Jung gives operator token. Same stage, different grammar layers. |
| I Ching = ontology | Hexagrams label schedule slots. They are not proofs, not operator definitions, not stage results. |
| correlation = proof | Correlated axes suggest structure. They do not confirm it. All correlations stay A1 fuel. |
| schedule label = ontology | S01–S64 are execution indices. They do not define what the operators DO. |
| thermodynamics = literal | Heating/cooling, Carnot, Szilard are search-direction metaphors. These are QIT engines. |
| Ne1/Ne2 = *-in/*-out | Old terrain-variant scheme is superseded. Do not mix. |

---

## 9. GRAMMAR LAYER OWNERSHIP

| Layer | Owned by | NOT owned by |
|---|---|---|
| Stage results (WIN/LOSE/win/lose) | IGT | Jung, I Ching |
| Mixed vs same-sign patterns | IGT | Jung, I Ching |
| First/second strategy (T vs F) | IGT (Ax5) | Jung |
| Operator pairings (NeTi, FeSi…) | Jung | IGT, I Ching |
| FeTi vs TeFi (loop family) | Jung (Ax4) | IGT |
| UP vs DOWN (composition order) | Jung (Ax6) | IGT |
| 64-schedule slot identity | I Ching | IGT, Jung |
| Hexagram-to-microstep mapping | I Ching | IGT, Jung |
