# Codex Ratchet: Deep Research Prompt Bank
**Version**: 3.0 (Ultimate Systems Edition)
**Target System**: OpenAI Deep Research / Gemini Advanced with GitHub Connector

> [!IMPORTANT]
> **MASTER CONNECTOR INSTRUCTION**
> When you copy-paste ANY of the prompts below to Deep Research, prepend this exact paragraph:
> ```text
> MASTER INSTRUCTION: You have direct write access to my GitHub repository via the GPT GitHub connector.
> When you finish researching and generate the formal YAML `problem_spec`, Python code, or Audit report, do NOT just output it in the chat.
> Instead, use your GitHub tool to create/modify files directly in the repository at the appropriate paths.
> Commit and push your changes with the message "Autopoietic Hub: [Action Completed]".
> ```

---
*(Sections A-D remain the same as above: Rival ToEs, Core Physics, Math Foundations, Cosmology)*
---

## Section E: Mass Analytics & System Improvement

**Prompt 16: "Mass Audit" Codebase Review & Optimization**
```text
Analyze the entire `system_v4/probes/` directory in my Codex-Ratchet repository. My system generates vast amounts of operator traces and tensor products across dimensions [4, 8, 16], which fundamentally bottlenecks Python due to NumPy GIL and allocation overhead.
Your task:
1. Perform a Mass Audit of all 30+ simulation files. Locate every loop that performs repetitive matrix multiplication, trace operations, or partial traces.
2. Formulate a systems-level optimization pass using Numba `@jit`, JAX, or PyTorch tensors, strictly targeting operations that scale $O(N^3)$ or worse.
3. Rewrite the worst-performing bottleneck functions.
4. Push your optimized code directly to a new branch via the GitHub connector and prepare a `MASS_AUDIT_REPORT.md` in `core_docs/`.
```

**Prompt 17: Leviathan Science Method + Holodeck System Integration**
```text
Research how to merge my two core architectures: The Leviathan framework (a continuous autonomous pipeline for ingesting real-world data and trading intents) and my Holodeck FEP system (a discrete QIT density matrix $S^3$ projection engine).
Your task:
1. Design an intake parser that converts high-frequency continuous data (like price feeds, robotic telemetry, or arXiv papers) into a finite, discrete "observable world" density matrix.
2. Structure the Holodeck FEP engine to minimize surprise (KL divergence) against this newly structured real-world density matrix.
3. Write the Python bridge script `leviathan_to_holodeck_bridge.py` and commit it.
```

## Section F: The "Negative Edge" (Finding Failure Modes)

**Prompt 18: Negative SIM Generation (Stress Testing the Ratchet)**
```text
Analyze the `autoresearch_sim_harness.py` and existing `problem_specs/`. The system currently has 13 automated checks, most of which are designed to PASS (positive witnesses for correct geometry). The most robust systems, however, are forged by negative tests (KILL conditions).
Your task:
1. Research the mathematical failure modes of bounded Lie algebras, non-commutative limits, and entropy loss.
2. Generate 5 brand new "Negative SIMs" (SIMs specifically designed to FAIL under pathological conditions, like enforcing perfect symmetry, or collapsing the Hilbert space dimension to 1).
3. Write the 5 new `_sim.py` files to prove the math, write their corresponding YAML `problem_specs` (with `target_status: KILL`), and push them directly to my repo.
```

**Prompt 19: The "Mass Sim" Auto-Generator**
```text
Research systematic procedural generation for computational math proofs. My Ratchet engine evaluates operators using the exact same CPTP/density matrix loops in every file.
Your task:
1. Build a "Mass Sim Generator" Python script (`mass_sim_generator.py`) that uses Jinja2 templates or AST manipulation.
2. It should take a list of conceptual goals (e.g., "prove string theory tension", "prove Hawking radiation") and automatically generate 50 distinct Python `_sim.py` scripts by applying randomized tensor contraction hypotheses.
3. Commit this code generation script to `system_v4/research/tools/` so my engine can begin generating its own code at scale.
```

**Prompt 20: Attractor Basin Visualization & Data Lake**
```text
Analyze how my system currently outputs `_results.json` files for every simulation in `system_v4/probes/a2_state/sim_results/`. These files hold raw tensor norms, entropy drops, and SS^3$ coordinates.
Your task:
1. Build a sweeping "Data Lake Indexer" that reads all 30+ JSON artifacts simultaneously.
2. Write a Python visualization dashboard (using Plotly or Dash) that renders the global "Attractor Basin". I need to see exactly where the 12 semantic axes concentrate all the random input states in 3D Hopf space.
3. Push the visualization code `global_basin_dashboard.py` directly to the repo.
```
