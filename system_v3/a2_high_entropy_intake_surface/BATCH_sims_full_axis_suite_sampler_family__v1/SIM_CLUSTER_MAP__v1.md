# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_full_axis_suite_sampler_family__v1`
Extraction mode: `SIM_FULL_AXIS_SAMPLER_PASS`

## Cluster S1: Sampler-emitted axis blocks
- source anchors:
  - `run_full_axis_suite.py:224-250`
  - `results_full_axis_suite.json:1-36`
- cluster members:
  - `axis3_plus`
  - `axis3_minus`
  - `axis4_composites`
  - `axis5_fga`
  - `axis5_fsa`
  - `axis6_lr`
- compressed read:
  - the sampler is one six-block axis cross-section rather than one narrow executable family
- possible downstream consequence:
  - later interpretation should treat it as a bridge surface spanning multiple later standalone families

## Cluster S2: Descendant naming drift
- source anchors:
  - `run_full_axis_suite.py:245-250`
  - `SIM_CATALOG_v1.3.md:86`
  - `SIM_CATALOG_v1.3.md:125`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:93-107`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:269-298`
- cluster members:
  - `S_SIM_AXIS3_WEYL_HOPF_PLUS` / `S_SIM_AXIS3_WEYL_HOPF_MINUS`
  - `S_SIM_AXIS3_WEYL_HOPF_GRID_V1`
  - `S_SIM_AXIS4_COMPOSITES`
  - `S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1`
  - `S_SIM_AXIS5_FGA_MONOTONE`
  - `S_SIM_AXIS5_FGA_SWEEP_V1`
  - `S_SIM_AXIS5_FSA_MONOTONE`
  - `S_SIM_AXIS5_FSA_SWEEP_V1`
  - `S_SIM_AXIS6_LEFT_RIGHT`
  - `S_SIM_AXIS6_LR_MULTI_V1`
- compressed read:
  - the sampler’s emitted names do not match the current standalone descendant names carried by the catalog and evidence pack
- possible downstream consequence:
  - later provenance work should preserve naming drift instead of silently equating these surfaces

## Cluster S3: Partial metric continuity
- source anchors:
  - `results_full_axis_suite.json:1-36`
  - standalone descendant result surfaces read in this batch
- cluster members:
  - close Axis3 flux magnitude
  - exact chirality sign match
  - near-zero Axis5 FSA continuity
  - diverged Axis4 / Axis5 FGA / Axis6 means
- compressed read:
  - the sampler anticipates the descendant classes conceptually, but only some signals remain numerically close
- possible downstream consequence:
  - later summaries should speak about continuity by subfamily, not blanket equivalence

## Cluster S4: Code-hash split between sampler and descendants
- source anchors:
  - `run_full_axis_suite.py` hash in this batch
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:93-107`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:269-298`
- cluster members:
  - sampler code hash `71aa883f...`
  - descendant code hash `1c8a7ac3...`
  - Axis4 descendant code hash `b741c60d...`
- compressed read:
  - the current top-level evidenced descendants do not point back to the sampler hash
- possible downstream consequence:
  - the sampler should not be treated as the current evidenced producer path for these standalone surfaces

## Cluster S5: Axis4 special divergence
- source anchors:
  - `results_full_axis_suite.json:1-36`
  - `results_S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1.json:1-6`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:102-107`
- cluster members:
  - sampler `axis4_composites`
  - descendant `S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1`
  - code hash `b741c60d...`
- compressed read:
  - Axis4 is the most visibly divergent descendant: different name, different hash lineage, and opposite-sign stored deltas
- possible downstream consequence:
  - later Axis4 interpretations should route through the dedicated Axis4 batches first, not through this sampler alone

## Cluster S6: Standalone sampler placement vs next raw-order family
- source anchors:
  - `SIM_CATALOG_v1.3.md:103`
  - raw-folder-order note in this batch
- cluster members:
  - `full_axis_suite`
  - `run_history_invariant_gradient_scan_v11.py`
- compressed read:
  - this sampler stands as its own bounded cross-axis family before the repo moves into the later history-scan files
- possible downstream consequence:
  - the next pass should begin the history-scan family cleanly rather than dragging it into this sampler batch
