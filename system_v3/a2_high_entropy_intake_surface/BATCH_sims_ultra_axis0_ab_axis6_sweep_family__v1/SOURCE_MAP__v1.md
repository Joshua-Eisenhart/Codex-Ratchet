# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_ultra_axis0_ab_axis6_sweep_family__v1`
Extraction mode: `SIM_ULTRA_AXIS0_AB_AXIS6_SWEEP_PASS`
Batch scope: final ultra sweep family centered on `run_ultra_axis0_ab_axis6_sweep.py` and `results_ultra_axis0_ab_axis6_sweep.json`, with `ultra4` held comparison-only as the preceding full-stack expansion anchor
Date: 2026-03-09

## 1) Batch Selection
- starting file in raw simpy folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra_axis0_ab_axis6_sweep.py`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra_axis0_ab_axis6_sweep.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra_axis0_ab_axis6_sweep.json`
- reason for bounded family:
  - `run_ultra_axis0_ab_axis6_sweep.py` is the next unprocessed raw-folder-order source
  - it has one direct paired result surface with the same basename
  - it is the final `simpy/` file in raw folder order:
    - total files in `simpy/`: `51`
    - this file index: `51 / 51`
  - it forms a narrower ultra sweep family than `ultra4`, keeping Stage16 and Axis0 AB sweep structure while dropping geometry and Axis12
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra4_full_stack.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra4_full_stack.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- deferred next raw-folder-order source:
  - none; the `simpy/` raw-order strip is exhausted after this file

## 2) Source Membership
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra_axis0_ab_axis6_sweep.py`
  - sha256: `2fbb822c7b34af815572f2ecc2644e92dcc6773748c1fea7b6791da1e96dc7f4`
  - size bytes: `14854`
  - line count: `398`
  - source role: narrower ultra sweep runner
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra_axis0_ab_axis6_sweep.json`
  - sha256: `95890e976b4a9945b825c5938f956945eb8d604527760fb0a145159e68f661ef`
  - size bytes: `25814`
  - line count: `912`
  - source role: narrower ultra sweep result surface

## 3) Structural Map Of The Family
### Ultra sweep runner: `run_ultra_axis0_ab_axis6_sweep.py`
- anchors:
  - `run_ultra_axis0_ab_axis6_sweep.py:1-398`
  - `run_ultra_axis0_ab_axis6_sweep.py:300-398`
- source role:
  - one ultra sweep runner that stores:
    - `stage16`
    - `axis0_ab`
    - `seqs`
    - `entanglers`
    - `entangle_reps_list`
    - `mix_modes`
  - writes one local SIM_ID:
    - `S_SIM_ULTRA_AXIS0_AB_STAGE16_AXIS6_SWEEP`
  - current result shape:
    - `stage16` keys: `48`
    - `axis0_ab` keys: `128`
    - `seqs` keys: `4`

### Stage16 branch
- source markers:
  - `results_ultra_axis0_ab_axis6_sweep.json`
- bounded read:
  - the strongest Stage16 absolute effect is:
    - `T1_inner_1_Se_DOWN_MIX_B`
    - `dS = -0.00636023707760236`
    - `dP = 0.0054656571570509405`
  - next strongest:
    - `T2_inner_1_Se_DOWN_MIX_B`
    - `dS = -0.005866225721841478`
    - `dP = 0.0050393197924720745`
  - the strongest Stage16 cells remain Se-focused, but the absolute effect scale is materially larger than in `ultra4`

### Axis0 AB branch
- source markers:
  - `results_ultra_axis0_ab_axis6_sweep.json`
- bounded read:
  - the `axis0_ab` map uses the same mixed-record contract as `ultra4`:
    - `32` absolute `SEQ01` baseline records
    - `96` delta records for `SEQ02` through `SEQ04`
  - the strongest stored delta is:
    - `T2_REV_BELL_CNOT_R1_SEQ04`
    - `dMI = 0.13975440288608165`
    - `dSAgB = -0.1395809537781036`
    - `dNegFrac = 0.06353665865384615`
  - large deltas again concentrate in `SEQ04` reverse Bell settings

### Comparison seam to `ultra4_full_stack`
- comparison anchors:
  - `run_ultra4_full_stack.py:280-412`
  - `results_ultra4_full_stack.json:1-906`
- bounded comparison read:
  - `ultra4` and the current ultra sweep share the same:
    - `stage16` keyset
    - `axis0_ab` keyset
  - but they diverge materially in both contract and values:
    - `ultra4` adds `berry_flux_plus`, `berry_flux_minus`, and `axis12`
    - current sweep adds explicit `mix_modes`, `entanglers`, and `entangle_reps_list`
    - `T1_inner_1_Se_DOWN_MIX_B`:
      - `ultra4 dS = -0.003048738279157809`
      - `sweep dS = -0.00636023707760236`
  - the current batch is therefore not just an evidence-shortened `ultra4`

### Raw-order exhaustion read
- source markers:
  - filename inventory of `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy`
- bounded read:
  - `run_ultra_axis0_ab_axis6_sweep.py` is the last raw-order `simpy/` file
  - after this batch, the current `simpy/` raw-order intake strip is exhausted

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra4_full_stack.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra4_full_stack.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:117`
  - `SIM_CATALOG_v1.3.md:131`
  - `SIM_CATALOG_v1.3.md:148-149`
- bounded comparison read:
  - the catalog lists both `ultra4_full_stack` and `ultra_axis0_ab_axis6_sweep`
  - the repo-held top-level evidence pack contains neither `S_SIM_ULTRA4_FULL_STACK` nor `S_SIM_ULTRA_AXIS0_AB_STAGE16_AXIS6_SWEEP`
  - the current batch closes the raw-order `simpy/` strip under the stated sims-only intake rule

## 5) Source-Class Read
- Best classification:
  - standalone final ultra sweep family with Stage16 and Axis0 AB sweep structure and explicit sweep metadata
- Not best classified as:
  - a repo-top evidenced ultra surface
  - the same bounded family as `run_ultra4_full_stack.py`
  - a file that leaves more raw-order `simpy/` families after it
- Theory-facing vs executable-facing split:
  - executable-facing:
    - one runner emits Stage16 and Axis0 AB sweep layers with explicit sweep metadata
  - theory-facing:
    - one proposal-side narrowing of the ultra strip that removes the geometry and Axis12 layers
  - evidence-facing:
    - local SIM_ID exists only in the writer contract
    - current repo-held top-level evidence pack omits the family
- possible downstream consequence:
  - later sims intake can treat the raw `simpy/` strip as exhausted after this batch and move to closure audit or residual inventory work instead of further raw-order family extraction
