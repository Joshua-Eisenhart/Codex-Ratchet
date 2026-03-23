# A2_MANIFOLD_GAP__v1 — Constraint Manifold Gap Analysis

**Date:** 2026-03-23T16:01 PDT  
**Sources:** `constraint_manifold.yaml`, `unified_evidence_report.json`  
**Scope:** Verify SIM coverage for every manifold constraint. Flag uncovered or KILL-producing. Propose new SIMs.

---

## 1. Summary

| Metric | Value |
|---|---|
| Total constraints (C1-C8 + X1-X8) | 16 |
| Constraints with ≥1 PASS-status SIM | **16** |
| Constraints with active KILL on coverage sim | **0** |
| KILLs in evidence report (total) | **5** |
| NO_TOKEN orphan sims | **4** |
| SIMs not mapped to any constraint | **~18** |
| Coverage ratio (manifold claims) | **1.00** |

**Verdict:** All 16 manifold constraints have at least one PASS-status covering SIM. No constraint is uncovered. However, the coverage is thin in places (single-sim coverage) and several KILLs exist in the broader evidence base outside the manifold's claimed coverage set.

---

## 2. Per-Constraint Coverage Verification

### Core Constraints (C1-C8)

| ID | Statement (short) | Coverage SIMs | SIM Status | Verdict |
|---|---|---|---|---|
| C1 | Finite dimension d < ∞ | foundations_sim.py | ✅ ALL_PASS | **COVERED** |
| C2 | Noncommutation AB ≠ BA | foundations_sim.py, topology_operator_sim.py | ✅ ALL_PASS | **COVERED** |
| C3 | CPTP admissibility | topology_operator_sim.py | ✅ ALL_PASS | **COVERED** |
| C4 | Operational equivalence | constraint_gap_sim.py | ✅ ALL_PASS | **COVERED** |
| C5 | Entropy monotonicity | foundations_sim.py, math_foundations_sim.py | ✅ ALL_PASS | **COVERED** |
| C6 | Dual-loop requirement | igt_advanced_sim.py | ✅ ALL_PASS | **COVERED** |
| C7 | 720° spinor periodicity | igt_advanced_sim.py, full_8stage_engine_sim.py | ✅ ALL_PASS | **COVERED** |
| C8 | Net ratchet gain ΔΦ ≥ 0 | constraint_gap_sim.py | ✅ ALL_PASS | **COVERED** |

### Cross-Cutting Properties (X1-X8)

| ID | Statement (short) | Coverage SIMs | SIM Status | Verdict |
|---|---|---|---|---|
| X1 | GT isolation from CPTP | constraint_gap_sim.py | ✅ ALL_PASS | **COVERED** |
| X2 | Chirality matters (T vs F first) | igt_game_theory_sim.py | ✅ ALL_PASS | **COVERED** |
| X3 | Attractor is Nash | igt_game_theory_sim.py | ✅ ALL_PASS | **COVERED** |
| X4 | Structure-saturation stalls | igt_advanced_sim.py | ✅ ALL_PASS | **COVERED** |
| X5 | Irrational escape from local min | igt_advanced_sim.py | ✅ ALL_PASS | **COVERED** |
| X6 | Refinement noncommutative | constraint_gap_sim.py | ✅ ALL_PASS | **COVERED** |
| X7 | Finite stability (basin escape) | constraint_gap_sim.py | ✅ ALL_PASS | **COVERED** |
| X8 | Holodeck fixed point | nlm_batch2_sim.py | ✅ ALL_PASS | **COVERED** |

---

## 3. KILL Tokens (5 active)

None of these KILLs are on sims listed as manifold coverage, but they represent open gaps in the broader evidence base:

| # | SIM Spec | Source File | Kill Reason | Manifold Relevance |
|---|---|---|---|---|
| 1 | S_SIM_BASIN_DEPTH_V1 | complexity_gap_sim.py | NO_CORRELATION | Tangential to X7 (basin stability) — complexity gap measures scaling, not basin depth |
| 2 | S_SIM_DUAL_SZILARD_V1 | szilard_64stage_sim.py | ADDITIVE | Tangential to C8 (ratchet gain) — dual Szilard test shows additive not superadditive |
| 3 | S_SIM_GAIN_CALIBRATION_V1 | gain_calibration_sim.py | NO_POSITIVE_DPHI_IN_SWEEP | **Direct threat to C8** — gain sweep finds no positive ΔΦ configuration |
| 4 | S_SIM_CALIBRATED_ENGINE_V1 | gain_calibration_sim.py | BEST_DPHI=-0.411196_STILL_NEGATIVE | **Direct threat to C8** — best calibrated engine still shows negative net gain |
| 5 | S_SIM_ABIOGENESIS_V1 | abiogenesis_sim.py | NO_SPONTANEOUS_LIFE | Not mapped to manifold — domain-specific claim |

> **⚠ WARNING:** KILLs #3 and #4 from `gain_calibration_sim.py` directly challenge **C8 (net ratchet gain ΔΦ ≥ 0)**. While `constraint_gap_sim.py` passes the C8 test, the gain calibration sim shows that under parameter sweep the net gain remains negative. This is the most significant gap in the manifold.

---

## 4. NO_TOKEN Orphan SIMs

These sims run successfully but emit no EvidenceTokens and therefore provide **zero** evidence:

| # | File | Status |
|---|---|---|
| 1 | navier_stokes_complexity_sim.py | NO_TOKENS |
| 2 | dual_weyl_spinor_engine_sim.py | NO_TOKENS |
| 3 | rock_falsifier_sim.py | NO_TOKENS |
| 4 | scale_testing_sim.py | NO_TOKENS |

**Action required:** These need to be instrumented to emit tokens (per AG-01 task) or removed from the sim roster.

---

## 5. Thin Coverage Flags

Seven constraints rely on a **single SIM** for coverage. If any of these sims is later invalidated, the constraint becomes uncovered:

| Constraint | Sole Coverage SIM |
|---|---|
| C3 (CPTP) | topology_operator_sim.py |
| C4 (Operational Equiv) | constraint_gap_sim.py |
| C6 (Dual-loop) | igt_advanced_sim.py |
| X1 (GT isolation) | constraint_gap_sim.py |
| X4 (Saturation stalls) | igt_advanced_sim.py |
| X5 (Irrational escape) | igt_advanced_sim.py |
| X8 (Holodeck FP) | nlm_batch2_sim.py |

**Risk:** `constraint_gap_sim.py` is a critical single-point-of-failure — it alone covers C4, X1, X6, X7, and partially C8. If it breaks, 5 constraints lose their only evidence.

---

## 6. Unmapped SIMs (not referenced by any constraint)

These 18 SIM files exist and emit tokens but are not mapped to any manifold constraint:

| File | Tokens | Status |
|---|---|---|
| deep_math_foundations_sim.py | 7 | ALL_PASS |
| arithmetic_gravity_sim.py | 6 | ALL_PASS |
| proof_cost_sim.py | 4 | ALL_PASS |
| complexity_gap_sim.py | 3 | KILL_PRESENT |
| engine_terrain_sim.py | 3 | ALL_PASS |
| godel_stall_sim.py | 3 | ALL_PASS |
| szilard_64stage_sim.py | 3 | KILL_PRESENT |
| demon_fixed_sim.py | 3 | ALL_PASS |
| type2_engine_sim.py | 2 | ALL_PASS |
| riemann_zeta_sim.py | 2 | ALL_PASS |
| p_vs_np_sim.py | 3 | ALL_PASS |
| navier_stokes_qit_sim.py | 2 | ALL_PASS |
| consciousness_sim.py | 2 | ALL_PASS |
| alignment_sim.py | 2 | ALL_PASS |
| abiogenesis_sim.py | 2 | KILL_PRESENT |
| quantum_gravity_sim.py | 2 | ALL_PASS |
| yang_mills_sim.py | 2 | ALL_PASS |
| chemistry_sim.py | 3 | ALL_PASS |
| world_model_sim.py | 3 | ALL_PASS |
| scientific_method_sim.py | 3 | ALL_PASS |
| gain_calibration_sim.py | 2 | KILL_PRESENT |
| navier_stokes_formal_sim.py | — | (not in report) |
| rock_falsifier_enhanced_sim.py | — | (not in report) |

---

## 7. Proposed New SIMs

### 7a. Strengthen Thin Coverage

| Proposal | Target Constraint | Rationale |
|---|---|---|
| **cptp_isolation_sim.py** | C3 | Second independent CPTP test; topology_operator_sim is currently the sole coverage. Test trace preservation + positivity on random Kraus channels. |
| **dual_loop_stall_sim.py** | C6 | Dedicated sim showing single-loop agents provably stall. Currently only tested inside igt_advanced_sim which mixes many concerns. |
| **holodeck_convergence_sim.py** | X8 | Stress-test fixed-point convergence under perturbation. Currently only nlm_batch2_sim covers this. |

### 7b. Resolve Active KILLs

| Proposal | Target KILL | Rationale |
|---|---|---|
| **gain_sweep_v2_sim.py** | gain_calibration KILL #3/#4 | Re-derive the C8 ratchet gain claim with corrected operator ordering (demon_fixed_sim proved eigenbasis fix matters). If the sweep still produces negative ΔΦ, C8 must be weakened or bounded. |
| **szilard_superadditive_sim.py** | szilard KILL #2 | Test super-additivity claim with non-identical Szilard engines. Current KILL proves identical engines are merely additive. |

### 7c. Map Unmapped Domains

| Proposal | Target Constraint | Rationale |
|---|---|---|
| **operational_equiv_v2_sim.py** | C4 | Extend C4 coverage using the deep_math_foundations probing infrastructure; current constraint_gap_sim only tests it shallowly. |
| **entropy_gravity_sim.py** | C5 | The arithmetic_gravity_sim already tests entropic gravity but isn't mapped to C5. Either map it or create a dedicated sim. |

---

## 8. Recommendations

1. **P0 — Resolve C8 tension:** The gain_calibration KILL directly contradicts the C8 net-ratchet-gain guarantee. Either fix the calibration sim (likely needs eigenbasis correction per demon_fixed_sim), or scope C8 to "under correct basis" conditions.

2. **P1 — Reduce single-point-of-failure risk:** Add second coverage sims for C3, C6, and X8 (see §7a proposals).

3. **P1 — Map unmapped sims:** At least 18 sims produce valid evidence but aren't referenced as coverage for any constraint. Update `constraint_manifold.yaml` to map relevant ones (e.g., `arithmetic_gravity_sim.py` → C5, `deep_math_foundations_sim.py` → C1).

4. **P2 — Fix NO_TOKEN orphans:** Instrument or remove the 4 orphan sims (AG-01 scope).

5. **P2 — Szilard additivity:** The ADDITIVE kill on dual-Szilard is an open question on whether the system claims super-additivity. If not claimed, close the KILL as out-of-scope.

---

**Token count at time of audit:** 100 (95 PASS / 5 KILL)  
**Manifold coverage:** 16/16 constraints covered (1.00)  
**Critical gap:** C8 ratchet gain challenged by gain_calibration_sim KILLs
