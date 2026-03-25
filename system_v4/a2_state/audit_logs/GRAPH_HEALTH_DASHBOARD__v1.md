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
- **Nodes**: 667
- **Edges**: 1121
- **Density**: 0.002524
- **Connected Components**: 286 (Largest: 295)
- **Degree Distribution**: Min=0, Max=66, Mean=3.36, Median=1.00
- **Isolated Nodes (degree 0)**: 229
- **Self-loops**: 0
- **Duplicate Edges**: 19
- **Dangling Edges**: 0

### Node Types Distribution
- `KERNEL_CONCEPT`: 410
- `REFINED_CONCEPT`: 145
- `EXTRACTED_CONCEPT`: 112

### Edge Relation Types Distribution
- `STRUCTURALLY_RELATED`: 624
- `EXCLUDES`: 168
- `CO_EXTRACTED`: 138
- `DEPENDS_ON`: 101
- `CONSTRAINS`: 45
- `RELATED_TO`: 22
- `REFINED_INTO`: 20
- `PROMOTED_TO_KERNEL`: 2
- `CONTRADICTS`: 1

### Missing Required Fields
None

### Health Anomalies
- ⚠️ 19 duplicate edges found

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

## evidence_graph.json
- **Nodes**: 31
- **Edges**: 15
- **Density**: 0.016129
- **Connected Components**: 16 (Largest: 16)
- **Degree Distribution**: Min=0, Max=15, Mean=0.97, Median=1.00
- **Isolated Nodes (degree 0)**: 15
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `NonCommutativity`: 15
- `SpecClaim`: 12
- `LieClosure`: 3
- `SystemState`: 1

### Edge Relation Types Distribution
- `supports`: 13
- `refutes`: 2

### Missing Required Fields
- `description`: 19 nodes missing

### Health Anomalies
- ⚠️ Many nodes missing 'description': 19 nodes

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
None

### Health Anomalies
- ✅ No significant anomalies detected.

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
None

### Health Anomalies
- ⚠️ High number of isolated nodes: 13481/13481 (100.0%)

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

## nested_system_graph_v1.json
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

## probe_evidence_graph.json
- **Nodes**: 261
- **Edges**: 202
- **Density**: 0.002977
- **Connected Components**: 60 (Largest: 21)
- **Degree Distribution**: Min=1, Max=20, Mean=1.55, Median=1.00
- **Isolated Nodes (degree 0)**: 0
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `evidence_token`: 200
- `probe_evidence`: 61

### Edge Relation Types Distribution
- `produces`: 202

### Missing Required Fields
None

### Health Anomalies
- ✅ No significant anomalies detected.

---

## promoted_subgraph.json
- **Nodes**: 296
- **Edges**: 717
- **Density**: 0.008211
- **Connected Components**: 18 (Largest: 261)
- **Degree Distribution**: Min=0, Max=65, Mean=4.84, Median=2.00
- **Isolated Nodes (degree 0)**: 4
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `REFINED_CONCEPT`: 145
- `EXTRACTED_CONCEPT`: 112
- `KERNEL_CONCEPT`: 39

### Edge Relation Types Distribution
- `STRUCTURALLY_RELATED`: 293
- `EXCLUDES`: 152
- `CO_EXTRACTED`: 138
- `DEPENDS_ON`: 47
- `CONSTRAINS`: 45
- `RELATED_TO`: 21
- `REFINED_INTO`: 18
- `PROMOTED_TO_KERNEL`: 2
- `CONTRADICTS`: 1

### Missing Required Fields
None

### Health Anomalies
- ✅ No significant anomalies detected.

---

## system_architecture_v1.json
- **Nodes**: 826
- **Edges**: 2931
- **Density**: 0.004301
- **Connected Components**: 3 (Largest: 818)
- **Degree Distribution**: Min=1, Max=219, Mean=7.10, Median=2.00
- **Isolated Nodes (degree 0)**: 0
- **Self-loops**: 13
- **Duplicate Edges**: 2
- **Dangling Edges**: 0

### Node Types Distribution
- `V3_TOOL`: 215
- `V4_SKILL`: 131
- `V4_TEST`: 93
- `V3_RUNTIME`: 92
- `V4_SKILL_SPEC`: 88
- `V3_SPEC`: 86
- `V4_RUNNER`: 18
- `UPGRADE_DOC`: 14
- `SYSTEM_LAYER`: 13
- `V4_PROBE`: 12
- `V4_GOVERNANCE`: 9
- `CANONICAL_STATE`: 9
- `V4_STATE`: 8
- `V3_STATE`: 8
- `SYSTEM_FLOWMIND`: 7
- `V3_SYSTEM_LAYER`: 6
- `LEV_CTX`: 4
- `COMPILATION_CONCEPT`: 3
- `LEV_PRIMITIVE`: 3
- `CR_CTX`: 3
- `SYSTEM_BRIDGE`: 1
- `RUNTIME_PRIMITIVE`: 1
- `GRAPH_STRUCTURE`: 1
- `SYSTEM_CAPABILITY`: 1

### Edge Relation Types Distribution
- `GOVERNS`: 457
- `CO_GOVERNED`: 396
- `BELONGS_TO_LAYER`: 340
- `REFERENCES`: 300
- `EVOLVED_INTO`: 225
- `IMPORTS`: 219
- `TESTS`: 215
- `CO_LAYER`: 175
- `USES`: 104
- `SPECIFIES`: 91
- `CO_IMPORTS`: 75
- `CO_ACCESSES`: 74
- `IMPLEMENTED_IN_V4_BY`: 46
- `PORTED_TO`: 37
- `READS_WRITES`: 30
- `READS_STATE`: 29
- `IMPLEMENTS`: 21
- `FEEDS`: 19
- `SHARES_CONCEPTS`: 18
- `MIRRORS`: 11
- `REQUIRES`: 8
- `RELATED_TO`: 7
- `MAPS_TO`: 6
- `SHARES_REQUIREMENTS`: 3
- `CONTAINS`: 2
- `ANALOGOUS_TO`: 2
- `DERIVED_FROM`: 2
- `PROBES`: 1
- `DISTILLS_TO`: 1
- `PACKAGES_FOR`: 1
- `COMPILES_TO`: 1
- `TESTED_BY`: 1
- `DISTILLS_INTO`: 1
- `OPERATES_ON`: 1
- `ENABLES`: 1
- `TYPES_USED_BY`: 1
- `PRODUCES`: 1
- `GOVERNED_BY`: 1
- `GATED_BY`: 1
- `LOGGED_BY`: 1
- `DEFINES_TYPES_FOR`: 1
- `DEFINES_GATES_FOR`: 1
- `DEFINES_TERMS_FOR`: 1
- `ENCODES`: 1
- `SUPERSEDES`: 1
- `OPERATIONALIZES`: 1

### Missing Required Fields
- `description`: 811 nodes missing

### Health Anomalies
- ⚠️ 2 duplicate edges found
- ⚠️ Many nodes missing 'description': 811 nodes

---

## system_graph_a2_refinery.json
- **Nodes**: 19977
- **Edges**: 40793
- **Density**: 0.000102
- **Connected Components**: 1107 (Largest: 18765)
- **Degree Distribution**: Min=0, Max=1898, Mean=4.08, Median=1.00
- **Isolated Nodes (degree 0)**: 1058
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `SOURCE_DOCUMENT`: 10107
- `EXTRACTED_CONCEPT`: 5903
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
- `SIM_EVIDENCED`: 68
- `THREAD_SEAL`: 21
- `TERM_ADMITTED`: 20
- `SKILL_CLUSTER`: 14
- `INTENT_SIGNAL`: 6
- `LEGACY_V3_TOOL`: 5
- `INTENT_REFINEMENT`: 3
- `CONTEXT_SIGNAL`: 2
- `CONCEPT`: 1
- `EMPIRICAL_EVIDENCE`: 1

### Edge Relation Types Distribution
- `RELATED_TO`: 9677
- `SOURCE_MAP_PASS`: 7129
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
- `MEMBER_OF`: 22
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

## system_graph_system_architecture.json
- **Nodes**: 5
- **Edges**: 0
- **Density**: 0.000000
- **Connected Components**: 5 (Largest: 1)
- **Degree Distribution**: Min=0, Max=0, Mean=0.00, Median=0.00
- **Isolated Nodes (degree 0)**: 5
- **Self-loops**: 0
- **Duplicate Edges**: 0
- **Dangling Edges**: 0

### Node Types Distribution
- `V3_TOOL`: 5

### Edge Relation Types Distribution
None

### Missing Required Fields
None

### Health Anomalies
- ⚠️ High number of isolated nodes: 5/5 (100.0%)

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
None

### Health Anomalies
- ⚠️ High number of isolated nodes: 195/298 (65.4%)

---

## trust_zone_registry_v1.json
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

