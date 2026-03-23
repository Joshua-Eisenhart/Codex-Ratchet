# PRO-01: γ Calibration Fix

## Context
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). Axioms: F01 (finite d), N01 (AB≠BA), CAS04 (operational equivalence). 8-stage engine, 32 microstates/type, 720° spinor. LIVE: 33 SIMs, 99 tokens, 94 PASS, 5 KILL. BANNED: "Win/Lose" use SG/EE.

## Required Reads
- `system_v4/probes/gain_calibration_sim.py`
- `system_v4/probes/szilard_64stage_sim.py`
- `system_v4/a2_state/audit_logs/A2_NLM_BATCH4_FULL_SYNTHESIS__v1.md` (NLM-16: γ≥2ω derivation)

## Problem
64-stage Lindblad engine produces ALL-NEGATIVE ΔΦ (≈ -0.41) across entire γ_sub sweep (0.01–1.0, γ_dom=5.0). The engine never ratchets forward.

Root causes to investigate:
1. Fe Lindblad operators dampen ALL d(d-1) modes equally — not energy-selective
2. All 4 operators run simultaneously per stage — maybe sequential is correct
3. γ ratio may need per-stage parameterization, not global
4. Type-1 should be γ-dominant (convergent) but Type-2 should be ω-dominant
5. NLM-16 derived γ≥2ω for critical damping from damped harmonic oscillator model

## Required Output
Save to `system_v4/probes/`:
- `gain_calibration_v2_sim.py` (the fix)
- `GAIN_CALIBRATION_FIX_NOTES.md` (what you changed and why)
- Run it and include results
