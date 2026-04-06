# Research Inventory and Foundational Findings

## Purpose
This doc gathers the actual research results that have been simulated so far.
It is the current evidence-backed inventory, not a speculative wish list.

Narrower docs outrank this one.

## Core conclusion
The system is converging on a small set of primitive building blocks:
- density matrices / density operators
- admissible probe families
- Pauli / Clifford operator bases
- partial trace and CPTP/channel structure
- correlation tensors and bipartite structure
- admissible geometry on the same carrier

The larger math catalog is real, but many items collapse into a smaller number of equivalence classes under the admissible probes.

## 1) State representations at L0
Probe: `state_representations_L0`
Artifact: `system_v4/probes/a2_state/sim_results/state_representations_L0_results.json`

### Findings
- 9 of 9 representations survive L0
- top representation: purification
- most extensible representation to d=4: coherence vector
- density matrix remains a canonical base object
- eigenvalues are weak because they lose phase information
- Husimi and Wigner are lossy / smoothed views

### Ranking summary
1. purification
2. coherence_vector
3. density_matrix
4. bloch
5. stokes
6. characteristic
7. eigenvalues
8. wigner
9. husimi

### Interpretation
- purification is highly discriminating but not naturally extensible to d=4 in the same way
- coherence vector is the best bridge from qubit to higher-dimensional operator language
- eigenvalue-only views are blind to noncommutation and phase-sensitive structure
- smoothed phase-space views trade exactness for coarse geometry

## 2) Geometry families at L0
Probe: `geometry_families_L0`
Artifact: `system_v4/probes/a2_state/sim_results/geometry_families_L0_results.json`

### Findings
Surviving geometry families:
- trace distance
- Bures distance
- Fubini-Study distance on pure states
- QFI
- QGT metric part

Killed or rejected as sole geometry:
- Hilbert-Schmidt as sole geometry: flat, misses curvature
- relative entropy as metric: not symmetric, no triangle inequality
- real-only restriction: kills Berry phase and curvature, halves the state space
- commutative operators: kill nontrivial geometry

### Important geometry result
For pure states, the Fubini-Study metric and Berry structure are tightly aligned.
The geometry is not separable from holonomy in the pure-state limit.

### Interpretation
- the system prefers curved, complex, information-geometric structure
- flat, real-only, or commutative reductions are too weak for the full carrier
- Berry/QGT/Fubini-Study are all views of a coherent CP^1-level geometry

## 3) Entropy and information batteries
Artifact: `entropy_readout_packet_run_results.json`
Source packet: `entropy_readout_packet_run_results.json`

### Findings
- spectral entropy families on qubits agree on ordering:
  - linear
  - Renyi-2
  - Tsallis-2
  - von Neumann
  all line up on the tested spectral pairs
- diagonal Shannon is basis dependent and shifts under unitary change
- product-proxy conditional entropy in the current L/R engine adds no signal
- pure-state Fi blind spot is not fixed by switching among spectral entropies
- Renyi-2 tracks vN ordering on qubit mixedness

### Interpretation
- vN entropy is not “the only thing”; it is one member of a spectral family that often agrees in qubit mixedness ordering
- basis-dependent Shannon-on-diagonal is not a substitute for intrinsic state entropy
- conditional entropy and coherent information need the full joint / reduced-state structure, not just a local proxy

## 4) Correlation / cut-state / Axis-0 evidence
Artifact: `axis0_full_spectrum_results.json` and related readout packet

### Findings
- local-only L|R family fails: low/no MI, negative coherent information, not useful for quantum advantage
- Xi_shell survives as the strongest candidate in the readout packet
- Xi_hist_outer and Xi_hist_cycle remain candidate families but are weaker than Xi_shell
- coherent information is the signed cut quantity that matters in these runs
- some trajectories are only partially consistent with compression-from-future framing; not universal

### Interpretation
- the bridge family matters
- coherent information is structurally load-bearing for cut-state / advantage claims
- total correlation alone is not enough
- the system is sensitive to transport geometry and history-window structure

## 5) What the 161-family inventory means
The inventory is not 161 unrelated items.
It should be grouped into a smaller number of structural classes:

### A. State-representation class
- density matrix
- Bloch/coherence vector
- Stokes-like parameterization
- purification
- spectrum/eigenvalue view
- phase-space distributions

### B. Geometry / metric class
- trace distance
- fidelity/Bures geometry
- Fubini-Study geometry
- QFI/QGT
- Berry phase / holonomy

### C. Correlation / entropy class
- mutual information
- conditional entropy
- coherent information
- entanglement entropy
- concurrence / negativity
- Rényi/Tsallis/min/max variants

### D. Algebra / dynamics class
- Pauli algebra
- Clifford algebra
- channels / CPTP maps
- commutators / noncommutation tests
- left/right action asymmetry

### E. Decomposition / compression class
- SVD
- Schmidt decomposition
- principal-subspace truncation
- low-rank density approximation

## 6) Minimal foundational primitives suggested by the research
The current evidence keeps pointing to five irreducibles:
1. density matrices
2. probes
3. operator algebra (Pauli/Clifford/noncommutation)
4. partial traces and channel structure
5. admissible geometry on the same carrier

Everything else should be tested as a derived view or a candidate compression of those primitives.

## 7) Practical consequences for the sim program
The next simulations should not ask only “does this family exist?”
They should ask:
- what does this family reduce to under the admissible probes?
- what geometry does it preserve or destroy?
- what does it detect that simpler families miss?
- what is the correct collapse class?
- what survives the negative controls?

## 8) Recommended next bounded sim layers
1. collapse analysis of the 161 families
2. dependency DAG for the families
3. L1 carrier/probe fence tests
4. geometry cross-checks on the same state
5. entropy and information cross-checks on the same carrier
6. axis tests only after the above

## 9) Evidence status
This doc is evidence-backed by actual sim artifacts.
It is not complete, but it is real.
