# External simulation runtime contract

ConstraintBox's kernel is not a simulation estate. The kernel is the deterministic intake, solver, symbolic, workflow, receipt, and Mini-Lev controller. Simulation engines are separately installed workloads that CB can challenge and verify through a small fixed surface.

This document records the executable and package boundary so the controller is not silently coupled to one developer machine.

## Controller authority

| Decision | Authority | Rule |
|---|---|---|
| Python executable | CB controller process | Use the interpreter that launched CB; no request, LLM, or public CLI executable override exists. |
| Julia executable | Operator environment, then CB profile check | Discover `julia` from `PATH`, check the version, then execute that same path. |
| Runtime compatibility | Deterministic profile code | Unsupported or missing runtime parks; an injected different executable fails. |
| Module ownership/version | Deterministic distribution inspection | Require a compatible window and an import origin owned by the named installed distribution. |
| Operation result | Controller recomputation | A separate worker executes the fixed API; CB recomputes positive, negative, boundary, binding, and source controls. |
| LLM explanation | Advisory only | An LLM may explain a parked/failed receipt but never selects a runtime, package version, worker, gate, or disposition. |

Local executable paths and SHA-256 values are retained in receipts as observations. They are explicitly not profile inputs. This catches a changed runtime during replay without turning a Homebrew path or one wheel build into the product policy.

## Active portable profiles

| Profile | Compatibility window | Used by |
|---|---|---|
| `external-cpython-3.11-3.13-v1` | CPython `>=3.11,<3.14` | `constraintbox engine-test` plus direct JAX, PyTorch, PySINDy, SciPy, and Diffrax capabilities. |
| `external-julia-1.12-v1` | Julia `>=1.12,<1.13` | External packet and Julia DifferentialEquations capability. |
| PyTorch distribution surface | `torch >=2.11,<2.12` | Fixed `torch.func.jacrev` challenge. |
| JAX distribution surface | `jax,jaxlib >=0.10,<0.11` | Fixed `jax.grad` / `jax.vmap` / `jax.jit` challenge. |
| PySINDy distribution surface | `pysindy >=2.1,<2.2`, `numpy >=2.3,<2.4` | Fixed `SINDy.fit` / `SINDy.predict` affine generator challenge. |
| PyDMD distribution surface | `PyDMD >=2025.8,<2026`, `numpy >=2.3,<2.4` | Fixed `DMD.fit` / `eigs` / reconstruction challenge. |
| PyMDP distribution surface | `inferactively-pymdp >=1.0,<1.1`, `jax >=0.10,<0.11` | Fixed `Agent.infer_states` / `infer_policies` challenge. |
| SciPy distribution surface | `scipy >=1.17,<1.18` | Fixed `scipy.linalg.expm` rotation challenge. |
| Diffrax distribution surface | `diffrax >=0.7,<0.8`, `jax,jaxlib >=0.10,<0.11` | Fixed `ODETerm` / `Tsit5` / `diffeqsolve` affine-flow challenge. |

The Julia DifferentialEquations capability also retains its strict-carrier project digest. That is a workload project/source binding, not a macOS path or binary hash policy. A source-level compatibility profile is not itself a clean-host installation result; the core wheel has that separate verification, while external workload installation is deliberately reported as unverified until it is actually rerun in a fresh external environment.

## Real integrated workload route

`constraintbox engine-test` with no `--capability` runs the first small cross-engine packet:

```text
controller-selected Python
  -> JAX grad/vmap/jit row
  -> PyTorch jacrev row
  -> PySINDy fit/predict row
  -> controller-built identified-rate JSON
  -> controller-selected Julia strict-carrier ODE solve
  -> deterministic receipt validation
```

The PySINDy-to-Julia JSON is a real, bounded producer/consumer handoff. The JAX and PyTorch rows are independently checked components in the same packet; they are not claimed to consume peer output. A passing receipt establishes only those named operations and controls, not engine readiness, CR truth, scientific validity, promotion, or release.

Run it from a source checkout with the selected Python environment:

```bash
PYTHONPATH=src python -m constraintbox engine-test --output /tmp/cb-packet.json
```

An unavailable compatible runtime returns `PARKED`; it does not fall back to a different executable. An injected alternate runtime returns `FAIL` with `runtime_selection_override_rejected`.

## Full capability-suite runtime-contract index

`constraintbox capability-suite` records two independent facts for every row:

1. `disposition` says whether the named bounded operation executed and independently replayed in this local run.
2. `runtime_contract_report` says whether the adapter has a controller-selected compatibility profile or remains host-bound. It does **not** turn a profile implementation into a clean external-install result.

The following is the documentation projection of the controller-owned `_RUNTIME_CONTRACT_BY_CAPABILITY` table in `constraintbox.capability_suite`; the test suite checks that the identifier/status rows below stay aligned with that source of authority.

| Capability identifier | Bounded operation actually challenged | Runtime-policy state | Controller profile / legacy policy | Clean external-install proof |
|---|---|---|---|---|
| `pytorch-jacobian-v1` | `torch.func.jacrev` | `PROFILE_IMPLEMENTED_UNVERIFIED` | `external-cpython-3.11-3.13-v1` | No |
| `jax-autodiff-v1` | `jax.grad` + `jax.vmap` + `jax.jit` | `PROFILE_IMPLEMENTED_UNVERIFIED` | `external-cpython-3.11-3.13-v1` | No |
| `pysindy-affine-generator-v1` | `SINDy.fit` + `SINDy.predict` | `PROFILE_IMPLEMENTED_UNVERIFIED` | `external-cpython-3.11-3.13-v1` | No |
| `julia-diffeq-v1` | `ODEProblem` + `solve` + `Tsit5` | `PROFILE_IMPLEMENTED_UNVERIFIED` | `external-julia-1.12-v1` | No |
| `scipy-expm-rotation-v1` | `scipy.linalg.expm` | `PROFILE_IMPLEMENTED_UNVERIFIED` | `external-cpython-3.11-3.13-v1` | No |
| `diffrax-tsit5-affine-flow-v1` | `ODETerm` + `Tsit5` + `PIDController` + `diffeqsolve` | `PROFILE_IMPLEMENTED_UNVERIFIED` | `external-cpython-3.11-3.13-v1` | No |
| `graph-topology-crosscheck-v1` | finite cycle/filled-complex and connectivity calls through GUDHI, TopoNetX, XGI, NetworkX, igraph, Rustworkx, PyTorch, and PyG | `PROFILE_IMPLEMENTED_UNVERIFIED` | `external-cpython-compatible-api-v1` | No |
| `pydmd-discrete-rate-v1` | `DMD.fit` + `eigs` + reconstruction | `PROFILE_IMPLEMENTED_UNVERIFIED` | `external-cpython-3.11-3.13-v1` | No |
| `pymdp-two-state-inference-v1` | `Agent.infer_states` + `infer_policies` | `PROFILE_IMPLEMENTED_UNVERIFIED` | `external-cpython-3.11-3.13-v1` | No |
| `pykoopman-identity-edmd-v1` | `Koopman.fit` + `predict` + `EDMD.fit` | `LEGACY_HOST_BOUND` | `legacy_exact_runtime_and_artifact_policy` | No |
| `quimb-cotengra-bounded-suite-v1` | Quimb eigensystem/trace + Cotengra search | `LEGACY_HOST_BOUND` | `legacy_exact_runtime_and_artifact_policy` | No |
| `multiengine-dlpack-diffeq-v1` | Torch-to-JAX DLPack plus independent Julia ODE lane | `LEGACY_HOST_BOUND` | `legacy_exact_runtime_and_artifact_policy` | No |
| `basic-packet-cross-engine-v1` | PySINDy identified-rate JSON consumed by Julia, plus fixed JAX/PyTorch rows | `LEGACY_HOST_BOUND` | `legacy_fixed_fixture_runtime_policy` | No |

`PROFILE_IMPLEMENTED_UNVERIFIED` means that the adapter no longer makes a specific local path, binary hash, or exact wheel build its acceptance policy. It does not mean a fresh machine has installed that external adapter successfully. `LEGACY_HOST_BOUND` means the old adapter itself still makes such a host-specific policy load-bearing, even if its local bounded operation happens to pass.

## Explicit migration boundary

The core wheel has a fresh clean-environment verification for the lean Python/SMT/SymPy/Rustworkx kernel. That does not extend to the external workload adapters. Within the full external suite, nine direct profiles have migrated to controller-selected compatibility policy but none has a clean external-install proof; the other four remain host-bound. Older satellite adapters remain in the checkout and may still carry historical host-specific pins. They are not part of the lean core and must not be described as portable or as normal-install CB dependencies until each is moved to this profile contract and rerun:

| Status | External adapter families |
|---|---|
| Controller-selected profile implemented; clean external-install verification still required | JAX, PyTorch, PySINDy, Julia DifferentialEquations, SciPy, Diffrax, graph/topology crosscheck, PyDMD, and PyMDP. |
| Legacy external-adapter migration still required | Basic packet suite adapter, PyKoopman, Quimb/Cotengra, multiengine DLPack/DiffEq, and other broad-estate adapters. |

This is deliberate containment: an un-migrated adapter cannot redefine CB core policy merely because its source happens to live beside the package. It remains an external test target until it has a controller-selected runtime, bounded operation, deterministic controls, a fresh receipt, and (before a portable-install claim) a clean external-install verification.
