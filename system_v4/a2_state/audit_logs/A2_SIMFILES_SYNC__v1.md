# A2_SIMFILES_SYNC — Audit Log v1

**Timestamp:** 2026-03-23T16:01 PDT  
**Prompt:** AG-06_simfiles_sync  
**Agent:** Antigravity  

---

## Objective

Sync the `SIM_FILES` list in `run_all_sims.py` with all `*_sim.py` files on disk in `system_v4/probes/`.

## Findings

### Files on disk: 35
### Files in SIM_FILES before sync: 33

### Missing from SIM_FILES (2 files added):

| File | Result File |
|---|---|
| `navier_stokes_formal_sim.py` | `navier_stokes_formal_results.json` |
| `rock_falsifier_enhanced_sim.py` | `rock_falsifier_enhanced_results.json` |

Both were added to the `SIM_FILES` list and the `result_files` mapping dict.

## Verification — `run_all_sims.py` Output

All **35/35** SIMs execute with `proc=PASS`.

### Token Summary

| Metric | Count |
|---|---|
| **Total tokens** | **107** |
| PASS | 102 |
| KILL | 5 |

### By Layer

| Layer | Name | PASS | KILL |
|---|---|---|---|
| 0 | Axioms | 3 | 0 |
| 1 | Derived Constraints | 1 | 0 |
| 2 | Arithmetic | 11 | 0 |
| 3 | Physics | 1 | 0 |
| 4 | Complexity | 3 | 0 |
| 5 | Topology/Operators | 8 | 0 |
| 6 | IGT | 4 | 0 |
| 7 | Engine Terrains | 5 | 0 |
| 8 | Advanced Theory | 66 | 0 |

### SIMs with KILL tokens (4)

| SIM | Kill Reason |
|---|---|
| `complexity_gap_sim.py` | NO_CORRELATION |
| `szilard_64stage_sim.py` | ADDITIVE |
| `gain_calibration_sim.py` | NO_POSITIVE_DPHI_IN_SWEEP, BEST_DPHI=-0.411196_STILL_NEGATIVE |
| `abiogenesis_sim.py` | NO_SPONTANEOUS_LIFE |

### SIMs with NO_TOKENS (4)

| SIM | Note |
|---|---|
| `navier_stokes_complexity_sim.py` | Runs but emits no EvidenceTokens |
| `dual_weyl_spinor_engine_sim.py` | Runs but emits no EvidenceTokens |
| `scale_testing_sim.py` | Runs but emits no EvidenceTokens |
| `rock_falsifier_enhanced_sim.py` | Runs but emits no EvidenceTokens |

## Status

**COMPLETE** — SIM_FILES synced. 35/35 execute. 107 tokens (102P / 5K).
