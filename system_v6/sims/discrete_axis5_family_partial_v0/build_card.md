# Build Card: discrete_axis5_family_partial_v0

## Boundary

- Packet: `system_v6/sims/discrete_axis5_family_partial_v0/`
- Work order row: `system_v6/receipts/axis_work_order_20260612.md`, Axis-5 operator-family selection.
- Claim ceiling: `axis_readout_candidate_only`.
- Status: `PARTIAL`, operator-family half only.
- Classification: `scratch_diagnostic`.
- Promotion allowed: `false`.
- Formal admission allowed: `false`.
- No git add/commit in this card.
- No builder `audit_verdict.md`; audit verdicts are outside this builder packet.

## Authority

- `system_v6/receipts/axes45_deep_vein_20260612.md`: Axis 5 has an independently pinned `{Ti,Te}` versus `{Fi,Fe}` operator-family half, while the full `axis5 x axis6` substage product remains blocked.
- `system_v6/receipts/axis_work_order_20260612.md`: Axis 5 is last of axes 0-6, with family split committed and substage product blocked on the substage-transition convention.
- `system_v6/sims/source_locked_operator_base_packet/`: source-locked `Ti`, `Te`, `Fi`, and `Fe` forms, with scratch/source-lock ceiling only.
- `system_v6/sims/discrete_axis0_field_v0/`: shared 33-cell carrier.
- `system_v6/sims/discrete_axis6_precedence_v0/`: Axis-6 rows used only for carrier-honest 6/5 independence checks, not for building a substage product.

## Object

This packet computes a finite partial Axis-5 family readout over the shared 33-cell carrier:

- Rows: 33 carrier cells x 4 source-locked operator rows = 132 rows.
- Dephasing side: `{Ti,Te}`.
- Unitary side: `{Fi,Fe}`.
- Witnesses computed per row:
  - entropy production `S(Phi(rho))-S(rho) >= 0`;
  - contractivity to the maximally mixed state;
  - purity preservation under unitary conjugation;
  - orbit norm preservation.
- Label drift is not resolved. `FeFi-vs-TeTi` and `FeFi-vs-TiTe` are carried as unresolved annotations only.
- The substage-product rows are explicit blocked rows. They are not built.

## Expected Result Surface

- `axis5_family_table`: 132 rows with computed entropy, purity, contractivity, orbit, family, and sign witnesses.
- `family_counts`: 66 `dephasing_gradient_side`, 66 `unitary_hamiltonian_side`, 0 primary-table `boundary` rows.
- `controls`: weak-dephasing-near-unitary boundary, shuffled-order, commuting controls, and pure controls.
- `independence_rows_vs_axes0_6`: computed carrier-honest 0/5 and 6/5 rows under the no-identity-leak rule.
- `substage_product_rows`: 4 blocked rows for the 2 x 2 `axis5 x axis6` product.
- `label_drift`: unresolved annotation state.

## Controls

- Weak-dephasing-near-unitary boundary row is computed and flagged `boundary`.
- Shuffled-order preserves family counts.
- Commuting controls keep `Ti/Fe` and `Te/Fi` neutral while `Ti/Fi` remains noncommuting.
- Pure controls preserve unitary purity and expose dephasing fixed-point boundary behavior.
- Operator labels are reported as an identity leak for Axis-5 and excluded from independence predictors.

## Tool Contract

The packet uses the standard envelope helper:

```text
scripts/build_three_engine_envelope.py
```

Claim-path tools:

- Julia: `Z3` with `LinearAlgebra` witness recomputation.
- JAX slot: `z3`, `cvc5`, with JAX/JAX NumPy witness recomputation.
- PyTorch: `torch.func`, `z3`, `cvc5`, with PyTorch tensor witness recomputation.

`numpy`, JSON serialization, hashing, and pathlib are supportive only.

## Validator Commands

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/discrete_axis5_family_partial_v0/discrete_axis5_family_partial_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/discrete_axis5_family_partial_v0/discrete_axis5_family_partial_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/discrete_axis5_family_partial_v0/discrete_axis5_family_partial_v0_pytorch.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/discrete_axis5_family_partial_v0/write_envelope_spec.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/discrete_axis5_family_partial_v0/discrete_axis5_family_partial_v0_envelope_spec.json > system_v6/sims/discrete_axis5_family_partial_v0/results/discrete_axis5_family_partial_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/discrete_axis5_family_partial_v0/validate_discrete_axis5_family_partial_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/discrete_axis5_family_partial_v0/results/discrete_axis5_family_partial_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/discrete_axis5_family_partial_v0/tests
```

## Status

Implementation status:

- Operator-family half built: 132 rows over the shared 33-cell carrier.
- Family counts: 66 `dephasing_gradient_side`, 66 `unitary_hamiltonian_side`, 0 primary-table `boundary` rows.
- Boundary control: weak-dephasing-near-unitary row computed and flagged `boundary`.
- 0/5 and 6/5 independence rows computed under no-identity-leak discipline:
  - Axis 5 from Axis 0 majority accuracy: `0.5`.
  - Axis 0 from Axis 5 majority accuracy: `0.5151515151515151`.
  - Axis 5 from Axis 6 majority accuracy: `0.5`.
  - Axis 6 from Axis 5 majority accuracy: `0.42424242424242425`.
  - operator-label identity leak detected and excluded.
- Substage product blocked by construction: 4 `blocked_not_built` rows.
- Label drift unresolved by construction.
- Boundary helper gate present.
- Local validator: `ok=true`, no errors.
- Generic three-engine validator: `ok=true`.
- Pytest: 2 passed.
