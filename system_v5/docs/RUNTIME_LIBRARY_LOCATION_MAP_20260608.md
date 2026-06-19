# Runtime Library Location Map

Status: current runtime map and install-location guard for Codex Ratchet.
Authority: subordinate to `AGENTS.md`, `CODEX.md`, and the process docs.
Updated: 2026-06-09.

This page exists because package state can be true in one environment and false
in another. Agents must check the actual target runtime before installing,
running, or claiming package-backed evidence.

Full installed/optional/avoid target sets are maintained in:

```text
system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md
```

## First Rule

Do not install because bare `python3` or the wrong Julia project cannot import a
package. First run:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
```

For machine-readable output:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py --json
```

The doctor is read-only. It installs nothing and deletes nothing.

Preferred shared Python entrypoint:

```bash
SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
```

`sim-stack` is a stable agent-facing alias. The physical environment remains
under `codex-ratchet/envs/main` for compatibility with older receipts.

## Canonical Locations

| Layer | Location | Role |
|---|---|---|
| Active repo | `/Users/joshuaeisenhart/Codex-Ratchet` | source, docs, probes, result receipts, lightweight project files |
| Python/JAX/PyTorch alias | `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3` | preferred shared Python runtime entrypoint for all agent surfaces |
| Python/JAX/PyTorch physical env | `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3` | physical target behind the alias; kept for older scripts and receipts |
| Python site-packages | `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/lib/python3.13/site-packages` | package bodies for the canonical Python runtime |
| Julia executable | `/opt/homebrew/bin/julia` | Julia runner |
| Julia carrier project | `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml` | repo-local lightweight project for carrier/Canon work |
| Julia depot | `/Users/joshuaeisenhart/.julia` | global Julia package depot and artifacts |
| GitHub source repos | `/Users/joshuaeisenhart/GitHub` | external/source repos, including world-engine and proof-ladder repos |

Approximate live sizes observed 2026-06-08:

```text
~/.local/share/sim-stack -> ~/.local/share/codex-ratchet/envs/main
~/.local/share/codex-ratchet/envs/main  3.5G
~/.julia                                5.5G
~/GitHub                                16G
```

These are not repo payloads.

## What May Live In The Repo

Allowed in repo:

- source code, probes, docs, scripts, result receipts, and lightweight project
  declarations such as `Project.toml`;
- local ignored lockfiles such as `system_v5/julia_carrier/Manifest.toml` when
  needed for a same-machine run, but do not treat an ignored local manifest as
  cross-agent evidence unless it is explicitly cited and hashed in the current
  receipt.

Not allowed in repo:

- `.CondaPkg/`;
- virtual environments: `.venv/`, `venv/`, `site-packages/`;
- `node_modules/`;
- Python bytecode/caches;
- package manager caches or downloaded package bodies.

If any appear, treat the environment state as dirty and run the doctor before
doing package-dependent work.

## Python Runtime Truth

Use this interpreter for Codex Ratchet JAX/PyTorch work:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
```

The physical target is:

```bash
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3
```

Do not use bare `python3`, `/opt/homebrew/bin/python3`, `/usr/bin/python3`, or
an IDE-selected interpreter for package truth. They can be valid Python
installations and still be the wrong Codex Ratchet runtime. In scripts and
agent receipts, prefer `SIM_PY` or the `sim-stack` alias unless an old receipt
is being reproduced exactly.

Current import-verified packages in the canonical env include:

```text
jax, jaxlib, equinox, diffrax, lineax, optimistix, blackjax, jaxopt,
optax, flax, orbax, chex, jaxtyping, dynamiqs, dynamax, flowMC, netket,
quimb, cotengra, autoray, e3nn_jax, jraph, haiku, numpyro, ott, qutip,
qutip_jax, jax_dataclasses, jaxlie, jaxga, pymc, scikit-learn, torch, torch_geometric,
torchdiffeq, torchode, xitorch, cvxpylayers, geomstats, e3nn, torch_ga,
clifford, z3, cvc5, sympy, numpy, scipy, pandas, networkx, igraph,
rustworkx, xgi, TopoNetX, gudhi, kanren, kahypar, opt_einsum
```

Use the full target-set page for the current split between `canon/core`,
`optional_probe_candidate`, `quarantined`, and `blocked_or_avoid`.

Current blocked or avoid packages:

```text
dgl                missing on this macOS/ARM + current torch stack
torch_scatter      missing; do not require for current PyG unless a pinned wheel receipt exists
torch_sparse       missing; do not require for current PyG unless a pinned wheel receipt exists
bayeux             imports against a removed JAX API; use blackjax/optimistix when scoped
oryx               imports against removed JAX internals
jax-verify         imports against removed JAX internals
```

Current optional Python graph/CS/AI packages that were not present in the
canonical env during the 2026-06-09 shakedown include:

```text
graph_tool, hypernetx, hypergraphx, ripser, persim, pyflagser, pygsp,
egglog, matchpy, distrax, pycauset, dowhy, causal_learn, causalai, pgmpy,
pomegranate
```

These are not automatic install targets. Use the full target-set page and an
install intent to decide whether one exact package belongs in an isolated
micro-probe.

Package import success is still not claim integration. It is only
`installed/import_verified` until a function-level receipt shows an API call
changing, constraining, certifying, or falsifying a bounded claim.

## Julia Runtime Truth

Use:

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier
```

The carrier project currently imports the core/Canon stack used by the active
foundation work, including:

```text
JSON3, JSON, CliffordAlgebras, Z3, Quaternions, Octonions, Graphs, ITensors,
QuantumClifford, QuantumOptics, Manifolds, Yao, DifferentialEquations,
Attractors, DynamicalSystems, ChaosTools
```

Strict carrier recheck on 2026-06-08 showed `Zygote` was visible through the
global default Julia project but not declared by the repo carrier project.
Treat it as optional/not carrier-verified until a deliberate install-intent
adds it to the carrier or scopes it to an isolated project.

Do not add `PythonCall`, `DLPack`, or `CondaPkg` back into
`system_v5/julia_carrier/Project.toml` unless the user explicitly asks for a
bridge micro-probe. They triggered a repo-local `.CondaPkg` once even though no
Julia carrier source used them.

`PythonCall`, `DLPack`, and `CondaPkg` may exist in the global Julia default
environment. Without `JULIA_LOAD_PATH=@:@stdlib`, Julia can fall through to
that global default even when the carrier project itself does not declare a
package. Importing `PythonCall` can create:

```text
/Users/joshuaeisenhart/.julia/environments/v1.12/.CondaPkg
```

That is outside the repo and should be treated as quarantined bridge machinery,
not as part of normal carrier work.

Known Julia blocked/avoid route:

```text
Basins.jl
```

Use `Attractors` + `DynamicalSystems` for basin work unless a separate isolated
compatibility project is explicitly created and import-verified.

## Optional Julia Projects

Use optional named projects only for their scoped package family:

```text
--project=@codex-ratchet-tensorkit-v1.12   TensorKit latest-style checks
--project=@codex-ratchet-peps-v1.12        PEPSKit compatibility checks
--project=@codex-ratchet-attractors-v1.12  isolated attractor/dynamics checks if needed
```

Do not globally downgrade the default or carrier project to make an optional
package coexist. Optional project success counts only for sims run under that
project and recorded with `Base.active_project()`.

## GitHub Source Repos

`/Users/joshuaeisenhart/GitHub` contains source checkouts and research/tooling
repos. They are not Python or Julia package environments by default.

Observed world-engine / proof-ladder groups:

```text
world engine: le-wm, lpwm, flowm, AnyFlow, Sana, stylegan3
proof ladder: auto_LiRPA
agent/OS: lev, leviathan*, hermes-agent*, codex-autoresearch, Sofia, pi-mono
```

Use these as source repos only after a task explicitly scopes them. Do not
assume cloning means installed into the Codex Ratchet Python env.

## Install Gate

Before any install, produce an install intent:

```json
{
  "requested_packages": [],
  "target_manager": "pip|uv|julia-pkg|conda|brew",
  "target_environment": "absolute interpreter or Julia active project",
  "reason": "bounded claim that needs this exact package",
  "preflight_command": "command that proved missing in the target env",
  "preflight_result": "already_present|missing|wrong_env|blocked|unknown",
  "install_allowed": false
}
```

Only the controller or the user can flip `install_allowed` to true.

If active package installers or precompile jobs are visible, mark package state
`in_flux` and do not start another install into the same manager/project.

## Receipt Language

Use these labels for packages:

- `canonical_env_verified`: imports in the target runtime used by the sim.
- `installed_only`: visible to a package manager, but not import-verified.
- `wrong_env`: installed somewhere other than the runtime the sim uses.
- `blocked_missing_package`: missing and no install authorized.
- `quarantined`: available only behind an isolated project or bridge probe.
- `claim_load_bearing`: function-level receipt proves the tool changes or
  certifies the bounded claim.

Never collapse `installed` into `claim_load_bearing`.
