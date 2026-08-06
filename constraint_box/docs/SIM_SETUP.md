# Simulation runtime setup

Simulation engines are installed separately; they are not part of the Core
install and are not contained in ConstraintBox. CB can challenge installed
engines through fixed, controller-owned profiles. For the core product, see
[CORE_INSTALL.md](CORE_INSTALL.md).

## Controller authority

CB uses the interpreter that launched it; no request, LLM, or public CLI
executable override exists. It discovers `julia` from `PATH`, checks the
version, then executes that same path. Local paths and SHA-256 values remain
receipt observations, not acceptance-policy inputs. A missing runtime parks;
an injected different executable fails.

## Current runtime profiles

| Surface | Compatibility window |
|---|---|
| Python worker | CPython `>=3.11,<3.14` |
| Julia worker | Julia `>=1.12,<1.13` |
| PyTorch | `torch >=2.11,<2.12` |
| JAX | `jax,jaxlib >=0.10,<0.11` |
| PySINDy | `pysindy >=2.1,<2.2`, `numpy >=2.3,<2.4` |
| SciPy | `scipy >=1.17,<1.18` |
| Diffrax | `diffrax >=0.7,<0.8`, `jax,jaxlib >=0.10,<0.11` |

Use a normal environment manager or the estate's own installer to install an
engine and its native dependencies. This document deliberately does not make a
single local wheel, path, binary hash, or GPU configuration the product policy.

## Install and test one capability at a time

Start with one profile-implemented adapter in an isolated environment. For
example, the JAX bounded operation has the following *compatible-install
candidate*, not a passing receipt:

```bash
python -m venv .cb-sim-jax
.cb-sim-jax/bin/python -m pip install /absolute/path/to/constraint_box
.cb-sim-jax/bin/python -m pip install "jax>=0.10,<0.11" "jaxlib>=0.10,<0.11"
PYTHONPATH=src .cb-sim-jax/bin/python -m constraintbox engine-test \
  --capability jax-autodiff-v1 \
  --request-id local-jax-check-1 \
  --run-dir /absolute/run-root/local-jax-check-1
```

Use the corresponding compatibility row above for the selected PyTorch,
PySINDy, Julia, SciPy, or Diffrax capability. Do not merge every engine into
one environment merely because it can be installed; create a declared
environment for the workload you are actually challenging. The result must be
read as an operation receipt, not an installation claim.

After the named capability is independently passing, a controller-selected
`constraintbox capability-suite` can challenge the fixed suite. It will report
the four legacy host-bound adapters as such; a green local operation does not
remove that state. The `requirements/candidates/` and `requirements/locks/`
directories are estate maintenance material, not proof that an arbitrary host
matches the current external runtime contract.

## Adapter source is not runtime or estate

Adapter source and fixtures live beside CB so their contracts can be inspected
and challenged. That does not install the runtime, its native dependencies, or
the broad sim estate. A source-level compatibility profile is not a clean-host
external-install result.

| Runtime-contract state | Current adapters |
|---|---|
| `PROFILE_IMPLEMENTED_UNVERIFIED` | PyTorch, JAX, PySINDy, Julia DifferentialEquations, SciPy, Diffrax, graph/topology crosscheck, PyDMD, PyMDP |
| `LEGACY_HOST_BOUND` | PyKoopman, Quimb/Cotengra, multiengine DLPack/DiffEq, legacy basic packet |

`PROFILE_IMPLEMENTED_UNVERIFIED` means that the adapter no longer requires one
local path, binary hash, or exact wheel build. It does not mean a fresh machine
installed it successfully. `LEGACY_HOST_BOUND` means that host-specific policy
is still load-bearing. The fresh external-install proof count is currently
zero.

## Ceiling

A missing estate must `PARKED` or fail. It cannot be replaced by an import
check, NumPy-only calculation, or handwritten JSON claiming another engine ran.
An external profile result is not engine readiness, sim-stack readiness, CR
truth, scientific validity, release, or promotion.
