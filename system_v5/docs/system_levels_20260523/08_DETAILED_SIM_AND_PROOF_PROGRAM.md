# Detailed Sim And Proof Program

Date: 2026-05-23

Status: working research program. Not an admission surface.

2026-05-23 quarantine note: sections that name "current completed vertical
slices", `all_pass`, fresh-rerun status, or contract-lint status were written
during the contaminated expansion window. Treat those sections as stale rerun
targets, not current evidence, until clean independent formal-scout receipts are
rebuilt.

## 1. Purpose

This document turns the philosophy and system manuals into concrete build
lanes. It answers:

```text
What should be simulated?
What controls are required?
What proof targets are plausible?
What would count as failure?
What should not be claimed?
```

## 2. Universal Sim Template

Every nontrivial scout should have:

```text
name
claim ceiling
carrier
operation registry
positive construction
negative controls
boundary controls
readouts
result JSON
lint
fresh rerun
open next work
```

### Carrier

State the finite object:

```text
rho in D(C^2)
rho_AB in D(C^2 tensor C^2)
N-cell finite lattice
finite graph with n nodes
finite token registry
finite process tensor
```

### Operation Registry

State the finite operations:

```text
Kraus instruments
CPTP maps
unitaries
dephasing channels
amplitude damping
finite effects
token compositions
finite path histories
```

### Controls

Controls must target specific smuggling risks:

```text
commuting control             kills fake N01
classical probability control kills primitive probability
product-cut control           kills fake entanglement/cut signal
basis/gauge scramble          kills coordinate artifact
path shuffle                  kills fake history/order claim
capacity overflow             kills hidden infinity
memory erasure                kills fake Holodeck memory claim
wrong flux                    kills externally assigned flux
matched nuisance              kills scale/parameter confound
```

### Readouts

Readouts must stay separate:

```text
log_z
F_Q
D(rho || sigma)
I_c
I(A:B)
trace distance
reconstruction score
cue confirmation
order gap
commuting control gap
flux current
capacity violation
IGT strategy payoff
Type1/Type2 strategy spread
```

Do not collapse them into one scalar unless that scalar is the explicit object
under test.

## 3. Quarantined Vertical Slice Targets

### 3.1 Basic Holodeck-QIT-FEP

Script:

```text
system_v5/ops/formal_scouts/sim_holodeck_qit_fep_predictive_world_model_probe.py
```

Quarantined prior status:

```text
formal_scout
prior all_pass/fresh-rerun/contract-lint claims are stale
clean independent rerun required before evidence use
```

What it tested:

```text
finite world-memory density state
projection/action instruments
sensor/error effect
posterior update
memory cue
commuting, classical, product, no-memory, no-projection controls
```

What it did not test:

```text
full engine registry
multi-cell world model
multi-seed topology grid
full Xi bridge
final Axis0
final flux
```

### 3.2 Flux-Guided QIT Engine Holodeck Runtime

Script:

```text
system_v5/ops/formal_scouts/sim_flux_qit_engine_holodeck_runtime_probe.py
```

Quarantined prior status:

```text
formal_scout
prior all_pass/fresh-rerun/contract-lint claims are stale
clean independent rerun required before evidence use
```

What it tested:

```text
16 source-backed ordered tokens
finite CPTP token instruments
derived flux current from world-memory cut
flux-guided engine path
Holodeck-QIT-FEP posterior update
wrong-flux, commuting, classical, memory-erasure controls
```

What it did not test:

```text
multi-seed robustness
multi-topology robustness
multi-carrier robustness
flux-current family comparison
process-tensor Xi bridge
Axis0 admission
```

### 3.3 IGT Engine Game-Theory Strategy Grammar

Script:

```text
system_v5/ops/formal_scouts/sim_igt_engine_game_theory_strategy_probe.py
```

Quarantined prior status:

```text
formal_scout
prior all_pass/fresh-rerun/contract-lint claims are stale
clean independent rerun required before evidence use
```

What it tested:

```text
each character can be a Type1 or Type2 engine
Type1 exposes 8 source-backed strategies
Type2 exposes 8 source-backed strategies
the Type1/Type2 union covers the 16 ordered-token registry
strategies are finite CPTP channel/readout rows
payoff is a named QIT readout, not primitive utility
the Type1-vs-Type2 payoff matrix is finite and nonconstant
noncommuting order gaps contribute to the game readout
commuting/identity controls collapse the order-gap content
```

What it did not test:

```text
replicator dynamics
strategy learning
Axis0 derived from game-process readouts
final IGT game theory
```

### 3.4 IGT Engine Population Holodeck Game

Script:

```text
system_v5/ops/formal_scouts/sim_igt_engine_population_holodeck_game_probe.py
```

Quarantined prior status:

```text
formal_scout
prior all_pass/fresh-rerun/contract-lint claims are stale
clean independent rerun required before evidence use
```

What it tested:

```text
six finite characters
each character is Type1 or Type2
each character has 8 source-backed strategies
strategy weights are derived from named QIT readouts
finite Holodeck world-memory density updates during play
adaptive weighted readout differs from uniform evaluation
commuting/identity control collapses order-gap and strategy-score content
memory-erasure control collapses world-memory content
```

What it did not test:

```text
large population scaling
replicator/mutation dynamics
multi-cell world model
strategy learning
Axis0 derived from game-process readouts
final IGT game theory
```

### 3.5 IGT QIT Extrema Policy Selectors

Script:

```text
system_v5/ops/formal_scouts/sim_igt_qit_game_extrema_policy_probe.py
```

Quarantined prior status:

```text
formal_scout
prior all_pass/fresh-rerun/contract-lint claims are stale
clean independent rerun required before evidence use
```

What it tested:

```text
maximax(M) = argmax_i max_j M_ij
maximin(M) = argmax_i min_j M_ij
minimax(M) = argmin_i max_j M_ij
minimin(M) = argmin_i min_j M_ij
QIT payoff matrix over Type1/Type2 engine strategies
QIT exposure matrix over disturbance, entropy cost, and order-gap content
constant matrix control collapses policy content
minimin over exposure acts as low-commitment policy, not weak utility
```

What the quarantined prior fixture reported:

```text
minimin over exposure selects NeTi
payoff maximax also selects NeTi
minimin mean exposure = 0.0572
exposure maximax mean exposure = 0.1615
minimin mean order gap = 0.0448
minimin future optionality = 0.1946
```

What it did not test:

```text
mixed-strategy equilibrium
Nash-like fixed point
large population policy evolution
Axis0 derived from extrema-policy history
final IGT game theory
```

### 3.6 Holodeck Science-Method IGT QIT-FEP Loop

Script:

```text
system_v5/ops/formal_scouts/sim_holodeck_science_method_igt_qit_fep_probe.py
system_v5/ops/formal_scouts/sim_holodeck_science_method_multiseed_policy_grid_probe.py
```

Quarantined prior status:

```text
formal_scout
prior all_pass/fresh-rerun/contract-lint claims are stale
prior R5 multiseed classifier pass claim is stale
clean independent rerun required before evidence use
```

What it tested:

```text
science-method loop:
  observe -> hypothesize -> predict -> experiment -> update -> falsify -> replicate

Holodeck layer:
  finite world-memory density state
  finite effects as observations
  finite instrument/path update
  posterior QIT-FEP readouts

IGT layer:
  minimin over exposure selects NeTi in this fixture
  policy token enters the experiment path as a bounded engine prefix
  IGT selects experiment policy but does not define truth

Controls:
  projection-off/no-update
  wrong hypotheses
  commuting-order collapse
  scalar entropy rejection
  three-fixture replication
```

What it found:

```text
selected hypothesis = H_true_target
hypothesis margin = 0.0142
active margin over no-update = 0.0375
order gap = 0.2432
commuting order gap ~= 5.55e-16
replicates = 3/3 pass
```

Important boundary:

```text
wrong-memory stress did not prove memory-specific load-bearing
final Holodeck / science method / IGT / Axis0 / Xi / flux / physics not admitted
```

R5 multiseed classifier:

```text
script = sim_holodeck_science_method_multiseed_policy_grid_probe.py
seeds = 12
policy rows = 24
token grid = 16
all 16 tokens select H_true_target
minimin(exposure) = NeTi
payoff maximax = NeTi
live memory active-margin delta over best control = 0.01033
commuting controls collapse order gap to ~1e-16
constant matrix collapses policy selector content
```

R5 interpretation:

```text
Holodeck science-method loop survives this bounded grid against the listed controls.
IGT policy specificity is not admitted because all tokens work.
minimin is not admitted as unique because it conflates with payoff maximax.
memory-specific truth selection is not admitted because controls still select
H_true_target.
memory remains a narrower active-update-margin candidate only, with
live_hypothesis_margin_beats_all_controls = false.
```

## 4. Required Engine/Axis Row Schema

Before a flux, Xi, or Axis0 scout can claim engine-level evidence, each runtime
row must carry the axis/engine fields explicitly. Otherwise agents will collapse
token labels into physics.

Required row fields:

```text
engine_type
sheet
terrain_family
terrain_realization
terrain_table_id
path_geometry
chart_loop_role
axis4_loop_family
axis5_family
judging_operator
exact_channel
ordered_token
axis6_precedence
axis6_action_side
closure_type
functional_readout
target_attractor
xi_bridge_status
axis0_role
axis0_readout_family
axis0_admission_status
control_degeneracy_tests
claim_ceiling
```

Minimal row controls:

```text
same token with commuting operators
same token with left/right action erased
same path with fiber/base swapped
same channel with phase/amplitude scrambled
same cut with product state
same readout under local gauge transform
```

The machine-readable field list lives in:

```text
system_v5/docs/system_levels_20260523/machine_readable/axes_qit_engine_registry_20260523.json
```

## 5. Next Sim Lane: Flux Current Family Grid

### Question

Is the passing flux result tied to one handcrafted current, or does a family of
derived flux currents consistently steer the QIT engine/Holodeck runtime?

### Candidate Currents

```text
J_geom   Hopf connection / holonomy current
J_chi    chirality sheet current
J_Bloch  world-target Bloch cross/difference current
J_ent    entropy or information flow current
J_cut    world-memory cut coupling current
J_axis   token/axis current
J_cross  cross-axis composite current
```

### Fixtures

```text
seeds: at least 30
carriers: qubit, qutrit-lite control if feasible, two-qubit cut
topologies: ring, path, star, K4
noise: dephasing, depolarizing, amplitude damping
engine paths: source-backed token loops
```

### Controls

```text
wrong_flux
random_flux
flux_erased
commuting_engine
classical_probability
product_cut
memory_erased
matched_current_magnitude
```

### Readouts

```text
reconstruction margin
path evidence margin
order gap
commuting gap
mutual information margin
coherent information margin
current sign stability
effect size distribution
Bonferroni/FDR corrected admission
```

### Pass

At least one flux-current family survives matched controls across multiple
seeds/topologies/carriers, and wrong/random/erased controls fail.

### Fail

The current only works on the current hand fixture or dissolves under matched
magnitude/random sign controls.

## 6. Next Sim Lane: Xi Process-Tensor Bridge

### Question

Can `{geometry, history, engine, holodeck}` be mapped into a finite cut state or
process tensor in a way that survives controls?

### Candidate Xi

```text
Xi(state) -> rho_AB
Xi(history) -> process tensor Υ
Xi(engine_path, memory_cut) -> posterior process state
```

### Required Inputs

```text
geometry fixture
engine token path
Holodeck world-memory state
finite instrument history
effect family
memory/probe cut
```

### Controls

```text
history shuffled
engine tokens randomized
geometry erased
memory cut productized
commuting channel replacement
classical probability replacement
same scalar entropy / different process
```

### Readouts

```text
process trace distance
relative entropy to controls
Axis0 candidate readouts
order sensitivity
gauge/basis stability
```

### Pass

Xi maps real structured process information into the cut/process object better
than controls.

### Fail

Xi reduces to a scalar summary, static cut, or nuisance parameter.

## 7. Next Sim Lane: Holodeck Cellular World Model

### Question

Can the Holodeck-FEP loop run over finite cells, not just one world-memory
qubit cut?

### Carrier

```text
N finite cells
each cell has rho_i in D(C^2)
memory cells or reference cut B
finite adjacency graph
```

### Update

```text
local CPTP instruments
neighbor coupling channel
sensor/error effects per region
compressed memory cue channel
finite action/path family
```

### Controls

```text
projection_off
sensor_error_off
memory_shuffle
commuting_update
classical_markov_update
random_adjacency
product_memory_cut
scalar_entropy_baseline
```

### Readouts

```text
local reconstruction score
global reconstruction score
cut mutual information
coherent information
path evidence
order gap
cell variance
cross-seed variance
cross-topology variance
```

### Pass

The QIT-Holodeck update improves reconstruction and memory/cut readouts beyond
classical and commuting controls across a finite grid.

### Fail

The update is equivalent to classical filtering, scalar entropy minimization,
or memory retrieval.

## 8. Internal Proof Program

### 7.1 QIT-FEP Finite Variational Theorem

Target statement:

For a finite density state, finite instrument family, and full-rank finite
effect, the posterior state constructed by the finite path sum minimizes the
relative-entropy free-energy functional:

```text
F_Q(sigma) = D(sigma || tau/Z) - log Z
```

Work needed:

```text
state support/domain conditions
full-rank effect conditions
finite-dimensional proof
relationship to Gibbs variational principle
non-uniqueness of Axis0 aggregates
```

Useful output:

```text
formal lemma packet
symbolic proof sketch
torch fixture only as sanity check
```

### 7.2 Engine Token CPTP Lemma

Target statement:

Every source-backed token in the 16-token registry maps to a finite CPTP
instrument under the current operator/terrain realization.

Work needed:

```text
define each operator channel
define each terrain channel
prove composition preserves CPTP
record path count bounds
separate token precedence from physical left/right closure
```

### 7.3 Flux Gauge/Basis Invariance Program

Question:

Which flux-current candidates are invariant under admissible gauge/basis
changes, and which are chart artifacts?

Tests:

```text
unitary basis change
reference-side gauge change
same physical state different chart
same scalar current different steering effect
```

Useful theorem:

```text
J is admissible only if its steering decision is invariant under declared
gauge/basis transformations or if it explicitly declares its chart dependence.
```

## 9. External Math Proof Targets

### 8.1 Yang-Mills Mass Gap Analog

Why plausible:

The project already has:

```text
finite noncommuting operators
connection/holonomy language
gauge-like transformations
spectral readouts
finite lattice potential
```

Finite analog:

```text
finite lattice gauge carrier
link variables as finite unitaries
plaquette/holonomy readouts
transfer operator spectrum
mass gap analog = nonzero spectral gap robust under scaling controls
```

Controls:

```text
abelian/commuting replacement
random link phases
gauge transform invariance
boundary condition swaps
finite-size scaling
```

Claim ceiling:

```text
finite Yang-Mills-like spectral-gap analog only
```

### 8.2 Navier-Stokes Regularity Analog

Why plausible:

The model already emphasizes:

```text
flows
dissipation
feedback
attractor basins
finite cells
entropy/readout bounds
```

Finite analog:

```text
finite cellular flow state
CPTP dissipative update
energy-like observable
vorticity-like observable
dissipation/entropy readout
bounded-time regularity gate
```

Controls:

```text
commuting diffusion
classical finite-difference baseline
energy injection
noise channels
topology variation
```

Claim ceiling:

```text
finite regularity/blow-up analog only
```

### 8.3 Riemann Hypothesis Spectral Analog

Why plausible:

The project can explore:

```text
finite spectra
random matrix statistics
trace formulas
phase/holonomy sums
prime-like finite sequences
```

Finite analog:

```text
construct finite Hermitian/unitary operator families
compare spectra to zeta-zero statistics
test against random/unitary/classical controls
look for invariant spectral constraints
```

Claim ceiling:

```text
spectral analogy and invariant search only
```

### 8.4 P vs NP Constraint Geometry Analog

Why plausible:

The project is naturally about:

```text
finite witnesses
verification
search
bounded work
constraint surfaces
proof receipts
```

Finite analog:

```text
finite verifier as probe family
candidate witness space as finite constraint manifold
search path family as engine trajectory
compare verification cost vs construction/search cost
```

Controls:

```text
random verifier
easy planted witness
hard unsat fixture
noncommuting search update
classical search baseline
compression shortcut controls
```

Claim ceiling:

```text
bounded proof-complexity/search-geometry model only
```

### 8.5 Hodge And BSD

Hodge finite analog:

```text
finite chain/cochain complex
harmonic representative projection
cycle/boundary distinguishability
algebraic-cycle-like candidate family
```

BSD finite analog:

```text
bounded elliptic curve data
mod-p point-count sequences
rank labels
spectral/entropy feature extraction
baseline ML/statistical controls
```

Claim ceiling:

```text
finite feature discovery or toy cohomology analog only
```

## 10. How To Decide What To Build First

Priority order:

1. closest to current passing receipts;
2. smallest finite carrier;
3. clearest negative controls;
4. strongest chance of producing a theorem-like lemma;
5. least likely to become pure analogy.

That selects:

```text
1. IGT extrema-policy population scale sweep / multi-cell Holodeck game scout
2. IGT minimin optionality stress grid
3. flux-current family grid
4. Xi process tensor bridge
5. QIT-FEP finite variational theorem packet
6. flux gauge/basis invariance packet
7. finite Yang-Mills spectral-gap analog
```

## 11. Stop Conditions

Stop or demote a lane if:

```text
controls are not clear
the claim requires continuum assumptions
the finite analog no longer resembles the target
the result is entirely scalar and loses process structure
the same effect appears in matched random/classical controls
the lane needs more source math before coding
```

That is not failure of the overall model. It is the ratchet doing its job.
