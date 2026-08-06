# Cloud GPU Acceptance

E3 is an acceleration profile, not a separate source of scientific authority.
It has two alternative routes:

```text
NVIDIA telemetry + JAX CUDA
                 or
NVIDIA telemetry + PyTorch CUDA
```

Requiring both frameworks for every job would waste disk, boot time and GPU
memory. The task contract chooses a route before dispatch. The unused route
does not load.

The two direct candidate inputs are separate:

- `requirements/candidates/e3-jax-cuda.in`
- `requirements/candidates/e3-torch-cuda.in`

## Required cloud evidence

| Evidence | Requirement |
|---|---|
| container | immutable image digest and candidate lock |
| device | GPU UUID, model, memory and driver from `nvidia-smi` |
| framework | exact version, CUDA runtime and actual GPU placement |
| native graph | StableHLO for JAX, or an explicit Torch dispatch trace |
| input | byte-identical local golden-fixture hash |
| output | declared finite observables, no producer verdict |
| parity | compare against E0/E1 CPU receipt under a predeclared tolerance |
| cost | elapsed time and monetary ceiling |
| negative | force CPU while claiming GPU; E3 must fail |

## Local result in this pack

The packaging host had no `nvidia-smi`, no CUDA JAX device and no Torch
installation in the selected environment. E3 returned `FAILED` and
`--enforce` exited nonzero. This is the required result; the pack does not
convert missing cloud hardware into a pass.

cuQuantum, Reactant.jl and multi-GPU orchestration remain candidate extensions,
not active E3 dependencies.
