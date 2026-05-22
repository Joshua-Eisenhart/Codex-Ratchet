# Next Goal Prompt: QIT Engine / Manifold Basin Build

**Updated:** 2026-05-21  
**Status:** superseded by `system_v5/ops/NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md`  
**Scope:** build the geometric constraint manifold and QIT engines directly; do not continue broad wiki routing unless it is required by a named build blocker.

**Supersession note:** This prompt was useful for D89-D92 scaffold work, but it is narrower than the user's full-engine/full-manifold/full-tensor-network request. Use `system_v5/ops/QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md` and `system_v5/ops/NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md` for the next session.

## Paste-Ready Goal Prompt

Continue in `/Users/joshuaeisenhart/Desktop/Codex Ratchet`.

Read first:

- `AGENTS.md`
- `.lev/pm/handoffs/20260520-formal-manifold-tooling-retool-session-1.md`
- `system_v5/ops/formal_scouts/README.md`
- `system_v5/ops/formal_scouts/sim_two_root_constraint_qit_engine_manifold_runtime_build_probe.py`
- `system_v5/ops/formal_scouts/results/two_root_constraint_qit_engine_manifold_runtime_build_probe_results.json`
- `system_v5/ops/formal_scouts/sim_two_root_constraint_phi_engine_parameter_sweep_probe.py`
- `system_v5/ops/formal_scouts/results/two_root_constraint_phi_engine_parameter_sweep_probe_results.json`
- `system_v5/ops/formal_scouts/sim_two_root_constraint_phi_schedule_suffix_basin_probe.py`
- `system_v5/ops/formal_scouts/results/two_root_constraint_phi_schedule_suffix_basin_probe_results.json`
- `system_v5/ops/formal_scouts/sim_two_root_constraint_phi_schedule_growth_law_tau_reconciliation_probe.py`
- `system_v5/ops/formal_scouts/results/two_root_constraint_phi_schedule_growth_law_tau_reconciliation_probe_results.json`
- `system_v5/grok_sim/iters/iter_176_phi_engine_cycle_basin_structure.py`
- `system_v5/grok_sim/results/iter_176_phi_engine_cycle_basin_structure_results.json`
- `system_v5/grok_sim/results/iter_180_schedule_basin_growth_law_results.json`
- `system_v5/grok_sim/results/iter_183_schedule_basin_geometry_results.json`
- `system_v5/grok_sim/results/iter_179_phi_schedule_T1_T2_composition_results.json`

Current working architecture:

- Constraint layers act as a ratchet/admission process, not a one-shot proof.
- Terrains are Topology4 density-law stages embedded/realized on Weyl-sheet density states; they are sub pseudo-attractor components, not free-standing primitive topologies.
- An engine is an ordered inner/outer composition of terrain stages, `Phi_engine = Phi_outer o Phi_inner`.
- A fixed linear single-qubit engine is a pseudo-attractor map when it is CPTP, has a unique fixed point, converges from multiple initial states, differs by Type-1/Type-2 mirror, and is irreducible to a single terrain steady state.
- Paired engines give the natural E=16 substrate hypothesis when one qubit/site is assigned per terrain-stage or engine-stage placement. This is a simulation substrate hypothesis, not canon.
- L20/Axis0 readout is the correlational entropy family on `rho_AB`: coherent information `I_c(A->B)`, conditional entropy `S(A|B)`, and mutual information `I(A:B)`.

Current evidence to preserve:

- D89 built a source-native E=8 exact density-matrix terrain-engine runtime from `canonical_qit_engine_specs.py`, with paired E=16 substrate metadata and E=8 split entropy readouts. It does not prove a real basin, full E=16 dynamics, PEPS/PEPS3D, tensor-network evidence, or final manifold.
- D90 ported grok_sim iter_176 `Phi_engine` to exact torch Liouvillian channels and swept 1,152 parameter slices.
- D90 result: nominal iter_176 slice is monostable; `interior_multibasin_candidates=0`; `interior_finite_time_slow_convergence_cases=32`; `boundary_multifixed_or_nonconvergent_candidates=272`.
- Interpretation: the current fixed linear single-qubit `Phi_engine` is a primitive monostable pseudo-attractor in the interior. True basin plurality likely requires an added mechanism: adaptive/state-dependent switching, coupled engines, or scale/tensor-network effects.
- D91 ported grok_sim iter_179 `Phi_schedule` into exact torch schedule composition. It confirms schedule-level pseudo-attractor distinctness and noncommutativity, but tightens the sidequest claim: the exact torch port finds 2 last-engine suffix classes through length 6, not the sidequest's 4 clusters, and every fixed schedule map remains asymptotically single-basin.
- D92 resolves the D91/iter_180 discrepancy: exact torch with sidequest-aligned stage duration `tau=0.5` reproduces the four-basin growth law `[2,4,4,4,4,4]` and the two-engine suffix memory window. Exact torch with `tau=1.0` reproduces D91's two-class collapse. Stage duration is therefore a control parameter for schedule-memory depth.
- D92 also verifies the N=2 basin geometry under exact torch `tau=0.5`: coplanar rank `2`, tetrahedron volume near zero, and yin-yang axis alignment with the Hamiltonian direction about `-0.95`.

Primary objective:

Build the next real engine/manifold mechanism that could create basin plurality and nontrivial `Phi0(rho_AB)`, without overclaiming. The next work is schedule/coupling construction and testing, not wiki ingestion or another single-engine parameter sweep.

Required next work, in order:

1. **Schedule duration / memory phase scout.**
   - Sweep stage duration `tau`, coupling/timing, and possibly Hamiltonian magnitude to map where memory depth is 1 engine versus 2 engines.
   - Keep `tau=0.5` and `tau=1.0` as anchors: `tau=0.5` gives four basins / last-two memory; `tau=1.0` gives two basins / last-one memory.
   - Controls: repeated same-engine schedules, reverse-order schedules, shuffled labels, and exact fixed-eigenspace checks.

2. **Adaptive engine switching scout.**
   - Build a source-native torch scout where the engine schedule switches between terrain/order branches based on a state observable such as `sign(<Z>)`, basin sector, entropy threshold, or `Phi0` proxy.
   - Test whether the induced nonlinear/adaptive map creates two or more stable basins from different initial states.
   - Controls: fixed Type-1 only, fixed Type-2 only, random switching, shuffled terrain order, and threshold-permuted switching.

3. **Coupled two-engine scout.**
   - Build a paired-engine runtime with two E=8 engines coupled through a bounded bridge operator or local two-site interaction.
   - Read `rho_AB` and report `I_c(A->B)`, `S(A|B)`, and `I(A:B)`.
   - Controls: uncoupled product engines, shuffled bridge, zero bridge, Type-1/Type-2 swap.

4. **E=16 tensor-substrate lift.**
   - Do not attempt dense full E=16 density evolution.
   - Use a named scalable method: quantum trajectories, vectorized doubled-MPS Lindblad, non-Hermitian TEBD, or local Krylov.
   - Record tensor-site count `L`, engine-stage site count `E`, schedule-repeat count `R`, Pauli qubit count `q`, and operator count `N` separately.

5. **Basin/admission checks.**
   - A basin claim needs fixed-state/fixed-observable/generated-channel evidence, not just finite-time visual convergence.
   - Separate asymptotic fixed-point multiplicity from finite-time slow convergence.
   - Preserve boundary degeneracies as boundary evidence, not as interior basin proof.

Minimum scout contract:

- Use the Makefile interpreter: `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3`.
- Add formal scouts under `system_v5/ops/formal_scouts/`.
- Write result JSON under `system_v5/ops/formal_scouts/results/`.
- Include `classification`, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, and explicit `claim_ceiling`.
- Run `scripts/lint_sim_contract.py` on each new scout.
- Index passing scouts in `system_v5/ops/formal_scouts/README.md`.
- Update `.lev/pm/handoffs/20260520-formal-manifold-tooling-retool-session-1.md`.

Forbidden overclaims:

- Do not claim a final geometric constraint manifold.
- Do not claim real attractor basin unless fixed-state/fixed-observable/generated-channel evidence supports it.
- Do not claim PEPS/PEPS3D or full tensor-network evidence without a real implementation.
- Do not claim E=16 dense evolution from E=8 paired metadata.
- Do not treat finite-time slow convergence as multi-basin behavior.
- Do not route more wiki batches as a substitute for engine/manifold construction.

Done condition:

- At least one new source-native engine/manifold scout runs and writes a green or honestly red receipt.
- The receipt decides one bounded mechanism question: adaptive switching, coupled engines, or E=16 tensor lift.
- README and handoff are updated.
- No staging or commit unless explicitly requested.
