# BUILD REPORT - forced_or_installed_carrier_comparison_v0

Build status: PASS.

Scope: only files under `system_v7/sims/forced_or_installed_carrier_comparison_v0/` were edited.

## Carrier Contract

Carrier: `rho=[[a, b+i*c], [b-i*c, 1-a]]`.

Validity: `0 <= a <= 1` and `a*(1-a)-b^2-c^2 >= 0`.

Readouts:

- `Z = 2a - 1`
- `X = 2b`
- `Y = 2c`

First carrier `C1`: `a=1/2`, `b=1/8`, `c=1/10`, PSD margin `359/1600`.

Installed fixture: probes `Z,X`, measured `Z=0`, `X=1/4`. This is informationally incomplete because `c` is not measured.

Forced fixture: probes `Z,X,Y`, measured `Z=0`, `X=1/4`, `Y=1/5`. This is complete for `(a,b,c)` against the reference carrier.

Claim ceiling: `FORCED` here means no second carrier with different `(a,b,c)` coordinates reproduces the table. It is coordinate-uniqueness vs the reference, not isomorphic or ontological uniqueness; no gauge quotient is applied in this v0 fixture.

## Raw Engine Outputs

Command:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/forced_or_installed_carrier_comparison_v0/forced_or_installed_carrier_comparison_v0_jax.py
```

Output:

```json
{
  "ok": true,
  "result_path": "/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/forced_or_installed_carrier_comparison_v0/results/forced_or_installed_carrier_comparison_v0_jax_results.json",
  "installed": {
    "z3": "installed",
    "cvc5": "installed"
  },
  "forced": {
    "z3": "forced",
    "cvc5": "forced"
  },
  "reproduce_on_off": {
    "z3": {
      "installed_on": "sat",
      "installed_off": "sat",
      "installed_off_mismatch": "sat",
      "forced_on": "unsat",
      "forced_off": "sat",
      "forced_off_mismatch": "sat",
      "forced_status_differs": true,
      "invalid_on": "unsat",
      "invalid_off": "sat",
      "invalid_off_mismatch": "sat",
      "invalid_status_differs": true
    },
    "cvc5": {
      "installed_on": "sat",
      "installed_off": "sat",
      "installed_off_mismatch": "sat",
      "forced_on": "unsat",
      "forced_off": "sat",
      "forced_off_mismatch": "sat",
      "forced_status_differs": true,
      "invalid_on": "unsat",
      "invalid_off": "sat",
      "invalid_off_mismatch": "sat",
      "invalid_status_differs": true
    }
  },
  "z3_installed_C2": {
    "carrier": {
      "a": "1/2",
      "b": "1/8",
      "c": "0"
    },
    "model_string": "[z3_installed_c2_c = 0,\n z3_installed_c2_b = 1/8,\n z3_installed_c2_a = 1/2]"
  },
  "cvc5_installed_C2": {
    "carrier": {
      "a": "(/ 1 2)",
      "b": "(/ 1 8)",
      "c": "0.0"
    },
    "model_string": "cvc5_installed_c2_a -> (/ 1 2)\ncvc5_installed_c2_b -> (/ 1 8)\ncvc5_installed_c2_c -> 0.0"
  }
}
```

Command:

```text
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/forced_or_installed_carrier_comparison_v0/forced_or_installed_carrier_comparison_v0_pytorch.py
```

Output:

```json
{
  "ok": true,
  "result_path": "/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/forced_or_installed_carrier_comparison_v0/results/forced_or_installed_carrier_comparison_v0_pytorch_results.json",
  "installed": {
    "z3": "installed",
    "cvc5": "installed"
  },
  "forced": {
    "z3": "forced",
    "cvc5": "forced"
  },
  "torch_func_role": "supportive"
}
```

Command:

```text
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v7/sims/forced_or_installed_carrier_comparison_v0/forced_or_installed_carrier_comparison_v0_julia.jl
```

Output:

```json
{
  "forced": {
    "julia_z3": "forced"
  },
  "installed": {
    "julia_z3": "installed"
  },
  "julia_installed_C2": "julia_installed_c2_c -> 0.0\njulia_installed_c2_a -> (/ 1.0 2.0)\njulia_installed_c2_b -> (/ 1.0 8.0)\n",
  "ok": true,
  "reproduce_on_off": {
    "julia_z3": {
      "forced_off": "sat",
      "forced_off_mismatch": "sat",
      "forced_on": "unsat",
      "forced_status_differs": true,
      "installed_off": "sat",
      "installed_off_mismatch": "sat",
      "installed_on": "sat",
      "invalid_off": "sat",
      "invalid_off_mismatch": "sat",
      "invalid_on": "unsat",
      "invalid_status_differs": true
    }
  },
  "result_path": "/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/forced_or_installed_carrier_comparison_v0/results/forced_or_installed_carrier_comparison_v0_julia_results.json"
}
```

Command:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/forced_or_installed_carrier_comparison_v0/check_agreement.py
```

Output:

```json
{
  "ok": true,
  "result_path": "/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/forced_or_installed_carrier_comparison_v0/results/forced_or_installed_carrier_comparison_v0_three_engine_results.json",
  "build_status": "PASS",
  "installed": {
    "jax_z3": "installed",
    "jax_cvc5": "installed",
    "pytorch_z3": "installed",
    "pytorch_cvc5": "installed",
    "julia_z3": "installed"
  },
  "forced": {
    "jax_z3": "forced",
    "jax_cvc5": "forced",
    "pytorch_z3": "forced",
    "pytorch_cvc5": "forced",
    "julia_z3": "forced"
  },
  "failures": []
}
```

## Raw Summary From Envelope

Command:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
import json
from pathlib import Path
root=Path('system_v7/sims/forced_or_installed_carrier_comparison_v0')
env=json.loads((root/'results/forced_or_installed_carrier_comparison_v0_three_engine_results.json').read_text())
print(json.dumps({
  'build_status': env['build_status'],
  'fixture_verdicts': env['fixture_verdicts'],
  'reproduce_on_off_comparison': env['reproduce_on_off_comparison'],
  'scramble_controls': env['scramble_controls'],
  'solver_found_C2': env['installed_multiplicity_witness'],
  'free_variable_declarations': env['free_variable_declarations'],
  'torch_func_depth': env['TOOL_INTEGRATION_DEPTH']['torch.func'],
  'failures': env['failures'],
}, indent=2, sort_keys=True))
PY
```

Output:

```json
{
  "build_status": "PASS",
  "failures": [],
  "fixture_verdicts": {
    "forced_complete": {
      "statuses": {
        "jax_cvc5": "unsat",
        "jax_z3": "unsat",
        "julia_z3": "unsat",
        "pytorch_cvc5": "unsat",
        "pytorch_z3": "unsat"
      },
      "verdicts": {
        "jax_cvc5": "forced",
        "jax_z3": "forced",
        "julia_z3": "forced",
        "pytorch_cvc5": "forced",
        "pytorch_z3": "forced"
      }
    },
    "installed_incomplete": {
      "statuses": {
        "jax_cvc5": "sat",
        "jax_z3": "sat",
        "julia_z3": "sat",
        "pytorch_cvc5": "sat",
        "pytorch_z3": "sat"
      },
      "verdicts": {
        "jax_cvc5": "installed",
        "jax_z3": "installed",
        "julia_z3": "installed",
        "pytorch_cvc5": "installed",
        "pytorch_z3": "installed"
      }
    }
  },
  "reproduce_on_off_comparison": {
    "jax": {
      "z3": {"installed_on": "sat", "installed_off": "sat", "installed_off_mismatch": "sat", "forced_on": "unsat", "forced_off": "sat", "forced_off_mismatch": "sat", "forced_status_differs": true, "invalid_on": "unsat", "invalid_off": "sat", "invalid_off_mismatch": "sat", "invalid_status_differs": true},
      "cvc5": {"installed_on": "sat", "installed_off": "sat", "installed_off_mismatch": "sat", "forced_on": "unsat", "forced_off": "sat", "forced_off_mismatch": "sat", "forced_status_differs": true, "invalid_on": "unsat", "invalid_off": "sat", "invalid_off_mismatch": "sat", "invalid_status_differs": true}
    },
    "julia": {
      "julia_z3": {"installed_on": "sat", "installed_off": "sat", "installed_off_mismatch": "sat", "forced_on": "unsat", "forced_off": "sat", "forced_off_mismatch": "sat", "forced_status_differs": true, "invalid_on": "unsat", "invalid_off": "sat", "invalid_off_mismatch": "sat", "invalid_status_differs": true}
    },
    "pytorch": {
      "z3": {"installed_on": "sat", "installed_off": "sat", "installed_off_mismatch": "sat", "forced_on": "unsat", "forced_off": "sat", "forced_off_mismatch": "sat", "forced_status_differs": true, "invalid_on": "unsat", "invalid_off": "sat", "invalid_off_mismatch": "sat", "invalid_status_differs": true},
      "cvc5": {"installed_on": "sat", "installed_off": "sat", "installed_off_mismatch": "sat", "forced_on": "unsat", "forced_off": "sat", "forced_off_mismatch": "sat", "forced_status_differs": true, "invalid_on": "unsat", "invalid_off": "sat", "invalid_off_mismatch": "sat", "invalid_status_differs": true}
    }
  },
  "scramble_controls": {
    "forced_scrambled_values": {
      "jax_cvc5": "sat",
      "jax_z3": "sat",
      "julia_z3": "sat"
    },
    "installed_scrambled_values": {
      "jax_cvc5": "sat",
      "jax_z3": "sat",
      "julia_z3": "sat"
    }
  },
  "solver_found_C2": {
    "z3": {
      "carrier": {"a": "1/2", "b": "1/8", "c": "0"},
      "model_string": "[z3_installed_c2_c = 0,\n z3_installed_c2_b = 1/8,\n z3_installed_c2_a = 1/2]"
    },
    "cvc5": {
      "carrier": {"a": "(/ 1 2)", "b": "(/ 1 8)", "c": "0.0"},
      "model_string": "cvc5_installed_c2_a -> (/ 1 2)\ncvc5_installed_c2_b -> (/ 1 8)\ncvc5_installed_c2_c -> 0.0"
    },
    "julia_z3": "julia_installed_c2_c -> 0.0\njulia_installed_c2_a -> (/ 1.0 2.0)\njulia_installed_c2_b -> (/ 1.0 8.0)\n"
  },
  "torch_func_depth": "supportive"
}
```

## C2 Witness Check

Installed witness from all solver families is `C2=(a=1/2,b=1/8,c=0)`.

- `C2` is PSD: margin `15/64`.
- `C2 != C1` because `c=0` while `C1.c=1/10`.
- Installed probes reproduce: `Z(C2)=0`, `X(C2)=1/4`.
- Complete probes do not allow that witness because `Y(C2)=0`, while the forced fixture measures `Y=1/5`.

The forced complete fixture is therefore not a cardinality tautology: the same complete probe set with scrambled `Y=-1/5` is SAT.

## Validator Outputs

Command:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v7/sims/forced_or_installed_carrier_comparison_v0/results/forced_or_installed_carrier_comparison_v0_three_engine_results.json
```

Output:

```json
{
  "ok": true,
  "result_json": "system_v7/sims/forced_or_installed_carrier_comparison_v0/results/forced_or_installed_carrier_comparison_v0_three_engine_results.json"
}
```

Command:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v7/sims/forced_or_installed_carrier_comparison_v0/results/forced_or_installed_carrier_comparison_v0_three_engine_results.json
```

Output:

```json
{
  "ok": true,
  "result_json": "system_v7/sims/forced_or_installed_carrier_comparison_v0/results/forced_or_installed_carrier_comparison_v0_three_engine_results.json"
}
```

Command:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v7/sims/forced_or_installed_carrier_comparison_v0/carrier_decision_core.py system_v7/sims/forced_or_installed_carrier_comparison_v0/forced_or_installed_carrier_comparison_v0_jax.py system_v7/sims/forced_or_installed_carrier_comparison_v0/forced_or_installed_carrier_comparison_v0_pytorch.py system_v7/sims/forced_or_installed_carrier_comparison_v0/check_agreement.py
```

Output:

```json
{
  "checked": 4,
  "violation_total": 0,
  "sims_with_violations": 0,
  "violations_by_type": {},
  "top_offenders": [],
  "violations": []
}
```
