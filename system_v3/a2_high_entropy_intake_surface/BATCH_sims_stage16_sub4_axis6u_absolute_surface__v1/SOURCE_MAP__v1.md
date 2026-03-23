# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_stage16_sub4_axis6u_absolute_surface__v1`
Extraction mode: `SIM_STAGE16_SUB4_AXIS6U_ABSOLUTE_PASS`
Batch scope: standalone Stage16 absolute baseline surface centered on `run_stage16_sub4_axis6u.py` and `results_stage16_sub4_axis6u.json`, with mixed-axis6 comparison surfaces, top-level Stage16 descendants, and the adjacent terrain-only sign suite held comparison-only
Date: 2026-03-09

## 1) Batch Selection
- starting file in raw simpy folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_sub4_axis6u.py`
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_sub4_axis6u.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_stage16_sub4_axis6u.json`
- reason for bounded family:
  - `run_stage16_sub4_axis6u.py` is the next unprocessed raw-folder-order source after the Stage16 mixed-axis6 family
  - it has one direct paired result surface with the same basename
  - it is an absolute Stage16 baseline surface rather than a mixed comparison or bundle-emitted descendant
  - the adjacent `run_terrain8_sign_suite.py` changes the executable contract from a `16`-cell Stage16 lattice to a terrain-only sign sweep and is therefore deferred as the next bounded family
- comparison-only anchors read:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_axis6_mix_control.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_stage16_axis6_mix_control.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_axis6_mix_sweep.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_terrain8_sign_suite.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_terrain8_sign_suite.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- deferred next raw-folder-order source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_terrain8_sign_suite.py`

## 2) Source Membership
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_sub4_axis6u.py`
  - sha256: `98464a84cef8615d4bb84c9bc2a7587688fe5a9fcb793adc1e732c9a7c3eebe2`
  - size bytes: `8135`
  - line count: `228`
  - source role: absolute Stage16 baseline runner
- Result surface:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_stage16_sub4_axis6u.json`
  - sha256: `2cf3e5c8c0e1715efc99a0bae0ed1f495333d83344d5f63c81f3fe1d640fcbd4`
  - size bytes: `5189`
  - line count: `168`
  - source role: absolute Stage16 baseline result surface

## 3) Structural Map Of The Family
### Absolute baseline runner: `run_stage16_sub4_axis6u.py`
- anchors:
  - `run_stage16_sub4_axis6u.py:1-228`
- source role:
  - one-qubit Stage16 absolute surface with:
    - `type1` / `type2`
    - `outer` / `inner`
    - `Se` / `Ne` / `Ni` / `Si`
  - uses `512` Ginibre random states with one fixed terrain order and one fixed operator stack per stage
  - writes absolute `vn_entropy_*` and `purity_*` summaries, not mixed-vs-uniform deltas
  - emits one local SIM_ID:
    - `S_SIM_STAGE16_SUB4_AXIS6U`
- result highlights:
  - lowest entropy and highest purity cell:
    - `type1.inner.1_Se_DOWN`
    - `vn_entropy_mean = 0.5758532170682593`
    - `purity_mean = 0.6077734155352288`
  - highest entropy and lowest purity cell:
    - `type2.inner.2_Ne_UP`
    - `vn_entropy_mean = 0.6703054812599413`
    - `purity_mean = 0.5224427900155866`
  - bounded read:
    - `Se` cells stay the most ordered
    - `Ne` cells stay the most mixed

### Mixed-axis6 baseline relation
- comparison anchors:
  - `run_stage16_axis6_mix_control.py:1-217`
  - `results_stage16_axis6_mix_control.json:1-166`
- bounded comparison read:
  - the absolute `vn_entropy_mean` / `purity_mean` values here match the `U_Smean` / `U_Pmean` baseline fields in `results_stage16_axis6_mix_control.json` for all `16` cells up to floating-point noise
  - only `3` cells differ at all, and the maximum absolute difference is `1.1102230246251565e-16`
  - this makes `stage16_sub4_axis6u` the baseline anchor for the mixed-axis6 family while still remaining a separate bounded source family

### Top-level descendant relation
- comparison anchors:
  - `results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json:1-50`
  - `results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json:1-50`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:336-414`
- bounded comparison read:
  - the repo-held top-level evidence pack contains related Stage16 descendants:
    - `S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4`
    - `S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5`
  - both descendants point to code hash:
    - `8f12b695b1c284709a4868bd5a3e6e662e6caef7790275497d7b79f06598a3d9`
  - both descendants share one output hash:
    - `955244986b65a4a45227f50737471c41ebf97d1462cabdd3d5b4a8467cbf7c8e`
  - the current local surface is absent from the top-level evidence pack:
    - no `S_SIM_STAGE16_SUB4_AXIS6U` block was found
  - the contracts are not the same:
    - current result stores absolute means and extrema
    - V4 / V5 store `dS` / `dP` deltas only

### Boundary to `terrain8_sign_suite`
- comparison anchors:
  - `run_terrain8_sign_suite.py:1-137`
  - `results_terrain8_sign_suite.json:1-20`
- bounded comparison read:
  - `terrain8_sign_suite` drops the Stage16 outer / inner structure and the four-operator per-stage stack
  - it uses `256` states and `64` cycles, producing a sign-by-terrain result surface rather than a `16`-cell Stage16 lattice
  - its paired result surface exists, so it begins the next bounded family instead of staying comparison-only inside this batch

## 4) Comparison Anchors
- comparison sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_axis6_mix_control.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_stage16_axis6_mix_control.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_axis6_mix_sweep.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_terrain8_sign_suite.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_terrain8_sign_suite.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:104-146`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:336-414`
- bounded comparison read:
  - the catalog lists:
    - the current local `stage16_sub4_axis6u`
    - the Stage16 V4 / V5 descendants
    - the next raw-order `terrain8_sign_suite`
  - the top-level evidence pack contains the two descendant Stage16 delta surfaces but not the current local `S_SIM_STAGE16_SUB4_AXIS6U`
  - raw-folder adjacency does not imply family identity:
    - `stage16_sub4_axis6u` remains the absolute Stage16 baseline batch
    - `terrain8_sign_suite` starts the next bounded family

## 5) Source-Class Read
- Best classification:
  - standalone absolute Stage16 baseline surface with local evidence only and comparison links to mixed-axis6 and top-level delta descendants
- Not best classified as:
  - the same bounded family as `run_stage16_axis6_mix_control.py` / `run_stage16_axis6_mix_sweep.py`
  - the same output contract as `S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4` / `S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5`
  - the same bounded family as `run_terrain8_sign_suite.py`
- Theory-facing vs executable-facing split:
  - executable-facing:
    - current runner produces absolute means and extrema over the full Stage16 lattice
  - theory-facing:
    - current result is the clean baseline against which mixed-axis6 perturbation families can be interpreted
  - evidence-facing:
    - the local SIM_ID exists only in the local writer contract
    - top-level admission currently favors the sibling V4 / V5 delta descendants instead
- possible downstream consequence:
  - later sims interpretation should treat this batch as the absolute Stage16 baseline family and let the next raw-order batch begin at `terrain8_sign_suite`
