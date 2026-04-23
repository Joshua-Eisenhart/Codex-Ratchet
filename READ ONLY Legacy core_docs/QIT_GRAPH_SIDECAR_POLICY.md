# QIT Graph Sidecar Policy

> Explicit contract for what each sidecar may and may not do relative to the owner graph.
> The owner stack is: `Pydantic → JSON → NetworkX → GraphML (export)`

---

## General Rules

1. **Owner graph is source of truth.** All structural facts (node existence, edge existence, attribute values) live in the owner layer.
2. **Sidecars are read-only projections.** They may compute derived views but must NOT create nodes or edges that don't exist in the owner graph.
3. **Sidecars may annotate.** They may attach computed payloads (multivectors, tensors, cell indices) as projections, stored in their own output files — not in the owner JSON.
4. **No sidecar may claim semantic ownership** until it passes a promotion gate (see `QIT_GRAPH_PROMOTION_GATES.md`).
5. **Sidecar output is ephemeral.** It can be regenerated from the owner graph at any time. Loss of a sidecar file must not lose structural truth.

---

## Per-Sidecar Policy

### LightRAG — Memory & Retrieval Sidecar

| Permission | Status |
|---|---|
| Read owner graph nodes/edges | ✅ Allowed |
| Query corpus + SIM result text | ✅ Allowed (target use) |
| Insert text documents for retrieval | ✅ Allowed |
| Create new owner-graph nodes | ❌ Prohibited |
| Modify owner-graph attributes | ❌ Prohibited |
| Claim retrieval results as proven facts | ❌ Prohibited |

**Current status**: Bounded corpus-build slice is landed under `work/lightrag_smoke/`; actual indexing/query remains blocked until a local embedding configuration is provided.

### TopoNetX — Topology Sidecar

| Permission | Status |
|---|---|
| Read owner graph nodes/edges | ✅ Allowed |
| Build CellComplex from owner edges | ✅ Allowed |
| Identify 1-cycles (closed stage loops) | ✅ Allowed |
| Identify 2-cells (stage diamonds, torus patches) | ✅ Allowed |
| Compute Betti numbers and boundary operators | ✅ Allowed |
| Create new owner-graph nodes | ❌ Prohibited |
| Promote 2-cells to owner-layer truth | ❌ Requires promotion gate |
| Replace NetworkX as the graph engine | ❌ Prohibited |

**Current status**: Bounded read-only projection. Live in `nested_graph_builder.py` and `toponetx_projection_adapter_audit.py`.

### clifford — Algebra Sidecar

| Permission | Status |
|---|---|
| Read owner graph edge relations | ✅ Allowed |
| Compute Cl(3,0) multivector payloads per edge | ✅ Allowed |
| Attach graded/oriented semantics as payloads | ✅ Allowed |
| Verify noncommutativity of operator products | ✅ Allowed |
| Modify owner-graph edge types or weights | ❌ Prohibited |
| Claim chirality pseudoscalar as governing semantic | ❌ Requires promotion gate |
| Replace flat edge labels with multivector-only identity | ❌ Prohibited |

**Current status**: Bounded read-only sidecar. Live in `graph_tool_integration.py` with `RELATION_GA_SPEC` mapping.

### PyG — Tensor Sidecar

| Permission | Status |
|---|---|
| Read owner graph nodes/edges | ✅ Allowed |
| Build HeteroData with tensor features | ✅ Allowed |
| Compute learned/dynamic embeddings | ✅ Allowed |
| Train GNNs over the tensorized graph | ✅ Allowed (future) |
| Create new owner-graph nodes from embeddings | ❌ Prohibited |
| Replace NetworkX as the graph engine | ❌ Prohibited |
| Use tensor distances as edge weights in owner graph | ❌ Requires promotion gate |

**Current status**: Bounded read-only sidecar. Live in `nested_graph_builder.py` and `pyg_heterograph_projection_audit.py`.

### kingdon — Optional GA-Torch Bridge

| Permission | Status |
|---|---|
| Couple clifford Cl(3) coefficients to PyTorch gradients | ✅ Allowed |
| Provide differentiable GA operations | ✅ Allowed |
| Replace clifford as the GA engine | ❌ Prohibited without explicit migration |
| Create owner-graph structure | ❌ Prohibited |

**Current status**: Not yet integrated. Listed as optional in owner/sidecar stack.

---

## Enforcement

- All sidecar scripts must check for the `PREFERRED_INTERPRETER` venv (`.venv_spec_graph/bin/python`) or gracefully degrade.
- All sidecar output files must live under `system_v4/a2_state/audit_logs/` or a sidecar-specific output path, NEVER in `system_v4/a2_state/graphs/` (owner territory).
- Exception: `graph_tool_integration.py` writes enriched copies to `enriched_*.json` — these are explicitly marked as sidecar projections, not owner truth.
