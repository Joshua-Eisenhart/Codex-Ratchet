---
id: "A2_3::SOURCE_MAP_PASS::control_plane_state_transition_digest_v1::0d1531cb9c950587"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# control_plane_state_transition_digest_v1
**Node ID:** `A2_3::SOURCE_MAP_PASS::control_plane_state_transition_digest_v1::0d1531cb9c950587`

## Description
STATE_TRANSITION_DIGEST_v1.md (1332B): # STATE_TRANSITION_DIGEST v1  Defines deterministic transition hashing at the A0 boundary for replay verification.  This is not a container primitive and does not modify B admission rules. It is a deterministic digest computed from existing artifacts/hashes.  ## Definition (normative)  For any accep

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[state_transition_digest]]
- **DEPENDS_ON** → [[state_transition_digest_v1]]
- **EXCLUDES** → [[v3_runtime_test_state_transition_digest]]
- **EXCLUDES** → [[test_state_transition_digest_py]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v2_state_transition_digest_v1]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v3_state_transition_digest_v1]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v4_state_transition_digest_v1]]

## Inward Relations
- [[LAYER_ISOLATION_INVARIANT_v1.md]] → **SOURCE_MAP_PASS**
