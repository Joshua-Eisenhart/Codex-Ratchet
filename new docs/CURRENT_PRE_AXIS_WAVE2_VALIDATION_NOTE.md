# Current Pre-Axis Wave-2 Validation Note

Date: 2026-04-04
Status: current snapshot — do not treat as closure

Validated in the current repo state:
- `system_v4/probes/sim_a0_kernel_discriminator.py` -> PASS
  - Results saved to `system_v4/probes/a2_state/sim_results/a0_kernel_discriminator_results.json`
  - Winner: `K1_Ic` (coherent information), score 5/6
- `system_v4/probes/sim_c1_mispair_probe.py` -> PASS
  - Results saved to `system_v4/probes/a2_state/sim_results/c1_mispair_probe_results.json`
  - Verdict: operator-driven mispair behavior; Fe/Fi are universally entangling, Ti/Te are not
- `system_v4/probes/sim_xi_bridge_bakeoff.py` -> PASS
  - Results saved to `system_v4/probes/a2_state/sim_results/xi_bridge_bakeoff_results.json`
  - Least-arbitrary bridge family: `chiral`
- `system_v4/probes/sim_history_vs_pointwise_ax0.py` -> PASS
  - Results saved to `system_v4/probes/a2_state/sim_results/history_vs_pointwise_ax0_results.json`
  - Pointwise and history-window families remain distinct; no collapse claimed

Additional validation:
- `pytest -q system_v4/tests/test_pimono_fail_closed_edge_cases.py system_v4/tests/test_pimono_runner_roundtrip_smoke.py`
  - 16 passed

What this note does NOT claim:
- No Axis-entry closure
- No Tier 5 closure
- No C1 closure
- No Type2 Weyl inversion resolution
- No claim that pointwise and history-window families should be merged
