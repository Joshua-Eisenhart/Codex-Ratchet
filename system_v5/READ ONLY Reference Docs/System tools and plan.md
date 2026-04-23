

**Current Truth**
- `Verified` Yes. `v5` has to be built so the model cannot “just vibe.”
- `Verified` The fix is not better prompting alone. It is **hard structure**:
  - fixed order
  - fixed tool requirements
  - fixed artifact requirements
  - fixed claim limits
  - fail-closed gates
- `Verified` If this is left to LLM judgment, it will drift, smooth, narrate, skip tiers, and call partial work “done.”

**Actually Broken**
- `Verified` The real failure mode is not intelligence. It is missing enforcement.
- `Verified` Without hard gates, the model will:
  - skip prerequisites
  - use whatever tool is easiest
  - produce summaries instead of substrates
  - mix diagnostic probes with real evidence
  - collapse open branches into one story
  - mutate docs instead of building runtime truth

**Evidence**
- `Verified` You already saw this in `v4`:
  - old-doc overload
  - graph overload
  - reduced probes treated too strongly
  - many folders with weak role boundaries
  - validator-green drift without substrate compliance
- `Verified` The repo already contains useful tools and sidecars, but they were not made mandatory at the right phases.

**Next Move**
- `Verified` `v5` needs a **Sim Admission Contract** and a **Process Contract**.

1. `Process Contract`
- every tranche has:
  - required order
  - allowed tools
  - required outputs
  - forbidden shortcuts
  - stop rule
- example order:
  1. carrier
  2. geometry
  3. Weyl/chirality
  4. transport
  5. negatives
  6. placement/embargo
  7. bridge/cut
  8. entropy
  9. only then higher consumers

2. `Sim Admission Contract`
- every sim must declare:
  - `sim_class`
  - `tier`
  - `required_tools`
  - `required_inputs`
  - `required_outputs`
  - `allowed_claims`
  - `promotion_blockers`
- if missing anything, it fails closed

3. `Tool Gate`
- for each tier, specify mandatory tools
- example:
  - `micro/pre-axis`: numeric + validator
  - `full-geometry`: numeric + graph + constraint + witness trace
  - if graph/formal tools are required and unused, result becomes `diagnostic_only`

4. `Claim Gate`
- no prose can upgrade a result
- only artifact class can
- example:
  - `diagnostic_only` cannot support geometry claims
  - `pre_axis_admission` cannot support Axis closure
  - `axis_entry` cannot rewrite lower-law placement

5. `No Smoothing Rule`
- branch conflicts must be stored as separate branches
- open candidates stay open
- dead branches get marked dead, not blended into survivors
- no “best narrative” field in core truth surfaces

6. `Boot Gate`
- boots do not read random docs
- boots read:
  - decision log
  - sim registry
  - artifact registry
  - tranche ledger
- nothing else is boot-authoritative

7. `Doc Freeze Rule`
- docs are reference only by default
- runtime truth must be emitted as machine-readable artifacts
- prose cannot be the active substrate

**Concrete Principle**
- do not trust the LLM to follow process
- make the process executable
- make violations mechanically visible
- make unauthorized success impossible

**Minimal v5 law**
- if a step is required, it must have an artifact
- if a tool is required, its output must be present
- if outputs are incomplete, the run is not promoted
- if branch status is open, the system may not narratively close it

It means now: `v5` must be designed to constrain the model like a dangerous junior operator, not trusted like a careful scientist.


For `v5`, I’d split them into **required now**, **required later**, and **optional sidecars**.

**Required Now**
- `networkx`
  - core graph structure
  - state graphs, dependency graphs, witness graphs, boot graphs
- `pydantic`
  - typed schemas for graph nodes, edges, witnesses, sim contracts
- `jsonschema`
  - artifact validation
- `GraphML` export/import
  - stable graph interchange for inspection and tooling
- `z3`
  - constraint checks, impossibility checks, embargo/admissibility checks
- `pytest`
  - executable gates for every tier
- `hypothesis`
  - property-based pressure on invariants and negatives

**Required For Full-Geometry Sims**
- `TopoNetX`
  - higher-order topology, cells, boundaries, loop/hole structure
- `igraph` or `networkit`
  - faster graph analytics if `networkx` gets too slow
- `witness trace recorder`
  - explicit step/event spine, not just summary JSON
- constraint report generator
  - what constraints were active, satisfied, violated
- graph artifact emitter
  - every full-geometry sim should emit a graph, not just scalars

**Useful For Engine/System Mirroring**
- heterograph tooling, likely `PyG`
  - different node/edge types for:
    - carrier
    - operator
    - witness
    - negative
    - boot dependency
    - runtime object
- graph query / RAG layer
  - maybe LightRAG, HippoRAG, or a simpler custom graph-backed retrieval layer
  - but only after canonical graph schema exists

**Optional Sidecars**
- `clifford`
  - if you want graded/noncommutative algebra surfaces represented directly
- SMT extras beyond `z3`
  - only if Z3 is not enough
- symbolic algebra tools
  - if exact derivation pressure becomes important

**What Each Tool Is For**
- `networkx`: canonical system graph
- `TopoNetX`: topology beyond plain pairwise edges
- `PyG`: typed/heterogeneous graph learning or richer relation handling
- `z3`: prove a thing is blocked / impossible / not admitted
- `pytest` + `hypothesis`: enforce contracts and attack assumptions
- `pydantic` + `jsonschema`: stop artifact drift and smoothing

**Minimum Clean Stack**
If you want the smallest serious setup:
1. `networkx`
2. `pydantic`
3. `jsonschema`
4. `z3`
5. `pytest`
6. `hypothesis`

That is enough to build:
- graph-backed system structure
- proof/admissibility gates
- tiered sim contracts
- fail-closed promotion

**Most Important Rule**
Do not install tools just because they exist.
Each one should have a named job in `v5`:
- graph structure
- higher-order topology
- proof/admissibility
- witness/event recording
- retrieval/self-understanding

It means now: `networkx + z3 + pydantic/jsonschema + pytest/hypothesis` is the real minimum; `TopoNetX` and `PyG` come in when you are ready for full-geometry and mirrored system/engine graphs.

1. Host Architecture Planes (The Lev Stack)
  From: 29 thing.txt & lev_nonclassical_runtime_design_audited.md


  ┌───────────────┬────────────────────────────────────────────────────────────────────────────────────┐
  │ Plane         │ Role                                                                               │
  ├───────────────┼────────────────────────────────────────────────────────────────────────────────────┤
  │ Topology      │ Host for allowable regions, graph connectivity, transitions, gates, and terminals. │
  │ Orchestration │ Host for loop policies, traversal strategies, retry behavior, and phase            │
  │               │ advancement.                                                                       │
  │ Dispatch      │ Plane for executing transforms, simulations, reviewers, and validators.            │
  │ Event Spine   │ Append-only host for witness traces, positive/negative evidence, and step history. │
  └───────────────┴────────────────────────────────────────────────────────────────────────────────────┘

  ---

  2. Shared Runtime Kernel (Primary Objects)
  From: 29 thing.txt & lev_nonclassical_runtime_design_audited.md


  ┌──────────────┬──────────────────────────────────────────────────────────────────────────────────────┐
  │ Object       │ Definition                                                                           │
  ├──────────────┼──────────────────────────────────────────────────────────────────────────────────────┤
  │ RuntimeState │ Carrying: region, phaseIndex, phasePeriod, loopScale, boundaries, invariants, dof,   │
  │              │ context.                                                                             │
  │ Probe        │ State-observation operator producing an Observation (probeId + features).            │
  │ Transform    │ Ordered state-evolution operator: apply(state, input) -> next_state.                 │
  │ Witness      │ Evidence object (kind: positive/negative/counterexample) with a trace of StepEvents. │
  │ StepEvent    │ Single transition record: at, op, beforeHash, afterHash.                             │
  └──────────────┴──────────────────────────────────────────────────────────────────────────────────────┘

  ---

  3. Retooled External Method/Operator Families
  From: 29 thing.txt (The "29 things")

   1. Nested Hopf Tori (multi-scale cyclic control)
   2. Topology / Orchestration / Dispatch Split (architectural isolation)
   3. Graph Topology Thinking (workflow as topology)
   4. Nonclassical State Space (order-sensitive composition)
   5. Phase / Loop-Scale Runtime Model (explicit recurrence)
   6. Karpathy Design Philosophy (minimal visible core)
   7. nanochat (inspectable conversational core)
   8. autoresearch (bounded self-improvement)
   9. llm-council (disagreement-preserving review)
   10. Bayesian Updating (evidence-driven state revision)
   11. Markov Chains (explicit transition laws)
   12. FEP / Active Inference (adaptive correction loops)
   13. Information Geometry (distinguishability-based metric)
   14. Algorithmic Information Theory (motif detection via compression)
   15. Property-Based Testing (invariant pressure)
   16. CEGIS (counterexample-guided synthesis)
   17. SAT / SMT (hard impossibility detection)
   18. Differential Testing (cross-implementation divergence)
   19. Model Checking (failure trace exploration)
   20. Abstract Interpretation (coarse coarse-to-fine refinement)
   21. Fuzzing (adversarial witness generation)
   22. AlphaGeometry-Style Search (disciplined search control)
   23. Program Synthesis (structured candidate generation)
   24. DreamCoder / Abstraction Learning (library-induction from traces)
   25. Evolutionary Search (variation-generation without fitness ontology)
   26. Constrained Decoding (transport discipline/schemas)
   27. Guardrail Pipelines (admission/boundary guards)
   28. Build / Reproducibility Systems (deterministic replayability)
   29. Graph Mining / Topology Extraction (motif/cluster extraction from traces)

  ---

  4. Local Source Repo Inventory & Families
  From: LOCAL_SOURCE_REPO_INVENTORY.md & SKILL_SOURCE_CORPUS.md


  ┌─────────────────────┬──────────────────────────────────────────────────┬─────────────────────────┐
  │ ID / Family         │ Local Presence / Path                            │ Status                  │
  ├─────────────────────┼──────────────────────────────────────────────────┼─────────────────────────┤
  │ Main Workspace      │ Codex Ratchet                                    │ repo_local              │
  │ Retooled External   │ 29 thing.txt                                     │ repo_local              │
  │ Methods             │                                                  │ (Authoritative Source)  │
  │ Lev Nonclassical    │ lev_nonclassical_runtime_design_audited.md       │ repo_local              │
  │ Design              │                                                  │ (Implementation         │
  │                     │                                                  │ Rendering)              │
  │ Leviathan v3.2      │ core_docs/a2_feed_high entropy doc/              │ repo_local              │
  │ Local               │                                                  │                         │
  │ pi-mono             │ work/reference_repos/other/pi-mono               │ repo_local              │
  │ lev-os/agents       │ work/reference_repos/lev-os/agents               │ repo_local (635 skills) │
  │ lev-os/leviathan    │ work/reference_repos/lev-os/leviathan            │ repo_local              │
  │ Karpathy family     │ autoresearch, llm-council, llm.c, minbpe,        │ repo_local              │
  │                     │ nanochat, nanoGPT                                │                         │
  │ External Audit      │ Context-Engineering, spec-kit, superpowers, mem0 │ repo_local              │
  │ family              │                                                  │                         │
  │ EverMind-AI family  │ EverMemOS, MSA                                   │ repo_local              │
  │ Formal Verification │ z3, alphageometry, AutoResearchClaw,             │ repo_local              │
  │                     │ dreamcoder-ec                                    │                         │
  │ OpenClaw-RL         │ [arXiv 2603.10165]                               │ url_only                │
  │ Brain/Memory        │ HippoRAG, LightRAG                               │ url_only                │
  │ Candidates          │                                                  │                         │
  └─────────────────────┴──────────────────────────────────────────────────┴─────────────────────────┘

  ---

  5. Graph Stack & Sidecar Toolchain
  From: SKILL_SOURCE_CORPUS.md & LOCAL_SOURCE_REPO_INVENTORY.md

  Base Carrier (Repo Local):
   * pydantic (Typed Schema)
   * networkx (In-memory engine)
   * JSON / GraphML (Interchange)

  Sidecar Environment (.venv_spec_graph):
   * torch / torch-geometric (Heterograph projection)
   * toponetx (Cell-complex / higher-order topology)
   * hypernetx / xgi (Hypergraph relations)
   * clifford / kingdon (Geometric algebra / noncommutative edges)
   * pyquaternion (Spinor transformations)
   * igraph / graphviz (Visual/Analysis)

  ---

  6. Admitted Graph Artifacts & Builders
  From: LOCAL_SOURCE_REPO_INVENTORY.md

   * nested_graph_v1.json (Populated cross-layer artifact)
   * nested_graph_builder.py (Live nested-graph operator)
   * skill_kernel_bridge_builder.py (Direct graph-formation operator)
   * v4_graph_builder.py (Owner graph builder)
   * Layer set: a2_high_intake, a2_mid_refinement, a2_low_control, a1_jargoned, promoted_subgraph.

  This list is rebuilt directly from the corpus sources. I have removed all summaries and shorthand. Is
  there a specific "missing category" you'd like me to expand on further, or should we move to the next
  phase of the System Skill Build Plan?





**Current Truth**
- `Verified` I have now read the full audited document at [lev_nonclassical_runtime_design_audited.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/lev_nonclassical_runtime_design_audited.md).
- `Verified` The doc is defining a bigger taxonomy than just `repos`, `skills`, and `graph tools`.
- `Verified` The categories it explicitly defines are:
  - `Host architecture planes`
  - `Runtime kernel objects`
  - `Runtime commitments / invariants`
  - `Method/operator families to retool`
  - `Integration-scope families`
  - `Layer placement`
  - `Immediate build order`
  - `Implementation review checklists`

**Actually Broken**
- `Verified` My earlier lists were wrong because they skipped doc-defined categories and kept collapsing everything into inventory-style buckets.
- `Verified` The category I was still missing is the doc’s own `integration expansion mandate` layer, which is not just a repo list. It is the explicit admission scope for whole external families.
- `Verified` I was also under-listing the doc’s `runtime kernel` and `host architecture` objects, which are first-class in this design.

**Evidence**
- `Verified` **Host architecture planes** named in [lev_nonclassical_runtime_design_audited.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/lev_nonclassical_runtime_design_audited.md):
  - `Topology`
  - `Orchestration`
  - `Dispatch`
  - `Event Spine`
- `Verified` **Runtime kernel objects** named there:
  - `RuntimeState`
  - `Probe`
  - `Observation`
  - `Transform`
  - `StepEvent`
  - `Witness`
  - runtime fields:
    - `region`
    - `phase`
    - `loop scale`
    - `boundaries`
    - `invariants`
    - `degrees of freedom`
- `Verified` **Runtime commitments / invariants** named there:
  - finitude
  - non-commutation
  - ordered transforms
  - probe-relative equivalence
  - append-only witness traces
  - tiered positive and negative simulations
  - explicit guards against illegal transitions
- `Verified` **Method/operator families** named there:
  - Nested Hopf Tori
  - Graph Topology Thinking
  - Nonclassical State Space
  - Phase / Loop-Scale Runtime Model
  - Karpathy Design Philosophy
  - `nanochat`
  - `autoresearch`
  - `llm-council`
  - Bayesian Updating
  - Markov Chains
  - FEP / Active Inference
  - Information Geometry
  - Algorithmic Information Theory
  - Property-Based Testing
  - CEGIS
  - SAT / SMT
  - Differential Testing
  - Model Checking
  - Abstract Interpretation
  - Fuzzing
  - AlphaGeometry-style Search
  - Program Synthesis
  - DreamCoder abstraction learning
  - Evolutionary Search
  - Constrained Decoding
  - Guardrail Pipelines
  - Build / Reproducibility Systems
  - Graph Mining / Topology Extraction
- `Verified` **Integration-scope families** named in the doc’s `Integration Expansion Mandate`:
  - local Lev nonclassical runtime design
  - `lev-os/agents`
  - `lev-os/leviathan`
  - Karpathy-family patterns
  - Z3 / SAT / SMT / model checking / fuzzing / constrained decoding families
  - `pi-mono`
  - EverMemOS / EverMind-style memory services
  - MSA / Memory Sparse Attention
  - [29 thing.txt](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/29%20thing.txt) as canonical source doc
  - multi-source cross-validation graph clusters such as `29 sources / 29 batches`
- `Verified` **Layer placement** named there:
  - `A2_HIGH_INTAKE`
  - `A2_MID_REFINEMENT`
  - `A2_LOW_CONTROL`
  - `Witness/runtime bridge`
  - `B_ADJUDICATED`
  - `SIM_EVIDENCED`
  - `External adaptor family`
- `Verified` **Immediate build order** named there:
  1. make pattern-only families explicit skills
  2. keep admitted skills graph-native from day one
  3. wire external memory into witness / intent / context
  4. bridge `pi-mono` against that memory seam
  5. only later evaluate `MSA`
- `Verified` This matches and extends the corpus docs in [SKILL_SOURCE_CORPUS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/legacy_docs/SKILL_SOURCE_CORPUS.md), [LOCAL_SOURCE_REPO_INVENTORY.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/legacy_docs/LOCAL_SOURCE_REPO_INVENTORY.md), and [SYSTEM_SKILL_BUILD_PLAN.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/legacy_docs/SYSTEM_SKILL_BUILD_PLAN.md), but the audited Lev doc is the cleaner top-level taxonomy.

**Next Move**
- `Verified` The correct list-building structure is now:
  1. `Architecture planes`
  2. `Runtime kernel objects`
  3. `Commitments / invariants`
  4. `Method/operator families`
  5. `Integration-scope families`
  6. `Layer placement`
  7. `Build order`
  8. `Actual repos / graph tools / sidecars that instantiate those`
- `Verified` If you want the next pass, I should produce the inventory in exactly that order and then map each item to local files/repos/tools instead of mixing categories again.

It means now: the audited Lev doc has been read, and the missing half was the document’s own architecture/runtime/integration taxonomy, not just more repo names.