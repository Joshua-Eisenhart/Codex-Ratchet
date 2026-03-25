# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_terrain8_sign_suite_family__v1`
Extraction mode: `SIM_TERRAIN8_SIGN_SUITE_PASS`
Batch scope: terrain-only sign suite centered on `run_terrain8_sign_suite.py` and `results_terrain8_sign_suite.json`, with Topology4 Terrain8 and adjacent `ultra2` surfaces held comparison-only
Date: 2026-03-09

## 1) Batch Selection
- starting file in raw simpy folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_terrain8_sign_suite.py`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_terrain8_sign_suite.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_terrain8_sign_suite.json`
- reason for bounded family:
  - `run_terrain8_sign_suite.py` is the next unprocessed raw-folder-order source
  - it has one direct paired result surface with the same basename
  - its executable contract is a terrain-only repeated-cycle sign sweep, not a Stage16 lattice and not a macro composite bundle
  - the adjacent `run_ultra2_axis0_ab_stage16_axis6.py` is better treated as the next bounded family because it mixes Stage16, Axis0 AB, and Axis12 surfaces into one macro result
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_topology4_channelfamily_suite_v2.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra2_axis0_ab_stage16_axis6.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra2_axis0_ab_stage16_axis6.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- deferred next raw-folder-order source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra2_axis0_ab_stage16_axis6.py`

## 2) Source Membership
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_terrain8_sign_suite.py`
  - sha256: `ae880aada392690b6ef541c41224ebb8bbb43b90a6170e6ec1c60ccc6300a369`
  - size bytes: `4421`
  - line count: `137`
  - source role: terrain-only sign sweep runner
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_terrain8_sign_suite.json`
  - sha256: `973cc8c0e1103bebd957239c1b8ff487ed070d27286b3b988511808ea8317a1b`
  - size bytes: `792`
  - line count: `20`
  - source role: terrain-only sign sweep result surface

## 3) Structural Map Of The Family
### Terrain-only sign runner: `run_terrain8_sign_suite.py`
- anchors:
  - `run_terrain8_sign_suite.py:1-137`
- source role:
  - one-qubit sign sweep across four terrains:
    - `Se`
    - `Ne`
    - `Ni`
    - `Si`
  - repeats one unitary-plus-terrain cycle `64` times for each random state
  - compares only:
    - `plus`
    - `minus`
  - writes one local SIM_ID:
    - `S_SIM_TERRAIN8_SIGN_SUITE`
- result highlights:
  - terrain ordering is stable across both signs:
    - lowest entropy / highest purity: `Se`
    - highest entropy / lowest purity: `Ne`
  - strongest sign-sensitive terrain:
    - `Ni`
    - `abs(entropy gap) = 0.001752965040475507`
    - `abs(purity gap) = 0.0017208049418918625`
  - next-strongest sign-sensitive terrain:
    - `Si`
    - `abs(entropy gap) = 0.00113301080489836`
  - effectively sign-invariant terrain:
    - `Ne`
    - `abs(entropy gap) = 6.34164105672852e-08`

### Top-level Terrain8 comparison seam
- comparison anchors:
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:54-89`
  - `results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json:1-79`
  - `run_axis12_topology4_channelfamily_suite_v2.py:1-214`
- bounded comparison read:
  - the repo-held top-level evidence pack contains:
    - `S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1`
  - that block points to current code hash:
    - `be1a8c714b57ebfe98559d14237d85b258f760f5db2691f10b3f778660edcb12`
  - the current local SIM_ID `S_SIM_TERRAIN8_SIGN_SUITE` is absent from the top-level evidence pack
  - shared `terrain8` naming does not imply the same surface:
    - local minus `Se` entropy is `0.023571598861606945`
    - top-level `Se_sign-1_{UP,DOWN}` entropies are about `0.39937` to `0.39948`
    - local `Ne` entropy is about `0.6931459`
    - top-level `Ne_sign*_*` entropies are about `0.41221` to `0.41606`

### Boundary to `ultra2_axis0_ab_stage16_axis6`
- comparison anchors:
  - `run_ultra2_axis0_ab_stage16_axis6.py:280-382`
  - `results_ultra2_axis0_ab_stage16_axis6.json:1-332`
- bounded comparison read:
  - `ultra2` is a composite macro surface, not a terrain-only suite
  - its stored result mixes:
    - `stage16` with `48` keys
    - `axis0_ab` with `16` keys
    - `axis12` with `8` keys
  - the catalog lists `ultra2`, but the repo-held top-level evidence pack has no `S_SIM_ULTRA2_AXIS0_AB_STAGE16_AXIS6` block
  - raw-order adjacency therefore marks the next family boundary rather than an in-batch extension

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_topology4_channelfamily_suite_v2.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra2_axis0_ab_stage16_axis6.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra2_axis0_ab_stage16_axis6.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:13`
  - `SIM_CATALOG_v1.3.md:59`
  - `SIM_CATALOG_v1.3.md:77`
  - `SIM_CATALOG_v1.3.md:115`
  - `SIM_CATALOG_v1.3.md:128`
  - `SIM_CATALOG_v1.3.md:146-147`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:54-89`
- bounded comparison read:
  - the catalog gives the local terrain-only suite and the top-level `TOPOLOGY4` Terrain8 descendant overlapping terrain language
  - only the top-level `S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1` has repo-held evidence-pack admission
  - `ultra2` is catalog-visible but not evidence-pack-visible in the current repo-held pack

## 5) Source-Class Read
- Best classification:
  - standalone terrain-only sign sensitivity surface with local evidence only and a strong naming/provenance seam against the top-level `TOPOLOGY4` Terrain8 descendant
- Not best classified as:
  - the same bounded family as `run_axis12_topology4_channelfamily_suite_v2.py`
  - the repo-top admitted Terrain8 surface
  - the same bounded family as `run_ultra2_axis0_ab_stage16_axis6.py`
- Theory-facing vs executable-facing split:
  - executable-facing:
    - one qubit
    - one repeated unitary-plus-terrain cycle
    - `256` states and `64` cycles
    - eight final mean metrics only
  - theory-facing:
    - isolates sign sensitivity across the four terrain types without Stage16, Axis0 AB, or topology machinery
  - evidence-facing:
    - the local SIM_ID is writer-local only
    - repo-top Terrain8 evidence currently points to a different Axis12/Topology4 family
- possible downstream consequence:
  - later terrain interpretation should treat this batch as the local terrain-sign family and not collapse it into the evidenced Topology4 Terrain8 surface or the adjacent `ultra2` macro bundle
