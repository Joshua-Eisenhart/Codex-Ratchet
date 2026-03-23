# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_oprole8_left_right_harness_family__v1`
Extraction mode: `SIM_OPROLE8_HARNESS_PASS`

## Cluster A
- cluster label:
  - fixed-role harness core
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_oprole8_left_right_suite.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_oprole8_left_right_suite.json`
- family role:
  - standalone micro harness for left/right operator asymmetry
- executable-facing read:
  - fixed matrices `R1..R4`, one observable, one result surface, one local evidence block
- theory-facing read:
  - role names are explicit placeholders rather than a final taxonomy
- tension anchor:
  - direct catalog admission exists without matching top-level evidence-pack admission

## Cluster B
- cluster label:
  - operator4 descendant comparison seam
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v2_full_axes.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- family role:
  - comparison-only descendant-like operator-role surface
- executable-facing read:
  - later suite uses `TI/TE/FI/FE` superoperators and emits a flat result object with `seed` and `trials`
- theory-facing read:
  - same broad left/right operator topic, but at a different abstraction level from `oprole8`
- tension anchor:
  - the descendant is evidenced at repo-top level while `oprole8` is not

## Cluster C
- cluster label:
  - provenance mismatch anchors
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v1.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
- family role:
  - boundary and provenance anchors, not source membership for this batch
- executable-facing read:
  - current `run_sim_suite_v1.py` main does not emit `S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1`
- evidence-facing read:
  - current top-level evidence pack still uses the current `run_sim_suite_v1.py` hash for that descendant block
- tension anchor:
  - current code-hash attribution and current emitter path do not line up

## Cross-Cluster Read
- `oprole8` is best treated as a separate harness family
- the later operator4 suite is a comparison successor, not a merged source member here
- evidence and provenance split three ways:
  - catalog keeps both micro surfaces
  - repo-top evidence keeps only the later operator4 descendant
  - current code-hash attribution for that descendant points at the wrong current suite file
