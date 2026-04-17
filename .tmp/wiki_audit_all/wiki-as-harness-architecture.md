---
title: Wiki As Harness Architecture
created: 2026-04-09
updated: 2026-04-12
type: concept
tags: [harness, system, canonical, architecture, language]
sources:
  - /Users/joshuaeisenhart/wiki/current/read-first.md
  - /Users/joshuaeisenhart/wiki/current/skills-and-agent-rules.md
  - /Users/joshuaeisenhart/wiki/current/wiki-harness-progress-and-audit.md
  - /Users/joshuaeisenhart/wiki/concepts/current-canonical-spine.md
framing: current
---

# Wiki As Harness Architecture

This is a second-layer harness architecture page. It should help explain how the wiki shapes controller/LLM behavior, but it does not replace `current/read-first.md` or the project `read-first.md` notes as the live entry tier.

The wiki is not a passive knowledge base. It is a cognitive harness that shapes LLM retrieval, framing, and saliency before reasoning begins. This page describes the 4-layer architecture.

## The 4 Layers

### Layer 1: Entry and routing stack

What is entry-tier, second-layer doctrine, mixed, legacy, archived.

Controls: which pages the model should treat as lower-entropy routing surfaces versus higher-entropy optional/support surfaces.

**Existing infrastructure:**
- `current/read-first.md` — the live front door
- relevant project `read-first.md` note — task-local front door
- [[current-canonical-spine]] — second-layer concept-level harness spine
- [[docs-framing-map]] — current vs legacy labeling
- [[docs-alignment-catalog]] — explicit provenance catalog
- `_archive/` directory — 22 archived files removed from active index

**Rule:** When the wiki is loaded as harness context, load the `current/` front door and relevant project front door first. Concept-level harness pages come after that on topic match. Legacy and archived pages are available for query but not loaded by default.

### Layer 2: Ontology Stack

What objects, processes, constraints, and structures are real in the system.

Controls: what the model treats as the actual building blocks.

**Existing infrastructure:**
- [[geometry-ingredient-map]] — carrier, constraint, and bridge geometry
- [[probe-doc-result-map]] — concept → probe → result mapping
- [[migration-registry]] — 28 irreducible families
- [[pytorch-ratchet-build-plan]] — phase status and architectural model
- [[constraint-surface-and-process]] — M(C), root constraints

**Rule:** The model must reason from the ontology stack, not from general quantum information theory. If the wiki says "density matrices are admissible objects under {F01, N01, CPTP}," the model must not say "density matrices are quantum states" (which is the default framing).

### Layer 3: Translation Stack

Same content restated in alternative framings that counter default LLM biases.

Controls: how the model describes the system.

**Current infrastructure:**
- [[nominalist-translation-rules]] — 7 mandatory translation rules
- [[llm-bias-inversion-rules]] — 6 specific LLM habit inversions
- [[harness-bias-inversions]] — controller-facing enforcement form of the six inversions
- [[nominalism-in-this-system]] — the philosophical foundation
- [[nominalist-framing]] — reading mode
- [[nominalist-cs-framing]] — implementation-native nominalist rendering for controller/wiki use
- [[llm-bias-and-failure-modes-reference]] — general failure modes

**Rule:** Before generating output, the model checks its draft against the translation rules and bias inversions. If it matches a default pattern, it rewrites.

**Worked method page:** [[harness-translated-companion]] — proof-of-method page anchored on the constraint-surface pair.

### Layer 4: Execution Stack

Each concept linked to probes, results, maturity, open questions, and falsification routes.

For wiki maintenance itself, the same harness logic should run Hermes-first: built-in wiki-capable tools are the default controller surface, while outside automation layers are subordinate supports for bounded tranches rather than the primary engine.

Controls: what evidence backs each claim, and what would disprove it.

**Current infrastructure:**
- [[probe-doc-result-map]] — the bridge page (NEW)
- [[docs-vs-sims-gap-audit]] — gap tracking (NEW)
- [[falsification-sim-designs]] — what would kill specific claims
- [[enforcement-and-process-rules]] — what "canonical" means
- [[controller-state-transition-model]] — bounded move and closure model for live controller work

**Rule:** Every claim must cite a probe file and result JSON. Claims without evidence are flagged as speculative. Claims with falsification routes are stronger than claims without.

## The Two Root Constraints As LLM Behavior

The harness should not merely explain F01 and N01. It should force the model to behave under them.

### F01 — finitude / bounded distinguishability

Math/source shorthand:
- `F01: |S| < ∞, |M| < ∞, dim(H) < ∞`
- only finite carriers, probes, operators, and paths are admissible

Required LLM behavior if F01 is followed:
- choose a finite packet, not a vague objective
- keep scope bounded to the explicitly requested lane and layer
- name exact files, commands, result paths, and audits
- refuse silent widening into adjacent lanes just because they are available
- treat unsupported summary language as inadmissible

Operational reading:
- bounded work is not a convenience; it is admissibility discipline
- finite witness paths beat generalized narrative

### N01 — noncommutation / order-sensitive composition

Math/source shorthand:
- `N01: A∘B ≠ B∘A in general`
- order belongs to the object
- swap-by-default is forbidden

Required LLM behavior if N01 is followed:
- preserve requested sequence exactly when the user specifies an order
- do not reorder phases because another task looks useful or easy
- do not count out-of-order work as progress
- do not mix side lanes before prerequisite layers are complete
- treat process order as part of correctness, not as a presentation preference

Operational reading:
- in this system, out-of-order execution is not merely suboptimal; it changes the object and invalidates the run

### Harness consequence

If the wiki is functioning as a real LLM harness, it should bias the model away from opportunistic helpfulness and toward constraint-obedient execution:
- finite, witness-backed, bounded moves under F01
- order-faithful, sequence-preserving execution under N01

That means the harness should suppress the default LLM habit of "doing nearby useful things" when those things violate requested order.

## How the Layers Interact

```
User query
    ↓
[Routing] Which pages are lower-entropy steering surfaces for this task? → Load spine + current pages
    ↓
[Ontology] What objects/constraints are real? → Ground in geometry-ingredient-map
    ↓
[Translation] How must this be described? → Apply nominalist + bias-inversion rules
    ↓
[Execution] What evidence backs this? → Cite probe/result from probe-doc-result-map
    ↓
Response (harness-shaped)
```

## Loading Priority (for harness context)

When the wiki is loaded to shape LLM behavior:

**Always load:**
1. `current/read-first.md` plus the rest of the needed `current/` spine
2. relevant project `read-first.md` note when the task is project-bound
3. [[current-canonical-spine]] only when concept-level harness doctrine is needed
4. [[nominalist-translation-rules]] — the 7 rules
5. [[llm-bias-inversion-rules]] — the 6 inversions
6. [[harness-bias-inversions]] — controller-facing enforcement view
7. [[llm-controller-contract]] — status labels and hard stops
8. [[enforcement-and-process-rules]] — the 13 rules
9. [[controller-state-transition-model]] — bounded controller and maintenance closure reading

**Load on demand (when topic matches):**
- Geometry: [[geometry-ingredient-map]], [[density-matrix-mathematics]], [[hopf-fibration-mathematics]]
- Constraints: [[constraint-surface-and-process]], [[pytorch-ratchet-build-plan]]
- Evidence: [[probe-doc-result-map]], [[docs-vs-sims-gap-audit]]
- Bridge: [[qit-engine-geometry-entropy-bridge]]

**Never load by default:**
- Legacy/speculative pages
- Archived files
- Source-notes indexes (too large, low signal)

## Related Pages

- [[nominalist-translation-rules]] — translation layer
- [[llm-bias-inversion-rules]] — bias counter layer
- [[harness-bias-inversions]] — controller-facing bias enforcement layer
- [[harness-translated-companion]] — proof-of-method companion page
- [[current-canonical-spine]] — second-layer concept-level harness spine
- [[probe-doc-result-map]] — execution layer
- [[llm-controller-contract]] — the execution contract
- [[controller-state-transition-model]] — execution-state bridge
- [[nominalist-cs-framing]] — implementation-native translation bridge
- [[nominalism-in-this-system]] — philosophical foundation
- [[docs-framing-map]] — provenance labeling
- [[constraint-on-distinguishability]] — root formal source for F01/N01
