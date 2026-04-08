# Enforcement and Process Rules

## Document Status
| Field | Value |
|-------|-------|
| **last_verified** | 2026-04-08 |
| **current_reviewed_policy** | SIM_TEMPLATE.py structure, tool manifest requirement, two-lane policy (no automated checker, no promotion gate — compliance is by discipline and review, not enforcement machinery) |
| **discovered** | L0-L7 constraint cascade, 28 irreducible families, 9 independent observables, simultaneous shell geometry |
| **planned** | Manifest checker CI, canonical promotion gate, Lean 4 / TLAPS proof layer, PyTorch migration of all 28 families |

## Purpose
These rules describe the target standard for new work. They are not yet automatically enforced — no CI checker, no promotion gate, no automated manifest validator exists. Until that machinery is built, compliance depends on discipline and review.

## Scope
This document governs active simulation and build work. It does not replace source-of-truth math; it constrains how we produce, validate, and classify work.

---

## Actual Plan Guardrail

This is not new information. It is the already-corrected operating plan that must be preserved across agents and docs:

1. start from the two root constraints
2. build the admissible carrier and probe math first
3. build foundational legos as independent pure-math sims
4. preserve the layered geometric-constraint-manifold view:
   - more constrained layers can be nested on the same state space
   - multiple active layers can operate at once
   - the exact final layer order is not yet closed
5. do not force canon on the current candidate order
6. only after the basic legos are real:
   - test how layers stack
   - test which orders and subsets can actually nest
   - test which structures survive composition

Concrete examples that must stay preserved:
- density matrices are near-first admissible objects under the root constraints
- left/right Weyl spinors must run on nested Hopf tori
- flux is an open derived family and must be built from its dependency chain, not assumed as primitive
- Pauli / Bloch / channel / differential machinery should be simmed as independent legos before compound claims

If a sim batch violates that order, it is off-plan even if it produces passing outputs.

---

## CURRENT STATE (what exists now)
- numpy legos = classical baselines (verified, committed). Count: see `system_v4/probes/` manifest.
- Negative battery concepts with multiple battery files and 100+ failure modes. Count: see [BATTERY_INDEX.md](BATTERY_INDEX.md).
- L0-L7 constraint cascade mapped. Counts: see PYTORCH_RATCHET_BUILD_PLAN.md Phase 2.
- Irreducible families identified with independent observables. Counts: see [MIGRATION_REGISTRY.md](MIGRATION_REGISTRY.md).
- Tool usage across sim files: z3, sympy, clifford, toponetx, torch all represented. Counts: see [TOOL_MANIFEST_AUDIT.md](TOOL_MANIFEST_AUDIT.md).
- The stack is broader than the older tool docs implied: cvc5, geomstats, e3nn, rustworkx, XGI, GUDHI, PyG are all now represented in sim-like files, but not yet equally load-bearing.
- PyTorch is NOT yet the primary substrate. numpy dominates.
- SIM_TEMPLATE.py now exists (system_v4/probes/SIM_TEMPLATE.py)
- Tool manifest is defined in the template but not yet present in legacy result JSONs
- Enforcement is ASPIRATIONAL until all new sims use the template and a checker validates canonical claims
- 7+ engine variants (core through Cl(6) unified)
- Axes: 6, 5, 3, 4 verified. Axes 1, 2 open. Axis 0 unsolved.
- The bridge / `Phi0` seam is now separated much better than before (`Xi`, `rho_AB`, cut kernels, `Phi0` bakeoffs), but it is still mostly numpy-first and underintegrated with proof/graph tooling.
- The basic plan is still only partially done: foundations and bridge separation are much better covered now, but the deep graph/proof integration pass has still not actually been completed.

## TARGET BUILD REGIME (what we are building toward)
All 13 rules below describe the target regime. They are the standard new work should meet. Legacy work is not retroactively invalid, but it is not promoted to canonical status without meeting these rules. No automated enforcement machinery exists yet — these are design constraints, not runtime checks.

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

## Rule 2: Try all tools; make at least one relevant tool load-bearing
Every canonical sim must attempt to use each relevant tool from the full stack. Document which tools were tried and why each was used or not relevant. Exceptions must be justified explicitly in the sim output. See TOOLING_STATUS.md for versions and install status.

This rule is stronger than a manifest declaration:
- a canonical sim must not merely import or declare tools
- at least one nontrivial tool outside the numeric baseline must be load-bearing for the actual claim
- the load-bearing tool should match the claim:
  - structural impossibility / minimality -> `z3` / `cvc5`
  - symbolic identity / derivation -> `sympy`
  - geometric product / spinor transport -> `clifford`
  - shell geometry / geodesics / Fréchet structure -> `geomstats`
  - equivariant computation -> `e3nn`
  - DAG / dependency / routing / packet-family structure -> `rustworkx`
  - hypergraph / multi-way structure -> `XGI`
  - cell-complex topology -> `TopoNetX`
  - filtrations / persistence -> `GUDHI`
  - graph-native dynamics -> `PyG`

Required tool-role contract:

**Proof layer:**
- **z3**: constraint proofs (UNSAT = impossible = quantum). Try for every structural claim.
- **cvc5**: cross-check z3 UNSAT claims; SyGuS synthesis for minimal generators and admissible-operator search.

**Symbolic layer:**
- **sympy**: symbolic algebra. Try for every formula derivation.

**Geometry layer:**
- **clifford Cl(3)/Cl(6)**: geometric algebra. Try for every geometric operation.
- **geomstats**: Riemannian manifold computation. Try for every shell metric, geodesic, or curvature calculation.
- **e3nn**: E(3)-equivariant layers. Try when symmetry-native PyTorch computation is relevant (O(3)/SU(2) operations).

**Graph layer:**
- **rustworkx**: fast graph algorithms, DAGs, dependency/routing/causal-order workloads. Try when graph performance matters or when working with directed acyclic structure.
- **XGI**: hypergraphs and simplicial complexes. Try when multi-way interactions (not just pairwise) are structurally relevant — shell/face/operator constraints, multipartite state relations.

**Topology layer:**
- **TopoNetX**: cell-complex topology. Try for every higher-order topological structure.
- **GUDHI**: persistent homology, filtrations, TDA. Try for every topological invariant computation at scale.

**Computation layer:**
- **PyG/PyTorch**: differentiable computation + message passing. Try for all core computation.

**Planned (not yet installed):**
- **Lean 4**: interactive theorem prover for math-side formalization above SMT level.
- **TLAPS**: temporal logic model checking for ratchet safety/liveness properties.

**Why:** Each tool carries a different ontological commitment. z3/cvc5 do constraint logic (non-classical). Clifford does geometric product (non-commutative). TopoNetX/GUDHI do topology (relational). geomstats does Riemannian geometry (intrinsic, not coordinate-first). e3nn does equivariant computation (symmetry-native). PyG does graph computation (non-Cartesian). Using them forces non-classical thinking.

## Rule 3: No engine jargon in sims
Standard mathematical terms only. Z-dephasing, not Ti. X-rotation, not Fi. The Jungian labels are a Rosetta mapping applied after the math is verified.

**Why:** Jungian labels carry psychological ontology that contaminates the math. The math should stand alone. Labels are a mapping layer, not a computation layer.

## Rule 4: Build from foundations (simultaneous shells, not sequential ladder)
Each shell adds constraints to the same state space. All active shells are present simultaneously — higher shells do not replace lower ones, they restrict further. Do not skip a shell. Do not assume. Test everything the constraints allow at the current level first, then show what the next constraint shell kills.

**Why:** The constraint manifold is nested simultaneous shells (S0 ⊃ S1 ⊃ S2 ⊃ ...), not a sequential pipeline. The ordering is discovered by sims, not assumed. Stay on the current shell until it is complete.

### Current audit note

The repo has improved here, but the full plan still has not been completed end-to-end.
The live gap is no longer just missing legos. It is missing integration:
- independent foundation legos exist
- bridge legos exist
- `rho_AB` and cut kernels now exist as separate object families
- but the proof/graph integration pass over that seam still lags

### Rule 4a: Candidate layer order is not canon

The geometric constraint manifold likely has a real nested order,
but the exact layer list and final order are still open.

So:
- preserve likely candidates and likely orders in docs
- sim every layer independently where possible
- then sim admissible stackings / nestings of those layers
- do not rewrite a likely order into canon before the stack tests exist

This applies especially to:
- nested Hopf torus layers
- Weyl left/right layer
- differential / flux candidate layer
- bridge / cut-state layer
- later entropy / `Phi0` layers

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

### Rule 11a: Sim the stack, not just the objects

After the independent legos exist, there is a second required program:
- which layers can coexist
- which layers must precede others
- which layers collapse when nested
- which candidate orders are impossible

That means:
- independent lego sims are necessary
- stack / nesting sims are also necessary
- neither replaces the other

## Rule 12: Anti-salience
The boring foundational work matters most. LLMs skip it (salience bias), smooth contradictions (compression bias), and agree to please (RLHF bias). Push back. Stay on the current layer. Do not leap ahead.

## Rule 13: Multiple narratives
Hold several divergent explanations simultaneously. Where they agree despite diverging = signal. Do not pick one story. Divergence is the information.

---

## Enforcement Mechanisms

### Automated (planned — not yet implemented)
- Every canonical sim must include a tool-use manifest: tried / used / omitted / why
- Sims are classified by depth: classical_baseline, canonical, supporting, audit
- classical_baseline remains valid and preserved, but is not promoted to canonical
- A manifest checker should fail work that claims canonical status without tool depth
- **Status:** No automated checker exists yet. This is a design requirement, not a deployed gate.

### Process (partially implemented)
- Each canonical sim starts from SIM_TEMPLATE.py (system_v4/probes/SIM_TEMPLATE.py) — **exists**
- Template includes required imports, validation structure, negative-test section, tool manifest, and `tool_integration_depth` — **exists**
- Agent prompts include these rules verbatim — **partially implemented**
- Hermes audits Rules 4-13 — **not yet automated**

### Cultural
- Speed is not the goal. Depth is.
- "ALL PASS" is suspicious. Failure modes are expected.
- If it was easy, you probably skipped something.
- A sim that omits a relevant tool must say why, in the sim itself.
- A sim that declares many tools but uses none of them load-bearing has not actually done the plan.
