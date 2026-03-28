# ENGINE 64-SCHEDULE ATLAS

**Date:** 2026-03-27
**Status:** Scaffold chart grounded against owner source docs. Not runtime closure. Not final authority. Earned by chart alignment, not by proof.

> **Governing split:** IGT = stage grammar. Jung = operator grammar. I Ching = 64-schedule index. They do not overlap. They do not redefine each other.

| System | Job | Must not do |
|---|---|---|
| `IGT` | lock `WIN / LOSE / win / lose`, same-sign vs mixed, outer vs inner, first vs second asymmetry | redefine operator order or hexagram semantics |
| `Jung` | name ordered pair tokens, loop families, and signed operators | replace IGT outcome structure |
| `I Ching` | index the 64-slot schedule atlas | define runtime truth, line meanings, or axis closure |

---

## 0. SOURCE GROUNDING (owner docs only)

| Concern | Strongest owner source | Safe read now |
|---|---|---|
| 4 topology math | `core_docs/a1_refined_Ratchet Fuel/constraint ladder/Axis 1 2 topology math...md` | `Se`, `Ne`, `Ni`, `Si` are proposed as 4 real QIT / geometry flow classes |
| generalized-spinor loop structure | `core_docs/a1_refined_Ratchet Fuel/constraint ladder/Axis 3 math Hopf fiber loop vs lifted base loop.md` | 8 stages exist before chirality choice: 4 on Hopf fiber loop + 4 on lifted base loop |
| Terrain8 pipeline | `core_docs/a1_refined_Ratchet Fuel/AXIS_FOUNDATION_COMPANION_v1.4.md` and `core_docs/a1_refined_Ratchet Fuel/sims/SIM_RUNBOOK_v1.4.md` | `Terrain8 = Topology4 × Flux2` is an owner-surface proposal |
| explicit in/out terrain names | `core_docs/a2_feed_high entropy doc/axes math. apple notes dump.txt` | one explicit Type-1 / Type-2 terrain naming surface, not the only alias layer |

| Topology | Strongest source-grounded math read | Strongest owner pair name | Apple Notes Type-1 / Type-2 names |
|---|---|---|---|
| `Se` | dissipative Lindblad radial expansion | `Funnel / Cannon` | `Inward funnel` / `Outward cannon` |
| `Ne` | Hamiltonian tangential circulation on `S^3` / Hopf side | `Vortex / Spiral` | `Spiral-in` / `Spiral-out` |
| `Ni` | dissipative Lindblad attraction / contraction | `Pit / Source` | `Pit (collapse)` / `Source (emergence)` |
| `Si` | commuting Hamiltonian plus invariant subspaces | `Hill / Citadel` | `Hill (accumulation)` / `Basin (release)` |

| Generalized-spinor claim | Safe read now |
|---|---|
| pre-chirality stage structure | the same 8 stages exist before choosing left- vs right-handed Weyl representation |
| inner loop | Hopf fiber loop, `U(1)` fiber circulation, 4 stages |
| outer loop | lifted base loop, horizontal transport on `S^3`, 4 stages |
| chirality / flux | chirality orients engine type; it does not create new base topologies |

| Type-1 vs Type-2 geometry | Safe read now |
|---|---|
| shared carrier | same Weyl-spinor / `SU(2) ≅ S^3` carrier family |
| shared topology basis | same `Se`, `Ne`, `Ni`, `Si` topology classes |
| shared loop basis | same Hopf-fiber and lifted-base loop families |
| what differs | engine-wide orientation / chirality / flux realization across the same topology set |
| chart correlation | Type-1 correlates to `*-in`, Type-2 correlates to `*-out` |
| safest pattern | `Terrain8 = Topology4 x orientation`, not 8 unrelated topology kinds |

| Terrain8 correlation | Type-1 | Type-2 |
|---|---|---|
| `Se` family | `Se-in` | `Se-out` |
| `Ne` family | `Ne-in` | `Ne-out` |
| `Ni` family | `Ni-in` | `Ni-out` |
| `Si` family | `Si-in` | `Si-out` |

The atlas keeps neutral IDs (`Se-in`, `Se-out`, etc.) because the owner docs do not yet give one fully unified 8-name canon. Refined-fuel and Apple Notes use overlapping but non-identical naming layers.

---

## 0B. TERRAIN FAMILY VS STAGE REALIZATION

| Object | Count | Meaning |
|---|---|---|
| base terrain families | `4` | `Se`, `Ne`, `Ni`, `Si` as shared topology classes |
| macro-stages per spinor | `8` | `4` terrains x `2` loops |
| orientation-tagged terrain IDs | `8` | `4` terrains x `2` Weyl orientations (`in/out`) |
| total macro-stage realizations across both spinors | `16` | `4` terrains x `2` loops x `2` orientations |

So:

- `Se` is the same terrain family on both loops
- outer `Se` and inner `Se` are different stage realizations on the same terrain
- left/right or Type-1/Type-2 does not create new topology classes
- left/right changes how the same terrain family is oriented and enacted

| Terrain family | Source-grounded math | Left / Type-1 outer | Left / Type-1 inner | Right / Type-2 outer | Right / Type-2 inner |
|---|---|---|---|---|---|
| `Se` | dissipative Lindblad radial expansion | `TiSe / LOSE / Ti↑` | `SeFi / win / Fi↓` | `FiSe / WIN / Fi↑` | `SeTi / lose / Ti↓` |
| `Ne` | Hamiltonian tangential circulation on `S^3` | `NeTi / WIN / Ti↓` | `FiNe / lose / Fi↑` | `NeFi / LOSE / Fi↓` | `TiNe / win / Ti↑` |
| `Ni` | dissipative Lindblad contraction / attraction | `NiFe / LOSE / Fe↓` | `TeNi / lose / Te↑` | `NiTe / LOSE / Te↓` | `FeNi / lose / Fe↑` |
| `Si` | commuting Hamiltonian plus invariant subspaces | `FeSi / WIN / Fe↑` | `SiTe / win / Te↓` | `TeSi / WIN / Te↑` | `SiFe / win / Fe↓` |

This is the actual per-terrain mapping:

- terrain family = shared topology class
- outer vs inner = loop realization of that terrain
- Type-1 vs Type-2 = orientation / chirality realization of that terrain

---

## 0C. EXPLICIT TERRAIN EQUATIONS

**Source:** `axes math. apple notes dump.txt` lines 9695-9761 (Lindblad operators + Hamiltonian sign)

Master equation form for every terrain:

`dρ/dt = -i[H, ρ] + γ(L ρ L† − ½{L†L, ρ})`

### Hamiltonian sign (chirality)

| Chirality | Hamiltonian |
|---|---|
| Type-1 (left Weyl) | `H_L = +n·σ` |
| Type-2 (right Weyl) | `H_R = −n·σ` |

### Lindblad operators (topology family)

| Topology | Lindblad operator `L` | Effect |
|---|---|---|
| Se | `√γ σ_z` | dephasing in computational basis |
| Ne | `√γ σ_x` | bit-flip mixing |
| Ni | `√γ σ_y` | phase-flip with rotation |
| Si | `√γ σ_−` (`= \|0⟩⟨1\|`) | amplitude damping |

### The 8 terrain equations

| Terrain | Name | Equation |
|---|---|---|
| `Se-in` | Funnel | `dρ/dt = -i[+n·σ, ρ] + γ(σ_z ρ σ_z − ρ)` |
| `Se-out` | Cannon | `dρ/dt = -i[−n·σ, ρ] + γ(σ_z ρ σ_z − ρ)` |
| `Ne-in` | Vortex | `dρ/dt = -i[+n·σ, ρ] + γ(σ_x ρ σ_x − ρ)` |
| `Ne-out` | Spiral | `dρ/dt = -i[−n·σ, ρ] + γ(σ_x ρ σ_x − ρ)` |
| `Ni-in` | Pit | `dρ/dt = -i[+n·σ, ρ] + γ(σ_y ρ σ_y − ρ)` |
| `Ni-out` | Source | `dρ/dt = -i[−n·σ, ρ] + γ(σ_y ρ σ_y − ρ)` |
| `Si-in` | Hill | `dρ/dt = -i[+n·σ, ρ] + γ(σ_− ρ σ_+ − ½{σ_+σ_−, ρ})` |
| `Si-out` | Citadel | `dρ/dt = -i[−n·σ, ρ] + γ(σ_− ρ σ_+ − ½{σ_+σ_−, ρ})` |

### What in/out changes per pair

| Pair | Same `L` | Different `H` | Geometric meaning |
|---|---|---|---|
| Funnel / Cannon | `σ_z` | `+n·σ` vs `−n·σ` | same dephasing, opposite unitary rotation |
| Vortex / Spiral | `σ_x` | `+n·σ` vs `−n·σ` | same mixing, opposite-handed circulation |
| Pit / Source | `σ_y` | `+n·σ` vs `−n·σ` | same phase-twist, opposite rotational contraction |
| Hill / Citadel | `σ_−` | `+n·σ` vs `−n·σ` | same amplitude damping, opposite unitary flow |

### Flux current

`J(ρ) = (i/ℏ)[ρ, H]`

Type-1: `J_L(ρ) = (i/ℏ)[ρ, +n·σ]`
Type-2: `J_R(ρ) = (i/ℏ)[ρ, −n·σ] = −J_L(ρ)`

So flux = sign of the flow generator. Left/right Weyl gives opposite orientation of the same flow.

### Feature matrix

| Feature | Se | Ne | Ni | Si |
|---|---|---|---|---|
| Lindblad dissipator | ✔ | ✔ | ✔ | ✔ |
| Hamiltonian flow | ✔ | ✔ | ✔ | ✔ |
| Divergence ≠ 0 (dissipative only) | Se ✔ | Ne ✗ (pure rotation if γ→0) | Ni ✔ | Si ✗ (stratified if γ→0) |
| Attractors exist | ✗ | ✗ | ✔ | ✗ |
| Circulation | ✗ | ✔ | ✗ | ✗ |
| Invariant strata | ✗ | ✗ | ✗ | ✔ |

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

## 3. LOOP ORDERS (current chart lock)

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

## 4. CHART TERRAIN IDS (8)

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

Source-grounded reading: the refined-fuel ladder strongly supports `4` real topology classes. This atlas’s `8` terrains are the current chart correlation for those `4` under two engine orientations.

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

## 11. AXIS GROUNDING STATUS

| Axis | Current best read | Grounding status |
|---|---|---|
| Ax0 | graph-edge / topology-partition helper | chart-level candidate only |
| Ax1 | one Topology4 factor in owner sources; exact local read still drifts between open/closed and isothermal/adiabatic wording | source-grounded factor, local binding not closed |
| Ax2 | one Topology4 factor in owner sources; current strongest candidate is expansion vs compression | source-grounded factor, local binding still under reconstruction |
| Ax3 | open: source math supports chirality / flux orientation; alternative proposal is outer vs inner | unresolved, do not close here |
| Ax4 | QIT ordering class: inductive vs deductive; chart correlates this to `FeTi / TeFi` | strongest source-grounded operator axis |
| Ax5 | first vs second strategy (`T` vs `F`) | chart / IGT correlation only |
| Ax6 | action / precedence orientation: operator first vs terrain first (`UP / DOWN`) | partially source-grounded; chart binding is clearer than the source-side closure |

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
- `Ax3 is not closed by this atlas`
- `Ax1/Ax2 owner-source Topology4 and this atlas's graph bindings are not the same claim`
- `I Ching labels ≠ ontology`
- `correlations ≠ proof`
- `8` chart terrains ≠ closed theorem of Weyl geometry
- `runtime step ids ≠ schedule-slot ids`
- `schedule-slot ids ≠ structural line meanings`
- `thermodynamics = search metaphor, not literal`
- `Ne1/Ne2 scheme is superseded by *-in/*-out`
- `terrain nicknames are source aliases, not one cleaned canon set`
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
- Owner source surfaces currently contain two different 8-way constructions:
  - generalized-spinor `8 = 4 topologies × 2 loop families`
  - Terrain8 `= Topology4 × Flux2`
  This atlas correlates them, but does not prove they are the same object.
- Exact Carnot-cylinder stroke accounting is still open — do not smuggle in as settled.
- The 48 non-starred cells in the 8×8 grid are schedule slots, not runtime claims.

---
