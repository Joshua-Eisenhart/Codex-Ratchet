# Root Derivation, Extended Axioms, And Operational Process Map

Date: 2026-05-23

Status: human-facing derivation map. Not canon by itself. This is a working
map for deciding which implications of the roots should become extended axioms,
which should stay process laws, and which should remain owner-thesis until a
finite gate exists.

Notation standard:

```text
system_v5/ops/constraint_audit_20260523/FOUNDATION_NAMING_NOTATION_AND_ENFORCEMENT_STANDARD_20260523.md
```

## 1. Why The Previous Lists Felt Incomplete

There are three different things that kept getting collapsed:

1. **Owner axioms**: the deep thesis: pure randomness, entropy bridge,
   retrocausal convergence, entropic monism, nominalist identity, emergence by
   survival, spinor/QIT first survivors, feedback-loop life/mind structure.
2. **Formal roots**: the minimal operational kernel the current ratchet can
   enforce cleanly: F01 finitude and N01 noncommutation.
3. **Extended implications**: what becomes forbidden once F01/N01 are taken
   seriously: no primitive identity, equality, probability, metric, closure,
   observer, global rank, etc.

The owner axioms are the model's generative story.

The formal roots are the execution kernel.

The extended implications are the anti-smuggling fences.

The process rules are how the system makes those fences real.

## 2. What Counts As An Extended Axiom

An implication should be promoted to an extended axiom only if it passes six
tests.

### Test 1: Root Pressure

It must follow from F01, N01, or their combination.

Examples:

- F01 pressures against completed infinity.
- N01 pressures against swap-by-default.
- F01+N01 pressures against classical Markov chains as primitive.

### Test 2: Primitive Ban

It must forbid a specific smuggled primitive.

Bad:

```text
be more quantum
avoid classical thinking
```

Good:

```text
no primitive tensor factorization
no primitive sample space
no primitive basis
```

### Test 3: Non-Redundancy

It must not merely rename an existing axiom.

For example:

- "no primitive time" and "no primitive causality" are one fence in this
  system because both are about replacing clock-causality with ordered
  composition.
- "no primitive metric" and "no primitive coordinate chart" are one fence if
  both are enforced by chart-scramble/invariant-readout controls.

### Test 4: CS Form

It must have a computer-science translation.

Example:

```text
No primitive identity
-> object identity requires handles, hashes, provenance, receipts, invariant checks
```

### Test 5: QIT / Math Form

It must have a QIT or math translation.

Example:

```text
No primitive equality
-> a ~_P b iff every finite probe in P fails to distinguish them
```

### Test 6: Enforcement Gate

It must have a tiny finite gate:

```text
positive case
negative/graveyard case
boundary case
observable
receipt
claim ceiling
```

If an implication has no gate yet, keep it as a candidate fence or process law,
not a formal extended axiom.

## 3. What F01 Implies By Itself

F01:

```text
All distinguishability is bounded.
```

### F01-A: Finite Carrier

No root object can require an infinite carrier.

CS form:

- finite memory;
- finite schemas;
- finite context windows;
- finite object handles.

QIT form:

```text
dim(H) < infinity
rho in D(H)
```

Process form:

- every sim declares carrier dimension;
- every run terminates;
- no continuum primitive can be load-bearing.

Status:

Already root.

### F01-B: Finite Probe Family

No claim can rely on "all possible observations."

CS form:

- validator set is finite;
- API contract is finite;
- test suite is finite;
- evidence surface is finite.

QIT form:

```text
P = {E_1, ..., E_n}
```

where `P` is a finite family of effects, instruments, or readouts.

Process form:

- equality and identity are probe-relative;
- every sim names the active probes.

Status:

Already covered by EA01/EA02/EA07.

### F01-C: Finite Witness

No proofless or unbounded evidence.

CS form:

- receipt path;
- exact command;
- finite result artifact;
- bounded claim ceiling.

QIT form:

- finite matrices;
- finite operator registry;
- finite path family;
- finite sample count.

Process form:

- every claim needs a receipt;
- no "this should work" status.

Status:

Already EA07.

### F01-D: No Primitive Continuity / Smoothness

A continuum, derivative, smooth manifold, limit, or path integral cannot be
primitive.

CS form:

- no unbounded streaming proof;
- no hidden continuous state;
- no "converges eventually" without finite threshold.

QIT form:

- no `int D[path]` as a primitive;
- replace with finite path sums;
- replace continuous flow with finite operator composition.

Process form:

- if a smooth manifold is used, it must be a derived chart/readout over a
  finite carrier;
- every differential claim needs a finite discretization or symbolic boundary.

Status:

Candidate extended axiom. It is present in topology fences (`no continuity,
differentiability, or smoothness by default`) but deserves a clearer front-door
row because it is one of the main ways classical math leaks back in.

Candidate ID:

```text
CF-14: No primitive continuity or smoothness
```

### F01-E: Finite Capacity

No object, boundary, registry, or witness has unlimited storage.

CS form:

- quotas;
- maximum registry sizes;
- token/context budgets;
- finite queue length;
- finite retry count.

QIT form:

- bounded Hilbert dimension;
- bounded entropy ceiling;
- bounded mutual information across a cut.

Process form:

- bounded work is not optional;
- "just keep trying" violates the constraint.

Status:

Currently a process law and capacity fence. It may not need a separate extended
axiom because it is close to F01 itself, but it should be explicitly enforced in
sim contracts.

### F01-F: No Primitive Global View

No agent or process sees the entire system by default.

CS form:

- scoped views;
- local indexes;
- materialized projections;
- no omniscient control plane.

QIT form:

- reduced states;
- partial traces;
- finite cuts;
- observer included in joint state.

Process form:

- audit reports must name scope;
- broad estate summaries are projections, not evidence.

Status:

Partly EA05 and EC13. Could remain a process consequence unless global-view
leakage keeps recurring.

## 4. What N01 Implies By Itself

N01:

```text
Composition is order-sensitive in general.
```

### N01-A: Order Is State

If `AB` and `BA` can differ, the path is part of the object.

CS form:

- event sourcing;
- append-only logs;
- deterministic replay;
- compensation events instead of erasure.

QIT form:

```text
Phi_AB(rho) != Phi_BA(rho)
```

Process form:

- receipt order matters;
- result JSON without run path is weak evidence.

Status:

Already N01 plus process rule.

### N01-B: No Primitive Time

A clock index does not explain order. Composition explains order.

CS form:

- event log beats wall-clock timestamp;
- ordering must be replayable;
- "last write wins" is not an ontology.

QIT form:

- ordered products of operators;
- commutator gaps;
- noncommuting path families.

Process form:

- every causality claim needs an order-gap or path-dependence observable.

Status:

Already EA04/EC11.

### N01-C: No Free Commutative Aggregation

You cannot average, sum, merge, sort, or batch order-sensitive objects and
assume meaning is preserved.

CS form:

- no unordered merge of receipts;
- no silent reordering of queue rows;
- no summary that erases path dependence.

QIT form:

- mixture is not sequence;
- channel average is not history;
- trace over path can erase the very signal being tested.

Process form:

- aggregation needs an ablation showing order information is not load-bearing.

Status:

Candidate process fence. It may become an extended axiom if enough failures
come from order-erasing aggregation.

Suggested ID:

```text
EA09 / EC18: No primitive commutative aggregation
```

### N01-D: No Free Reversibility

Order sensitivity does not imply invertibility.

CS form:

- undo is a new event, not erasure;
- rollback requires a compensation record;
- destructive mutation cannot be treated as time reversal.

QIT form:

- unitary maps can be reversible;
- amplitude damping and general CPTP maps need not have inverses.

Process form:

- closure/inverse checks are required before group language is used.

Status:

Already partly EA06/EC12, but irreversibility is important enough to keep as an
explicit enforcement note under closure.

### N01-E: No Primitive Simultaneity

If order belongs to composition, then simultaneity is not free.

CS form:

- concurrent tasks need a join/merge contract;
- "parallel" outputs require reconciliation;
- races are real state, not mere scheduling accidents.

QIT form:

- tensor product independence must be admitted;
- spacelike or commuting independence cannot be presumed.

Process form:

- parallel workers can prepare bounded packets, but shared state mutation is
  serialized.

Status:

Candidate process law. It may not need a separate mathematical axiom unless
the project starts making simultaneity claims.

## 5. What F01 + N01 Imply Together

The combination is stronger than either root alone.

### FN-A: Density Operators Become Natural Candidate Carriers

F01 wants finite carriers.

N01 wants noncommuting order.

Together they pressure toward:

```text
finite-dimensional density operators
rho in D(H)
```

This does not mean density matrices are assumed at root. It means they are one
of the first stable candidate survivors.

CS alignment:

- state is not a primitive object;
- state is an admissible finite representation of distinguishability.

QIT alignment:

- finite density matrices carry mixedness, distinguishability, noncommuting
  probes, and entropy readouts.

Process consequence:

- carrier-admission sims come before geometry, bridge, or Axis0 sims.

### FN-B: CPTP Maps Replace Classical Markov Chains

F01 forbids continuous hidden-state flows as primitives.

N01 forbids commutative state transitions as the default.

Together they pressure toward:

```text
rho_{n+1} = Phi(rho_n)
Phi(rho) = sum_k K_k rho K_k^dagger
sum_k K_k^dagger K_k = I
```

CS alignment:

- state transition functions require contracts and receipts.

QIT alignment:

- channels and instruments replace classical transition probabilities.

Process consequence:

- Markov-chain language is allowed only as a commuting/classical ablation or
  after a QIT channel translation.

### FN-C: Finite Path Sums Replace Continuum Path Integrals

F01 forbids continuum integration as primitive.

N01 says composition order matters.

Together:

```text
Z = sum_{finite histories h} weight(h) observable(Phi_h(rho))
```

CS alignment:

- finite event histories;
- finite replay traces;
- bounded workflow paths.

QIT alignment:

- finite Kraus/instrument histories;
- path-ordered operator products.

Process consequence:

- QIT-FEP and Feynman-like probes must use finite histories.

### FN-D: Graph / Topology Comes Before Metric Geometry

F01 gives finite tokens.

N01 gives ordered/compatible relations.

Before coordinates or metric distance, the first legal spatialization is:

```text
finite vertices
finite relations
finite paths
finite cycles
finite higher cells
```

CS alignment:

- dependency graphs;
- capability graphs;
- workflow graphs;
- state-transition graphs.

QIT alignment:

- tensor-network candidate structure;
- finite cuts;
- adjacency as compatibility, not metric distance.

Process consequence:

- graph/topology sims should precede smooth metric/manifold claims.

### FN-E: Boundaries Are Interfaces, Not Classical Markov Blankets

F01 makes boundaries finite.

N01 makes boundary-crossing operations order-sensitive.

Together:

```text
boundary = finite cut + admissible interaction/probe family
```

CS alignment:

- sandbox;
- namespace;
- interface;
- capability boundary.

QIT alignment:

- bipartite or multipartite cut;
- partial trace;
- instrument-mediated boundary interaction.

Process consequence:

- "Markov blanket" must be rebuilt as a finite QIT cut, not imported as a
  classical partition.

### FN-F: Independence Is Not Free

F01 makes subsystem declarations finite.

N01 makes composition order matter across subsystems.

Together:

```text
rho_AB = rho_A tensor rho_B
```

is a claim, not a default.

CS alignment:

- no ambient independence between modules;
- no default safe parallel mutation.

QIT alignment:

- product state is a witness;
- entanglement/correlation must be measured;
- tensor factorization must be declared and stress-tested.

Process consequence:

- every cut-state sim needs product, entangled, and matched controls.

Status:

Candidate extended axiom. This one is probably worth adding because tensor
factorization is a major QIT/FEP leakage point.

Candidate ID:

```text
CF-15: No primitive tensor factorization or independence
```

## 6. Current Extended Axiom Catalog

### 6.1 Already Strong

| Code | Name | Keep? | Why |
|---|---|---|---|
| F01 | Finitude | yes | root |
| N01 | Noncommutation | yes | root |
| EA01 | No primitive identity | yes | direct anti-Cartesian fence |
| EA02 / EC07 | Probe-relative equality | yes | equality becomes finite indistinguishability |
| EA03 | Boundary/contrast identity | yes | prevents unbounded center/self claims |
| EA04 / EC11 | No primitive time/causality | yes | order from composition, not clock |
| EA05 / EC15 | No primitive metric/coordinate/geometry | yes | geometry must be induced |
| EA06 / EC12 | No closure by default | yes | composition must be admitted |
| EA07 | Finite witness discipline | yes | makes F01 operational |
| EC08 | No cloning/broadcasting | yes | noncommuting states cannot be copied freely |
| EC09 | No primitive probability | yes | probability is probe/instrument indexed |
| EC10 | No primitive optimization/utility | yes | objectives must be named |
| EC13 | No outside observer | yes | observer belongs to joint system |
| EC14 | No global total order | yes | scalar rank cannot replace structure |
| EC16 | No semantic smuggling | yes | renamed classical concepts must be reproven |

### 6.2 Duplicates Or Near-Duplicates

These should not inflate the count.

| Claim | Better treatment |
|---|---|
| no primitive causality | part of EA04 unless a separate boundary-history gate is built |
| no primitive coordinates | part of EA05 |
| no primitive distance/norm | part of EA05 unless metric-specific gates diverge |
| no free inverse | part of EA06, with explicit irreversible-channel examples |
| no utility | part of EC10 |
| no scalar ranking | part of EC14, with scalarization-specific controls |

### 6.3 Candidate New Extended Axioms

These are the missing implications worth considering.

| Candidate | Root pressure | CS form | QIT/math form | Gate idea | Suggested status |
|---|---|---|---|---|---|
| No primitive continuity/smoothness | F01 | no hidden continuous state | finite path/operator families before manifolds | finite discretization vs continuum claim | candidate `CF-14` |
| No primitive tensor factorization/independence | F01+N01 | module independence not default | `rho_AB = rho_A tensor rho_B` must be witnessed | product vs entangled vs matched cut controls | candidate `CF-15` |
| No primitive classical Markov chain | F01+N01 | no bare finite-state stochastic chain | CPTP/instrument iteration before stochastic transition matrix | commuting Markov chain as ablation | candidate `CF-16` |
| No primitive classical Markov blanket | F01+N01 | no sharp external partition by default | finite cut state plus mediator/instrument | product/entangled/matched blanket controls | candidate `CF-17` |
| No primitive commutative aggregation | N01 | no unordered merge of receipts | average channel != history | order-erasing average control | candidate `CF-18` |
| No primitive scalarization | EC10+EC14 | dashboards are projections | vector/tensor readouts before scalar score | scalar loses signal control | candidate `CF-19` |
| No primitive basis/gauge | EA05+N01 | representation choice not ontology | basis-invariant readout plus basis-scramble control | remap/basis control must not decide claim | candidate `CF-20` |
| No primitive measurement/probe apparatus | EC09+EC13 | observer/probe is part of system | POVM/instrument must be declared | same state, different instruments differ | candidate `CF-21` |
| No primitive simultaneity | F01+N01 | concurrency is a contract, not ontology | incompatible events require ordering/instrument relation | race/order control | candidate `CF-22` |
| No primitive sample space | EC09+F01 | events require schema/probe | probability over effects, not bare outcomes | standalone `p(x)` killed | maybe under EC09 |
| No primitive global state/context | F01+EC13 | scoped views only | reduced states/cuts only | global-view oracle control | candidate `CF-23` |
| No primitive convergence/limit | F01+CF-14 | thresholds required | finite epsilon/step convergence | "eventual" without bound killed | candidate `CF-24` |
| No free reversibility | F01+N01 | inverse must be witnessed | irreversible channels are not unitary groups | amplitude damping vs unitary inverse control | candidate `CF-25` |

The strongest additions are:

```text
CF-14: no primitive continuity/smoothness
CF-15: no primitive tensor factorization/independence
CF-16: no primitive classical Markov chain
CF-17: no primitive classical Markov blanket
CF-18: no primitive commutative aggregation
CF-19: no primitive scalarization
CF-20: no primitive basis/gauge
CF-21: no primitive measurement/probe apparatus
CF-22: no primitive simultaneity
CF-23: no primitive global state/context
CF-24: no primitive convergence/limit
CF-25: no free reversibility
```

These remain candidate fences. They live in the candidate basin around
`M(C)`, not inside the accepted manifold, until a gate proves each one is
non-redundant and enforceable.

## 7. CS / QIT Alignment Table

| System idea | CS expression | QIT/math expression | Process consequence |
|---|---|---|---|
| state | finite witnessed state representation | finite density operator `rho` | declare carrier and dimension |
| operation | state transition under contract | CPTP map / instrument / operator product | declare operation registry |
| order | event log / replay order | noncommuting composition | order-gap plus commuting control |
| history | append-only receipt chain | finite path/Kraus history | path family must be enumerable |
| identity | handles, hashes, provenance | probe-relative indistinguishability | no bare object sameness |
| equality | schema/contract/invariant equivalence | finite probe-vector equivalence | no single-probe equality |
| boundary | sandbox/interface/capability | cut, partial trace, instrument boundary | no classical Markov blanket import |
| probability | observed outcome under named measurement | Born rule from named effect/instrument | no standalone `p(x)` |
| geometry | compatibility graph/projection | induced projective/Hopf/metric structure | graph/topology before metric |
| optimization | named objective function | named functional over finite states | no primitive best |
| observer | process inside system | subsystem in joint state | no outside observer |
| evidence | receipt/result/validator output | finite witness artifact | no claim without finite artifact |

## 8. Systems Thinking: The Ratchet As A Feedback System

The system is not only a list of axioms. It is a feedback machine.

### Stocks

The important stocks are:

- owner axioms;
- normalized candidates;
- constraint gates;
- runnable sims;
- receipts;
- survivors;
- graveyard;
- stale docs;
- trusted rebuild lanes.

### Flows

The main flows are:

```text
owner source -> normalized candidate -> bounded queue item -> sim/probe
           -> receipt -> registry/ledger -> survivor or graveyard
```

and:

```text
receipt changes -> stale docs/ledgers -> maintenance repair -> current state
```

### Feedback Loops

Negative loop:

```text
candidate -> stress control -> killed -> graveyard -> narrower next candidate
```

Positive loop:

```text
candidate -> survives gate -> larger but still bounded successor
```

Maintenance loop:

```text
new evidence -> stale surface detected -> handoff/registry/doc repair
```

Contamination loop:

```text
cross-lane import -> evidence ambiguity -> quarantine -> clean rebuild
```

Attractor loop:

```text
many candidates + repeated constraints -> stable survivor basin
```

This is the systems-thinking core:

```text
the manifold is not just a math object;
it is the emergent attractor surface of repeated constraint pressure.
```

## 9. The Operational Ladder From Foundations

This is the clean step-by-step path.

### Step 0: Preserve The Owner Axiom

Write the owner claim without shrinking it.

Example:

```text
pure randomness is base
```

Do not formalize too early.

### Step 1: Translate To A Finite Fixture

Convert the owner claim into a finite admissible object.

Example:

```text
finite high-entropy rho_N
N in {2,4,8}
```

### Step 2: Name The Root Pressure

Ask which root is active.

Examples:

- F01: finite carrier, finite witness.
- N01: order gap, path dependence.
- F01+N01: finite noncommuting carrier.

### Step 3: Classify The Implication

It can be:

- extended axiom;
- process law;
- candidate fence;
- owner-thesis only;
- empirical hypothesis;
- killed formulation.

### Step 4: Build The Gate

Every gate needs:

```text
positive case
negative case
boundary case
observable
claim ceiling
receipt path
```

### Step 5: Align CS And QIT

For every gate, name both forms:

```text
CS: what runtime primitive is forbidden?
QIT: what mathematical primitive is forbidden?
```

Example:

```text
No primitive tensor factorization
CS: module independence is not default
QIT: rho_AB = rho_A tensor rho_B must be witnessed
```

### Step 6: Run The Smallest Sim

Do not start with a bridge or Axis0 claim.

Start with:

```text
one carrier
one operator/probe
one control
one boundary
```

### Step 7: Record The State Transition

The result should say:

```text
survived
killed
open
blocked
demoted
```

and why.

### Step 8: Widen One Axis Only

Only after a bounded receipt exists:

- increase carrier size;
- or add one topology;
- or add one noise channel;
- or add one readout;
- or add one tool;
- not all at once.

## 10. What To Build Next

### Next Doc/Registry Move

Create a master constraint registry with four statuses:

```text
root
accepted extended axiom
candidate extended axiom
process law
```

This prevents count inflation.

### Next Sim Move

CF-14, CF-15, CF-16, CF-17, CF-18, CF-19, and CF-20 now have candidate-gate receipts:

```text
system_v5/ops/constraint_audit_20260523/results/cf14_finite_discrete_vs_continuum_smuggling_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf15_product_entangled_matched_cut_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf16_cptp_instrument_vs_classical_markov_chain_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf17_cut_instrument_vs_classical_markov_blanket_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf18_path_resolved_vs_order_erasing_average_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf19_vector_tensor_vs_scalar_loss_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf20_basis_scramble_gauge_invariance_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf21_declared_instrument_vs_primitive_probe_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf22_order_race_vs_primitive_simultaneity_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf23_scoped_view_vs_global_oracle_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf24_finite_epsilon_step_vs_limit_smuggling_gate_results.json
system_v5/ops/constraint_audit_20260523/results/cf25_irreversible_channel_vs_free_inverse_gate_results.json
system_v5/ops/constraint_audit_20260523/results/candidate_fence_nonredundancy_audit_results.json
```

They are still candidate fences, not accepted derived constraints. The
non-redundancy audit covers CF-14 through CF-25 as a ceiling receipt
only. It checks token overlap and exact duplicate structural fixture
signatures, not final formal independence. Actual promotion still requires an
explicit CF-to-DC review and M(C) recompute.

The next process is not another CF gate in this packet. It is a review layer:

1. decide whether any receipted CF should enter formal CF-to-DC review;
2. if yes, run promotion review and recompute or archive `M(C)`;
3. if no, keep all CF rows outside the accepted derived-constraint layer.

Each gate should be tiny.

### Next Systems Move

Make a controller checklist:

```text
Does this work unit have a finite object?
Does it name its root pressure?
Does it name which primitive it forbids?
Does it have CS and QIT forms?
Does it have a positive, negative, and boundary case?
Does it write a receipt?
Does it update the state surface?
```

That checklist is how the philosophy becomes operational.

## 11. Current Bottom Line

The system probably has:

```text
2 formal roots
13 accepted derived constraints
12 candidate fences
several process laws that should not inflate the axiom count
```

The leading candidate-fence build order is:

```text
no primitive basis/gauge
no primitive scalarization
no primitive measurement/probe apparatus
```

The most important process correction is:

```text
every owner axiom must pass through finite translation before formal admission.
```

The most important systems correction is:

```text
the manifold is the attractor basin created by repeated finite,
noncommuting constraint pressure.
```
