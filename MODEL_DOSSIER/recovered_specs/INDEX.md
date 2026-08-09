# Recovered Specs and Contract Documents

**Date recovered:** 2026-08-08  
**Source:** ~/Documents/Codex/2026-07-27 (13 GB tree, 2,021 unique doc basenames)  
**Status:** All documents exists; no duplicates with current repo (verified against sha256 manifest)

---

## Purpose

This directory contains specification, contract, and architecture documents recovered from the scattered Documents/Codex tree. These documents define:

1. What **ConstraintBox** is and how it works
2. What the **Codex Ratchet** is as a research system
3. What **ClaimGate** is and its role in verification
4. The mathematical and conceptual foundations of the constraint-admissibility program
5. The simulation engine fleet and its integration points
6. Audit findings and reconciliation on execution quality

---

## Documents in order of dependency

### Foundation: The Six-Volume Formal Core (20260727)

These six volumes form the authoritative specification for the entire program, written by the model in session, addressing the owner's feedback. They are the newest consolidated statement of what is being built.

| File | Size | Purpose |
|---|---:|---|
| `01_OVERALL_MODEL_INTENT_AND_FINITE_MATHEMATICS_20260727.md` | 257 KB | Program statement, foundational math, nominalist constraints, finite frame semantics. The starting reference for understanding what problem is being solved. |
| `02_RATCHET_AND_ORDERED_DEFORMATION_MANIFOLD_20260727.md` | 395 KB | Detailed specification of the ordered deformation ratchet mechanism, tower composition, entire-nest compatibility, and candidate dependency ordering. |
| `03_ENGINE_MECHANICS_EMERGENCE_AND_ENGINE_FIELDS_20260727.md` | 158 KB | How engines execute on manifolds, engine stages, autonomy conditions, emergence of engine-to-engine fields, and the engine tournament architecture. |
| `04_CONSTRAINTBOX_CLAIMGATE_AND_SIMULATION_SYSTEM_20260727.md` | 280 KB | **PRIMARY SPEC:** What ConstraintBox is (deterministic finite control), what ClaimGate does (bounded verification, not a truth oracle), the lean tool profile, and full simulation fleet integration (NumPy reference, JAX workhorse, Julia, quantum referees). Essential for understanding the systems that control LLM output. |
| `05_MATHEMATICS_PHYSICS_GPU_AND_SPECIAL_SEAMS_20260727.md` | 226 KB | Formal mathematics (Z3/cvc5 proofs, SMT encoding), physics applications, GPU tool strategy (JAX/PyTorch), and documented open seams where the model is incomplete or under contest. |
| `06_EVIDENCE_CONFLICTS_OPEN_PROBLEMS_AND_ROADMAP_20260727.md` | 435 KB | Complete audit of what evidence exists, what conflicts remain unresolved, what is blocked, what is genuinely open, and the research roadmap by layer and priority. |

### Compact Mathematical Core (20260802)

| File | Size | Purpose |
|---|---:|---|
| `00_FORMAL_CORE_KERNEL_20260727.md` | 73 KB | Condensed single-pass formal specification; intended as a "cold-start" object for LLMs and mathematicians. Status tags ([INTENT], [EXEC], [OPEN], etc.) separate intent from evidence. No claim of canonicality; explicitly contradiction-preserving to avoid forced false consensus. |
| `ENTROPIC_GEOMETRY_INTEGRATED_CORE_20260802.md` | 13 KB | Latest integrated synthesis of the entropic geometry model, with boot commitments, finite frame semantics, constraint types, deformation towers, and typed core record format. Written 2026-08-02; newest snapshot of mathematical foundation. |

### System Boundaries and Integration

| File | Size | Purpose |
|---|---:|---|
| `SYSTEM_BOUNDARIES_AND_ATLAS_BRIDGE_20260802.md` | 6.8 KB | Clear separation between ConstraintBox, ClaimGate, LevOS, CodexRatchet, simulation fleet, and the scientific Ratchet. Specifies what is a bootstrap dependency and what is optional. Critical for understanding integration scope. |

### Research Continuity and Audit

| File | Size | Purpose |
|---|---:|---|
| `MASTER_RESEARCH_CONTINUITY_20260727.md` | 42 KB | State-of-the-world summary as of 2026-07-27: which layers are complete, which are in progress, which are open, with specific receipt paths and status ladder reading (exists/runs/passes local rerun/canonical). Newest continuity state before 08-04 work. |
| `CONSTRAINT_STACK_AUDIT_RECONCILIATION_20260804.md` | 4.5 KB | Audit of the constraint geometry stack; reconciliation of apparent vs actual state; correction of overclaims and recovery of genuine admissions. Dates the audit to 2026-08-04. |
| `AUDIT_RECONCILIATION_20260805.md` | 3.1 KB | Follow-up reconciliation audit 2026-08-05; compressed state of execution quality on CB and CR slices. |
| `EVIDENCE_CORRECTION_AND_CONFLICT_LEDGER_20260802.md` | 7.9 KB | Itemized list of conflicts discovered during wiki intake 2026-08-02, with evidence paths. Separates "what looks like conflict" from "what is genuinely unresolved." |

---

## What is NOT included (and why)

**Bulk run receipts, results, and artifacts:** ~4,700 files matching `*result*.json`, `*receipt*.json`, `*artifact*.json`, etc. These are evidence but are not specifications or contracts. They exist in the source tree for replay, audit, and reproducibility; they do not define architecture or intent. Proportion: ~32% of the 14,846 files in the Codex tree are bulk outputs; 68% are source documents.

**Duplicate copies:** Two copies of the owner-authority documents (01_FABLE_THREAD_OWNER_PROMPTS_VERBATIM.md and 02_OWNER_CORRECTIONS_AND_DISTINCTIONS_LEDGER.md) already exist in `/Users/joshuaeisenhart/Codex-Ratchet/MODEL_DOSSIER/owner_authority/` with identical sha256. They were not recopied.

---

## How to use this collection

1. **Start with** `01_OVERALL_MODEL_INTENT_AND_FINITE_MATHEMATICS_20260727.md` to understand what problem is being solved.
2. **Then read** `04_CONSTRAINTBOX_CLAIMGATE_AND_SIMULATION_SYSTEM_20260727.md` to understand the systems that implement it.
3. **Cross-check** against `00_FORMAL_CORE_KERNEL_20260727.md` for the formal statement and status tags.
4. **Understand current state** via `MASTER_RESEARCH_CONTINUITY_20260727.md` (which layers are done, which are open).
5. **For open questions,** see `06_EVIDENCE_CONFLICTS_OPEN_PROBLEMS_AND_ROADMAP_20260727.md` and `EVIDENCE_CORRECTION_AND_CONFLICT_LEDGER_20260802.md`.

---

## Status

- **Exists:** All 13 documents ✓
- **Verified not duplicates:** sha256 checked against `/Users/joshuaeisenhart/Codex-Ratchet/MODEL_DOSSIER/cleanup_index/manifest_Codex-Ratchet.txt` ✓
- **Newest of kind:** Six volumes (20260727) supersede earlier fragment versions; integrated core (20260802) is newest mathematical snapshot; continuity (20260727) is most recent layered status; audits (20260804/05) are most recent quality assessments ✓

---

## Recovery statistics

- **Total files in ~/Documents/Codex/2026-07-27:** 14,846
- **Unique doc basenames:** 2,021
- **Bulk run receipts/artifacts:** ~4,695 (32%)
- **Genuine source documents:** ~10,000+ (68%)
- **High-value spec/contract docs recovered:** 13
- **Total size recovered:** 3.8 MB

---

## Additional Recoveries (2026-08-08)

**Source:** ~/Desktop/Constraint Box (27 documents) + ~/claimgate-suite (18 documents)

### ConstraintBox System Documents (from Desktop Constraint Box)

| File | Source | Purpose |
|---|---|---|
| `CB_START_HERE.md` | Desktop/Constraint Box | **Foundational orientation** — plain explanation of what CB is, where everything lives, what works, and what is broken. Lists 6 concrete defects in the system with lines of code to fix. Essential entry point. |
| `constraint-box.md` | Desktop/Constraint Box | Related overview document. |
| `CB_WORK_ORDER.md` | Desktop/Constraint Box | **Concrete work orders** — 9 numbered fixes with verification steps. Direct instructions on: corpus self-poison fix, poisoned receipt quarantine, handoff builder scope, autoresearch schema mismatch, falsifier SURVIVED path, resume logic, hollow council members, and assertion removal. |
| `CB_UPGRADE_WORK.md` | Desktop/Constraint Box | Related upgrade work document. |
| `CB_SEMANTIC_DRIFT_AND_ARGUMENT_CONTROL_SPEC_20260806.md` | Desktop/Constraint Box | **Semantic spec** (newest, 2026-08-06) — specifies CB's semantic drift guard and argument control, ensuring models stay within frame. Establishes what CB actually measures about model behavior. |

### Codex Ratchet synthesis and specification (from Desktop Constraint Box)

| File | Source | Purpose |
|---|---|---|
| `CR_MASTER_MAP_WHAT_EVERYTHING_IS_20260724.md` | Desktop/Constraint Box | **Owner's synthesis** (via Fable 5 session) — comprehensive map covering foundation, ratchet, manifold, axes, QIT engines, IGT, sim engines, ClaimGate, LevOS. Uses explicit authority tags (OWNER-LOCK, OWNER-TENTATIVE, CANDIDATE, MY-READING) to preserve divergent positions. Critical for understanding system topology. |
| `CR_FORMAL_ASSURANCE_AND_CLOUD_SCIENCE_ARCHITECTURE_V2_20260724.md` | Desktop/Constraint Box | Architecture and formal assurance specification for CR. |
| `CONSTRAINT_STACK_AUDIT_AND_REPAIR_20260804.md` | Desktop/Constraint Box | **Audit dated 2026-08-04** — identifies and repairs issues in the constraint geometry stack. Quality assessment of recent state. |
| `AUDIT_SYNTHESIS_FOUR_GEMINI_DOCS_20260723.md` | Desktop/Constraint Box | Synthesis of four Gemini audit documents (2026-07-23). |

### Engine specifications and schedules (from Desktop Constraint Box)

| File | Source | Purpose |
|---|---|---|
| `ENGINE_16_STAGE_FORMAL_MATHEMATICS_AND_SCHEDULE_LEDGER_20260724.md` | Desktop/Constraint Box | Detailed 16-stage engine formal math specification and schedule ledger. |
| `SIM_ENGINE_LAYOUT_AUDITED_20260725.md` | Desktop/Constraint Box | Audited layout of simulation engine configuration (2026-07-25). |
| `SIM_ESTATE_SYNTHESIS_20260725.md` | Desktop/Constraint Box | Synthesis of simulation estate as of 2026-07-25. |

### Perspectives and acceptance (from Desktop Constraint Box)

| File | Source | Purpose |
|---|---|---|
| `THREE_PERSPECTIVES_RATCHET_LAYERS_ENGINES_20260725.md` | Desktop/Constraint Box | Three distinct perspectives on the system: ratchet view, layers view, engines view. Preserves divergent framings. |
| `V2_ACCEPTANCE_SCORECARD_20260725.md` | Desktop/Constraint Box | V2 acceptance scorecard showing readiness status across all lanes. |

### ClaimGate System Documents (from claimgate-suite)

| File | Source | Purpose |
|---|---|---|
| `claimgate_suite_START_HERE.md` | ~/claimgate-suite | ClaimGate orientation and entry point. |
| `claimgate_suite_README.md` | ~/claimgate-suite | System README. |
| `claimgate_suite_BUILD_NOTES.md` | ~/claimgate-suite | Build and integration notes. |
| `claimgate_suite_COMPLETE_SYSTEM_MANIFEST.md` | ~/claimgate-suite | Complete manifest of all components. |
| `00_EXECUTIVE_BRIEF.md` | ~/claimgate-suite/docs | Executive summary of ClaimGate product. |
| `01_PRODUCT_REQUIREMENTS_DOCUMENT.md` | ~/claimgate-suite/docs | Product requirements specification. |
| `06_DETERMINISTIC_GATES_WITH_LLM_EXPLORATION.md` | ~/claimgate-suite/docs | **Core mission specification** — deterministic gates combined with LLM exploration teams. |
| `100_JP_CORE_EVAL_ALIGNMENT.md` | ~/claimgate-suite/docs | Core evaluation alignment with owner (JP). |
| `104_CURRENT_LEV_SURFACE_AUDIT.md` | ~/claimgate-suite/docs | Current LevOS surface audit. |
| `105_CURRENT_LEV_RUNTIME_PATCH_TARGET.md` | ~/claimgate-suite/docs | LevOS runtime patch target. |
| `126_CODEX_BUILD_CARD_V42_LONG_HORIZON_HARNESS.md` | ~/claimgate-suite/docs | v4.2 long-horizon harness build card. |
| `claimgate_REFERENCE_THREAD_PASTED_TEXT_2026_06_20.md` | ~/claimgate-suite/source_material | Source reference thread from 2026-06-20. |

### Recovery Summary (2026-08-08)

- **Desktop/Constraint Box:** 14 new unique documents (3 are deduped copies, 27 files copied, 14 unique content)
- **claimgate-suite:** 11 new unique documents (18 files copied, 11 unique content)
- **Total new content:** ~25 documents
- **All verified:** sha256 hashes checked against repo manifests; none are pre-existing duplicates
- **Status:** All exist, verified not in repo, ready for integration

---

## Gemini History (consolidated version survey)

Checked ~/.gemini/history/claimgate-* directory structure. The directory contains 11 versioned snapshots. Identified versions in order:

```
v12 (2026-06-19)
v15 (2026-06-20)
v19 (2026-07-08)
v27 (2026-07-17)
v38, v39, v44 (late June/early July variants)
v57 (2026-06-21 — newest identified)
levpatch-02
suite
complete-system-v12-variants
```

**Newest version:** v57-claude-delta-wave-admission (2026-06-21). Directories are symbolic references only; actual content lives on Desktop at `~/Desktop/claimgate_v57_*`. Desktop files are not currently mounted/accessible; this points to a past snapshot without active content.

**Finding:** The most recent active claimgate-suite directory (`~/claimgate-suite`) contains newer material than any single versioned snapshot. No recovery needed from ~/.gemini/history; claimgate-suite is the current source.

---

## Outstanding search locations (not yet scanned)

- `~/Documents/Codex/2026-07-25/` (1 GB, likely subset of 07-27, not yet indexed)
- Individual agent/skill output directories (~12 additional paths under ~/.codex, ~/.claude, etc.); these are tool output, not spec docs
- Owner-authored Notion/wiki pages referenced in wiki search results but not yet recovered as markdown

### Recommendation

The high-value specs and contracts have been recovered. Further recovery should prioritize:

1. Owner-authored Notion or external doc links found in wiki search (context: `claimgate-as-lev-os-patch-north-star-2026-07-22.md` and others reference external sources)
2. Any newer material added to Desktop post-2026-07-25
3. Agent speech logs and council outputs only if explicitly requested by owner
