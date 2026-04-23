# NLM AXIS 0 & AXIS 4/5 PREP DIGEST
**Target Engine:** Notebook LM (NLM)
**Objective:** Formally outline the structural math boundaries for Axis 0 (Correlation Gradient) and the exact geometric distinction between Axis 4 (Heating/Cooling directionality) vs Axis 5 (Hot/Cold absolute scale).

---

## 1. AXIS 4 vs AXIS 5: The Heat Metaphors vs QIT Math

We must rigorously separate "Hotter vs Colder" (Axis 4) from "Hot vs Cold" (Axis 5).

### Axis 5: Absolute Heat (Fe / Ti)
*   **Fe (Hot / Absolute Dissipation):** Maximizes state space, exports entropy to the environment. Operates as an energy-selective Lindbladian sink.
*   **Ti (Cold / Absolute Constraint):** Minimizes state space, forces structural rigidity. Operates as an eigenbasis projection.
*   **Math Form:** The absolute volume of the density matrix $\rho$ tracing towards maximum mixedness $I/d$ (Hot) versus pure state bounds (Cold).

### Axis 4: Heat Directionality (Te / Fi) — "Hotter vs Colder"
*   **TeFi (Hotter / Internalizing Heat):** Preserves heat and possibilities IN THE CORE. It is "putting heat internally" via the Inductive Loop.
*   **FeTi (Colder / Externalizing Heat):** Pushes heat and possibilities OUT EXTERNALLY. It is "refining a low entropy cooled model" via the Deductive Loop.
*   **Math Form:** Axis 4 measures *chirality*—the direction that heat is moving. Type-1 loops and Type-2 loops simply invert this directionality. **NLM Task:** Map the exact commutator traces that dictate inward heat preservation (TeFi) versus outward heat export (FeTi).

---

## 2. AXIS 0: The Correlation & Mutual Entropy Gradient

**Current Problem:** We have successfully mapped Von Neumann entropy $S(\rho)$ as our baseline volume bound. However, Axis 0 dictates the relative *gradient* of order between two coupled domains (e.g. Engine A vs Engine B, or Agent vs Environment).

**NLM Request:** We need to explicitly formulate Axis 0 mathematically. 
*   **Mutual Entropy / Mutual Information $I(A;B)$:** How to measure the shared correlations across the topological phase boundary.
*   *It can be negative.* While classical mutual information is strictly non-negative, quantum conditional entropy (and certain correlation gradients across geometric phase jumps) *can* be negative.
*   **NLM Task:** Derive the explicit QIT expressions for the Axis 0 gradient. Should we use Quantum Relative Entropy $S(\rho || \sigma) = \text{Tr}(\rho \log \rho - \rho \log \sigma)$ as the basis for Axis 0? Or does the exact definition of "mutual entropy that can be negative" strictly point to Quantum Conditional Entropy $S(A|B) = S(AB) - S(B)$? Notebook LM must choose the mathematically optimal gradient structure.

---
**Summary for NLM:**
Read the bundled `.txt` logic for the SIM probes (where we rebuilt Fe as energy-selective Lindbladians and stripped the old classical Szilard naming). Generate the math needed to formally implement Axis 0 as a gradient in the Python codebase!
