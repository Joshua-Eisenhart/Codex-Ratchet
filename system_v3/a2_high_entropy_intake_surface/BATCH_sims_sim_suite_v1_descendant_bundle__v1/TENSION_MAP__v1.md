# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_sim_suite_v1_descendant_bundle__v1`
Extraction mode: `SIM_SUITE_V1_BUNDLE_PASS`

## T1) One bundle emits ten descendants, but repo-top evidence attribution splits across six code hashes
- source markers:
  - `run_sim_suite_v1.py:568-623`
  - top-level evidence-pack blocks for all ten emitted SIM_IDs
- tension:
  - executable emission path is one current file
  - evidence-pack attribution is not one current file
- preserved read:
  - do not flatten bundle emission into one uniform top-level producer path
- possible downstream consequence:
  - later lineage claims should be descendant-specific, not bundle-global

## T2) Axis3 / Axis5 / Axis6 descendants remain aligned to current `run_sim_suite_v1.py`
- source markers:
  - `run_sim_suite_v1.py:572-590`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:93-98`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:269-298`
- tension:
  - these descendants are both emitted and evidenced under the current bundle hash `1c8a7ac3...`
  - other descendants in the same bundle are not
- preserved read:
  - keep the aligned subset explicit without overextending it to the full bundle
- possible downstream consequence:
  - continuity strength should be graded by descendant family

## T3) Axis4 all-bidir is emitted by the bundle but evidenced under the dedicated Axis4 core harness hash
- source markers:
  - `run_sim_suite_v1.py:592-595`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:187-250`
  - current `axis4_seq_cycle_sim.py` hash match `b741c60d...`
- tension:
  - bundle writes `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json`
  - repo-top evidence attributes that descendant to `b741c60d...`, the current `axis4_seq_cycle_sim.py` hash
- preserved read:
  - keep Axis4 provenance under its dedicated harness lineage rather than absorbing it into the bundle
- possible downstream consequence:
  - later Axis4 work should privilege dedicated Axis4 batches for producer-path claims

## T4) Axis12 descendants are emitted by the bundle but evidenced under dedicated Axis12 runner hashes
- source markers:
  - `run_sim_suite_v1.py:597-605`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:30-50`
  - current hash matches for `run_axis12_seq_constraints.py` and `run_axis12_channel_realization_suite.py`
- tension:
  - bundle emits both `S_SIM_AXIS12_SEQ_CONSTRAINTS_V2` and `S_SIM_AXIS12_CHANNEL_REALIZATION_V4`
  - repo-top evidence attributes them to dedicated Axis12 runners, not to the current bundle hash
- preserved read:
  - preserve Axis12 as a dedicated line even when the bundle can emit matching results
- possible downstream consequence:
  - later Axis12 producer claims should distinguish bundle emission from dedicated current provenance

## T5) Axis0 traj corr V4 is emitted by the bundle but evidenced under `run_axis0_traj_corr_suite.py`
- source markers:
  - `run_sim_suite_v1.py:617-620`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:1-10`
  - current `run_axis0_traj_corr_suite.py` hash match `a42e2207...`
- tension:
  - bundle emits `S_SIM_AXIS0_TRAJ_CORR_SUITE_V4`
  - repo-top evidence points to a dedicated Axis0 runner hash
- preserved read:
  - do not treat the bundle as the strongest current provenance source for Axis0 trajectory correlation
- possible downstream consequence:
  - later Axis0 summaries should preserve a dedicated-runner provenance seam

## T6) Stage16 V4 is emitted by the bundle, but the evidence hash points to the leading-space mega script, and V4/V5 files are byte-identical
- source markers:
  - `run_sim_suite_v1.py:607-610`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:336-373`
  - current hash match for ` simpy/ run_mega_axis0_ab_stage16_axis6.py`
  - `results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json`
  - `results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json`
- tension:
  - bundle emits Stage16 V4
  - repo-top evidence attributes V4 to `8f12b695...`, the current leading-space mega script hash
  - stored V4 and V5 result files are byte-identical despite versioned renaming
- preserved read:
  - keep both provenance drift and version-label drift explicit
- possible downstream consequence:
  - later Stage16 lineage claims should avoid assuming that version labels imply payload change

## T7) Negctrl Axis6 V2 is emitted by the bundle, but the evidence hash points to the current successor bundle hash, while v2 now emits V3
- source markers:
  - `run_sim_suite_v1.py:612-615`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:318-323`
  - current `run_sim_suite_v2_full_axes.py` hash match `dd05c8f6...`
  - `run_sim_suite_v2_full_axes.py:451-454`
  - `results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V2.json`
  - `results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V3.json`
- tension:
  - bundle emits negctrl V2
  - repo-top evidence attributes V2 to the current successor-bundle hash
  - current successor bundle emits V3, not V2
  - V2 and V3 preserve zero means but change trials from `256` to `512`
- preserved read:
  - keep the bundle-crossing provenance seam explicit
- possible downstream consequence:
  - later negctrl lineage work should distinguish metric continuity from version and producer continuity

## T8) `run_sim_suite_v2_full_axes.py` is adjacent in raw order but should not be merged into this batch
- source markers:
  - raw folder order around `run_sim_suite_v1.py`
  - `run_sim_suite_v2_full_axes.py:423-450`
- tension:
  - raw adjacency suggests a natural merge temptation
  - emitted SIM_ID set and version set differ enough that the bundle boundary should hold
- preserved read:
  - keep `sim_suite_v2` comparison-only for this batch
- possible downstream consequence:
  - the next batch should treat `sim_suite_v2` as its own successor bundle family
