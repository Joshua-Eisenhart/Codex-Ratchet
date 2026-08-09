# Graph Health Dashboard v1

A comprehensive health and topology profile for all A2 graphs in the corpus.

## evidence_graph.json
- **Nodes**: 33
- **Edges**: 17
- **Density**: 0.016098
- **Connected Components**: 16 (Largest: 18)
- **Degree Distribution**: Min=0, Max=17, Mean=1.03, Median=1.00
- **Isolated Nodes (degree 0)**: 15
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `NonCommutativity`: 15
- `SpecClaim`: 14
- `LieClosure`: 3
- `SystemState`: 1

### Edge Relation Types Distribution
- `supports`: 17

### Missing Required Fields
- `description`: 19 nodes missing

### Health Anomalies
- ⚠️ Many nodes missing 'description': 19 nodes

---

## system_graph_a2_refinery.json
- **Nodes**: 3
- **Edges**: 0
- **Density**: 0.000000
- **Connected Components**: 3 (Largest: 1)
- **Degree Distribution**: Min=0, Max=0, Mean=0.00, Median=0.00
- **Isolated Nodes (degree 0)**: 3
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `SIM_KILL`: 2
- `B_PARKED`: 1

### Edge Relation Types Distribution
None

### Missing Required Fields
None

### Health Anomalies
- ⚠️ High number of isolated nodes: 3/3 (100.0%)

---

