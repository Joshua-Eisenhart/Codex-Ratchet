# Sim Engines v0.1

This is the independent installation, inventory, and integration surface for
the complete computation estate. It is not ConstraintBox and it is not a
scientific claim.

The existing `serialized/` and `stress/` probes remain source history. V9 adds
the missing product machinery:

- portable install profiles in `install/profiles.v9.json`;
- a strict Julia project in `install/julia/`;
- a normalized tool registry with one integration level per tool;
- a live doctor that records what is installed on the current machine without
  upgrading installation into integration;
- source/test/evidence pointers for exercised tools.

## Portable setup

```bash
python3 sim_engines/install.py list
python3 sim_engines/install.py plan --profile python-base --profile graph-topology
python3 sim_engines/install.py create --profile python-base --profile graph-topology --venv .venv-sim
python3 sim_engines/install.py create --profile holodeck-world-model --venv .venv-holodeck-engines
```

Profiles resolve their declared includes. For example,
`holodeck-world-model` brings in `python-base` and `torch`; `cb-mirror` remains
an isolated five-package profile with no heavy runtime includes.

Julia is deliberately separate:

```bash
julia --startup-file=no --project=sim_engines/install/julia \
  -e 'using Pkg; Pkg.instantiate(); Pkg.precompile()'
```

No Java runtime is needed for CB. The optional temporal-formal profile belongs
here because TLC and Apalache are external verification tools. It is not a
default install profile.

## Live index

```bash
python3 sim_engines/registry/build_registry.py
python3 sim_engines/doctor.py --output-dir sim_engines/status
```

The live index reports registered and unregistered installed distributions.
It does not run every function probe. `declared_integration_level` comes from
source/receipt evidence; `live_install_state` comes from the current machine.
Both must be present before anyone describes a tool as exercised here.
