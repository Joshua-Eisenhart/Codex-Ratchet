# Attractor-basin external validation profile

This directory is an opt-in ConstraintBox challenge, not part of the CB core
dependency set and not a bundled simulation-engine runtime.

- `basin_controller.py` is the deterministic CB-owned orchestrator and gate.
- `smt_basin.py` is a CB-owned finite checker using Z3, CVC5, and an explicit
  CPython enumeration. It is not a simulation engine.
- `jax_basin.py`, `julia_basin.jl`, and `torch_basin.py` are separate external
  simulation-evidence producers. They cannot admit themselves or read a peer
  receipt.
- `object_card.json` fixes the map, grid, step count, boundary rule, expected
  controls, roles, and claim ceiling before any engine runs.
- `julia_environment/` is the exact Julia Project and Manifest used for the
  retained 2026-08-01 run. It is an external reproducibility input.

The controller requires a new, non-existing output directory for every run.
It runs each simulation lane twice, builds one typed observation bundle, runs
the SMT checker twice, calls the contained formal registry, and finishes in a
two-node Mini-Lev tool-to-gate flow with a retained semantic ledger.

`PASS` means only that this finite 341-point, 80-step challenge passed its
declared operations and hostile controls. It does not mean a continuous basin
proof, whole-engine readiness, whole-estate integration, ClaimGate admission,
release, promotion, CR truth, or automatic tuning.
