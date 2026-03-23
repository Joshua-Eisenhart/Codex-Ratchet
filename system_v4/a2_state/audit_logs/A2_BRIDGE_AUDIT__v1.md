# A2_BRIDGE_AUDIT__v1

**Auditor:** Antigravity (AG-07)  
**Date:** 2026-03-23T16:01Z  
**Source prompt:** `batch5_prompts/AG-07_bridge_audit.md`  
**Bridge script:** `system_v4/skills/evidence_witness_bridge.py`  
**Evidence report:** `system_v4/probes/a2_state/sim_results/unified_evidence_report.json`  
**Witness corpus:** `system_v4/runtime_state/probe_witnesses.json`

---

## 1. Bridge Run Summary

| Metric | Value |
|---|---|
| Tokens in evidence report | 100 |
| PASS tokens | 95 |
| KILL tokens | 5 |
| Witnesses created this run | 100 |
| Total corpus size (append-only) | 596 |
| POSITIVE witnesses in corpus | 570 |
| NEGATIVE witnesses in corpus | 26 |

**Verdict:** ✅ Bridge runs clean. Every token in `all_tokens` was converted to a Witness and recorded.

---

## 2. Missing Witnesses Check

> Every token in `unified_evidence_report.json` → does it have a witness?

**Result: ✅ ZERO missing witnesses.**

All 95 unique non-empty `token_id` values in the report have corresponding witnesses in the corpus. The 5 KILL tokens have empty `token_id` fields (by design — killed specs don't mint evidence IDs) but still produce NEGATIVE witnesses keyed by `sim_spec_id`.

---

## 3. Orphan Witnesses Check

> Are there witnesses in the corpus that don't correspond to any current token?

**Result: ⚠️ 3 orphan token_ids detected (from prior bridge runs).**

| Orphan token_id | Probable Origin |
|---|---|
| `E_SIM_DUAL_SZILARD_OK` | Was PASS in earlier run, now KILL |
| `E_SIM_STRUCTURE_DISCOVERED_OK` | Duplicate — still present in current report |
| `E_SIM_WORLD_MODEL_LEARNS_OK` | Duplicate — still present in current report |

**Root cause:** The corpus is append-only. Successive bridge runs stack witnesses. The 2 "duplicates" are false positives — they exist in the current report AND in prior runs. `E_SIM_DUAL_SZILARD_OK` is a true orphan: the spec now KILLs, but the old PASS witness persists in the ledger.

**Risk:** LOW. Append-only design is intentional. No data loss. Consumers should filter by `recorded_at` or latest run if they want current state.

---

## 4. KILL Tagging Audit

All 5 KILL tokens produce **NEGATIVE** witnesses with proper tagging:

| sim_spec_id | kill_reason | BoundaryTag | Violations |
|---|---|---|---|
| `S_SIM_BASIN_DEPTH_V1` | `NO_CORRELATION` | BLOCKED | `KILL:NO_CORRELATION` |
| `S_SIM_DUAL_SZILARD_V1` | `ADDITIVE` | BLOCKED | `KILL:ADDITIVE` |
| `S_SIM_GAIN_CALIBRATION_V1` | `NO_POSITIVE_DPHI_IN_SWEEP` | BLOCKED | `KILL:NO_POSITIVE_DPHI_IN_SWEEP` |
| `S_SIM_CALIBRATED_ENGINE_V1` | `BEST_DPHI=-0.411196_STILL_NEGATIVE` | BLOCKED | `KILL:BEST_DPHI=-0.411196_STILL_NEGATIVE` |
| `S_SIM_ABIOGENESIS_V1` | `NO_SPONTANEOUS_LIFE` | BLOCKED | `KILL:NO_SPONTANEOUS_LIFE` |

**Verdict:** ✅ All KILL tokens correctly tagged. `violations[]` contains the `KILL:` prefix + reason. `touched_boundaries` includes `BoundaryTag.BLOCKED`. The bridge logic at line 46–55 is working correctly.

---

## 5. NO_TOKENS Sims (Not Bridgeable)

4 simulation files run successfully but emit **zero EvidenceTokens**, so the bridge has nothing to convert:

| File | evidence_status |
|---|---|
| `navier_stokes_complexity_sim.py` | NO_TOKENS |
| `dual_weyl_spinor_engine_sim.py` | NO_TOKENS |
| `rock_falsifier_sim.py` | NO_TOKENS |
| `scale_testing_sim.py` | NO_TOKENS |

**Impact:** These sims are invisible to the witness system. They pass as processes but produce no auditable evidence. The orphan-sim fix task (conversation `6bf9a47a`) was dispatched to address this.

---

## 6. Bridge Code Observations

1. **Token routing** (line 77): Falls back from `all_tokens` → `evidence_ledger`. Current report uses `all_tokens`. ✅ Correct.
2. **AXIOM/F01/N01 → STABLE** (line 52): Foundation tokens get `BoundaryTag.STABLE`. ✅ Working.
3. **KILL → BLOCKED** (line 54): Checks for literal `"KILL"` in status string. ✅ Matches KILL status.
4. **Append-only corpus** (line 79): `WitnessRecorder` loads existing file before appending. Each run adds a full copy of all tokens. This causes corpus growth ~100 entries/run. Acceptable for current scale.

---

## 7. Verdict

| Check | Status |
|---|---|
| Bridge runs without error | ✅ PASS |
| Every token gets a witness | ✅ PASS |
| Missing witnesses | ✅ 0 |
| Orphan witnesses | ⚠️ 3 (expected, append-only) |
| KILL tagging correct | ✅ PASS |
| BLOCKED boundaries set | ✅ PASS |
| Violations array populated | ✅ PASS |
| NO_TOKENS sims flagged | ⚠️ 4 sims produce no tokens |

**Overall: PASS.** The evidence→witness bridge is functionally correct. All tokens are bridged, KILL tagging works, and boundary values are properly set. The two open items (orphan accumulation and NO_TOKENS sims) are known and tracked.
