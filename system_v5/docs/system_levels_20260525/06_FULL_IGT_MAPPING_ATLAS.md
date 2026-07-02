# Full IGT Mapping Atlas

Status: source-grounded mapping atlas and runtime scaffold, not manifold
closure, not final I Ching ontology, not a 64-cell PEPS3D proof.

This file exists because the deep manual still compressed the IGT layer too
much. The IGT mapping is not one label table. It is a bundle of separate maps
that must stay distinct:

```text
IGT = stage grammar
Jung = ordered operator/topology token grammar
I Ching = 64-slot schedule index
runtime 64 = two engines x eight macro stages x four operator slots
```

The mapping below preserves each of those surfaces explicitly.

## 1. Governing Split

| System | Owns | Must not do |
|---|---|---|
| IGT | `WIN`, `LOSE`, `win`, `lose`; quadrant labels; same-sign/mixed patterns; outer/inner result casing; first/second asymmetry | redefine operator maps, terrain laws, or hexagram semantics |
| Jung/operator grammar | ordered pair tokens such as `TiSe`, `NeTi`, `FeSi`, `NiFe`; operator-first vs terrain-first precedence; signed judging variants | replace IGT outcome structure |
| I Ching schedule index | `S01` through `S64` slot identity and optional hexagram tag family | define runtime truth, line meanings, axis closure, or manifold proof |
| Runtime scaffold | `2 engines x 8 macro stages x 4 operator slots = 64` executable substage rows | prove that the 64 rows are PEPS3D manifold cells |

The hard rule:

```text
IGT result label != operator map
ordered token != terrain generator
schedule index != runtime substage
runtime substage row != PEPS3D manifold cell unless cell action is explicit
```

## 2. Terrain And Topology Basis

The source-grounded topology basis is:

| Topology | Pair names | Math reading |
|---|---|---|
| `Se` | Funnel / Cannon | radial expansion; dissipative Lindblad or CPTP expansion |
| `Ne` | Vortex / Spiral | tangential Hamiltonian circulation on `S^3`; Hopf-fiber-tangent flow |
| `Ni` | Pit / Source | radial contraction; dissipative Lindblad attraction or cooling |
| `Si` | Hill / Citadel | stratified retention; commuting Hamiltonian plus invariant subspaces |

The atlas keeps two related but non-identical 8-way ideas visible:

```text
generalized-spinor 8 = 4 topologies x 2 loop families
Terrain8 proposal    = Topology4 x Flux2
```

The atlas correlates them. It does not prove that they are the same object.

## 3. IGT Quadrant Lock

IGT quadrant assignment:

| Perceiving topology | IGT quadrant | Dephasing/T-strategy | Rotation/F-strategy |
|---|---|---|---|
| `Ne` | `WinLose` | `NeTi` | `FiNe` |
| `Si` | `WinWin` | `SiTe` | `FeSi` |
| `Se` | `LoseWin` | `TiSe` | `SeFi` |
| `Ni` | `LoseLose` | `TeNi` | `NiFe` |

Interpretation:

```text
capital WIN/LOSE = outer or major stage result
lowercase win/lose = inner or minor stage result
```

This quadrant lock is chart/stage grammar. It is not the operator algebra and
not the carrier geometry.

## 4. Direct And Conjugated Frame Affinities

The operator/topology affinities are:

| Terrain frame | Topologies | Native judging/operator functions |
|---|---|---|
| direct frame | `Se`, `Ne` | `Ti`, `Fi` |
| conjugated frame | `Ni`, `Si` | `Te`, `Fe` |

This is why the token table splits as:

```text
Se/Ne use Ti or Fi
Ni/Si use Te or Fe
```

## 5. Full Ordered-Token Law

The token is determined by:

```text
topology
operator family
precedence order
```

Precedence:

```text
operator first = operator name written first
terrain first  = terrain/topology name written first
```

Full token table:

| Topology | Dephasing operator first | Dephasing terrain first | Rotation operator first | Rotation terrain first |
|---|---|---|---|---|
| `Se` | `TiSe` | `SeTi` | `FiSe` | `SeFi` |
| `Ne` | `TiNe` | `NeTi` | `FiNe` | `NeFi` |
| `Ni` | `TeNi` | `NiTe` | `FeNi` | `NiFe` |
| `Si` | `TeSi` | `SiTe` | `FeSi` | `SiFe` |

This is the 16 ordered-token surface. It is not the same as the 16
terrain-loop placements:

```text
16 ordered tokens      = topology x operator-family x precedence
16 terrain placements  = topology x Weyl sheet x loop field
```

## 6. Eight Signed Judging Variants

`UP` means operator first. `DOWN` means terrain first.

The operator map does not change between UP and DOWN. What changes is the
composition order in the token/stage grammar.

| Signed variant | Precedence | Ordered tokens | Native topology set | Current chart placements |
|---|---|---|---|---|
| `Ti-UP` | operator first | `TiSe`, `TiNe` | `Se`, `Ne` | Type-1 outer `Se`; Type-2 inner `Ne` |
| `Ti-DOWN` | terrain first | `SeTi`, `NeTi` | `Se`, `Ne` | Type-2 inner `Se`; Type-1 outer `Ne` |
| `Fe-UP` | operator first | `FeSi`, `FeNi` | `Si`, `Ni` | Type-1 outer `Si`; Type-2 inner `Ni` |
| `Fe-DOWN` | terrain first | `SiFe`, `NiFe` | `Si`, `Ni` | Type-2 inner `Si`; Type-1 outer `Ni` |
| `Te-UP` | operator first | `TeNi`, `TeSi` | `Ni`, `Si` | Type-1 inner `Ni`; Type-2 outer `Si` |
| `Te-DOWN` | terrain first | `NiTe`, `SiTe` | `Ni`, `Si` | Type-2 outer `Ni`; Type-1 inner `Si` |
| `Fi-UP` | operator first | `FiNe`, `FiSe` | `Ne`, `Se` | Type-1 inner `Ne`; Type-2 outer `Se` |
| `Fi-DOWN` | terrain first | `NeFi`, `SeFi` | `Ne`, `Se` | Type-2 outer `Ne`; Type-1 inner `Se` |

Noncommuting order target:

```text
Phi_T o U_O != U_O o Phi_T
```

where `Phi_T` is the terrain/channel map and `U_O` or `O` is the operator
action.

## 7. Axis/Loop Chart Used By IGT

Current chart lock:

```text
Ne --Ax2-- Se
|          |
Ax0        Ax0
|          |
Ni --Ax2-- Si
```

Axis family walks:

| Axis 4 family | Topology order |
|---|---|
| Inductive | `Se -> Si -> Ni -> Ne` |
| Deductive | `Se -> Ne -> Ni -> Si` |

Edge families:

| Edge family | Edges |
|---|---|
| `Ax0` | `Se-Si`, `Ne-Ni` |
| `Ax2` | `Se-Ne`, `Si-Ni` |

Loop edge walks:

| Loop family | Edge walk |
|---|---|
| Inductive `Se -> Si -> Ni -> Ne` | `Ax0 -> Ax2 -> Ax0 -> Ax2` |
| Deductive `Se -> Ne -> Ni -> Si` | `Ax2 -> Ax0 -> Ax2 -> Ax0` |

Do not overpromote this as final Axis0 or Axis2 proof. It is chart structure.

## 8. Global Locks By Engine Type

| Layer | Type-1 | Type-2 |
|---|---|---|
| Orientation/flux tag | `IN` | `OUT` |
| Major/outer result casing | `WIN` / `LOSE` | `WIN` / `LOSE` |
| Minor/inner result casing | `win` / `lose` | `win` / `lose` |
| Outer loop family | Deductive `FeTi` family | Inductive `TeFi` family |
| Inner loop family | Inductive `TeFi` family | Deductive `FeTi` family |

Do not collapse engine type into one bit only. Engine type correlates multiple
roles:

```text
orientation/flux tag
outer/inner loop family
token order
operator placement
result casing
Weyl sheet realization
```

## 9. Chart Terrain IDs

| Chart ID | Terrain ID | Topology | Flux/orientation tag | Engine family |
|---|---|---|---|---|
| T1 | `Se-in` | `Se` | `IN` | Type-1 |
| T2 | `Ne-in` | `Ne` | `IN` | Type-1 |
| T3 | `Ni-in` | `Ni` | `IN` | Type-1 |
| T4 | `Si-in` | `Si` | `IN` | Type-1 |
| T5 | `Se-out` | `Se` | `OUT` | Type-2 |
| T6 | `Si-out` | `Si` | `OUT` | Type-2 |
| T7 | `Ni-out` | `Ni` | `OUT` | Type-2 |
| T8 | `Ne-out` | `Ne` | `OUT` | Type-2 |

The `in/out` IDs are chart tags for orientation. They are not final flux proof.

## 10. Type-1 Full IGT Chart

Type-1 uses:

```text
outer loop = deductive order on lifted base loop
inner loop = inductive order on fiber loop
orientation tag = IN
```

Topology-aligned Type-1 chart:

| Topology | Terrain | Outer token | Outer A6 | Signed op | Outer result | Inner token | Inner A6 | Signed op | Inner result | Source pattern |
|---|---|---|---|---|---|---|---|---|---|---|
| `Se` | `Se-in` | `TiSe` | `UP` | `Ti-UP` | `LOSE` | `SeFi` | `DOWN` | `Fi-DOWN` | `win` | `LOSEwin` |
| `Ne` | `Ne-in` | `NeTi` | `DOWN` | `Ti-DOWN` | `WIN` | `FiNe` | `UP` | `Fi-UP` | `lose` | `WINlose` |
| `Ni` | `Ni-in` | `NiFe` | `DOWN` | `Fe-DOWN` | `LOSE` | `TeNi` | `UP` | `Te-UP` | `lose` | `loseLOSE` |
| `Si` | `Si-in` | `FeSi` | `UP` | `Fe-UP` | `WIN` | `SiTe` | `DOWN` | `Te-DOWN` | `win` | `winWIN` |

Type-1 loop traversal view:

| Loop | Order | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|---|---|---|---|---|---|
| Outer / major | Deductive | `Se-in : TiSe : LOSE` | `Ne-in : NeTi : WIN` | `Ni-in : NiFe : LOSE` | `Si-in : FeSi : WIN` |
| Inner / minor | Inductive | `Se-in : SeFi : win` | `Si-in : SiTe : win` | `Ni-in : TeNi : lose` | `Ne-in : FiNe : lose` |

Runtime macro-stage order used by the current scaffold:

```text
T1-M01 Se outer TiSe LOSE UP
T1-M02 Ne outer NeTi WIN DOWN
T1-M03 Ni outer NiFe LOSE DOWN
T1-M04 Si outer FeSi WIN UP
T1-M05 Se inner SeFi win DOWN
T1-M06 Si inner SiTe win DOWN
T1-M07 Ni inner TeNi lose UP
T1-M08 Ne inner FiNe lose UP
```

## 11. Type-2 Full IGT Chart

Type-2 uses:

```text
outer loop = inductive order on fiber loop
inner loop = deductive order on lifted base loop
orientation tag = OUT
```

Topology-aligned Type-2 chart:

| Topology | Terrain | Outer token | Outer A6 | Signed op | Outer result | Inner token | Inner A6 | Signed op | Inner result | Source pattern |
|---|---|---|---|---|---|---|---|---|---|---|
| `Se` | `Se-out` | `FiSe` | `UP` | `Fi-UP` | `WIN` | `SeTi` | `DOWN` | `Ti-DOWN` | `lose` | `loseWIN` |
| `Si` | `Si-out` | `TeSi` | `UP` | `Te-UP` | `WIN` | `SiFe` | `DOWN` | `Fe-DOWN` | `win` | `WINwin` |
| `Ni` | `Ni-out` | `NiTe` | `DOWN` | `Te-DOWN` | `LOSE` | `FeNi` | `UP` | `Fe-UP` | `lose` | `LOSElose` |
| `Ne` | `Ne-out` | `NeFi` | `DOWN` | `Fi-DOWN` | `LOSE` | `TiNe` | `UP` | `Ti-UP` | `win` | `winLOSE` |

Type-2 loop traversal view:

| Loop | Order | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|---|---|---|---|---|---|
| Outer / major | Inductive | `Se-out : FiSe : WIN` | `Si-out : TeSi : WIN` | `Ni-out : NiTe : LOSE` | `Ne-out : NeFi : LOSE` |
| Inner / minor | Deductive | `Se-out : SeTi : lose` | `Ne-out : TiNe : win` | `Ni-out : FeNi : lose` | `Si-out : SiFe : win` |

Runtime macro-stage order used by the current scaffold:

```text
T2-M01 Se outer FiSe WIN UP
T2-M02 Si outer TeSi WIN UP
T2-M03 Ni outer NiTe LOSE DOWN
T2-M04 Ne outer NeFi LOSE DOWN
T2-M05 Se inner SeTi lose DOWN
T2-M06 Ne inner TiNe win UP
T2-M07 Ni inner FeNi lose UP
T2-M08 Si inner SiFe win DOWN
```

## 12. Topology-Aligned Comparison

| Topology | Type-1 terrain | Type-1 major | Type-1 minor | Type-2 terrain | Type-2 major | Type-2 minor |
|---|---|---|---|---|---|---|
| `Se` | `Se-in` | `TiSe / LOSE / Ti-UP` | `SeFi / win / Fi-DOWN` | `Se-out` | `FiSe / WIN / Fi-UP` | `SeTi / lose / Ti-DOWN` |
| `Ne` | `Ne-in` | `NeTi / WIN / Ti-DOWN` | `FiNe / lose / Fi-UP` | `Ne-out` | `NeFi / LOSE / Fi-DOWN` | `TiNe / win / Ti-UP` |
| `Ni` | `Ni-in` | `NiFe / LOSE / Fe-DOWN` | `TeNi / lose / Te-UP` | `Ni-out` | `NiTe / LOSE / Te-DOWN` | `FeNi / lose / Fe-UP` |
| `Si` | `Si-in` | `FeSi / WIN / Fe-UP` | `SiTe / win / Te-DOWN` | `Si-out` | `TeSi / WIN / Te-UP` | `SiFe / win / Fe-DOWN` |

This is the mapping that most often gets lost. It preserves topology, terrain
ID, operator token, IGT result, signed operator, and engine type side by side.

## 13. The 64-Layer Split

There are at least three 64-count surfaces:

| Surface | Formula | Safe use | Must not claim |
|---|---|---|---|
| runtime 64 | `2 engines x 8 macro stages x 4 operator slots` | executable scaffold for current 64-substage rows | full manifold-cell embedding |
| chart atlas 64 | `8 terrain IDs x 8 signed operators` | schedule-index grid | runtime step `N` equals chart slot `N` |
| hexagram 64 | optional tag family | secondary symbolic index | ontology, line semantics, axis closure |

The current formal scout pressure is strongest for runtime grammar and schedule
portability. It still does not prove PEPS3D manifold cells.

## 14. 8x8 Schedule Index Grid

Rows are chart terrain IDs. Columns are signed operators. `*` marks the 16
chart-locked macro-stage occupancies. The other 48 cells are schedule slots, not
current runtime claims.

| Terrain / Op | `Ti-UP` | `Ti-DOWN` | `Te-UP` | `Te-DOWN` | `Fi-UP` | `Fi-DOWN` | `Fe-UP` | `Fe-DOWN` |
|---|---|---|---|---|---|---|---|---|
| `Se-in` | `S01*` | `S02` | `S03` | `S04` | `S05` | `S06*` | `S07` | `S08` |
| `Ne-in` | `S09` | `S10*` | `S11` | `S12` | `S13*` | `S14` | `S15` | `S16` |
| `Ni-in` | `S17` | `S18` | `S19*` | `S20` | `S21` | `S22` | `S23` | `S24*` |
| `Si-in` | `S25` | `S26` | `S27` | `S28*` | `S29` | `S30` | `S31*` | `S32` |
| `Se-out` | `S33` | `S34*` | `S35` | `S36` | `S37*` | `S38` | `S39` | `S40` |
| `Si-out` | `S41` | `S42` | `S43*` | `S44` | `S45` | `S46` | `S47` | `S48*` |
| `Ni-out` | `S49` | `S50` | `S51` | `S52*` | `S53` | `S54` | `S55*` | `S56` |
| `Ne-out` | `S57*` | `S58` | `S59` | `S60` | `S61` | `S62*` | `S63` | `S64` |

Mapping from starred cells to macro stages:

| Starred slot | Macro stage |
|---|---|
| `S01` | Type-1 outer `Se-in : TiSe : LOSE : Ti-UP` |
| `S06` | Type-1 inner `Se-in : SeFi : win : Fi-DOWN` |
| `S10` | Type-1 outer `Ne-in : NeTi : WIN : Ti-DOWN` |
| `S13` | Type-1 inner `Ne-in : FiNe : lose : Fi-UP` |
| `S19` | Type-1 inner `Ni-in : TeNi : lose : Te-UP` |
| `S24` | Type-1 outer `Ni-in : NiFe : LOSE : Fe-DOWN` |
| `S28` | Type-1 inner `Si-in : SiTe : win : Te-DOWN` |
| `S31` | Type-1 outer `Si-in : FeSi : WIN : Fe-UP` |
| `S34` | Type-2 inner `Se-out : SeTi : lose : Ti-DOWN` |
| `S37` | Type-2 outer `Se-out : FiSe : WIN : Fi-UP` |
| `S43` | Type-2 outer `Si-out : TeSi : WIN : Te-UP` |
| `S48` | Type-2 inner `Si-out : SiFe : win : Fe-DOWN` |
| `S52` | Type-2 outer `Ni-out : NiTe : LOSE : Te-DOWN` |
| `S55` | Type-2 inner `Ni-out : FeNi : lose : Fe-UP` |
| `S57` | Type-2 inner `Ne-out : TiNe : win : Ti-UP` |
| `S62` | Type-2 outer `Ne-out : NeFi : LOSE : Fi-DOWN` |

Note the deliberate mismatch between grid ordering and runtime chronological
ordering. The grid is a chart atlas; the runtime order is the engine loop order.

## 15. Runtime 64 Expansion Rule

The runtime scaffold expands every macro stage into four operator slots:

```text
operator slot sequence = Ti, Te, Fi, Fe
```

All four slots inherit the macro-stage context:

```text
engine type
outer/inner loop
topology
terrain ID
macro token
IGT result
Axis6 sign
source pattern
```

Important:

```text
macro token = chart token for the stage
operator slot = actual substage operator position in the runtime cycle
```

Those are not the same object. A row may have macro token `TiSe` while slot
`Fe` runs as the fourth substage under that macro context.

## 16. Type-1 Runtime 32 Rows

| Row | Macro | Loop | Topology | Terrain | Macro token/result/A6 | Slot |
|---|---|---|---|---|---|---|
| T1-01 | M01 | outer | `Se` | `Se-in` | `TiSe / LOSE / UP` | `Ti` |
| T1-02 | M01 | outer | `Se` | `Se-in` | `TiSe / LOSE / UP` | `Te` |
| T1-03 | M01 | outer | `Se` | `Se-in` | `TiSe / LOSE / UP` | `Fi` |
| T1-04 | M01 | outer | `Se` | `Se-in` | `TiSe / LOSE / UP` | `Fe` |
| T1-05 | M02 | outer | `Ne` | `Ne-in` | `NeTi / WIN / DOWN` | `Ti` |
| T1-06 | M02 | outer | `Ne` | `Ne-in` | `NeTi / WIN / DOWN` | `Te` |
| T1-07 | M02 | outer | `Ne` | `Ne-in` | `NeTi / WIN / DOWN` | `Fi` |
| T1-08 | M02 | outer | `Ne` | `Ne-in` | `NeTi / WIN / DOWN` | `Fe` |
| T1-09 | M03 | outer | `Ni` | `Ni-in` | `NiFe / LOSE / DOWN` | `Ti` |
| T1-10 | M03 | outer | `Ni` | `Ni-in` | `NiFe / LOSE / DOWN` | `Te` |
| T1-11 | M03 | outer | `Ni` | `Ni-in` | `NiFe / LOSE / DOWN` | `Fi` |
| T1-12 | M03 | outer | `Ni` | `Ni-in` | `NiFe / LOSE / DOWN` | `Fe` |
| T1-13 | M04 | outer | `Si` | `Si-in` | `FeSi / WIN / UP` | `Ti` |
| T1-14 | M04 | outer | `Si` | `Si-in` | `FeSi / WIN / UP` | `Te` |
| T1-15 | M04 | outer | `Si` | `Si-in` | `FeSi / WIN / UP` | `Fi` |
| T1-16 | M04 | outer | `Si` | `Si-in` | `FeSi / WIN / UP` | `Fe` |
| T1-17 | M05 | inner | `Se` | `Se-in` | `SeFi / win / DOWN` | `Ti` |
| T1-18 | M05 | inner | `Se` | `Se-in` | `SeFi / win / DOWN` | `Te` |
| T1-19 | M05 | inner | `Se` | `Se-in` | `SeFi / win / DOWN` | `Fi` |
| T1-20 | M05 | inner | `Se` | `Se-in` | `SeFi / win / DOWN` | `Fe` |
| T1-21 | M06 | inner | `Si` | `Si-in` | `SiTe / win / DOWN` | `Ti` |
| T1-22 | M06 | inner | `Si` | `Si-in` | `SiTe / win / DOWN` | `Te` |
| T1-23 | M06 | inner | `Si` | `Si-in` | `SiTe / win / DOWN` | `Fi` |
| T1-24 | M06 | inner | `Si` | `Si-in` | `SiTe / win / DOWN` | `Fe` |
| T1-25 | M07 | inner | `Ni` | `Ni-in` | `TeNi / lose / UP` | `Ti` |
| T1-26 | M07 | inner | `Ni` | `Ni-in` | `TeNi / lose / UP` | `Te` |
| T1-27 | M07 | inner | `Ni` | `Ni-in` | `TeNi / lose / UP` | `Fi` |
| T1-28 | M07 | inner | `Ni` | `Ni-in` | `TeNi / lose / UP` | `Fe` |
| T1-29 | M08 | inner | `Ne` | `Ne-in` | `FiNe / lose / UP` | `Ti` |
| T1-30 | M08 | inner | `Ne` | `Ne-in` | `FiNe / lose / UP` | `Te` |
| T1-31 | M08 | inner | `Ne` | `Ne-in` | `FiNe / lose / UP` | `Fi` |
| T1-32 | M08 | inner | `Ne` | `Ne-in` | `FiNe / lose / UP` | `Fe` |

## 17. Type-2 Runtime 32 Rows

| Row | Macro | Loop | Topology | Terrain | Macro token/result/A6 | Slot |
|---|---|---|---|---|---|---|
| T2-01 | M01 | outer | `Se` | `Se-out` | `FiSe / WIN / UP` | `Ti` |
| T2-02 | M01 | outer | `Se` | `Se-out` | `FiSe / WIN / UP` | `Te` |
| T2-03 | M01 | outer | `Se` | `Se-out` | `FiSe / WIN / UP` | `Fi` |
| T2-04 | M01 | outer | `Se` | `Se-out` | `FiSe / WIN / UP` | `Fe` |
| T2-05 | M02 | outer | `Si` | `Si-out` | `TeSi / WIN / UP` | `Ti` |
| T2-06 | M02 | outer | `Si` | `Si-out` | `TeSi / WIN / UP` | `Te` |
| T2-07 | M02 | outer | `Si` | `Si-out` | `TeSi / WIN / UP` | `Fi` |
| T2-08 | M02 | outer | `Si` | `Si-out` | `TeSi / WIN / UP` | `Fe` |
| T2-09 | M03 | outer | `Ni` | `Ni-out` | `NiTe / LOSE / DOWN` | `Ti` |
| T2-10 | M03 | outer | `Ni` | `Ni-out` | `NiTe / LOSE / DOWN` | `Te` |
| T2-11 | M03 | outer | `Ni` | `Ni-out` | `NiTe / LOSE / DOWN` | `Fi` |
| T2-12 | M03 | outer | `Ni` | `Ni-out` | `NiTe / LOSE / DOWN` | `Fe` |
| T2-13 | M04 | outer | `Ne` | `Ne-out` | `NeFi / LOSE / DOWN` | `Ti` |
| T2-14 | M04 | outer | `Ne` | `Ne-out` | `NeFi / LOSE / DOWN` | `Te` |
| T2-15 | M04 | outer | `Ne` | `Ne-out` | `NeFi / LOSE / DOWN` | `Fi` |
| T2-16 | M04 | outer | `Ne` | `Ne-out` | `NeFi / LOSE / DOWN` | `Fe` |
| T2-17 | M05 | inner | `Se` | `Se-out` | `SeTi / lose / DOWN` | `Ti` |
| T2-18 | M05 | inner | `Se` | `Se-out` | `SeTi / lose / DOWN` | `Te` |
| T2-19 | M05 | inner | `Se` | `Se-out` | `SeTi / lose / DOWN` | `Fi` |
| T2-20 | M05 | inner | `Se` | `Se-out` | `SeTi / lose / DOWN` | `Fe` |
| T2-21 | M06 | inner | `Ne` | `Ne-out` | `TiNe / win / UP` | `Ti` |
| T2-22 | M06 | inner | `Ne` | `Ne-out` | `TiNe / win / UP` | `Te` |
| T2-23 | M06 | inner | `Ne` | `Ne-out` | `TiNe / win / UP` | `Fi` |
| T2-24 | M06 | inner | `Ne` | `Ne-out` | `TiNe / win / UP` | `Fe` |
| T2-25 | M07 | inner | `Ni` | `Ni-out` | `FeNi / lose / UP` | `Ti` |
| T2-26 | M07 | inner | `Ni` | `Ni-out` | `FeNi / lose / UP` | `Te` |
| T2-27 | M07 | inner | `Ni` | `Ni-out` | `FeNi / lose / UP` | `Fi` |
| T2-28 | M07 | inner | `Ni` | `Ni-out` | `FeNi / lose / UP` | `Fe` |
| T2-29 | M08 | inner | `Si` | `Si-out` | `SiFe / win / DOWN` | `Ti` |
| T2-30 | M08 | inner | `Si` | `Si-out` | `SiFe / win / DOWN` | `Te` |
| T2-31 | M08 | inner | `Si` | `Si-out` | `SiFe / win / DOWN` | `Fi` |
| T2-32 | M08 | inner | `Si` | `Si-out` | `SiFe / win / DOWN` | `Fe` |

## 18. Invariants Preserved By The Mapping

| Invariant | Value |
|---|---|
| Terrain families | 4: `Se`, `Ne`, `Ni`, `Si` |
| Chart terrain IDs | 8: `Se-in`, `Ne-in`, `Ni-in`, `Si-in`, `Se-out`, `Si-out`, `Ni-out`, `Ne-out` |
| Macro stages per engine | 8 |
| Runtime substages per engine | 32 |
| Runtime substages total | 64 |
| Chart-locked macro-stage cells | 16 |
| IGT outcomes per engine | 2 `WIN`, 2 `LOSE`, 2 `win`, 2 `lose` |
| Signed operator variants | 8 |
| Ordered tokens | 16 |
| Non-starred schedule slots | 48 |

Engine signed-operator coverage:

| Engine | UP macro signed variants | DOWN macro signed variants |
|---|---|---|
| Type-1 | `Ti-UP`, `Fe-UP`, `Fi-UP`, `Te-UP` | `Ti-DOWN`, `Fe-DOWN`, `Fi-DOWN`, `Te-DOWN` |
| Type-2 | `Fi-UP`, `Te-UP`, `Fe-UP`, `Ti-UP` | `Ti-DOWN`, `Fe-DOWN`, `Te-DOWN`, `Fi-DOWN` |

## 19. What The Mapping Does And Does Not Earn

The mapping earns a precise scaffold:

```text
which topology maps to which IGT quadrant
which operator/topology ordered tokens exist
which signed variants exist
which Type-1 and Type-2 stage rows are chart-locked
which 16 macro stages are starred in the 8x8 grid
how the current runtime expands 16 macro stages to 64 operator slots
```

It does not earn:

```text
Fe source/runtime closure
64 PEPS3D manifold-cell embedding
final terrain-law GKSL dynamics for every substage
Axis0
flux
Xi/Phi0
physics
I Ching ontology
```

To promote a runtime row from schedule row to manifold cell, a sim still needs:

```text
finite PEPS3D cell anchor
spinor/Hopf/Weyl local state
finite probe/effect response
operator/channel/tensor action
N01 order witness
controls
receipt path
blocked downstream consumers
```

