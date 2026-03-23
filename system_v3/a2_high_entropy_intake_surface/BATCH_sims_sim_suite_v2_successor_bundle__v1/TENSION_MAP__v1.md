# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_sim_suite_v2_successor_bundle__v1`
Extraction mode: `SIM_SUITE_V2_SUCCESSOR_BUNDLE_PASS`

## T1) The current successor bundle emits seven descendants, but none carries the current bundle hash in the repo-top evidence pack
- source markers:
  - `run_sim_suite_v2_full_axes.py:423-460`
  - top-level evidence blocks for all seven emitted SIM_IDs
- tension:
  - executable emission path is one current file with hash `dd05c8f6...`
  - repo-top evidence attribution for the seven emitted descendants never uses `dd05c8f6...`
- preserved read:
  - do not treat current emission as current top-level provenance
- possible downstream consequence:
  - later lineage claims should separate “current emitter” from “current evidenced producer”

## T2) Topology4 terrain8 V1 is emitted by the successor bundle but evidenced under the dedicated Topology4 channel-family runner hash
- source markers:
  - `run_sim_suite_v2_full_axes.py:427-430`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:54-89`
  - current `run_axis12_topology4_channelfamily_suite_v2.py` hash match `be1a8c71...`
- tension:
  - the bundle emits `S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1`
  - repo-top evidence attributes it to the dedicated Topology4 runner hash
- preserved read:
  - keep Topology4 under its dedicated runner lineage rather than folding it into the bundle
- possible downstream consequence:
  - later Topology4 claims should privilege the dedicated topology batch over the successor bundle

## T3) Axis4 comp check V1 is emitted by the successor bundle but evidenced under the Axis4 core harness hash
- source markers:
  - `run_sim_suite_v2_full_axes.py:432-435`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:102-107`
  - current `axis4_seq_cycle_sim.py` hash match `b741c60d...`
- tension:
  - the bundle emits `S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1`
  - repo-top evidence attributes it to the dedicated Axis4 core harness hash
- preserved read:
  - keep Axis4 provenance under the dedicated Axis4 line
- possible downstream consequence:
  - later Axis4 producer-path claims should not use the successor bundle as strongest provenance

## T4) Axis56 operator4 LR V1 is emitted by the successor bundle but evidenced under the current predecessor-bundle hash
- source markers:
  - `run_sim_suite_v2_full_axes.py:437-440`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:254-265`
  - current `run_sim_suite_v1.py` hash match `1c8a7ac3...`
- tension:
  - the successor bundle emits `S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1`
  - repo-top evidence attributes that same result surface to the current `run_sim_suite_v1.py` hash
- preserved read:
  - keep the cross-bundle attribution explicit
- possible downstream consequence:
  - later operator-role lineage should preserve overlap without flattening bundle boundaries

## T5) Stage16 V5 is emitted by the successor bundle but evidenced under the leading-space mega-script hash, and its stored payload is byte-identical to V4
- source markers:
  - `run_sim_suite_v2_full_axes.py:442-445`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:377-414`
  - current leading-space ` run_mega_axis0_ab_stage16_axis6.py` hash match `8f12b695...`
  - `results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json`
  - `results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json`
- tension:
  - the bundle emits Stage16 V5
  - repo-top evidence attributes it to the mega-script hash
  - V4 and V5 result files are byte-identical despite renamed SIM_ID / filename
- preserved read:
  - keep both provenance drift and version-label drift explicit
- possible downstream consequence:
  - later Stage16 summaries should not assume V5 implies a changed payload or cleaner local provenance

## T6) Axis0 traj corr V5 is emitted by the successor bundle but evidenced under the dedicated Axis0 runner hash, and V5 materially shifts contract relative to V4
- source markers:
  - `run_sim_suite_v2_full_axes.py:447-450`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:14-26`
  - current `run_axis0_traj_corr_suite.py` hash match `a42e2207...`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json`
- tension:
  - the bundle emits Axis0 V5
  - repo-top evidence attributes V5 to the dedicated Axis0 runner hash
  - V4 is a single-sequence summary at `cycles = 16`
  - V5 is a two-sequence delta surface at `cycles = 64`
- preserved read:
  - preserve both provenance drift and behavioral contract drift
- possible downstream consequence:
  - later Axis0 work should distinguish version upgrade from bundle continuity

## T7) Negctrl Axis6 V3 is emitted by the successor bundle but evidenced under an all-zero code hash
- source markers:
  - `run_sim_suite_v2_full_axes.py:452-455`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:327-332`
- tension:
  - the bundle emits `S_SIM_NEGCTRL_AXIS6_COMMUTE_V3`
  - repo-top evidence records `CODE_HASH_SHA256` as all zeros
- preserved read:
  - keep the malformed or placeholder provenance explicit rather than guessing a producer
- possible downstream consequence:
  - later provenance work should treat this block as unresolved even though the metrics are stable zeros

## T8) Negctrl Axis0 NoEnt V1 is emitted by the successor bundle but evidenced under the leading-space `axis12_axis0_link` hash
- source markers:
  - `run_sim_suite_v2_full_axes.py:457-460`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:302-314`
  - current leading-space ` run_axis12_axis0_link_v1.py` hash match `e26448f3...`
  - ` run_axis12_axis0_link_v1.py:1-6`
- tension:
  - the bundle emits `S_SIM_NEGCTRL_AXIS0_NOENT_V1`
  - repo-top evidence attributes it to the current hash of an `axis12_axis0_link` runner
- preserved read:
  - preserve this as a cross-family provenance mismatch rather than a meaningful semantic link
- possible downstream consequence:
  - later negctrl-axis0 lineage work should treat the producer attribution as contradictory

## T9) The bundle is adjacent in raw order to Stage16 mix-control surfaces but should not absorb them
- source markers:
  - raw folder order around `run_sim_suite_v2_full_axes.py`
- tension:
  - raw adjacency tempts a Stage16-family merge
  - emitted SIM_ID set and descendant storage close the bundle boundary cleanly before `run_stage16_axis6_mix_control.py`
- preserved read:
  - keep the successor bundle and the next Stage16 family separate
- possible downstream consequence:
  - the next batch should start fresh at the Stage16 mix-control entrypoint
