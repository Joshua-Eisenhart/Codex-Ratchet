# AGW2-03 Shell-History Hybrid Probe Spec and Start

## Recommended Model
Codex-class or strong technical model

## Background
AGM-05 (Wave 001) established the Typed Shell Cut Contract: `(r, w_r, A_r|B_r, ρ_r)_r`.
AGM-08 identified the only viable path for shell to re-earn executable status as a History-Shell Hybridization:
`Ξ_shellhist: h ↦ {(r, w_r, ρ_{A_rB_r}^h)}_r`

This probe must prove whether the hybrid can add structural value to the history window by:
- Taking the existing `Xi_hist` history window output
- Applying a shell/radial band partition to produce a family of bipartite states indexed by shell layer `r`
- Checking whether the per-shell states `ρ_r` have non-trivial MI AND marginal deviation below a budget

The existing probes to build on:
- `sim_axis0_fe_indexed_xi_hist.py` — FE-indexed Xi_hist, which already has a layer-indexing structure
- `sim_axis0_dynamic_shell.py` — dynamic shell geometry
- `axis0_xi_strict_bakeoff_sim.py` — the strict bakeoff framework
- `engine_core.py` — `axis0_history_window_snapshot`, stage/subcycle history

## Task

**Part 1: Read and audit the existing closest probes**

Read:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis0_fe_indexed_xi_hist.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis0_dynamic_shell.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/AXIS0_TYPED_SHELL_CUT_CONTRACT.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/AXIS0_XI_HIST_STRICT_OPTIONS.md`

Determine: does any existing probe already implement the shell-indexed bipartite output? If yes, what does it show? If no, what is the exact gap in the code?

**Part 2: Build `sim_axis0_phase7_shell_hist_hybrid.py`**

The probe must:
1. Run the engine and collect the full history (using `GeometricEngine.run_cycle`)
2. Apply a 3-band shell partition: `r ∈ {inner_core, boundary, outer_rim}` — indexed by stage number within the 8-stage cycle (stages 0-2: inner_core, stages 3-5: boundary, stages 6-7: outer_rim)
3. For each shell band `r`, compute the history-window aggregated bipartite state `ρ_r` (L|R cut restricted to stages in band `r`)
4. For each `ρ_r`, measure: `MI(ρ_r)`, `marginal_deviation(ρ_r)`, `coherent_info(ρ_r)`
5. Report whether any `ρ_r` has MI > 0.01 AND marginal_deviation < 0.1

**Run the probe and save results to:** `a2_state/sim_results/axis0_phase7_shell_hist_hybrid.json`

## Write

**Probe:** `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis0_phase7_shell_hist_hybrid.py`

**Return:**
`/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/antigravity_prompt_batches/AXIS0_WAVE_002__EARNED_INFO_SEARCH/returns/AGW2-03_shell_hist_hybrid_spec__return.md`

## Required return sections

- `Gap audit result` (does any existing probe already do this?)
- `Shell-band MI results` (actual numbers per band per torus)
- `Marginal deviation per band` (actual numbers)
- `Does any shell band produce non-trivial earned MI`
- `What this means for Xi_shellhist viability`

## Anti-smoothing rule
If the shell partition collapses to ρ_product at all bands, say so explicitly. Do not describe the probe as "promising" without numbers. If any band shows non-trivial MI, report the marginal_deviation simultaneously — not separately.
