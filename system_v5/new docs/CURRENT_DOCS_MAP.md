# Current Docs Map

Purpose: this is the routing layer for `system_v5/new docs/`.
Use it to answer two questions quickly:

1. Which doc owns a topic right now?
2. Is that doc promoted, still being worked through, or only intake material?

---

## Processing States

| State | Meaning | Safe use |
|---|---|---|
| **canonical** | Best current synthesized surface for that topic | Safe starting point for summaries, handoffs, and planning |
| **working** | Active thinking-through doc with open unresolved parts | Use with canonical docs, not by itself |
| **draft** | Useful structure, but not yet stabilized | Use cautiously; expect rewrites |
| **audit** | Gap finder, residue checker, or reconciliation surface | Use to find problems, not as final doctrine |
| **plan** | Intended work or proposed build order | Not evidence of execution |
| **source-note** | Processed source capture or genealogy note | Useful provenance; not promoted doctrine |
| **intake-only** | `new content/` material not yet promoted | Do not treat as settled |
| **archived** | Superseded or overlap material | Read only for history or fact recovery |

Short rule: if a topic matters and there is a **canonical** doc for it, start there.

---

## Fast Routes

### If you need the system core

Start with:
- `CONSTRAINT_SURFACE_AND_PROCESS.md`
- `OWNER_THESIS_AND_COSMOLOGY.md`
- `SYSTEM_ARCHITECTURE_REFERENCE.md`

Then use:
- `AGENT_WORKFLOW_AND_BOOT_ARCHITECTURE.md`
- `15_stack_authority_and_capability_index.md`

### If you need live status, not theory

Start with:
- `TIER_STATUS.md`
- `SIM_CORRECTIONS_AND_CLASSIFICATIONS.md`
- `SIM_SESSION_INDEX.md`

Then check:
- `LLM_CONTROLLER_CONTRACT.md`
- `TOOLING_STATUS.md`
- `MIGRATION_REGISTRY.md`

### If you need the math spine

Start with:
- `CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md`
- `ENGINE_MATH_REFERENCE.md`
- `LADDERS_FENCES_ADMISSION_REFERENCE.md`

Then expand into:
- `AXIS_AND_ENTROPY_REFERENCE.md`
- `06_entropy_sweep_protocol.md`
- `07_model_math_geometry_sim_plan.md`

### If you need topic lineage or source provenance

Start with:
- `03_source_notes.md`
- `09_research_inventory_and_foundations.md`
- `LEGACY_CONTEXT_AND_GENEALOGY.md`

Then use:
- `V5_CONTENT_GAP_ANALYSIS.md`
- `SESSION_DEEP_CORRECTIONS_2026_04_05.md`

### If you need partially processed material

Read in this order:
- `new content/README.md`
- `new content/preprocessed/README.md`
- the specific preprocessed digest you need

Do not treat intake material as canon until its content is promoted into a top-level doc in `new docs/`.

---

## Topic Ownership

| Topic | Primary docs | Secondary docs | Processing read |
|---|---|---|---|
| Constraint surface, admissibility, anti-teleology | `CONSTRAINT_SURFACE_AND_PROCESS.md` | `LADDERS_FENCES_ADMISSION_REFERENCE.md`, `ENFORCEMENT_AND_PROCESS_RULES.md` | promoted core |
| Owner thesis and cross-domain claim | `OWNER_THESIS_AND_COSMOLOGY.md` | `10_cross_domain_equivalence_map.md`, `11_mass_equivalence_engine.md` | promoted core plus research overlays |
| CS translation, runtime kernel, host planes | `SYSTEM_ARCHITECTURE_REFERENCE.md` | `EXPLICIT_CONTROLLER_MODEL.md`, `AGENT_WORKFLOW_AND_BOOT_ARCHITECTURE.md` | promoted architecture |
| Boot roles, agent workflow, contamination | `AGENT_WORKFLOW_AND_BOOT_ARCHITECTURE.md` | `BOOT_PROMPT_TEMPLATES.md`, `15_stack_authority_and_capability_index.md` | promoted operations |
| Formal math chain from constraints to entropy/entanglement | `CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md` | `ENGINE_MATH_REFERENCE.md`, `AXIS_AND_ENTROPY_REFERENCE.md` | promoted math spine |
| Operator math, terrain math, placements, loop geometry | `ENGINE_MATH_REFERENCE.md` | `AXIS_AND_ENTROPY_REFERENCE.md`, `V5_CONTENT_GAP_ANALYSIS.md` | promoted, but some deeper v5 details still tracked as gaps |
| Axis stack and entropy placement | `AXIS_AND_ENTROPY_REFERENCE.md` | `06_entropy_sweep_protocol.md`, `TIER_STATUS.md` | mixed: promoted plus open areas |
| Sim admission, classification, evidence discipline | `LEGO_SIM_CONTRACT.md`, `LLM_CONTROLLER_CONTRACT.md` | `SIM_CORRECTIONS_AND_CLASSIFICATIONS.md`, `TOOL_MANIFEST_AUDIT.md` | promoted governance |
| Live sim truth and resolution status | `TIER_STATUS.md` | `SIM_SESSION_INDEX.md`, `SIM_CORRECTIONS_AND_CLASSIFICATIONS.md` | current status surfaces |
| Tool stack and runtime readiness | `TOOLING_STATUS.md` | `VENV_MIGRATION_STATUS.md`, `TOOL_MANIFEST_AUDIT.md` | current status surfaces |
| Torch migration state | `MIGRATION_REGISTRY.md` | `PYTORCH_RATCHET_BUILD_PLAN.md` | registry is current tracker; build plan is broader program doc |
| Research compression / density-matrix cluster | `01_pca_qpca_alignment.md`, `02_compression_to_density_matrix_map.md`, `04_system_math_alignment.md` | `05_research_index.md` | promoted research cluster |
| Foundational research inventory | `09_research_inventory_and_foundations.md` | `03_source_notes.md`, `05_research_index.md` | promoted plus provenance |
| Mimetic / language manifold layer | `12_mimetic_meme_manifold_harness.md`, `14_mimetic_meme_manifold_canonical_synthesis.md` | `13_mimetic_meme_manifold_source_map.md` | promoted cluster |
| External-tradition mapping | `TRADITION_SYSTEM_MAPPING_DETAILED.md` | `LEGACY_CONTEXT_AND_GENEALOGY.md` | still draft / comparative, not ownership surface |
| Residue, missing content, reconciliation | `AUDIT_PLATONIC_RESIDUE_AND_GAPS.md`, `V5_CONTENT_GAP_ANALYSIS.md` | `SESSION_DEEP_CORRECTIONS_2026_04_05.md` | audit surfaces only |

---

## Partially Processed Surfaces

These are the places most likely to confuse a new reader if they are treated as settled:

| Surface | Why it confuses | How to use it |
|---|---|---|
| `new content/` | Preprocessed intake sits next to promoted docs in the same broad tree | Treat as feeder material only |
| `03_source_notes.md` | Provenance is mixed with synthesis cues | Use for source recovery, not final framing |
| `TRADITION_SYSTEM_MAPPING_DETAILED.md` | Rich comparisons can look more settled than they are | Use as a draft comparative overlay |
| `V5_CONTENT_GAP_ANALYSIS.md` | It is a gap list, not a finished map of the current stack | Use to find missing topics and destination docs |
| `SESSION_DEEP_CORRECTIONS_2026_04_05.md` and session handoffs | Important corrections live here before full promotion | Use as correction intake, then verify the promoted destination doc |

---

## What Not To Do

- Do not summarize the system from `new content/` alone.
- Do not treat `plan`, `audit`, or `source-note` docs as if they were current truth.
- Do not assume a topic is missing just because it is not easy to find in one overview doc.
- Do not use a session record as the final owner surface if a promoted top-level doc exists.

---

## Minimal Reading Order

For a new pass over the stack:

1. `00_manifest.md`
2. `CURRENT_DOCS_MAP.md`
3. `CONSTRAINT_SURFACE_AND_PROCESS.md`
4. `SYSTEM_ARCHITECTURE_REFERENCE.md`
5. `TIER_STATUS.md`
6. Topic-specific canonical docs only after that
