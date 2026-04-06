# Model, Math, Geometry, and Simulation Plan

## What this doc is
This is the synthesis layer tying the owner model to the research stack.
It does not declare canon by itself.
It proposes how the math and geometry should be simulated, tested, and only then promoted.

Narrower docs outrank this one.

## Core correction
Do not treat entropy as the only target.
Do not treat any proposed axis math as admitted until it has been simulated.
Do not treat geometry as one thing.
The system should test the full family of allowed math and geometry from the start, then let the constraints narrow it.

## Owner-model alignment
The current thesis is:
- primitive substrate = constraint on distinguishability
- probes are fundamental to identity
- entropy is a later admissible measure, not the primitive
- density matrices are a natural base object once a finite carrier is admitted
- geometry is constraint compatibility on that carrier
- correlation, entanglement, and operator structure are not decorative; they are the thing being measured

This means the right question is not:
"What is the one true entropy or geometry?"

The right question is:
"Which families of math survive simulation at each admissible layer?"

## Base mathematical primitives that should probably be primary
Likely fundamental objects for the system:
- density matrices / density operators
- probes / admissible probe families
- channels / CPTP maps
- partial traces
- reduced states
- correlation tensors
- graph and cell-complex carriers
- Pauli and Clifford generators as operator bases

Working hypothesis:
- density matrices and probes are probably the first stable language
- geometry then appears as admissible structure on top of that language
- the axes are then families of constrained operations on those objects

## What must be simulated before promotion
Every proposed math family or axis family must be simulated first.
That includes:
- entropy families
- correlation measures
- geometry families
- operator families
- axis families
- bridge families
- kernel families

A family only becomes "real" in the stack after it survives:
1. the relevant base carrier
2. the geometric constraint manifold at that layer
3. the negative controls
4. the cross-representation bridge checks
5. the same-state / different-probe tests

## Geometry should be simulated from step one
Do not wait until later layers to simulate geometry.
All allowed geometry candidates should be tested early, including:
- spherical / Hopf geometry
- torus / nested torus geometry
- cell-complex / graph geometry
- Clifford / spinor geometry
- operator-transport geometry
- bridge geometry between local and global views

The point is not to pick one geometry first.
The point is to see which geometries are actually admissible under the constraints.

## The simulation ladder

### Layer 0: Constraint and probe admissibility
Test:
- what counts as a probe
- what counts as distinguishability
- what probe families preserve identity under the root constraints
- which representations violate the base rules

### Layer 1: Carrier admission
Test:
- finite carrier candidates
- density matrix representability
- positivity / trace / normalization
- whether the carrier can support the proposed probe family

### Layer 2: Geometry candidates
Test each geometry family on the same carrier:
- Hopf / sphere / torus
- graph / cell complex
- Clifford/spinorial encoding
- any allowed topological or transport geometry

Negative controls:
- carrier flattening
- metric smuggling
- classical continuum shortcuts

### Layer 3: Operator family admission
Test:
- Pauli operators
- Clifford generators
- local vs joint operators
- channel maps
- left/right action asymmetry
- composition order sensitivity

### Layer 4: Bipartite structure
Test:
- partial traces
- joint density matrices
- correlation tensors
- mutual information
- coherent information
- concurrence / negativity
- Schmidt-style decompositions where applicable

### Layer 5: Entropy families
Test all candidates, not just von Neumann:
- Shannon
- von Neumann
- Rényi
- Tsallis
- min/max entropy
- conditional entropy
- mutual information
- coherent information
- entanglement entropy
- bridge-weighted or shell-weighted variants if they are formally defined

### Layer 6: Axis families
Only after the lower layers are real, test the proposed axes as structured operations:
- Axis 0 polarity / signed scalar behavior
- Axis 6 left/right action asymmetry
- any other axes already proposed in the model

## Proposal for the sim design
Use the same underlying state and run it through many admissible representations.
For each representation, check:
- does it preserve the base constraints?
- does it preserve the carrier?
- does it preserve the geometry?
- does it preserve the probe relation?
- does it survive the negative suite?

This is closer to a model-selection problem than a single-run proof.

## What to compare across families
For each candidate family, compare:
- admissibility under the base constraints
- stability across the same state under different probes
- sensitivity to geometry changes
- sensitivity to chirality / orientation / left-right asymmetry
- sensitivity to composition order
- whether the measure is a true witness or only a summary statistic
- whether it is scalar-only or preserves tensor / operator structure

## The likely shape of the system if the hypothesis is right
If the current direction is correct, then the stable core will look like:
- density matrices as the base state language
- probes as the base epistemic language
- geometry as an admissible carrier structure
- correlation tensors and partial traces as the bridge language
- entropy and information measures as later-layer diagnostics, not the foundation

## Proposed test program
A real test program should include:
1. build the base carrier
2. apply the same probe family across multiple allowed geometries
3. compare the candidate math families on the same state
4. run explicit negative controls
5. record which family survives at each layer
6. promote only the surviving family for that layer
7. keep the others as open candidates, not failures unless falsified

## Suggested output artifacts
Each sim should emit:
- state definition
- carrier definition
- geometry family used
- probe family used
- measure family used
- negative controls used
- invariance checks
- bridge checks
- failure reasons if any
- promotion status

## Bottom line
The system should not be built as "entropy first" or "geometry first".
It should be built as:
- constraint first
- admissible carrier and probe families next
- all allowed geometries simulated early
- all proposed math tested on the same states
- only then does the stack narrow to the surviving operators and measures
