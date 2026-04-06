# NOTEBOOK LM: DEEP SYSTEM PROMPT BATCH
**Context:** Use these prompts sequentially or individually inside Notebook LM after uploading the `Codex_Ratchet_NLM_Batch3_Update.zip` context pack.

---

## PROMPT 1: AXIS 0 (The Correlation Gradient)
> "Based on the provided `.txt` files containing the QIT Python logic (specifically `gain_calibration_v2_sim.py` and `szilard_64stage_v2_sim.py`) and the `AXIS_` spec documents, we need to mathematically formalize **Axis 0**. 
> 
> Currently, the system builds its foundation on standard Von Neumann entropy ($S(\rho) = -\text{Tr}(\rho \log_2 \rho)$). However, Axis 0 governs the *gradient of correlation/diversity* between two halves of the topological engine (e.g., Deductive Loop vs Inductive Loop, or Agent vs Environment), which can measure negatively.
> 
> Calculate and provide the explicit Python-ready math for Axis 0. Should we use Quantum Conditional Entropy $S(A|B) = S(AB) - S(B)$ (since it can go negative and maps entanglement)? Or should we use Quantum Mutual Information $I(A:B)$? Provide the exact formula and explain mathematically how this gradient binds the 8-stage QIT loop."

---

## PROMPT 2: AXIS 4 vs AXIS 5 (Resolving Orthogonal Conflation)
> "In the file `orthogonality_sim.py_CODE_DIGEST.txt`, our tests successfully proved that Axis 5 (Absolute Heat/Cold via Fe/Ti) maps to orthogonal superoperator spaces (Trace distance = 0). However, the engine threw a structural alert indicating that **Axis 4 (Te/Fi) is conflating with Axis 5**.
> 
> According to the `NLM_AXIS_0_AND_4_PREP.md` spec, Axis 5 is "Absolute Heat/Cold" (Fe = max state space, Ti = min state space), whereas Axis 4 is "Hotter/Colder Heat Directionality" (TeFi pushes heat internally to the core, FeTi pushes heat externally to cool the model).
> 
> **Your Task:** Derive the exact CPTP/Lindbladian mathematical distinction between an operator that controls *absolute heat volume* versus an operator that controls *the direction of heat flow*. How do we rewrite the Hamiltonian flow (Te) and Spectral Filter (Fi) matrices in Python so their Hilbert-Schmidt inner product with Fe/Ti is strictly zero, decoupling Axis 4 from Axis 5?"

---

## PROMPT 3: TYPE 1 vs TYPE 2 (Symmetry Breaking)
> "Look at `qit_topology_parity_sim.py_CODE_DIGEST.txt`. We successfully proved that both the **Type-1 Engine** (Deductive loop outer, Inductive loop inner) and the **Type-2 Engine** (Inductive loop outer, Deductive loop inner) achieve macroscopic block-entropy processing ($\Delta \Phi > 0$). They possess topological parity.
> 
> However, symmetry in physics must eventually break. Under what explicit physical or topological conditions (e.g., severe environmental noise, infinite dimension bounds, or extreme Axis 0 gradients) would the Type-1 chirality naturally break symmetry and dominate Type-2, or vice versa? Provide the mathematical condition."

---

## PROMPT 4: IGT FIELD THEORY & THE MOLOCH TRAP
> "One of our upcoming architectural phases involves 'N-Agent IGT Fields' and the 'Moloch Trap'. 
> In the 8-stage loop, operators are classified as WIN/LOSE or win/lose strokes (as defined in `type2_process_cycle_sim.py_CODE_DIGEST.txt`). 
> 
> If an N-agent manifold consists entirely of 'WIN-only' agents (refusing the LOSE strokes), thermodynamics dictates the system hits the Moloch Trap (thermal death / total state saturation). 
> 
> What is the exact mathematical proof (using Lindblad dissipation and Non-Equilibrium Steady State matrices) that the inclusion of the 'LOSE' stroke (which sacrifices local state parity) is the strictly necessary requirement to maintain a global NESS $\Delta \Phi > 0$ and escape the Moloch Trap?"

---

## PROMPT 5: GRAVEYARD NEGATIVE SIMS (The Classical Failure)
> "In our evidence ledger (inside `SIM_EVIDENCE_PACK.txt`), we explicitly run `neg_classical_probability_sim.py` which forces a KILL token `CLASSICAL_PROBABILITY_INSUFFICIENT`. 
> 
> This means if we collapse the engine's Density Matrix $\rho$ into a standard diagonal classical probability vector (destroying off-diagonal coherence), the Ratchet fails to generate negative entropy.
> 
> Explain the underlying physics of this failure. Is it specifically the loss of the Berry Phase (geometric winding in the Hamiltonian) that destroys the super-additivity? Write a short, rigorous proof explaining why standard classical thermodynamics (e.g., classical Szilard engines) mathematically cannot replicate this 8-stage topology."

---

## PROMPT 6: AXES 7-12 (The Hopf Torus Expansion)
> "The user's architecture specifies 12 total axes. Thus far, we have only mapped Axes 0-6 tightly into the density matrix / Lindblad math. 
> 
> If Axes 1-6 model a $T^6$ torus embedded in complex configuration space, how do we geometrically map Axes 7-12? Do they represent a higher-order Hopf fibration? Do Axes 7-12 mirror Axes 1-6 but acting on the *operator manifold* rather than the *state manifold* (i.e., meta-operators evaluating the Lindbladians themselves)? Design the geometric blueprint for mapping Axes 7-12 into the existing system."
