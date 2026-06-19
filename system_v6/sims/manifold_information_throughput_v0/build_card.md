# manifold_information_throughput_v0 build card

classification: scratch_diagnostic
promotion_allowed: false
formal_admission_allowed: false
cost: LIGHT-SYMBOLIC
log_base: e

## Scope

Answer the owner question: how much information is processed over the committed manifold/channel/ratchet surfaces.

This packet computes fresh rows for:

- S4 channel throughput for `D_z`, `D_x`, `R_x`, and `R_z`.
- S5 pinned-time affine-flow throughput for the eight committed terrain flows.
- The committed eight-stage word and the density/spinor 720 double-traversal readout boundary.
- The ratchet information account: conditioning, quotient loss, retained record, and state-level loss without record.

## Parent Lineage

Parents are read as committed `HEAD:<path>` blobs and hash-bound in the result envelope:

- `manifold_entropy_ledger_v0`: typed entropy conventions and chain-rule control.
- `geo_s4_operator_stage_v0`: S4 qubit channel rows.
- `geo_s5_terrain_flows_v0`: S5 affine-flow rows.
- `compression_flow_radiated_record_v0`: radiated-record framing and record/account comparison.
- `engine_readout_spinor_lift_v0` and `engine_readout_strategy_fidelity_v0`: distinguishability/readout and 720 anchors.
- ratchet packets: `ratchet_s6_terrain_operator_shell_v0`, `ratchet_s6_terrain_sweep_v0`, and `ratchet_deep_chain_v0`.

## Computation Contract

- Entropy and information units are natural nats.
- Channel "input-output mutual information" is the Holevo information of the pinned uniform six-state Pauli ensemble unless a row explicitly says "capacity".
- Exact capacity rows are claimed only for dephasing and unitary/dephasing-like rows where the channel class earns it.
- General affine terrain rows emit certified pinned-ensemble lower bounds and honest quantum-capacity/coherent-information bounds.
- The 720 row separates density-quotient throughput from spinor-lift/readout record throughput.
- Entropy rows are readouts of channel/constraint structure, not primitive doctrine.

## Builder Output

Expected artifacts:

- `manifold_information_throughput_v0_jax.py`
- `manifold_information_throughput_v0_julia.jl`
- `manifold_information_throughput_v0_envelope.py`
- `validate_manifold_information_throughput_v0.py`
- `results/manifold_information_throughput_v0_jax_results.json`
- `results/manifold_information_throughput_v0_julia_results.json`
- `results/manifold_information_throughput_v0_envelope_results.json`

No separate audit verdict file is part of this packet.
