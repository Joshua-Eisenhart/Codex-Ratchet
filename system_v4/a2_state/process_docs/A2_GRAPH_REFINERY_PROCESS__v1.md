# A2_GRAPH_REFINERY_PROCESS__v1
Status: PROPOSED / V4 A2 REFINERY PROCESS
Date: 2026-03-17
Role: Repo-held process for graph-backed A2 high-entropy intake and refinement
Supersedes: `A2_HIGH_ENTROPY_INTAKE_PROCESS__v1.md` and `A2_MID_REFINEMENT_PROCESS__v1.md`

## 1) Purpose
This process governs the V4 graph-backed A2 refinery.

It exists so a fresh thread can:
- bootstrap from this repo-held process document
- ingest high-entropy source documents into the A2-3 outer graph
- refine and reduce through A2-2 with contradiction preservation
- selectively promote to A2-1 kernel under strict admission
- produce a persistent, queryable, updatable nested graph
- avoid mutating active A2-1 kernel memory without explicit promotion

Key upgrade from V3:
- batches are **graph nodes** with `trust_zone` and `admissibility_state`, not flat markdown
- contradictions are **explicit graph edges**, not prose in a markdown section
- lineage is **traceable through graph edges**, not through file naming conventions
- the entire refinery is **re-runnable** — later passes refine earlier nodes

## 2) Governing Inputs
Before running this process, a fresh thread should read these files in order:

1. This document
2. `system_v4/skills/a2_graph_refinery.py` (the refinery engine API)
3. `system_v4/skills/v4_graph_builder.py` (the underlying graph schema)
4. `system_v3/specs/07_A2_OPERATIONS_SPEC.md` (A2 operating doctrine — still valid)
5. `system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md` (admission law — still valid)
6. `system_v3/a2_state/A2_BRAIN_SLICE__v1.md` (current A2 understanding snapshot)
7. `system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md` (known term conflicts)

## 3) Source Roots
Primary source roots for ingestion, in priority order:

**Priority 1 — Core V4 design material (most needed info):**
- `core_docs/v4 upgrades/` — external systems research incl. `lev_nonclassical_runtime_design_audited.md`, graph suggestions, thread context extracts
- `core_docs/upgrade docs/` — bootpacks (Thread A v2.60, Thread B v3.9.13), 9 upgrade extraction passes, directed extraction Q&As, `jp graph prompt!!.txt`
- `work/audit_tmp/` — Codex's V4 build waves, `SYSTEM_V4_PREMATURE_DRAFT__2026_03_17` with graph/slice compiler drafts, test profiles

**Priority 2 — System architecture (self-understanding):**
- `system_v3/specs/` — all spec documents (layer law, constraints, protocols)
- `system_v3/tools/` — all tool scripts (agents, automations, skills)
- `system_v3/a2_state/` — A2 owner surfaces (brain slice, term conflicts, admission rules)
- `system_v3/a1_state/` — A1 state (exists but incomplete)

**Priority 3 — High-entropy fuel:**
- `core_docs/a2_feed_high entropy doc/` — raw high-entropy threads
- `core_docs/a1_refined_Ratchet Fuel/` — refined fuel batches

**Priority 4 — Prior V3 refinery output:**
- `system_v3/a2_high_entropy_intake_surface/` — 421 existing batches (may contain useful refined material)

Rule:
- process Priority 1 first — this is where the V4 design decisions live
- process `sims/` separately from theory/doc extraction (same rule as V3)

## 4) The Three Graph Layers

### A2-3 (Outer Graph) — High-Entropy Intake
- `trust_zone = "A2_3_INTAKE"`
- `admissibility_state = "PROPOSAL_ONLY"`
- Purpose: raw compression, source-mapping, clustering
- Each source document becomes a `SOURCE_DOCUMENT` node
- Each extracted concept becomes an `EXTRACTED_CONCEPT` node
- Connected by extraction-mode edges

### A2-2 (Mid Graph) — Reduction & Contradiction
- `trust_zone = "A2_2_CANDIDATE"`
- `admissibility_state = "PROPOSAL_ONLY"`
- Purpose: narrow, de-duplicate, preserve contradictions
- Strongest A2-3 concepts get promoted with `REFINED_INTO` lineage edges
- Contradictions between concepts get explicit `CONTRADICTS` edges
- Redundant A2-3 nodes are NOT deleted — they stay in the outer graph

### A2-1 (Kernel Graph) — Selective Promotion
- `trust_zone = "A2_1_KERNEL"`
- `admissibility_state = "ADMITTED"`
- Purpose: active control memory, innermost torus
- Only concepts that pass full promotion review reach this layer
- Connected to A2-2 sources by `PROMOTED_TO_KERNEL` edges
- This layer is small and tightly controlled

## 5) Extraction Modes
Each ingestion pass must declare ONE extraction mode:

| Mode | Purpose | Creates |
|------|---------|---------|
| `SOURCE_MAP_PASS` | Map what a document contains | Structure/content cluster nodes |
| `TERM_CONFLICT_PASS` | Find conflicting term definitions | Term nodes + `CONTRADICTS` edges |
| `ENGINE_PATTERN_PASS` | Extract engine/loop/cycle patterns | Pattern nodes |
| `MATH_CLASS_PASS` | Classify mathematical structures | Math-class nodes |
| `QIT_BRIDGE_PASS` | Map QIT connections | Bridge nodes |
| `PERSONALITY_ANALOGY_PASS` | Extract personality/Rosetta analogies | Analogy nodes |
| `CONTRADICTION_REPROCESS_PASS` | Re-examine existing contradictions | Updated `CONTRADICTS` edges |

Rule: do not mix extraction modes in one batch. One batch = one mode.

## 6) Processing Order
This is a looping process, not a one-pass extraction.

### First Full Pass: V4 Design Material (Priority 1)
1. Run `SOURCE_MAP_PASS` on all `core_docs/v4 upgrades/` documents
2. Run `SOURCE_MAP_PASS` on all `core_docs/upgrade docs/` documents (bootpacks, extraction passes)
3. Run `ENGINE_PATTERN_PASS` on `lev_nonclassical_runtime_design_audited.md` and bootpacks
4. Run `SOURCE_MAP_PASS` on key `work/audit_tmp/` directories (SYSTEM_V4_PREMATURE_DRAFT, v4_build_waves)
5. Run `TERM_CONFLICT_PASS` across the resulting A2-3 graph to find design tensions

### Second Full Pass: System Self-Understanding (Priority 2)
6. Run `SOURCE_MAP_PASS` on all `system_v3/specs/` documents
7. Run `SOURCE_MAP_PASS` on all `system_v3/tools/` scripts
8. Run `ENGINE_PATTERN_PASS` on system docs that define loops or cycles
9. Run `TERM_CONFLICT_PASS` to find tensions between V4 design intent and V3 implementation

### Third Full Pass: High-Entropy Fuel (Priority 3)
10. Run `SOURCE_MAP_PASS` on `core_docs/` fuel documents
11. Run `MATH_CLASS_PASS` on documents with mathematical content
12. Run `QIT_BRIDGE_PASS` on documents with physics/QIT connections

### Fourth Full Pass: Prior V3 Refinery Output (Priority 4)
13. Run `SOURCE_MAP_PASS` on the strongest V3 `BATCH_refinedfuel_*` directories
14. Run `CONTRADICTION_REPROCESS_PASS` to merge all contradiction layers

### Ongoing: Refinement and Promotion
15. After each major pass, review the A2-3 outer graph for promotion candidates
16. Promote the strongest to A2-2 with contradiction preservation
17. Selectively promote to A2-1 kernel only with explicit justification

## 7) Batch Packaging Rule
Each bounded processing step should produce one batch via `A2GraphRefinery.ingest_document()`.

Batch ID format: `BATCH_V4_{extraction_mode}_{subject}_{NNN}`

Example: `BATCH_V4_SOURCE_MAP_specs_zip_protocol_001`

The refinery automatically maintains a batch index at:
`system_v4/a2_state/refinery_batch_index.json`

## 8) Graph Persistence
The refinery saves to:
- `system_v4/a2_state/graphs/system_graph_a2_refinery.json` (Pydantic model)
- `system_v4/a2_state/graphs/system_graph_a2_refinery.graphml` (GraphML for analysis)

Both are overwritten on each save. The graph is cumulative — it grows with each batch.

## 9) Compression Rule (Same as V3)
Do not:
- copy whole source docs into node descriptions
- produce giant omnibus nodes
- dump full text for convenience

Do:
- compress into concept nodes
- cluster related concepts
- preserve contradictions as explicit edges
- keep concept nodes reusable for later passes

## 10) Mutation Rule (Same as V3)
Do not:
- modify A2-1 kernel nodes without explicit promotion justification
- treat A2-3 or A2-2 nodes as active control memory
- silently collapse contradictions

Only:
- add new nodes and edges
- update promotion_status on existing batches
- promote through explicit `promote_to_a2_2()` or `promote_to_kernel()` calls

## 11) Response Contract for Fresh Threads
Any thread following this process should report after each bounded step:
- current phase and pass number
- what document(s) were read
- what batch was produced (batch_id)
- how many nodes/edges were added
- current layer totals (A2-3 / A2-2 / A2-1 counts)
- what the next step will do

## 12) Re-Entry and Update Rule
As understanding improves:
- new extraction passes can be run on previously ingested documents
- existing A2-3 nodes are not replaced — new extractions add alongside
- A2-2 refined concepts may be superseded by later refinements
- the A2-1 kernel can grow but should remain small and tightly justified
- the graph is the living, updatable understanding substrate
