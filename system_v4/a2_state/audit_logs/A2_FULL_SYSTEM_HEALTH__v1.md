# A2 Full System Health Report — v1

**Timestamp:** 2026-03-23T16:03 PDT  
**Agent:** AG-12 (Antigravity)  
**Prompt:** `AG-12_full_health.md`

---

## 1  Executive Summary

| Metric | Value |
|--------|-------|
| Total evidence tokens | **107** |
| PASS | **102** |
| KILL | **5** |
| SIM files executed | **35** |
| SIMs clean (ALL_PASS) | 27 |
| SIMs with KILLs | 4 |
| SIMs with NO_TOKENS | 4 |
| Graph nodes | **142** |
| Graph edges | **107** |
| Witness corpus size | **703** |
| Constraint coverage | **16/16 (100%)** |
| Active workstreams | **7/7** |
| Overall verdict | **KNOWN_ISSUES · ATTENTION_REQUIRED** |

---

## 2  Token Inventory by Layer

| Layer | Name | PASS | KILL |
|-------|------|------|------|
| 0 | Axioms (F01, N01) | 3 | 0 |
| 1 | Derived Constraints | 1 | 0 |
| 2 | Arithmetic | 11 | 0 |
| 3 | Physics | 1 | 0 |
| 4 | Complexity | 3 | 0 |
| 5 | Topology / Operators | 8 | 0 |
| 6 | IGT | 4 | 0 |
| 7 | Engine Terrains | 5 | 0 |
| 8 | Advanced Theory | 66 | 0 |
| **Total** | | **102** | **0** |

> **Note:** All 5 KILLs are emitted outside the layer metadata and captured in the per-SIM results below.

---

## 3  KILL Analysis

| # | KILL Token | Source SIM | Kill Reason |
|---|-----------|-----------|-------------|
| 1 | `NO_CORRELATION` | `complexity_gap_sim.py` | Gap-scaling correlation test failed — no significant correlation detected |
| 2 | `ADDITIVE` | `szilard_64stage_sim.py` | Szilard dual-stage entropy is additive (not sub-additive as required) |
| 3 | `NO_POSITIVE_DPHI_IN_SWEEP` | `gain_calibration_sim.py` | Gain calibration sweep found no positive ΔΦ regime |
| 4 | `BEST_DPHI=-0.411196_STILL_NEGATIVE` | `gain_calibration_sim.py` | Best ΔΦ across sweep is still negative |
| 5 | `NO_SPONTANEOUS_LIFE` | `abiogenesis_sim.py` | Thermal death dominates — no spontaneous abiogenesis observed |

### Known Open KILLs (DNA Allowlisted)

These KILLs are tracked in `dna.yaml` graveyard / known-issues:

- `S_SIM_ABIOGENESIS_V1`
- `S_SIM_BASIN_DEPTH_V1`
- `S_SIM_CALIBRATED_ENGINE_V1`
- `S_SIM_DUAL_SZILARD_V1`
- `S_SIM_GAIN_CALIBRATION_V1`

---

## 4  SIM-by-SIM Results

| Status | SIM File | P | K | Evidence |
|--------|----------|---|---|----------|
| ✓ | `foundations_sim.py` | 5 | 0 | ALL_PASS |
| ✓ | `math_foundations_sim.py` | 5 | 0 | ALL_PASS |
| ✓ | `deep_math_foundations_sim.py` | 7 | 0 | ALL_PASS |
| ✓ | `arithmetic_gravity_sim.py` | 6 | 0 | ALL_PASS |
| ✓ | `proof_cost_sim.py` | 4 | 0 | ALL_PASS |
| ? | `navier_stokes_complexity_sim.py` | 0 | 0 | NO_TOKENS |
| ⚠ | `complexity_gap_sim.py` | 2 | 1 | KILL_PRESENT |
| ✓ | `topology_operator_sim.py` | 8 | 0 | ALL_PASS |
| ✓ | `igt_game_theory_sim.py` | 4 | 0 | ALL_PASS |
| ✓ | `engine_terrain_sim.py` | 3 | 0 | ALL_PASS |
| ✓ | `igt_advanced_sim.py` | 5 | 0 | ALL_PASS |
| ✓ | `godel_stall_sim.py` | 3 | 0 | ALL_PASS |
| ? | `dual_weyl_spinor_engine_sim.py` | 0 | 0 | NO_TOKENS |
| ✓ | `full_8stage_engine_sim.py` | 2 | 0 | ALL_PASS |
| ✓ | `rock_falsifier_sim.py` | 1 | 0 | ALL_PASS |
| ✓ | `constraint_gap_sim.py` | 5 | 0 | ALL_PASS |
| ⚠ | `szilard_64stage_sim.py` | 2 | 1 | KILL_PRESENT |
| ✓ | `nlm_batch2_sim.py` | 4 | 0 | ALL_PASS |
| ⚠ | `gain_calibration_sim.py` | 0 | 2 | KILL_PRESENT |
| ✓ | `demon_fixed_sim.py` | 3 | 0 | ALL_PASS |
| ✓ | `type2_engine_sim.py` | 2 | 0 | ALL_PASS |
| ✓ | `riemann_zeta_sim.py` | 2 | 0 | ALL_PASS |
| ✓ | `p_vs_np_sim.py` | 3 | 0 | ALL_PASS |
| ✓ | `navier_stokes_qit_sim.py` | 2 | 0 | ALL_PASS |
| ✓ | `consciousness_sim.py` | 2 | 0 | ALL_PASS |
| ✓ | `alignment_sim.py` | 2 | 0 | ALL_PASS |
| ⚠ | `abiogenesis_sim.py` | 1 | 1 | KILL_PRESENT |
| ✓ | `quantum_gravity_sim.py` | 2 | 0 | ALL_PASS |
| ✓ | `yang_mills_sim.py` | 2 | 0 | ALL_PASS |
| ? | `scale_testing_sim.py` | 0 | 0 | NO_TOKENS |
| ✓ | `chemistry_sim.py` | 3 | 0 | ALL_PASS |
| ✓ | `world_model_sim.py` | 3 | 0 | ALL_PASS |
| ✓ | `scientific_method_sim.py` | 3 | 0 | ALL_PASS |
| ✓ | `navier_stokes_formal_sim.py` | 6 | 0 | ALL_PASS |
| ? | `rock_falsifier_enhanced_sim.py` | 0 | 0 | NO_TOKENS |

---

## 5  Graph Stats

| Metric | Value |
|--------|-------|
| Nodes | 142 |
| Edges | 107 |
| Tokens materialized | 107 (102 PASS, 5 KILL) |
| Output | `system_v4/a2_state/graphs/probe_evidence_graph.json` |
| Worker packet | `A1_WORKER_LAUNCH_PACKET__PROBE_EVIDENCE__2026_03_23__v1.json` |
| Packet status | `READY_FROM_A2_PREBUILT_BATCH` |

---

## 6  Evidence → Witness Bridge

| Metric | Value |
|--------|-------|
| Tokens bridged | 107 |
| PASS witnesses | 102 |
| KILL witnesses | 5 |
| Total corpus entries | 703 |
| Output | `system_v4/runtime_state/probe_witnesses.json` |

---

## 7  Workstream Status

| Metric | Value |
|--------|-------|
| Active workstreams | 7/7 |
| Total workstream tokens | 66 |
| Total workstream kills | 2 |

---

## 8  Constraint Manifold Coverage

| Metric | Value |
|--------|-------|
| Total constraints | 16 |
| With SIM coverage | 16 |
| Coverage | **100%** |

---

## 9  Heartbeat Daemon Assessment

| Field | Value |
|-------|-------|
| DNA version | v1.0 |
| Probes registered | 35 |
| Runner status | ✓ OK |
| Evidence status | KNOWN_ISSUES |
| Trend | IMPROVING (PASS 95→102, +7) |
| Action | ATTENTION_REQUIRED |

---

## 10  Recommendations

1. **Fix NO_TOKEN SIMs:** `navier_stokes_complexity_sim.py`, `dual_weyl_spinor_engine_sim.py`, `scale_testing_sim.py`, `rock_falsifier_enhanced_sim.py` run successfully but emit zero EvidenceTokens — they need token emission added.
2. **Resolve open KILLs:**
   - `gain_calibration_sim.py` (2 KILLs) — re-derive ΔΦ sweep parameters or update the threshold.
   - `szilard_64stage_sim.py` — investigate sub-additivity requirement for dual-stage Szilard entropy.
   - `complexity_gap_sim.py` — strengthen correlation test or adjust gap-scaling model.
   - `abiogenesis_sim.py` — expected KILL (theoretical boundary), keep in graveyard.
3. **Trend is IMPROVING:** +7 PASS tokens since last tick, no new KILLs introduced.
