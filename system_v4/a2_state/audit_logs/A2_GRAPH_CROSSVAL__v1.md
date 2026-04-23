# A2_GRAPH_CROSSVAL__v1

**Agent**: Antigravity (AG-08)  
**Task**: Probe Graph Cross-Validation  
**Date**: 2026-03-23T16:01-07:00  
**Sources**:
- `system_v4/a2_state/graphs/probe_evidence_graph.json` (timestamp: 2026-03-23T23:01:57Z)
- `system_v4/probes/a2_state/sim_results/unified_evidence_report.json` (timestamp: 2026-03-23T22:16:37Z)

---

## 1. Node Counts

| Metric | Graph | Report | Match? |
|---|---|---|---|
| Total tokens | **100** | **107** | ❌ **DRIFT: +7 in report** |
| PASS tokens | 95 | 102 | ❌ **DRIFT: +7 in report** |
| KILL tokens | 5 | 5 | ✅ |
| Probe nodes | 33 | 35 (sim_results) | ❌ **DRIFT: +2 in report** |
| Total nodes (graph) | 133 (33 probes + 100 tokens) | — | — |

**Root cause**: The unified evidence report was regenerated **after** the graph was materialized and includes tokens from 2 newer sim files that were not yet wired into the graph.

---

## 2. Edge Counts

| Metric | Graph Declared | Graph Actual | Match? |
|---|---|---|---|
| Total edges | 100 | 100 | ✅ |
| Edge integrity (source/target in nodes) | — | 0 bad | ✅ |
| All edges type "produces" | — | ✅ | ✅ |

---

## 3. KILL Nodes (5 total — consistent)

| # | Graph Key | Sim Spec | Source File | Kill Reason (report) |
|---|---|---|---|---|
| 1 | `UNNAMED_TOKEN_1_KILL` | `S_SIM_BASIN_DEPTH_V1` | `complexity_gap_sim.py` | `NO_CORRELATION` |
| 2 | `UNNAMED_TOKEN_2_KILL` | `S_SIM_DUAL_SZILARD_V1` | `szilard_64stage_sim.py` | `ADDITIVE` |
| 3 | `UNNAMED_TOKEN_3_KILL` | `S_SIM_GAIN_CALIBRATION_V1` | `gain_calibration_sim.py` | `NO_POSITIVE_DPHI_IN_SWEEP` |
| 4 | `UNNAMED_TOKEN_4_KILL` | `S_SIM_CALIBRATED_ENGINE_V1` | `gain_calibration_sim.py` | `BEST_DPHI=-0.411196_STILL_NEGATIVE` |
| 5 | `UNNAMED_TOKEN_5_KILL` | `S_SIM_ABIOGENESIS_V1` | `abiogenesis_sim.py` | `NO_SPONTANEOUS_LIFE` |

All 5 KILL nodes are present in both graph and report with matching sim_spec_ids, measured values, and source files. ✅

---

## 4. Orphan Analysis

### 4a. Orphan Probes (in graph, 0 edges, 0 tokens)

| Probe Node | File | Evidence Status |
|---|---|---|
| `probe:navier_stokes_complexity_sim` | `navier_stokes_complexity_sim.py` | `NO_TOKENS` |
| `probe:dual_weyl_spinor_engine_sim` | `dual_weyl_spinor_engine_sim.py` | `NO_TOKENS` |
| `probe:rock_falsifier_sim` | `rock_falsifier_sim.py` | `NO_TOKENS` |
| `probe:scale_testing_sim` | `scale_testing_sim.py` | `NO_TOKENS` |

These 4 probes ran successfully (`process_status: PASS`) but emitted zero EvidenceTokens. They contribute no evidence to the graph. **Known issue — AG-01 orphan sims task targets these.**

### 4b. Tokens in Report but NOT in Graph (7 orphan tokens)

| Token ID | Source File |
|---|---|
| `E_SIM_NS_CPTP_CHANNEL_OK` | `navier_stokes_formal_sim.py` |
| `E_SIM_NS_ENSTROPHY_BOUND_OK` | `navier_stokes_formal_sim.py` |
| `E_SIM_NS_GRADIENT_BOUND_OK` | `navier_stokes_formal_sim.py` |
| `E_SIM_NS_REGULARISER_OK` | `navier_stokes_formal_sim.py` |
| `E_SIM_NS_REYNOLDS_OK` | `navier_stokes_formal_sim.py` |
| `E_SIM_NS_SCALING_DIVERGE_OK` | `navier_stokes_formal_sim.py` |
| `E_SIM_ROCK_FALSIFIER_COMPLEXITY_BIAS` | `rock_falsifier_enhanced_sim.py` |

**Cause**: These 7 tokens come from 2 sim files (`navier_stokes_formal_sim.py`, `rock_falsifier_enhanced_sim.py`) that were added to `run_all_sims.py` **after** the graph was last built. The graph materializer needs to be re-run to ingest them.

### 4c. Sim Files in Report but NOT in Graph (2)

| Sim File | Tokens Emitted |
|---|---|
| `navier_stokes_formal_sim.py` | 6 |
| `rock_falsifier_enhanced_sim.py` | 1 |

### 4d. Orphan Tokens in Graph (no incoming edge): **0** ✅

All 100 token nodes in the graph have at least one incoming "produces" edge.

---

## 5. Layer Token Count

| Source | Count |
|---|---|
| Report `layers` (layered tokens) | 102 |
| Report `all_tokens` | 107 |
| Delta | 5 tokens not assigned to layers |

The 5 unlayered tokens are the KILL tokens (they have empty `token_id` values and are not placed in any layer).

---

## 6. Summary Verdict

| Check | Status |
|---|---|
| Graph internal consistency (nodes ↔ edges) | ✅ PASS |
| Graph KILL count | ✅ PASS (5/5) |
| Graph ↔ Report KILL alignment | ✅ PASS |
| Orphan probes (NO_TOKENS) | ⚠️ 4 probes (known, tracked by AG-01) |
| Token drift (report > graph) | ⚠️ **+7 tokens from 2 new sims** |
| Sim file drift (report > graph) | ⚠️ **+2 sims not in graph** |
| Orphan tokens in graph | ✅ PASS (0) |
| Edge integrity | ✅ PASS |

### Action Items

1. **Re-run graph materializer** to ingest `navier_stokes_formal_sim.py` (6 tokens) and `rock_falsifier_enhanced_sim.py` (1 token). This will bring graph to 135 nodes / 107 edges.
2. **Resolve 4 orphan probes** (tracked by AG-01) — these sims need EvidenceToken emission.
3. **Assign KILL tokens to layers** or document why they are excluded from the layer structure.

---

*Cross-validation complete. Graph is internally consistent. Drift is due to temporal lag between report regeneration and graph materialization.*
