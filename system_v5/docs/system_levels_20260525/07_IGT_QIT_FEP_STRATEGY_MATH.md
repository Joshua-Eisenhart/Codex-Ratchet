# IGT QIT-FEP Strategy Math

Status: candidate strategy-math bridge, not canon, not a promotion receipt.

This file answers the gap left by the mapping atlas: the atlas maps labels and
schedule slots, but it does not yet say what an IGT strategy means
mathematically. This document translates the current IGT grammar into a
candidate QIT/FEP/game-theoretic math surface while keeping source constraints
visible.

## 1. Three Different Flips

Do not collapse these:

| Axis | Flip | Example | What changes |
|---|---|---|---|
| Axis6 | precedence/order | `NeTi` vs `TiNe` | terrain-first vs operator-first composition |
| Axis3/chart placement | outer vs inner | Type-1 outer `NeTi` vs Type-2 inner `TiNe` | density-visible/base-like major stage vs fiber/inner minor stage in the current chart |
| Axis5 | first vs second strategy | `T` strategy vs `F` strategy | dephasing/projection family vs rotation/coherence family |

`NeTi` and `TiNe` are not different because the labels point at different
terrain or operator families. They use the same topology and the same operator
family:

```text
Ne = Hamiltonian/tangential circulation terrain family
Ti = z-basis dephasing/projection operator family
```

They differ because Axis6 changes the order:

```text
NeTi = terrain-first / Ti-DOWN
TiNe = operator-first / Ti-UP
```

In the current chart that Axis6 swap also lands them on different Axis3
placements:

```text
NeTi = Type-1 outer Ne, major result WIN
TiNe = Type-2 inner Ne, minor result win
```

That is not a final theorem that Axis6 always equals Axis3. It is the current
chart correlation that future sims must either preserve or falsify.

## 2. The Local Math: NeTi vs TiNe

Let:

```text
Phi_Ne = Ne terrain/channel map
Pi_Ti  = Ti dephasing/projection channel
```

For the Ne terrain, the source terrain packet gives the clean Hamiltonian
circulation form:

```text
Phi_Ne,L(rho) ~= exp(dt L_Ne,L)(rho)
L_Ne,L(rho) = -i[H_L, rho]

Phi_Ne,R(rho) ~= exp(dt L_Ne,R)(rho)
L_Ne,R(rho) = -i[H_R, rho]
H_R = -H_L
```

For `Ti`, the operator packet gives the z-pinch/dephasing channel:

```text
P_0 = (I + sigma_z)/2
P_1 = (I - sigma_z)/2

Pi_Ti,q(rho) =
  (1-q) rho + q(P_0 rho P_0 + P_1 rho P_1)
```

Axis6 order gives two distinct maps:

```text
terrain-first:
  M_NeTi(rho) = Pi_Ti(Phi_Ne(rho))

operator-first:
  M_TiNe(rho) = Phi_Ne(Pi_Ti(rho))
```

Their difference is the order witness:

```text
Delta_A6(Ne,Ti; rho) =
  Pi_Ti(Phi_Ne(rho)) - Phi_Ne(Pi_Ti(rho))
```

This is the actual mathematical content of the label difference. If the order
witness is zero for the chosen carrier, probe, and controls, then the label swap
did not earn a noncommuting distinction.

Interpretation:

```text
NeTi:
  let Ne circulation move the state, then Ti pinches/projects/reads it.
  This is terrain-first, Type-1 outer, major WIN in the current chart.

TiNe:
  let Ti pinch/project first, then Ne circulation evolves the already-filtered
  state.
  This is operator-first, Type-2 inner, minor win in the current chart.
```

So `NeTi` has a more public/outer read in the current chart: circulation is
allowed to create or expose structure before the dephasing/projection operator
selects it. `TiNe` first filters the state, then circulation moves the
filtered state; that makes it an inner/minor success in the chart rather than
the same major strategy.

## 3. The Parallel Local Math: FeSi vs SiFe

`FeSi` and `SiFe` are the same kind of Axis6 pair but in the F/rotation family:

```text
Si = stratified/invariant-subspace terrain family
Fe = z-rotation family in the read-only operator packet
```

Let:

```text
Phi_Si = Si terrain/channel map
U_Fe   = Fe unitary rotation channel
```

Source-style Si terrain:

```text
L_Si(rho) =
  -i[H_C, rho]
  + sum_j kappa_j(P_j rho P_j - 1/2(P_j rho + rho P_j))

with [H_C, P_j] = 0
```

Fe operator packet:

```text
U_z(phi) =
  [[exp(-i phi/2), 0],
   [0, exp(i phi/2)]]

U_Fe(rho) = U_z(phi) rho U_z(phi)^dagger
```

Axis6 order:

```text
FeSi = operator-first / Fe-UP:
  M_FeSi(rho) = Phi_Si(U_Fe(rho))

SiFe = terrain-first / Fe-DOWN:
  M_SiFe(rho) = U_Fe(Phi_Si(rho))
```

Order witness:

```text
Delta_A6(Si,Fe; rho) =
  Phi_Si(U_Fe(rho)) - U_Fe(Phi_Si(rho))
```

Current chart placements:

```text
FeSi = Type-1 outer Si, major WIN
SiFe = Type-2 inner Si, minor win
```

Interpretation:

```text
FeSi:
  rotate/couple phase first, then stabilize/stratify in Si.

SiFe:
  stratify/protect first, then rotate inside or across the protected structure.
```

This is why the same apparent "function pair" can have different strategic
meaning after Axis6 and Axis3 are included.

## 4. Axis5: First Strategy Versus Second Strategy

Axis5 is the first/second strategy split. In the current math packet, the clean
operator-family version is:

```text
T-strategy = dephasing/projection/pinching family
  {Ti, Te}

F-strategy = coherent rotation/unitary family
  {Fi, Fe}
```

This is not just a label. The two families act differently on information.

T-strategy:

```text
Pi(rho) = sum_a P_a rho P_a
```

or partially:

```text
Pi_q(rho) = (1-q)rho + q sum_a P_a rho P_a
```

T-strategy selects, distinguishes, partitions, and makes some alternatives
classically legible. It is "cold" in the strategy sense because it tends toward
selection, competition, exclusion, or measurement-like commitment. It may
increase von Neumann entropy under dephasing, so "cold" must not be read as a
literal temperature claim unless a thermodynamic model is supplied.

F-strategy:

```text
U(rho) = U rho U^dagger
```

F-strategy rotates, phase-aligns, preserves coherence, or changes relational
orientation without immediately pinching alternatives. It is "hot" in the
strategy sense because it can support coupling, coordination, coalition, and
cooperative interference before a later projection resolves the alternatives.
Again, "hot" is a strategy/coordination reading unless separately tied to a
thermal model.

## 5. IGT Quadrants As Strategy Pairs

Current quadrant map:

| Topology | IGT quadrant | T-strategy | F-strategy |
|---|---|---|---|
| `Ne` | `WinLose` | `NeTi` | `FiNe` |
| `Si` | `WinWin` | `SiTe` | `FeSi` |
| `Se` | `LoseWin` | `TiSe` | `SeFi` |
| `Ni` | `LoseLose` | `TeNi` | `NiFe` |

This says each perceiving topology carries two strategy routes:

```text
T route = dephasing/projection route
F route = rotation/cooperation route
```

The IGT quadrant then records the current chart result signs for those routes.

For `Ne / WinLose`:

```text
T-strategy: NeTi -> WIN in Type-1 outer chart
F-strategy: FiNe -> lose in Type-1 inner chart
```

But Type-2 flips the placements:

```text
NeFi -> LOSE in Type-2 outer chart
TiNe -> win in Type-2 inner chart
```

So "WinLose" is not one move. It is a topology-level strategy profile with
different results depending on:

```text
Axis5: T vs F strategy
Axis6: operator-first vs terrain-first
Axis3/chart: outer vs inner placement
engine type: Type-1 vs Type-2
```

## 6. Classical Game Theory Translation

Classical game theory normally starts with:

```text
players i = 1..n
actions a_i in A_i
joint action a = (a_1, ..., a_n)
payoff u_i(a)
mixed strategy p_i over A_i
```

The QIT-FEP translation should not merely rename `p_i` as `rho`. It needs a
finite operational carrier:

```text
H_i = finite strategy Hilbert space for player i
rho = joint strategy/cut/world state in D(tensor_i H_i)
E_i = finite effect/payoff/probe family
u_i becomes an observable or effect-weighted payoff functional
strategy move = channel/instrument, not just probability vector
history = finite noncommuting instrument path
```

A classical payoff can be embedded as a diagonal payoff observable:

```text
U_i = sum_a u_i(a) |a><a|
Payoff_i(rho) = Tr(U_i rho)
```

But the nonclassical part enters when strategies are channels/instruments and
order matters:

```text
rho_h = K_h rho K_h^dagger / Tr(K_h rho K_h^dagger)
h = finite strategy/history path
```

Then a QIT-FEP-aligned objective can be written as a candidate functional:

```text
G_i(pi_i, pi_-i) =
  E_h[Tr(U_i rho_h)]
  - beta_i F_Q(rho_h)
  + lambda_i I_i(cut_h)
  - c_i(path_h)
```

where:

```text
F_Q = finite quantum free-energy-like term
I_i = coherent information, mutual information, or coalition/cut information
c_i = cost of strategy path, commitment, or control
```

This is only a candidate bridge. It becomes admissible only when the carrier,
effects, instruments, controls, and result receipts exist.

## 7. Why A Lose Can Be A Common Strategy

In this framework, `LOSE` or `lose` is not automatically "bad." It is a signed
stage result inside a larger path functional.

A local loss can be globally adaptive if it increases:

```text
coalition support
future option value
credibility / commitment
mutual information across a group
shared posterior alignment
collective action capacity
sympathy / compassion response
```

Candidate inequality:

```text
immediate local payoff loss:
  Delta Payoff_i < 0

but path-level gain:
  Delta G_i =
    Delta Payoff_i
    - beta Delta F_Q
    + lambda Delta I_collective
    + mu Delta Z_future
    - Delta cost
  > 0
```

This is the mathematical shape behind a "play the victim" or
compassion-organizing strategy. It is not just deception or weakness. It can be
a real strategic channel:

```text
accept or display local loss
shift observers' posterior
increase coalition mutual information
increase group coordination
increase future action capacity
```

In ordinary political language, this is why some compassionate or grievance
frames can organize large-scale collective action. In the math, the local
negative payoff is outweighed by a positive change in group-level information,
coordination, and future path value.

This should be tested, not canonized.

## 8. F Strategies As Cooperative / Hot

The F family is cooperative in this candidate reading because it is rotation
and coupling before pinching:

```text
rho -> U rho U^dagger
```

That allows:

```text
phase alignment
coherence preservation
correlation building
coalition formation
joint posterior movement
```

The T family is competitive/cold in this candidate reading because it is
projection and distinction:

```text
rho -> sum_a P_a rho P_a
```

That allows:

```text
classification
commitment
exclusion
selection
legible win/loss partitioning
```

Neither family is morally better. They are different strategy operators. A
large-scale social strategy may combine them:

```text
F route:
  build shared affective/cooperative coherence

T route:
  project that coherence into legible claims, boundaries, opponents, demands,
  institutions, or policy choices
```

That combined route is where the IGT/game-theory mapping becomes interesting.

## 9. Strategy Correlation Probes To Build

Candidate formal scouts:

1. Axis6 order witness for paired tokens:

```text
Delta_A6(Ne,Ti; rho) =
  Pi_Ti(Phi_Ne(rho)) - Phi_Ne(Pi_Ti(rho))

Delta_A6(Si,Fe; rho) =
  Phi_Si(U_Fe(rho)) - U_Fe(Phi_Si(rho))
```

Controls:

```text
commuting Phi_T and O control
order-erased control
outer/inner erased control
sheet-erased control
```

2. Axis5 T/F strategy separation:

```text
T route = dephasing/projection channel
F route = rotation/unitary channel
```

Readouts:

```text
payoff
entropy
coherent information
mutual information
coalition cut response
future option count
```

3. Local loss / global coalition gain:

```text
Delta Payoff_i < 0
Delta I_collective > 0
Delta G_i > 0
```

Controls:

```text
no-observer control
no-coalition channel control
shuffle group labels
replace F route with T-only route
erase future path term
```

4. "Hot" cooperative F strategy:

```text
F channel increases or preserves correlation/coherence before projection
T-only control loses the coalition/coherence signal
```

Controls:

```text
dephase before F
random phase rotation
product-state-only carrier
commuting-only histories
```

## 10. Nonclaim Boundary

This document is a math bridge proposal. It does not prove:

```text
that IGT is game theory
that liberal politics is reducible to one token
that victim strategy is always deceptive or always good
that F is literally thermodynamic heat
that T is literally thermodynamic cold
that Axis5/Axis6/Axis3 correlations are final
```

It does state the next admissible research target:

```text
IGT strategy claims must become finite channel/instrument/path functionals with
payoff, information, free-energy, order, and coalition controls.
```

