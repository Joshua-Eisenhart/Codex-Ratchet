# BUILD_REPORT -- carrier_type_admissibility_matrix_v0

## Bottom Line

BUILD STATUS: PASS

`order_gap_clean` was added with the verified clean fixture values: `Z=1/2`, `X=3/4`, `ZX=1/4`, `XZ=3/8`. All solver legs (`z3`, `cvc5`, `julia_z3`) agree that `classical_noncontextual` is excluded and `complex_rho` is admitted on this fixture.

Claim ceiling remains `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

`y_phase_exclusion` for `real_rebit` is fenced as `by_construction=true`: a real-symmetric rebit has no Y degree of freedom, so `Y=3/4` is outside the class by design. It is a boundary/control only, not a load-bearing carrier-type negative. The genuine load-bearing negative remains `order_gap_clean`, where `classical_noncontextual` is excluded by the non-disturbing joint contradiction `ZX=1/4` versus `XZ=3/8`.

## Scope Notes

- `quotient` is a near-trivial null baseline: one bounded free readout variable per measured probe, so it admits any in-range table. The load-bearing carrier-type negative is `order_gap_clean` for `classical_noncontextual`; the `real_rebit` Y-phase row is by construction and fenced from load-bearing status.
- The Luders readout maps are one chosen measurement geometry. The clean order-gap result is a fixture-local contextuality-flavored negative under that chosen geometry, not a general contextuality theorem.
- Existing `order_gap_exclusion` with `Z=1` is retained but relabeled as over-determined: the marginal already helps pin the classical joint, so it is marginal plus order-gap pressure rather than the isolated contextuality negative.
- Rung-0.5 Boolean/counting fork remains held.

## Updated Matrix

All solver rows (`z3`, `cvc5`, `julia_z3`) agree with the table below and have empty `unknown_set`.

| Fixture | Allowed Set | Excluded Set | Verdict |
| --- | --- | --- | --- |
| `marginal_multiplicity` | `quotient`, `classical_noncontextual`, `real_rebit`, `complex_rho` | empty | `installed` |
| `order_gap_exclusion` | `quotient`, `real_rebit`, `complex_rho` | `classical_noncontextual` | `installed`; over-determined Z=1 fixture |
| `order_gap_clean` | `quotient`, `real_rebit`, `complex_rho` | `classical_noncontextual` | `installed`; clean isolated order-gap fixture |
| `y_phase_exclusion` | `quotient`, `classical_noncontextual`, `complex_rho` | `real_rebit` | `installed`; `real_rebit` exclusion is `by_construction` boundary/control |
| `scrambled_order_gap` | `quotient` | `classical_noncontextual`, `real_rebit`, `complex_rho` | `single_allowed_by_panel` |

## `order_gap_clean` Isolation Proof

Clean fixture values:

```json
{
  "Z": "1/2",
  "X": "3/4",
  "ZX": "1/4",
  "XZ": "3/8",
  "complex_rho_witness": {"a": "1/2", "b": "1/4"}
}
```

Classical noncontextual isolation:

| Solver | `Z,X` marginals | `Z,X,ZX` branch | `Z,X,XZ` branch | joint `Z,X,ZX,XZ` |
| --- | --- | --- | --- | --- |
| `z3` | `sat` | `sat` | `sat` | `unsat` |
| `cvc5` | `sat` | `sat` | `sat` | `unsat` |
| `julia_z3` | `sat` | `sat` | `sat` | `unsat` |

The exclusion mechanism is only the non-disturbing classical joint: the same classical `J` would have to equal both `ZX=1/4` and `XZ=3/8`.

Complex rho admission:

| Solver | Status | Witness |
| --- | --- | --- |
| `z3` | `sat` | `a=1/2`, `b=1/4`, `c=0` |
| `cvc5` | `sat` | `a=1/2`, `b=1/4`, `c=0` |
| `julia_z3` | `sat` | `a=1/2`, `b=1/4`, `c=0` |

PSD check for the named witness: `a*(1-a)=1/4 >= b^2=1/16`.

## Deterministic Witness Selection

Python and Julia now use the same explicit fixture order for reproduce ON/OFF witness selection:

```text
marginal_multiplicity
order_gap_exclusion
order_gap_clean
y_phase_exclusion
scrambled_order_gap
invalid_probability
```

Observed reproduce ON/OFF witnesses now match across `z3`, `cvc5`, and `julia_z3`:

| Carrier Type | Fixture | ON | OFF |
| --- | --- | --- | --- |
| `quotient` | `invalid_probability` | `unsat` | `sat` |
| `classical_noncontextual` | `order_gap_exclusion` | `unsat` | `sat` |
| `real_rebit` | `y_phase_exclusion` | `unsat` | `sat` |
| `complex_rho` | `scrambled_order_gap` | `unsat` | `sat` |

## Fresh Commands And Results

Environment doctor:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
```

```text
ok=True install_state=stable_observed
repo=/Users/joshuaeisenhart/Codex-Ratchet
sim_stack_alias=/Users/joshuaeisenhart/.local/share/sim-stack
physical_python_env=/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main
python=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
julia=/opt/homebrew/bin/julia
julia_project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier
julia_load_path=@:@stdlib
No repo-local env pollution, missing expected modules, or active installers observed.
```

Python/JAX z3+cvc5 leg:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/carrier_type_admissibility_matrix_v0/carrier_type_admissibility_matrix_v0_jax.py
```

Result: `ok=true`; `order_gap_clean` allowed `quotient`, `real_rebit`, `complex_rho`; excluded `classical_noncontextual`; isolation proof `passed=true` for both `z3` and `cvc5`.

Julia/Z3.jl leg:

```text
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v7/sims/carrier_type_admissibility_matrix_v0/carrier_type_admissibility_matrix_v0_julia.jl
```

Result: `ok=true`; `order_gap_clean` allowed `quotient`, `real_rebit`, `complex_rho`; excluded `classical_noncontextual`; isolation proof `passed=true`.

Agreement envelope:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/carrier_type_admissibility_matrix_v0/check_agreement.py
```

```json
{
  "ok": true,
  "build_status": "PASS",
  "failures": [],
  "result_path": "/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/carrier_type_admissibility_matrix_v0/results/carrier_type_admissibility_matrix_v0_three_engine_results.json"
}
```

Three-engine validator:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v7/sims/carrier_type_admissibility_matrix_v0/results/carrier_type_admissibility_matrix_v0_three_engine_results.json
```

```json
{
  "ok": true,
  "result_json": "system_v7/sims/carrier_type_admissibility_matrix_v0/results/carrier_type_admissibility_matrix_v0_three_engine_results.json"
}
```

Sim contract lint:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v7/sims/carrier_type_admissibility_matrix_v0/carrier_type_admissibility_matrix_v0_jax.py system_v7/sims/carrier_type_admissibility_matrix_v0/check_agreement.py
```

```json
{
  "checked": 2,
  "violation_total": 0,
  "sims_with_violations": 0,
  "violations_by_type": {},
  "top_offenders": [],
  "violations": []
}
```

Python compile check:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m py_compile system_v7/sims/carrier_type_admissibility_matrix_v0/carrier_type_admissibility_matrix_v0_jax.py system_v7/sims/carrier_type_admissibility_matrix_v0/check_agreement.py
```

Result: exit code `0`.

JSON spec check:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m json.tool system_v7/sims/carrier_type_admissibility_matrix_v0/spec.json
```

Result: exit code `0`.

## Result Files

- `results/carrier_type_admissibility_matrix_v0_jax_results.json`
- `results/carrier_type_admissibility_matrix_v0_julia_results.json`
- `results/carrier_type_admissibility_matrix_v0_three_engine_results.json`

## Limits

This result does not prove `rho` is wrong or excluded. `complex_rho` is admitted on `marginal_multiplicity`, `order_gap_exclusion`, `order_gap_clean`, and `y_phase_exclusion`.

This result does not promote a carrier beyond `scratch_diagnostic` and does not close the Rung-0.5 Boolean/counting fork.
