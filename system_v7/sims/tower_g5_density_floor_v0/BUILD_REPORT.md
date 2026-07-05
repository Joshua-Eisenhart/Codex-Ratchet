# Build Report - tower_g5_density_floor_v0

Status: PASS, `classification=scratch_diagnostic`, `promotion_allowed=false`.

Fresh run commands:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier -e 'using QuantumOptics, Z3, JSON; println("JULIA_G5_IMPORTS_OK project=", Base.active_project())'
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
import jax, torch, sympy, z3, cvc5
print('PY_G5_IMPORTS_OK', 'jax', jax.__version__, 'torch', torch.__version__, 'sympy', sympy.__version__)
PY
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier tower_g5_density_floor_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 tower_g5_density_floor_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 tower_g5_density_floor_v0_pytorch.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 check_agreement.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 /Users/joshuaeisenhart/Codex-Ratchet/scripts/validate_three_engine_sim_result.py --require-pytorch results/tower_g5_density_floor_v0_three_engine_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v7/sims/tower_g5_density_floor_v0/tower_g5_density_floor_v0_jax.py system_v7/sims/tower_g5_density_floor_v0/tower_g5_density_floor_v0_pytorch.py system_v7/sims/tower_g5_density_floor_v0/check_agreement.py
```

Environment note: the broad doctor returned `ok=False` because unrelated canonical-env imports `quimb` and `clifford` failed. The packages scoped by this G5 rung passed direct fresh import checks: Julia `QuantumOptics`, `Z3`, `JSON`; Python `jax 0.10.1`, `torch 2.11.0`, `sympy 1.14.0`, `z3`, and `cvc5`.

Witness values from `results/tower_g5_density_floor_v0_three_engine_results.json`:

| Witness | Julia | JAX | PyTorch |
|---|---:|---:|---:|
| same statistics -> same rho residual | 0.0 | 0.0 | 0.0 |
| distinct statistics rho distance | 0.5196152422706632 | 0.5196152422706632 | 0.5196152422706632 |
| label shuffle residual | 0.0 | 0.0 | 0.0 |
| unitary trace residual | 0.0 | 0.0 | 0.0 |
| dephasing trace residual | 0.0 | 0.0 | 0.0 |

Installed-vs-forced record:

```json
{
  "installed_by_closure_demand": true,
  "closure_demand": "downstream unitary and dephasing operators require rho in D(C^2), not only a probe-statistics quotient label",
  "removable": true,
  "removed_demand_record": {
    "bare_quotient_suffices": true,
    "rho_required": false
  }
}
```

Parity: `max_divergence=0.0`, `all_pass=true`.

Validation:

- `validate_three_engine_sim_result.py --require-pytorch`: `ok=true`
- `lint_sim_contract.py` on the new Python sources: `checked=3`, `violation_total=0`
