---
title: Current Research Overlays
created: 2026-04-07
updated: 2026-04-14
type: summary
tags: [reference, research]
sources:
  - raw/articles/new-docs/03_source_notes.md
  - raw/articles/new-docs/05_research_index.md
  - raw/articles/new-docs/09_research_inventory_and_foundations.md
framing: current
---

# Current Research Overlays

## Overview
Routing page for the current research stack. This page maps raw source notes, current-docs-aligned pages, and external support traditions into one controlled research lane.

The goal is not to flatten all research into one story. The goal is to keep the current stack readable while attaching the right external references to the right gaps.

## Source Categories
The research stack draws from multiple overlapping source categories:
- Core mathematical documents (differential geometry, quantum information, operator algebra)
- Simulation results from system_v4/probes/a2_state/sim_results/
- Cross-domain equivalence mappings from [[cross-domain-equivalence-map]]
- External formal tradition references from [[formal-methods-and-witness-discipline-reference]]
- Support bibliography for explanation, correlative thinking, and process language from [[research-support-bibliography]]
- Owner corrections and session notes

## Research routing by gap
This overlay page is organized by what kind of support the current stack still needs.

### Distinguishability and admissibility
Use these pages when the question is what can be told apart, what is operationally equivalent, and what survives probe-relative comparison:
- [[constraint-on-distinguishability]]
- [[constraint-on-distinguishability-formal-reference]]
- [[distinguishability-formal-reference]]
- [[distance-metrics-state-space]]
- [[support-first-constraint-manifold-dependency-chain]]

### Spectral compression and low-rank structure
Use these pages when the question is how PCA, QPCA, Schmidt structure, and density-matrix truncation align:
- [[compression-to-density-matrix-map]]
- [[pca-qpca-alignment]]
- [[pca-qpca-density-matrix-view]]
- [[schmidt-decomposition-bipartite]]
- [[quantum-computing-applications]]

### Geometry and holonomy
Use these pages when the question is which intrinsic geometry the carrier admits:
- [[information-geometry-reference]]
- [[quantum-fisher-information-geometry]]
- [[quantum-geometry-fubini-study]]
- [[doubly-quantum-mechanics]]
- [[qit-geometry-thermodynamics-harness-synthesis]]
- [[berry-phase-and-holonomy]]
- [[fiber-bundles-and-spin-geometry]]
- [[cl3-cl6-micro-sims]]
- [[gerbe-g-tower-and-motives-packets]]
- [[g-structure-tower]]
- [[hopf-foliation-structure]]
- [[bundle-towers-and-layered-supports]]
- [[foliations-distributions-and-constrained-order]]

### Operator algebra and channels
Use these pages when the question is noncommutation, basis choice, and dynamical maps:
- [[clifford-algebra-qit]]
- [[operator-algebras-and-representation]]
- [[cptp-maps-and-channels]]
- [[arxiv-2603-21852-eml-operator]]
- [[qit-vocabulary-discipline-reference]]

### Dynamical stability and recurrence
Use these pages when the question is recurrence, metastability, stability regions, invariant sets, or open-system recovery behavior:
- [[attractor-basins-formal-reference]]
- [[qit-basin-engine-synthesis]]
- [[stochastic-thermodynamics-reference]]
- [[cptp-maps-and-channels]]
- [[distance-metrics-state-space]]
- [[qit-vocabulary-discipline-reference]]

### Entanglement, correlation, and information
Use these pages when the question is bipartite structure, correlation, and entropy families:
- [[entanglement-theory]]
- [[quantum-information-measures]]
- [[quantum-shannon-theory-reference]]
- [[schmidt-decomposition-bipartite]]
- [[axis-and-entropy-reference]]
- [[jk-fuzz-field]]
- [[i-scalar-and-axis-0-genealogy]]

### Graph / proof / tool stack
Use these pages when the question is which graph, proof, symbolic, or geometry-side tool is supposed to do what in the active working stack:
- [[tooling-status]]
- [[executable-root-axiom-micro-sims]]
- [[sim-tranche-2026-04-14-axioms-tools-gerbes-motives]]
- [[nonclassical-system-tool-plan]]
- [[tool-capability-sim-program]]
- [[classical-baseline-vs-canonical-tool-boundary]]
- [[networkx-graph-structure-reference]]
- [[pydantic-typed-schema-reference]]
- [[jsonschema-artifact-validation-reference]]
- [[pytest-tiered-gate-reference]]
- [[hypothesis-property-based-testing-reference]]
- [[witness-recorder-and-trace-reference]]
- [[lean4-proof-assistant-reference]]
- [[tlaps-temporal-proof-reference]]
- [[z3-smt-solver-reference]]
- [[cvc5-smt-and-sygus-reference]]
- [[sympy-symbolic-math-reference]]
- [[rustworkx-graph-algorithms-reference]]
- [[xgi-hypergraph-reference]]
- [[toponetx-topological-complex-reference]]
- [[pytorch-geometric-reference]]
- [[gudhi-persistent-topology-reference]]
- [[geomstats-manifold-geometry-reference]]
- [[clifford-geometric-algebra-reference]]
- [[e3nn-equivariant-geometry-reference]]

Use [[sim-tranche-2026-04-14-axioms-tools-gerbes-motives]] when the question is not a timeless tool description but which sim packets landed in the 2026-04-14 axiom/tool/gerbe/G-tower/motives tranche and which artifacts only have `exists` status pending a fresh rerun.

### Nominalist and process framing
Use these pages when the question is how to describe the system without collapsing it into generic metaphysics:
- [[nominalist-cs-cluster]]
- [[nominalism-in-this-system]]
- [[nominalist-cs-framing]]
- [[codex-ratchet-cs-bounded-system-framing]]
- [[controller-state-transition-model]]
- [[nominalist-cs-jp-systems-bridge]]
- [[nominalism-philosophical-foundation]]
- [[nominalist-framing]]
- [[harness-bias-inversions]]
- [[topos-quantum-mechanics-reference]]
- [[process-philosophy-and-relational-physics]]
- [[autopoiesis-and-enactivism-reference]]
- [[fep-and-active-inference-reference]]
- [[evolutionary-epistemology-reference]]
- [[chinese-philosophy-reference]]
- [[qit-vocabulary-discipline-reference]]
- [[research-support-bibliography]]

For nominalist-CS routing, use this order: [[nominalist-cs-cluster]] -> [[nominalist-cs-framing]] -> [[codex-ratchet-cs-bounded-system-framing]] -> [[controller-state-transition-model]] -> either [[qit-engine-dev-framing]] for the runtime/dev lane or [[nominalist-cs-jp-systems-bridge]] for the metaphor/self-similar lane. Use [[five-framework-cluster]] only as the quick recall query after the main route is clear.

Use this split inside the Chinese-philosophy lane: Confucian material is strongest for naming discipline, role-grounding, and cultivation; Daoist and correlative material are strongest for process-first, anti-essential, and transformation-centered support.

### AI, world models, and alignment support
Use these pages when the question is how the QIT engine / density-matrix stack touches AI research without overclaiming:
- [[leviathan-framework]]
- [[graph-driven-intent-runtime]]
- [[qit-ai-foundations-bridge]]
- [[qit-engine-dev-framing]]
- [[qit-engine-dev-technical-brief]]
- [[qit-engine-constraint-engineering-bridge]]
- [[leviathan-to-qit-engine-glossary]]
- [[leviathan-world-engine-memo]]
- [[leviathan-science-method-qit-engine-crosswalk]]
- [[holodeck-qit-fep-leviathan-integration]]
- [[why-qit-engines-need-exotic-geometry]]
- [[prediction-first-memory-vs-llm-memory]]
- [[holodeck-as-recall-space]]
- [[recursive-science-methodology-reference]]
- [[ai-ml-density-matrix-connections]]
- [[fep-and-active-inference-reference]]
- [[llm-bias-and-failure-modes-reference]]
- [[moloch-trap-reference]]
- [[operationalism-and-measurement-reference]]
- [[distinguishability-formal-reference]]
- [[qit-vocabulary-discipline-reference]]

For the Leviathan / JP-facing lane, keep the authority order explicit: [[leviathan-framework]] is the genealogy-first social-OS source surface, [[recursive-science-methodology-reference]] is the cleaned method layer, [[graph-driven-intent-runtime]] is the runtime/dev bridge, and [[holodeck-qit-fep-leviathan-integration]] carries the world-model and memory-side integration. That preserves legacy provenance inside the overlay lane without promoting the manuscript itself to repo-current authority.

Use the holodeck memory lane with explicit authority separation:
- [[holodeck-docs]] = provenance-first source digest
- [[projective-holodeck-memory-model]] = extracted legacy kernel
- [[holodeck-as-recall-space]] and [[prediction-first-memory-vs-llm-memory]] = current support/translation pages
- [[holodeck-qit-fep-leviathan-integration]] = current dev-facing integration surface

When the question is not provenance but which external support lane should stabilize the memory-runtime interpretation, read [[research-support-bibliography]] after those support pages. In that bibliography, Cluster 4 is the prediction-first memory / recall-space support lane and Cluster 5 is the recursive science-method / engine-pattern support lane.

That keeps a load-bearing legacy memory/perception idea visible without promoting the full restored source to current-truth status.

### Personality / engine-grammar translation lane
Use these pages when the question is how to preserve the legacy personality package as candidate engine grammar without collapsing it into pop typology or current runtime proof:
- [[legacy-psychology-personality]]
- [[emotional-evolution-personality-system]]
- [[personality-theory-mapping]]
- [[leviathan-science-method-qit-engine-crosswalk]]

Treat MBTI/Jung/politics/hormone overlays as historical source vocabulary unless a narrower current page explicitly reuses one piece. For dev-facing translation, hand forward into the crosswalk and adjacent current pages rather than starting with the typology tables.

When the question is support-layer translation rather than provenance, use this order: [[emotional-evolution-personality-system]] -> [[personality-theory-mapping]] -> [[process-and-systems-thinking-reference]] -> [[operationalism-and-measurement-reference]] -> [[evolutionary-epistemology-reference]] -> [[moloch-trap-reference]] -> [[research-support-bibliography]] -> [[leviathan-science-method-qit-engine-crosswalk]]. That keeps the lane in process / measurement / coordination language instead of letting MBTI labels become the handoff interface.

This lane is genealogy/translation support, not earned runtime proof.

For JP-facing runtime handoff, use [[graph-driven-intent-runtime]] alongside that lane and keep [[model-context-overlay]] in a genealogy/translation role rather than treating it as a runtime authority page.

### Legacy routing and comparison control
Use these pages when a current research question depends on legacy provenance or branch separation, not when a legacy source should silently define present-tense truth:
- [[current-docs-vs-legacy-framing]]
- [[legacy-source-history]]
- [[legacy-speculative-frameworks]]
- [[dark-empress-vs-grandmaster]]
- [[legacy-speculative-theory]]

This lane exists to stop the legacy books, social-OS manuscripts, personality materials, and holodeck sources from collapsing into one smoothed "legacy doctrine" blob. Read it to identify which branch is actually carrying the claim, then hand forward into the narrower support or current pages.

For current research work, treat this as routing/provenance support rather than evidence closure: it helps decide which legacy stream a claim came from and which current bridge page should absorb it, but it does not itself promote those legacy claims to repo-current truth.

### Harness and multi-thread control
Use these pages when the question is how the wiki is supposed to steer future readers and agents:
- [[llm-controller-contract]]
- [[codex-audit-controller-contract]]
- [[concurrency-and-trace-theory-reference]]
- [[mimetic-meme-manifold-harness]]
- [[mimetic-meme-manifold-canonical-synthesis]]
- [[research-support-bibliography]]
- [[stack-authority-and-capability-index]]

## How Sources Feed the Stack
Sources feed into the research through a layered ingestion process:
1. Raw sources land in raw/articles/new-docs/
2. Preprocessed digests extract key structures and claims
3. Sim code tests specific claims against the [[constraint-on-distinguishability-full-math|constraint surface]]
4. Results are recorded in JSON artifacts
5. The [[current-preaxis-status-and-ordering-note|status ledger]] tracks what has been validated

6. The overlay layer attaches the relevant external reference pages so future research does not have to rediscover the support structure from scratch.

## Source Integrity Rules
- Every sim must cite its source materials
- Source pointers required on all formal outputs
- No placeholder content ("...", "etc.") in formal saves
- Owner corrections take precedence over LLM-generated content
- Sources are archived in raw/ and never modified after ingestion

## Overlays and Cross-References
The research overlays connect several routed support and evidence pages:
- [[pca-qpca-alignment]]: PCA/QPCA correspondence
- [[constraint-on-distinguishability-full-math]]: Full mathematical treatment
- [[research-index-compression-terms]]: Compression term definitions
- [[research-inventory-and-foundational-findings]]: Foundational findings
- [[research-inventory-and-foundations]]: evidence-backed inventory and collapse classes
- [[current-canonical-spine]]: second-layer reading-order router for the stack
- [[notebooklm-reference-pack-intake]]: bounded intake ledger for the large external bibliography
- [[research-source-coverage-index]]: which domains actually have downloaded packets versus citation-only stubs

## Related pages
- [[new-docs-manifest]]
- [[topic-map]]
- [[research-index-compression-terms]]
- [[research-inventory-and-foundational-findings]]
- [[pca-qpca-alignment]]
- [[research-inventory-and-foundations]]
- [[current-canonical-spine]]
- [[wiki-driven-arxiv-search-queue]]
