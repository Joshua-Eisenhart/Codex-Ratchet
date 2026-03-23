# A2 Graveyard Resurrection Audit — v1

**Timestamp:** 2026-03-23T16:01:17-07:00
**Auditor:** Antigravity (AG-09)
**Sources:**
- `system_v4/skills/intent-compiler/dna.yaml` (graveyard section)
- `system_v4/probes/a2_state/sim_results/unified_evidence_report.json`

---

## Summary

| Metric | Count |
|--------|-------|
| Total tokens in report | 99 |
| PASS | 94 |
| KILL | 5 |
| resolved_kills in dna.yaml | 3 |
| known_open_kills in dna.yaml | 6 → **5 after fix** |
| current_kills in dna.yaml | 5 |
| **Mismatches found** | **2 (same root cause)** |

---

## 1. Resolved Kills — Verification

All 3 `resolved_kills` confirmed **PASS** in the evidence report. ✅

| Token | Status in Report | Source File | Fix Description |
|-------|:---:|---|---|
| `S_SIM_DEMON_V1` | ✅ PASS | demon_fixed_sim.py (via nlm_batch2_sim.py) | basis-matched measurement |
| `S_SIM_WORLD_MODEL_V1` | ✅ PASS | world_model_sim.py | Random init + adaptive step + FEP blend (now split into 3 sub-tokens, all PASS) |
| `S_SIM_STRUCTURE_V1` | ✅ PASS | world_model_sim.py | Random init (I/d → make_random_density_matrix) (now `S_SIM_WORLD_MODEL_STRUCTURE_V1`) |

**Verdict:** All resurrections confirmed. No false recoveries.

---

## 2. Known Open Kills — Verification

| Token | Status in Report | Kill Reason | Match? |
|-------|:---:|---|:---:|
| `S_SIM_BASIN_DEPTH_V1` | KILL | NO_CORRELATION | ✅ |
| `S_SIM_SZILARD_V1` | **NOT IN REPORT** | — | ⚠️ PHANTOM |
| `S_SIM_DUAL_SZILARD_V1` | KILL | ADDITIVE | ✅ |
| `S_SIM_GAIN_CALIBRATION_V1` | KILL | NO_POSITIVE_DPHI_IN_SWEEP | ✅ |
| `S_SIM_CALIBRATED_ENGINE_V1` | KILL | BEST_DPHI=-0.411196_STILL_NEGATIVE | ✅ |
| `S_SIM_ABIOGENESIS_V1` | KILL | NO_SPONTANEOUS_LIFE | ✅ |

**Verdict:** 5/6 known_open_kills confirmed KILL. 1 phantom entry (`S_SIM_SZILARD_V1`) removed.

---

## 3. Current Kills — Verification

| Token (dna.yaml) | Actual Token in Report | Match? |
|---|---|:---:|
| `S_SIM_BASIN_DEPTH_V1` | `S_SIM_BASIN_DEPTH_V1` | ✅ |
| ~~`S_SIM_SZILARD_V1`~~ → **`S_SIM_DUAL_SZILARD_V1`** | `S_SIM_DUAL_SZILARD_V1` | ⚠️ → ✅ FIXED |
| `S_SIM_GAIN_CALIBRATION_V1` | `S_SIM_GAIN_CALIBRATION_V1` | ✅ |
| `S_SIM_CALIBRATED_ENGINE_V1` | `S_SIM_CALIBRATED_ENGINE_V1` | ✅ |
| `S_SIM_ABIOGENESIS_V1` | `S_SIM_ABIOGENESIS_V1` | ✅ |

**Verdict:** 4/5 matched on first pass. 1 misnamed token fixed.

---

## 4. Mismatches Found & Fixed

### Mismatch 1: `current_kills` — wrong token name
- **Was:** `S_SIM_SZILARD_V1`
- **Should be:** `S_SIM_DUAL_SZILARD_V1`
- **Root cause:** `szilard_64stage_sim.py` emits `S_SIM_DUAL_SZILARD_V1` (testing dual-engine additivity), not `S_SIM_SZILARD_V1`. The `current_kills` entry used a stale/shortened name.
- **Fix:** Updated `dna.yaml` `current_kills[1].token` to `S_SIM_DUAL_SZILARD_V1`.

### Mismatch 2: `known_open_kills` — phantom entry
- **Was:** Listed both `S_SIM_SZILARD_V1` AND `S_SIM_DUAL_SZILARD_V1`
- **Issue:** `S_SIM_SZILARD_V1` does not exist as a token in the evidence report. Only `S_SIM_DUAL_SZILARD_V1` is real.
- **Fix:** Removed `S_SIM_SZILARD_V1` from `known_open_kills`. List now has 5 entries (matching the 5 actual KILLs).

---

## 5. Post-Fix State

After fixes, `dna.yaml` graveyard is **fully consistent** with `unified_evidence_report.json`:

- **5 current_kills** ↔ **5 KILL tokens in report** (1:1 match)
- **5 known_open_kills** ↔ **5 KILL tokens in report** (1:1 match)
- **3 resolved_kills** → all confirmed PASS
- **0 mismatches remaining**

**Graveyard status: CLEAN** ✅
