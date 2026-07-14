---
name: codex-ratchet-env-agent-coordination
description: Coordinate Codex Ratchet package installs and package-dependent workers so libraries are found in the intended Python, Julia, GitHub, and optional-project locations before any agent installs or claims tool evidence.
---

# Codex Ratchet Env Agent Coordination

Use this whenever a Codex Ratchet task mentions broken installs, missing
libraries, package locations, Julia/JAX/PyTorch tooling, GitHub source repos,
or any install request from Claude, Codex, Hermes, Gemini, or another worker.

This skill is a coordination guard, not an install recipe.

## First Rule

Do not install because a package is missing from the wrong runtime. Read:

```text
system_v5/docs/RUNTIME_LIBRARY_LOCATION_MAP_20260608.md
system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md
```

Then run the read-only doctor:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
```

For machine-readable worker input:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py --json
```

The doctor installs nothing and deletes nothing.

## Canonical Anchors

Use these unless the user explicitly scopes another environment:

```text
repo: /Users/joshuaeisenhart/Codex-Ratchet
python_preferred_alias: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
python_physical_env: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main
julia: /opt/homebrew/bin/julia
julia_carrier_project: /Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml
julia_depot: /Users/joshuaeisenhart/.julia
github_source_repos: /Users/joshuaeisenhart/GitHub
```

Prefer the `sim-stack` alias in commands and worker receipts. The older
`codex-ratchet/envs/main` path is the physical target behind the alias and is
kept for receipt compatibility.

The repo gets source, docs, probes, receipts, and lightweight project files.
Package bodies, virtualenvs, CondaPkg envs, node_modules, and caches do not
belong in the repo.

## Known Current Package Truth

Python/JAX/PyTorch work uses the shared `sim-stack` alias. Current avoid/block list:

```text
dgl
torch_scatter
torch_sparse
bayeux
```

These are not reasons to install during ordinary sim work. Use PyG native
scatter paths, blackjax/optimistix, or a bounded isolated receipt if the user
explicitly asks to revisit them.

Current canonical Python already has the dense JAX/PyTorch/graph/topology
surface described in `system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md`.
Treat missing optional CS/AI packages such as `hypernetx`, `hypergraphx`,
`egglog`, `pycauset`, `dowhy`, `causal_learn`, `pgmpy`, and extra topology
helpers as `optional_probe_candidate`, not default installs.

Julia carrier work uses the repo carrier project. Do not add `PythonCall`,
`DLPack`, or `CondaPkg` to `system_v5/julia_carrier/Project.toml` unless the
user explicitly asks for a bridge micro-probe. Their normal home, when needed,
is quarantined global/isolated bridge machinery, not the carrier project.

`Basins.jl` is blocked by default; use `Attractors` + `DynamicalSystems` unless
an isolated compatibility project is explicitly built and import-verified.

Julia category/rewriting/ML/proof extensions such as `CombinatorialSpaces`,
`Catlab`, `AlgebraicRewriting`, `Flux`, `Lux`, `Enzyme`, interval,
reachability, and SOS packages are optional isolated-project candidates first,
not strict-carrier defaults.

## Install Intent Gate

Before any package install, create an install intent:

```json
{
  "worker": "codex|claude|hermes|gemini|other",
  "requested_packages": ["..."],
  "target_manager": "pip|uv|julia-pkg|conda|brew|other",
  "target_environment": "absolute interpreter or Julia active project",
  "reason": "which bounded claim needs these packages",
  "preflight_command": "read-only command proving the target env lacks it",
  "preflight_result": "already_present|missing|wrong_env|blocked|unknown",
  "install_allowed": false
}
```

Only the controller or the user can set `install_allowed` to true. If another
installer/precompile is active, mark package state `in_flux` and do not install
into the same manager/project.

## Worker Receipt Requirements

Every package-dependent worker reports:

```text
sys.executable or Base.active_project()
package import status in the actual target runtime
module __file__ or Julia project/depot path
known blocked packages skipped or quarantined
repo pollution scan result
active installer state
```

Do not accept worker prose like "installed" or "works" unless it names the
target runtime and import receipt.

## Classification

Use these labels:

- `canonical_env_verified`: imports in the target runtime used by the sim.
- `installed_only`: declared by a package manager, not import-verified.
- `wrong_env`: installed elsewhere, not in the runtime the sim uses.
- `blocked_missing_package`: missing and no install authorized.
- `quarantined`: available only behind isolated project/bridge receipt.
- `claim_load_bearing`: function-level receipt shows the tool changes,
  constrains, certifies, or falsifies the bounded claim.

Import success is not claim integration.

## Output

Return:

```text
Environment state:
Canonical paths:
Repo pollution:
Python import status:
Julia import status:
Active installers:
Install decision:
Next safe action:
```

Do not promote scientific claims from this skill. It only controls environment
and install truth.
