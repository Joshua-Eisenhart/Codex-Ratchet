# Nonclassical Tool Integration Audit - 2026-05-14

Status: working audit for clean v5 legos and formal scouts. Noncanonical.

## Current Tool Levels

| Tool | Current level | Evidence surface | Next deeper integration |
|---|---|---|---|
| PyTorch | load-bearing | density matrices, CPTP channels, MPS/tensor states, spectra, entropy, autograd-ready tensors | make gradient-bearing coherent-information and channel-order scouts standard |
| opt_einsum | load-bearing | partial traces, MPS contractions, bipartite cut readouts | use named contraction recipes for every cut/factorization |
| SymPy | load-bearing | exact entropy boundaries, Kraus completeness, symbolic identities | pair every numeric entropy lego with one exact small-state boundary |
| z3 | load-bearing | trace/sign/type impossibility, non-collapse constraints | add SAT/UNSAT guards for each admission/coercion and signed-entropy claim |
| clifford | load-bearing | chirality/projector and Pauli/Clifford representation gaps | connect chirality projectors directly to density-block entropy and allowed transitions |
| geomstats | load-bearing/supportive mixed | Hopf projection and geometry backend checks | move from distance checks to explicit manifold/geodesic constraints where APIs support it |
| GUDHI | load-bearing | simplicial homology and persistent entropy witnesses | use filtrations generated from state/cut data, not hand-set filtrations only |
| TopoNetX | load-bearing | joint-admission complexes and finite cell/simplicial witnesses | encode layer-transition complexes, not only result summaries |
| XGI | load-bearing | hyperedge entropy/topology witnesses | use hyperedges for multi-cut correlation and triple information legos |
| rustworkx | load-bearing | admission-flow and transition graphs | make admissibility ratchets explicit directed graphs with killed edges |
| PyG | load-bearing/support witness | support graph and edge-index conversion | use message passing as a real constraint propagator over layer graphs |
| QuTiP | supportive when installed | entropy cross-checks and quantum object sanity checks | add channel evolution cross-checks for small density/channel legos |
| networkx | supportive/load-bearing bridge | graph construction for PyG/GUDHI/XGI | keep as graph interchange, not the final proof surface |

## Integration Rule

Do not claim "full stack" because a tool imported. A tool is load-bearing only
when a positive, graveyard, or boundary predicate would fail without that tool's
function/API surface.

## Immediate Integration Work

1. Add signed entropy legos:
   - conditional entropy can be negative on entangled bipartite states.
   - coherent information separates entangled, classical-correlated, and product controls.
   - coherent-information gradients are computable with PyTorch autograd.
2. Add layer-coupling scouts:
   - type admission matrix: which readouts accept each geometry output.
   - ordered transition matrix: which readouts become meaningful only after coupling/bipartition.
   - signed readout depth: where conditional/coherent information first appears.
3. Audit:
   - all results remain `promotion_allowed:false` unless promoted later.
   - no target-system labels in executable names.
   - every scout has nearby graveyards and a claim ceiling.
