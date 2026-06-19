# Build Card: discrete_axes12_pair_v0

## Boundary

- Packet: `system_v6/sims/discrete_axes12_pair_v0/`
- Work order row: `system_v6/receipts/axis_work_order_20260612.md`, axes 1 + 2 built as a pair.
- Claim ceiling: `axis_readout_candidate_only`.
- Classification: `scratch_diagnostic`.
- Promotion allowed: `false`.
- Formal admission allowed: `false`.
- No git add/commit in this card.
- No builder `audit_verdict.md`; audits are outside this builder packet.

## Authority

- `system_v6/receipts/axes12_deep_vein_20260612.md` at `3d40599c9`: legality/kernel split, frame split with `K_t`, product semantics, maturity fences, and packet-pair design.
- `system_v6/receipts/audit_standards_codex_v1.md` at `c83842e55`: no-identity-leak, freshness, builder boundary, and future packet fields.
- `system_v6/receipts/axis_work_order_20260612.md`: axes 1 + 2 are built as a pair because they jointly factor the four perceiving-topology classes.
- `system_v6/sims/terrain_generator_sheet_packet/`: committed scratch substrate only; not dedicated axes 1/2 admission.
- Existing committed axes 0/4/5/6 packets for cumulative carrier-honest independence rows.

## Object

This packet computes a paired finite readout candidate:

- Axis 1: legality/kernel classification, `unitary` versus `proper_cptp`, computed from Kraus rank, trace preservation, Choi positivity, unitality, purity preservation, and eigenvalue preservation.
- Axis 2: frame classification, `direct` versus `conjugated`, with `K_t = i V_t^dagger dot(V_t)` computed for dynamic conjugated rows.
- Joint row: `(axis1_class, axis2_frame_class) -> product_alias`, with labels assigned after computation:
  - `(proper_cptp, direct) -> Se`
  - `(proper_cptp, conjugated) -> Ni`
  - `(unitary, direct) -> Ne`
  - `(unitary, conjugated) -> Si`

The Carnot thermodynamic strokes are fenced as a different object. This packet does not identify Carnot four strokes with the axes 1 x 2 product.

## Expected Result Surface

- `axis12_row_table`: 10 committed-substrate row readouts.
- `axis12_cell_product_table`: 33-cell carrier projection of the paired readout.
- `joint_product_table`: computed product map with aliases last.
- `stability_under_axis0_standard`: stable and changed one-step edge counts.
- `independence_rows_vs_axes0_4_5_6`: cumulative no-identity-leak rows.
- `controls`: unitary calibration, manifestly conjugated nonzero `K_t`, product-degeneracy flag, shuffled-order label failure, falsifier reachability.

## Controls

- A unitary row must classify as `axis1=unitary` with `kraus_rank=1` and purity preservation.
- A manifestly conjugated row must compute nonzero `K_t`.
- A forced-bit product degeneracy must be flagged, not accepted.
- A shuffled-label row must fail without channel/frame evidence.
- Falsifier branches must be reachable and named.

## Tool Contract

The packet uses the standard envelope helper:

```text
scripts/build_three_engine_envelope.py
```

Claim-path tools:

- Julia: `Graphs`, `Z3`.
- JAX/Python slot: `sympy`, `z3`, `cvc5` with JAX/JAX NumPy support.
- PyTorch: `torch.func`, `sympy`, `z3`, `cvc5`.

## Validator Commands

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/discrete_axes12_pair_v0/discrete_axes12_pair_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/discrete_axes12_pair_v0/discrete_axes12_pair_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/discrete_axes12_pair_v0/discrete_axes12_pair_v0_pytorch.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/discrete_axes12_pair_v0/write_envelope_spec.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/discrete_axes12_pair_v0/discrete_axes12_pair_v0_envelope_spec.json > system_v6/sims/discrete_axes12_pair_v0/results/discrete_axes12_pair_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/discrete_axes12_pair_v0/validate_discrete_axes12_pair_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/discrete_axes12_pair_v0/results/discrete_axes12_pair_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/discrete_axes12_pair_v0/tests
```

## Status

Implementation status: built in this packet. Local rerun status belongs to the validator results, not this card prose.
