# Aligned Sim Backlog and Build Order

## Purpose
This doc is the next-step bridge from the newly tested L0 building blocks to the rest of the system.
It is not a theory doc. It is a build-order doc for what should be simulated next, in the right alignment.

## What the recent L0 work established
Reported by the recent foundation runs:
- state representations at L0 were compared directly
- geometry families at L0 were compared directly
- a broader math inventory was catalogued
- an entropy sweep across low layers was also run

The key point is not that one metric won everywhere.
The key point is that several families collapse to the same underlying structure under different probes, while some remain genuinely distinct.

## Likely base primitives after the L0 passes
The current working hypothesis is:
- density matrices are foundational
- probes are foundational
- Pauli / Clifford generators are foundational operator bases
- partial trace / CPTP structure is foundational for dynamics and composition
- geometry is not separate from the carrier; it is constraint-compatible structure on the same state space

## L0 collapse classes to keep separate
The 161-family inventory should not be treated as 161 unrelated things.
A first-pass collapse map is:

### 1. State representation class
Likely one family with multiple views:
- density matrix
- Bloch vector / coherence vector
- purification
- eigenvalue / spectrum view
- Stokes-type parameterization

These differ by probe power and dimensional extensibility, not by ontological status.

### 2. Geometry / metric class
A second family of views over the same carrier:
- trace distance
- fidelity / Bures geometry
- Fubini-Study geometry for pure states
- quantum geometric tensor / quantum Fisher information
- Berry phase / holonomy

These are not interchangeable, but they are aligned to the same carrier geometry when the carrier is admissible.

### 3. Entropy / information class
A third family of measures over reduced or joint states:
- mutual information
- conditional entropy
- coherent information
- von Neumann entropy
- Rényi / Tsallis / min/max variants

These are not the same quantity and should not be collapsed too early.

### 4. Algebra / channel class
A fourth family of operators and dynamics:
- Pauli algebra
- Clifford algebra
- CPTP maps
- channels / instruments
- commutators / noncommutation tests

### 5. Decomposition / compression class
A fifth family of factorization tools:
- Schmidt decomposition
- SVD
- principal-subspace truncation
- low-rank approximation

## What the L0 passes suggest
The early signal is that:
- spectrum-only views are too lossy to be the whole story
- coherence-vector style representations are better than eigenvalues alone
- Fubini-Study / Berry-type geometry is real on the pure-state surface
- flat geometry by itself is insufficient as a sole geometry
- the allowed math is likely carrier-first and probe-relative

## Build order after L0
The next simulations should follow this order:

### L1: Carrier and probe admissibility
Test whether the candidate representation preserves:
- trace / normalization
- positivity where required
- probe-relative identity
- the ability to distinguish operators under admissible probes

### L2: Geometry survivability on the same carrier
Test all allowed geometry families on the same state:
- metric consistency
- triangle inequality where relevant
- curvature / holonomy behavior
- pure vs mixed distinctions
- real vs complex collapse failure modes

### L3: Operator family discrimination
Test:
- commutators vs commuting collapse
- left/right action asymmetry
- Pauli vs Clifford operator bases
- channel action vs static summaries

### L4: Bipartite structure and correlation
Test:
- partial trace families
- mutual information
- conditional entropy
- coherent information
- concurrence / negativity
- Schmidt-mode structure

### L5: Entropy family sweep
Only after the carrier, geometry, and operator layer are admitted should the full entropy family sweep become decisive.

## What to simulate next
The next aligned simulations should include:

1. Collapse analysis
   - Which of the 161 families are actually the same thing under different probes?
   - Which are genuinely distinct?

2. Dependency DAG
   - Which families require which lower-level primitives?
   - Which are derived views rather than new structure?

3. L1 upward fence test
   - take the L0 survivors and push them through the next admissibility fences

4. Geometry cross-checks on the same state
   - compare Fubini-Study, Bures, trace distance, QFI, QGT, Berry

5. Entropy family cross-checks on the same carrier
   - compare Shannon, vN, Rényi, conditional entropy, mutual information, coherent information, min-entropy, and negativity/discord-style witnesses where applicable

6. Axis tests only after admission
   - Axis 0 should be tested as a carrier-relative polarity / signed scalar
   - Axis 6 should be tested as left/right action asymmetry
   - neither should be promoted until the lower layers are stable

## Negative controls that must stay in every batch
- carrier flattening
- spectrum-only blindness
- commutative collapse
- real-only collapse
- flat-geometry-only collapse
- entropy assumption lock-in
- diagnostic-only substitution for real evidence

## Promotion rule
A family is not canon because it is elegant.
It is canon only if it:
- survives the base carrier
- survives the geometry layer
- survives the operator layer
- survives the negative suite
- remains distinct under probe changes when it should remain distinct

## Practical takeaway
The repo now has enough evidence to stop treating the system as a single entropy story.
The correct build program is a stacked one:
carrier → geometry → operators → correlations → entropy → axes.
