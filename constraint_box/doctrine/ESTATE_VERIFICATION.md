# Simulation Estate Verification

**Date:** 2026-07-25
**Profile status:** proposed; `promotion_allowed: false`
**Execution:** isolated temporary environments, sequential workers

## Executed result

| Estate | Direct capabilities run | Resolved distributions | Result |
|---|---|---:|---|
| E0 constraint-core | finite Python, NumPy, SciPy, Z3, cvc5, TLA+/TLC | 4 Python packages plus external Java/TLC | `READY` |
| E1 manifold-local | JAX x64 CPU, Diffrax, quimb, cotengra | 22 | `READY` |
| E2 science-fields | PySINDy, PyDMD, inferactively-pymdp | 40 | `READY` |
| E3 cloud | NVIDIA, JAX CUDA, Torch CUDA | local probe only | `FAILED` as expected: no GPU route |

For E0–E2, every active capability passed its controller-owned positive check,
dispatch check and replay. Capabilities with a Python dependency also passed
dependency severance. Mutable finite/numeric fixtures passed the mutation
control.

## Manifold-fixture coverage

| Fixture | Evidence in this build | Coverage |
|---|---|---|
| F0 finite histories | four histories, two projections, fibres `[2,2]`, Hartley 2 bits | acceptance |
| F1 density stratum | trace, spectrum, rank, Rényi-0, von Neumann and dephased entropy | three-family parity |
| F2 channel order | SciPy finite channel propagation | partial; order tournament not yet wired |
| F3 history-pair field | core unit tests retain off-diagonal terms | core-tested; no independent estate parity |
| F4 extension fibre | core unit tests and F0 fibre counts | core-tested |
| F5 tensor factor | cotengra path cost and maximum intermediate size | path-tested; exact contraction rival pending |
| F6 known flow/law | Diffrax trajectory and fixed-library PySINDy recovery | acceptance |
| F7 known rate | PyDMD recovered multiplier `0.5` | acceptance |
| F8 finite active inference | posterior/policy normalization and finite free-energy telemetry | acceptance |
| F9 CPU/GPU parity | local CPU golden exists | cloud execution not run |

## Cross-estate parity

NumPy 2.5.1, JAX 0.11.0 x64 and quimb 1.14.0 agreed within `1e-8` on all six
declared F1 observables. The machine-readable receipt is
`estate_runs/E0_E1_DENSITY_PARITY.json`.

## TLA+ result

TLC 2.19 from stable `tla2tools.jar` 1.7.4 generated 73 states and found 45
distinct states with no invariant violation after two defects were corrected:

1. the observation transition did not assign a concrete evidence value;
2. policy generation could change after authorization but before worker start.

The acceptance control weakens `EvidenceBeforeEligibility`; TLC then reports
the invariant violation. The JAR is not included in this ZIP.

## Bugs found by executing the estate

| Defect | Consequence | Repair |
|---|---|---|
| resolving a venv Python symlink | silently tested the base interpreter | preserve the declared venv path |
| JAX dephasing passed a list to `eigvalsh` | false tool failure | build a backend-native array |
| generic coefficient tolerance | false PySINDy failure | fixed-law-specific tolerance and residual discriminator |
| unbounded TLA policy generation | non-terminating model state space | bounded model constant |
| policy change after authorization | stale-policy worker start | forbid the race in the transition system |
| terminal deadlock | TLC rejected absorbing dispositions | explicit terminal hold |

## Evidence files

- `estate_runs/E0_ACCEPTANCE.json`
- `estate_runs/E1_ACCEPTANCE.json`
- `estate_runs/E2_ACCEPTANCE.json`
- `estate_runs/E0_E1_DENSITY_PARITY.json`
- `estate_runs/E3_LOCAL_BOOT.json`
- `estate_runs/SUITE_INDEX.json`

The temporary environments and TLA+ JAR are intentionally not packaged.
