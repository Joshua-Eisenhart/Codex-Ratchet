# Sim Stack Full Target Sets

Status: current stack target map for Codex Ratchet agents.
Updated: 2026-07-09.
Authority: subordinate to `AGENTS.md`, `CODEX.md`, process docs, and the live runtime doctor.

This page answers the package-map question only. Import reachability is not
scientific integration, and scientific integration is not admission.

## Canonical Runtime

Use the runtime map first:

```text
system_v5/docs/RUNTIME_LIBRARY_LOCATION_MAP_20260608.md
```

Then verify live state:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
```

Do not install because Homebrew Python, bare `python3`, the global Julia
default project, or an archive doc cannot import a package.

## Python/JAX Canon Set

Current canonical-env verified core:

```text
jax==0.10.1
jaxlib==0.10.1
equinox==0.13.8
diffrax==0.7.2
lineax==0.1.1
optimistix==0.1.0
blackjax==1.5
jaxopt==0.8.5
optax==0.2.8
flax==0.12.7
orbax
chex==0.1.91
jaxtyping==0.3.10
dynamiqs==0.3.4
netket==3.21.0
quimb==1.14.0
cotengra==0.8.0
e3nn_jax==0.21.0
jraph==0.0.6.dev0
haiku==0.0.16
numpyro==0.21.0
ott==0.6.0
qutip
qutip_jax==0.1.1
z3
cvc5==1.3.3
sympy==1.14.0
```

Target role:

- JAX itself: vectorized finite sweeps, `jit`/`vmap`, x64 numeric work.
- Diffrax/Dynamiqs/NetKet/Quimb/Cotengra: dynamics, open quantum systems,
  many-body, and tensor-network checks.
- Equinox/Lineax/Optimistix/Optax/Jaxopt/Blackjax/Numpyro: candidate and
  counterexample generation, not proof promotion by themselves.
- Z3/CVC5/SymPy: finite structural checks and exact/symbolic sidecars.
- Jraph/E3nn-jax/OTT: graph, equivariance, and optimal-transport surfaces when
  the bounded claim needs that exact API.

Current optional JAX-adjacent imports that are available in the canonical env
but should still be matched to a bounded claim:

```text
dynamax==1.0.1
flowMC==0.6.0
qutip_jax==0.1.1
jax_dataclasses
jaxlie
jaxga
autoray==0.8.2
pymc==6.0.1
scikit-learn==1.8.0
```

Avoid or replace:

```text
bayeux  -> blackjax + optimistix
oryx    -> avoid; imports against removed JAX internals
jax-verify -> avoid/defer; imports against removed JAX internals
jax.experimental.host_callback -> current callback/debug APIs outside claim path
jax.interpreters.* internals -> public JAX APIs only
```

## Python/PyTorch Canon Set

Current canonical-env verified core:

```text
torch==2.11.0
torch_geometric==2.7.0
torchdiffeq==0.2.5
torchode==1.0.1
xitorch==0.3.0
cvxpylayers==1.2.0
geomstats==2.8.0
e3nn==0.6.0
torch_ga==0.0.6
clifford
z3
cvc5==1.3.3
sympy==1.14.0
```

Target role:

- PyTorch: autograd, `torch.func`, batched Jacobians/Hessians, tensorized
  graph/network work.
- PyG: message passing and graph machinery. Current PyG can run without
  forcing the old extension packages for ordinary local work.
- Torchdiffeq/Torchode/Xitorch/Cvxpylayers: witness/candidate generation.
- Geomstats with `GEOMSTATS_BACKEND=pytorch`, E3NN, Torch-GA, Clifford:
  geometry/equivariance/GA surfaces when load-bearing.
- Z3/CVC5/SymPy: proof/symbolic checks over torch-derived finite values.

Avoid or require pinned wheel/container receipt:

```text
dgl
torch_scatter
torch_sparse
pyg-lib
torch-cluster
torch-spline-conv
```

`torch-cluster` and `torch-spline-conv` are especially bad new foundations:
the current PyG release line deprecates or ignores them in favor of consolidated
acceleration paths. Do not let agents make them default requirements.

Missing but not required for current Ratchet claims:

```text
torchvision
torchaudio
```

`lightning==2.6.5` and `pytorch-lightning==2.6.5` are now import-visible in the
canonical environment, but they are not canon engine dependencies. They are
reached eagerly by PyKoopman's NNDMD import path, which remains quarantined and
untested.

## Python System Identification Surface

Canonical function surface:

```text
pysindy==2.1.0
```

PySINDy has a green affine continuous-generator function receipt and selected
upstream tests. Use exact `x_dot` only when the simulation genuinely exposes
the derivative; trajectory-estimation results need their own absolute error
gate. Discrete PySINDy uses `DiscreteSINDy` with `x_next=` by keyword.

Quarantined package with one admitted core function surface:

```text
pykoopman==1.2.1
  admitted: Koopman + Identity + EDMD with explicit affine bias coordinate
  blocked: Polynomial on canonical sklearn, NNDMD/neural path, full package contract
```

Do not satisfy PyKoopman's old pinned metadata by downgrading the canonical
NumPy, SciPy, scikit-learn, PyDMD, Torch, or Lightning stack. Use the pinned
Python 3.11 environment only for upstream compatibility tests.

Receipts and exact paths:

```text
system_v5/ops/PYSINDY_PYKOOPMAN_TOOL_STATUS_20260709.md
system_v4/probes/a2_state/sim_results/pysindy_capability_results.json
system_v4/probes/a2_state/sim_results/pykoopman_capability_results.json
```

## Python Graph, Topology, CS, And AI Surface

Current canonical-env verified:

```text
networkx==3.6.1
igraph==1.0.0
rustworkx==0.17.1
xgi==0.10.1
toponetx==0.4.0
gudhi==3.12.0
kanren==1.0.5
kahypar==1.3.7
opt_einsum==3.4.0
numpy==2.3.4
scipy==1.17.1
pandas==2.3.3
```

Use these before adding more graph libraries. Likely enough now:

- `networkx`: reference graph algorithms and readable fixtures.
- `rustworkx`: faster finite graph kernels.
- `igraph`: alternate performant graph algorithms.
- `xgi`: hypergraph relations.
- `TopoNetX`: cell/simplicial/combinatorial topology.
- `GUDHI`: persistent topology and simplicial complexes.
- `kanren`: small logic/relation probes.
- `kahypar`: graph/hypergraph partitioning when the bounded claim needs it.
- `opt_einsum`: contraction path support, normally behind tensor-network tools.

Optional probe candidates, not canon installs yet:

```text
hypernetx
hypergraphx
ripser
persim
pyflagser
pygsp
egglog
matchpy
distrax
pycauset
dowhy
causal_learn
pgmpy
pomegranate
```

Only add one after an install intent names the exact finite claim, API surface,
and why the existing installed graph/topology set is insufficient.

## CS Geometry Upgrade Bundle Intake

Incoming packet processed:

```text
system_v5/docs/maintenance/cs_geometry_upgrade_bundle_intake_20260609.md
```

Current engine/ladder upgrade plan:

```text
system_v5/docs/SIM_ENGINE_AND_LADDER_UPGRADE_PLAN_20260609.md
```

The accepted build pressure is:

```text
finite carrier
-> graph / hypergraph / rewrite representation
-> multiway or causal event graph
-> topology / quotient / basin readouts
-> GNN / AI only after the explicit graph object exists
```

The packet is not runtime truth, not an install order, and not a promotion
receipt. Its library catalogs are candidate menus only. Current doctor output
and this target-set page override bundle rows, especially for known avoid or
quarantine entries such as `bayeux`, DGL, `torch_scatter`, `torch_sparse`,
PythonCall, DLPack, and CondaPkg.

Good first CS/geometry micro-probes should use already verified tools before
adding new dependencies:

```text
rustworkx_dag_order
xgi_hyperedge_loss
toponetx_boundary_hodge
gudhi_tiny_filtration
pyg_message_passing_ablation
cvc5_graph_rewrite_invariant
```

Rows such as Catlab, AlgebraicRewriting, CombinatorialSpaces, egglog, PGMax,
HyperNetX, HypergraphX, ripser, persim, and pyflagser remain
`optional_probe_candidate` until an install intent proves the exact API and
bounded claim.

## Julia Strict Carrier Set

Strict carrier command:

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier
```

Current carrier direct dependency set:

```text
Attractors
ChaosTools
CliffordAlgebras
Dates
DifferentialEquations
DynamicalSystems
Graphs
Grassmann
ITensorMPS
ITensors
JSON
JSON3
LinearAlgebra
Manifolds
Octonions
QuantumClifford
QuantumOptics
QuantumToolbox
Quaternions
SHA
StaticArrays
Symbolics
Yao
Z3
```

Target role:

- Julia owns Canon: finite carriers, structure constants, order/bracket
  semantics, algebra artifacts, and Julia-side SMT checks.
- QIT stack: QuantumOptics, QuantumToolbox, QuantumClifford, Yao, ITensors,
  ITensorMPS.
- Geometry/algebra stack: CliffordAlgebras, Grassmann, Octonions, Quaternions,
  Manifolds, StaticArrays, Symbolics.
- Dynamics/basins: DifferentialEquations, DynamicalSystems, Attractors,
  ChaosTools.
- Graphs: finite graph carriers and control topology.

Quarantined or isolated by default:

```text
PythonCall
DLPack
CondaPkg
CombinatorialSpaces
Catlab
AlgebraicRewriting
TensorKit
PEPSKit
TensorOperations
ITensorNetworks
Flux
Lux
Enzyme
Zygote
IntervalArithmetic
TaylorModels
ReachabilityAnalysis
JuMP
SumOfSquares
CVC5.jl
GraphNeuralNetworks
GeometricFlux
```

These may be good tools. They are not automatically carrier tools. Put them in
isolated named projects first unless a fresh compatibility check proves they
do not downgrade or pollute the strict carrier.

Avoid by default:

```text
Basins.jl -> Attractors + DynamicalSystems
TensorFlow.jl
PyCall as claim-bearing bridge
old Jax.jl wrappers
Clipper.jl as Clifford foundation
```

## Upgrade Policy

Prefer modern, supported packages when all of these hold:

- import/API works in the actual target runtime;
- macOS ARM and Python/Julia versions are supported without source-build traps;
- the package does not require stale JAX internals or exact old Torch wheels;
- the package has a bounded role in a current Ratchet claim;
- removing or bypassing the package changes the observable, constraint,
  certificate, or falsifier.

Install nothing merely because a library is interesting. Add missing libraries
through micro-probes in this order:

1. inventory/import check in target runtime;
2. one-function API probe;
3. tool-lego fit probe;
4. coupling probe only after both tools have function receipts;
5. engine skill/agent update after the probe proves the mapping.

## Agent Rule

Agents should say `already_present` when the package is in this document and
the doctor confirms the runtime. Agents should say `optional_probe_candidate`
for missing graph/CS/AI packages unless a current task proves a bounded need.
Agents should say `blocked_or_avoid` for the avoid list and must not reinstall
those by default.
