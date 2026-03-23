# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / OUTER-CACHE DISTILLATE
Batch: `BATCH_sims_axis4_p03_core_harness_family__v1`
Extraction mode: `SIM_AXIS4_CORE_PASS`

## Distillate D1
- statement:
  - the Axis4 P03 core family currently consists of two near-duplicate harnesses but one presently evidenced producer path
- source anchors:
  - `axis4_seq_cycle_sim.py:2-13`
  - `run_axis4_sims.py:2-12`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:111-183`
- possible downstream consequence:
  - later sims interpretation should preserve duplicate-harness uncertainty instead of silently canonizing one script

## Distillate D2
- statement:
  - both harnesses encode the same executable Axis4 polarity split: contract-first on `+`, redistribute-first on `-`
- source anchors:
  - `axis4_seq_cycle_sim.py:121-126`
  - `run_axis4_sims.py:101-103`
- possible downstream consequence:
  - this family is a strong executable-facing anchor for the Axis4 variance-order seam

## Distillate D3
- statement:
  - the current P03 result family is a strict Type-1 family with shared knob values: `seed=0`, `num_states=256`, `cycles=64`, `axis3_sign=+1`
- source anchors:
  - `axis4_seq_cycle_sim.py:224-231`
  - `run_axis4_sims.py:196-203`
  - all four P03 result JSONs
- possible downstream consequence:
  - later Type-2 or broader family claims must not piggyback on these files without additional source evidence

## Distillate D4
- statement:
  - `polarity_plus` is sequence-invariant in the stored P03 results, while `polarity_minus` is sequence-sensitive
- source anchors:
  - `results_S_SIM_AXIS4_SEQ01_P03.json:9-24`
  - `results_S_SIM_AXIS4_SEQ04_P03.json:9-24`
- possible downstream consequence:
  - later Axis4 summaries should talk about polarity-specific sequence sensitivity, not generic sequence sensitivity

## Distillate D5
- statement:
  - the four stored P03 output hashes align exactly with the top-level evidence-pack entries under the `axis4_seq_cycle_sim.py` hash
- source anchors:
  - four P03 result files in this batch
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:111-183`
- possible downstream consequence:
  - this makes the P03 family one of the cleaner current runner/result/evidence linkages in the sims source class

## Distillate D6
- statement:
  - the next coherent Axis4 re-entry should move from the P03 core harness family into the bidirectional suite scripts and result files
- source anchors:
  - deferred same-family sources listed in this batch
- possible downstream consequence:
  - later passes can test whether the bidirectional suite preserves or complicates the current polarity asymmetry read
