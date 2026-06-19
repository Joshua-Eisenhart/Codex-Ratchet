# mct_dynamic_admissibility_packet_v0 preflight

Generated: 2026-06-09T17:32:36-07:00
Repo: /Users/joshuaeisenhart/Codex-Ratchet
Makefile PYTHON: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3

## 1. Terrain packet still valid

Command run:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/terrain_generator_sheet_packet/results/terrain_generator_sheet_packet_envelope_results.json --require-pytorch
```

Exit status: `0`

Key output lines:

```text
{
  "ok": true,
  "result_json": "system_v6/sims/terrain_generator_sheet_packet/results/terrain_generator_sheet_packet_envelope_results.json"
}
```

Verdict: **PASS**

## 2. Julia env default imports

Command run:

```bash
julia -e 'using QuantumOptics, Z3, Graphs, JSON, SHA; println("ok")'
```

Exit status: `0`

Key output lines:

```text
ok
```

Verdict: **PASS**

## 3. Python env package imports

Command run:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PYCODE'
import importlib.metadata as md
import jax, z3, cvc5, sympy
import torch, torch_geometric
mods = [('jax', jax), ('z3-solver', z3), ('cvc5', cvc5), ('sympy', sympy), ('torch', torch), ('torch-geometric', torch_geometric)]
for dist, mod in mods:
    version = getattr(mod, '__version__', None)
    if version is None:
        try:
            version = md.version(dist)
        except Exception as exc:
            version = f'unknown ({exc.__class__.__name__})'
    print(f'{dist}: {version}')
PYCODE
```

Exit status: `0`

Key output lines:

```text
jax: 0.10.1
z3-solver: 4.16.0.0
cvc5: 1.3.3
sympy: 1.14.0
torch: 2.11.0
torch-geometric: 2.7.0
```

Verdict: **PASS**

## 4a. Validator help

Command run:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --help
```

Exit status: `0`

Key output lines:

```text
usage: validate_three_engine_sim_result.py [-h] [--require-pytorch]
                                           [--allow-canonical]
                                           [--require-source-backed]
                                           [--strict-source-backed]
                                           result_json

Validate a three-engine sim result envelope. This checks the result-shape
contract only. It does not prove the math.

positional arguments:
  result_json

options:
  -h, --help            show this help message and exit
  --require-pytorch
  --allow-canonical
  --require-source-backed
                        Also read declared engine source files and require
                        source-backed rich package evidence.
  --strict-source-backed
                        Like --require-source-backed, but fail mixed/thin
                        declared load-bearing claims too.
```

Verdict: **PASS**

## 4b. Capability probe help

Command run:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --help
```

Exit status: `0`

Key output lines:

```text
usage: verify_load_bearing_has_capability_probe.py [-h] [--report-json]
                                                   [--sim SIM]

options:
  -h, --help     show this help message and exit
  --report-json  Write JSON summary to /Users/joshuaeisenhart/Codex-Ratchet/sy
                 stem_v4/probes/a2_state/sim_results/load_bearing_capability_a
                 udit.json
  --sim SIM      Gate a single sim path; print JSON report; exit 0 if all
                 load-bearing tools have passing capability probes.
```

Verdict: **PASS**

## 5a. Disk writable

Command run:

```bash
test -w system_v6/sims && stat -f '%Sp %Su %Sg %N' system_v6/sims
```

Exit status: `0`

Key output lines:

```text
drwxr-xr-x joshuaeisenhart staff system_v6/sims
```

Verdict: **PASS**

## 5b. Collision check

Command run:

```bash
test -e system_v6/sims/mct_dynamic_admissibility_packet_v0; rc=$?; if [ $rc -eq 0 ]; then find system_v6/sims/mct_dynamic_admissibility_packet_v0 -maxdepth 2 -print; else echo 'no pre-existing system_v6/sims/mct_dynamic_admissibility_packet_v0'; fi; exit $rc
```

Exit status: `1`

Key output lines:

```text
no pre-existing system_v6/sims/mct_dynamic_admissibility_packet_v0
```

Verdict: **PASS**

