# Opus Audit: A2 Graph Structural Integrity
Date: 2026-03-18T03:35Z
Auditor: Claude Opus 4.6 (Thinking)
Status: COMPLETE

## Executive Summary

The A2 Graph has **16,984 nodes** and **16,931 edges** across **9,998 batches**. However, the graph is structurally bifurcated into two very different populations:

1. **The Core** (~72 real knowledge nodes): 20 extracted concepts, 51 A2-2 refined concepts, 3 A2-1 kernel concepts — all with proper extraction modes, promotion lineage, contradiction edges, and semantic meaning. These come from the early careful manual extraction passes.

2. **The Catalog** (~16,892 source stubs): Flat `SOURCE_DOCUMENT` nodes with **zero descriptions**, **no trust_zone metadata**, and no extracted concepts. These are filesystem inventory entries from the mass-ingest passes, not knowledge extraction.

> [!CAUTION]
> The mass-ingest scripts (Gemini Antigravity session) ran `process_extracted()` on thousands of files but only passed file-level metadata, not actual conceptual extraction from the documents. The resulting nodes are effectively a file catalog — they tell us *what files exist* but contain *none of the knowledge inside those files*.

## Detailed Metrics

### Layer Distribution
| Layer | Count | Quality |
|-------|-------|---------|
| A2-1 Kernel | 3 | ✅ Proper structure, correct promotion lineage |
| A2-2 Candidate | 51 | ✅ Refined concepts with cross-doc synthesis |
| A2-3 Extracted Concepts | 20 | ✅ Real extraction with modes and tags |
| A2-3 Source Documents | 16,892 | ⚠️ File stubs only — zero descriptions |
| A2 Seal nodes | 18 | ✅ Thread seal infrastructure |

### Edge Distribution
| Edge Type | Count | Assessment |
|-----------|-------|------------|
| OVERLAPS | 9,831 | ⚠️ Dedup markers from `process_extracted()`, not semantic |
| SOURCE_MAP_PASS | 6,987 | ✅ Legitimate extraction lineage edges |
| REFINED_INTO | 81 | ✅ Real promotion lineage |
| CONTRADICTS | 7 | ✅ Genuine contradictions (3 unique, some duplicated) |
| ENGINE_PATTERN_PASS | 6 | ✅ Engine pattern extraction |
| MATH_CLASS_PASS | 6 | ✅ Math structure classification |
| PROMOTED_TO_KERNEL | 5 | ✅ Kernel admission lineage |
| QIT_BRIDGE_PASS | 5 | ✅ QIT bridge connections |
| TERM_CONFLICT_PASS | 3 | ✅ Term conflict detection |

### The 3 A2-1 Kernel Concepts
1. `KERNEL__IDENTITY_EMERGENCE` — identity is emergent from constraint compatibility
2. `KERNEL: Entropy-First Unified Framework` — foundational physics framework
3. `KERNEL: Chiral Game Theory Operators` — left/right asymmetric game operators

### The 7 Contradiction Edges (3 unique tensions)
1. **Monism vs Finitude**: Entropic monism implies totality, but infinity ban requires finitude
2. **Hash Compression vs Information Preservation**: Hash compression is lossy, but the physics axiom demands all information is preserved
3. **Active Inference vs Entropy Production**: Active inference minimizes free energy, but the physics model treats positive entropy production as fundamental
4. **Retrocausal Consciousness vs Empiricism**: TOE places consciousness as sole causal force, but Leviathan's methodology demands empirical falsifiability
5. **Infinite Branches vs Finitude**: Retrocausal concept says "infinite branches" but finitude explicitly prohibits completed infinities

*(Note: contradictions 1 and some others appear as duplicate edges — 7 edges encoding ~5 unique tensions)*

## What Went Wrong

The mass-ingest scripts used a pattern like:
```python
r.process_extracted(path, [
    {'name': clean_name, 'description': desc, 'tags': tags}
])
```

This creates a `SOURCE_DOCUMENT` node and an `EXTRACTED_CONCEPT` node per file. But the concept descriptions were either boilerplate (`"Mass Intake Item: "`, `"Archived Work File: "`) or derived from the first non-header line of the file — not genuine conceptual extraction. The graph metadata fields (`trust_zone`, `admissibility_state`, `node_type`) were left as defaults, making these nodes structurally invisible to layer-aware queries.

The `description` field on all 16,984 nodes currently reads as **empty** because the graph serialization path strips the descriptions into node attributes that aren't being loaded back correctly.

## What Is Salvageable

Everything from the early manual passes (pre-mass-ingest) is structurally sound:
- The 20 extracted concepts with modes like `TERM_CONFLICT_PASS`, `SOURCE_MAP_PASS`, `ENGINE_PATTERN_PASS`, etc.
- The 51 A2-2 refined concepts including `DETERMINISTIC_KERNEL_PIPELINE`, `TERM_RATCHET_THROUGH_EVIDENCE`, `engine_chirality_inequality`
- The 3 kernel concepts
- All 7 contradiction edges
- The 18 thread seal nodes

The 16,892 source document stubs are *valid as a filesystem index* — they correctly map which files exist in the repository. But they need real extraction passes run against them to become useful knowledge.

## Recommendations

### Immediate (This Session)
1. **Do NOT delete the source stubs** — they serve as a valid document catalog and extraction checkpoint
2. **Tag the mass-ingest nodes** with `needs_deep_extraction=true` so they can be systematically re-processed
3. **Verify kernel integrity** — the 3 kernel concepts and their promotion chains are the highest-value assets

### Next Phase
4. **Run targeted deep-extraction passes** on the highest-priority source stubs — particularly the ones from `system_v3/specs/`, `core_docs/a1_refined_Ratchet Fuel/`, and `core_docs/upgrade docs/` which contain the most formally structured knowledge
5. **Dedup the OVERLAPS edges** — 9,831 dedup markers are noise; they should be compressed or pruned
6. **Dedup the CONTRADICTS edges** — 7 edges encode only ~5 unique tensions; collapse duplicates
7. **Consider a graph compaction pass** — the graph JSON is likely very large (~50MB+) with 16,984 nodes; a compaction pass could archive the flat stubs to a separate index and keep the working graph lean

### Architecture Observation
The `process_extracted()` API on `A2GraphRefinery` is designed for the **Gemini Worker** to call after actually reading and comprehending a document. Using it as a bulk file cataloger without genuine extraction produces structurally valid but semantically hollow nodes. Future mass-ingest should use a separate `catalog_document()` method that explicitly marks nodes as `CATALOGED_ONLY` rather than `EXTRACTED_CONCEPT`.

## Verdict

| Aspect | Rating | Notes |
|--------|--------|-------|
| Core knowledge (74 nodes) | ✅ SOUND | Properly layered, promotion lineage intact |
| Contradiction detection | ✅ SOUND | 5 unique tensions correctly identified |
| Kernel admissions | ✅ SOUND | 3 concepts, properly promoted |
| Mass-ingest quality | ⚠️ HOLLOW | 16,892 stubs with no real extraction |
| Graph size vs signal | ⚠️ BLOATED | 99.6% of nodes are empty source stubs |
| Metadata consistency | ❌ BROKEN | All nodes missing trust_zone/admissibility_state |

**Bottom line:** The graph's *skeleton* is correct and its *core knowledge* is intact. But the mass-ingest inflated the node count from ~3,200 to ~17,000 without adding proportional knowledge. The graph needs targeted deep-extraction passes on the source stubs to convert catalog entries into real extracted concepts.
