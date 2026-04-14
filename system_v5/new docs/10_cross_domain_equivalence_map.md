# Cross-Domain Equivalence Map

## Purpose
This doc connects the current research stack to actual domains:
- quantum information processing
- compression and spectral math
- information geometry
- machine learning / AI
- computer science / algorithms
- physics
- evolutionary / selection-style models

It is evidence-backed, but still a working map.

## Short answer
Yes: many of the objects you care about have density-matrix / operator / channel versions.
Not every classical formula survives unchanged, but a large fraction does survive as a quantum or operator-algebraic analogue.

The recurring pattern is:
- classical distribution / feature vector / state estimate
  → density operator / channel / reduced state
- scalar summary
  → spectral or information-geometric functional
- geometry on samples
  → geometry on state space / manifold / channel space
- evolution rule
  → CPTP map, unitary, Lindbladian, or constrained update

## 1) Entropy families and their density-matrix forms
The answer is not "one entropy for everything".
The answer is "many entropy families become well-defined on density operators."

### Common quantum-compatible forms
- von Neumann entropy: S(ρ) = -Tr(ρ log ρ)
- Rényi entropy: S_α(ρ) = (1/(1-α)) log Tr(ρ^α)
- Tsallis entropy: T_q(ρ) = (Tr(ρ^q)-1)/(1-q)
- min-entropy: S_min(ρ) = -log λ_max(ρ)
- max-entropy: dual extremal forms used in one-shot information theory
- relative entropy: D(ρ||σ) = Tr(ρ(log ρ - log σ))
- conditional entropy: S(A|B) = S(AB) - S(B)
- mutual information: I(A:B) = S(A) + S(B) - S(AB)
- coherent information: I_c(A⟩B) = S(B) - S(AB)

### Important boundary
- some classical entropies are basis-dependent if naively ported
- diagonal Shannon entropy is not intrinsic to the state; it depends on basis/probe
- spectral families often agree on ordering for qubit mixedness, but not on all tasks

### What the current sims already showed
- spectral families are qubit-order equivalent in the tested battery
- Shannon-on-diagonal shifts under basis change
- product-proxy conditional entropy in the current L/R engine added no signal
- no simple entropy replacement fixed pure-state Fi blindness

## 2) Quantum information processing math
These are already native to density-matrix language:
- state preparation
- unitary channels
- CPTP maps
- partial trace
- measurement / POVMs
- entanglement witnesses
- coherent information and channel capacity ideas
- mutual information as total correlation
- fidelity / Bures / trace-distance state comparison
- QFI / QGT / Berry geometry

This is the core reason density matrices and probes look fundamental in your stack.
They unify state, measurement, and evolution.

## 3) Compression math and spectral math
Many compression tools are really the same operator story in different clothing:
- SVD
- PCA / quantum PCA
- Schmidt decomposition
- low-rank approximation
- spectral truncation
- principal subspace projection
- covariance/operator eigenstructure

### Relationship to the stack
- SVD/PCA are compression on Euclidean data
- Schmidt decomposition is compression on bipartite quantum structure
- quantum PCA is spectral compression on a density operator / covariance-like object
- low-rank density approximations are compression of mixed-state structure

### Why this matters
Compression is not just a numerical trick.
It is a candidate equivalence between:
- redundancy
- distinguishability
- accessible information
- admissible probe families

## 4) Rich geometry
The geometry layer is not a decorative overlay.
It is part of the admissible structure on state space.

### Geometry objects already supported by the research
- trace distance: operational metric
- fidelity / Bures distance: information geometry
- Fubini-Study metric: pure-state projective geometry
- quantum Fisher information: sensitivity metric
- quantum geometric tensor: metric + curvature package
- Berry phase / holonomy: curvature/transport effect

### What the L0 geometry run showed
- trace distance, Bures, and Fubini-Study survive as real metrics
- Hilbert-Schmidt alone is too flat as a sole geometry
- relative entropy is not a metric
- real-only restriction kills Berry phase and curvature
- commutative operators kill nontrivial geometry

### Meaning
The admissible geometry is curved, complex, and probe-relative.
This is why pure-state CP^1 / Hopf-type structure keeps appearing.

## 5) Where these ideas show up in actual fields

### Quantum computing
- state tracking by density matrices
- channel composition
- error correction and noise modeling
- fidelity, trace distance, and Bures comparisons
- entanglement and concurrence/negativity witnesses
- QFI/QGT for parameter estimation and variational circuits

### Physics
- statistical mechanics and thermal states
- open quantum systems / Lindblad dynamics
- many-body correlations and reduced states
- geometric phase, Berry curvature, adiabatic transport
- information geometry for phase transitions and state distinguishability

### Computer science / algorithms
- compression and low-rank approximation
- spectral methods for clustering, embedding, and graph analysis
- operational equivalence and Blackwell-style comparisons
- channel capacity / information flow framing
- distinguishability under finite probe families

### AI / ML
- covariance and representation learning
- manifold methods / geometry-aware embeddings
- uncertainty and entropy regularization
- spectral compression of networks or activations
- tensor and operator viewpoints on correlations

### Evolutionary / selection-style models
- state = population distribution or mixture state
- probe = selection pressure / observable
- geometry = admissible transition manifold
- entropy = diversity / uncertainty / coarse-grained spread
- coherent information analogues can express retention across constraints

This is not literally quantum biology by default.
It is a structural analogy: constrained state evolution under admissible probes.

## 6) The mass-equivalence idea
Your hypothesis is plausible in the following precise sense:

Many systems can be reframed as:
- a state carrier
- a probe family
- a constraint manifold
- an admissible geometry
- an information functional
- an evolution rule

That gives a common engine for comparing:
- physics
- quantum information
- compression
- learning dynamics
- evolutionary selection

The equivalence is not exact identity across all domains.
It is a structural equivalence class under the right probes.

## 7) What is most likely to be fundamental
Based on the current research, the most robust primitives are:
- density matrices / operators
- admissible probes
- partial trace / channel structure
- noncommuting operator algebra
- curved information geometry

Entropy is important, but not first.
It is one diagnostic family among several.

## 8) Simulation implications
The next sims should test these correspondences directly:
- same state, many entropy forms
- same state, many geometry forms
- same state, many compression forms
- same probe family across multiple carriers
- same carrier across multiple probes
- explicit negative controls for basis dependence, commutative collapse, and flat-geometry collapse

## 9) Practical verdict
Yes, there is a serious prospect of a common engine spanning many fields.
But the engine must be built from admissible carrier/probe/geometry structure first,
then the measures are compared on top of that.
