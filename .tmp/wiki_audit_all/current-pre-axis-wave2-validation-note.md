---
title: Current Pre-Axis Wave2 Validation Note
created: 2026-04-07
updated: 2026-04-08
type: summary
tags: [reference, research, simulation, validation]
sources:
  - raw/articles/new-READ ONLY Reference Docs_old/CURRENT_PRE_AXIS_WAVE2_VALIDATION_NOTE.md
framing: current
---

# Current Pre-Axis Wave-2 Validation Note

## Overview
Current snapshot dated 2026-04-04. Status: do not treat as closure. Records specific wave-2 simulation results that were validated.

## Validated Results
- sim_a0_kernel_discriminator.py -> PASS. Winner: K1_Ic (coherent information), score 5/6. Results in a0_kernel_discriminator_results.json.
- sim_c1_mispair_probe.py -> PASS. Verdict: operator-driven mispair behavior. The current artifact set supports an operator-structured mismatch diagnosis, but not the older `Fe/Fi universally entangling` summary. Results in `c1_mispair_probe_results.json`.
- sim_xi_bridge_bakeoff.py -> PASS. Least-arbitrary bridge family: chiral. Results in xi_bridge_bakeoff_results.json.
- sim_history_vs_pointwise_ax0.py -> PASS. Pointwise and history-window families remain distinct; no collapse claimed. Results in history_vs_pointwise_ax0_results.json.

## Additional Validation
pytest tests passed: 16/16 on test_pimono_fail_closed_edge_cases.py and test_pimono_runner_roundtrip_smoke.py.

## What This Note Does NOT Claim
- No Axis-entry closure
- No Tier 5 closure
- No C1 closure
- No Type2 Weyl inversion resolution
- No claim that pointwise and history-window families should be merged

## Related pages
- [[current-pre-axis-sim-status-keep-open-diagnostic-broken]]
- [[current-pre-axis-sim-status-wave1-refresh]]
- [[current-preaxis-status-and-ordering-note]]
