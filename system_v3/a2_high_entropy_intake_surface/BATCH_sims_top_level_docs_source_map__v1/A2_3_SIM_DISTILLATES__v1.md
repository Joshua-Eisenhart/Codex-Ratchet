# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / OUTER-CACHE DISTILLATE
Batch: `BATCH_sims_top_level_docs_source_map__v1`
Extraction mode: `SIM_SOURCE_MAP_PASS`

## Distillate D1
- statement:
  - the top-level sims source class is internally tripartite: filename catalog, engineering runbook, and generated evidence pack
- source anchors:
  - `SIM_CATALOG_v1.3.md:1-5`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:1-10`
  - `SIM_RUNBOOK_v1.4.md:1-4`
- possible downstream consequence:
  - later sims ingestion should preserve these role boundaries instead of flattening docs, runners, and evidence into one layer

## Distillate D2
- statement:
  - the strongest executable-facing motif is strict hash-anchored evidence transport with no interleaved prose
- source anchors:
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:1-10`
  - `SIM_RUNBOOK_v1.4.md:10-18`
  - `SIM_RUNBOOK_v1.4.md:104-121`
- possible downstream consequence:
  - reusable as a sims-specific evidence hygiene pattern, but still source-local until checked against current active runtime/spec surfaces

## Distillate D3
- statement:
  - the top-level docs prioritize a specific family order: micro sanity checks, then Axis0/Axis4, then Axis12/history, then Stage16, then Ultra
- source anchors:
  - `SIM_CATALOG_v1.3.md:151-159`
  - `SIM_RUNBOOK_v1.4.md:94-100`
- possible downstream consequence:
  - later per-family batches can follow this order without pretending it is already earned system law

## Distillate D4
- statement:
  - the docs encode explicit evidence assumptions: fixed seeds, code hashes, output hashes, normalized outputs, and negative controls as fault detectors
- source anchors:
  - `SIM_RUNBOOK_v1.4.md:34-47`
  - `SIM_RUNBOOK_v1.4.md:66-72`
  - `SIM_CATALOG_v1.3.md:159`
- possible downstream consequence:
  - later executable-facing batches should test whether the actual runner/result surfaces satisfy these assumptions

## Distillate D5
- statement:
  - current top-level evidence surfacing is partial rather than complete: the catalog inventories `62` result files while the present evidence pack exposes `29` `SIM_EVIDENCE` blocks
- source anchors:
  - `SIM_CATALOG_v1.3.md:5`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:1-663`
- possible downstream consequence:
  - later result-family batches are required before claiming full evidence coverage for the sims corpus

## Distillate D6
- statement:
  - executable-facing hygiene risk is already visible at the source-tree level through leading-space runner filenames, committed cache artifacts, and loose `simpy/simson` wording
- source anchors:
  - `SIM_RUNBOOK_v1.4.md:125-129`
  - observed folder inventory under `sims/simpy` and `sims/simson`
- possible downstream consequence:
  - the next sims batch should inspect the earliest executable-facing runner family rather than staying only at the doc layer
