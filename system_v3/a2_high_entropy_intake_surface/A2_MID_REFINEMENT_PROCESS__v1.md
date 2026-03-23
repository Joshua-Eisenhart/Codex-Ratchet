# A2_MID_REFINEMENT_PROCESS__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REFINEMENT PROCESS
Date: 2026-03-08
Role: Repo-held process for second-pass A2-2 refinement from existing A2-high intake artifacts

## 1) Purpose
This surface governs the A2-mid refinement lane that operates on existing intake batches.

It exists so a fresh thread can:
- bootstrap from repo-held guidance
- read the strongest existing A2-high batches
- produce narrower A2-2 candidate reductions
- preserve contradictions while reducing redundancy
- avoid direct mutation of active A2-1 control memory

This surface is:
- noncanon
- reduction-oriented
- parent-batch-driven
- contradiction-preserving
- source-linked

This surface is not:
- a raw core-doc intake process
- A2-1 kernel law
- A1 cartridge doctrine
- runtime state

## 2) Governing Inputs
Before running this process, read these files in order:

1. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md`
2. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md`
3. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
4. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
5. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md`
6. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
7. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
8. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/A2_HIGH_ENTROPY_INTAKE_PROCESS__v1.md`
9. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`

## 3) Inputs And Selection Rule
This process operates primarily on:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/`

Primary rule:
- prefer existing strong A2-high or prior A2-mid batches over rereading raw core docs
- reread raw source only when a parent batch is clearly insufficient for the bounded refinement goal
- select bounded parent batches using the current ledger, not ad hoc memory

Strong parent selection signals:
- `A2_2_CANDIDATE`
- `A2_3_REUSABLE` with clear later reduction value
- high contradiction density with good source linkage
- broad first-pass batch that is too large or mixed for later selective use

Weak parent selection signals:
- giant source-map pass with no clear reduction target
- duplicated replay or low-yield inventory material
- parent batches whose main value is only corpus coverage

## 4) Layer Placement
This process is for:
- narrower A2-2 candidate compressions
- contradiction-preserving reductions
- selective reuse of prior A2-high artifacts

This process is not for:
- direct A2-1 updates
- direct A1 outputs
- raw-doc bulk intake by default

Kernel consequence statements are allowed only as:
- possible downstream consequence
- possible later A2-1 relevance

Do not promote proposal-side reductions into control law from this surface.

## 5) Output Surface
Write all outputs under:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/`

Use batch folders like:
- `BATCH_A2MID_<short_name>__v1/`

## 6) Required Files Per A2-Mid Batch
Each A2-mid batch must include:
- `SOURCE_DEPENDENCY_MAP__v1.md`
- `SELECTION_RATIONALE__v1.md`
- `A2_2_REFINED_CANDIDATES__v1.md`
- `CONTRADICTION_PRESERVATION__v1.md`
- `DOWNSTREAM_CONSEQUENCE_NOTES__v1.md`
- `MANIFEST.json`

Each batch must preserve:
- parent batch ids
- extraction mode
- source linkage through the parent artifacts
- contradiction markers
- proposal status
- raw-source reread status
- promotion / quarantine status

## 7) Allowed Extraction Modes
Examples:
- `A2_MID_REFINEMENT_PASS`
- `ENGINE_PATTERN_REDUCTION_PASS`
- `TERM_CONFLICT_REDUCTION_PASS`
- `QIT_BRIDGE_REDUCTION_PASS`
- `MATH_CLASS_REDUCTION_PASS`
- `CONTRADICTION_REPROCESS_PASS`

Rule:
- each bounded batch must declare its extraction mode
- do not mix many unrelated reduction goals into one batch

## 8) Manifest Rule
Each `MANIFEST.json` should include:
- `batch_id`
- `batch_scope`
- `extraction_mode`
- `promotion_status`
- `parent_batch_ids`
- `selection_basis`
- `raw_source_reread_needed`
- `candidate_items`
- `quarantined_items`
- `control_surface_mutation`

`control_surface_mutation` should normally be:
- `NONE`

## 9) Compression Rule
This is a reduction surface.

Do not:
- copy large parent content blocks
- create omnibus restatements of the parent
- silently collapse contradictions

Do:
- narrow
- de-duplicate
- preserve source-linked tensions
- isolate the most reusable candidate structures

## 10) Mutation Rule
Do not:
- append-save directly into active A2 surfaces by default
- rewrite system docs
- treat A2-mid outputs as direct control memory

Only:
- produce bounded reduction artifacts in this surface

Promotion from these batches into active A2 should happen later, selectively, under separate control.

## 11) Ledger Rule
For every A2-mid batch:
- append one entry to `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- record:
  - batch id
  - extraction mode
  - source family
  - usefulness read
  - promotion status
  - tensions

## 12) Response Contract For Fresh Threads
Any thread following this process should report after each bounded step:
- current phase
- what was read
- what batch was produced
- whether to stay on the current model
- exactly how many more `go on` prompts to queue
- what the next `go on` will do
