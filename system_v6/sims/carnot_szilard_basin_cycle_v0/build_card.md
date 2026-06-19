# BUILD CARD -- carnot_szilard_basin_cycle_v0

packet: `carnot_szilard_basin_cycle_v0`
scope: `system_v6/sims/carnot_szilard_basin_cycle_v0/`
boundary: file-disjoint packet build only. NO git add/commit.
classification: `scratch_diagnostic`
row_classification: `classical_baseline` for classical legality anchors only.
promotion_allowed: false
formal_admission_allowed: false

## Authority

- Doctrine commit `24d03db89`: basin-cycle ledger closure, basin-Landauer floor, computed structure map.
- Blind panel 7 commit `1f8ddb9e1`: floor `ln(m)`, closure `dissipation >= ln(m) - r`, Szilard honesty clause, alternation gap `D-I ~ 2ue[A,B]`.
- Stroke map commit `e0d6f5055`: build only per-cycle typed counting ledger, packet-local record rows, floor test, and structure-map table.
- Consumed rows: RETURN DoF `f41d4c311`; classical fences `e10273983` and `d79d71a0d`; committed D/I alternation anchors.

## Object

The packet computes, for each committed RETURN DoF row `G0`, `G2`, and `stage_shift_Rx_to_Rz`:

- `m_sample` from distinct sampled perturbed cells in the committed trajectory rows.
- `m_full_graph` from the finite graph cells that relax to the committed terminal class.
- `floor_nats = ln(m)` for both readings.
- packet-local syndrome tables for perfect, erased, and over-recorded records.
- closure rows under the finite state-plus-record convention.
- the Szilard honesty row: a perfect record can make immediate dissipation zero only when the reset charge remains `ln(m)`.

Controls:

- record-erased: floor binds fully.
- over-recorded: reset charge appears.
- commuting D/I: `D=UEUE`, `I=EUEU` collapse when `U,E` commute.
- noncommuting D/I: small-stroke gap is compared to `2ue[A,B]`.
- shuffled-order N01: reset/readout/relax order is rejected.
- mis-ledgered omitted reset charge: caught by the closure/SMT gate.

## Six Honest Boundaries

1. Heat/work variables on the basin carrier remain open; no `q_hot`, `q_cold`, `work_out`, or temperature variable is faked.
2. The basin record object is packet-local. The Z4 packet is cited only as the convention.
3. The basin-Landauer floor is typed counting nats, not thermodynamic heat.
4. A basin analogue of adiabatic isolation or bath-gating remains open; boundaries 1 and 4 stay open.
5. Spatial/readout return is not ledger closure; closure is computed separately.
6. No physics, bridge, M(C), Axis0 admission, engine placement, QCA/index, or manifold admission claim.

## Engineering Contract

- all three engine lanes: Julia, JAX, PyTorch.
- standard helper envelope: `scripts/build_three_engine_envelope.py`.
- honest `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, and `TOOL_INTENT_MATRIX`.
- SMT gates bind computed m/floor/reset values and flip under erased/misledger controls.
- packet-local validator plus `validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent`.
- pytest coverage for floor, closure, honesty, alternation, controls, map boundaries, and validator pass.
