# Cross-Graph Overlap Analysis Report

## Node Connectivity and Overlap Matrix

| | A2_INTAKE | A2_REFINEMENT | A2_CONTROL | PROMOTED | A1_JARGONED |
|---|---|---|---|---|---|
| **A2_INTAKE** | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| **A2_REFINEMENT** | 0.0000 | 1.0000 | 0.0524 | 0.0705 | 0.0000 |
| **A2_CONTROL** | 0.0000 | 0.0524 | 1.0000 | 0.4438 | 0.1454 |
| **PROMOTED** | 0.0000 | 0.0705 | 0.4438 | 1.0000 | 0.2388 |
| **A1_JARGONED** | 0.0000 | 0.0000 | 0.1454 | 0.2388 | 1.0000 |

## Pairwise Intersection Details

### A2_INTAKE vs A2_REFINEMENT
- **Shared Nodes:** 0
- **Unique to A2_INTAKE:** 8793
- **Unique to A2_REFINEMENT:** 858
- **Shared Edges:** 0

### A2_INTAKE vs A2_CONTROL
- **Shared Nodes:** 0
- **Unique to A2_INTAKE:** 8793
- **Unique to A2_CONTROL:** 667
- **Shared Edges:** 0

### A2_INTAKE vs PROMOTED
- **Shared Nodes:** 0
- **Unique to A2_INTAKE:** 8793
- **Unique to PROMOTED:** 296
- **Shared Edges:** 0

### A2_INTAKE vs A1_JARGONED
- **Shared Nodes:** 0
- **Unique to A2_INTAKE:** 8793
- **Unique to A1_JARGONED:** 420
- **Shared Edges:** 0

### A2_REFINEMENT vs A2_CONTROL
- **Shared Nodes:** 76
- **Unique to A2_REFINEMENT:** 782
- **Unique to A2_CONTROL:** 591
- **Shared Edges:** 2

### A2_REFINEMENT vs PROMOTED
- **Shared Nodes:** 76
- **Unique to A2_REFINEMENT:** 782
- **Unique to PROMOTED:** 220
- **Shared Edges:** 1

### A2_REFINEMENT vs A1_JARGONED
- **Shared Nodes:** 0
- **Unique to A2_REFINEMENT:** 858
- **Unique to A1_JARGONED:** 420
- **Shared Edges:** 0

### A2_CONTROL vs PROMOTED
- **Shared Nodes:** 296
- **Unique to A2_CONTROL:** 371
- **Unique to PROMOTED:** 0
- **Shared Edges:** 717

### A2_CONTROL vs A1_JARGONED
- **Shared Nodes:** 138
- **Unique to A2_CONTROL:** 529
- **Unique to A1_JARGONED:** 282
- **Shared Edges:** 77

### PROMOTED vs A1_JARGONED
- **Shared Nodes:** 138
- **Unique to PROMOTED:** 158
- **Unique to A1_JARGONED:** 282
- **Shared Edges:** 68

## Critical Integrity Checks

### 1. Promoted ⊆ Low-Control
- **Status:** PASS

### 2. Flow Integrity (Intake → Refinement → Control)
- **Refinement nodes not in Intake:** 858
- **Control nodes not in Refinement:** 591

### 3. Unexpected Placements
- **Spontaneous nodes in Control (not in Ref/Intake):** 591
  - Examples:
    - `A2_1::KERNEL::a2_deterministic_tick_sequence::e132b0c90141d83b`
    - `A2_3::SOURCE_MAP_PASS::relational_transport_admissibility_v1::b227577258ac9143`
    - `A2_3::SOURCE_MAP_PASS::run_super_batch::1ba823e0446c63fd`
    - `A2_1::KERNEL::KERNEL__IDENTITY_EMERGENCE::0b5dbc77cac1b7bc`
    - `A2_3::SOURCE_MAP_PASS::finite_universe_compressibility::71ef60b58bfaa3d3`