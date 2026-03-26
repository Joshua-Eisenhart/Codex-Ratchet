# QIT Compression Future References

> Future-use note for compression methods that are relevant to the Ratchet/QIT stack later, but are not the right build target right now.

## Status

- `future_reference_only: true`
- `build_now: no`
- `reason`: these methods solve scale/compression problems that the current QIT graph lane does not have yet

## Papers

| Method | Source | What It Actually Does | Likely Ratchet Slot Later |
|---|---|---|---|
| `QJL` | [arXiv:2406.03482](https://arxiv.org/abs/2406.03482) | Johnson-Lindenstrauss transform plus 1-bit quantization for unbiased inner-product estimation with low memory overhead | compress retrieval/vector-memory surfaces where inner products must remain reliable |
| `TurboQuant` | [arXiv:2504.19874](https://arxiv.org/abs/2504.19874) | online Euclidean vector quantization with random rotation, scalar quantization, and residual-QJL correction | compress large embedding/tensor stores after the system has substantial vector state |
| `PolarQuant` | [arXiv:2502.02617](https://arxiv.org/abs/2502.02617) | random preconditioning plus recursive polar-coordinate quantization for KV caches | compress trajectory/state embeddings later if a polar/angular representation is empirically better than Cartesian storage |

## What They Are Not

These papers do **not** directly solve:

- nested Hopf torus modeling
- Weyl spinor/chirality semantics
- TopoNetX cell-complex construction
- `clifford`-class edge semantics
- owner-graph ontology design

They are compression papers for high-dimensional vector/tensor representations, not nonclassical graph/topology papers.

## Why Not Now

Right now the QIT graph lane is still small:

- `41` nodes
- `185` edges
- bounded sidecars only
- no live LightRAG integration
- no history graph storing massive trajectory volumes

So compression would be premature optimization.

## Revisit Triggers

Re-open this lane when one or more of these become true:

1. QIT graph payloads become large enough that edge/node tensors are a real memory cost.
2. LightRAG or another retrieval sidecar is indexing a large local corpus and embedding storage becomes expensive.
3. A history graph exists and is storing large numbers of engine trajectory snapshots.
4. PyG projections or learned graph features become large enough to need quantized storage.
5. Runtime/state compression becomes a measurable bottleneck in actual profiling.

## Best Later Placement

If these methods are adopted later, the safest placement is:

- owner truth remains: `Pydantic -> JSON -> NetworkX -> GraphML`
- topology remains: `TopoNetX`
- algebra remains: `clifford`
- tensor graph views remain: `PyG`
- compression enters **after** those, as a sidecar over:
  - retrieval embeddings
  - tensor projections
  - history/state snapshots
  - large vector stores

## Read This With

- [QIT_GRAPH_SYNC_README.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/QIT_GRAPH_SYNC_README.md)
- [QIT_GRAPH_SIDECAR_POLICY.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/QIT_GRAPH_SIDECAR_POLICY.md)
- [QIT_GRAPH_RUNTIME_MODEL.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/QIT_GRAPH_RUNTIME_MODEL.md)
