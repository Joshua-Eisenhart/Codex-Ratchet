# BUILD CARD - basin_dof_perturb_and_read_v0

You are codex1 (builder, xhigh). Repo: `/Users/joshuaeisenhart/Codex-Ratchet`.
Build everything inside `system_v6/sims/basin_dof_perturb_and_read_v0/`
(file-disjoint). NO git add/commit. The builder must not write
`audit_verdict.md`; validator and envelope use `scripts/builder_audit_boundary.py`
fully through `builder_audit_boundary_errors(...)`.

## Authority

1. `system_v6/receipts/owner_doctrine_axes_as_existence_probes_20260612.md`
   at `fcf1b3858`: thesis 2 binds. Perturb along each engine DoF, read axes
   along the trajectory, and require at least one return DoF plus at least one
   boundary.
2. `system_v6/receipts/attractor_basin_criterion_20260611.md`: requirement 8
   is the engine-DoF perturbation test. Requirement 9 controls stay mandatory.
3. Committed basin machinery: 33-cell `R_C`, G0-G5 generating rows, may/must
   split, terminal classes, and absent-exit proofs from
   `basin_rc_transition_graph_v0` and `basin_generating_set_sweep_v0`.
4. `discrete_axis0_field_v0` at `5d330b427`: consume the polarity readout by
   source/hash and rebuild it per anti-collage.
5. `manifold_super_sim_v2_weld` at `d6815079e`: committed substrate context.

## Object

For each realizable engine DoF direction on the 33-cell carrier:

- perturb a pinned ensemble of cells with finite pinned perturbation sizes;
- evolve under the DoF's finite `R_C` transition graph;
- read the rebuilt axis0 polarity per cell along the trajectory;
- classify the direction as:
  - `RETURN`: re-enters the prior G0 terminal class and the axis0 readout
    reconverges to pre-perturbation terminal readout values;
  - `BOUNDARY`: escapes to a different terminal class, with terminal
    absent-exit checked;
  - `SCRAMBLING`: returns spatially but readout does not reconverge.

The required DoF table rows are `G0`, `G1`, `G2`, `G3L`, `G3R`, `G4`, `G5`,
`stage_shift_Rx_to_Rz`, and `loop_reverse_G5`. The committed flux direction is
recorded as not realizable on the 33-cell carrier without lifting to the flux
packet's carrier, and is not counted as a DoF row.

## Controls

- Zero perturbation must classify `RETURN`.
- Over perturbation past the carrier basin scale must classify `BOUNDARY`.
- Probe-erased constant field must classify `DEGRADED`; this proves the axis
  readout is load-bearing.
- Shuffled-order `N01` must fire and classify as boundary or scrambling.

## Fences

- Realization-relative.
- No manifold-existence claim from this packet alone.
- No axis admission.
- No basin theorem.
- `classification = scratch_diagnostic`.
- `claim_ceiling = basin_dof_readout_rows_only`.
- `promotion_allowed = false`.
- `formal_admission_allowed = false`.

## Engineering Contract

Use all three engines in honest all-three mode:

- Julia: `Graphs` and `Z3`.
- JAX/Python: `networkx`, `sympy`, `z3`, and `cvc5`.
- PyTorch: `torch.func`, `torch_geometric`, `sympy`, `z3`, and `cvc5`.

The envelope is built through `scripts/build_three_engine_envelope.py`.
SMT rows bind computed values and include erased flips. Packet-local validator,
generic strict three-engine validator, contract lint, and pytest must be run.

## Expected Commands

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/basin_dof_perturb_and_read_v0/basin_dof_perturb_and_read_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/basin_dof_perturb_and_read_v0/basin_dof_perturb_and_read_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/basin_dof_perturb_and_read_v0/basin_dof_perturb_and_read_v0_pytorch.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/basin_dof_perturb_and_read_v0/write_envelope_spec.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/basin_dof_perturb_and_read_v0/basin_dof_perturb_and_read_v0_envelope_spec.json > system_v6/sims/basin_dof_perturb_and_read_v0/results/basin_dof_perturb_and_read_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/basin_dof_perturb_and_read_v0/validate_basin_dof_perturb_and_read_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/basin_dof_perturb_and_read_v0/results/basin_dof_perturb_and_read_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v6/sims/basin_dof_perturb_and_read_v0/basin_dof_perturb_and_read_v0_common.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/basin_dof_perturb_and_read_v0/tests
```
