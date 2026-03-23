# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis4_directional_suite_family__v1`
Extraction mode: `SIM_AXIS4_DIRECTIONAL_PASS`
Batch scope: Axis4 directional-suite family beginning at `run_axis4_seq01_both_dirs.py`; four executable runners, four paired result surfaces, and one theory-facing aggregate sibling
Date: 2026-03-08

## 1) Batch Selection
- starting file in raw simpy folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_seq01_both_dirs.py`
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_seq01_both_dirs.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_seq02_both_dirs.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_seq03_seq04_both_dirs.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_type2_all_seq_both_dirs.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis4_seq01_both_dirs.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis4_seq02_both_dirs.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis4_seq03_seq04_both_dirs.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis4_type2_all_seq_both_dirs.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json`
- reason for bounded family:
  - `run_axis4_seq01_both_dirs.py` is the first unprocessed directional-suite source named in the prior batch handoff
  - `run_axis4_seq02_both_dirs.py`, `run_axis4_seq03_seq04_both_dirs.py`, and `run_axis4_type2_all_seq_both_dirs.py` share the same polarity kernel, fixed knob block, and evidence-writing pattern, so they form one coherent executable family
  - `results_axis4_seq01_both_dirs.json`, `results_axis4_seq02_both_dirs.json`, `results_axis4_seq03_seq04_both_dirs.json`, and `results_axis4_type2_all_seq_both_dirs.json` are the nearest executable-facing result surfaces for those runners
  - `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json` is included as the nearest theory-facing aggregate sibling because its stored metrics numerically compress the directional runner results across T1 and T2
- raw-folder-order note:
  - previously processed same-family-adjacent source intervenes in the raw listing:
    - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_sims.py`
  - this batch crosses that already-processed harness rather than reopening the prior P03 core batch
- deferred next raw-folder-order source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_batch_v3.py`

## 2) Source Membership
- Runner A:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_seq01_both_dirs.py`
  - sha256: `03dd8e6ebb0822b1021817bc1f7783a60fc3cf017f27f622d3cf505fc64b972a`
  - size bytes: `6804`
  - line count: `190`
  - source role: Type-1 Seq01 bidirectional runner
- Runner B:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_seq02_both_dirs.py`
  - sha256: `a4c0e6efff1fb6afb6f435bf5fd4136bf730c77e78782bc496475813604908eb`
  - size bytes: `7179`
  - line count: `195`
  - source role: Type-1 Seq02 bidirectional runner
- Runner C:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_seq03_seq04_both_dirs.py`
  - sha256: `1af5c548ac7ddec0d57b8bc2643ffeeab0c03740153cba1f408fad1e7b7adb21`
  - size bytes: `8242`
  - line count: `211`
  - source role: Type-1 Seq03 and Seq04 bidirectional runner
- Runner D:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_type2_all_seq_both_dirs.py`
  - sha256: `e32952553888c1a4894d9d4fe0961ad1ab605b60cc90b837951884beadcf5988`
  - size bytes: `8611`
  - line count: `226`
  - source role: Type-2 all-sequence bidirectional runner
- Result A:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis4_seq01_both_dirs.json`
  - sha256: `53184cc679cc162bb2198a3c7dbb6791971ed32cc8dba23448fe1ce441cec668`
  - size bytes: `1477`
  - line count: `63`
  - source role: paired Type-1 Seq01 result surface
- Result B:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis4_seq02_both_dirs.json`
  - sha256: `78e8ebd027ce0b4d96cdb7100cc3ee7d65f8440c79a21603019bce0ea4417702`
  - size bytes: `1476`
  - line count: `63`
  - source role: paired Type-1 Seq02 result surface
- Result C:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis4_seq03_seq04_both_dirs.json`
  - sha256: `df335267575819978b44affa4888467f7fffea3d94d593fc24e1e188c360e6cc`
  - size bytes: `2754`
  - line count: `107`
  - source role: paired Type-1 Seq03 and Seq04 result surface
- Result D:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis4_type2_all_seq_both_dirs.json`
  - sha256: `c8353cd4f83c20770796b27f809c42e765dc559617c208a884dd1393ebc9c8a7`
  - size bytes: `5753`
  - line count: `221`
  - source role: paired Type-2 all-sequence result surface
- Aggregate sibling:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json`
  - sha256: `e088e8cea763046b6549fa995cf0bf7857b874c178af1de4a84b0489033905ec`
  - size bytes: `5210`
  - line count: `200`
  - source role: theory-facing aggregate bidirectional compression surface

## 3) Structural Map Of The Family
### Type-1 directional runners
- anchors:
  - `run_axis4_seq01_both_dirs.py:2-5`
  - `run_axis4_seq01_both_dirs.py:101-104`
  - `run_axis4_seq01_both_dirs.py:140-146`
  - `run_axis4_seq01_both_dirs.py:157-184`
  - `run_axis4_seq02_both_dirs.py:3-5`
  - `run_axis4_seq02_both_dirs.py:102-103`
  - `run_axis4_seq02_both_dirs.py:142-149`
  - `run_axis4_seq02_both_dirs.py:161-189`
  - `run_axis4_seq03_seq04_both_dirs.py:3-5`
  - `run_axis4_seq03_seq04_both_dirs.py:101-103`
  - `run_axis4_seq03_seq04_both_dirs.py:148-158`
  - `run_axis4_seq03_seq04_both_dirs.py:185-205`
- source role:
  - the first three runners share one executable kernel:
    - `seed=0`
    - `num_states=256`
    - `cycles=64`
    - `axis3_sign=+1`
    - `theta=0.07`
    - `n_vec=(0.3, 0.4, 0.866025403784)`
  - each script runs both polarities for both directions
  - Seq01 and Seq02 each write one result file with two SIM_ID labels
  - Seq03 and Seq04 are merged into one combined result file

### Type-2 all-sequence runner
- anchors:
  - `run_axis4_type2_all_seq_both_dirs.py:3-5`
  - `run_axis4_type2_all_seq_both_dirs.py:101-103`
  - `run_axis4_type2_all_seq_both_dirs.py:148-160`
  - `run_axis4_type2_all_seq_both_dirs.py:203-220`
- source role:
  - preserves the same fixed knobs but flips `axis3_sign=-1`
  - runs all four sequences in both directions
  - writes one Type-2 result file plus one packed evidence file with eight SIM_EVIDENCE blocks

### Executable-facing result family
- anchors:
  - `results_axis4_seq01_both_dirs.json:1-63`
  - `results_axis4_seq02_both_dirs.json:1-63`
  - `results_axis4_seq03_seq04_both_dirs.json:1-107`
  - `results_axis4_type2_all_seq_both_dirs.json:1-221`
- source role:
  - Type-1 and Type-2 outputs preserve both `plus` and `minus` metrics for forward and reverse directions
  - stored Type-1 plus-branch entropy means are direction-specific but sequence-invariant:
    - forward: `0.6164742886688184`
    - reverse: `0.5831978117405376`
  - stored Type-2 plus-branch entropy means are numerically identical to the Type-1 plus branch by direction
  - minus-branch entropy means vary by both sequence and direction in both type families

### Theory-facing aggregate sibling
- anchors:
  - `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json:1-200`
  - `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json:2-185`
  - `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json:186-200`
- source role:
  - stores `SEQ01` through `SEQ04` under `T1_fwd`, `T1_rev`, `T2_fwd`, and `T2_rev`
  - preserves the same fixed params block as the runners
  - numerically matches the runners' minus branch only; it does not carry any plus-branch metrics

## 4) Comparison Anchors
- comparison sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
- relevant anchors:
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:187-250`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:418-662`
  - `SIM_CATALOG_v1.3.md:91-95`
- bounded comparison read:
  - the catalog lists the aggregate sibling and the four executable result files side by side as one local Axis4 family
  - the top-level evidence pack records `S_SIM_AXIS4_SEQ01_FWD` through `S_SIM_AXIS4_SEQ04_REV` under code hash `b741c60dbce45bfbf221208e172117382e9ac4ec16845b36499ae9f33eb73f1a`, not under any of the four directional runner hashes in this batch
  - the top-level evidence pack separately records `S_SIM_AXIS4_SEQ_ALL_BIDIR_V1` with output hash `e088e8cea763046b6549fa995cf0bf7857b874c178af1de4a84b0489033905ec`, matching the aggregate sibling in this batch
  - no per-direction Type-2 SIM_ID blocks were found in the top-level evidence pack for this family

## 5) Source-Class Read
- Best classification:
  - Axis4 executable directional suite with one adjacent theory-facing aggregate compression surface
- Not best classified as:
  - ordinary conceptual doc extraction
  - clean single-producer provenance family
  - runtime-confirmed evidence family
- Theory-facing vs executable-facing split:
  - executable-facing:
    - four runner scripts
    - four paired result JSONs
    - fixed knob block
    - explicit result and packed-evidence write contracts
  - theory-facing:
    - `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json` as a minus-only T1/T2 compression surface
  - evidence-facing:
    - top-level evidence-pack entries that bind this family to the earlier core harness hash rather than to the directional runner hashes
- possible downstream consequence:
  - later sims summaries should keep the directional runners, their paired results, and the aggregate sibling linked but not collapsed into one implied producer path
