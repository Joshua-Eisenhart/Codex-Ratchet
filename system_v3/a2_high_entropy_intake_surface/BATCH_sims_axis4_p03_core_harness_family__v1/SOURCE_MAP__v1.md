# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis4_p03_core_harness_family__v1`
Extraction mode: `SIM_AXIS4_CORE_PASS`
Batch scope: Axis4 P03 core harness family beginning at `axis4_seq_cycle_sim.py`; two near-duplicate harnesses plus the four paired P03 result surfaces
Date: 2026-03-08

## 1) Batch Selection
- starting file in raw simpy folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/axis4_seq_cycle_sim.py`
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/axis4_seq_cycle_sim.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_sims.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS4_SEQ01_P03.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS4_SEQ02_P03.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS4_SEQ03_P03.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS4_SEQ04_P03.json`
- reason for bounded family:
  - `axis4_seq_cycle_sim.py` is the first unprocessed source in raw folder order after the prior batch
  - the nearest coherent result family is the four `results_S_SIM_AXIS4_SEQ0*_P03.json` files it writes
  - `run_axis4_sims.py` is a near-duplicate harness targeting the same P03 output family and must be read here to preserve duplicate-harness tension rather than smoothing it away
- raw-folder-order note:
  - unrelated sources intervene in the raw `simpy/` listing between `axis4_seq_cycle_sim.py` and later `run_axis4_*` directional suite scripts:
    - `mega_sims_failure_detector.py`
    - `mega_sims_run_02.py`
    - `mega_sims_trivial_check.py`
    - `prove_foundation.py`
    - early `run_axis0_*` scripts
  - this batch uses the small-related-docs rule to keep the Axis4 P03 core harness family separate from those unrelated surfaces
- deferred next meaningful same-family sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_seq01_both_dirs.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_seq02_both_dirs.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_seq03_seq04_both_dirs.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_type2_all_seq_both_dirs.py`

## 2) Source Membership
- Harness A:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/axis4_seq_cycle_sim.py`
  - sha256: `b741c60dbce45bfbf221208e172117382e9ac4ec16845b36499ae9f33eb73f1a`
  - size bytes: `8872`
  - line count: `269`
  - source role: currently evidenced Axis4 P03 harness
- Harness B:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis4_sims.py`
  - sha256: `1fac087cb9bed1e4028d93aa4f477565b9b50f78a3b1bf70e6bbd963037917b3`
  - size bytes: `7339`
  - line count: `234`
  - source role: alternate/duplicate Axis4 P03 harness surface
- Result A:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS4_SEQ01_P03.json`
  - sha256: `9a7aa90166cc0b70a33c79a10d0730e8dacc6bfc1b49b5c21a03b6a3f7606a69`
  - size bytes: `849`
  - line count: `39`
- Result B:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS4_SEQ02_P03.json`
  - sha256: `9bc8805d9ba33cb0469bb69714a4a7bd6566c78b7fc2ac3b73a0087d86069e27`
  - size bytes: `847`
  - line count: `39`
- Result C:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS4_SEQ03_P03.json`
  - sha256: `29ec1eba103c5a2e0898819130afe2244d9e3a7d28d2b634f03bd2f98ce42497`
  - size bytes: `848`
  - line count: `39`
- Result D:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS4_SEQ04_P03.json`
  - sha256: `339aeaa36d48bb4b5a04f56172f448df095572bba3d9c86b97a34521eb4d4259`
  - size bytes: `849`
  - line count: `39`

## 3) Structural Map Of The Family
### Harness A: `axis4_seq_cycle_sim.py`
- anchors:
  - `axis4_seq_cycle_sim.py:2-13`
  - `axis4_seq_cycle_sim.py:121-126`
  - `axis4_seq_cycle_sim.py:215-231`
  - `axis4_seq_cycle_sim.py:246-266`
- source role:
  - self-describes with the name `run_axis4_sims.py`
  - defines the Axis4 polarity split as:
    - polarity `+` = terrain CPTP then pinch
    - polarity `-` = unitary then terrain CPTP
  - fixes one P03 family:
    - four sequences
    - `seed=0`
    - `num_states=256`
    - `cycles=64`
    - `axis3_sign=+1`
  - writes one JSON and one `evidence_<SIM_ID>.txt` per P03 SIM_ID

### Harness B: `run_axis4_sims.py`
- anchors:
  - `run_axis4_sims.py:2-12`
  - `run_axis4_sims.py:101-103`
  - `run_axis4_sims.py:188-204`
  - `run_axis4_sims.py:215-229`
- source role:
  - encodes the same four P03 sequences and the same polarity story
  - fixes the same knob block:
    - `seed=0`
    - `num_states=256`
    - `cycles=64`
    - `axis3_sign=+1`
  - writes one combined `sim_evidence_pack.txt` rather than one evidence file per SIM_ID

### Result Surface Family: four P03 JSONs
- anchors:
  - `results_S_SIM_AXIS4_SEQ01_P03.json:1-39`
  - `results_S_SIM_AXIS4_SEQ02_P03.json:1-39`
  - `results_S_SIM_AXIS4_SEQ03_P03.json:1-39`
  - `results_S_SIM_AXIS4_SEQ04_P03.json:1-39`
- source role:
  - each result stores the same small schema:
    - `axis3_sign`
    - `cycles`
    - `n_vec`
    - `num_states`
    - `polarity_minus`
    - `polarity_plus`
    - `seed`
    - `sequence`
    - `sim_id`
    - `terrain_params`
    - `theta`
- bounded read:
  - `polarity_plus` means are identical across all four sequences
  - `polarity_minus` means vary by sequence order

## 4) Comparison Anchor
- comparison source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- relevant anchors:
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:111-183`
- bounded comparison read:
  - the top-level evidence pack records the four P03 `SIM_ID`s with:
    - code hash `b741c60dbce45bfbf221208e172117382e9ac4ec16845b36499ae9f33eb73f1a`
    - output hashes matching the four current P03 result files
  - no current evidence-pack anchor was found for the alternate harness hash `1fac087cb9bed1e4028d93aa4f477565b9b50f78a3b1bf70e6bbd963037917b3`

## 5) Source-Class Read
- Best classification:
  - Axis4 P03 core executable/result family with duplicate harness residue and one currently evidenced producer path
- Not best classified as:
  - full Axis4 suite coverage
  - Type-2 evidence family
  - ordinary conceptual doc extraction
- Theory-facing vs executable-facing split:
  - theory-facing:
    - polarity `+` as contract-first
    - polarity `-` as redistribute-first
  - executable-facing:
    - fixed knob block
    - per-sequence `SIM_ID` mapping
    - per-file vs packed evidence emission
  - evidence-facing:
    - four small JSONs and matching evidence-pack hashes
- possible downstream consequence:
  - this is the right root family for later Axis4 directional-suite intake because it fixes the core polarity story and the duplicate-harness ambiguity first
