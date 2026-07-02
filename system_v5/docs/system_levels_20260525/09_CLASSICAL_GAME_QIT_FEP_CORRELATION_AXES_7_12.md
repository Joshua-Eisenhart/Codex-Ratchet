# Classical Game To QIT-FEP Correlation Space And Axes 7-12 Shadow Map

Status: exploratory correlation space, not canon, not an axis definition, not a
sim receipt, not a promotion artifact.

This document records the next exploratory space after the single-engine IGT
strategy maps:

```text
classical game theory math
-> QIT-FEP lift aligned to the engine model
-> population / game-world simulations
-> possible mirror axes 7-12 as collective constraints
```

The point is not to declare axes 7-12. The point is to make the open problem
precise enough that later sims can explore it without turning speculation into
doctrine.

## 1. The Bootstrap Problem

The current working map covers axes 1-6 as local/single-engine or
single-chart-family distinctions. It is still not fully earned. The proposed
axes 7-12 are not available as definitions yet.

The hard dependency is:

```text
axes 1-6 give each engine its local coordinate grammar
axes 7-12, if real, act over collectives of engines
```

The tricky part is that the collective manifold may expose structure that is
hard to see at the single-engine level:

```text
bottom-up constraint:
  cannot define collective axes until each engine has stable local axes

top-down clue:
  population/game-world dynamics may reveal the natural collective variables
  before the formal local-to-collective derivation is finished
```

This is why axes 7-12 should be handled as shadow axes or mirror candidates:
they are allowed to guide exploratory correlation scans, but they must not
become repo truth until the lower map and carrier gates are earned.

## 2. Classical Game Baseline

Start with a finite classical game:

```text
players i in {1, ..., N}
action set A_i
joint action a = (a_1, ..., a_N)
payoff u_i(a)
mixed strategy p_i in Delta(A_i)
joint mixed state p(a)
interaction graph or hypergraph G
history h = (a^0, a^1, ..., a^T)
```

Classical correlation features worth keeping:

| Classical feature | Formula sketch | What it sees |
|---|---|---|
| Expected payoff | `E[u_i] = sum_a p(a) u_i(a)` | local payoff pressure |
| Payoff covariance | `Cov(u_i,u_j)` | whether players' outcomes align or conflict |
| Pareto gap | `max_a sum_i u_i(a) - sum_i E[u_i]` | collective inefficiency |
| Nash/exploitability gap | `max_{a_i'} E[u_i(a_i',a_-i)] - E[u_i]` | unilateral incentive pressure |
| Coalition value | `V(C) = E[sum_{i in C} u_i]` | group advantage |
| Local-loss/global-gain | `Delta u_i < 0`, `Delta V(C) > 0` | sacrifice, victim, compassion, coalition strategies |
| Strategy-response Jacobian | `d p_i' / d p_j` | who moves whom |
| Replicator/mirror update | `p_i' proportional p_i exp(eta u_i)` | adaptive selection dynamics |

This classical baseline is useful because it gives controls. If a claimed
QIT-FEP pattern does not beat or distinguish the classical baseline, the lift
has not earned anything.

## 3. QIT-FEP Lift

The QIT-FEP lift replaces classical probability vectors with finite operational
states, effects, and channels:

```text
H_i             = finite strategy / observation / memory Hilbert space
rho_i           = local engine state
rho_G           = joint population state on tensor_i H_i
E_i             = finite effect/probe family for player i
U_i             = diagonal payoff observable lifted from u_i
M_i             = local engine strategy channel
C_{ij}          = interaction channel between engines i and j
C_C             = coalition or hyperedge channel over C
Pi_i            = finite instrument / policy path for player i
h               = finite history of channels and effects
```

Payoff lift:

```text
U_i = sum_a u_i(a) |a><a|
Payoff_i(rho_G) = Tr(U_i rho_G)
```

Correlation lift:

```text
Cov_Q(i,j) =
  Tr((U_i tensor U_j) rho_G)
  - Tr(U_i rho_G) Tr(U_j rho_G)
```

Information lift:

```text
I_Q(i:j) = S(rho_i) + S(rho_j) - S(rho_ij)

TotalCorr(C) =
  sum_{i in C} S(rho_i) - S(rho_C)
```

FEP-aligned path objective:

```text
G_i(path) =
  E_h[Tr(U_i rho_h)]
  - beta_i F_Q(rho_h)
  + lambda_i I_Q(i:C_h)
  + mu_i Z_future(h)
  + nu_i Credibility_i(h)
  - cost_i(h)
```

The terms are candidate readouts:

| Term | Meaning |
|---|---|
| `Tr(U_i rho_h)` | payoff or reward |
| `F_Q` | finite free-energy-like surprise / model mismatch term |
| `I_Q(i:C_h)` | individual-to-coalition information coupling |
| `Z_future` | future option value or reachable-path count |
| `Credibility_i` | commitment / signal reliability / reputation readout |
| `cost_i` | effort, risk, constraint, or control cost |

This is where a local loss can be strategically common:

```text
Delta Payoff_i < 0
Delta G_i > 0
```

The local payoff term loses, but coalition information, future option value, or
credibility can make the path-level objective positive.

## 4. Engine As Character, Engine-Time As Map Point

The larger exploratory picture is a finite game world:

```text
each character = one engine instance
each engine-time = one point on the population map
each point carries local engine coordinates
```

Define a finite event set:

```text
V = {(i, t, m, s)}
```

where:

```text
i = engine / character id
t = world time
m = macro-stage or loop position
s = optional runtime slot
```

Each event point can carry:

```text
engine_type in {T1, T2}
terrain/topology
loop placement
Axis3 outer/inner placement
Axis5 T/F strategy family
Axis6 order
IGT result casing
local state rho_{i,t,m,s}
local effect vector e_{i,t,m,s}
```

Edges and hyperedges:

| Edge type | Example | Meaning |
|---|---|---|
| temporal | `(i,t)->(i,t+1)` | engine memory / path continuity |
| stage | `(i,t,m)->(i,t,m+1)` | engine loop traversal |
| interaction | `(i,t)->(j,t)` | pairwise game contact |
| coalition hyperedge | `{i,j,k,...}` | collective strategy / group signal |
| observation | `world -> i` | perception / evidence update |
| action | `i -> world` | intervention / policy effect |
| PEPS3D bond/cell | local finite carrier anchor | nonclassical manifold carrier obligation |

The population state can be represented as:

```text
rho_G(t) on tensor_i H_i
```

or, for scalable exploration:

```text
finite tensor network / PEPS3D-like carrier over the event graph
```

This is not yet the admitted PEPS3D manifold. It is the exploratory graph on
which a future admitted carrier would have to live.

## 5. Axes 7-12 As Shadow Collective Axes

Axes 7-12 are not defined. The table below is only a placeholder for what their
job might be if they are mirror axes over collectives.

| Shadow axis | Mirrors local axis | Collective question | Candidate math object | Blocker |
|---|---|---|---|---|
| A7 shadow | A1 polarity/family split | which groups align or oppose across terrain outcome families? | coalition partition / payoff-sign covariance / group boundary cut | A1 must be stable locally |
| A8 shadow | A2 adjacency/quadrant split | which collective routes connect or separate game quadrants? | interaction graph cut / hypergraph incidence / quadrant transition kernel | A2 must be stable locally |
| A9 shadow | A3 inner/outer | what is private/internal to an engine versus public/collective signal? | hidden/public state split, observation instrument, public-effect projection | A3 must be stable locally |
| A10 shadow | A4 loop family | how does a coalition order deductive and inductive updates? | population loop schedule, causal path order, group memory cycle | A4 must be stable locally |
| A11 shadow | A5 T/F strategy | when does the collective project/compete versus cohere/cooperate? | T/F channel mixture over coalition state, coherence-vs-projection readout | A5 must be stable locally |
| A12 shadow | A6 precedence/order | does norm/action/control come first, or does terrain/evidence come first? | noncommuting collective channel order, policy-before-evidence vs evidence-before-policy witness | A6 must be stable locally |

These names are intentionally weak. The actual axes may not match this table.
The table only preserves the intuition that axes 7-12 are collective mirrors
rather than another copy of the local engine axes.

## 6. Why The Geometric Constraint Manifold Might See A7-A12 First

The individual engine map asks:

```text
what is the local channel, loop, terrain, and order?
```

The geometric constraint manifold may instead ask:

```text
what finite multi-engine states survive all constraints at once?
```

That makes collective axes plausible because some constraints only appear over
relations:

```text
coalition alignment
public/private signal separation
multi-agent causal order
shared posterior / common knowledge
group memory loop
multi-engine PEPS3D cell compatibility
```

So the paradox is real:

```text
you need axes 1-6 to label each engine point
but the manifold over many engine points may reveal the axes 7-12 constraints
more naturally than a single engine does
```

The safe resolution is a two-level exploratory loop:

```text
local-first:
  keep axes 1-6 as the required coordinate grammar for each engine point

population-first:
  let classical and QIT-FEP population sims search for stable collective
  invariants, but keep them as A7-A12 candidates only
```

## 7. Classical-To-QIT Correlation Pipeline

A useful pipeline should run the same game in multiple representations.

### 7.1 Classical Baseline

```text
finite agents
finite actions
payoff tensors
interaction graph or hypergraph
classical mixed strategies
classical dynamics: best response, replicator, mirror descent, or finite policy tree
```

Readouts:

```text
payoff
payoff covariance
Nash gap
Pareto gap
coalition value
local-loss/global-gain frequency
strategy-response Jacobian
```

### 7.2 Engine-Labeled Classical Baseline

Attach local engine labels without changing the classical dynamics:

```text
engine type
IGT quadrant
Axis3 placement
Axis5 T/F family
Axis6 order
loop family
```

Control purpose:

```text
if labels alone predict everything, the model has not earned nonclassical
content; it has only built a classifier over the classical simulation.
```

### 7.3 QIT-FEP Lift

Replace strategy updates with finite channels/instruments:

```text
rho_G(t+1) =
  C_interaction(
    tensor_i M_i^{engine/path}(rho_G(t))
  )
```

Readouts:

```text
Payoff_i(rho_G)
F_Q(rho_G)
I_Q(i:j)
TotalCorr(C)
coherence / off-diagonal survival
order witness Delta_A6
collective T/F witness Delta_A11_candidate
```

### 7.4 Geometry/Carrier Attempt

Only after the channel/instrument comparison works:

```text
attach finite PEPS3D site/bond/cell anchors
test one local cell
test one interaction bond
test one coalition hyperedge
test order-erased and label-erased controls
```

This is where exploratory population work could start to pressure the
geometric constraint manifold without claiming closure.

## 8. Pattern Families To Look For

The interesting patterns are correlations across levels, not label matches.

| Pattern | Classical readout | QIT-FEP readout | Possible shadow-axis clue |
|---|---|---|---|
| Local loss becomes collective gain | `Delta u_i < 0`, `Delta V(C) > 0` | `Delta Payoff_i < 0`, `Delta G_i > 0` | A7/A11 |
| Cooperation outperforms competition only after projection | coalition payoff rises after F then T | coherence rises under F, payoff realized after T | A11 then A12 |
| Public signal differs from private engine state | action visible, motive hidden | public effect projection differs from local density | A9 |
| Group memory changes strategy value | history-dependent payoff | process-tensor / path objective changes sign | A10 |
| Order of collective interpretation matters | policy-first vs evidence-first gives different equilibrium | nonzero collective order witness | A12 |
| Engine type matters only in population | T1/T2 same locally, diverges under interaction | interaction channel separates engine sheets | A7/A8/A10 |
| Manifold sees relation before local labels settle | graph invariant predicts outcome better than token labels | tensor-network / hypergraph invariant survives controls | A7-A12 candidate |

These are correlation targets. They do not define the axes.

## 9. Controls That Prevent Canon Drift

Every exploratory run needs controls:

```text
label-erased control
Axis5-erased control
Axis6-order-erased control
engine-type-erased control
randomized interaction graph
randomized payoff tensor
classical diagonal-only density
product-state-only carrier
no-coalition channel
no-public-signal channel
wrong semisymmetry pairing
single-agent-only collapse
```

If a claimed A7-A12 signal survives only in the labeled run and disappears
under the math readouts, it is not a collective axis. If it survives after
labels are erased but the finite interaction/channel structure remains, it may
be a real candidate invariant.

## 10. Minimum Exploratory Sim Sequence

The first exploratory sequence should be deliberately small:

1. Two to four agents only.
2. Two actions per agent.
3. Two engine types.
4. One IGT quadrant pair first, such as `Ne/WinLose` against `Si/WinWin`.
5. Classical payoff matrix with known equilibria.
6. Classical readouts: payoff, Nash gap, coalition value, local-loss/global-gain.
7. Engine-labeled classical control.
8. QIT-FEP channel lift with diagonal payoff observables.
9. One Axis6 order witness.
10. One Axis5 T/F witness.
11. One coalition information witness.
12. Label-erased and order-erased controls.

Only after that works should the sim scale to:

```text
all 16 strategy tokens
all 8 semisymmetry pairs
multi-time histories
population graphs
coalition hyperedges
candidate A7-A12 shadow readouts
PEPS3D carrier attempts
```

## 11. Nonclaim Boundary

This document does not prove:

```text
axes 7-12 exist
what axes 7-12 are
that the geometric constraint manifold is more naturally A7-A12 than A1-A6
that classical game theory is equivalent to QIT-FEP
that IGT labels are game-theory primitives
that each character-engine in a population sim is an admitted manifold cell
that large-scale politics has been reduced to one strategy family
```

It does preserve the exploratory hypothesis:

```text
classical game theory can provide finite baseline correlations;
QIT-FEP can lift those correlations into density/channel/path math;
multi-engine game-world sims may reveal collective mirror constraints;
axes 7-12 should remain shadow candidates until axes 1-6 and carrier gates are
earned.
```

