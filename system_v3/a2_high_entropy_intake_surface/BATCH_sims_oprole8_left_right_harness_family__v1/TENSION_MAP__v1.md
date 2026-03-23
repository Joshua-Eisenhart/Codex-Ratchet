# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_oprole8_left_right_harness_family__v1`
Extraction mode: `SIM_OPROLE8_HARNESS_PASS`

## T1) Harness status vs final operator-role interpretation
- source markers:
  - `run_oprole8_left_right_suite.py:1-4`
  - `run_oprole8_left_right_suite.py:37-43`
- tension:
  - the runner explicitly says it is a harness using fixed matrices for `R1..R4`
  - the comment also explicitly says it is not claiming final `Ti/Te/Fi/Fe`
- preserved read:
  - do not silently translate `R1..R4` into the later operator-role taxonomy
- possible downstream consequence:
  - `oprole8` should remain a precursor or sibling harness, not a renamed current role suite

## T2) Catalog keeps `oprole8` and `S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1` as separate micro surfaces
- source markers:
  - `SIM_CATALOG_v1.3.md:120-122`
- tension:
  - both surfaces live under `MICRO: Operator roles`
  - they are listed as separate result families rather than one canonical rename chain
- preserved read:
  - keep the split explicit even though both target left/right operator behavior
- possible downstream consequence:
  - later operator-role mapping should preserve a harness-to-descendant seam

## T3) `oprole8` has a local evidence contract but no repo-top evidence-pack block
- source markers:
  - `run_oprole8_left_right_suite.py:72-83`
  - negative search across `SIM_EVIDENCE_PACK_autogen_v2.txt`
- tension:
  - the script writes a local `SIM_EVIDENCE` block for `S_SIM_OPROLE8_LEFT_RIGHT_SUITE`
  - the repo-held top-level evidence pack contains no matching block
- preserved read:
  - keep local evidencing distinct from top-level evidence admission
- possible downstream consequence:
  - this batch should stay proposal-side in provenance strength

## T4) Current evidence-pack code hash for the operator4 descendant points at the wrong current suite file
- source markers:
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:253-266`
  - `run_sim_suite_v1.py:568-620`
  - `run_sim_suite_v2_full_axes.py:423-440`
- tension:
  - the top-level evidence pack gives `S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1` the code hash `1c8a7ac3...`
  - that hash matches the current `run_sim_suite_v1.py`
  - the current file that actually emits `S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1` is `run_sim_suite_v2_full_axes.py`, whose hash is `dd05c8f6...`
- preserved read:
  - do not treat current evidence-pack code attribution as clean provenance for the current emitter path
- possible downstream consequence:
  - later lineage work must distinguish output continuity from current-script provenance

## T5) `oprole8` result schema differs materially from the later operator4 descendant
- source markers:
  - `results_oprole8_left_right_suite.json:1-12`
  - `results_S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1.json:1-12`
- tension:
  - `oprole8` stores one nested `metrics` object and omits explicit `seed` and `trials`
  - the later operator4 descendant stores a flat object and includes `seed = 0` and `trials = 512`
- preserved read:
  - do not overstate continuity just because both surfaces report `*_delta_trace_mean` and `*_comm_norm_mean`
- possible downstream consequence:
  - later comparisons should treat schema and runtime contract drift as real lineage evidence

## T6) `oprole8` role behavior is visibly asymmetric before any later role taxonomy is imposed
- source markers:
  - `run_oprole8_left_right_suite.py:45-61`
  - `results_oprole8_left_right_suite.json:2-10`
- tension:
  - three role deltas cluster around `0.745` to `0.761`
  - `R3_delta_trace_mean` drops to `0.15033990853793744`
- preserved read:
  - keep the harness asymmetry explicit rather than smoothing it into a uniform operator-role baseline
- possible downstream consequence:
  - later role interpretation should account for observable-choice bias inside the harness
