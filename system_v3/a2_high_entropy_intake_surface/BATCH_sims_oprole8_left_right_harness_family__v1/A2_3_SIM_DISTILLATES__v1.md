# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_oprole8_left_right_harness_family__v1`
Extraction mode: `SIM_OPROLE8_HARNESS_PASS`

## Distillate D1
- strongest source-bound read:
  - `oprole8` is a standalone fixed-role harness family with a direct paired result surface, not a multi-sim bundle
- supporting anchors:
  - `run_oprole8_left_right_suite.py`
  - `results_oprole8_left_right_suite.json`

## Distillate D2
- strongest source-bound read:
  - the harness is explicitly executable-facing and provisional:
    - fixed matrices
    - one observable
    - one result file
    - explicit disclaimer against treating the roles as final `Ti/Te/Fi/Fe`
- supporting anchors:
  - `run_oprole8_left_right_suite.py:1-4`
  - `run_oprole8_left_right_suite.py:37-47`

## Distillate D3
- strongest source-bound read:
  - the later `S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1` surface is best treated as a separate descendant-like operator-role suite rather than a direct rename of `oprole8`
- supporting anchors:
  - `SIM_CATALOG_v1.3.md:120-122`
  - `run_sim_suite_v2_full_axes.py:249-282`
  - `run_sim_suite_v2_full_axes.py:423-440`

## Distillate D4
- evidence assumptions extracted:
  - local script evidence emission is weaker than repo-top evidence admission
  - current top-level evidence absence for `oprole8` should be preserved
  - current top-level evidence for the later operator4 descendant carries a code-hash mismatch against the current emitter file
- supporting anchors:
  - `run_oprole8_left_right_suite.py:72-83`
  - negative search across `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:253-266`

## Distillate D5
- runtime expectations extracted:
  - `oprole8` runs `256` random-density trials and computes left/right delta plus commutator norms for four fixed roles
  - it writes one nested result JSON and one single-block local evidence file
  - the later operator4 descendant uses `512` trials and a different role implementation contract
- supporting anchors:
  - `run_oprole8_left_right_suite.py:32-85`
  - `results_S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1.json`

## Distillate D6
- failure modes extracted:
  - collapsing placeholder `R1..R4` roles into final `TI/TE/FI/FE`
  - treating catalog co-location as proof of one clean lineage
  - trusting the current evidence-pack code hash for the descendant as a clean current producer path
- supporting anchors:
  - tension items `T1` through `T5`
