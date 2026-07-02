# Strategy Loop Engine Semisymmetry Map

Status: candidate comparison atlas, not canon, not a sim receipt, not a
promotion artifact.

This document extends `06_FULL_IGT_MAPPING_ATLAS.md` and
`07_IGT_QIT_FEP_STRATEGY_MATH.md`.

The missing requirement is:

```text
map every ordered strategy token
map each token into its loop position
map each loop into its engine
compare each row to its semisymmetrical equivalent
then define the math witnesses that would make the comparison executable
```

The comparisons below are source-grounded chart maps. They are not yet
nonclassical manifold admissions. A row becomes admissible only when it has the
finite map, spinor-derived density, PEPS3D carrier anchor, controls, and receipt
required by the repo gate.

## 1. Objects That Must Not Be Collapsed

The strategy map has four different levels:

| Level | Object | Example | What changes at this level |
|---|---|---|---|
| Strategy token | ordered topology/operator pair | `NeTi`, `TiNe` | Axis6 order and Axis5 family |
| Loop placement | outer or inner path stage | Type-1 outer `NeTi` | Axis3 placement, result casing, loop family |
| Engine placement | Type-1 or Type-2 macro-stage | `T1-M02`, `T2-M06` | engine orientation, loop assignment, runtime order |
| Runtime slot | macro-stage expanded across slots | `T1-05` through `T1-08` | substage operator slot under one macro context |

The common failure is to read one level as if it proves the next one. It does
not. The token map tells us the intended channel order. The loop map tells us
where the token lives in the chart. The engine map tells us how the loop is
sequenced. The runtime slot map tells us where the four operator slots are
attached. None of those alone proves a PEPS3D cell.

## 2. Channel Notation

Let:

```text
rho          = finite spinor-derived density state
Phi_Se      = Se terrain/channel map
Phi_Ne      = Ne terrain/channel map
Phi_Ni      = Ni terrain/channel map
Phi_Si      = Si terrain/channel map
D_Ti        = Ti dephasing/projection channel
D_Te        = Te dephasing/projection channel
U_Fi        = Fi coherent rotation/unitary channel
U_Fe        = Fe coherent rotation/unitary channel
```

Composition convention:

```text
(A o B)(rho) = A(B(rho))
```

So the written-first side acts first:

```text
TiNe = Phi_Ne o D_Ti
NeTi = D_Ti o Phi_Ne
```

This is the Axis6 distinction. If the two maps commute on a test state, the
strategy token has collapsed for that fixture:

```text
Delta_A6(A,B; rho) = (A o B)(rho) - (B o A)(rho)
```

The row is only informative when a finite norm or effect readout sees a
nonzero difference.

## 3. All 16 Ordered Strategy Channels

The 16 strategy tokens are topology x native operator family x Axis6 order.

| Topology | IGT quadrant | Strategy family | Token | Order | Candidate channel |
|---|---|---|---|---|---|
| `Se` | `LoseWin` | T/dephasing | `TiSe` | operator first / UP | `M_TiSe = Phi_Se o D_Ti` |
| `Se` | `LoseWin` | T/dephasing | `SeTi` | terrain first / DOWN | `M_SeTi = D_Ti o Phi_Se` |
| `Se` | `LoseWin` | F/rotation | `FiSe` | operator first / UP | `M_FiSe = Phi_Se o U_Fi` |
| `Se` | `LoseWin` | F/rotation | `SeFi` | terrain first / DOWN | `M_SeFi = U_Fi o Phi_Se` |
| `Ne` | `WinLose` | T/dephasing | `TiNe` | operator first / UP | `M_TiNe = Phi_Ne o D_Ti` |
| `Ne` | `WinLose` | T/dephasing | `NeTi` | terrain first / DOWN | `M_NeTi = D_Ti o Phi_Ne` |
| `Ne` | `WinLose` | F/rotation | `FiNe` | operator first / UP | `M_FiNe = Phi_Ne o U_Fi` |
| `Ne` | `WinLose` | F/rotation | `NeFi` | terrain first / DOWN | `M_NeFi = U_Fi o Phi_Ne` |
| `Ni` | `LoseLose` | T/dephasing | `TeNi` | operator first / UP | `M_TeNi = Phi_Ni o D_Te` |
| `Ni` | `LoseLose` | T/dephasing | `NiTe` | terrain first / DOWN | `M_NiTe = D_Te o Phi_Ni` |
| `Ni` | `LoseLose` | F/rotation | `FeNi` | operator first / UP | `M_FeNi = Phi_Ni o U_Fe` |
| `Ni` | `LoseLose` | F/rotation | `NiFe` | terrain first / DOWN | `M_NiFe = U_Fe o Phi_Ni` |
| `Si` | `WinWin` | T/dephasing | `TeSi` | operator first / UP | `M_TeSi = Phi_Si o D_Te` |
| `Si` | `WinWin` | T/dephasing | `SiTe` | terrain first / DOWN | `M_SiTe = D_Te o Phi_Si` |
| `Si` | `WinWin` | F/rotation | `FeSi` | operator first / UP | `M_FeSi = Phi_Si o U_Fe` |
| `Si` | `WinWin` | F/rotation | `SiFe` | terrain first / DOWN | `M_SiFe = U_Fe o Phi_Si` |

Direct-frame strategies use `Ti` and `Fi` over `Se`/`Ne`. Conjugated-frame
strategies use `Te` and `Fe` over `Ni`/`Si`.

## 4. Axis5 Meaning: First And Second Strategy

Axis5 is the split between the two strategy families:

```text
T strategy = dephasing/projection/pinching family
F strategy = coherent rotation/unitary family
```

Candidate mathematical difference:

```text
T route:
  D_q(rho) = (1-q) rho + q sum_a P_a rho P_a

F route:
  U(rho) = U rho U*
```

The T route tends to make alternatives legible by suppressing or selecting
coherence relative to a probe basis. It is "cold" only in the strategic sense:
partition, distinction, competition, boundary, adversarial contrast.

The F route tends to preserve, rotate, align, or redistribute coherence. It is
"hot" only in the strategic sense: coupling, coalition, compassion, shared
posterior, affective alignment, coordination. It is not literal thermodynamic
heat unless a later model gives a thermal variable and receipt.

For every topology, the Axis5 comparison is:

```text
Delta_A5(T,F; rho) =
  feature(M_F(rho)) - feature(M_T(rho))
```

Useful features include off-diagonal coherence, mutual information, collective
posterior alignment, payoff, expected free energy, and future option value.

## 5. Type-1 Engine Loop Map

Type-1 has:

```text
orientation tag = IN
outer loop      = deductive order on lifted base loop
inner loop      = inductive order on fiber loop
```

Type-1 outer / major loop:

| Stage | Loop order | Terrain | Strategy token | Axis5 | Axis6 | IGT result | Channel |
|---|---|---|---|---|---|---|---|
| T1-M01 | deductive 1 | `Se-in` | `TiSe` | T | UP | `LOSE` | `Phi_Se o D_Ti` |
| T1-M02 | deductive 2 | `Ne-in` | `NeTi` | T | DOWN | `WIN` | `D_Ti o Phi_Ne` |
| T1-M03 | deductive 3 | `Ni-in` | `NiFe` | F | DOWN | `LOSE` | `U_Fe o Phi_Ni` |
| T1-M04 | deductive 4 | `Si-in` | `FeSi` | F | UP | `WIN` | `Phi_Si o U_Fe` |

Type-1 inner / minor loop:

| Stage | Loop order | Terrain | Strategy token | Axis5 | Axis6 | IGT result | Channel |
|---|---|---|---|---|---|---|---|
| T1-M05 | inductive 1 | `Se-in` | `SeFi` | F | DOWN | `win` | `U_Fi o Phi_Se` |
| T1-M06 | inductive 2 | `Si-in` | `SiTe` | T | DOWN | `win` | `D_Te o Phi_Si` |
| T1-M07 | inductive 3 | `Ni-in` | `TeNi` | T | UP | `lose` | `Phi_Ni o D_Te` |
| T1-M08 | inductive 4 | `Ne-in` | `FiNe` | F | UP | `lose` | `Phi_Ne o U_Fi` |

As ordered loop channels:

```text
L_T1_outer = M_FeSi o M_NiFe o M_NeTi o M_TiSe
L_T1_inner = M_FiNe o M_TeNi o M_SiTe o M_SeFi

E_T1 = L_T1_inner o L_T1_outer
```

The last line is a candidate comparison convention only. Runtime code may use a
different interleaving, and that must be checked before making engine claims.

## 6. Type-2 Engine Loop Map

Type-2 has:

```text
orientation tag = OUT
outer loop      = inductive order on fiber loop
inner loop      = deductive order on lifted base loop
```

Type-2 outer / major loop:

| Stage | Loop order | Terrain | Strategy token | Axis5 | Axis6 | IGT result | Channel |
|---|---|---|---|---|---|---|---|
| T2-M01 | inductive 1 | `Se-out` | `FiSe` | F | UP | `WIN` | `Phi_Se o U_Fi` |
| T2-M02 | inductive 2 | `Si-out` | `TeSi` | T | UP | `WIN` | `Phi_Si o D_Te` |
| T2-M03 | inductive 3 | `Ni-out` | `NiTe` | T | DOWN | `LOSE` | `D_Te o Phi_Ni` |
| T2-M04 | inductive 4 | `Ne-out` | `NeFi` | F | DOWN | `LOSE` | `U_Fi o Phi_Ne` |

Type-2 inner / minor loop:

| Stage | Loop order | Terrain | Strategy token | Axis5 | Axis6 | IGT result | Channel |
|---|---|---|---|---|---|---|---|
| T2-M05 | deductive 1 | `Se-out` | `SeTi` | T | DOWN | `lose` | `D_Ti o Phi_Se` |
| T2-M06 | deductive 2 | `Ne-out` | `TiNe` | T | UP | `win` | `Phi_Ne o D_Ti` |
| T2-M07 | deductive 3 | `Ni-out` | `FeNi` | F | UP | `lose` | `Phi_Ni o U_Fe` |
| T2-M08 | deductive 4 | `Si-out` | `SiFe` | F | DOWN | `win` | `U_Fe o Phi_Si` |

As ordered loop channels:

```text
L_T2_outer = M_NeFi o M_NiTe o M_TeSi o M_FiSe
L_T2_inner = M_SiFe o M_FeNi o M_TiNe o M_SeTi

E_T2 = L_T2_inner o L_T2_outer
```

Again, the engine product is a comparison notation until matched to the runtime
implementation and receipt.

## 7. Strategy-Level Semisymmetry Pairs

Semisymmetry here means:

```text
same topology
same Axis5 strategy family
opposite Axis6 order
opposite Type-1/Type-2 engine placement
usually outer/inner casing flip
```

It is not full symmetry because result sign, casing, loop role, sheet, and
engine orientation do not all remain fixed.

| Pair | Strategy A | Placement A | Strategy B | Placement B | Preserved | Flipped |
|---|---|---|---|---|---|---|
| Se-T | `TiSe / LOSE` | T1 outer, deductive, UP | `SeTi / lose` | T2 inner, deductive, DOWN | `Se`, T-family, deductive walk | Axis6, engine, outer/inner, casing |
| Se-F | `SeFi / win` | T1 inner, inductive, DOWN | `FiSe / WIN` | T2 outer, inductive, UP | `Se`, F-family, inductive walk | Axis6, engine, inner/outer, casing |
| Ne-T | `NeTi / WIN` | T1 outer, deductive, DOWN | `TiNe / win` | T2 inner, deductive, UP | `Ne`, T-family, deductive walk | Axis6, engine, outer/inner, casing |
| Ne-F | `FiNe / lose` | T1 inner, inductive, UP | `NeFi / LOSE` | T2 outer, inductive, DOWN | `Ne`, F-family, inductive walk | Axis6, engine, inner/outer, casing |
| Ni-T | `TeNi / lose` | T1 inner, inductive, UP | `NiTe / LOSE` | T2 outer, inductive, DOWN | `Ni`, T-family, inductive walk | Axis6, engine, inner/outer, casing |
| Ni-F | `NiFe / LOSE` | T1 outer, deductive, DOWN | `FeNi / lose` | T2 inner, deductive, UP | `Ni`, F-family, deductive walk | Axis6, engine, outer/inner, casing |
| Si-T | `SiTe / win` | T1 inner, inductive, DOWN | `TeSi / WIN` | T2 outer, inductive, UP | `Si`, T-family, inductive walk | Axis6, engine, inner/outer, casing |
| Si-F | `FeSi / WIN` | T1 outer, deductive, UP | `SiFe / win` | T2 inner, deductive, DOWN | `Si`, F-family, deductive walk | Axis6, engine, outer/inner, casing |

This table is the direct answer to the `NeTi` versus `TiNe` question generalized
to all strategies. `NeTi` and `TiNe` are one row of a broader eight-pair
semisymmetry system.

## 8. Loop-Level Semisymmetry

The loop-level semisymmetries are stronger than the single-token pairs because
they preserve the topology walk.

### 8.1 Deductive Semisymmetry

Type-1 outer and Type-2 inner both use the deductive topology walk:

```text
Se -> Ne -> Ni -> Si
```

But Type-1 realizes it as outer/major/IN while Type-2 realizes it as
inner/minor/OUT.

| Deductive step | T1 outer | T2 inner | Same | Different |
|---|---|---|---|---|
| 1 | `Se-in : TiSe : LOSE : UP` | `Se-out : SeTi : lose : DOWN` | `Se`, T-family | Axis6, sheet, casing |
| 2 | `Ne-in : NeTi : WIN : DOWN` | `Ne-out : TiNe : win : UP` | `Ne`, T-family | Axis6, sheet, casing |
| 3 | `Ni-in : NiFe : LOSE : DOWN` | `Ni-out : FeNi : lose : UP` | `Ni`, F-family | Axis6, sheet, casing |
| 4 | `Si-in : FeSi : WIN : UP` | `Si-out : SiFe : win : DOWN` | `Si`, F-family | Axis6, sheet, casing |

Candidate loop difference:

```text
Delta_deductive(rho) =
  L_T1_outer(rho) - L_T2_inner(rho)
```

That is not expected to be zero. The point is to measure what survives the
semisymmetry after sheet, casing, and Axis6 are flipped.

### 8.2 Inductive Semisymmetry

Type-1 inner and Type-2 outer both use the inductive topology walk:

```text
Se -> Si -> Ni -> Ne
```

But Type-1 realizes it as inner/minor/IN while Type-2 realizes it as
outer/major/OUT.

| Inductive step | T1 inner | T2 outer | Same | Different |
|---|---|---|---|---|
| 1 | `Se-in : SeFi : win : DOWN` | `Se-out : FiSe : WIN : UP` | `Se`, F-family | Axis6, sheet, casing |
| 2 | `Si-in : SiTe : win : DOWN` | `Si-out : TeSi : WIN : UP` | `Si`, T-family | Axis6, sheet, casing |
| 3 | `Ni-in : TeNi : lose : UP` | `Ni-out : NiTe : LOSE : DOWN` | `Ni`, T-family | Axis6, sheet, casing |
| 4 | `Ne-in : FiNe : lose : UP` | `Ne-out : NeFi : LOSE : DOWN` | `Ne`, F-family | Axis6, sheet, casing |

Candidate loop difference:

```text
Delta_inductive(rho) =
  L_T1_inner(rho) - L_T2_outer(rho)
```

Again, the desired readout is not equality. The desired readout is which
features are invariant, which reverse sign, and which collapse under controls.

## 9. Engine-Level Comparison

At the engine level the comparison is:

```text
E_T1 = [TiSe, NeTi, NiFe, FeSi, SeFi, SiTe, TeNi, FiNe]
E_T2 = [FiSe, TeSi, NiTe, NeFi, SeTi, TiNe, FeNi, SiFe]
```

These are ordered application lists. If written as channel products:

```text
E_T1(rho) =
  M_FiNe(M_TeNi(M_SiTe(M_SeFi(M_FeSi(M_NiFe(M_NeTi(M_TiSe(rho))))))))

E_T2(rho) =
  M_SiFe(M_FeNi(M_TiNe(M_SeTi(M_NeFi(M_NiTe(M_TeSi(M_FiSe(rho))))))))
```

Engine-level semisymmetry is partial:

| Engine feature | Type-1 | Type-2 | Relation |
|---|---|---|---|
| orientation tag | IN | OUT | flipped |
| outer loop family | deductive | inductive | swapped |
| inner loop family | inductive | deductive | swapped |
| major casing | `WIN/LOSE` | `WIN/LOSE` | preserved as outer result class |
| minor casing | `win/lose` | `win/lose` | preserved as inner result class |
| topology coverage | Se, Ne, Ni, Si twice | Se, Si, Ni, Ne twice | preserved set, different order |
| Axis5 coverage | four T, four F | four T, four F | preserved count |
| Axis6 coverage | four UP, four DOWN | four UP, four DOWN | preserved count |
| token identities | 8 of 16 | complementary 8 of 16 | partitioned |

The engine comparison witness should therefore not ask whether `E_T1 == E_T2`.
It should ask:

```text
Which effects are invariant under engine swap?
Which effects reverse under IN/OUT?
Which effects follow the loop family rather than the engine type?
Which effects follow Axis5 T/F rather than topology?
Which effects vanish when Axis6 order is erased?
```

## 10. Runtime-64 Slot Comparison Rule

The 64 runtime rows are:

```text
2 engines x 8 macro stages x 4 operator slots
```

For strategy comparison, a runtime slot inherits:

```text
engine type
macro stage
loop placement
topology
terrain ID
macro strategy token
macro result
Axis5 family
Axis6 order
slot operator in [Ti, Te, Fi, Fe]
```

The slot operator is not the same object as the macro strategy token. Example:

```text
T1-M02 macro token = NeTi
T1-05 slot = Ti under NeTi context
T1-06 slot = Te under NeTi context
T1-07 slot = Fi under NeTi context
T1-08 slot = Fe under NeTi context
```

Candidate slot maps must declare their convention:

```text
slot-after-macro:   R_{m,s}(rho) = O_s(M_m(rho))
slot-before-macro:  R_{m,s}(rho) = M_m(O_s(rho))
interleaved:        R_{m,s} uses a runtime-specific carrier update
context-only:       slot is a readout/probe under macro context, not a channel
```

Until that convention is tied to code and controls, runtime slot rows are
schedule/context rows, not PEPS3D substage cells.

## 11. Strategy Interpretation By Quadrant

This section translates the chart into game-theoretic strategy hypotheses. It
does not moralize the rows and does not claim psychology.

| Topology | IGT quadrant | T route | F route | Candidate strategic reading |
|---|---|---|---|---|
| `Ne` | `WinLose` | `NeTi` / `TiNe` | `FiNe` / `NeFi` | expansion through possibility-generation plus later selection; can create a major public win and a minor/local loss depending on route |
| `Si` | `WinWin` | `SiTe` / `TeSi` | `FeSi` / `SiFe` | stabilization, shared retention, institutional cooperation; both major and minor reads trend positive in the current chart |
| `Se` | `LoseWin` | `TiSe` / `SeTi` | `SeFi` / `FiSe` | immediate exposure or sacrifice can convert to minor/major win under the paired route |
| `Ni` | `LoseLose` | `TeNi` / `NiTe` | `NiFe` / `FeNi` | contraction, closure, austerity, collapse-risk, or severe filtering; current chart keeps both reads negative |

The user-supplied "lose can be common" idea fits especially into routes where:

```text
local payoff decreases
collective information or coalition value increases
future option value increases
shared posterior alignment increases
credibility or commitment increases
```

This should be measured as:

```text
Delta payoff_i < 0

Delta G_i =
  Delta payoff_i
  - beta Delta F_Q
  + lambda Delta I_collective
  + mu Delta Z_future
  + nu Delta C_credibility
  - Delta path_cost
```

The "play the victim" strategy belongs here only as a candidate channel family:
a public local-loss signal can couple observers, increase mutual information,
shift coalition priors, and make future collective action cheaper. It can be
deceptive, honest, compassionate, adaptive, or maladaptive depending on the
finite path and payoff/information readouts. The label alone decides nothing.

## 12. Comparison Metrics For Each Level

Every level should have its own finite witness.

### 12.1 Strategy-token witness

For Axis6 pairs:

```text
W_strategy(token_a, token_b; rho, E) =
  || E(M_a(rho)) - E(M_b(rho)) ||
```

where `E` is a finite effect/probe family. The key control is order erasure:

```text
M_a = M_b after order erasure
```

If order erasure does not collapse the signal, the witness is probably seeing a
different confound.

### 12.2 Axis5 T/F witness

For T/F pairs inside one topology:

```text
W_A5(T,F; rho) =
  [
    C_offdiag(M_F(rho)) - C_offdiag(M_T(rho)),
    I_collective(M_F(rho)) - I_collective(M_T(rho)),
    payoff(M_F(rho)) - payoff(M_T(rho)),
    G(M_F(rho)) - G(M_T(rho))
  ]
```

Expected candidate pattern:

```text
F route preserves or redirects coherence/coupling more than T route
T route makes boundary/projection readouts sharper than F route
```

That is a hypothesis to test, not a doctrine.

### 12.3 Loop witness

For deductive and inductive loop pairs:

```text
W_loop =
  [
    effect_vector(L_A(rho)) - effect_vector(L_B(rho)),
    entropy_path(L_A) - entropy_path(L_B),
    order_sensitivity_path(L_A) - order_sensitivity_path(L_B),
    coalition_or_payoff_path(L_A) - coalition_or_payoff_path(L_B)
  ]
```

Controls:

```text
shuffle topology order
erase Axis6 order
force all routes T-only
force all routes F-only
swap IN/OUT labels without changing channels
```

### 12.4 Engine witness

For full engine paths:

```text
W_engine(E_T1,E_T2; rho) =
  [
    final_effect_gap,
    path_entropy_gap,
    mutual_information_gap,
    free_energy_gap,
    order_erasure_gap,
    loop_swap_gap,
    slot_ablation_gap
  ]
```

Controls:

```text
single-engine only
wrong semisymmetry pairing
same topology order with random tokens
same tokens with shuffled topology order
classical diagonal-only density
commuting operators only
no PEPS3D carrier anchor
```

### 12.5 Runtime-slot witness

For 64-slot claims:

```text
W_slot(R_{m,s}, R_{m',s'}; rho)
```

must name whether the slot is a channel, probe, tensor-cell action, or context
readout. Without that, the 64 rows stay a runtime scaffold.

## 13. Minimal Sim Ratchet From This Map

The admissible ratchet is:

1. Pick one semisymmetry pair, such as `NeTi` vs `TiNe`.
2. Build torch-native finite density states from admitted spinor carriers.
3. Attach a finite PEPS3D site/bond/cell anchor from the start.
4. Implement both channel orders.
5. Run order-erased, label-erased, commuting, diagonal-only, and wrong-pair controls.
6. Measure strategy-token witnesses.
7. Only after one pair is clean, run all eight semisymmetry pairs.
8. Only after pair-level receipts are clean, run loop-level deductive and inductive witnesses.
9. Only after loop-level receipts are clean, run engine-level comparison.
10. Only after engine-level receipts are clean, attempt runtime-64 slot-cell embedding.

The first full target should not be "prove the 64 engine". It should be:

```text
one finite PEPS3D-carried spinor-density pair
one Axis6 semisymmetry witness
one T/F Axis5 contrast
one negative/control battery
one receipt with blocked downstream consumers
```

## 14. Nonclaim Boundary

This map does not prove:

```text
IGT is final game theory
Jung labels are substrate
I Ching slots are ontology
Type-1 and Type-2 are physically complete engines
64 runtime rows are PEPS3D cells
F routes are literally heat
T routes are literally cold
liberal politics reduces to F strategy
victim strategy is always deceptive or always good
Axis0, flux, Xi, Phi0, Holodeck, or physics
```

It does provide a complete candidate comparison scaffold for:

```text
all 16 strategy tokens
all 4 engine loops
both engine paths
all 8 same-topology semisymmetry pairs
deductive and inductive loop semisymmetry
runtime-64 slot comparison obligations
```

