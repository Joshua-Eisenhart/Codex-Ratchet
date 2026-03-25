# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_stage16_axis6_mix_control_sweep_family__v1`
Extraction mode: `SIM_STAGE16_AXIS6_MIX_FAMILY_PASS`
Batch scope: Stage16 mixed-axis6 comparison family centered on `run_stage16_axis6_mix_control.py` and `run_stage16_axis6_mix_sweep.py`, with `run_stage16_sub4_axis6u.py` held as the uniform-baseline comparison anchor
Date: 2026-03-09

## 1) Batch Selection
- starting file in raw simpy folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_axis6_mix_control.py`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_axis6_mix_control.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_axis6_mix_sweep.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_stage16_axis6_mix_control.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_stage16_axis6_mix_sweep.json`
- reason for bounded family:
  - `run_stage16_axis6_mix_control.py` is the next unprocessed raw-folder-order source
  - `run_stage16_axis6_mix_sweep.py` is immediately adjacent in raw order and shares the same:
    - terrain order
    - outer / inner axis6 patterns
    - operator family
    - Stage16 stage labeling
    - result contract built around `dS` / `dP` against a uniform baseline
  - both have direct paired result surfaces with matching basenames
  - the next adjacent Stage16 file, `run_stage16_sub4_axis6u.py`, is better treated as comparison-only because it is the exact uniform-baseline anchor rather than a mixed-axis6 comparison surface
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_sub4_axis6u.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_stage16_sub4_axis6u.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- deferred next raw-folder-order source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_sub4_axis6u.py`

## 2) Source Membership
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_axis6_mix_control.py`
  - sha256: `eae10800e8f7bfdc9b5172de0f3c5a2860d8ef7030e073e8d8ea20c2379da29d`
  - size bytes: `7772`
  - line count: `217`
  - source role: paired uniform-vs-mixed control runner
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_axis6_mix_sweep.py`
  - sha256: `2ddb438803d9f8673070f9d8c1f62684c5ad72242a6855d70dd60dc27643d78c`
  - size bytes: `7847`
  - line count: `219`
  - source role: mixed-pattern sweep runner
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_stage16_axis6_mix_control.json`
  - sha256: `935cf461f8c002c61e28a227ff313c0b1495682bc043810387d077f8efdfc46f`
  - size bytes: `4388`
  - line count: `166`
  - source role: paired control result surface
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_stage16_axis6_mix_sweep.json`
  - sha256: `0b5212ec02c3134a5c87aaad64436b9da39fee7009d4a2ee76727e53d4ad6504`
  - size bytes: `6041`
  - line count: `262`
  - source role: paired mix-mode sweep result surface

## 3) Structural Map Of The Family
### Control runner: `run_stage16_axis6_mix_control.py`
- anchors:
  - `run_stage16_axis6_mix_control.py:1-217`
- source role:
  - compares one mixed intra-stage axis6 pattern against the uniform baseline for each Stage16 cell
  - uses the same starting `rho0` for the uniform and mixed branch inside each trial
  - emits one SIM_ID:
    - `S_SIM_STAGE16_AXIS6_MIX_CONTROL`
- result highlights:
  - strongest absolute entropy shift:
    - `type1.inner.1_Se_DOWN.dS = -0.003179466511197049`
  - strongest positive entropy shift:
    - `type1.outer.1_Se_UP.dS = 0.002944306968714838`
  - `Ne` and `Si` stages are exactly or near-exactly zero in several cells

### Sweep runner: `run_stage16_axis6_mix_sweep.py`
- anchors:
  - `run_stage16_axis6_mix_sweep.py:1-219`
- source role:
  - expands the comparison from one mixed pattern to three mix modes:
    - `MIX_A`
    - `MIX_B`
    - `MIX_R`
  - measures each mix mode against the uniform baseline
  - emits one SIM_ID:
    - `S_SIM_STAGE16_AXIS6_MIX_SWEEP`
- result highlights:
  - strongest absolute entropy shift:
    - `type2.inner.4_Si_DOWN.MIX_B.dS = 0.012297811982750595`
  - strongest absolute purity shift:
    - `type2.inner.4_Si_DOWN.MIX_B.dP = -0.010416817457124194`
  - randomized `MIX_R` sometimes exceeds fixed patterns, especially in Type1 `Se` / `Ni` cells

### Uniform-baseline comparison anchor: `run_stage16_sub4_axis6u.py`
- anchors:
  - `run_stage16_sub4_axis6u.py:1-228`
  - `results_stage16_sub4_axis6u.json:1-168`
- bounded comparison read:
  - the `U_Smean` and `U_Pmean` baseline values in `results_stage16_axis6_mix_control.json` match the absolute `vn_entropy_mean` and `purity_mean` values in `results_stage16_sub4_axis6u.json` exactly for all `16` stage cells
  - this makes `sub4_axis6u` the correct comparison anchor, but not the same bounded family:
    - it is an absolute uniform-axis6 surface
    - it does not compare mixed patterns

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_sub4_axis6u.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_stage16_sub4_axis6u.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:110-112`
  - `SIM_CATALOG_v1.3.md:143-145`
- bounded comparison read:
  - the catalog groups all three raw surfaces together under Stage16:
    - `stage16_axis6_mix_control`
    - `stage16_axis6_mix_sweep`
    - `stage16_sub4_axis6u`
  - searching the repo-held top-level evidence pack found no block for:
    - `S_SIM_STAGE16_AXIS6_MIX_CONTROL`
    - `S_SIM_STAGE16_AXIS6_MIX_SWEEP`
    - `S_SIM_STAGE16_SUB4_AXIS6U`
  - the evidence gap is therefore batch-wide, not just one file-specific omission

## 5) Source-Class Read
- Best classification:
  - tight two-run Stage16 mixed-axis6 comparison family with one absolute baseline anchor held comparison-only
- Not best classified as:
  - one fully evidenced Stage16 family
  - same bounded family as `stage16_sub4_axis6u`
  - same source family as the bundle-style `sim_suite_v1` or `sim_suite_v2`
- Theory-facing vs executable-facing split:
  - executable-facing:
    - `mix_control` is a paired comparison against one mixed pattern
    - `mix_sweep` is a three-mode sweep against the same uniform baseline
  - theory-facing:
    - the family isolates whether intra-stage axis6 mixing perturbs the Stage16 baseline and how strongly by mix mode
  - evidence-facing:
    - catalog admission exists
    - repo-top evidence-pack admission is absent
- possible downstream consequence:
  - later sims interpretation should treat this batch as the Stage16 mixed-axis6 comparison family, with `sub4_axis6u` as its baseline reference rather than as the same bounded source family
