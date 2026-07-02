# Math Proof Agenda

Date: 2026-05-23

Status: research agenda. This does not claim any open problem is solved.

External status note:

The Clay Mathematics Institute lists the Millennium Prize Problems. As of the
current official Clay pages checked for this packet, the Poincare conjecture is
the resolved one; the main open targets for this project-facing agenda are
Riemann Hypothesis, P vs NP, Navier-Stokes, Yang-Mills mass gap, Hodge
Conjecture, and Birch and Swinnerton-Dyer.

Reference URLs checked:

```text
https://www.claymath.org/millennium-problems/
https://www.claymath.org/millennium/poincare-conjecture/
```

## 1. What This Project Can Actually Do

This project should not begin by trying to "solve Riemann" or "solve P vs NP."

It can do useful proof work by:

```text
1. translating a hard problem into the constraint/QIT language;
2. finding finite toy analogs;
3. building counterexample searches;
4. extracting invariant candidates;
5. identifying what would need a real theorem;
6. rejecting bad translations early.
```

Sims do not prove infinite theorems. They can expose structure, kill false
routes, and generate proof targets.

## 2. Plausibility Ranking For This System

### Highest Near-Term Fit: Internal Physics/QIT Math

Why:

The model already uses finite density states, noncommuting channels, spinor
geometry, Hopf/Weyl structures, finite path sums, and entropy/cut readouts.

Near-term proof targets:

```text
QIT-FEP finite variational identity
capacity bounds for finite path families
noncommuting order-gap lemmas
flux-current invariance or non-invariance under gauge/basis changes
Axis0 candidate equivalence/nonequivalence theorems
Holodeck posterior-update monotonicity under named controls
```

This is the most plausible area for near-term proof work.

### Strong Fit: Yang-Mills And Mass Gap Analogs

Why it fits:

```text
gauge fields, curvature, holonomy, connection, mass gap, spectral gap,
noncommuting operators
```

QIT translation:

```text
finite lattice gauge carrier
finite connection/holonomy operators
finite Wilson-loop-like readouts
finite transfer operator spectrum
mass-gap analog = lower spectral gap bounded away from zero under scaling
```

Near-term scout:

```text
finite SU(2)-like lattice channel family with gauge controls and spectral-gap
readout.
```

Claim ceiling:

```text
toy mass-gap analog only, not Yang-Mills proof.
```

### Strong Fit: Navier-Stokes Analogs

Why it fits:

```text
flow, dissipation, turbulence, finite energy, regularity/breakdown,
attractor basins
```

QIT translation:

```text
finite cellular density lattice
CPTP dissipative update
energy-like observable
entropy/dissipation readout
regularity analog = bounded observable growth across finite time horizon
breakdown analog = threshold blow-up in bounded fixture
```

Near-term scout:

```text
finite lattice flow channel comparing noncommuting update, commuting diffusion,
and classical finite-difference controls.
```

Claim ceiling:

```text
finite regularity analog only.
```

### Medium Fit: Riemann Hypothesis

Why it might fit:

```text
spectral statistics
random matrix theory
operator zeros
trace formulas
prime distribution as constraint pattern
```

QIT translation:

```text
finite Hermitian operator families
spectral statistics
unitary evolution phases
trace-formula-like finite sums
zeta-zero comparison as a readout, not a proof
```

Near-term scout:

```text
finite operator family whose spectrum is compared against zeta-zero statistics
and random/unitary controls.
```

Claim ceiling:

```text
spectral analogy or invariant search only.
```

### Medium-Low Fit: P vs NP

Why it might fit:

```text
finite witnesses, verification, search, proof complexity, bounded work
```

QIT/CS translation:

```text
finite verifier as probe family
solution search as path family
constraint manifold as feasible witness surface
P vs NP analog = gap between checking and constructing under bounded channels
```

Near-term scout:

```text
bounded witness-search geometry comparing verifier complexity, search path
growth, and compression under noncommuting update rules.
```

Claim ceiling:

```text
complexity-geometry toy model only.
```

### Medium Fit But Requires Different Expertise: Hodge Conjecture

Why it might fit:

```text
geometry, topology, algebraic cycles, cohomology, forms
```

QIT translation:

```text
finite chain/cochain complexes
Hodge decomposition analogs
projectors onto harmonic representatives
cycle vs boundary distinguishability under finite probes
```

Near-term scout:

```text
finite complex where candidate algebraic-cycle analogs are tested against
topological/harmonic controls.
```

Claim ceiling:

```text
finite cohomology analog only.
```

### Medium Fit But Far From Current Sims: Birch And Swinnerton-Dyer

Why it might fit:

```text
elliptic curves, ranks, L-functions, modularity, finite mod-p evidence
```

QIT translation:

```text
finite mod-p point-count sequences
rank-like finite invariant
spectral or entropy readout over arithmetic data
correlation between vanishing order analog and rank analog
```

Near-term scout:

```text
bounded elliptic-curve data fixture that tests whether QIT-style spectral or
entropy features recover known rank labels better than baselines.
```

Claim ceiling:

```text
feature-discovery and analogy only.
```

## 3. Other Plausible Math Lanes

Potentially useful adjacent targets:

```text
Atiyah-Singer index theorem analogs
Ricci flow and geometric evolution analogs
spectral graph theory
operator algebras
noncommutative geometry
topological quantum field theory toy models
random matrix universality
complexity theory and proof complexity
information geometry
categorical process theories
```

These may be more useful than directly attacking a Millennium problem because
they can produce tools, lemmas, and finite gates that later feed larger proof
programs.

## 4. Proof-Work Process

For any proof target:

```text
1. name the exact theorem or conjecture;
2. name the accepted mathematical statement from external sources;
3. identify which part maps to F01/N01/QIT;
4. build a finite toy analog;
5. state what would count as failure;
6. run counterexample search;
7. extract invariant or lemma candidate;
8. do not claim the original theorem unless a conventional proof exists.
```

## 5. Immediate Next Proof-Lane Candidates

Best next three:

```text
1. internal QIT-FEP finite variational theorem packet;
2. flux-current gauge/basis invariance packet;
3. finite lattice Yang-Mills spectral-gap analog scout.
```

Why:

They are closest to existing sims and least likely to become empty analogy.
