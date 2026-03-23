# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_top_level_docs_source_map__v1`
Extraction mode: `SIM_SOURCE_MAP_PASS`

## Cluster S1: Top-level role split
- source anchors:
  - `SIM_CATALOG_v1.3.md:1-5`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:1-10`
  - `SIM_RUNBOOK_v1.4.md:1-4`
- cluster members:
  - derived filename catalog
  - generated evidence pack
  - engineering runbook
- compressed read:
  - the top-level sims source class is already internally layered into mapping, executable discipline, and evidence payload surfaces
- possible downstream consequence:
  - later sims batches can stay role-separated instead of flattening docs, runners, and results into one summary

## Cluster S2: Sim family taxonomy
- source anchors:
  - `SIM_CATALOG_v1.3.md:23-131`
  - `SIM_CATALOG_v1.3.md:151-159`
- cluster members:
  - Axis0
  - Axis12
  - Topology4
  - Axis4
  - Axis5
  - Axis6
  - Stage16
  - Ultra / Ultra4
  - operator-role
  - Axis3
  - terrain
- compressed read:
  - the catalog organizes the sims corpus as named family clusters and also proposes a repeatable order from micro sanity checks toward larger end-to-end stacks
- possible downstream consequence:
  - useful seed for later family-by-family runner/result batches

## Cluster S3: Evidence admissibility contract
- source anchors:
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:1-10`
  - `SIM_RUNBOOK_v1.4.md:10-18`
  - `SIM_RUNBOOK_v1.4.md:104-121`
- cluster members:
  - `SIM_ID`
  - `CODE_HASH_SHA256`
  - `OUTPUT_HASH_SHA256`
  - `METRIC`
  - `EVIDENCE_SIGNAL`
  - no extra prose
- compressed read:
  - admissible evidence is modeled as contiguous hash-anchored blocks only, with zero commentary allowed in the Thread-B transport path
- possible downstream consequence:
  - later executable-facing batches should preserve this contract language as source-local evidence hygiene, not as a generic repo rule

## Cluster S4: Runtime expectations
- source anchors:
  - `SIM_RUNBOOK_v1.4.md:22-47`
  - `SIM_CATALOG_v1.3.md:133-159`
- cluster members:
  - boot / replay before sim execution
  - run from `simpy/simson`
  - auto-write `results_*.json`
  - auto-write paste-ready evidence packs
  - fix seeds
  - hash code
  - normalize output
- compressed read:
  - the top-level docs expect a deterministic loop from runner execution to normalized results to paste-ready evidence, with minimal manual intervention
- possible downstream consequence:
  - later runner/result passes can test whether the actual scripts and JSON surfaces satisfy this claimed workflow

## Cluster S5: Failure handling and controls
- source anchors:
  - `SIM_RUNBOOK_v1.4.md:51-72`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:302-327`
- cluster members:
  - sharded runs
  - binary search on failures
  - negative controls
  - no-entanglement / no-correlation control
  - commutation-forced control
  - label-swap control
- compressed read:
  - the runbook treats failure localization and negative controls as first-class engineering requirements rather than optional cleanup
- possible downstream consequence:
  - later executable-facing intake should keep control runs and attack/bug-detection runs separate from positive-evidence narratives

## Cluster S6: Theory-facing vs executable-facing seam
- source anchors:
  - `SIM_CATALOG_v1.3.md:8-21`
  - `SIM_RUNBOOK_v1.4.md:76-100`
  - `SIM_CATALOG_v1.3.md:133-159`
- cluster members:
  - Axis4 variance-order notes
  - Topology4 base-class note
  - Axis3 chirality / Terrain8 note
  - minimal sim suite
  - run entrypoints
- compressed read:
  - the top-level docs mix interpretive family semantics with concrete execution order, so this seam must stay explicit in later sims processing
- possible downstream consequence:
  - later batches should avoid promoting theory-facing notes into executable truth without tying them to specific runner/result evidence
