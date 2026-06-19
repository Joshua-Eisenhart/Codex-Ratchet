# BUILD_REPORT -- probe_quotient_fingerprint_floor_v1

## Bottom Line

BUILD STATUS: PASS

Tautology guard: PASS. Full `P` is `UNSAT` and erased `P'` is `SAT` for both Python `z3` and Python `cvc5`; Julia `Z3.jl` also reports full `P` as `UNSAT` and erased `P'` as `SAT`.

Claim ceiling: `Q=X/~_P` is the FORCED floor, trivially well-defined for the exact supplied finite probe table. The `z3`/`cvc5`/`Z3.jl` checks are consistency checks, not load-bearing structural discovery; the load-bearing forced-vs-installed content lives in the cross-type discriminator, not here.

Status ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

## Files

- `spec.json`
- `probe_quotient_fingerprint_floor_v1_jax.py`
- `probe_quotient_fingerprint_floor_v1_julia.jl`
- `check_agreement.py`
- `results/probe_quotient_fingerprint_floor_v1_jax_results.json`
- `results/probe_quotient_fingerprint_floor_v1_julia_results.json`
- `results/probe_quotient_fingerprint_floor_v1_three_engine_results.json`
- `BUILD_REPORT.md`

## Raw Outputs

### Environment Doctor

Command:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
```

Exit code: `0`

Output:

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

### Julia Carrier Z3 Check

Command:

```text
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier -e 'using JSON, Z3; println("active_project=", Base.active_project()); println("Z3_OK=", Z3.check(Z3.Solver()))'
```

Exit code: `0`

Output:

```text
active_project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml
Z3_OK=sat
```

### JAX/Python Leg

Command:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 probe_quotient_fingerprint_floor_v1_jax.py
```

Exit code: `0`

Output:

```json
{
  "ok": true,
  "result_path": "/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/probe_quotient_fingerprint_floor_v1/results/probe_quotient_fingerprint_floor_v1_jax_results.json",
  "smt_flip": {
    "z3_full_P": "unsat",
    "z3_erased_P": "sat",
    "cvc5_full_P": "unsat",
    "cvc5_erased_P": "sat",
    "real_vs_erased_flip_confirmed": true,
    "encoding": "SMT variables are equal to measured table entries and full-P class ids; the asserted violation is soundness-or-coarseness failure for the active probe list."
  }
}
```

### Julia Leg

Command:

```text
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier probe_quotient_fingerprint_floor_v1_julia.jl
```

Exit code: `0`

Output:

```json
{
  "ok": true,
  "result_path": "/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/probe_quotient_fingerprint_floor_v1/results/probe_quotient_fingerprint_floor_v1_julia_results.json",
  "smt_flip": {
    "encoding": "Z3.jl variables are equal to measured table entries and full-P class ids; the asserted violation is soundness-or-coarseness failure for the active probe list.",
    "julia_z3_erased_P": "sat",
    "julia_z3_full_P": "unsat",
    "real_vs_erased_flip_confirmed": true
  }
}
```

### Envelope

Command:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 check_agreement.py
```

Exit code: `0`

Output:

```json
{
  "ok": true,
  "result_path": "/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/probe_quotient_fingerprint_floor_v1/results/probe_quotient_fingerprint_floor_v1_three_engine_results.json",
  "build_status": "PASS",
  "failures": []
}
```

### Source Carrier-Smuggling Grep

Command:

```text
grep -iE "density|rho|born|povm|pauli|sigma|hilbert|complex|qubit|ket|bloch" probe_quotient_fingerprint_floor_v1_*.py *.jl
```

Exit code: `1` (`grep` found no matches)

Output:

```text

```

### Extended Hard-Constraint Grep

Command:

```text
grep -iE "density|rho|born|povm|pauli|sigma|hilbert|complex|qubit|ket|bloch|\.conj|trace\(" probe_quotient_fingerprint_floor_v1_*.py *.jl
```

Exit code: `1` (`grep` found no matches)

Output:

```text

```

### SMT Flip Summary

```text
z3_full_P=unsat
z3_erased_P=sat
cvc5_full_P=unsat
cvc5_erased_P=sat
julia_z3_full_P=unsat
julia_z3_erased_P=sat
tautology_guard_tripped=false
```

### Three-Engine Validator

Command:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 /Users/joshuaeisenhart/Codex-Ratchet/scripts/validate_three_engine_sim_result.py results/probe_quotient_fingerprint_floor_v1_three_engine_results.json
```

Exit code: `0`

Output:

```json
{
  "ok": true,
  "result_json": "results/probe_quotient_fingerprint_floor_v1_three_engine_results.json"
}
```

### Sim Contract Lint

Command:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v7/sims/probe_quotient_fingerprint_floor_v1/probe_quotient_fingerprint_floor_v1_jax.py system_v7/sims/probe_quotient_fingerprint_floor_v1/check_agreement.py
```

Exit code: `0`

Output:

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

### Banned Verb Scan Over Result JSON And Spec

Command:

```text
grep -RniE "\b(causes|creates|drives|produces|generates|makes|forces|determines)\b" results/*.json spec.json
```

Exit code: `1` (`grep` found no matches)

Output:

```text

```

## Check Matrix

| Check | Status |
| --- | --- |
| Pure finite probe-outcome table; no forbidden carrier terms in source legs | PASS |
| Erase one probe column merges a previously distinct pair | PASS: `x0`, `x2`; class count `5 -> 4` |
| Add the probe column back splits that pair | PASS: class count `4 -> 5` |
| Python z3 full `P` / erased `P'` | PASS: `unsat` / `sat` |
| Python cvc5 full `P` / erased `P'` | PASS: `unsat` / `sat` |
| Julia Z3.jl full `P` / erased `P'` | PASS: `unsat` / `sat` |
| Tautology guard | PASS: erased case is `sat` |
| `validate_three_engine_sim_result.py` | PASS |
| `lint_sim_contract.py` | PASS |
| `surviving_alternatives` non-empty with Rung-0.5 fork open | PASS |
| Claim ceiling remains `scratch_diagnostic` | PASS |

## Limits

This build does not claim carrier ontology, counting/cardinality as forced, rho-is-installed, geometry, physics, a canonical result, or any rung above 0.
