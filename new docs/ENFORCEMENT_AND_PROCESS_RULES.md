# Enforcement and Process Rules

## Purpose
These rules are BINDING. They are not suggestions. Every sim, every agent, every piece of work must satisfy them. Violations mean the work is incomplete.

## Rule 1: PyTorch-native computation
All new computation uses PyTorch tensors. numpy is for loading data or converting formats, NOT for core computation. Density matrices = torch tensors. Operators = torch operations. Gradients = autograd.

## Rule 2: Graph + proof tools are REQUIRED
Every sim file must use at least 2 of: z3, sympy, clifford, TopoNetX, PyG/PyTorch. These are not optional verification — they ARE the computation substrate.

## Rule 3: No engine jargon in sims
Standard mathematical terms only. Z-dephasing, not Ti. X-rotation, not Fi. The Jungian labels are a Rosetta mapping applied AFTER the math is verified.

## Rule 4: Build from foundations
Each layer builds on verified lower layers. Do not skip. Do not assume. Test everything the constraints allow FIRST, then show what the next constraint kills.

## Rule 5: Depth over breadth
Fewer sims, much deeper each. Every lego needs: multiple test states, theoretical comparison, negative/failure case, cross-validation, boundary/edge case. Not "compute one value and check."

## Rule 6: Negative testing is mandatory
Every positive test has a corresponding negative. Not "does it work" but "when does it break, and why."

## Rule 7: Constraint proofs, not classical proofs
Use z3 UNSAT (this is impossible) not just SAT (this works). Quantum math is constraint-based: what's FORBIDDEN is more fundamental than what's TRUE.

## Rule 8: No Platonic/causal language
"survived" not "created." "coupled with" not "causes." "constraint on distinguishability" not "fundamental reality." Nominalist throughout.

## Rule 9: The computational graph IS the ratchet
Forward = possibilities. Backward = constraints. Graph topology = constraint manifold. Gradient = load-bearing. This is not metaphor — it is architecture.

## Rule 10: Classical legos are baselines, not answers
The 84 numpy legos show what works classically. The constraint cascade shows what FAILS classically. The quantum version uses PyTorch+tools. The numpy versions are the BEFORE picture.

## Rule 11: Presume less, test more
Explore what the math allows, don't just test what the engine proposes. The constraint manifold ordering is DISCOVERED by sims, not assumed by design.

## Rule 12: Anti-salience
The boring foundational work matters most. LLMs skip it (salience bias). Push back on exciting leaps. Stay on the current layer until it's complete.

## Rule 13: Multiple narratives
Hold several divergent explanations simultaneously. Where they agree despite diverging = signal. Don't pick one story.

## Enforcement Mechanism
- SIM_TEMPLATE.py: every new sim starts from this template
- regenerate_sim_manifest.py: flags files missing tool imports as INCOMPLETE
- Pre-commit validation: checks Rules 1-3 automatically
- Hermes audit: reviews for Rules 4-13
