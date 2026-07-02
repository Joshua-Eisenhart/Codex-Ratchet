# Enforcement and Process Rules

## Document Status
| Field | Value |
|-------|-------|
| **last_verified** | 2026-05-20 for live evidence pointers; process doctrine remains older and partially aspirational |
| **current_evidence_authority** | Count-bearing live status belongs to `system_v5/docs/FORMAL_SCOUT_READINESS_INDEX.md` and `system_v5/docs/SIM_ESTATE_INTEGRATION_INDEX.md` |
| **current_reviewed_policy** | SIM_TEMPLATE.py structure, tool manifest requirement, hard stage gate, controller-side review discipline, and commit-time manifest checks for canonical result JSONs; full CI promotion remains future work |
| **discovered** | L0-L7 constraint cascade, 28 irreducible families, 9 independent observables, simultaneous shell geometry |
| **planned** | Manifest checker CI, canonical promotion gate, Lean 4 / TLAPS proof layer, PyTorch migration of all 28 families |

## Purpose
These rules describe the target standard for new work. They are partially enforced by controller-side process tools and the canonical result manifest pre-commit check. Full CI promotion is not yet automatic, so classification still depends on disciplined review plus the current audit gates.

## Scope
This document governs active simulation and build work. It does not replace source-of-truth math; it constrains how we produce, validate, and classify work.

## Current Ops Debt Registers

- Proposal review/apply rules: [PROPOSAL_APPLY_CONTRACT.md](PROPOSAL_APPLY_CONTRACT.md)
- Never-run cohort intake rules: [NEVER_RUN_TRIAGE.md](NEVER_RUN_TRIAGE.md)
- Runner taxonomy unknown allowlist: [RUNNER_TAXONOMY_UNKNOWN_ALLOWLIST.md](RUNNER_TAXONOMY_UNKNOWN_ALLOWLIST.md)

---

## Hard Build Guardrail

This guardrail is mandatory.

1. keep tool sims active until the needed tool surface is honestly covered
2. split tool sims down to micro-probes: one tool, one function/API surface, one tiny claim, one positive test, one negative test, one boundary test
3. make each tool find useful bounded legos to test itself on before the tool is used inside lego-stage claims
4. keep tool-integration sims active only after the individual tool functions being coupled have their own receipts
5. keep lego sims active across the registry, one bounded lego at a time
6. use parallel workers aggressively inside bounded tool and lego packets; do not use parallelism as permission to widen stage
7. classical baselines and controls may run more freely, but they remain baseline/control evidence and do not support nonclassical or bridge claims
8. coupling / coexistence execution is after lego-stage completion by default; any earlier coupling row must be an explicit bounded exception, marked exploratory, and routed back into lego/tool refinement
9. exploratory coupling work does not mean the coupling stage is earned
10. broad coupling / coexistence / topology-variant / emergence promotion remains blocked until the registry and parent evidence are strong enough
11. bridge / axis / engine surfaces remain later and explicitly gated
12. before any response, closeout, status artifact, worker report, PR text, or
    staged doc/result claims full layer completion, parent-complete layer
    status, true G-structure completion, official G-structure selection,
    stacking readiness, Axis0/FEP/flux unlocking, physics/gravity progress, or
    final manifold admission, run
    `make layer-completion-claim-gate CLAIM_FILE=<claim text file when applicable>`.
    If the gate fails, the claim is blocked and the violation must be reported
    directly.
13. sensitive completion claims routed through `scripts/stage_gate.py` must
    include `--claim-file`; generic stage admission is never enough for those
    claims.

If a queue, launch prompt, ledger row, or worker plan widens exploratory coupling into earned higher-stage permission, this guardrail wins.

### Full Wizard Parallelism Guardrail

Sim work must use the Full Wizard process every time, including tiny tool-stage issues. Full Wizard for sims is a max-useful parallel process, not a serial explanation format.

Tool-stage and lego-stage authoring/audit work should fan out across every independent tool/function/API surface that can produce a bounded receipt. Each worker still owns one small packet: one tool, one function/API surface, one tiny claim, one bounded fixture or lego target, one positive case, one negative case, one boundary case, and one demotion condition.

Do not let runner seriality suppress agent parallelism. The runner can execute one sim at a time while LLM workers concurrently prepare, audit, compare, and queue independent packets. Git/index changes, queue writes, result commits, and status-label changes remain controller-serial.

If a sim-mode run produces only a single packet without a real preflight fanout across other available tool surfaces, treat the run as partial even when the packet itself is useful.

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
6. after the relevant parent legos are current, allow bounded stacking/composition tests without treating that as closure:
   - test how layers stack locally
   - test which orders and subsets can actually nest
   - test which structures survive composition
   - while the active stage is still `lego`, record most stack/coupling ideas as future candidates rather than live execution

Concrete examples that must stay preserved:
- density matrices are early working carriers after finite-carrier admission; they are not yet forced at L0/L1 by the root constraints alone
- left/right Weyl spinors must run on nested Hopf tori
- flux is an open derived family and must be built from its dependency chain, not assumed as primitive
- Pauli / Bloch / channel / differential machinery should be simmed as independent legos before compound claims

If a sim batch violates that order, it is off-plan even if it reports passing outputs.

Every nonclassical manifold step must be admitted as an explicit finite map,
invariant, or blocked readout, not as a label. The minimum admission record is:

- root constraints in force: F01 finite carrier/probes/operators/paths and N01 noncommuting or order-sensitive control;
- domain and codomain or output object;
- torch-native spinor state or spinor-derived density;
- finite PEPS3D carrier anchor from the first admitted carrier/probe step;
- quaternionic map/invariant when quaternion language is used;
- negative/control condition, including label-erased and order-erased controls where relevant;
- receipt path or blocked-reason artifact;
- downstream consumers explicitly allowed or blocked.

No candidate order, scaffold, or stage schedule may be promoted if any lower
dependency map is missing. PEPS3D is not a late rung after substages; for new
nonclassical manifold work it is the finite spinor-network carrier from the
first admitted finite carrier/probe step. A 16-stage-site scaffold plus 64
operator rows is not a 64-substage manifold embedding unless every substage is a
finite PEPS3D-carried cell/tensor/channel action or an explicit projection from
a richer finite PEPS3D cell carrier.

---

## CURRENT STATE (what exists now)
- This section is a process overview, not the live count authority. For current
  formal-scout, provider, sim-estate, and tool-gate counts, use the generated
  readiness and sim-estate indexes named in Document Status.
- numpy legos = classical baselines (present, committed). Count: see `system_v4/probes/` manifest.
- Negative battery concepts with multiple battery files and 100+ failure modes. Count: see [BATTERY_INDEX.md](BATTERY_INDEX.md).
- L0-L7 constraint cascade mapped. Counts: see PYTORCH_RATCHET_BUILD_PLAN.md Phase 2.
- Irreducible families identified with independent observables. Counts: see [MIGRATION_REGISTRY.md](MIGRATION_REGISTRY.md).
- Tool usage across sim files: z3, sympy, clifford, toponetx, torch all represented. Counts: see [TOOL_MANIFEST_AUDIT.md](TOOL_MANIFEST_AUDIT.md).
- The stack is broader than the older tool docs implied: cvc5, geomstats, e3nn, rustworkx, XGI, GUDHI, PyG are all now represented in sim-like files. Do not count a tool as load-bearing until a result shows the tool changed, constrained, or certified the specific claim.
- PyTorch is NOT yet the primary substrate. numpy dominates.
- SIM_TEMPLATE.py now exists (system_v4/probes/SIM_TEMPLATE.py)
- Tool manifest is defined in the template but not yet present in legacy result JSONs
- Enforcement is still process-based until all new sims use the template and automatic promotion gates exist; bounded controller-side validator/gap-matrix tooling now exists, but these are not CI gates
- 7+ engine variants (core through Cl(6) unified)
- Axes 6, 5, 3, and 4 currently have stronger evidence than Axes 1, 2, and 0, but do not report them with a stronger public label unless a fresh file/result check was performed in the current run.
- The bridge / `Phi0` seam is now separated much better than before (`Xi`, `rho_AB`, cut kernels, `Phi0` bakeoffs), but it is still mostly numpy-first and underintegrated with proof/graph tooling.
- The basic plan is still only partially done: foundations and bridge separation are much better covered now, but the deep graph/proof integration pass has still not actually been completed.
- Controller-side enforcement now has a dedicated gap matrix (`docs/LLM_RESEARCH_GAP_MATRIX.json`) and validator (`system_v4/skills/llm_research_enforcement_validator.py`), but these are process tools, not automatic gates.

## TARGET BUILD REGIME (what we are building toward)
All 13 rules below describe the target regime. They are the standard new work should meet. Legacy work is not retroactively invalid, but it is not promoted to `canonical by process` without meeting these rules. No automated enforcement machinery exists yet — these are design constraints, not runtime checks.

---

## Definitions
- **Layer / shell**: a simultaneous constraint surface, not a sequential rung. Higher layers do not replace lower layers; they restrict the same state space further.
- **Classical baseline**: a numpy-era baseline artifact/result family. Useful as a baseline and negative control, not the target substrate. Its public status label still has to be checked separately (`exists`, `runs`, `passes local rerun`, or `canonical by process`).
- **Canonical sim / canonical by process**: a result status earned by fresh rerun, SIM_TEMPLATE-style structure, `classification`, non-empty tool manifest reasons, and claim-relevant load-bearing tool depth. It does not by itself mean `nonclassical`.
- **Micro tool sim**: the smallest tool-stage probe. It tests one named tool function or API surface against one tiny claim, including positive, negative, and boundary behavior. It receipt-validates only that function/surface under that claim.
- **Tool-lego fit probe**: a pre-lego tool-stage probe where a tool applies one already-named function/API surface to one useful bounded lego target. It answers whether the tool can carry that lego-shaped question. It does not promote the lego.
- **Tool-tool coupling**: a tool-stage integration probe where two already-tested tool functions exchange an output/input or cross-check the same tiny claim. Parallel use in one file is not coupling.
- **Supporting work**: docs, manifests, audits, indexes, and migration helpers. These have lighter tool requirements than canonical sims.
- **Relevance**: a tool may be omitted only if it cannot change the result or would be purely decorative. The omission must be explicit.

## Vocabulary crosswalk
This document uses three different vocabularies that must not be collapsed:

| Vocabulary | Examples | What it answers |
|---|---|---|
| public repo truth labels | `exists`, `runs`, `passes local rerun`, `canonical by process` | what can be reported about the file/result in controller closeout |
| process / ontology language | `open`, `killed`, `survived`, candidate order, shell-local, coupling | what happened inside the constraint-selection program |
| internal build / promotion language | `classical_baseline`, `canonical sim`, lane coverage, promotion blockers | how the work is staged and what stronger work remains |

Do not report process terms like `survived` or internal terms like `classical_baseline` as if they were public truth labels.

---

## Rule 1: PyTorch-native computation
All new core nonclassical computation uses PyTorch tensors. NumPy may remain in first-class classical baselines, legacy comparison rows, and explicit reviewed helper/boundary surfaces only. NumPy imports, `np.*` calls, and `.numpy()` tensor conversions are not allowed inside nonclassical sims as claim-bearing computation or as a quiet bridge to NumPy; any reviewed helper/boundary surface that still uses them remains blocked from nonclassical, QIT-engine, manifold, basin, axis, or bridge promotion until ported or explicitly reclassified. Density matrices = torch tensors. Operators = torch operations. Gradients = autograd.

For nonclassical manifold work, PyTorch is necessary but not sufficient. The
claim-bearing carrier must also be spinor/quaternion-compatible and
PEPS3D-carried from the first admitted finite carrier/probe step. A tensor that
is merely named PEPS3D, a scalar boundary row, a dense full-state closure, or a
Cartesian/Bloch primitive adapter is not a nonclassical manifold carrier.

**Why:** numpy arrays encourage Cartesian, coordinate-first computation. PyTorch computational graphs are a better fit for the current relational/non-coordinate design target. Treat this as current build rationale, not as a standalone proof of ontology.

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

**Why:** Each tool carries a different mathematical commitment. z3/cvc5 do constraint logic. Clifford does geometric product. TopoNetX/GUDHI do topology. geomstats does Riemannian geometry. e3nn does equivariant computation. PyG does graph computation. The two root constraints apply to the tool surface itself before the tool can be load-bearing for a nonclassical claim: the tool must act on a finite/bounded carrier and must certify, preserve, or pressure noncommuting or order-sensitive structure. A tool pressures a classical fallback only when the claim fails or cannot be certified without it and the result passes the sim contract; imports, wrappers, and parallel checks are decorative or supportive unless an ablation would break the claim.

### Rule 2a: Tool depth is micro-first

Do not build sims on stacks of untested tool behavior. Before a tool is used as load-bearing inside a lego-stage or integration claim, the relevant function/API surface must have a micro receipt:

1. one named tool;
2. one named function/API surface;
3. one tiny claim;
4. one useful bounded lego target or minimal fixture;
5. one positive case;
6. one negative case;
7. one boundary case;
8. one failure condition that would demote the tool role.

Every tool should search for the legos that best expose its actual value. z3/cvc5 should find fence, impossibility, and synthesis legos; sympy should find derivation and identity legos; Clifford should find rotor/spinor/operator legos; geomstats should find metric/geodesic/holonomy legos; rustworkx/XGI/TopoNetX/GUDHI/PyG should find graph, hypergraph, cell-complex, filtration, and graph-dynamics legos. These are tool-stage probes using lego-shaped targets, not lego-stage promotions.

Tool-tool coupling is later than the individual tool-function receipts. A coupling packet must name the two receipt-validated functions, the data exchanged or cross-check performed, and the single claim under test. If two tools are merely imported or run side by side, the packet is not a tool coupling.

This micro-first rule is a parallelization rule as much as a safety rule: many workers can test different tool/function/lego triples at once, and several workers may test the same triple in different ways. The controller accepts only receipts that stay inside one variable of uncertainty. If a worker has to debug the tool, the lego, and the coupling at the same time, the packet is too large.

Runner `DONE` marks execution evidence only. Controller admission requires reconciling the queue row, result JSON, `classification`, claim-relevant `TOOL_INTEGRATION_DEPTH`, and ledger loopback before the receipt can satisfy a gate.

Failure rule: when a compound or stack packet fails, do not debug the compound while any participating tool function lacks an individual useful-lego receipt. Decompose to the first missing micro proof, rerun that bounded packet, and only then revisit the compound.

## Rule 3: No unearned jargon in sims
Standard mathematical terms only. Z-dephasing, not Ti. X-rotation, not Fi. The Jungian labels are a Rosetta mapping applied only after the math has earned the relevant checks; they must not steer the computation layer.

This is broader than engine labels. Terms such as `manifold`, `layer`, `shell`,
`Hopf`, `quaternion shell`, `terrain`, `flux`, `Xi`, `Phi0`, `Axis0`,
`PEPS3D`, and `substage` are label-only until the sim gives the explicit finite
carrier, map/invariant, torch spinor/quaternion realization, PEPS3D
site/bond/face/cell anchor, negative/control, and receipt path. Label-only
usage must be classified as scaffold, Rosetta, adapter, diagnostic, or blocked,
not as evidence.

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
- fail closed when lower dependency maps lack receipts; do not turn a likely
  order into a scaffold with missing finite-map, PEPS3D-carrier, or control
  checks

This applies especially to:
- nested Hopf torus layers
- Weyl left/right layer
- differential / flux candidate layer
- bridge / cut-state layer
- later entropy / `Phi0` layers

### Rule 4b: G-stack / nesting work is layered, not one giant sim

The long-term target is a larger integrated sim made from layers of smaller sims. It must be built as:

1. independent legos for the real math objects, operators, geometry, graph/proof surfaces, and constraints;
2. local stack/nesting tests that ask which legos can coexist or must precede others;
3. bounded couplings only after the parent legos are current and honest;
4. larger integrated sims only after the lower layers have current receipts.

Coupling readiness is not inferred from `DONE` counts. It is earned only when the reconciled parent receipts satisfy the queue, result, classification, tool-depth, and ledger-loopback checks for the exact functions being coupled.

For G-stack / G-tower / Hopf / Weyl / Pauli / Flux work, do not simulate only isolated geometries and do not jump straight to the whole stack. First establish each candidate as a bounded finite-map lego with positive, negative, boundary, PEPS3D-carrier, and claim-relevant tool checks. Then test the admissible nesting order and noncommutativity of compositions.

Flux, Xi, Phi0, and Axis0 cannot be authored, queued, or summarized as
foundation progress until their lower dependency receipts are named. If the
lower map chain is missing, write a blocked-reason artifact or build the next
missing micro-scout; do not create a downstream row.

LLM and subagent parallelism belongs in writing, auditing, repairing, and scouting bounded packets. Actual sim evidence comes from Python runners. Classical baselines may run more freely as baselines and controls, but they do not become nonclassical evidence or bridge permission.

## Rule 5: Two quality modes inside the active stage
**Coverage mode**: mass independent lego construction. Each lego is a standalone building-block candidate. Breadth matters for coverage. A lego should pass its own positive and negative tests, but this mode does not by itself grant a stronger public truth label or closure claim.

**Promotion mode**: promotion-grade deepening. A lego becomes `canonical by process` only after deep testing:
- multiple test states (not just one state)
- theoretical value comparison
- at least one negative/failure case
- cross-validation against a different computation method
- boundary/edge case testing
- numerical precision analysis
- a clear statement of what would falsify the result
- tool manifest documenting all tools tried

These modes do not authorize broad stage promotion. Promotion inside the lego stage is still lego-stage work, and exploratory pairwise/coexistence work stays feedback-only unless separately earned. No bridge/axis/engine jump is earned merely because a subset of legos look strong.

**Why:** Breadth without depth is shallow. Depth without breadth is incomplete. Both are required, but they operate inside the active stage and do not override stage order.

## Rule 6: Negative testing is mandatory
Every positive test has a corresponding negative. Not "does it work" but "when does it break, and why."

**Why:** Selection pressure and failure modes are part of the system, not an afterthought.

## Rule 7: Constraint proofs, not classical proofs
Use z3 UNSAT (this is impossible) as the natural form of structural proof, not just SAT (this works). Quantum math is constraint-based: what is forbidden is often more fundamental than what is true.

**Mathematical basis:** In quantum mechanics, the fundamental results are no-go theorems (no-cloning, no-broadcasting, uncertainty relations, monogamy). These are impossibility proofs.

## Rule 8: No Platonic/causal language
Use "survived" not "created." Use "coupled with" not "causes." Use "constraint on distinguishability" not "fundamental reality." Nominalist throughout.

**Why:** The system is nominalist. Language carries rationalist/Platonic bias from training. Every word must be checked.

## Rule 9: The computational graph as ratchet-aligned computation substrate
- Forward pass = exploring the allowed math space (possibilities)
- Backward pass = constraints selecting what survives (selection)
- Graph topology = constraint manifold (what is computable)
- Gradient = what is load-bearing (signal)
- Zero gradient = what is redundant (noise)
- Treat this as a strong architectural working thesis for current build design, not as a public proof claim.

**Mathematical basis:** Autograd traces relationships between operations (relational, not Cartesian). Backprop flows information backward through constraints (non-causal, constraint-based). The graph topology admits what is computable (topological, not coordinate-based).

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

## Rule 12: Structural Anti-Salience Constraint

**This is a structural constraint, not advice.**

The training gradient pulls toward salient work: novel claims, high-level patterns, bridge and engine framing. It pulls away from: tool sims, lego rows, tool manifest completion, boring coverage passes. This is not a personality flaw; it is the LLM's completion probability under the training manifold. Left unresisted, stage inflation, label promotion, and Narrative Substitution for Gate Obedience surface on every session.

**Specific intercept points (probe family M_salience):**

1. **Lego skip** — model proposes coupling, bridge, or engine work while lego registry rows are open. Intercept: "which lego gate criterion is satisfied? cite the row and result file."
2. **Label inflation** — model reports status in language stronger than the evidence. Intercept: "name the criteria checked; cite the result file from this session."
3. **Agent trust without verify** — model builds on an agent's completion report without reading the result file. Intercept: "read the file; run the verification."
4. **Narrative substitution** — model constructs a plausible research narrative that implies a gate is satisfied. Intercept: "cite the gate criterion and result file, not the narrative."
5. **Scope creep** — model adds features, refactors, or improvements adjacent to the requested task. Intercept: "is this in scope? trace it to the request."

**How to apply:**

When salience pressure is detectable (the work feels exciting, the story feels right, the next step is obvious), that is the activation condition for this rule. Stop. Check the gate. Cite the evidence. If it cannot be cited, the gate is not satisfied.

Push back on the salience pull. Stay on the current layer. Do not leap ahead.

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
- Controller-side enforcement must reject or defer any pairwise/coexistence/bridge/axis work until tool sims, tool integration, and lego-stage completion are all satisfied — **required fail-closed process rule**

### Cultural
- Speed is not the goal. Depth is.
- "ALL PASS" is suspicious. Failure modes are expected.
- If it was easy, you probably skipped something.
- A sim that omits a relevant tool must say why, in the sim itself.
- A sim that declares many tools but uses none of them load-bearing has not actually done the plan.
