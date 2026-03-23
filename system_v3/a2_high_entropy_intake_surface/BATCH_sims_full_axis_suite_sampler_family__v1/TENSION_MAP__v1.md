# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_full_axis_suite_sampler_family__v1`
Extraction mode: `SIM_FULL_AXIS_SAMPLER_PASS`

## T1) Sampler-emitted SIM_IDs vs current standalone descendant names
- source markers:
  - `run_full_axis_suite.py:245-250`
  - `SIM_CATALOG_v1.3.md:86`
  - `SIM_CATALOG_v1.3.md:125`
- tension:
  - the sampler emits six SIM_ID names such as `S_SIM_AXIS6_LEFT_RIGHT` and `S_SIM_AXIS4_COMPOSITES`
  - current standalone descendants appear under different names such as `S_SIM_AXIS6_LR_MULTI_V1` and `S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1`
- preserved read:
  - keep naming drift explicit rather than silently translating one family into the other
- possible downstream consequence:
  - later catalog reconciliation should preserve the sampler/descendant rename seam

## T2) Cross-axis anticipation vs non-identical descendants
- source markers:
  - `results_full_axis_suite.json:1-36`
  - descendant result surfaces read in this batch
- tension:
  - the sampler clearly anticipates current standalone axis families
  - several descendant metrics diverge materially from the sampler:
    - Axis4 deltas differ in sign
    - Axis5 FGA mean differs materially
    - Axis6 means differ materially
- preserved read:
  - do not smooth this into “same run, later renamed”
- possible downstream consequence:
  - continuity claims should be partial and subfamily-specific

## T3) Top-level evidence pack favors descendants, not the sampler’s own SIM_IDs
- source markers:
  - `run_full_axis_suite.py:245-250`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:93-107`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:269-298`
- tension:
  - the script writes six local evidence blocks
  - the repo-held top-level evidence pack exposes only descendant names and no block for the sampler’s emitted SIM_IDs
- preserved read:
  - keep script-local evidencing distinct from repo-top evidence admission
- possible downstream consequence:
  - the sampler should stay proposal-side in provenance strength

## T4) Sampler hash vs descendant code hashes
- source markers:
  - sampler hash in this batch
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:93-107`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:269-298`
- tension:
  - sampler code hash is `71aa883f...`
  - current top-level evidence uses `1c8a7ac3...` for Axis3/5/6 descendants and `b741c60d...` for the Axis4 descendant
- preserved read:
  - do not treat current standalone descendants as if they were evidenced under the sampler hash
- possible downstream consequence:
  - later producer-path claims must distinguish conceptual anticipation from direct provenance

## T5) Axis3 continuity is closer than Axis4/5/6 continuity
- source markers:
  - `results_full_axis_suite.json:1-36`
  - `results_S_SIM_AXIS3_WEYL_HOPF_GRID_V1.json:1-8`
  - descendant result surfaces for Axis4/5/6
- tension:
  - Axis3 chirality signs match exactly and flux magnitudes are only slightly different
  - the other descendants show stronger schema or mean-value drift
- preserved read:
  - keep closeness uneven by axis rather than speaking about one uniform continuity level
- possible downstream consequence:
  - later sampler summaries should grade continuity axis by axis

## T6) Axis4 descendant routes through a different live lineage
- source markers:
  - `results_full_axis_suite.json:1-36`
  - `results_S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1.json:1-6`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:102-107`
- tension:
  - sampler Axis4 block is `axis4_composites`
  - current evidenced Axis4 descendant uses a different name, different code hash, and opposite-sign stored deltas
- preserved read:
  - preserve the dedicated Axis4 lineage rather than absorbing it into the sampler
- possible downstream consequence:
  - later Axis4 work should prioritize the dedicated Axis4 batches already produced
