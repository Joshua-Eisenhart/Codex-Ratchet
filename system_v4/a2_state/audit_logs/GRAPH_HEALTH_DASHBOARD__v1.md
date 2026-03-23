# Graph Health Dashboard v1

A comprehensive health and topology profile for all A2 graphs in the corpus.

## a1_jargoned_graph_v1.json
- **Nodes**: 420
- **Edges**: 1288
- **Density**: 0.007319
- **Connected Components**: 75 (Largest: 231)
- **Degree Distribution**: Min=0, Max=45, Mean=6.13, Median=3.00
- **Isolated Nodes (degree 0)**: 49
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `KERNEL_CONCEPT`: 415
- `EXTRACTED_CONCEPT`: 5

### Edge Relation Types Distribution
- `OVERLAPS`: 498
- `STRUCTURALLY_RELATED`: 385
- `DEPENDS_ON`: 184
- `RELATED_TO`: 141
- `EXCLUDES`: 73
- `REFINED_INTO`: 6
- `CONTRADICTS`: 1

### Missing Required Fields
None

### Health Anomalies
- ✅ No significant anomalies detected.

---

## a2_high_intake_graph_v1.json
- **Nodes**: 8793
- **Edges**: 16279
- **Density**: 0.000211
- **Connected Components**: 1708 (Largest: 4894)
- **Degree Distribution**: Min=1, Max=185, Mean=3.70, Median=1.00
- **Isolated Nodes (degree 0)**: 0
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `EXTRACTED_CONCEPT`: 5765
- `SOURCE_DOCUMENT`: 3028

### Edge Relation Types Distribution
- `RELATED_TO`: 6001
- `SOURCE_MAP_PASS`: 5449
- `STRUCTURALLY_RELATED`: 3010
- `EXCLUDES`: 793
- `DEPENDS_ON`: 753
- `ENGINE_PATTERN_PASS`: 258
- `MATH_CLASS_PASS`: 6
- `QIT_BRIDGE_PASS`: 5
- `CONTRADICTS`: 3
- `OVERLAPS`: 1

### Missing Required Fields
None

### Health Anomalies
- ✅ No significant anomalies detected.

---

## a2_low_control_graph_v1.json
- **Nodes**: 419
- **Edges**: 858
- **Density**: 0.004899
- **Connected Components**: 272 (Largest: 62)
- **Degree Distribution**: Min=0, Max=53, Mean=4.10, Median=0.00
- **Isolated Nodes (degree 0)**: 218
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `KERNEL_CONCEPT`: 419

### Edge Relation Types Distribution
- `OVERLAPS`: 614
- `STRUCTURALLY_RELATED`: 178
- `DEPENDS_ON`: 55
- `EXCLUDES`: 9
- `RELATED_TO`: 2

### Missing Required Fields
None

### Health Anomalies
- ⚠️ High number of isolated nodes: 218/419 (52.0%)

---

## a2_mid_refinement_graph_v1.json
- **Nodes**: 858
- **Edges**: 3029
- **Density**: 0.004119
- **Connected Components**: 547 (Largest: 50)
- **Degree Distribution**: Min=0, Max=49, Mean=7.06, Median=0.00
- **Isolated Nodes (degree 0)**: 481
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `REFINED_CONCEPT`: 858

### Edge Relation Types Distribution
- `OVERLAPS`: 2947
- `DEPENDS_ON`: 43
- `STRUCTURALLY_RELATED`: 30
- `EXCLUDES`: 5
- `REFINED_INTO`: 2
- `RELATED_TO`: 2

### Missing Required Fields
None

### Health Anomalies
- ⚠️ High number of isolated nodes: 481/858 (56.1%)

---

## enriched_a2_low_control_graph_v1.json
- **Nodes**: 419
- **Edges**: 858
- **Density**: 0.004899
- **Connected Components**: 272 (Largest: 62)
- **Degree Distribution**: Min=0, Max=53, Mean=4.10, Median=0.00
- **Isolated Nodes (degree 0)**: 218
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `KERNEL_CONCEPT`: 419

### Edge Relation Types Distribution
- `OVERLAPS`: 614
- `STRUCTURALLY_RELATED`: 178
- `DEPENDS_ON`: 55
- `EXCLUDES`: 9
- `RELATED_TO`: 2

### Missing Required Fields
None

### Health Anomalies
- ⚠️ High number of isolated nodes: 218/419 (52.0%)

---

## identity_registry_overlap_suggestions_v1.json
- **Nodes**: 7392
- **Edges**: 95106
- **Density**: 0.001741
- **Connected Components**: 510 (Largest: 5018)
- **Degree Distribution**: Min=1, Max=200, Mean=25.73, Median=10.00
- **Isolated Nodes (degree 0)**: 0
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `IDENTITY_ENTITY`: 7392

### Edge Relation Types Distribution
- `IDENTITY_OVERLAP`: 95106

### Missing Required Fields
- `admissibility_state`: 7392 nodes missing

### Health Anomalies
- ⚠️ Many nodes missing 'admissibility_state': 7392 nodes

---

## identity_registry_v1.json
- **Nodes**: 13481
- **Edges**: 0
- **Density**: 0.000000
- **Connected Components**: 13481 (Largest: 1)
- **Degree Distribution**: Min=0, Max=0, Mean=0.00, Median=0.00
- **Isolated Nodes (degree 0)**: 13481
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `IDENTITY_ENTITY`: 13481

### Edge Relation Types Distribution
None

### Missing Required Fields
- `admissibility_state`: 13481 nodes missing

### Health Anomalies
- ⚠️ High number of isolated nodes: 13481/13481 (100.0%)
- ⚠️ Many nodes missing 'admissibility_state': 13481 nodes

---

## nested_graph_v1.json
- **Nodes**: 0
- **Edges**: 0
- **Density**: 0.000000
- **Connected Components**: 0 (Largest: 0)
- **Degree Distribution**: Min=0, Max=0, Mean=0.00, Median=0.00
- **Isolated Nodes (degree 0)**: 0
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
None

### Edge Relation Types Distribution
None

### Missing Required Fields
None

### Health Anomalies
- ✅ No significant anomalies detected.

---

## promoted_subgraph.json
- **Nodes**: 296
- **Edges**: 733
- **Density**: 0.008394
- **Connected Components**: 14 (Largest: 265)
- **Degree Distribution**: Min=1, Max=68, Mean=4.95, Median=2.00
- **Isolated Nodes (degree 0)**: 0
- **Self-loops**: 0
- **Duplicate Edges**: 2
- **Dangling Edges**: 0

### Node Types Distribution
- `REFINED_CONCEPT`: 145
- `EXTRACTED_CONCEPT`: 112
- `KERNEL_CONCEPT`: 39

### Edge Relation Types Distribution
- `STRUCTURALLY_RELATED`: 294
- `EXCLUDES`: 163
- `CO_EXTRACTED`: 140
- `DEPENDS_ON`: 47
- `CONSTRAINS`: 45
- `RELATED_TO`: 21
- `REFINED_INTO`: 18
- `PROMOTED_TO_KERNEL`: 4
- `CONTRADICTS`: 1

### Missing Required Fields
None

### Health Anomalies
- ⚠️ 2 duplicate edges found

---

## system_graph_a2_refinery.json
- **Nodes**: 19941
- **Edges**: 40763
- **Density**: 0.000103
- **Connected Components**: 1086 (Largest: 18758)
- **Degree Distribution**: Min=0, Max=1898, Mean=4.09, Median=1.00
- **Isolated Nodes (degree 0)**: 1045
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `SOURCE_DOCUMENT`: 10099
- `EXTRACTED_CONCEPT`: 5895
- `REFINED_CONCEPT`: 1287
- `KERNEL_CONCEPT`: 842
- `CARTRIDGE_PACKAGE`: 401
- `EXECUTION_BLOCK`: 401
- `B_OUTCOME`: 401
- `SKILL`: 123
- `GRAVEYARD_RECORD`: 99
- `SIM_KILL`: 98
- `B_PARKED`: 96
- `B_SURVIVOR`: 78
- `SIM_EVIDENCED`: 67
- `THREAD_SEAL`: 21
- `TERM_ADMITTED`: 20
- `INTENT_SIGNAL`: 6
- `INTENT_REFINEMENT`: 3
- `CONTEXT_SIGNAL`: 2
- `CONCEPT`: 1
- `EMPIRICAL_EVIDENCE`: 1

### Edge Relation Types Distribution
- `RELATED_TO`: 9677
- `SOURCE_MAP_PASS`: 7121
- `OVERLAPS`: 6641
- `DEPENDS_ON`: 6000
- `STRUCTURALLY_RELATED`: 5409
- `EXCLUDES`: 2008
- `SOURCE_MAP`: 976
- `STRIPPED_FROM`: 401
- `ROSETTA_MAP`: 401
- `PACKAGED_FROM`: 401
- `COMPILED_FROM`: 401
- `ADJUDICATED_FROM`: 401
- `ENGINE_PATTERN_PASS`: 258
- `SKILL_OPERATES_ON`: 119
- `GRAVEYARD_OF`: 100
- `SIM_KILLED`: 98
- `REFINED_INTO`: 77
- `SIM_EVIDENCE_FOR`: 67
- `PART_OF`: 47
- `ACCEPTED_FROM`: 47
- `PARKED_FROM`: 38
- `TERM_ADMITTED_FROM`: 20
- `BEAT_IN_RATCHET`: 17
- `SKILL_FOLLOWS`: 12
- `MATH_CLASS_PASS`: 6
- `CONTRADICTS`: 5
- `QIT_BRIDGE_PASS`: 5
- `TERM_CONFLICT_PASS`: 3
- `PROMOTED_TO_KERNEL`: 3
- `REFINES_INTENT`: 3
- `EVIDENCED_FROM`: 1

### Missing Required Fields
None

### Health Anomalies
- ✅ No significant anomalies detected.

---

## system_graph_v3_full_system_ingest_v1.json
- **Nodes**: 1236
- **Edges**: 0
- **Density**: 0.000000
- **Connected Components**: 1236 (Largest: 1)
- **Degree Distribution**: Min=0, Max=0, Mean=0.00, Median=0.00
- **Isolated Nodes (degree 0)**: 1236
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `CONTROL_SURFACE`: 454
- `STATE_SURFACE`: 354
- `SKILL`: 228
- `PROTOCOL`: 123
- `QUEUE_SURFACE`: 49
- `SPEC`: 10
- `MEMORY_SURFACE`: 8
- `CONTRACT`: 7
- `PUBLIC_DOC`: 3

### Edge Relation Types Distribution
None

### Missing Required Fields
None

### Health Anomalies
- ⚠️ High number of isolated nodes: 1236/1236 (100.0%)

---

## system_graph_v3_ingest_pass1.json
- **Nodes**: 298
- **Edges**: 133
- **Density**: 0.001503
- **Connected Components**: 202 (Largest: 74)
- **Degree Distribution**: Min=0, Max=12, Mean=0.89, Median=0.00
- **Isolated Nodes (degree 0)**: 195
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `SKILL`: 157
- `PROTOCOL`: 68
- `AGENT`: 39
- `VALIDATOR`: 17
- `SPEC`: 10
- `CONTRACT`: 7

### Edge Relation Types Distribution
- `IMPORTS_FROM`: 133

### Missing Required Fields
- `admissibility_state`: 298 nodes missing

### Health Anomalies
- ⚠️ High number of isolated nodes: 195/298 (65.4%)
- ⚠️ Many nodes missing 'admissibility_state': 298 nodes

---

