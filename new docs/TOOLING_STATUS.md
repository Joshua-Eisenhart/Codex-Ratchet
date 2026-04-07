# Tooling Status

Date: 2026-04-07
Supersedes: all prior tooling status docs

---

## Canonical Interpreter

`/opt/homebrew/bin/python3` — all live skills and probes must use this.

---

## Tool Status

### GREEN — Installed, imported, verified working

| Tool | Version | Role | Current usage |
|---|---|---|---|
| numpy | (system) | Numeric backbone, classical baselines | everywhere — baseline substrate |
| torch | 2.8.0 | Core computation substrate (target) | 8+ sim files, growing |
| torch_geometric (PyG) | 2.7.0 | Graph dynamics, message passing | 7+ sim files |
| z3-solver | 4.16.0 | SMT constraint proofs (UNSAT) | 29+ sim files |
| cvc5 | 1.3.3 | SMT cross-check, SyGuS synthesis | **NEW** — installed, not yet used in sims |
| sympy | 1.14.0 | Symbolic algebra, formula derivation | 15+ sim files |
| clifford | 1.5.1 | Geometric algebra Cl(3)/Cl(6) | 62+ sim files (mentions) |
| TopoNetX | 0.4.0 | Cell-complex topology | 11+ sim files |
| GUDHI | 3.12.0 | Persistent homology, TDA, simplicial/cubical/Rips | **was installed, now canonical** — not yet used in sims |
| geomstats | 2.8.0 | Manifold geometry, Riemannian statistics | **NEW** — installed, not yet used in sims |
| e3nn | 0.6.0 | E(3)-equivariant neural networks | **NEW** — installed, not yet used in sims |
| networkx | (system) | Graph construction, owner graph | v4_graph_builder, probes |
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
| quimb | Tensor networks — not needed until Phase 6+ |
| qutip | Quantum toolbox — overlaps with hand-built legos; add if needed |
| ripser | Superseded by GUDHI for persistent homology |
| pySMT | z3 + cvc5 direct is cleaner than pySMT abstraction layer |

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
├── GUDHI       — persistent homology, simplicial/cubical/Rips/alpha complexes
└── e3nn        — O(3)/E(3)-equivariant computation on PyTorch

TOPOLOGY LAYER
├── TopoNetX    — cell complexes, higher-order structure
└── GUDHI       — (also here) filtrations, persistence diagrams

COMPUTATION LAYER
├── torch       — core differentiable substrate, autograd
├── PyG         — graph neural networks, message passing
└── numpy       — baseline comparison only

SYMBOLIC LAYER
└── sympy       — algebra, derivation, symbolic verification
```

All layers are simultaneous constraint shells, not a sequential pipeline.
Every canonical sim must document which tools from each layer were tried.

---

## Tool-Role Contract (expanded)

| Tool | Must do | Must NOT be reduced to |
|---|---|---|
| z3 | UNSAT impossibility proofs for structural claims | post-hoc SAT confirmation |
| cvc5 | Cross-check z3 UNSAT claims; SyGuS synthesis for minimal generators | redundant z3 clone |
| sympy | Derive formulas symbolically before numerics | verify-only layer |
| clifford | Native geometric product computation in Cl(3)/Cl(6) | roundtrip unit test |
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
