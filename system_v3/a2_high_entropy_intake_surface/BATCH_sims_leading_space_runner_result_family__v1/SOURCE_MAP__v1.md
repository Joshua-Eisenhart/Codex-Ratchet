# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_leading_space_runner_result_family__v1`
Extraction mode: `SIM_RUNNER_RESULT_PASS`
Batch scope: first executable-facing sims batch in folder order; three leading-space `simpy` runners plus their paired `simson` JSON results; `__pycache__` excluded from source membership
Date: 2026-03-08

## 1) Batch Selection
- selected runner sources in exact folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_axis0_boundary_bookkeep_sweep_v2.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_axis12_axis0_link_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_mega_axis0_ab_stage16_axis6.py`
- paired result sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_boundary_bookkeep_sweep_v2.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_axis0_link_v1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_mega_axis0_ab_stage16_axis6.json`
- reason for bounded family:
  - these are the first meaningful executable/result sources after the top-level docs batch
  - the three runners share one filesystem irregularity class: literal leading-space basenames
  - each runner advertises one paired JSON artifact and an evidence-pack sidecar, allowing a clean runner/result coupling pass without executing anything
- explicitly excluded from source membership:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/__pycache__/ run_axis0_boundary_bookkeep_sweep_v2.cpython-313.pyc`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/__pycache__/ run_axis12_axis0_link_v1.cpython-313.pyc`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/__pycache__/ run_mega_axis0_ab_stage16_axis6.cpython-313.pyc`
- deferred next meaningful noncache source in folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/axis4_seq_cycle_sim.py`

## 2) Source Membership
- Runner A:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_axis0_boundary_bookkeep_sweep_v2.py`
  - sha256: `845b9a5c1957d611706233216c2ff3c1f27b5950ee76bb9c1a4b56f98aaf5b39`
  - size bytes: `9360`
  - line count: `277`
  - paired result: `results_axis0_boundary_bookkeep_sweep_v2.json`
- Result A:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_boundary_bookkeep_sweep_v2.json`
  - sha256: `903340f0dc0c13ff670e8273b9ad00df9c76f016397b179d6dd8095af3c33b24`
  - size bytes: `4572`
  - line count: `174`
- Runner B:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_axis12_axis0_link_v1.py`
  - sha256: `e26448f38d58f47a10a2fef76afdf76786141dc2e3c94cf1cfb30ceefb35f193`
  - size bytes: `12436`
  - line count: `342`
  - paired result: `results_axis12_axis0_link_v1.json`
- Result B:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_axis0_link_v1.json`
  - sha256: `ab6d8e02ccccdf72e6f289e849908c74e5cd952ec02d4953af3b1f9a195854f1`
  - size bytes: `20344`
  - line count: `721`
- Runner C:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/ run_mega_axis0_ab_stage16_axis6.py`
  - sha256: `8f12b695b1c284709a4868bd5a3e6e662e6caef7790275497d7b79f06598a3d9`
  - size bytes: `14769`
  - line count: `380`
  - paired result: `results_mega_axis0_ab_stage16_axis6.json`
- Result C:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_mega_axis0_ab_stage16_axis6.json`
  - sha256: `f6c16532bdb3eea470e7dd5617c811dfc996e811ea08e37bfff6291a7a68f461`
  - size bytes: `11176`
  - line count: `350`

## 3) Structural Map Of The Runner/Result Family
### Pair A: boundary bookkeeping sweep
- runner anchors:
  - ` run_axis0_boundary_bookkeep_sweep_v2.py:4-12`
  - ` run_axis0_boundary_bookkeep_sweep_v2.py:150-158`
  - ` run_axis0_boundary_bookkeep_sweep_v2.py:181-215`
  - ` run_axis0_boundary_bookkeep_sweep_v2.py:221-275`
- result anchors:
  - `results_axis0_boundary_bookkeep_sweep_v2.json:2-21`
  - `results_axis0_boundary_bookkeep_sweep_v2.json:22-167`
  - `results_axis0_boundary_bookkeep_sweep_v2.json:168-174`
- source role:
  - sweeps three boundary record bandwidth classes: `REC1`, `REC3`, `REC9`
  - compares `SEQ01` versus `SEQ02`
  - spans axis3 sign `+/-` and init modes `GINIBRE` / `BELL`
  - emits one evidence block keyed to delta metrics between the two sequence orders
- bounded read:
  - result contains `12` run buckets and `4` `REC9` buckets

### Pair B: Axis12/Axis0 link variants
- runner anchors:
  - ` run_axis12_axis0_link_v1.py:137-164`
  - ` run_axis12_axis0_link_v1.py:186-249`
  - ` run_axis12_axis0_link_v1.py:297-336`
- result anchors:
  - `results_axis12_axis0_link_v1.json:2-240`
  - `results_axis12_axis0_link_v1.json:242-480`
  - `results_axis12_axis0_link_v1.json:482-720`
- source role:
  - defines three variants: `canon`, `swap`, `rand`
  - calculates combinatorial Axis12 edge counts for `SEQ01`-`SEQ04`
  - separately computes Axis0 metrics across the same four sequences, two signs, and two init modes
  - emits three evidence blocks, one per variant
- bounded read:
  - result contains `3` variants
  - each variant contains `4` Axis12 sequence entries and `4` Axis0 sequence entries

### Pair C: mega aggregate family
- runner anchors:
  - ` run_mega_axis0_ab_stage16_axis6.py:189-208`
  - ` run_mega_axis0_ab_stage16_axis6.py:210-245`
  - ` run_mega_axis0_ab_stage16_axis6.py:249-378`
- result anchors:
  - `results_mega_axis0_ab_stage16_axis6.json:2-195`
  - `results_mega_axis0_ab_stage16_axis6.json:196-240`
  - `results_mega_axis0_ab_stage16_axis6.json:241-350`
- source role:
  - combines one-qubit Stage16 uniform-vs-mixed comparisons with AB Axis0 trajectory suites
  - spans four seeds, four terrain sequences, forward/reverse direction, two axis3 signs, and two init modes
  - emits one compact evidence block against the combined aggregate
- bounded read:
  - result contains `32` `axis0_ab` entries
  - result contains `16` `stage16` entries
  - result uses `4` seeds

## 4) Shared Engineering Pattern
- each runner defines local sha256 helpers and writes JSON first, then evidence-pack text:
  - ` run_axis0_boundary_bookkeep_sweep_v2.py:17-25`
  - ` run_axis12_axis0_link_v1.py:11-19`
  - ` run_mega_axis0_ab_stage16_axis6.py:11-19`
- each runner hard-codes deterministic-looking knob blocks:
  - Pair A: `seed=0`, `trials=512`, `cycles=64`
  - Pair B: `seed=0`, `trials=128`, `cycles=16`
  - Pair C: `seeds=[0,1,2,3]`, `stage_states=1024`, `axis0_trials=256`, `axis0_cycles=64`
- source-class read:
  - this family is executable-facing and result-facing, not theory-only
  - it is still upper-lane source corpus for sims intake, not earned evidence by itself in this batch
