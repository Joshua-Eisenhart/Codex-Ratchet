# BUILD CARD - axis_triple_consistency_b6_v0

Status: builder packet, no `audit_verdict.md`, no git staging.

Ceiling: `axis_readout_candidate_only + consistency_row_only`.

## Authority Quotes

Work order (`system_v6/receipts/axis_work_order_20260612.md:12`):

> with 0+3+6 on one carrier, the scaffold relation **b6 = -b0*b3** becomes a COMPUTED consistency row (NOT an independence proof - the receipt's own warning)

Scaffold line (`system_v6/foundations/working_math_scaffold_20260609.md:117`):

> Axis 6 - precedence / signed orientation: b_6 = -b_0 b_3. Anchors: L_A vs R_A; Phi_T(O(rho)) vs O(Phi_T(rho)). Turns 4 operators into 8 signed operators.

Panel 6 q2 (`system_v6/receipts/cross_model_anchor_recompute_panel6_20260612.md:11`) pins the two check points:

- `eta=pi/6 + fiber -> b6=-1`
- `eta=pi/3 + base -> b6=-1`

## Carrier Decision

Carrier: the committed Axis-3 Hopf loop-family sample: sheets `L/R`, eta values `pi/8`, `pi/4`, `3*pi/8`, placements `gamma_in/fiber` and `gamma_out/lifted_base`, and the committed `phi_index`/`chi_index` pins.

This card computes:

- `b0 = sign(cos 2eta)` directly on the Hopf eta leaf.
- `b3` from the card/panel fiber-base convention: `fiber=+1`, `base/lifted_base=-1`.
- `b6` from the committed pinned pair on the Hopf Bloch states: `O = D_z` from the S4 operator packet, `Phi_T = Ne_Spiral_R` at `h=1/2` from the S5 terrain packet.

Compromise named explicitly: this is a Hopf-state realization of the pinned `D_z`/`Ne_Spiral_R` precedence functional. It matches both panel points but does not make the full pinned Hopf sample satisfy the relation universally. That failure is preserved as the finding.

The older chart-role convention from `AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md` is preserved as a context-only diagnostic field, not used as the primary relation row.

## Anti-By-Construction Discipline

The row computes `b0`, `b3`, and `b6` independently first. The relation `b6 = -(b0*b3)` is evaluated only after those signs exist. The table must be able to fail, and it does fail on this raw shared object.

## Controls

- Convention flip: flip `b3`; the target flips to `b6 = +b0*b3` under the original `b3` labels.
- Scrambled b6: replace `b6` by deterministic sha256 noise and report chance-scale agreement.
- Commuting control: set `O = Phi_T = D_z`; the precedence sign becomes neutral for every sampled Hopf state.
- Independence reminder row: consistency is not independence and cannot promote axis admission.

## Expected Commands

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/axis_triple_consistency_b6_v0/axis_triple_consistency_b6_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/axis_triple_consistency_b6_v0/axis_triple_consistency_b6_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/axis_triple_consistency_b6_v0/axis_triple_consistency_b6_v0_pytorch.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/axis_triple_consistency_b6_v0/write_envelope_spec.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/axis_triple_consistency_b6_v0/axis_triple_consistency_b6_v0_envelope_spec.json > system_v6/sims/axis_triple_consistency_b6_v0/results/axis_triple_consistency_b6_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/axis_triple_consistency_b6_v0/validate_axis_triple_consistency_b6_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/axis_triple_consistency_b6_v0/results/axis_triple_consistency_b6_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/axis_triple_consistency_b6_v0/tests
```

## Claim Boundary

Allowed: computed Hopf consistency table, panel-point reproduction, negative/control rows, exact violation listing.

Disallowed: axis independence proof, canonical cross-axis law, Axis-6 admission, physics/manifold theorem, or any claim that hides the violations.
