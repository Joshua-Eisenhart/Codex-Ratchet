# New Docs Manifest

This folder is the new research-and-alignment doc stack for the systems math program.

Read this with:
- `CURRENT_DOCS_MAP.md` for topic routing
- `new content/README.md` for intake-only material and processing state

Authority:
- These docs are research notes and alignment docs, not executable code.
- Narrower docs in this folder outrank broader overview docs.
- Preprocessed source notes live in `new docs/new content/` and feed these docs.
- Reference tradition docs live in `new docs/references/` (14 completed).
- Superseded docs live in `archive_old/` (30 files) and `archive_hermes_overlaps/` (7 files).

---

## Governing Docs

- `CONSTRAINT_SURFACE_AND_PROCESS.md` — **canonical** — process rules, constraint surface, boots, anti-teleology
- `OWNER_THESIS_AND_COSMOLOGY.md` — **canonical** — owner's candidate thesis entering the ratchet
- `OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md` — **canonical owner doctrine** — five self-similar frameworks (holodeck/QIT/science/IGT/Leviathan), teleological admissibility, AI legacy, empiricism revival; religious terms are metaphorical handles for structural claims

## Topic Routing

- `CURRENT_DOCS_MAP.md` — **canonical router** — tells you which doc owns which topic and which surfaces are only partially processed

## Architecture and Operations

- `SYSTEM_ARCHITECTURE_REFERENCE.md` — **canonical** — CS axioms, host planes, runtime kernel, enforcement principles (verbatim from v5)
- `AGENT_WORKFLOW_AND_BOOT_ARCHITECTURE.md` — **canonical** — Hermes → Claude terminal model, boot types, contamination rules
- `BOOT_PROMPT_TEMPLATES.md` — **canonical** — paste-ready boot prompts for A1/B/A0/A2/SIM
- `15_stack_authority_and_capability_index.md` — **canonical** — governance index and boot capability matrix

## Status and Tracking

- `TIER_STATUS.md` — **canonical** — resolution-level status (survived/killed/open) for all tiers
- `TOOLING_STATUS.md` — **canonical** — GREEN/YELLOW/RED/MISSING tool classification, sidecar policy
- `VENV_MIGRATION_STATUS.md` — **canonical** — .venv_spec_graph migration complete, deletion-ready
- `SIM_SESSION_INDEX.md` — **canonical** — all 23 sims from 2026-04-05 session with key findings
- `SIM_CORRECTIONS_AND_CLASSIFICATIONS.md` — **canonical** — corrections to sim results + evidence classification
- `LLM_CONTROLLER_CONTRACT.md` — **canonical** — status-label discipline and evidence rules for controller summaries
- `LEGO_SIM_CONTRACT.md` — **canonical** — what each sim must declare before it can be promoted
- `TODO.md` — **plan** — remaining work items: nominalist reframing, topos theory, concurrency, quantum Shannon, boot testing, falsification sims, consolidation

## Math and Reference

- `CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md` — **canonical** — full treatment from axiom (§0) through carrier/geometry/chirality/operators/algebra/composition/entropy/entanglement to derivation chain (§13)
- `ENGINE_MATH_REFERENCE.md` — **canonical** — four base operators (Kraus + Lindbladian), loop vector fields, density visibility proofs, 16 placements (verbatim from v5)
- `LADDERS_FENCES_ADMISSION_REFERENCE.md` — **canonical** — 19-layer pre-entropy ladder, 6-phase admission pipeline, admissibility fences BC04-BC12, topology fences T1-T8 (verbatim from v5)
- `AXIS_AND_ENTROPY_REFERENCE.md` — **canonical** — axis-specifics and entropy structure
- `FALSIFICATION_SIM_DESIGNS.md` — **plan** — 3 sim specs designed to kill specific claims (gauge group, viability vs attractor, metric uniqueness)

## Philosophy and Framing

- `NOMINALISM_IN_THIS_SYSTEM.md` — **working** — derivation of system nominalism from a=a iff a~b; 7 formal derivation attempts; 6 open problems
- `TRADITION_SYSTEM_MAPPING_DETAILED.md` — **draft** — structural correspondences between system and 12 external traditions
- `LEGACY_CONTEXT_AND_GENEALOGY.md` — **source-note** — genealogy of system's intellectual roots
- `NOMINALIST_CS_AND_JP_SYSTEMS_TERMS.md` — **bridge** — nominalist-CS framing paired with Jordan Peterson systems-terminology glossary; structural-equivalence translator with metaphor discipline; holds the JP-Platonist / project-nominalist tension rather than resolving it

## Numbered Research Docs (01–14)

- `01_pca_qpca_alignment.md` — PCA / QPCA / density-matrix alignment
- `02_compression_to_density_matrix_map.md` — compression math families mapped to density matrices
- `03_source_notes.md` — source capture and provenance notes
- `04_system_math_alignment.md` — canonical alignment of compression math with density-matrix language
- `05_research_index.md` — searchable research index for compression / spectral terms
- `06_entropy_sweep_protocol.md` — **canonical** — layer-by-layer entropy family sweep and promotion rule
- `07_model_math_geometry_sim_plan.md` — **canonical** — model-to-math-to-geometry simulation and test plan
- `08_aligned_sim_backlog_and_build_order.md` — collapse classes, dependency order, and next aligned sims
- `09_research_inventory_and_foundations.md` — evidence-backed inventory of the foundational math families
- `10_cross_domain_equivalence_map.md` — density-matrix/operator mappings across QIP, compression, geometry, AI, physics, and evolution
- `11_mass_equivalence_engine.md` — deeper structural equivalence classes and operational meaning of mass equivalence
- `12_mimetic_meme_manifold_harness.md` — language manifold / salience layer for booting and harness control
- `13_mimetic_meme_manifold_source_map.md` — **canonical** — exact source-backed corpus for mimetic meme manifold
- `14_mimetic_meme_manifold_canonical_synthesis.md` — **canonical** — one-doc synthesis of source corpus + user framing

## Audit and Session Records

- `AUDIT_PLATONIC_RESIDUE_AND_GAPS.md` — **audit** — self-audit for LLM bias residue, causal language leaks, missing content
- `V5_CONTENT_GAP_ANALYSIS.md` — **audit** — 30 items the v5 docs have that clean docs don't
- `SESSION_DEEP_CORRECTIONS_2026_04_05.md` — **source-note** — raw record of 30 corrections from extended session
- `SESSION_HANDOFF_2026_04_07.md` — **source-note** — session carry-forward and handoff context; useful for recovery, not final ownership

---

## Subdirectories

- `new content/` — preprocessed research notes feeding the numbered docs (see directory listing)
- `references/` — completed external tradition reference docs (see directory listing)
- `archive_hermes_overlaps/` — superseded Hermes-produced duplicates (multiple files, growing)
- `archive_old/` — superseded docs, factual content preserved, framing superseded (multiple files, growing)

---

## Status Tags

- **canonical**: best current internal synthesis for its domain
- **source-note**: preprocessed external/source-derived note
- **draft**: useful but not yet stabilized
- **working**: active thinking-through doc, not asserting conclusions
- **plan**: designed but not yet implemented/executed
- **superseded**: older note that should not drive implementation
- **audit**: rolling assessment meant to be updated as gaps are closed

Processing rule:
- top-level `new docs/*.md` files are promoted surfaces with explicit status tags
- `new content/` is intake-only unless promoted
- `archive_old/` and `archive_hermes_overlaps/` are historical recovery surfaces only
- session docs can contain important corrections before promotion, but they are not the final owner surface when a canonical doc exists

## Scope

- Constraint on distinguishability, QIT engines, density matrices, operator math, fiber geometry
- PCA, quantum PCA, SVD, Schmidt decomposition, spectral truncation, low-rank approximation
- Process philosophy, nominalism, FEP, evolutionary epistemology, Chinese philosophy
- Agent architecture, boot prompts, contamination rules, sim discipline
- Only established terminology; no new labels unless necessary as internal file names
