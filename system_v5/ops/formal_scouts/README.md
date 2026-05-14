# Formal-Scout Geometric Constraint Manifold Work

Status: exploratory, noncanonical

This directory is the clean middle layer between informal provider proposals and
canonical `system_v4/probes` sims.

`system_v4/probes` is the reference corpus for this work, not the exploratory
write surface. New manifold exploration stays here unless a later promotion
manifest explicitly moves a hardened sim.

## Rules

- Harnesses may import existing formal legos.
- Harnesses must write result receipts under `results/`.
- Harnesses must set `classification: formal_scout`.
- Harnesses must set `promotion_allowed: false`.
- Harnesses must include nearby graveyards.
- Names must describe the math being simulated.

## Current Harnesses

| Harness | Result | Readout | Ceiling |
|---|---|---|---|
| `sim_nested_finite_geometry_holonomy_noncommutation_probe.py` | `results/nested_finite_geometry_holonomy_noncommutation_probe_results.json` | nested density/Hopf/holonomy/transport tower | formal scout only |
| `sim_entropy_reduction_before_hopf_projection_order_probe.py` | `results/entropy_reduction_before_hopf_projection_order_probe_results.json` | entropy-filtered finite density family before Hopf projection readout | formal scout only |

## Next Queue

| Priority | Candidate | Purpose | Status |
|---|---|---|---|
| 1 | `sim_entropy_reduction_before_hopf_projection_order_probe.py` | test whether entropy filtering before projection changes finite survivor/readout structure | passing scout |
| 2 | `sim_su2_unit_quaternion_hopf_holonomy_order_probe.py` | test non-Abelian/SU(2)-style transport against U(1) controls | proposal targets importable |
| 3 | `sim_spinor_clifford_pauli_projection_order_probe.py` | test spinor-to-Clifford-to-Pauli layer ordering with adjacent controls | proposed |
| 4 | `sim_topology_cycle_hopf_projection_order_probe.py` | test finite topology readouts around Hopf projection and path order | proposed |

## Provider Split

Grok/Gemini may propose alternatives and attacks. Their output is not evidence
until Codex maps it to real repo callables and a formal-scout receipt.

Latest provider receipt: `provider_scouts_20260514.md`.

Machine-readable provider receipts live under `provider_receipts/`.

## Validation

Run:

`/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/validate_formal_scout_results.py`

Fresh rerun plus receipt validation:

`/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/validate_formal_scout_results.py --fresh-rerun`

Name lint:

`/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/lint_formal_scout_names.py`

Provider receipts:

`/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/validate_provider_receipts.py`
