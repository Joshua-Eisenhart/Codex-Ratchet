# ENGINE 64-SCHEDULE ATLAS

**Date:** 2026-03-27
**Status:** Scaffold chart. Not runtime closure. Not final authority. Earned by chart alignment, not by proof.

> **Governing split:** IGT = stage grammar. Jung = operator grammar. I Ching = 64-schedule index. They do not overlap. They do not redefine each other.

| System | Job | Must not do |
|---|---|---|
| `IGT` | lock `WIN / LOSE / win / lose`, same-sign vs mixed, outer vs inner, first vs second asymmetry | redefine operator order or hexagram semantics |
| `Jung` | name ordered pair tokens, loop families, and signed operators | replace IGT outcome structure |
| `I Ching` | index the 64-slot schedule atlas | define runtime truth, line meanings, or axis closure |

---

## 1. GLOBAL LOCKS

| Layer | Type-1 | Type-2 |
|---|---|---|
| Flux | `IN` | `OUT` |
| Major / Outer casing | `WIN / LOSE` | `WIN / LOSE` |
| Minor / Inner casing | `win / lose` | `win / lose` |
| Outer loop family | Deductive `FeTi` | Inductive `TeFi` |
| Inner loop family | Inductive `TeFi` | Deductive `FeTi` |

---

## 2. IGT QUADRANT LOCK

| Topology | IGT quadrant | T-strategy | F-strategy | T1 major | T1 minor | T2 major | T2 minor |
|---|---|---|---|---|---|---|---|
| `Ne` | `WinLose` | NeTi | FiNe | `NeTi → WIN` | `FiNe → lose` | `NeFi → LOSE` | `TiNe → win` |
| `Si` | `WinWin` | SiTe | FeSi | `FeSi → WIN` | `SiTe → win` | `TeSi → WIN` | `SiFe → win` |
| `Se` | `LoseWin` | TiSe | SeFi | `TiSe → LOSE` | `SeFi → win` | `FiSe → WIN` | `SeTi → lose` |
| `Ni` | `LoseLose` | TeNi | NiFe | `NiFe → LOSE` | `TeNi → lose` | `NiTe → LOSE` | `FeNi → lose` |

---

## 3. LOOP ORDERS (Ax0/Ax2 graph-derived)

```
Ne ──Ax2── Se
│          │
Ax0        Ax0
│          │
Ni ──Ax2── Si
```

| Axis 4 family | Order |
|---|---|
| Inductive | `Se → Si → Ni → Ne` |
| Deductive | `Se → Ne → Ni → Si` |

| Edge family | Edges |
|---|---|
| `Ax0` | `Se-Si`, `Ne-Ni` |
| `Ax2` | `Se-Ne`, `Si-Ni` |

| Loop | Edge walk |
|---|---|
| Inductive `Se → Si → Ni → Ne` | `Ax0 → Ax2 → Ax0 → Ax2` |
| Deductive `Se → Ne → Ni → Si` | `Ax2 → Ax0 → Ax2 → Ax0` |

---

## 4. TERRAINS (8)

| # | Terrain | Topology | Flux | Engine family |
|---|---|---|---|---|
| T1 | `Se-in` | Se | IN | Type-1 |
| T2 | `Ne-in` | Ne | IN | Type-1 |
| T3 | `Ni-in` | Ni | IN | Type-1 |
| T4 | `Si-in` | Si | IN | Type-1 |
| T5 | `Se-out` | Se | OUT | Type-2 |
| T6 | `Si-out` | Si | OUT | Type-2 |
| T7 | `Ni-out` | Ni | OUT | Type-2 |
| T8 | `Ne-out` | Ne | OUT | Type-2 |

---

## 5. SIGNED OPERATORS (8)

`UP` = operator first. `DOWN` = terrain first. Non-commuting: `Φ_T ∘ U_O ≠ U_O ∘ Φ_T`.

| # | Signed op | Ax6 | Token examples | Role surface |
|---|---|---|---|---|
| O1 | `Ti↑` | UP | `TiSe`, `TiNe` | T1 major `Se`; T2 minor `Ne` |
| O2 | `Ti↓` | DOWN | `NeTi`, `SeTi` | T1 major `Ne`; T2 minor `Se` |
| O3 | `Fe↑` | UP | `FeSi`, `FeNi` | T1 major `Si`; T2 minor `Ni` |
| O4 | `Fe↓` | DOWN | `NiFe`, `SiFe` | T1 major `Ni`; T2 minor `Si` |
| O5 | `Te↑` | UP | `TeNi`, `TeSi` | T1 minor `Ni`; T2 major `Si` |
| O6 | `Te↓` | DOWN | `SiTe`, `NiTe` | T1 minor `Si`; T2 major `Ni` |
| O7 | `Fi↑` | UP | `FiNe`, `FiSe` | T1 minor `Ne`; T2 major `Se` |
| O8 | `Fi↓` | DOWN | `SeFi`, `NeFi` | T1 minor `Se`; T2 major `Ne` |

---

## 6. TYPE-1 FULL CHART (IN flux)

| Step | Topology | Terrain | Outer / Major | Ax6 | Signed op | Outer result | Inner / Minor | Ax6 | Signed op | Inner result | Pattern |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `Se` | `Se-in` | `TiSe` | `UP` | `Ti↑` | `LOSE` | `SeFi` | `DOWN` | `Fi↓` | `win` | `LOSEwin` |
| 2 | `Ne` | `Ne-in` | `NeTi` | `DOWN` | `Ti↓` | `WIN` | `FiNe` | `UP` | `Fi↑` | `lose` | `WINlose` |
| 3 | `Ni` | `Ni-in` | `NiFe` | `DOWN` | `Fe↓` | `LOSE` | `TeNi` | `UP` | `Te↑` | `lose` | `loseLOSE` |
| 4 | `Si` | `Si-in` | `FeSi` | `UP` | `Fe↑` | `WIN` | `SiTe` | `DOWN` | `Te↓` | `win` | `winWIN` |

### Type-1 loop view

| Loop | Order | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|---|---|---|---|---|---|
| Outer / Major | Deductive | `Se-in : TiSe : LOSE` | `Ne-in : NeTi : WIN` | `Ni-in : NiFe : LOSE` | `Si-in : FeSi : WIN` |
| Inner / Minor | Inductive | `Se-in : SeFi : win` | `Si-in : SiTe : win` | `Ni-in : TeNi : lose` | `Ne-in : FiNe : lose` |

---

## 7. TYPE-2 FULL CHART (OUT flux)

| Step | Topology | Terrain | Outer / Major | Ax6 | Signed op | Outer result | Inner / Minor | Ax6 | Signed op | Inner result | Pattern |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `Se` | `Se-out` | `FiSe` | `UP` | `Fi↑` | `WIN` | `SeTi` | `DOWN` | `Ti↓` | `lose` | `loseWIN` |
| 2 | `Si` | `Si-out` | `TeSi` | `UP` | `Te↑` | `WIN` | `SiFe` | `DOWN` | `Fe↓` | `win` | `WINwin` |
| 3 | `Ni` | `Ni-out` | `NiTe` | `DOWN` | `Te↓` | `LOSE` | `FeNi` | `UP` | `Fe↑` | `lose` | `LOSElose` |
| 4 | `Ne` | `Ne-out` | `NeFi` | `DOWN` | `Fi↓` | `LOSE` | `TiNe` | `UP` | `Ti↑` | `win` | `winLOSE` |

### Type-2 loop view

| Loop | Order | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|---|---|---|---|---|---|
| Outer / Major | Inductive | `Se-out : FiSe : WIN` | `Si-out : TeSi : WIN` | `Ni-out : NiTe : LOSE` | `Ne-out : NeFi : LOSE` |
| Inner / Minor | Deductive | `Se-out : SeTi : lose` | `Ne-out : TiNe : win` | `Ni-out : FeNi : lose` | `Si-out : SiFe : win` |

---

## 8. TOPOLOGY-ALIGNED COMPARISON

| Topology | T1 terrain | T1 major | T1 minor | T2 terrain | T2 major | T2 minor |
|---|---|---|---|---|---|---|
| `Se` | `Se-in` | `TiSe / LOSE / Ti↑` | `SeFi / win / Fi↓` | `Se-out` | `FiSe / WIN / Fi↑` | `SeTi / lose / Ti↓` |
| `Ne` | `Ne-in` | `NeTi / WIN / Ti↓` | `FiNe / lose / Fi↑` | `Ne-out` | `NeFi / LOSE / Fi↓` | `TiNe / win / Ti↑` |
| `Ni` | `Ni-in` | `NiFe / LOSE / Fe↓` | `TeNi / lose / Te↑` | `Ni-out` | `NiTe / LOSE / Te↓` | `FeNi / lose / Fe↑` |
| `Si` | `Si-in` | `FeSi / WIN / Fe↑` | `SiTe / win / Te↓` | `Si-out` | `TeSi / WIN / Te↑` | `SiFe / win / Fe↓` |

---

## 9. 64-LAYER SPLIT

| Layer | Safe use now | Must not claim |
|---|---|---|
| Live runtime `64` | `2 engines × 8 terrains × 4 operator slots` | full signed-operator closure or hexagram equivalence |
| Chart atlas `64` | `8 terrains × 8 signed operators` as schedule-index surface | that runtime step `N` equals chart slot `N` |
| Hexagram layer `64` | optional secondary tag family for schedule slots | primary ontology, line semantics, or closure proof |

---

## 10. 64 SCHEDULE INDEX GRID (8 × 8)

Rows = terrains. Cols = signed operators. `*` = one of the 16 chart-locked macro-stage occupancies.

| Terrain \ Op | `Ti↑` | `Ti↓` | `Te↑` | `Te↓` | `Fi↑` | `Fi↓` | `Fe↑` | `Fe↓` |
|---|---|---|---|---|---|---|---|---|
| `Se-in` | `S01*` | `S02` | `S03` | `S04` | `S05` | `S06*` | `S07` | `S08` |
| `Ne-in` | `S09` | `S10*` | `S11` | `S12` | `S13*` | `S14` | `S15` | `S16` |
| `Ni-in` | `S17` | `S18` | `S19*` | `S20` | `S21` | `S22` | `S23` | `S24*` |
| `Si-in` | `S25` | `S26` | `S27` | `S28*` | `S29` | `S30` | `S31*` | `S32` |
| `Se-out` | `S33` | `S34*` | `S35` | `S36` | `S37*` | `S38` | `S39` | `S40` |
| `Si-out` | `S41` | `S42` | `S43*` | `S44` | `S45` | `S46` | `S47` | `S48*` |
| `Ni-out` | `S49` | `S50` | `S51` | `S52*` | `S53` | `S54` | `S55*` | `S56` |
| `Ne-out` | `S57*` | `S58` | `S59` | `S60` | `S61` | `S62*` | `S63` | `S64` |

Hexagram labels may be attached to `S01-S64` as schedule tags only. They do not inherit binary line semantics.

---

## 11. AXIS OVERLAY

| Axis | Grammar layer | What it governs |
|---|---|---|
| Ax0 | Graph edge | Ne/Ni vs Se/Si |
| Ax1 | Graph edge (cross) | Se/Ni vs Ne/Si |
| Ax2 | Graph edge | Se/Ne vs Si/Ni |
| Ax3 | IGT | IN flux vs OUT flux *(scaffold — not closed by proof)* |
| Ax4 | Jung | FeTi (deductive) vs TeFi (inductive) |
| Ax5 | IGT | First strategy (Te/Ti) vs second (Fe/Fi) |
| Ax6 | Jung | UP (operator first) vs DOWN (terrain first) |

---

## 12. INVARIANTS

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
| Signed operators per engine | 8 (4 ops × 2 signs) |
| Chart-locked macro-stages | 16 (starred cells in grid) |
| Terrains overlap between engines | 0 |

| Engine | `↑` stages | `↓` stages |
|---|---|---|
| Type-1 | `Ti↑`, `Fe↑`, `Fi↑`, `Te↑` | `Ti↓`, `Fe↓`, `Fi↓`, `Te↓` |
| Type-2 | `Fi↑`, `Te↑`, `Fe↑`, `Ti↑` | `Ti↓`, `Fe↓`, `Te↓`, `Fi↓` |

---

## 13. HARD NON-CLAIMS

- `type ≠ flow ≠ chirality ≠ precedence`
- `outer / inner ≠ Ax3`
- `I Ching labels ≠ ontology`
- `correlations ≠ proof`
- `runtime step ids ≠ schedule-slot ids`
- `schedule-slot ids ≠ structural line meanings`
- `thermodynamics = search metaphor, not literal`
- `Ne1/Ne2 scheme is superseded by *-in/*-out`
- `this document ≠ proof of full 64-state closure`

---

## 14. GRAMMAR LAYER OWNERSHIP

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

---

## Open / Disputed Items

- Loop traversal order is Carnot-grounded and graph-derived, but not yet proven by directional sim.
- Apple Notes dump contains older loop-order blocks; this chart follows the Ax0/Ax2 graph order.
- Exact Carnot-cylinder stroke accounting is still open — do not smuggle in as settled.
- The 48 non-starred cells in the 8×8 grid are schedule slots, not runtime claims.
