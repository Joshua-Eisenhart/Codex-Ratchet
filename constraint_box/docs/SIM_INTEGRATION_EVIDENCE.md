# Simulation integration evidence

This is an evidence and rerun guide for external simulation workloads.  It is
not a CB-core installation guide, an engine bundle, or a claim that every
simulation library is ready.  Core installation remains in
[CORE_INSTALL.md](CORE_INSTALL.md); external runtime setup remains in
[SIM_SETUP.md](SIM_SETUP.md).

## What a real evidence run contains

Run the fixed suite only after the selected external runtimes have been
installed.  It creates a new directory and, for every profile, retains:

- the tool result and capability receipt;
- the Mini-LevOS flow events, head, and flow receipt;
- a controller-origin attestation; and
- a second, fresh-process independent replay result.

The suite does not accept an import check, a NumPy substitute, or a JSON file
written by a caller as evidence that another engine ran.  The aggregate result
is eligible only when all named tool operations and their independent replays
are eligible.

```bash
cd /path/to/constraint_box
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m constraintbox capability-suite \
  --request-id local-sim-suite-001 \
  --run-dir /absolute/new/cb-sim-suite-001 \
  --output /absolute/new/cb-sim-suite-001-result.json
```

The run directory must be new.  A missing compatible engine must become a
non-eligible result; it must not cause the controller to select another
interpreter or install a package.

## Fixed test matrix

| Profile | Actual bounded operation | Test role |
|---|---|---|
| `pytorch-jacobian-v1` | `torch.func.jacrev` on CPU `float64` | Jacobian with positive, wrong-value, and boundary controls |
| `jax-autodiff-v1` | `jax.grad`, `jax.vmap`, `jax.jit` | x64 derivative controls |
| `pysindy-affine-generator-v1` | `SINDy.fit`, `SINDy.predict` | affine system identification and held-out prediction |
| `julia-diffeq-v1` | `ODEProblem`, `solve`, `Tsit5` | strict-carrier ODE solve |
| `scipy-expm-rotation-v1` | `scipy.linalg.expm` | rotation-matrix exponential |
| `diffrax-tsit5-affine-flow-v1` | `ODETerm`, `Tsit5`, `PIDController`, `diffeqsolve` | affine ODE flow |
| `pydmd-discrete-rate-v1` | `DMD.fit`, `DMD.eigs`, reconstruction | scalar-rate decomposition |
| `pymdp-two-state-inference-v1` | `Agent.infer_states`, `Agent.infer_policies` | two-state categorical inference |
| `pykoopman-identity-edmd-v1` | `Koopman.fit`, `Koopman.predict`, `EDMD.fit` | bounded identity-plus-EDMD contraction |
| `quimb-cotengra-bounded-suite-v1` | Quimb `qarray/eigvalsh/trace`; Cotengra `HyperOptimizer.search` | bounded tensor-network operations |
| `multiengine-dlpack-diffeq-v1` | PyTorch `jacrev` -> DLPack -> JAX `from_dlpack/jit/vmap`; separate Julia `Tsit5` lane | real Torch-to-JAX tensor consumer; Julia lane is independent, not a peer-output consumer |
| `basic-packet-cross-engine-v1` | PySINDy `fit/predict` -> controller-built JSON -> Julia `ODEProblem/solve/Tsit5` | real legacy PySINDy-to-Julia producer/consumer handoff |

The final two rows are the only current cross-engine consumer paths.  They are
integration diagnostics, not a claim of a single all-engine simulation.  The
next integration work should add a small number of genuine shared-simulation
workloads only after each constituent profile has clean-install evidence.

## Separate evidence product

Raw external results belong in a separate evidence ZIP, not in the contained
CB core ZIP.  Build it from a completed suite with:

```bash
PYTHONPATH=src python scripts/build_sim_integration_evidence_bundle.py \
  --run-dir /absolute/new/cb-sim-suite-001 \
  --suite-result /absolute/new/cb-sim-suite-001-result.json \
  --output /absolute/out/ConstraintBox_Sim_Integration_Evidence.zip

PYTHONPATH=src python scripts/verify_sim_integration_evidence_bundle.py \
  --bundle /absolute/out/ConstraintBox_Sim_Integration_Evidence.zip \
  --receipt /absolute/out/ConstraintBox_Sim_Integration_Evidence.verification.json
```

The bundle verifier checks every archived digest, validates all twelve profile
rows, checks the retained aggregate against the exported result, and confirms
that each row contains its flow receipt, origin attestation, and fresh replay.
It makes no claim of clean external installation, broad engine readiness, CR
truth, scientific validity, release, or promotion.

## Interpreting the two status dimensions

Each profile reports both an operation disposition and a runtime-contract
state.  They must not be merged.

| Field | Meaning |
|---|---|
| `ELIGIBLE` disposition | this named bounded operation ran under the selected local runtime and passed its fixed controls and independent replay |
| `PROFILE_IMPLEMENTED_UNVERIFIED` | controller source contains a portable version/API profile, but no clean external installation has yet proved it |
| `LEGACY_HOST_BOUND` | the operation ran locally, but its adapter still depends on legacy exact-host policy and requires migration |

Thus a green local row is useful proof of a real operation, while still not
being proof that a fresh user can install the same external engine elsewhere.
