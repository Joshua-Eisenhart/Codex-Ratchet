# Tooling Status

Date: 2026-04-08
Supersedes: all prior tooling status docs

---

## Canonical Interpreter

`/opt/homebrew/bin/python3` — all live skills and probes must use this.

---

## Current Truth

- The stack is broader and more active than the older docs implied.
- The repo-level proof/graph/geometry tool surface is now real, but uneven.
- The current bridge / `Phi0` seam is still mostly numpy-first and underintegrated with the proof/graph stack.
- The basic foundations-first plan is still only partially complete:
  - foundational legos are now much better covered
  - bridge / cut-state / `Phi0` separation is now real
  - deep graph/proof integration into that seam is still behind

### 2026-04-08 controller spot audit

This is the current quick scan over `425` sim-like probe files in `system_v4/probes/`
(files beginning with `sim_`, `axis0_`, or `validate_`):

| Tool | Detected in sim-like files | Read |
|---|---:|---|
| torch | 134 | heavily present |
| sympy | 102 | heavily present |
| z3 | 100 | heavily present |
| clifford | 82 | strong geometry usage |
| rustworkx | 64 | present, but often in broad all-tools sims |
| geomstats | 59 | present, but seam usage still shallow |
| gudhi | 59 | present, but seam usage still shallow |
| e3nn | 55 | present, but seam usage still shallow |
| XGI | 55 | present, but seam usage still shallow |
| torch_geometric (PyG) | 55 | present, but seam usage still shallow |
| cvc5 | 54 | present, but still underused as a true proving engine |
| TopoNetX | 3 | clear underused outlier |

Interpretation:
- most tools are now present in real sim files
- not all of that presence is deep usage
- `TopoNetX` is still the clearest underused graph/topology tool
- the bridge / `Phi0` seam is still not where the stack is being used most deeply

---

## Tool Status

### GREEN — Installed, imported, verified working

| Tool | Version | Role | Current usage |
|---|---|---|---|
| numpy | (system) | Numeric backbone, classical baselines | everywhere — baseline substrate |
| torch | 2.8.0 | Core computation substrate (target) | 134 sim-like files detected |
| torch_geometric (PyG) | 2.7.0 | Graph dynamics, message passing | 55 sim-like files detected |
| z3-solver | 4.16.0 | SMT constraint proofs (UNSAT) | 100 sim-like files detected |
| cvc5 | 1.3.3 | SMT cross-check, SyGuS synthesis | 54 sim-like files detected |
| sympy | 1.14.0 | Symbolic algebra, formula derivation | 102 sim-like files detected |
| clifford | 1.5.1 | Geometric algebra Cl(3)/Cl(6) | 82 sim-like files detected |
| TopoNetX | 0.4.0 | Cell-complex topology | 3 sim-like files detected; underused |
| GUDHI | 3.12.0 | Persistent homology, TDA, simplicial/cubical/Rips | 59 sim-like files detected |
| geomstats | 2.8.0 | Manifold geometry, Riemannian statistics | 59 sim-like files detected |
| e3nn | 0.6.0 | E(3)-equivariant neural networks | 55 sim-like files detected |
| rustworkx | 0.17.1 | Fast graph kernels, DAGs, routing, dependency graphs | 64 sim-like files detected |
| XGI | 0.10.1 | Hypergraphs, simplicial complexes, higher-order interactions | 55 sim-like files detected |
| networkx | (system) | Graph construction, owner graph | v4_graph_builder, probes — to be superseded by rustworkx for perf-critical paths |
| pydantic | (system) | Typed schemas | schema validation |
| pytest | (system) | Test gates | test suites |
| hypothesis | (system) | Property-based testing | test suites |

### PLANNED — Not yet installed

| Tool | Role | Blocker |
|---|---|---|
| Lean 4 | Interactive theorem prover (math formalization) | Separate toolchain install (elan/lake), not pip |
| TLAPS (TLA+ Proof System) | Temporal logic model checking (system properties) | Separate install, targets safety/liveness of ratchet spec |

### REMOVED from consideration (for now)

| Tool | Reason |
|---|---|
| DGL | Redundant with PyG unless PyG becomes a blocker |
| quimb | Tensor networks — not needed until Phase 6+ |
| qutip | Quantum toolbox — overlaps with hand-built legos; add if needed |
| ripser | Superseded by GUDHI for persistent homology |
| pySMT | z3 + cvc5 direct is cleaner than pySMT abstraction layer |
| HyperNetX | XGI covers the hypergraph need; add only if richer hypergraph analytics needed |

---

## Stack Architecture

```
PROOF LAYER
├── z3          — UNSAT impossibility, constraint logic
├── cvc5        — cross-check, SyGuS synthesis, admissible-operator search
├── (Lean 4)    — [planned] math formalization above SMT
└── (TLAPS)     — [planned] ratchet state-machine safety/liveness

GEOMETRY LAYER
├── clifford    — Cl(3)/Cl(6) geometric algebra
├── geomstats   — Riemannian manifolds, geodesics, curvature, Fréchet mean
└── e3nn        — O(3)/E(3)-equivariant computation on PyTorch

GRAPH LAYER
├── rustworkx   — fast graph kernels, DAGs, routing, dependency, causal-order
├── PyG         — differentiable graph computation, message passing
└── XGI         — hypergraphs, simplicial complexes, higher-order interactions

TOPOLOGY LAYER
├── TopoNetX    — cell complexes, higher-order structure
├── GUDHI       — persistent homology, simplicial/cubical/Rips/alpha filtrations
└── XGI         — (also here) simplicial complex construction

COMPUTATION LAYER
├── torch       — core differentiable substrate, autograd
├── numpy       — baseline comparison only
└── rustworkx   — (also here) performance-critical graph algorithms

SYMBOLIC LAYER
└── sympy       — algebra, derivation, symbolic verification
```

All layers are simultaneous constraint shells, not a sequential pipeline.
Every canonical sim must document which tools from each layer were tried.
That said, the current failure mode is no longer "tool missing." It is
"tool declared or imported, but not load-bearing in the actual seam under study."

---

## Current Integration Gaps

### Gap 1 — Bridge / `Phi0` seam is underusing proof tools

The current bridge / `Phi0` work is now much more disciplined than before,
but it is still mostly:
- numpy-first
- manifest-rich
- proof-light

What is still missing there:
- real `z3` / `cvc5` disqualification and impossibility claims
- not just post-hoc numeric separation

### Gap 2 — Graph / topology tools are not yet central to the seam

The seam is still weak on:
- graph-structured packet / family reasoning
- hypergraph treatment of multi-way packet relations
- topology/cell-complex reasoning on shell families

Right now:
- `rustworkx`, `XGI`, `PyG`, `GUDHI`, `geomstats`, `e3nn` are present
- `TopoNetX` is still barely used
- recent seam sims do not yet make graph/topology tools load-bearing

### Gap 3 — The basic plan is still only partially executed

The actual plan should be:
1. foundations as independent legos
2. bridge families as independent legos
3. `rho_AB` construction as its own object family
4. cut kernels as their own family
5. graph/proof integration on that seam
6. only then promotion pressure

The repo is now much closer to that than before, but step 5 is still behind.

---

## Tool-Role Contract (expanded)

| Tool | Must do | Must NOT be reduced to |
|---|---|---|
| z3 | UNSAT impossibility proofs for structural claims | post-hoc SAT confirmation |
| cvc5 | Cross-check z3 UNSAT claims; SyGuS synthesis for minimal generators | redundant z3 clone |
| sympy | Derive formulas symbolically before numerics | verify-only layer |
| clifford | Native geometric product computation in Cl(3)/Cl(6) | roundtrip unit test |
| rustworkx | Fast graph algorithms, DAG ordering, dependency/routing/causal workloads | NetworkX drop-in replacement without using its speed |
| XGI | Hypergraph and simplicial complex construction for multi-way interactions | pairwise graph with extra labels |
| TopoNetX | Cell-complex topology, higher-order structure | Betti-number-only checker |
| GUDHI | Persistent homology, filtrations, topological data analysis at scale | unused import |
| geomstats | Riemannian metrics, geodesics, Fréchet means on shell manifolds | numpy wrapper for manifold labels |
| e3nn | E(3)-equivariant layers for symmetry-native PyTorch computation | decorative equivariance claim |
| torch | Tensors, gradients, autograd as core substrate | numpy replacement with same API |
| PyG | Message passing as computation, graph-native dynamics | graph inspection/visualization only |

---

## Heartbeat

Heartbeat launchd agent UNLOADED as of 2026-04-04.
macOS TCC blocks `/bin/bash` from accessing `~/Desktop` via launchd.
Re-enable requires Full Disk Access for bash or moving repo out of Desktop.
