# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_sim_suite_v2_successor_bundle__v1`
Extraction mode: `SIM_SUITE_V2_SUCCESSOR_BUNDLE_PASS`
Batch scope: `run_sim_suite_v2_full_axes.py` successor bundle plus its seven emitted descendant result surfaces, with prior and dedicated runners kept comparison-only
Date: 2026-03-08

## 1) Batch Selection
- starting file in raw simpy folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v2_full_axes.py`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v2_full_axes.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V3.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_NEGCTRL_AXIS0_NOENT_V1.json`
- reason for bounded family:
  - `run_sim_suite_v2_full_axes.py` is the next unprocessed raw-folder-order entrypoint after `run_sim_suite_v1.py`
  - its `main()` emits exactly seven descendant result surfaces in one pass
  - those seven result surfaces exist in `simson/` under the exact filenames written in `main()`
  - adjacent files such as `run_stage16_axis6_mix_control.py` and `run_stage16_axis6_mix_sweep.py` begin a different raw-order family and were not merged into this bundle
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_topology4_channelfamily_suite_v2.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/axis4_seq_cycle_sim.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_traj_corr_suite.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_mega_axis0_ab_stage16_axis6.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_axis12_axis0_link_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V2.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- deferred next raw-folder-order source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_axis6_mix_control.py`

## 2) Source Membership
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v2_full_axes.py`
  - sha256: `dd05c8f6d5bbef5df8b7f12cb1f50f8ade1c36f9fb83e397122d89a5376c1989`
  - size bytes: `18624`
  - line count: `467`
  - source role: seven-sim successor bundle runner
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
  - sha256: `218b43b4a1adee0149363f5103840329693d81e82beea73485fdc1235e2a6e9a`
  - size bytes: `1833`
  - line count: `79`
  - source role: topology4 terrain8 descendant
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1.json`
  - sha256: `182e5db19b340ebff90cf564e439ee5744bda423f9bf93c1fc278a45bfdcb9f0`
  - size bytes: `126`
  - line count: `6`
  - source role: axis4 composite-check descendant
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1.json`
  - sha256: `09b2af8dd407c985c7f5e7a9dbf0787519baacf0e53b994551a81d93b2388284`
  - size bytes: `383`
  - line count: `12`
  - source role: axis56 operator4 descendant
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json`
  - sha256: `955244986b65a4a45227f50737471c41ebf97d1462cabdd3d5b4a8467cbf7c8e`
  - size bytes: `1445`
  - line count: `50`
  - source role: stage16 sub4 uniform axis6 descendant
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json`
  - sha256: `24307828db85e99c5c75a0fb8687189e151139c687bc3d787367b6afd4f79df8`
  - size bytes: `688`
  - line count: `32`
  - source role: axis0 trajectory-correlation V5 descendant
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V3.json`
  - sha256: `f5621f2a3d65686685a37de0faef48580cc8abcbc5109f2809c0dbb6407129a3`
  - size bytes: `71`
  - line count: `5`
  - source role: axis6 negctrl V3 descendant
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_NEGCTRL_AXIS0_NOENT_V1.json`
  - sha256: `dc77a0e6ea956a699df6e1616538fa9d74e40aa488d13500010a61d88437b609`
  - size bytes: `649`
  - line count: `32`
  - source role: axis0 no-entangler negctrl descendant

## 3) Structural Map Of The Family
### Successor bundle runner: `run_sim_suite_v2_full_axes.py`
- anchors:
  - `run_sim_suite_v2_full_axes.py:178-208`
  - `run_sim_suite_v2_full_axes.py:220-246`
  - `run_sim_suite_v2_full_axes.py:249-282`
  - `run_sim_suite_v2_full_axes.py:285-340`
  - `run_sim_suite_v2_full_axes.py:346-395`
  - `run_sim_suite_v2_full_axes.py:398-421`
  - `run_sim_suite_v2_full_axes.py:423-463`
- source role:
  - one successor bundle with seven embedded sims:
    - `S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1`
    - `S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1`
    - `S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1`
    - `S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5`
    - `S_SIM_AXIS0_TRAJ_CORR_SUITE_V5`
    - `S_SIM_NEGCTRL_AXIS6_COMMUTE_V3`
    - `S_SIM_NEGCTRL_AXIS0_NOENT_V1`
  - writes seven result JSONs plus one local evidence pack
  - current runner hash:
    - `dd05c8f6d5bbef5df8b7f12cb1f50f8ade1c36f9fb83e397122d89a5376c1989`
- bounded read:
  - executable bundle membership is coherent
  - repo-top provenance is not coherent with the current bundle hash

### Current descendants with non-bundle evidence attribution
- evidence-pack code-hash map:
  - Topology4 terrain8 V1 -> `be1a8c71...` -> current `run_axis12_topology4_channelfamily_suite_v2.py`
  - Axis4 comp check V1 -> `b741c60d...` -> current `axis4_seq_cycle_sim.py`
  - Axis56 operator4 LR V1 -> `1c8a7ac3...` -> current `run_sim_suite_v1.py`
  - Stage16 sub4 uniform axis6 V5 -> `8f12b695...` -> current leading-space ` run_mega_axis0_ab_stage16_axis6.py`
  - Axis0 traj corr suite V5 -> `a42e2207...` -> current `run_axis0_traj_corr_suite.py`
  - Negctrl axis6 commute V3 -> `00000000...` -> no current runner hash match; zero-hash admission
  - Negctrl axis0 noent V1 -> `e26448f3...` -> current leading-space ` run_axis12_axis0_link_v1.py`
- bounded read:
  - none of the seven emitted descendants carries the current `run_sim_suite_v2_full_axes.py` hash in the repo-held top-level evidence pack
  - provenance is fragmented across dedicated runners, the prior bundle hash, a leading-space mega hash, a cross-family leading-space hash, and one zero-hash block

### Result-surface highlights
- `results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
  - 16 sign/topology/up-down cells
  - minimum entropy cell:
    - `Si_sign-1_DOWN.entropy_mean = 0.32534208782053975`
  - maximum entropy cell:
    - `Ni_sign-1_DOWN.entropy_mean = 0.4371846694682789`
  - maximum purity cell:
    - `Si_sign-1_UP.purity_mean = 0.8057525632184778`
- `results_S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1.json`
  - near-zero but nonzero split:
    - `delta_entropy_mean = 8.787818373125038e-05`
    - `delta_purity_mean = -9.274188033376717e-05`
- `results_S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1.json`
  - operator-role flat result with `seed = 0`, `trials = 512`
  - strongest delta is `TE_delta_trace_mean = 1.1808332795843097`
  - weakest commutator mean is `TI_comm_norm_mean = 0.530039494923813`
- `results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json`
  - same stored payload as Stage16 V4
  - all `dS` means positive and all `dP` means negative
- `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json`
  - two-sequence delta surface:
    - `SEQ01_metrics.MI_mean = 0.12489839387783339`
    - `SEQ02_metrics.MI_mean = 0.12643876777492513`
    - `delta_MI_mean_SEQ02_minus_SEQ01 = 0.0015403738970917458`
    - `delta_SAgB_min_mean_SEQ02_minus_SEQ01 = -0.05338828597951362`
- `results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V3.json`
  - `delta_trace_mean = 0.0`
  - `comm_norm_mean = 0.0`
  - `trials = 512`
- `results_S_SIM_NEGCTRL_AXIS0_NOENT_V1.json`
  - both sequences preserve nonnegative conditional-entropy minima:
    - `SEQ01_metrics.SAgB_min_mean = 0.3394315118479687`
    - `SEQ02_metrics.SAgB_min_mean = 0.3499393975875372`
  - both sequences keep `neg_SAgB_frac_mean = 0.0`

### Version and predecessor comparison seam
- comparison anchors:
  - `results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json`
  - `results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V2.json`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json`
- bounded comparison read:
  - Stage16:
    - V4 and V5 are byte-identical despite different filenames and different SIM_ID labels
  - Negctrl Axis6:
    - V2 and V3 preserve the same zero means
    - trials change from `256` to `512`
  - Axis0 trajectory correlation:
    - V4 is a single-sequence summary with `cycles = 16`
    - V5 becomes a two-sequence delta surface with `cycles = 64`
    - V5 reduces the observed negative-conditional-entropy fraction relative to V4

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_topology4_channelfamily_suite_v2.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/axis4_seq_cycle_sim.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_traj_corr_suite.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_mega_axis0_ab_stage16_axis6.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_axis12_axis0_link_v1.py`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:10-16`
  - `SIM_CATALOG_v1.3.md:39-41`
  - `SIM_CATALOG_v1.3.md:59`
  - `SIM_CATALOG_v1.3.md:77`
  - `SIM_CATALOG_v1.3.md:86`
  - `SIM_CATALOG_v1.3.md:108`
  - `SIM_CATALOG_v1.3.md:121`
  - `SIM_CATALOG_v1.3.md:141-142`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:14-26`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:54-107`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:254-265`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:302-414`
- bounded comparison read:
  - the catalog lists the seven descendants and separately lists both `run_sim_suite_v1.py` and `run_sim_suite_v2_full_axes.py` as relevant entrypoints
  - the top-level evidence pack contains all seven descendant blocks
  - none of those seven blocks uses the current `run_sim_suite_v2_full_axes.py` hash
  - the strongest cross-family mismatch is `S_SIM_NEGCTRL_AXIS0_NOENT_V1`:
    - emitted here by `run_sim_suite_v2_full_axes.py`
    - evidenced under the current leading-space ` run_axis12_axis0_link_v1.py` hash

## 5) Source-Class Read
- Best classification:
  - successor multisim bundle with full descendant storage and fully externalized provenance attribution
- Not best classified as:
  - strongest current top-level producer path for its own descendants
  - the same bounded source family as `run_sim_suite_v1.py`
  - one narrow theory family
- Theory-facing vs executable-facing split:
  - executable-facing:
    - one bundle file
    - seven emitted results
    - seven local evidence blocks
  - theory-facing:
    - topology4 terrain8, axis4 variance split, operator roles, stage16, axis0 dynamics, and negctrls are bundled together
  - evidence-facing:
    - all seven descendants are repo-top evidenced
    - none of them is repo-top evidenced under the current bundle hash
- possible downstream consequence:
  - later sims interpretation should treat this batch as a successor bundle that can emit the surfaces, while preserving that current repo-top provenance has already moved elsewhere or become contradictory for every emitted descendant
