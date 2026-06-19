# geo_s6_s7_mode_sweep_v0 build card

Status: builder-lane packet only. No audit verdict is included.

Ceiling:
- `classification=scratch_diagnostic`
- `promotion_allowed=false`
- `formal_admission_allowed=false`

Scope:
- Build a file-disjoint S6/S7 mode sweep under `system_v6/sims/geo_s6_s7_mode_sweep_v0/`.
- Read committed parents hash-bound:
  - `system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json`
  - `system_v6/sims/geo_s7_discrete_refinement_v0/results/geo_s7_discrete_refinement_v0_envelope_results.json`
- Replicate the committed mode-sweep caveat machinery from `geo_s2_s5_mode_sweep_v0` and `geo_s3_s4_mode_sweep_v0`.
- Do not touch active lanes:
  - `terrain_spinor_shell_nest_v0`
  - `ratchet_s2_three_shell_chain_v0`
  - `engine_readout_strategy_fidelity_v0`

Required outputs:
- `geo_s6_s7_mode_sweep_v0.py`
- `geo_s6_s7_mode_sweep_v0_julia.jl`
- `validate_geo_s6_s7_mode_sweep_v0.py`
- `results/geo_s6_s7_mode_sweep_v0_julia_results.json`
- `results/geo_s6_s7_mode_sweep_v0_envelope_results.json`
- `results/geo_s6_s7_mode_sweep_v0_validator_results.json`

Required rows:
- S6 RESTRICTED: shell-band restriction over committed leakage rows with computed class narrowing and byte-exact no-op control.
- S6 QUOTIENTED: lens-quotient class-level well-definedness for preserve/move/cross/leave taxonomy, with exclusions named when pre-quotient data is required.
- S7 RESTRICTED: sub-grid reruns over reduced `N` support with 2:1 cover honored.
- S7 QUOTIENTED: lens-order commensurability rows with honest incommensurate failures.
- N01 order rows for S6 and S7 with both pipelines emitted and gap reported.

Non-claims:
- No RATCHETED mode.
- No promotion.
- No bridge, physics, runtime, or Axis closure.
