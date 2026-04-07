# Enforcement and Process Rules

## Purpose
These rules are BINDING. They are not suggestions. Every sim, every agent, every piece of work must satisfy them. Violations mean the work is incomplete.

## Current State (2026-04-07)
- 84 numpy legos built = CLASSICAL BASELINES (the BEFORE picture)
- 11 negative batteries (107 failure modes)
- Constraint cascade L0-L7 mapped: 53→66→48→43→28 irreducible
- 9 independent observables discovered
- 7+ engine variants (core through Cl(6) unified)
- Axes: 6✅ 5✅ 3✅ 4✅ (1⬜ 2⬜)
- PyTorch pivot identified: computational graph = ratchet architecture
- Axis 0 insight: ∇I_c on shell topology via autograd

---

## Rule 1: PyTorch-native computation
All new computation uses PyTorch tensors. numpy is for loading data or converting formats, NOT for core computation. Density matrices = torch tensors. Operators = torch operations. Gradients = autograd.

**Why:** numpy arrays ARE Cartesian grids — they import Platonic/Cartesian ontology. PyTorch computational graphs are RELATIONAL (edges, not coordinates). Quantum math is relational. The substrate must match the ontology.

## Rule 2: TRY ALL tools, use what's relevant
Every sim must ATTEMPT to use each tool: z3, sympy, clifford, TopoNetX, PyG/PyTorch. Document which tools were tried and why each was used or not relevant. The default is ALL tools. The exception must be justified.

- **z3**: constraint proofs (UNSAT = impossible = quantum). Try for every structural claim.
- **sympy**: symbolic algebra. Try for every formula derivation.
- **clifford Cl(3)/Cl(6)**: geometric algebra. Try for every geometric operation.
- **TopoNetX**: cell complex topology. Try for every topological structure.
- **PyG/PyTorch**: differentiable computation + message passing. Try for ALL core computation.

**Why:** Each tool carries a different ontological commitment. z3 does constraint logic (non-classical). Clifford does geometric product (non-commutative). TopoNetX does topology (relational). PyG does graph computation (non-Cartesian). Using them forces non-classical thinking.

## Rule 3: No engine jargon in sims
Standard mathematical terms only. Z-dephasing, not Ti. X-rotation, not Fi. The Jungian labels are a Rosetta mapping applied AFTER the math is verified.

**Why:** Jungian labels carry psychological ontology that contaminates the math. The math should stand alone. Labels are a mapping layer, not a computation layer.

## Rule 4: Build from foundations
Each layer builds on verified lower layers. Do not skip. Do not assume. Test everything the constraints allow FIRST, then show what the next constraint kills.

**Why:** The constraint manifold ordering is DISCOVERED by sims, not assumed. The user has repeatedly corrected: don't skip to exciting stuff, stay on the current layer until it's complete.

## Rule 5: Depth over breadth
Fewer sims, much deeper each. Every lego needs:
- Multiple test states (not just |0⟩ — use 10+ diverse states)
- Theoretical value comparison (not just "does it run")
- At least one negative/failure case per item
- Cross-validation against a different computation method
- Boundary/edge case testing (what happens at extremes)
- Numerical precision analysis (at what tolerance does it break)

**Why:** 84 shallow legos is less valuable than 10 deep ones. The user has stressed: deep testing, not shallow verification.

## Rule 6: Negative testing is mandatory
Every positive test has a corresponding negative. Not "does it work" but "when does it break, and why."

**Why:** The system is biased 84:11 positive:negative. Selection pressure and failure modes are the weak point identified by Hermes audit.

## Rule 7: Constraint proofs, not classical proofs
Use z3 UNSAT (this is impossible) not just SAT (this works). Quantum math is constraint-based: what's FORBIDDEN is more fundamental than what's TRUE.

**Mathematical basis:** In quantum mechanics, the fundamental results are no-go theorems (no-cloning, no-broadcasting, uncertainty relations, monogamy). These are IMPOSSIBILITY proofs. z3 UNSAT is the natural encoding.

## Rule 8: No Platonic/causal language
"survived" not "created." "coupled with" not "causes." "constraint on distinguishability" not "fundamental reality." Nominalist throughout.

**Why:** The system is nominalist (forms real but material, statistics IS causality, subject=object). Language carries rationalist/Platonic bias from training. Every word must be checked.

## Rule 9: The computational graph IS the ratchet
- Forward pass = exploring the allowed math space (possibilities)
- Backward pass = constraints selecting what survives (selection)
- Graph topology = constraint manifold (what's computable)
- Gradient = what's load-bearing (signal)
- Zero gradient = what's redundant (noise)
- This is not metaphor — it is the architecture.

**Mathematical basis:** Autograd traces relationships between operations (relational, not Cartesian). Backprop flows information backward through constraints (non-causal, constraint-based). The graph topology determines what's computable (topological, not coordinate-based).

## Rule 10: Classical legos are baselines, not answers
The 84 numpy legos show what works classically. The constraint cascade shows what FAILS classically. The quantum version uses PyTorch+tools. The numpy versions are the BEFORE picture.

**Why:** The user identified this: we built classical legos and called them done. They're not done — they're the starting point. The constraint layers show which classical approaches fail and need quantum replacement.

## Rule 11: Presume less, test more
Explore what the math allows, don't just test what the engine proposes. The constraint manifold ordering is DISCOVERED by sims, not assumed by design. Test ALL options — all rotation axes, all dephasing bases, all channel types, all entropies — not just the ones the engine uses.

## Rule 12: Anti-salience
The boring foundational work matters most. LLMs skip it (salience bias), smooth contradictions (compression bias), and agree to please (RLHF bias). Push back. Stay on the current layer. Don't leap ahead.

## Rule 13: Multiple narratives
Hold several divergent explanations simultaneously. Where they agree despite diverging = signal. Don't pick one story. Divergence IS the information.

---

## Enforcement Mechanisms

### Automated
- Every sim file must document which tools were tried and which were used
- regenerate_sim_manifest.py classifies files by tool depth
- New sims without PyTorch = classified as "classical_baseline" not "canonical"

### Process
- Each sim starts from SIM_TEMPLATE.py (to be built)
- Template includes required imports, validation structure, negative test section
- Agent prompts include these rules verbatim
- Hermes audits for Rules 4-13

### Cultural
- Speed is not the goal. Depth is.
- "ALL PASS" is suspicious. Failure modes are expected.
- If it was easy, you probably skipped something.
