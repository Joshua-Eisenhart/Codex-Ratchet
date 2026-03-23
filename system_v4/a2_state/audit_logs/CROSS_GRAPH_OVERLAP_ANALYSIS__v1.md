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
- **Shared Edges:** 3

### A2_REFINEMENT vs PROMOTED
- **Shared Nodes:** 76
- **Unique to A2_REFINEMENT:** 782
- **Unique to PROMOTED:** 220
- **Shared Edges:** 2

### A2_REFINEMENT vs A1_JARGONED
- **Shared Nodes:** 0
- **Unique to A2_REFINEMENT:** 858
- **Unique to A1_JARGONED:** 420
- **Shared Edges:** 0

### A2_CONTROL vs PROMOTED
- **Shared Nodes:** 296
- **Unique to A2_CONTROL:** 371
- **Unique to PROMOTED:** 0
- **Shared Edges:** 731

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
    - `A2_3::SOURCE_MAP_PASS::a2_state_v3_a2_controller_launch_packet__current__20::d5f400862792dac3`
    - `A2_3::SOURCE_MAP_PASS::a1_thread_boot_eight_hard_rules::305bb4ebdc28de2b`
    - `A2_3::SOURCE_MAP_PASS::workspace_layout_v1::5e299d60c482e0cf`
    - `A2_3::SOURCE_MAP_PASS::doc_a711a4ddad9c::90955d3e62817c96`
    - `A2_3::SOURCE_MAP_PASS::zip_boot_binding_rules::f5841e532ff7e2f3`