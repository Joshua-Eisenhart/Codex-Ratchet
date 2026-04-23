# Mass Equivalence Engine — Deeper Map

## Purpose
This doc is the deeper version of the cross-domain map.
It answers: what is actually shared across entropy, geometry, compression, QIT, AI, physics, and evolutionary-style models?

The answer is not that every formula is identical.
The answer is that many domains can be represented by the same underlying engine:
- state carrier
- probe family
- operator/channel dynamics
- admissible geometry
- information functional
- constraint manifold

## Core claim
A large class of mathematical objects in these fields are equivalent up to representation:
- density matrices / operators
- state vectors / pure-state rays
- partial traces / reduced states
- channels / CPTP maps / Lindbladians
- correlation measures
- spectral decompositions
- manifold metrics and curvature objects

That does not mean all the fields are the same.
It means they can often be cast into a common operational form.

## 1) Exact quantum/operator lifts
These are genuine operator versions, not just analogies.

### Entropy and information
- von Neumann entropy: S(ρ) = -Tr(ρ log ρ)
- Rényi entropy family: S_α(ρ) = (1/(1-α)) log Tr(ρ^α)
- Tsallis entropy family: T_q(ρ) = (Tr(ρ^q)-1)/(1-q)
- min-entropy: -log λ_max(ρ)
- max-entropy: one-shot dual extremal forms
- relative entropy: D(ρ||σ)
- mutual information: I(A:B)
- conditional entropy: S(A|B)
- coherent information: I_c(A⟩B)

### Geometry
- trace distance
- fidelity / Bures geometry
- Fubini-Study geometry for pure rays
- quantum Fisher information
- quantum geometric tensor
- Berry phase / Berry curvature / holonomy

### Compression / factorization
- spectral decomposition
- Schmidt decomposition
- singular-value structure for matrices and bipartite operators
- low-rank state approximation
- quantum PCA style projection

### Evolution
- unitary channels
- CPTP channels
- open-system Lindblad evolution
- Kraus operator sums
- measurement update / instruments

## 2) Approximate or structural lifts
These are not exact identities, but they are strong alignments.

### Classical to quantum-like
- probability distribution → diagonal density matrix or coarse operator state
- feature vector → pure-state amplitude vector or encoded operator state
- covariance matrix → density-like covariance operator
- sample geometry → state-space geometry
- selection dynamics → constrained state evolution / viability on a carrier

### Compression / ML to QIT-like
- PCA → spectral truncation / low-rank operator projection
- SVD → Schmidt decomposition / operator factorization
- representation learning → probe selection / equivalence-class refinement
- clustering → partition under admissible probe signatures
- uncertainty quantification → entropy / mixedness / spread

### Evolutionary models to constrained-state dynamics
- population distribution → state over types
- fitness landscape → probe-weighted admissibility surface
- selection → survivorship under constraints
- mutation/recombination → channel / update map
- attractor or ratchet language → state-space survivorship under repeated admissibility

## 3) What the current sims actually support
The research so far is not abstract only; it already points to a stable core.

### State representations at L0
Artifact: `state_representations_L0_results.json`
- 9 of 9 representations survive
- purification ranks highest
- coherence vector is the best d=4-extensible bridge
- eigenvalues are weak because they discard phase
- Husimi and Wigner are lossy/smoothed

Interpretation:
- there is no single canonical state representation for all uses
- the best representation depends on what the probe needs to see

### Geometry at L0
Artifact: `geometry_families_L0_results.json`
- trace distance survives
- Bures survives
- Fubini-Study survives on pure states
- QFI survives
- QGT metric part survives
- HS-alone is too flat
- relative entropy is not a metric
- real-only collapse kills Berry/curvature
- commutative collapse kills geometry

Interpretation:
- the admissible geometry is curved and complex
- the geometry is inseparable from the carrier and from the probe family

### Entropy battery
Artifact: `entropy_readout_packet_run_results.json`
- spectral entropy families agree on qubit mixedness ordering
- diagonal Shannon is basis-dependent
- product-proxy conditional entropy adds no signal in the current L/R engine
- no simple spectral entropy rescues the pure-state Fi blind spot

Interpretation:
- entropy is useful, but it is not a universal substitute for geometry, operator structure, or channel structure

### Correlation / axis evidence
Artifact: `axis0_full_spectrum_results.json`
- local-only L|R families fail to give useful signal
- Xi_shell is the strongest candidate bridge family in the packet
- coherent information is the signed cut quantity that matters

Interpretation:
- total correlation is not enough
- bridge and cut structure are load-bearing

## 4) The real equivalence classes
A useful deep map is not 1:1 between fields.
It is a partition into structural classes.

### Class A: State-carrier class
Examples:
- density matrix
- pure state / ray
- coherence vector
- purification
- Bloch / Stokes / operator coordinates
- phase-space distributions (when treated as encoded views)

What it does:
- carries the system state
- supports probe action
- supports reduced descriptions

### Class B: Distinguishability / geometry class
Examples:
- trace distance
- fidelity / Bures
- Fubini-Study
- QFI
- QGT
- Berry curvature / holonomy

What it does:
- tells you how far states are under admissible probes
- detects curvature and sensitivity
- separates flat from genuinely geometric structure

### Class C: Correlation / entropic class
Examples:
- mutual information
- conditional entropy
- coherent information
- entanglement entropy
- concurrence / negativity
- min/Rényi/Tsallis/vN variants

What it does:
- summarizes shared structure between subsystems
- measures information retained or lost under reduction
- detects quantum vs classical correlations when used properly

### Class D: Operator / dynamical class
Examples:
- Pauli and Clifford bases
- commutators
- channels
- Kraus maps
- Lindbladians
- measurement instruments

What it does:
- evolves, perturbs, and probes the carrier
- decides whether structure is visible or invisible

### Class E: Compression / factorization class
Examples:
- SVD
- PCA
- Schmidt decomposition
- low-rank truncation
- spectral projectors

What it does:
- finds the smallest subspace or factorization preserving admissible signal

## 5) Where each class matters in actual domains

### Quantum computing
- carrier class: qubits, density matrices, pure rays
- geometry class: fidelity, trace distance, QFI for parameter estimation
- correlation class: entanglement, mutual information, coherent information
- operator class: gates, channels, noise models
- compression class: circuit compression, state compression, QPCA ideas

### Physics
- carrier class: quantum states, thermal states, reduced density operators
- geometry class: projective geometry, information geometry, Berry phase
- correlation class: entanglement and thermal correlations
- operator class: Hamiltonians, Lindbladians, measurement
- compression class: low-rank effective models, mode truncation

### Computer science / algorithms
- carrier class: feature embeddings, distributional states, matrices
- geometry class: metrics for similarity and clustering
- correlation class: dependence structure, information flow
- operator class: transforms, kernels, channel-like processes
- compression class: PCA, SVD, dimensionality reduction, approximate inference

### AI / ML
- carrier class: representation states / latent states
- geometry class: manifold learning, metric learning, uncertainty geometry
- correlation class: mutual information, entropy regularization, bottleneck ideas
- operator class: transformations, layers, diffusion/transition processes
- compression class: bottlenecks, low-rank adaptation, pruning, distillation

### Evolutionary / selection-style models
- carrier class: population or genotype distribution
- geometry class: distance between population states / selective landscapes
- correlation class: linkage / shared structure / retention of signal
- operator class: mutation-selection update, inheritance maps
- compression class: coarse-graining by phenotype or fitness equivalence

## 6) What "mass equivalence" can mean operationally
It should mean one of these, not a vague identity:

1. Same carrier, different representation
- e.g. density matrix vs Bloch vs coherence vector

2. Same operator action, different probe family
- e.g. commutator sensitivity vs spectral-only view

3. Same geometry, different coordinate system
- e.g. Fubini-Study vs Berry transport on pure states

4. Same information functional, different subsystem cut
- e.g. mutual information vs coherent information vs conditional entropy

5. Same compression problem, different basis
- e.g. PCA vs SVD vs Schmidt

6. Same constraint surface, different domain labels
- e.g. selection dynamics, inference, and channel evolution as the same admissibility problem

## 7) Why density matrices matter so much
Density matrices are likely fundamental in your stack because they are the least lossy common currency for:
- state
- mixture
- uncertainty
- reduction
- channel action
- entropy
- geometry
- correlation

If the engine is built around finite admissible probes, then density operators are the natural base language for the carrier.

## 8) What should be simulated next
The next research sims should test equivalence class by equivalence class:
- compare carrier encodings on the same probe family
- compare geometry metrics on the same state family
- compare entropy families on the same joint/reduced state family
- compare compression families on the same operator data
- run negative controls for basis dependence, real-only collapse, commutative collapse, and spectrum-only blindness

## 9) Practical conclusion
Yes, there may be a broad structural equivalence across many engines of math.
But the equivalence is not “everything is the same.”
It is:
- the same carrier language
- the same probe logic
- the same constraint manifold logic
- the same geometry/information/compression interaction

That is enough to unify a lot of physics, QIT, AI, CS, and evolutionary modeling without pretending they are literally identical.
