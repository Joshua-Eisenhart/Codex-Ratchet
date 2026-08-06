# Proposed Simulation Capability Estate

This is a candidate decomposition, not a canonical ordering. The layers are
deployment and evidence boundaries. They are not the manifold itself.

## Layer table

| Estate layer | Purpose | Required candidate capabilities | Optional rivals or reproductions |
|---|---|---|---|
| `E0 constraint-core` | cheap bounded checking and small manifold-floor fixtures | Python core, NumPy, SciPy, Z3 | cvc5, TLA+/TLC |
| `E1 manifold-local` | density, channel, history-pair, ODE and tensor-network work | JAX x64, Diffrax, quimb, cotengra | no heavy rival is loaded by this profile |
| `E2 science-fields` | candidate laws, rates, finite active inference and field models | PySINDy, PyDMD, `inferactively-pymdp` | no Python-3.11 satellite is loaded by this profile |
| `E3 cloud-accelerated` | large fixed-shape search, contraction and hybrid graph campaigns | NVIDIA telemetry plus **either** JAX CUDA or PyTorch CUDA | the unused GPU route is not required |

Candidate extensions are kept outside the active profile until they earn a
fixture: Julia/QuantumOptics, PyTorch-local, PyKoopman, Attractors.jl,
cuQuantum, Reactant.jl and multi-GPU orchestration. Naming one here does not
make it installed, integrated or required.

## Why this is better than one environment

- ConstraintBox can boot and veto cheaply without loading JAX, Julia or Torch.
- The manifold workhorse can be installed without the science-field proposal
  libraries.
- A future PyKoopman profile can remain in a Python 3.11 satellite instead of
  constraining the active E2 environment.
- GPU packages do not contaminate local CPU locks.
- Each heavy runtime follows tombstone-and-boot: read a bound artifact, run,
  write evidence, exit, and release memory.

## Readiness meanings

| State | Meaning |
|---|---|
| `READY` | exact tested lock, source digest, positive fixture, negative fixture, severance and deterministic replay passed |
| `DEGRADED` | all required capabilities passed; one or more optional capabilities did not |
| `UNAVAILABLE` | a required dependency or hardware target is absent |
| `DRIFT` | installed version, worker source, fixture or lock differs from the tested contract |
| `FAILED` | installed capability ran but a witness or control failed |
| `UNTESTED` | named or installed but no acceptance evidence exists |

An import is never `READY`.

## Non-flattening rule

A capability is bound to named finite observables. It does not acquire authority
over every lower or higher layer merely because it can represent their arrays.
PySINDy may propose a law over a declared trajectory; it cannot determine the
carrier, choose its own feature library, or validate the law. A tensor
contraction may compute one declared factor graph; it cannot establish that the
manifold factorizes.
