# Sim Engine And Ladder Upgrade Plan

Status: current upgrade plan, reconciled from Hermes proposal and Codex
adjudication.
Date: 2026-06-09.
Authority: subordinate to `AGENTS.md`, `CODEX.md`, process docs, live runtime
doctor, and the current runtime map.

This plan is about what to install, what not to install, and how to upgrade the
sim engines and sim ladder without turning package availability into a
scientific claim.

## Controlling Rule

Install now:

```text
nothing
```

The current stack is already broad enough for the next useful work. The first
upgrade is ladder/receipt/packet discipline, not dependency expansion.

Every later install requires an install intent naming:

- exact package;
- target manager and target environment;
- bounded finite claim;
- missing API/function that the current installed stack cannot provide;
- read-only preflight proving the package is missing from the correct target;
- isolated-project plan when the package is risky;
- controller/user approval before `install_allowed=true`.

Import success is still only `canonical_env_verified` or `installed_only`.
Claim integration starts at a function-level receipt and becomes
`claim_load_bearing` only when removing or bypassing the tool changes,
constrains, certifies, or falsifies the bounded claim.

Tool-function receipts may be authored before final M(C), but they stay in
tool-stage language:

```text
classification=scratch_diagnostic with evidence_level=tool_capability
or classification=tool_lego_fit_probe where the validator permits it
```

Before full M(C), a tool receipt must not claim system fit, same-carrier
geometry, topology readout, AI/GNN readout, engine admission, bridge, Axis, or
physics. Any packet that uses those stronger phrases must point to the explicit
M(C) fields it depends on or remain `scratch_diagnostic` with downstream
consumers blocked.

## Runtime Anchors

Use these paths for all worker prompts and receipts:

```text
active_repo: /Users/joshuaeisenhart/Codex-Ratchet
python: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
python_physical_env: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main
julia: /opt/homebrew/bin/julia
julia_carrier_project: /Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier
julia_load_path: @:@stdlib
```

Run before package-sensitive work:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/audit_runtime_mapping_references.py
```

## Use Now

Use already verified packages before adding anything.

Python/JAX:

```text
jax, diffrax, dynamiqs, netket, quimb, cotengra, autoray,
equinox, lineax, optimistix, optax, jaxopt, blackjax,
flax, orbax, haiku, numpyro, qutip, qutip_jax,
jraph, e3nn_jax, ott, z3, cvc5, sympy
```

Python/PyTorch:

```text
torch, torch_geometric, torchdiffeq, torchode, xitorch,
cvxpylayers, geomstats, e3nn, torch_ga, clifford, z3, cvc5, sympy
```

Python graph/topology/CS:

```text
networkx, igraph, rustworkx, xgi, TopoNetX, GUDHI,
kanren, kahypar, opt_einsum
```

Julia strict carrier:

```text
CliffordAlgebras, Grassmann, Quaternions, Octonions, Graphs,
ITensors, ITensorMPS, QuantumClifford, QuantumOptics, QuantumToolbox,
Yao, Manifolds, DifferentialEquations, DynamicalSystems, Attractors,
ChaosTools, Symbolics, Z3
```

## Avoid Or Quarantine

Do not let agents install these as ordinary upgrades:

```text
dgl
torch_scatter
torch_sparse
pyg-lib
torch-cluster
torch-spline-conv
bayeux
oryx
jax-verify
Basins.jl
TensorFlow.jl
old Jax.jl wrappers
PyCall.jl as claim-bearing bridge
PythonCall, DLPack, CondaPkg inside the strict Julia carrier
```

Use `Attractors.jl` plus `DynamicalSystems.jl` instead of `Basins.jl`.
Use `blackjax` plus `optimistix` instead of `bayeux`.
Use modern PyG native paths instead of forcing old extension wheels.

DLPack is not globally banned. It is excluded from the strict Julia carrier by
default. Cross-runtime exchange should prefer hash-verified Canon artifacts,
JSON receipts, or versioned binary receipts first. DLPack becomes admissible
only inside a scoped bridge/exchange micro-probe that records producer runtime,
consumer runtime, package versions, tensor shape/dtype/device, artifact hashes,
and an explicit no-hidden-host-copy check.

## Optional Install Queues

These are candidate queues, not permission to install.

### Python Rewrite And Equality Saturation

First candidates:

```text
egglog
matchpy
```

Use only if `z3`/`cvc5` plus current graph tools cannot cleanly express a
bounded quotient/rewrite claim.

### Python Hypergraph And Topology Extensions

Candidates:

```text
hypernetx
hypergraphx
ripser
persim
pyflagser
pygsp
```

Use only if `xgi`, `TopoNetX`, and `GUDHI` are insufficient for a named
incidence, filtration, or directed-complex API.

### Python Probabilistic Graph And Causal AI

Candidates:

```text
pgmpy
pomegranate
causal-learn
dowhy
PGMax
distrax
```

Use only after the finite graph/hypergraph/cell object exists and the bounded
claim is evaluator reliability, factor-graph belief propagation, causal
readout, or probabilistic control.

### Later World And Embodied Dynamics

Candidates:

```text
JAX-MD
Brax
MJX
```

Use only after explicit `M(C)`, graph/event object, and topology/readout layers
exist. These are not current foundations.

### Julia Optional Isolated Projects

Do not add these directly to the strict carrier first:

```text
Catlab.jl
AlgebraicRewriting.jl
CombinatorialSpaces.jl
MetaGraphsNext.jl
TensorKit.jl
PEPSKit.jl
TensorOperations.jl
ITensorNetworks.jl
CVC5.jl
IntervalArithmetic.jl
TaylorModels.jl
ReachabilityAnalysis.jl
JuMP.jl
SumOfSquares.jl
Lux.jl
Zygote.jl
Enzyme.jl
```

Use named isolated Julia projects by package family. A package can migrate
toward the strict carrier only after an isolated micro-probe proves import/API
compatibility, no core downgrade, and a claim-bearing role.

## Engine Upgrade Plan

### Julia Canon

Julia stays semantic owner for:

- finite carriers;
- algebra tables and structure constants;
- bracket/order policy;
- graph object semantics when admitted;
- proof tags and source/artifact hashes;
- carrier/QIT/algebra sidecars.

Upgrade actions:

1. Keep the strict carrier clean.
2. Record Canon artifact fields in every consumer:
   `artifact_path`, `artifact_sha256`, `source_sha256`, `proof_tag`,
   `proof_pass`, `table_version`, `bracket_convention`.
3. Create optional isolated projects only after an install intent.
4. Never treat global Julia visibility as carrier truth.

### JAX Workhorse

JAX owns scale, dynamics, and counterexample search after the finite object is
fixed by Canon or by the current finite packet.

Required habits:

- set `jax_enable_x64=True` before float64 claims;
- avoid JAX internals and removed APIs;
- use public JAX/Jraph/E3NN-JAX/OTT/Diffrax/Dynamiqs APIs;
- consume Julia Canon artifacts by hash;
- do not use optimizer convergence as proof.

### PyTorch Graph And Autograd

PyTorch is the graph/autograd/helper layer. It is claim-bearing only when its
removal changes the observable or falsifier.

Use:

- `torch.func` for Jacobians/Hessians;
- PyG for graph message passing and ablation;
- `geomstats` with torch backend when relevant;
- `e3nn`, `torch_ga`, `clifford` for equivariance/GA geometry;
- proof sidecars over torch-derived finite values.

Do not create decorative `torch_*` fields or no-op PyTorch paths to satisfy old
all-engine gates.

### Proof And CS Sidecars

`z3`, `cvc5`, and `sympy` are sidecars for finite structure, symbolic identity,
and exact checks. Solver use is genuine only when the solver derives the
contradiction, invariant, or witness from encoded finite structure instead of
re-checking a precomputed scalar or a free Boolean contradiction.

## Sim Ladder

The current ladder should be read as a dependency order, not a proof that later
layers are admitted.

```text
0. Runtime / receipt hygiene
1. F01 and N01 root constraints
2. Explicit finite M(C)
3. Canon carrier artifact + bracket/order runtime
4. CS finite-object layer
   - graph
   - hypergraph
   - rewrite / e-graph
   - event / multiway / causal graph
   - cell / simplicial / chain-complex object
5. Same-carrier geometry micro-legos
   - spinor / Clifford
   - Hopf / S3 -> S2
   - Weyl / chirality
   - path / holonomy / associator
   - octonion / G2 / Fano / Spin(7) tower as scratch until admitted
6. Topology / quotient / basin readouts
   - persistence
   - Hodge / boundary operators
   - quotient maps
   - update / basin / invariant / escape controls
7. AI / GNN evaluator layer
   - message passing
   - learned scorer
   - counterexample search
   - reliability evaluator
   - never proof by itself
8. QIT / terrain / operator / engine grammar as scoped finite work
9. Cross-model readout matrix
10. Bridge / Axis / physics-facing claims, embargoed until dependencies exist
```

QIT tools can appear earlier when they are carrying a finite carrier/readout
claim. QIT-engine-as-basin or physics-facing QIT-engine language remains later
and requires its own admission receipts.

## Wave A: No-Install Micro-Probes

Wave A uses only already verified tools. Each probe is `scratch_diagnostic` or
`tool_lego_fit_probe` unless a later gate explicitly admits more. Pure
tool-function receipts before full M(C) should use `scratch_diagnostic` with
`evidence_level=tool_capability`; useful lego-shaped tool probes may use
`tool_lego_fit_probe` when the validator accepts that category. Neither status
admits system fit.

### A1. `rustworkx_dag_order`

Tool/API surface: `rustworkx.PyDiGraph`, topological sort / cycle handling.

Claim:

```text
finite dependency/order structure can encode local event dependency without
smuggling a total order.
```

Controls:

- cycle insertion fails or changes verdict;
- same endpoints with different path order do not collapse;
- order reversal changes the observable.

### A2. `xgi_hyperedge_loss`

Tool/API surface: `xgi.Hypergraph`, incidence and hyperedge projection.

Claim:

```text
a 3-way relation carries information not preserved by pairwise projection.
```

Controls:

- pairwise projection erases the target relation;
- full hypergraph preserves it;
- degenerate hyperedge reduces to pairwise baseline.

### A3. `toponetx_boundary_hodge`

Tool/API surface: `TopoNetX` cell/simplicial complex boundary/incidence.

Claim:

```text
boundary/incidence/Hodge-like local structure is a finite object, not scalar
adjacency.
```

Controls:

- broken orientation changes boundary result;
- scalar adjacency cannot reproduce the boundary operator;
- empty or degenerate complex is blocked or demoted.

### A4. `gudhi_tiny_filtration`

Tool/API surface: `GUDHI` simplex tree / filtration / Betti or barcode output.

Claim:

```text
finite filtration emits an explicit topology readout for a tiny carrier.
```

Controls:

- scrambled filtration changes barcode or Betti readout;
- metric-free baseline cannot claim the same topology;
- degenerate filtration is demoted.

### A5. `cvc5_graph_rewrite_invariant`

Tool/API surface: Python `cvc5` finite relation encoding, with `z3` optional
cross-check.

Claim:

```text
a graph/rewrite side condition is SAT/UNSAT because of bound finite relations,
not because of a decorative Boolean contradiction.
```

Controls:

- remove side condition;
- reverse rewrite;
- quotient-erasure control;
- solver must derive from encoded structure.

### A6. `pyg_message_passing_ablation`

Tool/API surface: `torch_geometric.data.Data`, one message-passing layer or
explicit PyG propagation function.

Claim:

```text
message passing changes a bounded graph observable after the graph object
exists.
```

Controls:

- node-feature shuffle;
- edge removal;
- static scalar baseline;
- if the static baseline gives the same verdict, PyG is decorative.

## M(C) Gap Before Promotion

Wave A may run before final M(C) completion only as tool-stage or
scratch-diagnostic work. Tool-function receipts before full M(C) are
`tool_capability` evidence only; tool-lego fit packets are pre-admission fit
evidence only. Promotion remains blocked until M(C) fields are
explicit:

- finite carrier set or tensor anchor;
- admissible state family;
- probe/readout family;
- operation/control family;
- equivalence or quotient relation;
- positive witnesses;
- negative and erased controls;
- boundary/invariant/escape controls;
- blocked downstream consumers;
- receipt schema and validator.

Any packet claiming system fit, same-carrier geometry, topology readout, or
AI/GNN readout must cite the explicit M(C) fields it uses. If those fields are
missing or partial, the packet remains scratch and blocks downstream consumers.

## Receipt Upgrade

New CS/AI sims should emit at least:

```json
{
  "object_id": "...",
  "ladder_layer": "cs_graph|hypergraph|rewrite|topology|ai_gnn",
  "classification": "scratch_diagnostic",
  "evidence_level": "tool_capability|tool_lego_fit",
  "promotion_allowed": false,
  "formal_admission_allowed": false,
  "finite_object": {
    "carrier_ref": "...",
    "graph_ref": "...",
    "hypergraph_ref": "...",
    "cell_complex_ref": "..."
  },
  "tool_claim": {
    "tool": "...",
    "api_surface": "...",
    "observable": "...",
    "positive": "...",
    "negative": "...",
    "boundary": "...",
    "demotion_condition": "..."
  },
  "engine_contract": {
    "julia": "ran|blocked|not_scoped",
    "jax": "ran|blocked|not_scoped",
    "pytorch": "ran|blocked|not_scoped"
  },
  "exchange_contract": {
    "mode": "hash_verified_json|versioned_binary_receipt|dlpack_micro_probe|not_applicable",
    "producer_runtime": "...",
    "consumer_runtime": "...",
    "artifact_sha256": "...",
    "no_hidden_host_copy": true
  },
  "claim_ceiling": "tool-stage or scratch only"
}
```

When consuming Canon, also emit the `canon_runtime` and
`foreign_runtime_manifest` fields from
`system_v5/docs/JULIA_CANON_RUNTIME_CONTRACT.md`.

Default cross-runtime exchange is hash-verified artifact exchange. DLPack is an
exchange micro-probe route, not a carrier dependency.

## Practical Build Order

1. Freeze this plan and keep install decision at `nothing`.
2. Harden the explicit M(C) gap table.
3. Build Wave A no-install micro-probes.
4. Add the first AI/GNN probe only after a graph/hypergraph/cell object exists.
5. Author install intents only for gaps Wave A exposes.
6. Run isolated optional-project probes before strict-carrier or core-env
   adoption.
7. Patch skills/agents only after a function-level receipt proves the mapping.
8. Keep bridge, Axis, flux, basin, and physics-facing work embargoed until
   dependency receipts exist.

## Messages For Other Surfaces

Use this short packet for Hermes, Claude, and Codex TUI:

```text
Adopt system_v5/docs/SIM_ENGINE_AND_LADDER_UPGRADE_PLAN_20260609.md.
Install now: nothing. Use current sim-stack and strict Julia carrier.
First work is Wave A no-install micro-probes:
rustworkx_dag_order, xgi_hyperedge_loss, toponetx_boundary_hodge,
gudhi_tiny_filtration, cvc5_graph_rewrite_invariant,
pyg_message_passing_ablation.
AI/GNN is downstream of explicit graph/hypergraph/cell object. Optional
packages require install-intent and one-function probe. Do not install DGL,
torch_scatter, torch_sparse, bayeux, Basins.jl, PyCall, PythonCall, DLPack,
CondaPkg in strict carrier, or old JAX internals. Use hash-verified artifacts
first; DLPack only inside a scoped bridge/exchange micro-probe. No promotion
from this plan.
```
