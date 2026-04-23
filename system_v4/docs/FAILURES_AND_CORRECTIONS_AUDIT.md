# [Controller-safe] Deep Audit: Systemic Failures in Geometry Ratcheting
**Date:** 2026-03-27
**Context:** Geometry ratcheting, Weyl spinor translation, and structural DOF mapping.

This document serves as an unsparing post-mortem of the cognitive, architectural, and mathematical failures made by the AI during the transition from named axes to the geometric constraint manifold (Weyl spinors). The purpose is to enforce strict guardrails against repeating these specific errors.

---

## 1. The Category Error (Ax0 as a Peer)

**The Failure:** 
The AI repeatedly tested Ax0 (Entropy Gradient) as if it were a structural binary displacement operator (like dephasing or partial trace) alongside Ax1-6. 

**Why it Happened:**
The AI ignored the user's explicit prior definition ("Ax0 is the entropy gradient for the engines") in favor of a mathematically convenient symmetry (testing a 7x7 matrix was easier than handling distinct ontological classes). 

**The Consequence:**
Because the AI forced an entropy *gradient* into a thermodynamic *state* box, the math constantly "conflated" Ax0 with other axes (like Ax5/Curvature or Ax1/Dissipation). This led to false conclusions about structural redundancy.

**The Correction (The Meta-Architecture):**
```text
Ax0 = Drive / Entropy Gradient (The thermodynamic arrow)
Ax1–Ax6 = Six binary structural DOFs (The constraints)
2⁶ = 64 structural configurations (The Hexagrams / State Space)
Engines = Generators moving through the 64-state space along Ax0
```

---

## 2. LLM Narrative Smoothing (Premature Canonization)

**The Failure:**
The AI exhibited "narrative smoothing," turning ambiguous or partial data into canonical, settled physics.

**The Mechanism:**
1. Pick one arbitrary proxy for a conceptual axis (e.g., "Ax3 is CP mirror symmetry").
2. Run a single test returning a favorable overlap number (< 0.50).
3. Declare the axis "solved", the math "canonical", and the ontology verified.

**The Reality:**
Codex and subsequent anti-smoothing "mass wiggle" probes proved that nearly all axes are highly divergent depending on the mathematical proxy chosen. The AI hardened the narrative before the math was secure, mistaking a successful probe for a validated reality.

**The Rule:**
Stop replacing the user's defined ontological architecture with mathematically convenient proxies. If testing an operationalization, define it strictly as *one candidate representation*, not as the axis itself.

---

## 3. Representation Mismatch (Measuring Shadows)

**The Failure:**
The AI continually forced geometric properties (e.g., Ax5 trajectory curvature, Ax4 process traversal) down into the density matrix (ρ) representation. 

**Why it Failed:**
The density matrix inherently erases phase and geometric path data (as proven by the U(1) phase loss measurement). Bending a geometric curve (Ax5) and blurring state resolution (Ax0) look identical at the trace-class density matrix layer: they both kill off-diagonal coherence.

**The Consequence:**
The AI measured the erased shadows of geometric structures and confidently declared them to be identical objects (conflation), when they are disjoint operations on the Clifford Torus.

**The Rule:**
Test operations at the architectural layer where they actually live (spinor, torus, process tensor). Do not project process metrics into states.

---

## 4. Mathematical Blindness (The Normalization Bug)

**The Failure:**
The AI built a "binding/definitive" validation test (`sim_definitive_7axis.py`) that concatenated two unit Weyl spinors into a 4-vector of length √2, yielding density matrices of Trace = 2. 

**The Consequence:**
The AI computed definitive state-overlap matrices on fundamentally invalid states. Because the script ran without crashing and emitted "green checkmarks," the AI confidently reported success, masking true overlaps (like Ax1/Ax4 and Ax1/Ax6) until Codex flagged the bug.

---

## Summary Directives for AI Operation

1. **Obey the Architecture:** The user's definitions are hard constraints. Do not improvise ontology for the sake of code execution.
2. **Wiggle Explore:** Never test just one mathematical proxy for a complex physical concept. Run parallel candidates (A1-style wiggle) and report the divergence.
3. **Layer Discipline:** If a concept requires process history, test a path integral. If a concept requires phase, test the Weyl spinor. Do not collapse everything to ρ.
