# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis4_p03_core_harness_family__v1`
Extraction mode: `SIM_AXIS4_CORE_PASS`

## Cluster S1: Axis4 P03 sequence map
- source anchors:
  - `axis4_seq_cycle_sim.py:217-221`
  - `run_axis4_sims.py:189-193`
  - `results_S_SIM_AXIS4_SEQ01_P03.json:31-35`
  - `results_S_SIM_AXIS4_SEQ04_P03.json:31-35`
- cluster members:
  - `S_SIM_AXIS4_SEQ01_P03`
  - `S_SIM_AXIS4_SEQ02_P03`
  - `S_SIM_AXIS4_SEQ03_P03`
  - `S_SIM_AXIS4_SEQ04_P03`
- compressed read:
  - both harnesses define the same four P03 sequence objects and the result family preserves them one-file-per-SIM_ID
- possible downstream consequence:
  - useful stable root mapping for later Axis4 family batches

## Cluster S2: Polarity model
- source anchors:
  - `axis4_seq_cycle_sim.py:121-126`
  - `run_axis4_sims.py:101-103`
  - `results_S_SIM_AXIS4_SEQ01_P03.json:9-24`
- cluster members:
  - polarity `+`
  - polarity `-`
  - pinch
  - unitary redistribution
  - entropy
  - purity
- compressed read:
  - both harnesses operationalize Axis4 as an ordering contrast between contraction-first and redistribution-first dynamics
- possible downstream consequence:
  - this is the clearest current executable-facing articulation of the Axis4 theory seam

## Cluster S3: Output-contract divergence
- source anchors:
  - `axis4_seq_cycle_sim.py:247-263`
  - `run_axis4_sims.py:215-229`
- cluster members:
  - per-SIM `evidence_<SIM_ID>.txt`
  - one combined `sim_evidence_pack.txt`
  - same `results_<SIM_ID>.json` target pattern
- compressed read:
  - the two harnesses target the same result namespace but not the same evidence sidecar contract
- possible downstream consequence:
  - later evidence reconciliation must account for these two competing output patterns

## Cluster S4: Currently evidenced producer path
- source anchors:
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:111-183`
  - harness hash records in this batch
- cluster members:
  - code hash `b741c60d...`
  - four P03 output hashes
  - top-level evidence-pack entries
- compressed read:
  - the repo-held evidence pack binds the P03 family to `axis4_seq_cycle_sim.py`, not to `run_axis4_sims.py`
- possible downstream consequence:
  - this gives one current producer path and one alternate unresolved authoring surface

## Cluster S5: Sequence asymmetry pattern
- source anchors:
  - `results_S_SIM_AXIS4_SEQ01_P03.json:9-24`
  - `results_S_SIM_AXIS4_SEQ02_P03.json:9-24`
  - `results_S_SIM_AXIS4_SEQ03_P03.json:9-24`
  - `results_S_SIM_AXIS4_SEQ04_P03.json:9-24`
- cluster members:
  - invariant `polarity_plus`
  - variable `polarity_minus`
- compressed read:
  - the current P03 results preserve sequence differences only on the minus branch; the plus branch is numerically unchanged across all four sequences
- possible downstream consequence:
  - later Axis4 summaries should not claim symmetric sequence sensitivity across both polarities

## Cluster S6: Duplicate-harness residue
- source anchors:
  - `axis4_seq_cycle_sim.py:2-3`
  - `run_axis4_sims.py:2-3`
  - repo search results within `sims/`
- cluster members:
  - duplicate title string `run_axis4_sims.py`
  - second harness file with different hash
  - no current evidence-pack reference to the second hash
- compressed read:
  - this family contains unresolved authoring duplication rather than one clean canonical script path
- possible downstream consequence:
  - future executable-facing cleanup must preserve provenance and avoid silently picking a winner
