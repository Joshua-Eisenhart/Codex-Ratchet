---
name: sim-stack-maintenance
description: Use when stewarding Codex Ratchet Julia, JAX, PyTorch, SMT, topology, tensor, graph, or bridge packages across installs, upgrades, package audits, engine-skill drift, or worker confusion about which libraries are available.
---

MIRROR: authoritative copy is .claude/skills/sim-stack-maintenance/SKILL.md; sync direction .claude -> codex_skills.

# Sim Stack Maintenance

Keep the Codex Ratchet runtime/tool layer healthy without turning package
presence into a scientific claim. This is a stewardship skill for the transient
environment; use the sim/proof skills for bounded result work.

## Cardinal Rule

Packages are used when relevant, never forced. A sim needs at least one
claim-relevant aligned package doing real work, not every installed package and
not decorative imports.

## Required Preflight

Read:

```text
system_v5/docs/RUNTIME_LIBRARY_LOCATION_MAP_20260608.md
system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md
```

Then run the read-only doctor from the active repo:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
```

For active reference drift:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/audit_runtime_mapping_references.py
```

Use `$codex-ratchet-env-agent-coordination` for install intent and active
installer checks. One package manager/project mutates at a time.

## Current Runtime Anchors

```text
repo: /Users/joshuaeisenhart/Codex-Ratchet
python: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
julia: JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier
```

Do not use bare `python3`, Homebrew Python, global Julia default-project
observations, or repo-local virtualenvs as active sim-stack truth.

## Package Truth Boundaries

- Python avoid/block list by default: `dgl`, `torch_scatter`, `torch_sparse`,
  `bayeux`.
- Use PyG native scatter paths and `blackjax`/`optimistix` instead of trying to
  resurrect those broken mappings during ordinary work.
- Many modern graph/topology/CS surfaces are already in the canonical Python
  env: `networkx`, `igraph`, `rustworkx`, `xgi`, `TopoNetX`, `gudhi`, and
  `kanren`. Do not install `hypernetx`, `hypergraphx`, `egglog`, causal
  packages, or extra topology packages unless the full target-set doc and a
  micro-probe install intent show why the installed set is insufficient.
- Strict Julia carrier excludes `PythonCall`, `DLPack`, and `CondaPkg` unless
  the user explicitly asks for an isolated bridge micro-probe.
- `Basins.jl` is blocked by default; prefer `Attractors` plus
  `DynamicalSystems` unless a separate compatibility receipt proves otherwise.
- Julia category/rewriting/ML/proof extensions such as `CombinatorialSpaces`,
  `Catlab`, `AlgebraicRewriting`, `Flux`, `Lux`, `Enzyme`, interval,
  reachability, and SOS packages are optional isolated projects first, not
  strict-carrier defaults.

## Maintenance Checks

Use live probes, not memory:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_engine_stack_shakedown.py
make runtime-environment-audit
```

The shakedown is a strict receipt-validating `classification=audit` artifact
with `promotion_allowed=false`. A pass means the runtime and skill wiring are
reachable; it does not admit a lego, bridge, manifold, Axis0, or physics claim.

## Skill And Agent Drift

Keep these surfaces mutually consistent:

- `system_v5/codex_skills/`
- `/Users/joshuaeisenhart/.codex/skills/`
- `/Users/joshuaeisenhart/.codex-second/skills/`
- `.claude/skills/`
- `.claude/agents/`

The engine skills are a package menu matched to claim shape:
`julia-sim`, `jax-sim`, `pytorch-sim`, and `three-engine-sim`. Use
`codex-ratchet-tool-status-auditor` to distinguish import reachability from
load-bearing tool integration.

## Output

Return:

```text
Environment state:
Runtime anchors:
Import/API shakedown:
Skill/agent drift:
Blocked/quarantined packages:
Install decision:
Next safe action:
```

No promotion claim is emitted by this skill.
