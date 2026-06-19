# Build Card: discrete_axis6_precedence_v0

## Boundary

- Packet: `system_v6/sims/discrete_axis6_precedence_v0/`
- Work order row: `f6112e407`, Axis-6 precedence polarity.
- Claim ceiling: `axis_readout_candidate_only`.
- Classification: `scratch_diagnostic`.
- No git add/commit in this card.
- No builder `audit_verdict.md`; audit verdicts are outside this builder packet.

## Pinned Object

This packet computes Axis-6 as a same-carrier precedence readout:

- Operator-first: `Phi_T(O(rho_cell))`.
- Terrain-first: `O(Phi_T(rho_cell))`.
- Pinned operator: committed S4 `D_z`, `pin_sha256=0d7ae0b81d7a92ba490818bb37afe2204cb905fdc43d4d58f35387e64fb72566`.
- Pinned terrain: committed S5 `Ne_Spiral_R` flow at `h=1/2`, `pin_sha256=ced1d4a8395b66077defbfa44dade651cac9c02ef7ea95cca9918a4019b0634a`.
- Carrier: committed Axis-0 Family A 33-cell carrier from `discrete_axis0_field_v0` (`5d330b427`), with 33 cells and 198 generator-labelled edges.

The predeclared sign functional is:

```text
b6 = sign(||Phi_T(O(rho_cell)) - O(Phi_T(rho_cell))||_1 * Delta_z)
```

For qubit Bloch differences, the trace norm is computed as the Euclidean norm of the Bloch difference vector. Zero weighted z difference is neutral.

## Expected Result Surface

- `precedence_table`: 33 rows, one per Family A carrier cell.
- `precedence_counts`: positive/negative/neutral/nonneutral Axis-6 counts.
- `stability_under_committed_dynamics`: one-step and two-step stability over the committed generator graph.
- `independence_rows_vs_axis0`: carrier-honest Axis-0/Axis-6 rows, including the full Axis-0 feature report and identity-leak caveat.
- `b0_b6_prediction`: 33-row staged prediction of `-b3` only; this packet does not measure Axis-3 on the same carrier.
- `axis6_contender_registry_staged_rows`: primary run row plus staged-not-run contenders for commutator-sign, L/R spectral order, and win/lose discriminator.

## Controls

- Commuting control: `O=D_z`, `Phi_T=D_z`, all cells neutral.
- Shuffled-order/N01: reversing the declared order gap flips all nonzero signs.
- Frozen-factor projection: non-identity Axis-0 factors do not perfectly recover `b6`.
- Constant-field degenerate: identity/identity pair is all neutral.
- Label permutation: label-only reproduction fails.

## Tool Contract

The packet uses the standard envelope helper:

```text
scripts/build_three_engine_envelope.py
```

Claim-path tools:

- Julia: `Graphs`, `Z3`.
- JAX slot: `networkx`, `sympy`, `z3`, `cvc5`.
- PyTorch: `torch.func`, `torch_geometric`, `sympy`, `z3`, `cvc5`.

`numpy` and `scipy` are not claim-path tools.

## Validator Commands

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/discrete_axis6_precedence_v0/discrete_axis6_precedence_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/discrete_axis6_precedence_v0/discrete_axis6_precedence_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/discrete_axis6_precedence_v0/discrete_axis6_precedence_v0_pytorch.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/discrete_axis6_precedence_v0/write_envelope_spec.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/discrete_axis6_precedence_v0/discrete_axis6_precedence_v0_envelope_spec.json > system_v6/sims/discrete_axis6_precedence_v0/results/discrete_axis6_precedence_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/discrete_axis6_precedence_v0/validate_discrete_axis6_precedence_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/discrete_axis6_precedence_v0/results/discrete_axis6_precedence_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/discrete_axis6_precedence_v0/tests
```

## Status

Implementation status:

- Precedence table: 33 rows.
- Precedence counts: 14 operator-first, 14 terrain-first, 5 neutral, 28 nonneutral.
- One-step committed-dynamics stability: 174 stable edges, 24 changed edges, 198 total.
- Two-step committed-dynamics stability: 945 stable paths, 243 changed paths, 1188 total.
- Carrier-honest Axis-0/Axis-6 rows:
  - `axis6_not_recoverable_from_axis0_response`: majority accuracy 0.48484848484848486.
  - `axis0_response_not_recoverable_from_axis6`: majority accuracy 0.5151515151515151.
  - identity-leak-excluded best predictor accuracy: 0.9696969696969697.
- `b0_b6_prediction`: 33 staged rows, status `staged_prediction_only_requires_axis3_same_carrier_follow_on`.
- Local validator: `ok=true`, no errors.
- Generic three-engine validator: `ok=true`.
