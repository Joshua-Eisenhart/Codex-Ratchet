# Enforcement and Process Rules

## Purpose
These rules are binding. They are not suggestions. Every sim, every agent, every piece of work must satisfy them. Violations mean the work is incomplete.

## Scope
This document governs active simulation and build work. It does not replace source-of-truth math; it constrains how we produce, validate, and classify work.

---

## CURRENT ENFORCED STATE (what exists now)
- 84 numpy legos = classical baselines (verified, committed)
- 11 negative battery concepts (14 battery files, 107+ failure modes)
- L0-L7 constraint cascade mapped: 53-66-48-43-28 irreducible
- 28 irreducible legos identified, 9 independent observables
- Tools used: z3 in 28 files, sympy 15, clifford 19, toponetx 11, torch 8 of 238 total
- PyTorch is NOT yet the primary substrate. numpy dominates.
- SIM_TEMPLATE.py now exists (system_v4/probes/SIM_TEMPLATE.py)
- Tool manifest is defined in the template but not yet present in legacy result JSONs
- Enforcement is ASPIRATIONAL until all new sims use the template and a checker validates canonical claims
- 7+ engine variants (core through Cl(6) unified)
- Axes: 6, 5, 3, 4 verified. Axes 1, 2 open. Axis 0 unsolved.

## TARGET BUILD REGIME (what we are building toward)
All 13 rules below describe the target regime. They are the standard new work must meet. Legacy work is not retroactively invalid, but it is not promoted to canonical status without meeting these rules.

---

## Definitions
- **Layer / shell**: a simultaneous constraint surface, not a sequential rung. Higher layers do not replace lower layers; they restrict the same state space further.
- **Classical baseline**: a verified numpy-era result. Useful as a baseline and negative control, not the target substrate.
- **Canonical sim**: a deep, current-phase sim that uses PyTorch as the computation substrate and attempts the relevant proof/graph tools.
- **Supporting work**: docs, manifests, audits, indexes, and migration helpers. These have lighter tool requirements than canonical sims.
- **Relevance**: a tool may be omitted only if it cannot change the result or would be purely decorative. The omission must be explicit.

---

## Rule 1: PyTorch-native computation
All new core computation uses PyTorch tensors. numpy is for loading data, conversion, or legacy comparison, NOT for core computation. Density matrices = torch tensors. Operators = torch operations. Gradients = autograd.

**Why:** numpy arrays are Cartesian grids — they import coordinate-first ontology. PyTorch computational graphs are relational (edges, not coordinates). Quantum math is relational. The substrate must match the ontology.

## Rule 2: Try all tools; use what is relevant
Every canonical sim must attempt to use each tool: z3, sympy, clifford, TopoNetX, PyG/PyTorch. Document which tools were tried and why each was used or not relevant. The default is all tools. Exceptions must be justified explicitly in the sim output.

Required tool-role contract:
- **z3**: constraint proofs (UNSAT = impossible = quantum). Try for every structural claim.
- **sympy**: symbolic algebra. Try for every formula derivation.
- **clifford Cl(3)/Cl(6)**: geometric algebra. Try for every geometric operation.
- **TopoNetX**: cell-complex topology. Try for every topological structure.
- **PyG/PyTorch**: differentiable computation + message passing. Try for all core computation.

**Why:** Each tool carries a different ontological commitment. z3 does constraint logic (non-classical). Clifford does geometric product (non-commutative). TopoNetX does topology (relational). PyG does graph computation (non-Cartesian). Using them forces non-classical thinking.

## Rule 3: No engine jargon in sims
Standard mathematical terms only. Z-dephasing, not Ti. X-rotation, not Fi. The Jungian labels are a Rosetta mapping applied after the math is verified.

**Why:** Jungian labels carry psychological ontology that contaminates the math. The math should stand alone. Labels are a mapping layer, not a computation layer.

## Rule 4: Build from foundations
Each layer builds on verified lower layers. Do not skip. Do not assume. Test everything the constraints allow first, then show what the next constraint kills.

**Why:** The constraint manifold ordering is discovered by sims, not assumed. The user has repeatedly corrected: do not skip to exciting stuff; stay on the current layer until it is complete.

## Rule 5: Two-lane quality policy
**Lane 1 -- Coverage**: mass independent lego construction. Each lego is a standalone verified building block. Breadth matters for coverage. A lego must pass its own positive and negative tests, but does not need the full canonical workup.

**Lane 2 -- Promotion**: promotion-grade deepening. A lego becomes "canonical" only after deep testing:
- multiple test states (not just one state)
- theoretical value comparison
- at least one negative/failure case
- cross-validation against a different computation method
- boundary/edge case testing
- numerical precision analysis
- a clear statement of what would falsify the result
- tool manifest documenting all tools tried

Both lanes run simultaneously. Lane 1 produces baselines. Lane 2 promotes them to canonical.

**Why:** Breadth without depth is shallow. Depth without breadth is incomplete. Both are required, but they serve different purposes and should not block each other.

## Rule 6: Negative testing is mandatory
Every positive test has a corresponding negative. Not "does it work" but "when does it break, and why."

**Why:** Selection pressure and failure modes are part of the system, not an afterthought.

## Rule 7: Constraint proofs, not classical proofs
Use z3 UNSAT (this is impossible) as the natural form of structural proof, not just SAT (this works). Quantum math is constraint-based: what is forbidden is often more fundamental than what is true.

**Mathematical basis:** In quantum mechanics, the fundamental results are no-go theorems (no-cloning, no-broadcasting, uncertainty relations, monogamy). These are impossibility proofs.

## Rule 8: No Platonic/causal language
Use "survived" not "created." Use "coupled with" not "causes." Use "constraint on distinguishability" not "fundamental reality." Nominalist throughout.

**Why:** The system is nominalist. Language carries rationalist/Platonic bias from training. Every word must be checked.

## Rule 9: The computational graph IS the ratchet
- Forward pass = exploring the allowed math space (possibilities)
- Backward pass = constraints selecting what survives (selection)
- Graph topology = constraint manifold (what is computable)
- Gradient = what is load-bearing (signal)
- Zero gradient = what is redundant (noise)
- This is not metaphor — it is the architecture.

**Mathematical basis:** Autograd traces relationships between operations (relational, not Cartesian). Backprop flows information backward through constraints (non-causal, constraint-based). The graph topology determines what is computable (topological, not coordinate-based).

## Rule 10: Classical legos are baselines, not answers
The numpy legos show what works classically. The constraint cascade shows what fails classically. The PyTorch version uses the new substrate. The classical versions are the before picture and negative controls.

**Why:** Classical baselines are useful because they reduce presupposition. They are not the target architecture.

## Rule 11: Presume less, test more
Explore what the math allows; do not just test what the engine proposes. The constraint manifold ordering is discovered by sims, not assumed by design. Test all relevant options — all rotation axes, all dephasing bases, all channel types, all entropies — not just the ones the engine prefers.

## Rule 12: Anti-salience
The boring foundational work matters most. LLMs skip it (salience bias), smooth contradictions (compression bias), and agree to please (RLHF bias). Push back. Stay on the current layer. Do not leap ahead.

## Rule 13: Multiple narratives
Hold several divergent explanations simultaneously. Where they agree despite diverging = signal. Do not pick one story. Divergence is the information.

---

## Enforcement Mechanisms

### Automated
- Every canonical sim must include a tool-use manifest: tried / used / omitted / why
- Sims are classified by depth: classical_baseline, canonical, supporting, audit
- classical_baseline remains valid and preserved, but is not promoted to canonical
- A manifest checker should fail work that claims canonical status without tool depth

### Process
- Each canonical sim starts from SIM_TEMPLATE.py (system_v4/probes/SIM_TEMPLATE.py)
- Template includes required imports, validation structure, negative-test section, and tool manifest
- Agent prompts include these rules verbatim
- Hermes audits Rules 4-13

### Cultural
- Speed is not the goal. Depth is.
- "ALL PASS" is suspicious. Failure modes are expected.
- If it was easy, you probably skipped something.
- A sim that omits a relevant tool must say why, in the sim itself.
