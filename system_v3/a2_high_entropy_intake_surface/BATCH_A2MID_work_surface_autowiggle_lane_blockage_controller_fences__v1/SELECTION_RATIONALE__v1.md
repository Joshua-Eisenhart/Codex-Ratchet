# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_work_surface_autowiggle_lane_blockage_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why This Parent
- `BATCH_work_surface_autowiggle_lane_blockage__v1` was the strongest remaining work-surface blockage packet on the controller action board
- it compresses the zero-canon autowiggle diagnosis, raw extract drift, and the first fail-closed external A1 lane shell into one bounded family
- reducing it now gives the controller smaller failure-class and workaround-routing fences instead of another broad archaeology packet

## Why This Reduction Goal
- bounded goal:
  - isolate controller-usable rules for blockage classification, raw-drift preservation, ascent-proof gating, fail-closed shell mechanics, and offload-versus-repair routing
- excluded for now:
  - claiming the autowiggle lane is repaired
  - treating selector output as proof of internal maturity
  - smoothing the raw count drift into one cleaned history

## Deferred Alternatives
- `BATCH_work_surface_autowiggle_fix_and_a1_firewall__v1`
  - strongest immediate follow-on once the blockage packet is narrowed
- `BATCH_a2feed_thread_b_3_4_2_bootpack_source_map__v1`
  - strongest next compact grammar/admissibility packet after the current work-surface pair
