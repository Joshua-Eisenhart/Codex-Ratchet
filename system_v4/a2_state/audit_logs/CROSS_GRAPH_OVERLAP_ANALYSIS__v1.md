# Cross-Graph Overlap Analysis Report

## Node Connectivity and Overlap Matrix

| | A2_INTAKE | A2_REFINEMENT | A2_CONTROL | PROMOTED | A1_JARGONED |
|---|---|---|---|---|---|
| **A2_INTAKE** | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| **A2_REFINEMENT** | 0.0000 | 1.0000 | 0.0000 | 0.0705 | 0.0000 |
| **A2_CONTROL** | 0.0000 | 0.0000 | 1.0000 | 0.0720 | 0.0000 |
| **PROMOTED** | 0.0000 | 0.0705 | 0.0720 | 1.0000 | 0.2388 |
| **A1_JARGONED** | 0.0000 | 0.0000 | 0.0000 | 0.2388 | 1.0000 |

## Pairwise Intersection Details

### A2_INTAKE vs A2_REFINEMENT
- **Shared Nodes:** 0
- **Unique to A2_INTAKE:** 8793
- **Unique to A2_REFINEMENT:** 858
- **Shared Edges:** 0

### A2_INTAKE vs A2_CONTROL
- **Shared Nodes:** 0
- **Unique to A2_INTAKE:** 8793
- **Unique to A2_CONTROL:** 419
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
- **Shared Nodes:** 0
- **Unique to A2_REFINEMENT:** 858
- **Unique to A2_CONTROL:** 419
- **Shared Edges:** 0

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
- **Shared Nodes:** 48
- **Unique to A2_CONTROL:** 371
- **Unique to PROMOTED:** 248
- **Shared Edges:** 12

### A2_CONTROL vs A1_JARGONED
- **Shared Nodes:** 0
- **Unique to A2_CONTROL:** 419
- **Unique to A1_JARGONED:** 420
- **Shared Edges:** 0

### PROMOTED vs A1_JARGONED
- **Shared Nodes:** 138
- **Unique to PROMOTED:** 158
- **Unique to A1_JARGONED:** 282
- **Shared Edges:** 68

## Critical Integrity Checks

### 1. Promoted ⊆ Low-Control
- **Status:** FAIL
- **Missing Nodes from Control (248):**
  - `A2_1::KERNEL::a2_deterministic_tick_sequence::e132b0c90141d83b`
  - `A2_1::KERNEL::evidence_ladder_sims::4828333df471f578`
  - `A2_3::SOURCE_MAP_PASS::high_entropy_raw_text_dumps::6b4bfa213a204882`
  - `A2_3::SOURCE_MAP_PASS::system_v4_rebuild_frame::fb7004f2fc9ec689`
  - `A2_2::REFINED::TERM_RATCHET_THROUGH_EVIDENCE::abe368163df03e4a`
  - `A2_3::SOURCE_MAP_PASS::axis_foundation_companion::6c80c870b389efc1`
  - `A2_2::REFINED::auto_go_on_rule::bc5b6dadfe65f230`
  - `A2_3::SOURCE_MAP_PASS::derived_only_guard::06512d5867bc5b48`
  - `A2_2::REFINED::a1_wiggle_five_lanes::65d3c7dbd70b3eb8`
  - `A2_3::SOURCE_MAP_PASS::control_plane_bundle_architecture::b5fb627b4f8a3d7b`
  - ... and 238 more.

### 2. Flow Integrity (Intake → Refinement → Control)
- **Refinement nodes not in Intake:** 858
- **Control nodes not in Refinement:** 419

### 3. Unexpected Placements
- **Spontaneous nodes in Control (not in Ref/Intake):** 419
  - Examples:
    - `A2_3::SOURCE_MAP_PASS::system_upgrade_plan_extract_pass8::51d3da3c60bc09a1`
    - `A2_3::SOURCE_MAP_PASS::doc_a711a4ddad9c::90955d3e62817c96`
    - `A2_3::SOURCE_MAP_PASS::fix_near_001_park_near_duplicate::cd2897d4d49d40e0`
    - `A2_3::SOURCE_MAP_PASS::sim_term_generic_negative_py::d65954cb3d6bdbc2`
    - `A2_3::SOURCE_MAP_PASS::doc_63997ac5ae28::921196b37a538ecf`