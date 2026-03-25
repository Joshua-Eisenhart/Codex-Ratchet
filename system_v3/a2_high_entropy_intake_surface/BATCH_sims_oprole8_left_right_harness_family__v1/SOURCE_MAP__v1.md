# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_oprole8_left_right_harness_family__v1`
Extraction mode: `SIM_OPROLE8_HARNESS_PASS`
Batch scope: fixed-role left/right harness centered on `run_oprole8_left_right_suite.py` and its paired result surface, with bounded comparison to later operator-role suite surfaces
Date: 2026-03-08

## 1) Batch Selection
- starting file in raw simpy folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_oprole8_left_right_suite.py`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_oprole8_left_right_suite.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_oprole8_left_right_suite.json`
- reason for bounded family:
  - `run_oprole8_left_right_suite.py` is the next unprocessed raw-folder-order source after the history strip
  - it has a direct paired result surface with the same basename
  - the runner explicitly frames itself as a harness using fixed placeholder operator matrices and says it is not claiming final `Ti/Te/Fi/Fe`
  - the adjacent `run_sim_suite_v1.py` and `run_sim_suite_v2_full_axes.py` are broader multi-sim suite surfaces, so they were read only as boundary and lineage anchors rather than merged into source membership
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v2_full_axes.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- deferred next raw-folder-order source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v1.py`

## 2) Source Membership
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_oprole8_left_right_suite.py`
  - sha256: `c03a64c2010440acb2d14c3966602d7579f43f1420ea58e367c7ea5b87316d6a`
  - size bytes: `2821`
  - line count: `88`
  - source role: fixed-role operator harness runner
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_oprole8_left_right_suite.json`
  - sha256: `55fd7768e78047fa75f928ada714c84671c7522b8ee23c345ea2c9e6cbdfb5c7`
  - size bytes: `388`
  - line count: `12`
  - source role: paired harness result surface

## 3) Structural Map Of The Family
### Runner: `run_oprole8_left_right_suite.py`
- anchors:
  - `run_oprole8_left_right_suite.py:1-4`
  - `run_oprole8_left_right_suite.py:32-47`
  - `run_oprole8_left_right_suite.py:48-61`
  - `run_oprole8_left_right_suite.py:63-85`
- source role:
  - uses four fixed operator matrices as role placeholders:
    - `R1 = Z`
    - `R2 = X`
    - `R3 = Y`
    - `R4 = H`
  - defines one observable:
    - `O = Y + 0.2*X`
  - measures left/right difference and commutator norm across `256` random density trials
  - writes one paired result JSON plus one local single-block `sim_evidence_pack.txt`
  - emits local SIM_ID:
    - `S_SIM_OPROLE8_LEFT_RIGHT_SUITE`
- bounded read:
  - this is a harness surface, not a final operator-role taxonomy claim
  - executable contract is compact and self-contained:
    - no multi-sim bundle
    - no descendant naming
    - no cross-axis story

### Result surface: `results_oprole8_left_right_suite.json`
- anchors:
  - `results_oprole8_left_right_suite.json:1-12`
- source role:
  - stores one nested `metrics` object rather than a flat result payload
  - notable stored values:
    - `R1_delta_trace_mean = 0.7608547029521484`
    - `R2_delta_trace_mean = 0.7453810932042721`
    - `R3_delta_trace_mean = 0.15033990853793744`
    - `R4_delta_trace_mean = 0.7597519757091086`
    - `R1_comm_norm_mean = 0.86430693635737`
    - `R2_comm_norm_mean = 0.8176041091889896`
    - `R3_comm_norm_mean = 0.8373920058612034`
    - `R4_comm_norm_mean = 0.8347256505653264`
- bounded read:
  - `R3` is the standout asymmetry:
    - its delta-trace mean is far lower than the other three roles
    - the observable contains `Y`, so the harness is not role-symmetric even before any theory-facing mapping

### Comparison-only successor seam
- successor anchors:
  - `run_sim_suite_v2_full_axes.py:249-282`
  - `run_sim_suite_v2_full_axes.py:423-440`
  - `results_S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1.json:1-12`
  - `run_sim_suite_v1.py:568-620`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:253-266`
- bounded comparison read:
  - `run_sim_suite_v2_full_axes.py` emits a different operator-role surface:
    - `S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1`
    - roles are `TI`, `TE`, `FI`, `FE`
    - roles are implemented as superoperators, not fixed matrices
    - result surface is flat and includes `seed` and `trials`
  - `run_sim_suite_v1.py` does not emit that operator-role suite in its current `main()`
  - the top-level evidence pack carries the `S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1` block, but its code hash matches the current `run_sim_suite_v1.py` hash rather than the current `run_sim_suite_v2_full_axes.py` hash
  - no top-level evidence-pack block was found for `S_SIM_OPROLE8_LEFT_RIGHT_SUITE`

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v2_full_axes.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:120-122`
  - `SIM_CATALOG_v1.3.md:139-142`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:253-266`
  - `run_sim_suite_v1.py:568-620`
  - `run_sim_suite_v2_full_axes.py:249-282`
  - `run_sim_suite_v2_full_axes.py:423-440`
- bounded comparison read:
  - the catalog lists `oprole8_left_right_suite` and `S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1` as separate micro surfaces
  - the later operator4 suite is descendant-like in topic but not a silent rename of `oprole8`
  - evidence admission is asymmetric:
    - direct top-level evidence for operator4 descendant exists
    - direct top-level evidence for `oprole8` was not found
  - provenance is contradictory:
    - the current evidence-pack code hash for the operator4 descendant is `1c8a7ac3...`
    - that matches the current `run_sim_suite_v1.py`
    - the current emitter of that SIM_ID is `run_sim_suite_v2_full_axes.py` with hash `dd05c8f6...`

## 5) Source-Class Read
- Best classification:
  - standalone fixed-role harness micro-family with one paired result surface
- Not best classified as:
  - the same family as the later operator4 suite descendant
  - a current top-level evidenced operator-role surface
  - a broad multi-sim bundle
- Theory-facing vs executable-facing split:
  - executable-facing:
    - one compact harness script
    - one compact nested result surface
    - one local single-block evidence emission path
  - theory-facing:
    - role names are placeholders and explicitly not the final `Ti/Te/Fi/Fe`
    - the surface is useful as an early harness for left/right operator asymmetry, not as a settled role ontology
  - evidence-facing:
    - catalog admission exists
    - repo-top evidence admission does not
- possible downstream consequence:
  - later sims interpretation should keep `oprole8` separate from the current operator4 descendant lineage and preserve the code-hash seam rather than folding them together
