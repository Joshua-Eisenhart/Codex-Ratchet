---
id: "A2_3::SOURCE_MAP_PASS::state_transition_digest::ff010611f4a9fa89"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# state_transition_digest
**Node ID:** `A2_3::SOURCE_MAP_PASS::state_transition_digest::ff010611f4a9fa89`

## Description
Deterministic digest at A0 boundary combining previous sequence inputs. sha256(previous_state_hash + export_block_hash + snapshot_hash + compiler_version).

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **EXCLUDES** → [[sysrepair_v2_state_transition_digest_v1]]
- **EXCLUDES** → [[sysrepair_v3_state_transition_digest_v1]]
- **EXCLUDES** → [[sysrepair_v4_state_transition_digest_v1]]
- **EXCLUDES** → [[v3_runtime_test_state_transition_digest]]
- **EXCLUDES** → [[state_transition_digest_v1]]
- **EXCLUDES** → [[test_state_transition_digest_py]]
- **DEPENDS_ON** → [[export_block]]
- **DEPENDS_ON** → [[input]]

## Inward Relations
- [[STATE_TRANSITION_DIGEST_v1.md]] → **SOURCE_MAP_PASS**
- [[promotion_binding_and_evidence_digests]] → **DEPENDS_ON**
- [[control_plane_state_transition_digest_v1]] → **DEPENDS_ON**
- [[v3_runtime_a1_a0_b_sim_runner]] → **DEPENDS_ON**
