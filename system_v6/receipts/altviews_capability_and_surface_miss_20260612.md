# Alt-views (grok-4.3 + gemini, advisory only) — the capability question + the surface v3 miss (2026-06-12)

Role per the fleet doctrine: ALTERNATIVE VIEWS AND OPTIONS, never authority; the codex workers test what survives. Raw: /tmp/altview_grok.json, /tmp/altview_gemini.txt.

## CONVERGENT ROWS (both routes independently)

- Q1 CHIRAL INFORMATION RECTIFICATION / DIODE (both routes, both high-confidence, standard-math-grounded): the L/R index pair as directional information routing a Szilard engine cannot do — the capability registry gets this as the top alt-view candidate w/ both routes finite tests.
- Q2 PURITY-INDUCED RADIAL SHRINKAGE (gemini rank-1 high-confidence, standard-math): an entangled pattern single-site reduced state is MIXED (Bloch radius < 1) — if the predicted -z cell expects near-pure radius, THE MISS IS PREDICTED BY ENTANGLEMENT ITSELF: the prediction erred, not the recovery; the finite check = compute the reduced-state radii (immediately checkable against the committed v3 results).

## GROK Q1+Q2 (verbatim)

**Q1 Options (ranked by descending confidence)**

Option 1 (standard-math-grounded, highest confidence): The dual-loop architecture supplies a finite, autonomous implementation of a controlled-phase or CNOT primitive between two logical qubits encoded in the 6-bit schedule. The dissipative loop supplies the measurement leg while the unitary loop supplies the conditional rotation; their non-commuting composition plus opposite chirality indices yields a net controlled unitary whose process matrix can be reconstructed from 64-slot outcome histograms. Finite test: prepare product input states |00\rangle, |01\rangle, |10\rangle, |11\rangle, run one full 64-step word, and verify that the observed two-site correlator matches the ideal CNOT truth table to within statistical error set by shot noise.

Option 2 (standard-math-grounded): The machine functions as a chiral information diode that rectifies quantized flux unidirectionally, allowing erasure of one logical bit conditioned on the parity of a second bit without an external feedback channel. This exceeds Szilard because the stage word itself encodes the conditional logic. Finite test: initialize two bits in a known joint state, execute left-chirality versus right-chirality words, and confirm that only one chirality produces a net reduction in total Shannon entropy while the opposite chirality increases it, measured by final projective readout.

Option 3 (partially speculative): The non-commuting loops generate a protected logical qubit whose dephasing rate is suppressed by the topological winding of the 8-stage word, enabling repeated error-transparent gates inside a single 64-slot cycle. Finite test: embed a Ramsey sequence across two successive words and show that coherence time scales linearly with the number of completed words rather than remaining constant as in an unstructured Szilard loop.

Option 4 (speculative): The engine can implement a finite, autonomous form of one-way quantum computation by consuming the dissipative-loop outcomes as cluster-state stabilizers. Finite test: prepare a four-qubit linear cluster encoded in successive schedule slots, run the word, and verify that adaptive single-site measurements reproduce the expected MBQC output statistics for a chosen Boolean function to within 5 % of the ideal value.

**Q2 Options (ranked by descending confidence)**

Option 1 (standard-math-grounded, highest confidence): The stored entangled state was a Bell pair whose single-site reduced states are exactly I/2; the prediction erroneously assumed a pure product state polarized at −z. The observed occupancy of other Bloch cells is therefore the correct maximally mixed outcome. Finite check: recompute the predicted cell using the actual reduced density matrices obtained by partial trace of the registered entangled pattern; agreement with data confirms the mismatch was a prediction-label error.

Option 2 (standard-math-grounded): Residual unitary evolution or readout miscalibration rotated the local Bloch vectors of the entangled pattern out of the target cell while leaving product patterns invariant because their stabilizers commute with the error channel. Finite check: insert an additional tomography block after storage and before readout; if the reconstructed local Bloch vectors lie on the equator rather than at −z only for the entangled pattern, the rotation hypothesis is supported.

Option 3 (partially speculative): The associative-memory Hamiltonian contains an implicit product-state bias in its Hebbian weights, so that only separable patterns converge to the registered chart cells while entangled patterns relax to a different attractor whose marginals occupy neighboring cells. Finite check: retrain the network with an explicit penalty term that enforces the target marginals for the entangled pattern and verify whether the missed cell is recovered.

Option 4 (speculative): The entangled pattern experienced an unaccounted entanglement-breaking channel (e.g., independent dephasing on each site) whose fixed point lies outside the predicted cell. Finite check: compare revival of the missed cell when the identical pattern is stored for half the usual time versus when an equivalent product pattern is stored for the full time; faster degradation only for the entangled case supports the channel hypothesis.

## GEMINI Q1+Q2 (verbatim)

### Q1: Capabilities of a Dual-Loop Noncommuting QIT Engine

**1. Chiral Information Rectification (Rank 1: Confidence High | Standard-Math-Grounded)**
While a Szilard engine requires a discrete measurement-and-feedback step to extract work from a single bath, a dual-loop machine with chiral variants can function as an autonomous "Information-Driven Ratchet." The non-commutativity between the unitary loop (coherent rotation) and the dissipative loop (measurement/reset) allows the engine to rectify vacuum or thermal fluctuations into a steady-state information-flux without an external "observer" trigger. By alternating stages, the machine breaks time-reversal symmetry at the schedule level.
*   **Finite Test:** Place the engine between two thermal baths at equal temperature ($T_H = T_L$). A Szilard engine will produce zero net work. If the QIT engine generates a persistent, direction-dependent current (flux) proportional to the chirality index, it demonstrates autonomous rectification.

**2. Non-Abelian Holonomic Work Extraction (Rank 2: Confidence Medium | Speculative)**
Because the loops do not commute, the sequence of operations within the 64-slot schedule generates a geometric phase (holonomy) that a single-loop engine cannot access. This allows for "Path-Dependent Work," where the energy extracted depends on the *order* of the stages in the stage word, rather than just the state of the bits. The engine can essentially "steer" the state through the Hilbert space to regions of lower local entropy that are inaccessible via simple dissipative erasure.
*   **Finite Test:** Run two schedules with identical stage counts but different stage-word permutations (e.g., $[U, D]$ vs $[D, U]$). If the work yield $\Delta W$ differs between the two sequences despite identical initial/final states, the machine is utilizing non-Abelian holonomy.

**3. Passive Quantum Error Correction as a Thermodynamic Cycle (Rank 3: Confidence Medium | Standard-Math-Grounded)**
In a Szilard engine, entropy is managed by discrete erasure. In this dual-loop machine, the unitary loop can be configured to perform syndrome-like rotations while the dissipative loop acts as a "cold reservoir" that continuously drains entropy from specific sub-manifolds. This allows the machine to maintain a "Code Space" in a steady state against noise—effectively performing "Passive QEC." The 64-slot schedule acts as a recurring parity check that "pins" the system to a specific manifold.
*   **Finite Test:** Introduce a known noise source (e.g., bit-flips at rate $\gamma$). Monitor the fidelity of a stored state over 1000+ cycles. A Szilard engine's stored state will decay at rate $\gamma$; the QIT engine should show a "Fidelity Plateau" where entropy remains constant despite the noise.

---

### Q2: Why the Entangled Pattern Missed the -z Cell

**1. Purity-Induced Radial Shrinkage (Rank 1: Confidence High | Standard-Math-Grounded)**
Associative memory predictions often assume states map to the surface of the Bloch sphere (pure states). However, for an entangled pattern, the single-site reduced density matrix $\rho_i$ is necessarily mixed ($\text{Tr}(\rho^2) < 1$). A mixed state lives *inside* the sphere, not on the surface. If the -z cell was defined as a surface region, the entangled state likely missed it because the site’s state "shrunk" toward the center (the maximally mixed state at the origin) due to its correlations with other sites.
*   **Finite Check:** Calculate the Linear Entropy $S_L = 1 - \text{Tr}(\rho_i^2)$ for the missed site. If $S_L > 0.1$, the state is too mixed to reliably hit a surface-defined cell; the "miss" is a depth error, not a coordinate error.

**2. Basis-Gauge Mismatch in Reduced Projections (Rank 2: Confidence Medium | Standard-Math-Grounded)**
Product states have a local, unique mapping to Bloch coordinates. For entangled patterns (e.g., a Bell-state family), the "information" is stored in the bipartite correlations, not the individual sites. The network may have successfully retrieved the correct *global* entangled state, but the local projection onto the -z cell is sensitive to the specific entanglement basis used in the "chart" definition. A small phase-shift in the entanglement (e.g., $|00\rangle + |11\rangle$ vs $|00\rangle - |11\rangle$) can wildly move the reduced state's position if the chart assumes a fixed global gauge.
*   **Finite Check:** Compute the Mutual Information $I(A:B)$ between the missed site and its neighbors. If $I(A:B)$ is high, re-visualize the "missed" state in the joint 2-site Hilbert space. If the 2-site state matches the pattern, the error was in the single-site mapping logic.

**3. Dissipative "Dark State" Attraction (Rank 3: Confidence Low | Speculative)**
The dissipative loop of the network might possess a "Dark State"—a specific state attractor that is transparent to product states but strongly attracts entangled manifolds. If the entangled pattern overlaps with this dark state, the retrieval dynamics will "pull" the state away from the predicted -z cell toward the attractor's coordinates. This would explain why product states (which don't see the dark state) hit their targets, while entangled states are diverted.
*   **Finite Check:** Map the "Retrieval Trajectory" in time-steps. If the entangled state begins at -z but migrates away during the dissipative stages of the cycle, while product states remain stationary at their cells, a dissipative bias (attractor) is present.
