Bottom line: `GENUINE-WITH-CAVEATS` at `scratch_diagnostic` ceiling. The 3 RETURN / 6 BOUNDARY table is real for the packet's computed finite graph rows, the probe-erased and over-perturbation controls fire, and the three-engine/tooling validators pass. The caveat is load-bearing: the classifications inherit formula relativity from the committed Axis-0 `phi` candidate, and the reported `0 SCRAMBLING` is vacuous in part because the current return predicate makes scrambling unreachable on this carrier/readout path.

Verdict vocabulary:

- `classification`: `scratch_diagnostic`
- `claim_ceiling`: `basin_dof_readout_rows_only`
- `promotion_allowed`: `false`
- `formal_admission_allowed`: `false`
- audit verdict: `GENUINE-WITH-CAVEATS`
- not admitted: axis admission, basin theorem, manifold existence proof, bridge/physics inference, canonical promotion

## What I Checked

This was a read-only audit except for this file. I did not run builders that rewrite result JSON. I recomputed selected rows through the packet's shared builder functions, validated the committed result payload in read-only mode, and checked the current axis0 correction surface.

The packet directory is currently untracked in this checkout:

- `system_v6/sims/basin_dof_perturb_and_read_v0/`

That means this verdict audits the working-tree packet, not a committed object.

## Classification Reality

The RETURN path is real for at least one nonzero packet row. I recomputed `stage_shift_Rx_to_Rz` end-to-end from `basin_dof_perturb_and_read_v0_common.py`:

- generators: `Se_Funnel_L`, `Ni_Pit_L`, `Ni_Source_R`, `Ne_Spiral_R`, `D_z`, `R_z`
- state count: `33`
- prior terminal class: `[16]`
- recomputed terminal class: `[16]`
- `returned_to_prior_terminal_class`: `true`
- `axis0_readout_reconverged`: `true`
- `absent_exit_checked`: `true`
- sample row: seed `0`, size `0`, trajectory `[0, 5, 4, 15, 16]`, terminal `16`, baseline polarity `neutral_no_polarity`, final polarity `neutral_no_polarity`

The BOUNDARY path is real for at least one row. I recomputed `G1` end-to-end:

- generators: `R_x`, `R_z`, `Ne_Spiral_R`, `Ne_Vortex_L`
- state count: `33`
- prior terminal class: `[16]`
- recomputed terminal classes:
  - `[0, 1, 3, 7, 9, 10, 14, 18, 22, 23, 25, 29, 31, 32]`
  - `[2, 4, 5, 6, 8, 11, 12, 13, 15, 17, 19, 20, 21, 24, 26, 27, 28, 30]`
  - `[16]`
- `returned_to_prior_terminal_class`: `false`
- `escaped_to_different_terminal_class`: `true`
- `boundary_found`: `true`
- `axis0_readout_reconverged`: `false`
- `absent_exit_checked`: `true`
- sample row: seed `0`, size `0`, trajectory `[0]`, terminal `0`, baseline polarity `neutral_no_polarity`, final polarity `axis0_minus_homeostatic_response`

The `0 SCRAMBLING` result should not be cited as a discovered absence of scrambling. The code predicate has a `SCRAMBLING` branch, but under the current carrier and return definition it is unreachable: `returned_to_prior_terminal_class` requires terminal classes exactly equal to the baseline `[16]`, and readout is sampled only at terminal cell `16`. For all returned rows (`G0`, `G2`, `stage_shift_Rx_to_Rz`), every final terminal cell is `16`, so readout reconvergence is implied. This makes expectation-2's "boundary via escape or scrambling" met by escape boundaries, with the scrambling alternative vacuous in part.

## DoF Set

The nine rows are:

1. `G0`
2. `G1`
3. `G2`
4. `G3L`
5. `G3R`
6. `G4`
7. `G5`
8. `stage_shift_Rx_to_Rz`
9. `loop_reverse_G5`

`G0` through `G5` are the committed `basin_generating_set_sweep_v0` generator-family rows, not cherry-picked after the result. `stage_shift_Rx_to_Rz` and `loop_reverse_G5` are build-card-required derived stage/loop directions. The flux direction is honestly excluded from the counted DoF rows as `blocked_not_realizable_on_33_cell_carrier_without_lift`.

Caveat: `G4` is not a full 33-cell same-carrier perturbation row; it is the conditioned-shell restriction with `state_count=4`. It is still a declared generator-family row from the committed sweep, but future citations should not flatten it into "all nine are same 33-cell carrier rows."

## Formula-Relativity Inheritance

The axis0 correction affects this packet. The packet consumes `discrete_axis0_field_v0` at `5d330b427` as the readout probe. The current audit annotation on that packet says the scalar formula

`phi=(2x-5y+7z+3xy-z^2+4r2+11shell)/97`

was builder-chosen and later registered as `A0.CP.0_committed`, one legitimate candidate among alternatives, not unqualified "the Axis-0 readout." It also says the nonrecoverability wording is surrogate-level only.

Therefore this packet's `RETURN`, `BOUNDARY`, and `SCRAMBLING` classifications are formula-relative to the committed `A0.CP.0_committed` / `phi` probe. They are not probe-family-invariant basin classifications. The result is citable only as:

> For the committed Axis-0 `phi` candidate (`A0.CP.0_committed`) on the finite 33-cell carrier, the packet computes 3 RETURN and 6 BOUNDARY DoF rows, with no nonvacuous scrambling search.

Do not cite it as "the basin readout" until the Axis-0 contender sweep collapses or explicitly preserves alternatives.

## Controls

The zero-perturbation control is a calibration, not independent evidence:

- classification: `RETURN`
- sample count: `6`
- all zero-size rows reconverge to terminal cell `16` and polarity `neutral_no_polarity`

The over-perturbation control goes through the real boundary path:

- classification: `BOUNDARY`
- `past_basin_scale`: `true`
- root-off state count: `125`
- base state count: `33`
- outside `Adm_C` sample cells: `[0, 1, 2, 3, 4, 5]`
- partition changed: `true`
- absent-exit checked: `true`

The probe-erased control degrades by removing the axis readout:

- classification: `DEGRADED`
- constant field gives `neutral_no_polarity` on all `33` cells
- nonzero gradient edges drop to `0`
- base return/boundary signature is no longer a meaningful axis-reading classification, because the spatial rows lose the polarity predicate

Caveat: the erased control proves the readout is load-bearing by degenerating the polarity field. It does not produce a row-by-row alternate `RETURN/BOUNDARY/SCRAMBLING` table under a second admissible nonconstant probe.

The shuffled-order `N01` control fires:

- classification: `BOUNDARY`
- `n01_order_control_fired`: `true`
- base terminal class count: `1`
- shuffled terminal class count: `3`
- partition changed: `true`

## Circularity Checks

Frozen-factor: no frozen flux factor is counted as a DoF row; the flux direction is excluded instead of smuggled. The `G4` conditioned-shell restriction is the closest risk because its state set changes to 4 cells, so cite it as a restricted-carrier row, not a same-carrier perturbation row.

Definitional: the zero perturbation RETURN is explicitly a calibration. More importantly, for returned rows, readout reconvergence is implied by returning to singleton terminal class `[16]`; this is why `0 SCRAMBLING` is not an independent negative finding.

Post-hoc statistic: the nine DoF rows are build-card declared, and `G0` through `G5` come from the committed generator sweep. The inherited Axis-0 `phi` formula was builder-chosen in the parent packet, so the correct containment is formula-relative citation, not deletion of this packet.

Structure-by-symmetry: I found no promoted symmetry-forced discovery claim in this packet. The result is a finite graph classification table and controls only. Do not upgrade the BOUNDARY partitions into discovered substructure without a later symmetry/adversarial analysis.

## SMT And Tool Honesty

SMT rows are real aggregate bindings, not mere boolean assertions:

- z3: base identity `unsat`, erased flip `sat`
- cvc5: base identity `unsat`, erased flip `sat`
- bound values: `dof_total=9`, `return_dof_count=3`, `boundary_dof_count=6`, `scrambling_dof_count=0`, `zero_return=1`, `over_boundary=1`, `probe_degraded=1`, `n01_fired=1`

Caveat: these solver rows bind the aggregate count/control identity. They do not independently prove every trajectory row; the trajectory reality comes from the graph recomputation and the cross-backend result agreement.

The envelope reports all three engine lanes present with no peer-result reads:

- Julia: `Graphs`, `Z3`
- JAX/Python: `networkx`, `sympy`, `z3`, `cvc5`
- PyTorch: `torch.func`, `torch_geometric`, `sympy`, `z3`, `cvc5`

The envelope comparison reports all lanes agree on `return=3`, `boundary=6`, `scrambling=0`, with `max_divergence=0`.

## Validator Reruns

I ran these read-only checks:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
import json, sys
from pathlib import Path
root=Path('/Users/joshuaeisenhart/Codex-Ratchet')
sim=root/'system_v6/sims/basin_dof_perturb_and_read_v0'
sys.path.insert(0,str(sim))
import validate_basin_dof_perturb_and_read_v0 as v
payload=json.loads((sim/'results/basin_dof_perturb_and_read_v0_envelope_results.json').read_text())
errors=v.validate_payload(payload)
print(json.dumps({'read_only_packet_validator_ok': not errors, 'errors': errors}, indent=2, sort_keys=True))
PY
```

Result: `read_only_packet_validator_ok=true`, `errors=[]`.

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/basin_dof_perturb_and_read_v0/results/basin_dof_perturb_and_read_v0_envelope_results.json
```

Result: `ok=true`.

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v6/sims/basin_dof_perturb_and_read_v0/basin_dof_perturb_and_read_v0_common.py
```

Result: `violation_total=0`.

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/basin_dof_perturb_and_read_v0/tests
```

Result: `5 passed`.

I did not run the Julia/JAX/PyTorch builder entrypoints or envelope writer because they rewrite result JSON and the audit scope was read-only except this verdict.

## Future-Citation Rule

Allowed short citation:

> `basin_dof_perturb_and_read_v0` is an audited `scratch_diagnostic` working-tree packet: for the committed Axis-0 `phi` candidate (`A0.CP.0_committed`) on the finite carrier, it computes 3 RETURN and 6 BOUNDARY DoF rows across the declared generator/stage/loop directions, with probe-erased and over-perturbation controls firing; expectation 2 is met by return plus escape-boundary rows, but the `0 SCRAMBLING` finding is vacuous in part under the current singleton-terminal return predicate.

Forbidden citation:

- "Axis-0 admission"
- "basin theorem"
- "probe-invariant basin classification"
- "nonzero scrambling search completed"
- "all nine rows are same-carrier 33-cell perturbations"
- "manifold existence proof"

## Doctrine Expectation-2 Adjudication

Expectation 2 is `MET / VACUOUS-IN-PART`.

It is met because there is at least one real RETURN row with terminal re-entry plus `phi`-readout reconvergence, and at least one real BOUNDARY row by escape to a different terminal partition. It is vacuous in part because the `SCRAMBLING` alternative could not have been detected under the current return/readout machinery; returned rows imply reconverged readout on singleton terminal cell `16`.
