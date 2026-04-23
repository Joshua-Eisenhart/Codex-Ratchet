# AGW2-01 Phase 5D — Maximum Earned Information Search

## Recommended Model
Strong code + synthesis (Sonnet or Opus class)

## Background
Wave 001 established:
- Phase 4: 69 candidates searched. Constructive winner = `20_cross_s1_symmetric_retro` with MI ~1.54 bits. `matched_marginal_winner = null`. Marginal deviation 0.655–0.784 for all candidates.
- Phase 5A: Nelder-Mead optimizer (15 restarts, 12 blocks) confirms max marginal-preserving MI = product state (≈ 10⁻¹⁵). `best_source = product_seed` in all 12 blocks.
- Phase 5C: Temporal ordering is noise (0/6 signal). Weyl/chirality axis is the surviving earned lever.
- Wave 001 AGM-08 controller verdict: Phase 5D should search ONLY chirality-indexed states under strict marginal-proximity budget.

## Task
Build and run `sim_axis0_phase5d_max_earned_info.py`.

**This probe must:**

1. Construct a search family restricted to Weyl/chirality-indexed states — states where the coupling parameter is a function of LR-asymmetry (Weyl geometry), NOT retro-temporal weighting.

2. Use a marginal-proximity budget: search for ρ_AB where `d(ρ_AB, ρ_A ⊗ ρ_B) < ε` (Frobenius distance from product state) for ε ∈ {0.01, 0.05, 0.10, 0.20}.

3. For each ε budget, find the state in the chirality-indexed family with maximum correlation to the geometry ramp (not raw MI — correlation to `lr_asym` trajectory).

4. Report per ε-budget: `max_geometry_correlation`, `marginal_deviation`, `MI_at_winner`, `is_product_state_dominant`.

5. If `is_product_state_dominant = True` at all ε, the chirality-indexed earned-info lane is closed on this carrier and must be logged.

**Read first:**
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis0_phase5a_marginal_preserving.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis0_phase4_final_bridge.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis0_phase5c_earned_vs_smuggled.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/engine_core.py`

**Existing results to reference:**
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/axis0_phase4_results.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/axis0_phase5a_results.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/axis0_phase5c_results.json`

## Write

**Probe:** `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis0_phase5d_max_earned_info.py`

**Results:** auto-saved to `a2_state/sim_results/axis0_phase5d_results.json` by the probe

**Return:**
`/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/antigravity_prompt_batches/AXIS0_WAVE_002__EARNED_INFO_SEARCH/returns/AGW2-01_phase5d_max_earned_info__return.md`

## Required return sections

- `What the search family was` (exact parameterization used)
- `What the ε-budget sweep found` (actual numbers per ε)
- `Is the chirality-indexed earned-info lane open or closed on this carrier`
- `What changes if the carrier changes`
- `Best next test if lane is closed` / `Best next test if lane is open`

## Anti-smoothing rule
Do not report "the probe ran" without the actual numbers. Do not promote any non-zero MI result to earned closure without confirming `marginal_deviation < ε` for the budget used.
