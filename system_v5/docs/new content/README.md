# New Content Drop Zone

This folder is for preprocessed incoming material before it is promoted into the new docs stack.

Read this with:
- `../00_manifest.md` for the promoted stack
- `../CURRENT_DOCS_MAP.md` for topic ownership and processing state

Intended use:
- paste or dump raw source-derived notes here
- normalize terminology
- strip duplicates
- extract only the established math terms and source facts
- move stable synthesis into `new docs/`

Suggested subfolders:
- `preprocessed/` — normalized source notes
- `raw/` — optional raw dumps if needed later
- `bridge/` — temporary glue between raw notes and doc synthesis

## Processing Ladder

Use these states consistently:

1. `raw/` or ad hoc intake
   - unprocessed source capture
   - may contain duplicates, mixed terminology, and unresolved framing
2. `preprocessed/`
   - cleaned enough to mine facts, terminology, and candidate structure
   - still not promoted doctrine
3. top-level `new docs/*.md`
   - promoted synthesis or explicit audit/plan/working surface
4. `canonical` top-level doc
   - best current owner surface for that topic

Short rule:
- if a point only exists here, it is still in intake
- if a canonical top-level doc exists, that doc outranks this folder

Current preprocessed digests:

| Digest | Main topic | Likely promoted destination |
|---|---|---|
| `preprocessed/00_pca_qpca_source_digest.md` | PCA / QPCA / spectral compression | `01_pca_qpca_alignment.md`, `02_compression_to_density_matrix_map.md`, `05_research_index.md` |
| `preprocessed/01_entropy_layer_source_digest.md` | entropy-layer material | `06_entropy_sweep_protocol.md`, `AXIS_AND_ENTROPY_REFERENCE.md` |
| `preprocessed/02_model_math_geometry_source_digest.md` | model → math → geometry chain | `07_model_math_geometry_sim_plan.md`, `CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md` |
| `preprocessed/03_aligned_sim_backlog_source_digest.md` | build order and dependency collapse | `08_aligned_sim_backlog_and_build_order.md` |
| `preprocessed/04_foundation_research_digest.md` | foundation research inventory | `09_research_inventory_and_foundations.md` |
| `preprocessed/05_cross_domain_equivalence_source_digest.md` | cross-domain mappings | `10_cross_domain_equivalence_map.md` |
| `preprocessed/06_mass_equivalence_engine_digest.md` | mass-equivalence cluster | `11_mass_equivalence_engine.md` |
| `preprocessed/07_mimetic_meme_manifold_boot_dictionary_digest.md` | boot/salience language layer | `12_mimetic_meme_manifold_harness.md` |
| `preprocessed/08_mimetic_meme_manifold_macro_corpus_digest.md` | macro corpus synthesis | `13_mimetic_meme_manifold_source_map.md`, `14_mimetic_meme_manifold_canonical_synthesis.md` |

## What Counts As "Not Fully Processed"

A doc or note is still not fully processed when any of these are true:
- it only exists in `new content/`
- it mainly preserves source language instead of system language
- it has not been routed to a clear top-level owner doc
- its claims are only present in session notes, audits, or handoff material
- it is still listed as a gap in `../V5_CONTENT_GAP_ANALYSIS.md`

Rule:
- nothing here is canonical until it has been promoted into `new docs/`

Do not use this folder alone for final summaries, implementation guidance, or doctrine claims.
