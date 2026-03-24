# GAIN CALIBRATION FIX NOTES

## Prompt
PRO-01: γ Calibration Fix

## Files Read
- `system_v4/a2_state/batch5_prompts/PRO-01_gamma_calibration.md`
- `system_v4/probes/gain_calibration_sim.py`
- `system_v4/probes/szilard_64stage_sim.py`
- `system_v4/a2_state/audit_logs/A2_NLM_BATCH4_FULL_SYNTHESIS__v1.md`

## Problem Observed
The original gain calibration setup reported all-negative net `ΔΦ` across the γ_sub sweep. The engine never ratcheted forward.

## Diagnosis
The failure was not just "γ too small". The larger structural problems were:

1. **Fe was symmetric across all off-diagonal modes**
   - This behaves like generic mixing and drives the state toward `I/d`.
   - That erases structure instead of building a convergent basin.

2. **All 4 operators were applied simultaneously in every stage**
   - This washed out stage identity.
   - It also made the dominant operator less dominant in practice.

3. **Ti used one measurement style everywhere**
   - NLM-17 says this should be context dependent.
   - Adiabatic / `Up` Ti should be eigenbasis-adaptive.
   - Isothermal / `Down` Ti should use computational-basis style dephasing.

4. **Te needed to stay subordinate to damping in Type-1**
   - NLM-16 gives the damped-oscillator intuition: Type-1 must be γ-dominant.
   - The original scheme still let coherent rotation compete too strongly with convergence.

5. **Fi was too weakly structural**
   - It needed to actively sharpen or flatten the spectrum depending on stage polarity.

## Changes Made in `gain_calibration_v2_sim.py`

### 1. Fe → energy-selective cooling
Replaced all-to-all dissipation with excited-to-ground transitions only:
- `|k> -> |0>` for `k = 1..d-1`

Effect:
- Fe now builds low-entropy structure instead of driving maximally mixed collapse.

### 2. Sequential dominant-first application
Instead of summing all operators into one simultaneous Lindblad step, each microstep applies:
1. dominant operator first
2. remaining operators afterward

Effect:
- preserves stage identity
- respects noncommutation more directly
- makes dominant/subordinate separation real rather than nominal

### 3. Context-sensitive Ti
- `Up` stages: eigenbasis-adaptive projectors
- `Down` stages: computational-basis projectors

Effect:
- matches the NLM-17 distinction between coherent/adiabatic vs pointer-basis/isothermal measurement

### 4. Fi → spectral shaping
- `Down` stages sharpen the spectrum
- `Up` stages flatten the spectrum slightly

Effect:
- Fi now participates in convergence vs exploration rather than acting as a weak blur

### 5. Type-1 damping bias preserved
When Te is dominant, its effective `ω` is clipped so the convergent Type-1 engine remains damping-dominant.

Effect:
- consistent with the NLM-16 `γ >= 2ω` intuition for convergence

## Local Run Results
Run configuration:
- `d = 4`
- `n_cycles = 5`
- `γ_dom = 5.0`
- sweep: `γ_sub in [0.01, 0.05, 0.10, 0.20, 0.35, 0.50, 0.75, 1.00]`

### Sweep results

| γ_sub | γ_dom/γ_sub | total ΔΦ | mean ΔΦ/cycle | status |
|---:|---:|---:|---:|:---|
| 0.01 | 500.00 | +0.236222 | +0.047244 | PASS |
| 0.05 | 100.00 | +0.249948 | +0.049990 | PASS |
| 0.10 | 50.00 | +0.267069 | +0.053414 | PASS |
| 0.20 | 25.00 | +0.301127 | +0.060225 | PASS |
| 0.35 | 14.29 | +0.351634 | +0.070327 | PASS |
| 0.50 | 10.00 | +0.401534 | +0.080307 | PASS |
| 0.75 | 6.67 | +0.481715 | +0.096343 | PASS |
| 1.00 | 5.00 | +0.534762 | +0.106952 | PASS |

### Best configuration
- `γ_sub = 1.00`
- `γ_dom / γ_sub = 5.00`
- `total ΔΦ = +0.534762`

### Threshold
- Positive regime held through the full tested range.
- In this sweep, every tested `γ_sub` produced net `ΔΦ > 0`.

## Evidence tokens produced
- `E_SIM_GAIN_PHASE_DIAGRAM_V2_OK` → PASS
- `E_SIM_CALIBRATED_RATCHET_V2_OK` → PASS

## Interpretation
The original KILL was caused more by **wrong dissipation topology** than by raw gain magnitude alone.

The key fix was making Fe **selective and convergent** instead of **symmetric and mixing**.
That, together with sequential operator application and context-sensitive Ti, was enough to recover a positive ratchet phase diagram.

## Remaining caveats
1. This is a **Type-1 convergence fix**, not yet a full Type-1 / Type-2 joint calibration theory.
2. `γ_sub` is still shared across subordinate operators rather than stage-specific.
3. The sweep shows a monotone improvement up to `γ_sub = 1.00`, so further testing above `1.00` may still be useful.
4. The current result shows that `γ >= 2ω` is a good orientation rule, but topology of Fe/Ti matters just as much as the scalar ratio.
