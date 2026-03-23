# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_state_transition_chain_a_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved Tensions
- preserve the tension that summary attributes the run to `replay` while still marking `needs_real_llm true`
- preserve the tension that summary, soak, and sequence counters preserve `3` A1 steps while canonical state and executed events preserve only `2`
- preserve the tension that summary/state bind to `3ce0407f...` while the last executed event ends on `232c1595...`
- preserve the tension that the third strategy survives in `zip_packets/` and sequence counters while no third-step export, snapshot, SIM packet, or event row exists
- preserve the tension that the second-step proposal advances both lanes to `S0002` while final survivors advance only `S_BIND_ALPHA_ALT_ALT_S0002` and keep the target lane at `S_BIND_ALPHA_S0001`
- preserve the tension that step `2` records `SCHEMA_FAIL / ITEM_PARSE / STAGE_2_SCHEMA_CHECK` while the paired second export leaves the target `NEGATIVE_CLASS` blank
- preserve the tension that the root keeps an exact duplicate ` 3` file family and runtime-path leakage inside archived event rows

## Non-Smoothing Rule
- this reduction does not flatten the parent into either:
  - a three-step completed run
  - or a cleanly replay-classified two-step closure story
- the usable controller read is narrower:
  - keep executed state and queued continuation distinct
  - keep lineage labels and demand flags distinct
  - keep target-lane stall, duplicate-family residue, and runtime-path leakage explicit
