# Extended Constraint Candidate Ledger

Date: 2026-05-23

Status: working candidate ledger. Not canon by itself.

## 1. Purpose

This ledger expands the thin roots into candidate derived constraints and shows
what each one would require to become enforceable.

It uses this ladder:

```text
root pressure
  -> forbidden primitive
  -> CS form
  -> QIT/math form
  -> enforcement gate
  -> current status
```

## 2. Roots

### RC-F01: Finitude

Root pressure:

```text
No completed infinities or unbounded witnesses at root.
```

Immediate enforcement:

```text
finite carrier
finite registry
finite path family
finite probe family
finite receipt
bounded claim ceiling
```

### RC-N01: Noncommutation

Root pressure:

```text
Order-sensitive composition is primitive.
```

Immediate enforcement:

```text
forward/reversed gap
commuting control
token precedence
left/right action audit
path-order readout
```

## 3. Derived Constraint Candidates

### DC-01: No Primitive Identity

Root pressure:

```text
F01: identity must be finitely witnessed.
N01: identity cannot ignore operation order/context.
```

Forbidden primitive:

```text
object self-sameness as absolute starting point
```

CS form:

```text
object identity requires handle, schema, provenance, equality contract, and
receipt.
```

QIT/math form:

```text
identity is equivalence under a finite probe family P
```

Gate:

```text
same label / different probe result
same state under one probe / distinguishable under another
basis-invariant equality vs coordinate equality
```

Status:

```text
strong doctrine, needs consolidated gate family
```

### DC-02: No Primitive Equality

Forbidden primitive:

```text
free substitution by `=`
```

CS form:

```text
equality must name comparison method and scope
```

QIT/math form:

```text
a ~_P b iff all E in finite P give same operational readout within tolerance
```

Controls:

```text
same entropy but trace-distinct
same coordinates after bad chart but different invariant
same invariant but different active probe
```

### DC-03: No Primitive Probability

Forbidden primitive:

```text
sample space or probability distribution before probe
```

CS form:

```text
probability field must reference source probe/effect and state
```

QIT/math form:

```text
p(E|rho)=Tr(E rho)
```

Gate:

```text
same rho, different E gives different probability
classical probability baseline loses order/cut signal
```

### DC-04: No Primitive Time Or Causality

Forbidden primitive:

```text
global clock, total causal order, past-push story
```

CS form:

```text
event order is a finite relation, not a global default
```

QIT/math form:

```text
ordered channel composition
process tensor
boundary-conditioned finite histories
```

Gate:

```text
order reversal matters for noncommuting case
commuting case erases order gap
endpoint effect changes admitted path family
```

### DC-05: No Primitive Metric Or Coordinates

Forbidden primitive:

```text
coordinate chart as physical structure
```

CS form:

```text
coordinate fields are views; invariant readouts are required
```

QIT/math form:

```text
trace distance, fidelity, relative entropy, gauge-invariant readouts
```

Gate:

```text
chart scramble
unitary basis change
same physical state / different coordinates
coordinate metric fails while invariant survives
```

### DC-06: No Closure By Default

Forbidden primitive:

```text
assuming group/algebra closure, inverse, identity, or associativity beyond
the declared operation
```

CS form:

```text
operation family must declare closure type and failure cases
```

QIT/math form:

```text
unitary group vs non-invertible CPTP semigroup
```

Gate:

```text
amplitude damping has no inverse
dephasing loses coherence
composition leaves family or changes type
```

### DC-07: Finite Witness Discipline

Forbidden primitive:

```text
truth without finite evidence
```

CS form:

```text
receipt path, command, result, lint, fresh-rerun
```

QIT/math form:

```text
finite matrices, finite path families, finite proof objects
```

Gate:

```text
claim without receipt fails admission
```

### DC-08: No Cloning / Broadcasting For Noncommuting States

Forbidden primitive:

```text
copying unknown noncommuting state as if classical
```

CS form:

```text
copy/cache operations must declare what is copied: handle, data, sample,
classical readout, or quantum state surrogate
```

QIT/math form:

```text
no-cloning and no-broadcasting pressure for noncommuting state families
```

Gate:

```text
copy works for commuting classicalized controls
copy fails for noncommuting states under active probes
```

### DC-09: No Primitive Optimization Or Utility

Forbidden primitive:

```text
best, optimal, utility, or objective without functional
```

CS form:

```text
optimizer must name objective, constraints, state space, and tie-breaking
```

QIT/math form:

```text
argmin only after finite functional F is declared
```

Gate:

```text
different functionals pick different optima
global scalar optimum fails under alternate probe
```

### DC-10: No Outside Observer

Forbidden primitive:

```text
privileged observer outside the same substrate
```

CS form:

```text
observer/probe is part of the system boundary
```

QIT/math form:

```text
joint rho_AB; probe side A and probed side B are cut choices
```

Gate:

```text
tracing observer changes reduced state
product observer control loses signal
```

### DC-11: No Global Total Order

Forbidden primitive:

```text
one scalar ranking all states/processes
```

CS form:

```text
rank function must declare domain, equivalence classes, and incomparables
```

QIT/math form:

```text
entropy/purity/free energy are partial readouts, not total order
```

Gate:

```text
same entropy trace-distinct states
different entropy but same active classification
multi-readout disagreement
```

### DC-12: No Semantic Smuggling

Forbidden primitive:

```text
renamed classical concept treated as QIT proof
```

CS form:

```text
every imported term needs behavior tests and negative controls
```

QIT/math form:

```text
classical MI != coherent information
classical Markov chain != quantum instrument history
classical blanket != noncommuting cut/process tensor
```

Gate:

```text
classical property fails in QIT case
renamed object loses under controls
```

## 4. Candidate Fences Needing More Work

### CF-13: No Primitive Tensor Factorization

Pressure:

```text
F01 gives finite factors but not a privileged factorization;
N01 means factor order/cuts can matter.
```

Gate:

```text
same global state, different cut; readout changes.
factorization chosen by process/controls, not labels.
```

### CF-14: No Primitive Classical Markov Chain

Pressure:

```text
classical Markov chains use primitive probability, state equality, and ordered
time index.
```

QIT replacement:

```text
finite CPTP instrument iteration or process tensor
```

Gate:

```text
classical Markov baseline loses noncommuting path-history signal
```

### CF-15: No Primitive Classical Markov Blanket

Pressure:

```text
classical blankets assume sharp partitions and conditional independences.
```

QIT replacement:

```text
finite bipartite/tripartite cut with mediator and noncommuting boundary
operators
```

Gate:

```text
classical blanket baseline fails where QIT cut/process tensor separates
```

### CF-16: No Primitive Scalarization

Pressure:

```text
single scalar summaries erase noncommuting process structure.
```

Gate:

```text
scalar readout passes but process control fails;
multi-readout family needed.
```

### CF-17: No Primitive Smoothness / Continuity

Pressure:

```text
continuum and derivative structures violate F01 if imported at root.
```

Replacement:

```text
finite difference, finite graph, finite path, finite lattice, bounded sweep
```

Gate:

```text
continuous-language claim must survive finite discretization and scaling
controls
```

### CF-18: No Free Reversibility

Pressure:

```text
N01 and CPTP dynamics distinguish reversible unitary from irreversible channel.
```

Gate:

```text
unitary inverse works; damping/dephasing inverse fails.
```

## 5. Promotion Requirements

A candidate fence can become a derived constraint only when it has:

```text
root pressure
specific forbidden primitive
CS form
QIT/math form
positive fixture
negative control
boundary control
receipt
non-redundancy check against existing constraints
```

## 6. Current Best Next Fences To Formalize

Priority:

```text
1. no primitive classical Markov chain
2. no primitive classical Markov blanket
3. no primitive tensor factorization
4. no primitive scalarization
5. no primitive smoothness/continuity
```

Why:

These are exactly where FEP, Holodeck, flux, process tensors, and proof-target
translations are most likely to smuggle classical structure.

