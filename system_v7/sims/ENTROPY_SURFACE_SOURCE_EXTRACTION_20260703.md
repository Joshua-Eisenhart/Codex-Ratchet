- Lines 75-78: entropy map is “scalar functional over the partition `X_t/~_P`”; geometry map is “adjacency / mutual-information distance / Fisher metric / Hamming graph on `X_t`”
- Lines 83-83: “entropy throws away *which* distinctions and keeps the count; relational geometry throws away the count and keeps adjacency”
- Lines 122-132: “THE CO-RATCHET (entropy + geometry recomputed each step)” and `E_{t+1} = EntropySuite(...)`, `G_{t+1} = InducedGeometry(...)`
- Lines 137-151: recomputing `E` and `G` is “background-independent”; the written `E↔G` equations are a “simultaneous mutual recursion / fixed-point equation”; final disposition: entropy is downstream readout, `E_t` is not in `Adm_C`.

2. `reference_docs_from_josh/toe_cosmology/DR_entropic_monism_hopf.md` quotes

- Lines 5-11: start from “information/entropy exchange,” define distance from mutual information, and use `S^3` because qubit pure states/Hopf/Bloch structure match `S^1 -> S^3 -> S^2`.
- Lines 30-34: mutual information uses von Neumann entropy: `I(A:B)=S(rho_A)+S(rho_B)-S(rho_AB)`, `S(rho)=-Tr(rho log rho)`.
- Lines 52-58 and 78-82: regularized/log inverse MI becomes edge length; shortest-path graph metric supplies metric structure.
- Lines 143-146 and 193-198: normalized qubit spinor lives on `S^3`; quotient global phase gives Bloch sphere `S^2`; Hopf map diagnostic projects `S^3 -> S^2`.

3. Existing sims computing pieces of surface identity

- `coupled_coratchet_dualloop_sim.py` lines 2-24, 45-63, 108: computes entropy ratchet dual loop, cooling/heating entropy fixed points, noncommuting order flux; does NOT compute metric equality, Bures/fidelity equality, `K_rho=-log rho`, or separation-UNSAT for surface identity.
- `coratchet_axis_orthogonality_sim.py` lines 2-24, 56-76, 136-139: computes terrain-native entropy/coherence surface behavior and z3/cvc5 forced axis laws; does NOT prove entropy-geometry metric equality or `E↔G` fixed-point uniqueness.
- `terrain_differentiation_sim.py` lines 8-15, 51-58: computes terrain fingerprints including fixed-point Bloch, radius, fixed-point entropy, generator spectral gaps, chirality/trajectory geometry proxies; does NOT compute Bures/fidelity metrics or surface identity equality.
- `terrain_information_signature_sim.py` lines 9-22, 61-79, 99-139: computes entropy-production/info-channel signatures and solver-forced 3-class partition; does NOT compute full 8-way metric equality or `K_rho=-log rho`.
- `terrain_8way_separation_sim.py` lines 2-15, 56-73, 97-98: computes 8-terrain separation via coherence kill, steady fixed-point `sz`, phase velocity, with z3/cvc5 no-collision UNSAT; does NOT connect separation to entropy-geometry metric equality.
- `terrain_sourcelock_axis0_sim.py` lines 10-11, 23-43: computes/source-locks terrain dissipator fixed-point `z`; does NOT compute entropy readout, Bures/fidelity, or surface identity.
- `terrain_qutip_crosscheck.py` lines 2-7, 51-58: validates terrain Liouvillians and CPTP flows against QuTiP; does NOT compute entropy/geometry identity.
- Repo-wide search: `K_rho=-log rho` absent; Bures absent; `fidelity` exists in memory/no-cloning/Hopfield-style sims but not as surface-identity metric equality; `logm` relative-entropy pieces exist in `agent_loop_sim.py`, `holodeck_sim.py`, `lev_bridge_sim.py`, `three_qubit_octonion_fep.py`, but not named `K_rho=-log rho` or tied to co-ratchet surface equality.
tokens used
47,759
1. `P1_must_read/...entropic_monism...DRAFT_20260614.md` quotes

- Lines 46-48: “### 1.2 Entropy is the primary READOUT, not the substance” / “Entropy is the **primary scalar readout** of `D_t`”
- Lines 52-53: “entropy = readout/measure over the partition of distinctions” / “entropy derived”
- Lines 75-78: entropy map is “scalar functional over the partition `X_t/~_P`”; geometry map is “adjacency / mutual-information distance / Fisher metric / Hamming graph on `X_t`”
- Lines 83-83: “entropy throws away *which* distinctions and keeps the count; relational geometry throws away the count and keeps adjacency”
- Lines 122-132: “THE CO-RATCHET (entropy + geometry recomputed each step)” and `E_{t+1} = EntropySuite(...)`, `G_{t+1} = InducedGeometry(...)`
- Lines 137-151: recomputing `E` and `G` is “background-independent”; the written `E↔G` equations are a “simultaneous mutual recursion / fixed-point equation”; final disposition: entropy is downstream readout, `E_t` is not in `Adm_C`.

2. `reference_docs_from_josh/toe_cosmology/DR_entropic_monism_hopf.md` quotes

- Lines 5-11: start from “information/entropy exchange,” define distance from mutual information, and use `S^3` because qubit pure states/Hopf/Bloch structure match `S^1 -> S^3 -> S^2`.
- Lines 30-34: mutual information uses von Neumann entropy: `I(A:B)=S(rho_A)+S(rho_B)-S(rho_AB)`, `S(rho)=-Tr(rho log rho)`.
- Lines 52-58 and 78-82: regularized/log inverse MI becomes edge length; shortest-path graph metric supplies metric structure.
- Lines 143-146 and 193-198: normalized qubit spinor lives on `S^3`; quotient global phase gives Bloch sphere `S^2`; Hopf map diagnostic projects `S^3 -> S^2`.

3. Existing sims computing pieces of surface identity

- `coupled_coratchet_dualloop_sim.py` lines 2-24, 45-63, 108: computes entropy ratchet dual loop, cooling/heating entropy fixed points, noncommuting order flux; does NOT compute metric equality, Bures/fidelity equality, `K_rho=-log rho`, or separation-UNSAT for surface identity.
- `coratchet_axis_orthogonality_sim.py` lines 2-24, 56-76, 136-139: computes terrain-native entropy/coherence surface behavior and z3/cvc5 forced axis laws; does NOT prove entropy-geometry metric equality or `E↔G` fixed-point uniqueness.
- `terrain_differentiation_sim.py` lines 8-15, 51-58: computes terrain fingerprints including fixed-point Bloch, radius, fixed-point entropy, generator spectral gaps, chirality/trajectory geometry proxies; does NOT compute Bures/fidelity metrics or surface identity equality.
- `terrain_information_signature_sim.py` lines 9-22, 61-79, 99-139: computes entropy-production/info-channel signatures and solver-forced 3-class partition; does NOT compute full 8-way metric equality or `K_rho=-log rho`.
- `terrain_8way_separation_sim.py` lines 2-15, 56-73, 97-98: computes 8-terrain separation via coherence kill, steady fixed-point `sz`, phase velocity, with z3/cvc5 no-collision UNSAT; does NOT connect separation to entropy-geometry metric equality.
- `terrain_sourcelock_axis0_sim.py` lines 10-11, 23-43: computes/source-locks terrain dissipator fixed-point `z`; does NOT compute entropy readout, Bures/fidelity, or surface identity.
- `terrain_qutip_crosscheck.py` lines 2-7, 51-58: validates terrain Liouvillians and CPTP flows against QuTiP; does NOT compute entropy/geometry identity.
- Repo-wide search: `K_rho=-log rho` absent; Bures absent; `fidelity` exists in memory/no-cloning/Hopfield-style sims but not as surface-identity metric equality; `logm` relative-entropy pieces exist in `agent_loop_sim.py`, `holodeck_sim.py`, `lev_bridge_sim.py`, `three_qubit_octonion_fep.py`, but not named `K_rho=-log rho` or tied to co-ratchet surface equality.
