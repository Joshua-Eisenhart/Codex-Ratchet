# QIT Concept → Graph Layer Mapping

Canonical owner/sidecar stack:

```
Owner truth:           Pydantic → JSON → NetworkX → GraphML (export)
Understanding/memory:  LightRAG
Nonclassical topology: TopoNetX
Nonclassical algebra:  clifford
Tensor/learning:       PyG
Optional GA-torch:     kingdon
```

---

## Axis 0 (Identity / Entropy Gradient)

| Layer | What It Holds | Status |
|---|---|---|
| **NetworkX (owner)** | `AXIS::axis_0` node, `AXIS_GOVERNS` edges to both ENGINE nodes | **Live.** Owner graph stores the proven existence and dependency edges. |
| **clifford (next carrier)** | The `AXIS_GOVERNS` edge payload encodes the entropy gradient as a grade-1 multivector `[0, 0.4, 0.4, 0.4]` in Cl(3,0) | **Bounded read-only sidecar.** Captures gradient direction, which a flat edge label can't express. Not yet governing. |
| **TopoNetX** | Not primary. Axis 0 is a 0-cell (node), not a higher-order structure. | — |
| **LightRAG** | Retrievable context: "Axis 0 is the identity/entropy axis. Proven load-bearing by `sim_neg_axis0_frozen.py`." | **Not yet integrated.** |

## Hopf Torus (inner / Clifford / outer)

| Layer | What It Holds | Status |
|---|---|---|
| **NetworkX (owner)** | `TORUS::inner`, `TORUS::clifford`, `TORUS::outer` nodes + `TORUS_NESTING` edges (inner→Clifford→outer) + `STAGE_ON_TORUS` edges linking macro-stages to their torus | **Live.** Discrete structural facts. |
| **TopoNetX (next carrier)** | Each torus becomes a 2-cell in the CellComplex. The nesting becomes a filtration of cell complexes. The boundary operator ∂₂ captures fiber/base loop boundary structure. | **Correct next semantic carrier.** Currently a bounded read-only projection. Tori are 2-manifolds — only cell complexes represent them properly. |
| **clifford (next carrier)** | `TORUS_NESTING` edge payloads encode nesting as a grade-2 bivector `[0, 0, 0, 0, 0, 1.0, 0, 0]` (e₁∧e₃ plane) | **Bounded read-only sidecar.** Captures that inner→outer ≠ outer→inner. |
| **PyG (next carrier)** | Tensor features on torus nodes: `[nesting_rank, curvature, radius_ratio]` | **Bounded read-only sidecar.** For future learned embeddings. |
| **LightRAG** | Retrievable context about the Hopf fibration S³→S² and what each torus surface means physically. | **Not yet integrated.** |

## Weyl Chirality (Type 1 Deductive / Type 2 Inductive)

| Layer | What It Holds | Status |
|---|---|---|
| **NetworkX (owner)** | `ENGINE::type1_deductive`, `ENGINE::type2_inductive` nodes + `CHIRALITY_COUPLING` edge + `ENGINE_OWNS_STAGE` edges (16 per type) | **Live.** Structural facts. |
| **clifford (next carrier)** | `CHIRALITY_COUPLING` edge as the pseudoscalar `e₁∧e₂∧e₃ = [0,0,0,0,0,0,0,1.0]` | **Correct next semantic carrier.** Chirality IS the pseudoscalar in Cl(3). The coupling is a parity transformation — exactly what grade-3 represents. Currently bounded read-only. |
| **TopoNetX (next carrier)** | The two engine types + coupling form a 1-cell. Shared-torus stages create 2-cells (triangles). | **Bounded read-only projection.** |
| **PyG (next carrier)** | Hetero edge type `('type1', 'couples_with', 'type2')` with learned coupling strength tensor | **Bounded read-only sidecar.** |

## Engine Stages / Subcycles

| Layer | What It Holds | Status |
|---|---|---|
| **NetworkX (owner)** | 16 `MACRO_STAGE` nodes (terrain labels, loop/mode/boundary attributes) + `STAGE_SEQUENCE` cycle edges (n→n+1, with cycle closure) + `OPERATOR_ACTS_ON` edges (4 operators × 16 stages = 64) | **Live.** The canonical 16×4 model. |
| **TopoNetX (next carrier)** | The 8-stage cycle per engine type becomes a 1-cycle (closed loop of 1-cells). The operator subcycle Ti→Fe→Te→Fi at each stage is a separate 1-cycle. Together they form 2-cells ("stage diamonds"). | **Correct next semantic carrier.** Currently bounded read-only. The distinction between "8 stages in a row" vs "8 stages forming a loop" is exactly the difference between a 1-chain and a 1-cycle. |
| **clifford (next carrier)** | `SUBCYCLE_ORDER` edges as grade-1 vectors along e₁ (causality axis): `[0, 1.0, 0, 0]`. `STAGE_SEQUENCE` edges as `[0, 0.8, 0.2, 0]`. | **Bounded read-only.** Encodes operator irreversibility (Ti→Fe ≠ Fe→Ti). |
| **PyG (next carrier)** | Edge features encoding the 4-operator subcycle as a `4×8` tensor. Node features encoding stage metadata. | **Bounded read-only.** For future stage-prediction models. |
| **kingdon (optional)** | Couple clifford Cl(3) coefficients directly to PyTorch gradients for end-to-end differentiable GA edge training. | **Not yet integrated.** |

---

## Summary Table

| Physical Concept | Owner (NetworkX) | TopoNetX | clifford | PyG | LightRAG |
|---|---|---|---|---|---|
| **Axis 0** | Node + governs edges | — | Gradient direction (next) | — | Text retrieval (future) |
| **Hopf Tori** | Nodes + nesting + stage links | **2-cells (next carrier)** | Nesting orientation (next) | Tensor features (next) | Fibration context (future) |
| **Chirality** | Engine nodes + coupling edge | 1-cell (next) | **Pseudoscalar e₁₂₃ (next carrier)** | Hetero edge (next) | — |
| **Macro-stages** | 16 nodes + sequence cycle | **1-cycles (next carrier)** | Causal vectors (next) | Stage tensors (next) | — |
| **Subcycles** | Operator→Stage edges (64) | Stage diamonds (next) | **Irreversibility vectors (next carrier)** | 4×8 op tensors (next) | — |
| **Neg witnesses** | 9 nodes + proves edges | — | Negative bivectors (next) | — | Kill context (future) |
