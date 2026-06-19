# Environment Redundancy Audit

Repo audited: `/Users/joshuaeisenhart/Codex-Ratchet`  
Audit mode: read-only, except writing this report.  
Canonical doctrine checked: libraries live outside the repo in depots/envs, not vendored or cloned into project source.

## 1. Vendored-In-Repo Scan

Verdict: no vendored sim tool libraries were found inside the repo.

Checks run:

```text
find . -path ./.git -prune -o \( -type d \( -name site-packages -o -name node_modules -o -name .julia -o -name .CondaPkg -o -name venv -o -name .venv \) -print \)
find . -path ./.git -prune -o -type f \( -name '*.whl' -o -name 'setup.py' -o -name 'pyproject.toml' -o -name 'Project.toml' -o -name 'Manifest.toml' \) -print
find . -path ./.git -prune -o -type f -size +50M -print0 | xargs -0 du -sh
rg -n "^path\s*=|path\s*=\s*\"|repo-rev|repo-url" -g 'Manifest.toml' -g 'Project.toml' .
```

Findings:

- No repo-local `site-packages/`, `node_modules/`, `.julia/`, `.CondaPkg/`, `venv/`, `.venv/`, or wheel files were found.
- No files larger than 50 MB were found outside `.git`.
- The only `Project.toml` / `Manifest.toml` files found are expected project specs:
  - `system_v5/julia_carrier/Project.toml`
  - `system_v5/julia_carrier/Manifest.toml`
  - `system_v5/julia_optional/acsets_pilot/Project.toml`
  - `system_v5/julia_optional/acsets_pilot/Manifest.toml`
- `pyproject.toml` is not a Python package project; it only contains local `mutmut` config.
- Manifest local-path dependency check found no `path = ...` entries pointing into the repo.
- `system_v5/julia_carrier/Manifest.toml` is 152K and `system_v5/julia_optional/acsets_pilot/Manifest.toml` is 16K. These are manifests/specs, not package source.

Top repo sizes checked:

```text
173M ./.git
 95M ./system_v5
 95M ./system_v4
 30M ./READ ONLY Legacy core_docs
3.2M ./scripts
1.0M ./work
676K ./visualizer
496K ./.claude
```

`.gitignore` coverage:

- Present: `node_modules/`, `.CondaPkg/`, `**/.CondaPkg/`, `archive/`, `*.zip`, generated JSON result estates, `system_v5/legos/results/`, and `system_v5/julia_carrier/Manifest.toml`.
- Gap: `.gitignore` does not explicitly list `.venv/`, `venv/`, `site-packages/`, `.julia/`, or `*.whl`. The current repo is clean anyway, but these should be added to prevent future accidental vendoring.

## 2. Python Env Redundancy

Verdict: no redundant Codex Ratchet Python sim env was found. The apparent two paths are one env: `/Users/joshuaeisenhart/.local/share/sim-stack` is a symlink to `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main`.

Canonical env from `Makefile`:

```text
SIM_STACK := /Users/joshuaeisenhart/.local/share/sim-stack
SIM_PY ?= $(SIM_STACK)/bin/python3
PYTHON ?= $(SIM_PY)
```

Enumerated envs:

```text
/Users/joshuaeisenhart/.local/share/sim-stack -> /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main
```

No additional env dirs were found under `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/*`. No repo-local `pyvenv.cfg` or activation files were found.

Sizes:

```text
3.5G /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main
0B   /Users/joshuaeisenhart/.local/share/sim-stack  (symlink)
```

Python version:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
Python 3.13.6
```

Heavyweight sim packages installed in the canonical env:

```text
torch 2.11.0
torch-geometric 2.7.0
torch_ga 0.0.6
torchdiffeq 0.2.5
torchode 1.0.1
xitorch 0.3.0
cvxpylayers 1.2.0
jax 0.10.1
jaxlib 0.10.1
jaxopt 0.8.5
jaxtyping 0.3.10
equinox 0.13.8
diffrax 0.7.2
lineax 0.1.1
optimistix 0.1.0
blackjax 1.5
optax 0.2.8
flax 0.12.7
dynamiqs 0.3.4
dynamax 1.0.1
NetKet 3.21.0
quimb 1.14.0
cotengra 0.8.0
qutip 5.2.3
qutip-jax 0.1.1
geomstats 2.8.0
e3nn 0.6.0
e3nn-jax 0.21.0
clifford 1.5.1
kingdon 2.1.1
z3-solver 4.16.0.0
cvc5 1.3.3
sympy 1.14.0
gudhi 3.12.0
TopoNetX 0.4.0
xgi 0.10.1
rustworkx 0.17.1
igraph 1.0.0
networkx 3.6.1
kahypar 1.3.7
miniKanren 1.0.5
```

Redundant heavyweight packages installed in more than one Codex Ratchet env:

```text
None found. There is only one physical Codex Ratchet Python env.
```

Runtime doctor result:

```text
schema: codex_runtime_env_doctor.v1
summary.ok: true
install_state: stable_observed
active_installers.ok: true
repo_pollution: []
canonical python alias: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
physical python env: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main
```

Receipts and scripts currently point to the same env:

- `system_v5/ops/tooling/codex_runtime_capability_shakedown_results.json` records `canonical_python` as `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3` and `sys_executable` as `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3`.
- Recent result coverage files record package files under `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/lib/python3.13/site-packages/...`.
- Several older scripts and docs still use the physical path directly, for example `system_v5/grok_sim/loop_runner/*.py` and some historical docs. This is drift in command spelling, not a second env.
- The runtime mapping reference audit returned `ok: true`, `failure_count: 0`, with warnings only for older/reference docs still naming the physical path or Homebrew/local Python.

## 3. Julia Redundancy

Verdict: Julia packages are depot-shared, not vendored per project. The `julia_carrier` and `acsets_pilot` manifests duplicate dependency declarations, but package bodies and artifacts live in the shared depot, so this is not redundant repo disk usage.

Julia depot size and major contents:

```text
6.0G /Users/joshuaeisenhart/.julia
4.5G /Users/joshuaeisenhart/.julia/compiled
669M /Users/joshuaeisenhart/.julia/packages
537M /Users/joshuaeisenhart/.julia/artifacts
144M /Users/joshuaeisenhart/.julia/scratchspaces
140M /Users/joshuaeisenhart/.julia/environments
140M /Users/joshuaeisenhart/.julia/environments/v1.12/.CondaPkg
```

Second depot check:

```text
find ~ -maxdepth 4 -type d -name .julia
/Users/joshuaeisenhart/.julia
```

Runtime doctor Julia state:

```text
julia executable: /opt/homebrew/Cellar/julia/1.12.6/bin/julia
active project: /Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml
load path: @:@stdlib
depot path: /Users/joshuaeisenhart/.julia:/opt/homebrew/Cellar/julia/1.12.6/local/share/julia:/opt/homebrew/Cellar/julia/1.12.6/share/julia
```

Manifest comparison:

```text
system_v5/julia_carrier/Manifest.toml deps: 459
system_v5/julia_optional/acsets_pilot/Manifest.toml deps: 89
shared deps observed: ArgTools, Artifacts, Base64, ColorTypes, Colors, Combinatorics, Compat, CompilerSupportLibraries_jll, Crayons, DataAPI, DataStructures, Dates, Downloads, JSON, JSON3, LinearAlgebra, StaticArrays, Tables, and standard library/JLL support packages.
```

Interpretation:

- The shared manifest entries are normal Julia project resolution overlap.
- The actual package source is under `/Users/joshuaeisenhart/.julia/packages`, and artifacts are under `/Users/joshuaeisenhart/.julia/artifacts`.
- No Julia package source or artifact copy was found inside the repo.
- The 140M `/Users/joshuaeisenhart/.julia/environments/v1.12/.CondaPkg` is outside the repo. It is bridge/global default-environment residue, not part of the strict carrier. The runtime doctor confirms strict carrier excludes `CondaPkg`, `DLPack`, and `PythonCall`.

## 4. Verdict And Consolidation Plan

Bottom-line verdict:

- Repo vendoring: clean. No sim libraries were found vendored in-repo.
- Python redundancy: clean. There is one physical Codex Ratchet Python env, 3.5G at `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main`, exposed by the canonical alias `/Users/joshuaeisenhart/.local/share/sim-stack`.
- Julia redundancy: acceptable. One user depot at `/Users/joshuaeisenhart/.julia` holds package bodies/artifacts; repo project manifests do not duplicate package source.
- Main remaining risk: old docs/scripts and archive surfaces still mention physical Python paths or Homebrew Python, which can confuse future agents. The runtime guard catches this as warnings, not failures.

Recommended canonical Python env for v6:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
```

Reason:

- It is the Makefile `PYTHON` default.
- It resolves to the existing physical env at `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main`.
- Current runtime docs, skills, and doctor all identify it as the preferred command surface.
- Recent receipts using either the alias or physical path refer to the same site-packages tree.

Bounded consolidation plan, no action taken:

1. Keep `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main` as the only physical Python sim env.
2. Keep `/Users/joshuaeisenhart/.local/share/sim-stack` as the public/canonical alias for commands, docs, skills, and v6 Makefile references.
3. Do not create repo-local `.venv`, `venv`, `.CondaPkg`, `.julia`, or `site-packages` directories.
4. Leave old physical-path receipts alone as historical evidence; update only active scripts/docs when touched.
5. Add `.gitignore` entries for `.venv/`, `venv/`, `site-packages/`, `.julia/`, and `*.whl` to close the remaining future-vendoring gaps.
6. Leave `/Users/joshuaeisenhart/.julia/environments/v1.12/.CondaPkg` frozen/quarantined unless a separate bridge cleanup task is opened. It is outside the repo and not active strict-carrier evidence.
7. Do not delete any env or depot from this audit alone. There is no redundant Codex Ratchet env to remove.
