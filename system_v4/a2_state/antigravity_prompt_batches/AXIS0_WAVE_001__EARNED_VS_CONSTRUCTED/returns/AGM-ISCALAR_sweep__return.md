# i-Scalar Functional Sweep — Return

**Date:** 2026-03-30
**Probe:** `sim_axis0_iscalar_sweep.py`
**Results file:** `a2_state/sim_results/axis0_iscalar_sweep_results.json`

---

## Winner

**Option C — Coherent Information Survival (`C_coherent_info`)**

Composite score: **0.833**

| Option | Sign consistency | Mean \|A0\| | Doctrine fit | Composite |
|---|---|---|---|---|
| C — Coherent info | 1.000 | 2.1059 | 0.500 | **0.833** |
| D — JK path entropy | 0.722 | 7.7310 | 0.556 | 0.759 |
| B — MI variance | 1.000 | 0.1823 | 0.500 | 0.561 |
| A — MI diversity | 1.000 | 0.0166 | 0.500 | 0.506 |

---

## What Option C is actually measuring

The i-scalar measures whether **negative conditional entropy (I_c) survives perturbation**. A homeostatic result means the Bell injection decays under noise — the prior does not dominate. This is the correct behavior for the current engine: the engine's entanglement is injected, not earned, so it collapses under perturbation. Option C reads that collapse with a high, consistent signal (mean |A0| = 2.106 across all 18 configs).

---

## Key finding: doctrine T1/T2 split is absent in Option C

Option C is **uniformly homeostatic across all 18 configs** (T1 homeostatic fraction = 100%, T2 allostatic fraction = 0%). The doctrine target is T1 homeostatic AND T2 allostatic. Option C gets the T1 side right and the T2 side wrong in every single config. This is not a threshold effect — the composite sweep (Phase 6 Clifford) independently confirms Option C never produces a T1/T2 polarity split at any ε (0.01 → 0.50).

**The only clean T1/T2 polarity split in the data lives in Option D at ε = 0.01 and ε = 0.12 on Clifford exclusively.** Option D is noisy (sign consistency 0.722) but carries the only engine-type discriminating signal in the dataset.

---

## What the composite sweep adds

Phase 6 Clifford Goal 3: composite `C + α·D` was swept across α ∈ {0, 0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0}. Best α = 0.0, best doctrine fit = 0.500. The composite does not improve on Option C alone — Option D's noise destroys doctrine fit at α > 0.2 without ever adding the T2-allostatic signal at the non-Clifford tori.

**The composite fix is not viable at the current carrier.**

---

## Controller decision on i-scalar selection

**Option C is the canonical i-scalar monotone for the Universal Clock** under the criterion of sign consistency and signal strength. It is the winner by composite score. Its doctrine limitation (no T2/T1 polarity split) is a real finding, not a reason to demote it — it reflects the fact that the Bell injection in the current constructive bridge is uniformly homeostatic. The doctrine gap is a property of the carrier, not a failure of the functional.

**Option D is not selected** as the canonical i-scalar but should be archived as the only known config showing a T1/T2 geometry-specific polarity split (T2/Clifford at ε = 0.01, depolarizing).

---

## Open wall this closes

AGM-07 item 2 ("i-scalar selection") is now decided: **Option C is selected.** The open controller decision is closed by the sweep evidence.

---

## What this does not solve

- The doctrine T1/T2 split is still missing. Option C does not discriminate engine type by polarity, only by magnitude (ratio T2/T1 = 0.993 — negligible). The carrier change needed to produce a clean polarity split remains unspecified.
- The i-scalar is currently applied over a Bell-injected joint state. The canonical i-scalar value over an *earned* joint state (marginal-preserving) is unmeasured because no marginal-preserving state with non-zero MI exists on the current carrier.
