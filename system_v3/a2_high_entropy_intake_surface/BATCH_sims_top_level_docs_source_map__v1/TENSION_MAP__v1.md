# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_top_level_docs_source_map__v1`
Extraction mode: `SIM_SOURCE_MAP_PASS`

## T1) Filename-derived catalog vs evidence semantics
- source markers:
  - `SIM_CATALOG_v1.3.md:1-5`
  - `SIM_CATALOG_v1.3.md:23-131`
- tension:
  - the catalog explicitly derives from JSON filenames, yet it also organizes the corpus into meaning-bearing family clusters and execution priorities
  - filename structure is useful, but it is not identical to result-body evidence
- preserved read:
  - keep the catalog as a structural map and planning surface, not as direct proof of sim behavior
- possible downstream consequence:
  - later passes should pair catalog entries with runner and result bodies before promoting any narrower family claims

## T2) Engineering-only self-label vs theory-facing interpretation
- source markers:
  - `SIM_RUNBOOK_v1.4.md:3-4`
  - `SIM_RUNBOOK_v1.4.md:76-100`
- tension:
  - the runbook says it is engineering rather than truth-claims
  - the same document still includes theory-facing interpretation for Axis4, Topology4, and Axis3 plus a prioritized worldview of what to test first
- preserved read:
  - keep the engineering role and the interpretive layer both visible; do not smooth one into the other
- possible downstream consequence:
  - later batches may need to split workflow instructions from theory-facing notes

## T3) Catalog coverage vs evidence-pack coverage
- source markers:
  - `SIM_CATALOG_v1.3.md:5`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:1-663`
- tension:
  - the catalog inventories `62` result files
  - the current evidence pack contains `29` `BEGIN SIM_EVIDENCE v1` blocks, so top-level evidence packaging is only a partial projection of the visible result corpus
- preserved read:
  - treat the evidence pack as a selected/generated evidence subset, not as a complete mirror of all result JSONs
- possible downstream consequence:
  - later per-result extraction is required before claiming full source-class coverage

## T4) Runbook wording vs observed tree roles
- source markers:
  - `SIM_RUNBOOK_v1.4.md:125-129`
- tension:
  - the runbook says `run_*` scripts in `simpy/simson` are the harnesses
  - observed inventory shows `51` `.py` harnesses in `simpy/` and `62` `.json` result files in `simson/`, with no `run_*` scripts under `simson/`
- preserved read:
  - treat `simpy/` as the executable harness root and `simson/` as the result/evidence root unless narrower source evidence later contradicts that split
- possible downstream consequence:
  - future manifests should use path-specific roles rather than combined `simpy/simson` wording

## T5) Strict Thread-B evidence purity vs A2 intake commentary
- source markers:
  - `SIM_RUNBOOK_v1.4.md:10-18`
  - `SIM_RUNBOOK_v1.4.md:104-121`
- tension:
  - the runbook forbids any prose around `SIM_EVIDENCE` blocks in the transport path
  - this A2 batch is necessarily commentary/compression oriented
- preserved read:
  - these intake artifacts are not admissible Thread-B evidence payloads; they are outer-lane summaries only
- possible downstream consequence:
  - do not feed this batch downward as a `SIM_EVIDENCE` pack

## T6) Repeatable-run expectation vs filesystem hygiene
- source markers:
  - `SIM_RUNBOOK_v1.4.md:22-47`
  - observed folder inventory under `sims/simpy`
- tension:
  - the runbook assumes a low-drama repeatable run workflow
  - the source tree includes leading-space runner filenames and committed `__pycache__` artifacts that can complicate deterministic path handling
- preserved read:
  - keep this as an executable-facing hygiene risk, not as proof that the sims are invalid
- possible downstream consequence:
  - the next executable-facing batch should audit runner/result pairing and path hygiene without mutating source corpus
