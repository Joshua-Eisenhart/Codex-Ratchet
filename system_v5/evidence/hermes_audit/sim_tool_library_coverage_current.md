# Sim Tool Library Coverage — 2026-06-08

Status: environment/tool inventory plus current-envelope coverage. Not an install plan by itself.

## Bottom line

The machine has many useful libraries already. The current three-engine envelope estate uses only a narrow slice of them: Julia mostly `QuantumOptics`/`CliffordAlgebras`/`Z3`; JAX almost always `z3`/`cvc5` plus baseline `jax.numpy`; PyTorch almost always `torch.func`. That supports bounded scratch/proof pressure, but it is not the full sim-library stack the model wants.

Full JSON: `system_v5/evidence/hermes_audit/sim_tool_library_coverage_current.json`

## Current envelope usage

- envelopes in source-claim audit: `39`

### Source-backed package counts
- `jax:cvc5`: `39`
- `jax:z3`: `39`
- `pytorch:torch.func`: `39`
- `julia:CliffordAlgebras`: `26`
- `julia:Z3`: `26`
- `julia:QuantumOptics`: `24`
- `jax:qutip`: `4`
- `pytorch:e3nn`: `1`
- `pytorch:torch_ga`: `1`
- `pytorch:cvc5`: `1`
- `pytorch:z3`: `1`
- `jax:sympy`: `1`
- `pytorch:sympy`: `1`

## Julia default-project inventory (not strict-carrier truth)

> **Strict-carrier caveat:** this section inventories the global/default Julia project. It is useful future fuel, but it is not evidence that a package is available under the strict carrier command `JULIA_LOAD_PATH=@:@stdlib --project=system_v5/julia_carrier`. `ITensorNetworks` and `TensorOperations` require install intent, isolated-project evidence, or deliberate admission before a carrier claim may cite them.

- active project: `/Users/joshuaeisenhart/.julia/environments/v1.12/Project.toml`
- ✅ `QuantumOptics`
- ✅ `QuantumToolbox`
- ✅ `Yao`
- — `QXTools`
- — `QXZoo`
- — `QXGraphDecompositions`
- ✅ `Attractors`
- ✅ `DynamicalSystems`
- — `Basins`
- ✅ `Z3`
- — `CVC5`
- ✅ `CliffordAlgebras`
- ✅ `Grassmann`
- ✅ `Octonions`
- ✅ `Quaternions`
- ✅ `StaticArrays`
- ✅ `Manifolds`
- ✅ `CombinatorialSpaces`
- ✅ `DifferentialEquations`
- ✅ `ITensors`
- ✅ `ITensorMPS`
- ✅ `ITensorNetworks`
- ✅ `TensorOperations`
- ✅ `Symbolics`
- ✅ `Graphs`
- ✅ `PythonCall`
- ✅ `DLPack`
- — `CUDA`
- — `Reactant`
- ✅ `Enzyme`
- ✅ `Flux`
- ✅ `Lux`
- — `GraphNeuralNetworks`
- — `GraphNeuralNets`

## Python/JAX/PyTorch inventory

- Python: `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3`
- ✅ `jax` `0.10.1`
- ✅ `diffrax` `0.7.2`
- ✅ `dynamiqs` `0.3.4`
- ✅ `netket` `3.21.0`
- ✅ `qutip` `5.2.3`
- ✅ `quimb` `1.14.0`
- ✅ `cotengra` `0.8.0`
- ✅ `jaxopt`
- ✅ `lineax` `0.1.1`
- ✅ `jraph` `0.0.6.dev0`
- ✅ `ott` `0.6.0`
- ✅ `e3nn_jax` `0.21.0`
- ✅ `optax` `0.2.8`
- ✅ `equinox` `0.13.8`
- ✅ `flax` `0.12.7`
- ✅ `z3`
- ✅ `cvc5` `1.3.3`
- ✅ `sympy` `1.14.0`
- ✅ `toponetx`
- ✅ `gudhi` `3.12.0`
- ✅ `rustworkx` `0.17.1`
- ✅ `networkx` `3.6.1`
- ✅ `xgi` `0.10.1`
- ✅ `torch` `2.11.0`
- ✅ `torch_ga` `0.0.6`
- ✅ `torch_geometric` `2.7.0`
- ✅ `clifford` `1.5.1`
- ✅ `geomstats` `2.8.0`
- ✅ `e3nn` `0.6.0`
- ✅ `functorch` `2.11.0`
- ✅ `numpy` `2.3.4`
- ✅ `scipy` `1.17.1`
- ✅ `mpmath` `1.3.0`

## Use as future sim fuel

- QIT/open-systems: Julia `QuantumOptics`, `ITensors`; JAX `dynamiqs`, `qutip`, `quimb`, `netket`.
- Attractors/dynamics: Julia `Attractors`, `DynamicalSystems`, `DifferentialEquations`; JAX `diffrax` with `vmap`/`jit` for basin maps.
- Proof pressure: Julia `Z3`; Python `z3`, `cvc5`, `sympy`; keep solver variables bound to computed finite objects.
- Spinor/noncomm/nonassoc: use Julia `CliffordAlgebras`, `Grassmann`, `Octonions`, `Quaternions`, and `Manifolds` when present; `StaticArrays` and `CombinatorialSpaces` are useful candidates but must be import-verified before use.
- Cross-engine bridge: PythonCall/DLPack/CUDA/Reactant/Enzyme are not in the default Julia project right now; treat interop as future setup, not current evidence.

